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
        win = cfg.get("publish_windows")  # okno per cel (decyzja 06/07), zmienialne przez target_update
        if r["channel"] == "x":
            lines.append(f"- x: {cfg.get('posts_per_day', '3-5')} postow DZIENNIE, "
                         f"WYLACZNIE w oknie {win or '09:00-21:00'}")
        elif r["channel"].startswith("linkedin"):
            # FIX 07/07: NIE hardkoduj 10:00 - to przeczylo oknu US 13:00-18:00 (LLM bral jawne 10:00).
            # Czas WYPROWADZAMY z okna publikacji celu (strefa odbiorcow).
            w = win or "08:00-18:00"
            start = w.split("-")[0].strip()
            lines.append(f"- {r['channel']}: poniedzialek-piatek 1 post, sobota NIC, niedziela ARTYKUL "
                         f"(format article); publikuj WYLACZNIE w oknie {w} (proponuj godzine od {start}, "
                         f"NIGDY przed {start} - to okno strefy czasowej odbiorcow tego celu)")
        else:
            lines.append(f"- {r['channel']}: {json.dumps(cfg.get('weekly_pattern', 'wg uznania'), ensure_ascii=False)}"
                         + (f"; okno {win}" if win else ""))
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


_DAYS_PL = ["Poniedzialek", "Wtorek", "Sroda", "Czwartek", "Piatek", "Sobota", "Niedziela"]


def _target_label(brand_id, ch):
    """Czytelne oznaczenie celu (feedback Tomasza 04/07): kanal + KTORA marka/profil."""
    if ch == "x":
        return f"🐦X-{brand_id}" if brand_id != "AGS" else "🐦X"
    if ch == "linkedin" and brand_id == "AGS":
        return "💼LI-profil"
    if ch.startswith("linkedin"):
        return f"🏢LI-{brand_id}"
    return f"📣{ch}-{brand_id}"


def plan_text(brand_id="AGS"):
    """Plan grupowany po DNIACH, pelne tematy, emoji kanalow (split >4096 robi warstwa wysylki)."""
    items = plan_items(brand_id)
    if not items:
        return "(brak propozycji planu)"
    lines = []
    last_day = None
    for i, it in enumerate(items, 1):
        dt = it["scheduled_for"].astimezone(WARSAW) if it.get("scheduled_for") else None
        if dt and dt.date() != last_day:
            lines.append("")
            lines.append(f"——— {_DAYS_PL[dt.weekday()]} {dt.strftime('%d/%m')} ———")
            last_day = dt.date()
        ch = " + ".join(_target_label(brand_id, c) for c in (it.get("target_channels") or []))
        hhmm = dt.strftime("%H:%M") if dt else "??:??"
        lines.append(f"{i}. {hhmm} | {ch}")
        lines.append(f"    {it['master_theme']}")
    return "\n".join(lines).strip()


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
        "Niedzielny LinkedIn = format article. REGULA PRAWDY: tematy WYLACZNIE na faktach ze schowka/"
        "strategii/archiwum - ZERO zmyslonych anegdot, wydarzen i liczb z zycia wlasciciela; brak faktu = "
        "ujecie ogolne albo jawnie hipotetyczne. Wywolaj emit_plan."
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
                 "\n\nSteruj guzikami ponizej albo rozmowa: \"wywal 3\", \"przesun 2 na czwartek 14:00\", "
                 "\"zamien 5 na temat...\".")
        send_plan_controls(chat, brand_id)
    return n


# ---------------- nawigacja zatwierdzania (krok 2, plannav:) ----------------
def _tg(method, payload):
    from . import conversation
    return conversation._tg(method, payload)


def send_plan_controls(chat_id, brand_id="AGS"):
    """Osobna krotka wiadomosc z guzikami sterowania planem (tekst planu moze byc dzielony na czesci,
    wiec guziki jada oddzielnie - zawsze na wierzchu)."""
    n = len(plan_items(brand_id))
    if not n:
        return
    kb = {"inline_keyboard": [
        [{"text": f"✅ Zatwierdz wszystkie ({n})", "callback_data": "plannav:all:-"}],
        [{"text": "🔍 Przegladaj po kolei", "callback_data": "plannav:first:-"}],
    ]}
    _tg("sendMessage", {"chat_id": chat_id, "text": "Sterowanie planem:", "reply_markup": kb})


