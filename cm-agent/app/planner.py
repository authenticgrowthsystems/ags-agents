"""FAZA 2: proaktywny planer tygodnia (CM_FAZA2_DESIGN_v1, decyzje Tomasza 04/07).
Trigger: cron niedziela 20:15 (POST /plan) + 'zaplanuj tydzien' w rozmowie. Horyzont: tydzien szczegolowo
+ zarys miesiaca (brand_config cm_month_outline). Wsad: brand_strategy + SCHOWEK (inspirations) +
content_memory (antydubel, co gralo) + kadencja per cel (kanon 11d) + biezaca kolejka.
Wynik: content_items status='proposed' + JEDNA ponumerowana wiadomosc na Telegram.
Akceptacja/edycje w rozmowie (plan_approve/plan_edit) -> 'planned' -> generacja CALOSCI od razu (D-F2-3)."""
import datetime
import json
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import db, config, tasks, content_memory
from .brand import load_brand
from .generate import client

WARSAW = ZoneInfo("Europe/Warsaw")

PLAN_TOOL = {
    "name": "emit_plan",
    "description": "Zwroc plan tygodnia jako strukture. KAZDA pozycja: temat z katem, cele, slot ISO, format.",
    "input_schema": {
        "type": "object",
        "properties": {
            "month_outline": {"type": "string",
                              "description": "Zarys kierunkow biezacego miesiaca (3-5 zdan, spojny z filarami)."},
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "theme": {"type": "string", "description": "Temat-matka z uzgodnionym katem narracji."},
                "targets": {"type": "array", "items": {"type": "string"},
                            "description": "Kanaly z listy AKTYWNYCH celow (np. x, linkedin)."},
                "slot": {"type": "string", "description": "ISO 8601 z offsetem, np. 2026-07-06T10:00:00+02:00"},
                "format": {"type": "string", "enum": ["post", "article"],
                           "description": "article TYLKO dla niedzielnego LinkedIn (kanon 11d)."},
            }, "required": ["theme", "targets", "slot"]}},
        },
        "required": ["items"],
    },
}


def _tg_send(chat_id, text):
    from . import conversation
    conversation._reply(chat_id, text)


def _admin_chat():
    from . import hitl
    return hitl._admin_chat_id()


def _cadence_text(brand_id):
    rows = db.fetchall(
        "SELECT channel, config FROM channels WHERE brand_id=%s AND supervised=true AND status IN ('active','draft')",
        (brand_id,))
    lines = []
    for r in rows:
        cfg = r.get("config") or {}
        if r["channel"] == "x":
            lines.append(f"- x: {cfg.get('posts_per_day', '3-5')} postow DZIENNIE, rozlozone miedzy 09:00 a 21:00")
        elif r["channel"].startswith("linkedin"):
            lines.append(f"- {r['channel']}: poniedzialek-piatek 1 post (ok. 10:00), sobota NIC, "
                         "niedziela ARTYKUL (format article, ok. 11:00)")
        else:
            lines.append(f"- {r['channel']}: {json.dumps(cfg.get('weekly_pattern', 'wg uznania'), ensure_ascii=False)}")
    return "\n".join(lines) or "(brak aktywnych celow)"


def _schowek_text(brand_id, limit=15):
    rows = db.fetchall(
        "SELECT id, content FROM inspirations WHERE status='new' ORDER BY created_at DESC LIMIT %s", (limit,))
    return "\n".join(f"- (schowek #{r['id']}) {(r['content'] or '')[:100]}" for r in rows) or "(schowek pusty)"


def _current_plan_text(brand_id):
    rows = db.fetchall(
        """SELECT master_theme, status, scheduled_for FROM content_items
           WHERE brand_id=%s AND status IN ('proposed','planned','needs_approval','approved','drafting')
           ORDER BY scheduled_for NULLS LAST LIMIT 40""", (brand_id,))
    out = []
    for r in rows:
        when = r["scheduled_for"].astimezone(WARSAW).strftime("%a %d/%m %H:%M") if r.get("scheduled_for") else "?"
        out.append(f"- [{r['status']}] {when} {r['master_theme'][:70]}")
    return "\n".join(out) or "(nic zaplanowanego)"