def _nav_card_payload(brand_id, item_id=None):
    """(text, keyboard) karty pozycji: item_id=None -> pierwsza 'proposed'."""
    items = plan_items(brand_id)
    if not items:
        return "📋 Przeglad zakonczony - brak pozycji do decyzji. Zatwierdzone poszly do produkcji.", None
    idx = 0
    if item_id:
        for i, it in enumerate(items):
            if str(it["id"]) == str(item_id):
                idx = i
                break
    it = items[idx]
    dt = it["scheduled_for"].astimezone(WARSAW) if it.get("scheduled_for") else None
    when = f"{_DAYS_PL[dt.weekday()]} {dt.strftime('%d/%m %H:%M')}" if dt else "brak slotu"
    ch = " + ".join(_target_label(brand_id, c) for c in (it.get("target_channels") or []))
    text = (f"📋 Pozycja {idx + 1} z {len(items)} (status: czeka na decyzje)\n\n"
            f"🕐 {when}\n📣 {ch}\n\n{it['master_theme']}")
    iid = str(it["id"])
    # zawijanie jak w matnav (fix 06/07)
    prev_id = str(items[(idx - 1) % len(items)]["id"])
    next_id = str(items[(idx + 1) % len(items)]["id"])
    kb = {"inline_keyboard": [
        [{"text": "✅ Zatwierdz", "callback_data": f"plannav:ok:{iid}"},
         {"text": "❌ Odrzuc", "callback_data": f"plannav:no:{iid}"},
         {"text": "🔄 Inny kat", "callback_data": f"plannav:angle:{iid}"}],
        [{"text": "⬅️", "callback_data": f"plannav:show:{prev_id}"},
         {"text": f"{idx + 1}/{len(items)}", "callback_data": "plannav:pos:-"},
         {"text": "➡️", "callback_data": f"plannav:show:{next_id}"}],
        [{"text": f"✅ Zatwierdz WSZYSTKIE pozostale ({len(items)})", "callback_data": "plannav:all:-"}],
    ]}
    return text, kb


def _next_after(brand_id, item_id):
    """Po decyzji o item_id: id kolejnej czekajacej pozycji (do plynnego przegladu)."""
    items = plan_items(brand_id)
    return str(items[0]["id"]) if items else None


def _reangle_theme(item_id, brand_id="AGS"):
    """'Inny kat': przeformulowanie tematu pozycji (LLM, tier plan_angle->sonnet default z routera)."""
    row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (item_id,))
    if not row:
        return False
    brand = load_brand(brand_id)
    model, tier, source = tasks.model_for("plan_angle")
    resp = client().messages.create(
        model=model, max_tokens=300, thinking={"type": "disabled"},
        system=[{"type": "text", "text": f"Glos marki (skrot):\n{brand['voice_bible'][:1500]}"}],
        messages=[{"role": "user", "content":
                   f"Przeformuluj temat posta na INNY, swiezy kat (ta sama esencja, inna perspektywa). "
                   f"Zachowaj ewentualny prefiks [ARTYKUL]. Zwroc TYLKO nowy temat.\n\n{row['master_theme']}"}])
    tasks.log_task("plan_angle", tier, model, source, getattr(resp, "usage", None), item_id)
    new_theme = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    if not new_theme:
        return False
    db.execute("UPDATE content_items SET master_theme=%s, updated_at=NOW() WHERE id=%s", (new_theme, item_id))
    return True


def handle_nav(payload, wake_event=None):
    """Obsluga callbackow plannav:<akcja>:<arg> (n8n = czysty transport). Edytuje karte w miejscu."""
    raw = str(payload.get("raw") or "")
    chat_id = payload.get("chat_id")
    message_id = payload.get("message_id")
    parts = raw.split(":", 2)
    action = parts[1] if len(parts) > 1 else ""
    arg = parts[2] if len(parts) > 2 else ""
    brand_id = "AGS"

    def edit(text, kb=None):
        body = {"chat_id": chat_id, "message_id": message_id, "text": text[:4000]}
        if kb:
            body["reply_markup"] = kb
        r = _tg("editMessageText", body)
        if not (r and r.get("ok")):
            if "not modified" in str((r or {}).get("description", "")):
                return  # ta sama tresc - nie duplikuj karty (fix 06/07)
            _tg("sendMessage", {"chat_id": chat_id, "text": text[:4000], **({"reply_markup": kb} if kb else {})})

    if action == "pos":
        return
    if action == "all":
        ok, _ = approve_plan(brand_id)
        if wake_event:
            wake_event.set()
        edit(f"✅ Plan zatwierdzony w calosci: {ok} pozycji poszlo do produkcji. Materialy przyjda po kolei; "
             "NIC nie publikuje sie bez tapniecia (kanon 19/07) - po 24h ciszy przypomnienie guzikami.")
        return
    if action == "first":
        text, kb = _nav_card_payload(brand_id)
        edit(text, kb)
        return
    if action == "show":
        text, kb = _nav_card_payload(brand_id, arg)
        edit(text, kb)
        return
    if action in ("ok", "no"):
        db.set_item_status(arg, "planned" if action == "ok" else "rejected")
        if action == "ok" and wake_event:
            wake_event.set()
        nxt = _next_after(brand_id, arg)
        if nxt:
            text, kb = _nav_card_payload(brand_id, nxt)
            head = "✅ Zatwierdzona -> produkcja.\n\n" if action == "ok" else "❌ Odrzucona.\n\n"
            edit(head + text, kb)
        else:
            edit("📋 Przeglad zakonczony - wszystkie pozycje rozstrzygniete. Zatwierdzone sa w produkcji.")
        return
    if action == "angle":
        if _reangle_theme(arg, brand_id):
            text, kb = _nav_card_payload(brand_id, arg)
            edit("🔄 Nowy kat:\n\n" + text, kb)
        else:
            edit("Nie udalo sie przeformulowac - sprobuj jeszcze raz.")
        return


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