def _month_outline(brand_id):
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key='cm_month_outline' ORDER BY version DESC LIMIT 1",
        (brand_id,))
    return (row or {}).get("config_value") or ""


def _save_month_outline(brand_id, outline):
    if not (outline or "").strip():
        return
    try:
        db.execute(
            """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
               VALUES (%s,'cm_month_outline',%s,1,'cm-planner',NOW())
               ON CONFLICT (brand_id, config_key) DO UPDATE
                 SET config_value=EXCLUDED.config_value, version=brand_config.version+1,
                     updated_by='cm-planner', updated_at=NOW()""",
            (brand_id, outline.strip()))
    except Exception:
        pass  # brak grantu przed DDL 009 nie wywraca planu


def plan_items(brand_id="AGS"):
    """Pozycje 'proposed' w stalej kolejnosci = numeracja widoczna dla Tomasza (1..N)."""
    return db.fetchall(
        """SELECT id, master_theme, target_channels, scheduled_for FROM content_items
           WHERE brand_id=%s AND status='proposed' ORDER BY scheduled_for NULLS LAST, created_at""",
        (brand_id,))


def plan_text(brand_id="AGS"):
    items = plan_items(brand_id)
    if not items:
        return "(brak propozycji planu)"
    lines = []
    for i, it in enumerate(items, 1):
        when = it["scheduled_for"].astimezone(WARSAW).strftime("%a %d/%m %H:%M") if it.get("scheduled_for") else "?"
        ch = ",".join(it.get("target_channels") or [])
        lines.append(f"{i}. [{when}] ({ch}) {it['master_theme'][:90]}")
    return "\n".join(lines)


def build_plan(brand_id="AGS", days=7):
    """Zbuduj propozycje planu (LLM tier 'planner', wymuszone narzedzie) -> INSERT 'proposed' -> wiadomosc."""
    brand = load_brand(brand_id)
    model, tier, source = tasks.model_for("planner")
    now = datetime.datetime.now(WARSAW)
    start = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=days)
    recent = content_memory.get_published(brand_id, days_ago=14, limit=25)
    recent_txt = "\n".join(f"- {(p['content'] or '')[:80]}" for p in recent) or "(brak)"
    strat = brand.get("strategy") or {}
    msg = (
        f"Zaplanuj publikacje od {start.strftime('%A %d/%m')} do {(end - datetime.timedelta(days=1)).strftime('%A %d/%m')} "
        f"(strefa Europe/Warsaw; dzis jest {now.strftime('%A %d/%m/%Y %H:%M')}).\n\n"
        f"KADENCJA (trzymaj sie jej DOKLADNIE):\n{_cadence_text(brand_id)}\n\n"
        f"FILARY/AUDIENCE: {json.dumps({'audience': strat.get('target_audience'), 'pillars': strat.get('content_pillars'), 'topics': strat.get('core_topics')}, ensure_ascii=False)[:600]}\n\n"
        f"ZARYS MIESIACA (dotychczasowy): {_month_outline(brand_id)[:500] or '(brak - zaproponuj)'}\n\n"
        f"SCHOWEK (pomysly czekajace - wykorzystaj najlepsze):\n{_schowek_text(brand_id)}\n\n"
        f"OSTATNIE PUBLIKACJE (NIE dubluj tematow):\n{recent_txt}\n\n"
        f"JUZ ZAPLANOWANE (nie koliduj slotami):\n{_current_plan_text(brand_id)}\n\n"
        "Kazdy temat: konkretny kat, brand voice, build-in-public gdzie pasuje. Sloty rozlozone naturalnie. "
        "Niedzielny LinkedIn = format article. Wywolaj emit_plan."
    )
    resp = client().messages.create(
        model=model, max_tokens=4096,
        thinking={"type": "disabled"},
        system=[{"type": "text", "text": f"Jestes planerem tresci marki {brand_id}. Glos marki:\n{brand['voice_bible'][:3000]}"}],
        tools=[PLAN_TOOL], tool_choice={"type": "tool", "name": "emit_plan"},
        messages=[{"role": "user", "content": msg}],
    )
    tasks.log_task("planner", tier, model, source, getattr(resp, "usage", None))
    tu = next((b for b in resp.content if getattr(b, "type", "") == "tool_use" and b.name == "emit_plan"), None)
    if tu is None:
        return 0
    data = tu.input if isinstance(tu.input, dict) else {}
    items = data.get("items") or []
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []
    valid_channels = {r["channel"] for r in db.fetchall(
        "SELECT channel FROM channels WHERE brand_id=%s AND supervised=true AND status IN ('active','draft')", (brand_id,))}
    n = 0
    for it in items:
        theme = str(it.get("theme") or "").strip()
        targets = [t for t in (it.get("targets") or []) if t in valid_channels]
        if not theme or not targets:
            continue
        try:
            slot = datetime.datetime.fromisoformat(str(it.get("slot")))
            if slot.tzinfo is None:
                slot = slot.replace(tzinfo=WARSAW)
        except (ValueError, TypeError):
            continue
        if str(it.get("format") or "post") == "article":
            theme = "[ARTYKUL] " + theme
        db.execute(
            """INSERT INTO content_items (brand_id, master_theme, target_channels, status, scheduled_for)
               VALUES (%s,%s,%s,'proposed',%s)""",
            (brand_id, theme, targets, slot))
        n += 1
    _save_month_outline(brand_id, str(data.get("month_outline") or ""))
    chat = _admin_chat()
    if chat and n:
        outline = str(data.get("month_outline") or "").strip()
        head = f"📋 Propozycja planu ({n} pozycji):\n"
        if outline:
            head = f"🗓 Zarys miesiaca: {outline[:400]}\n\n" + head
        _tg_send(chat, head + plan_text(brand_id) +
                 "\n\nOdpisz: \"zatwierdz plan\" (calosc) albo edytuj: \"wywal 3\", \"przesun 2 na czwartek 14:00\", "
                 "\"zamien 5 na temat...\". Po zatwierdzeniu generuje wszystkie materialy od razu.")
    return n


def approve_plan(brand_id="AGS", except_numbers=None):
    """'proposed' -> 'planned' (calosc poza wyjatkami, ktore ida do 'rejected'). Generacja rusza od razu."""
    except_numbers = set(except_numbers or [])
    items = plan_items(brand_id)
    ok, skipped = 0, 0
    for i, it in enumerate(items, 1):
        if i in except_numbers:
            db.set_item_status(it["id"], "rejected")
            skipped += 1
        else:
            db.set_item_status(it["id"], "planned")
            ok += 1
    return ok, skipped


def edit_plan_item(brand_id, number, new_theme=None, new_slot=None, remove=False):
    items = plan_items(brand_id)
    if number < 1 or number > len(items):
        return f"Nie ma pozycji {number} (plan ma {len(items)})."
    it = items[number - 1]
    if remove:
        db.set_item_status(it["id"], "rejected")
        return f"🗑 Pozycja {number} usunieta z planu."
    if new_slot:
        try:
            slot = datetime.datetime.fromisoformat(str(new_slot))
            if slot.tzinfo is None:
                slot = slot.replace(tzinfo=WARSAW)
            db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s", (slot, it["id"]))
        except (ValueError, TypeError):
            return "Nie rozumiem terminu - podaj konkretnie."
    if new_theme:
        db.execute("UPDATE content_items SET master_theme=%s, updated_at=NOW() WHERE id=%s",
                   (str(new_theme).strip(), it["id"]))
    return f"✏️ Pozycja {number} zaktualizowana."
