# -*- coding: utf-8 -*-
"""SUBAGENT-PRACOWNIK + SEMI-AUTO (decyzje Tomasza 06/07, autonomia BE).
(A) Subagent pilnuje SWOJEJ kadencji: widzi luke w slotach dzis/jutro -> ZGLASZA CM przez
    agent_messages (kontrakt agent->agent, ledger) -> CM proponuje tematy (LLM: schowek + pamiec
    publikacji) -> Tomasz dostaje intake z guzikami [Do kolejki]/[Dzis]/[Odrzuc] per propozycja.
(B) Semi-auto zaczepki CM (kanon 10, brand_config cm_work_mode='semi'|'auto'): poranna odprawa -
    jedna wiadomosc: co czeka na decyzje (karty/intake/plan) + guzik przegladu.
Anty-spam: max 1 zgloszenie luki per kanal/dzien, max 1 odprawa/dzien (stan w brand_config)."""
import datetime
import json
from zoneinfo import ZoneInfo

from . import db, tasks, content_memory
from .matreview import _state_get, _state_set, send_intake_buttons, pending_items

WARSAW = ZoneInfo("Europe/Warsaw")
ACTIVE_FOR_SLOTS = ("planned", "drafting", "needs_approval", "approved", "dispatching")
NUDGE_WINDOW = (9, 0, 11, 30)   # odprawa poranna miedzy 09:00 a 11:30
PROPOSALS_PER_GAP = 2

PROPOSE_TOOL = {
    "name": "emit_themes",
    "description": "Zwroc propozycje tematow do publikacji jako strukture.",
    "input_schema": {
        "type": "object",
        "properties": {"themes": {"type": "array", "items": {"type": "string"},
                                  "description": "Tematy-matki z konkretnym katem narracji, po polsku."}},
        "required": ["themes"],
    },
}


def _work_mode():
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='cm_work_mode'")
    return (r or {}).get("config_value") or "supervised"


def _admin_chat():
    from . import hitl
    return hitl._admin_chat_id()


def _send(text, kb=None):
    from . import conversation
    chat = _admin_chat()
    if not chat:
        return False
    body = {"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}
    if kb:
        body["reply_markup"] = kb
    r = conversation._tg("sendMessage", body)
    return bool(r and r.get("ok"))


# ---------------- (A) luka w kadencji -> subagent wola CM ----------------
def _expected(channel, cfg, day):
    """Ile publikacji kanal POWINIEN miec danego dnia (kanon 11d)."""
    if channel == "x":
        return int(str(cfg.get("posts_per_day", "3")).split("-")[0] or 3)
    if channel.startswith("linkedin"):
        return 0 if day.weekday() == 5 else 1
    return 0


def _scheduled(brand_id, channel, day):
    day_start = datetime.datetime.combine(day, datetime.time(0, 0), WARSAW)
    r = db.fetchone(
        """SELECT COUNT(*) AS n FROM content_items
           WHERE brand_id=%s AND %s = ANY(target_channels) AND status = ANY(%s)
             AND scheduled_for >= %s AND scheduled_for < %s""",
        (brand_id, channel, list(ACTIVE_FOR_SLOTS), day_start, day_start + datetime.timedelta(days=1)))
    return (r or {}).get("n") or 0


def _agent_id(name_like):
    r = db.fetchone("SELECT agent_id FROM agent_registry WHERE agent_name ILIKE %s ORDER BY created_at LIMIT 1",
                    (name_like,))
    return r["agent_id"] if r else None


def _ledger_gap(channel, day, missing):
    """Kontrakt agent->agent: zgloszenie luki do agent_messages (best-effort - brak wpisu w
    agent_registry nie blokuje mechanizmu, zostaje log w stanie)."""
    try:
        sub, cm = _agent_id(f"%{channel.split('_')[0]}%"), _agent_id("%content-manager%")
        if sub and cm:
            db.execute(
                """INSERT INTO agent_messages (from_agent_id, to_agent_id, message_type, payload)
                   VALUES (%s,%s,'request',%s)""",
                (sub, cm, json.dumps({"kind": "cadence_gap", "channel": channel,
                                      "day": day.isoformat(), "missing": missing})))
    except Exception:
        pass


def _propose_for_gap(brand_id, channel, day, missing):
    """CM: propozycje tematow pod luke (schowek + pamiec antydubel) -> content_items 'draft'
    -> intake z guzikami do Tomasza."""
    from .brand import load_brand
    from .generate import client
    brand = load_brand(brand_id)
    schowek = db.fetchall(
        "SELECT id, content FROM inspirations WHERE status='new' ORDER BY created_at DESC LIMIT 10")
    sch_txt = "\n".join(f"- (schowek #{r['id']}) {(r['content'] or '')[:90]}" for r in schowek) or "(pusty)"
    recent = content_memory.get_published(brand_id, days_ago=14, limit=15)
    rec_txt = "\n".join(f"- {(p['content'] or '')[:70]}" for p in recent) or "(brak)"
    # ANTYDUBEL (incydent 06/07: dwie wariacje 'Tolerance of difficulty'): propozycja MUSI omijac
    # tematy juz czekajace w kolejce i szkicach
    queued = db.fetchall(
        """SELECT master_theme FROM content_items WHERE brand_id=%s
           AND status IN ('draft','proposed','planned','drafting','needs_approval','approved')
           ORDER BY updated_at DESC LIMIT 40""", (brand_id,))
    q_txt = "\n".join(f"- {(r['master_theme'] or '')[:80]}" for r in queued) or "(pusto)"
    model, tier, source = tasks.model_for("planner")
    n = min(missing, PROPOSALS_PER_GAP)
    resp = client().messages.create(
        model=model, max_tokens=600, thinking={"type": "disabled"},
        system=[{"type": "text", "text": f"Jestes CM marki {brand_id}. Glos marki (skrot):\n{brand['voice_bible'][:1500]}"}],
        tools=[PROPOSE_TOOL], tool_choice={"type": "tool", "name": "emit_themes"},
        messages=[{"role": "user", "content":
                   f"Subagent kanalu {channel} zglasza luke w kadencji: {day.strftime('%A %d/%m')} brakuje "
                   f"{missing} publikacji. Zaproponuj DOKLADNIE {n} tematy-matki (konkretny kat, brand voice, "
                   f"build-in-public gdzie pasuje). Pisz NIENAGANNA polszczyzna.\n\n"
                   f"SCHOWEK (wykorzystaj najlepsze):\n{sch_txt}\n\n"
                   f"OSTATNIE PUBLIKACJE (nie dubluj):\n{rec_txt}\n\n"
                   f"JUZ W KOLEJCE/SZKICACH (ZAKAZ tematow podobnych do ponizszych - nawet innym katem):\n{q_txt}\n\n"
                   f"Wywolaj emit_themes."}])
    tasks.log_task("planner", tier, model, source, getattr(resp, "usage", None))
    tu = next((b for b in resp.content if getattr(b, "type", "") == "tool_use"), None)
    themes = [str(t).strip() for t in ((tu.input or {}).get("themes") or [])][:n] if tu else []
    made = 0
    for theme in themes:
        if not theme:
            continue
        row = db.fetchone(
            """INSERT INTO content_items (brand_id, master_theme, target_channels, status)
               VALUES (%s,%s,%s,'draft') RETURNING id""", (brand_id, theme, [channel]))
        send_intake_buttons(row["id"], theme)
        made += 1
    return made


def check_gaps(brand_id="AGS"):
    """Petla workera: kazdy supervised aktywny kanal sprawdza SWOJA kadencje na dzis+jutro."""
    now = datetime.datetime.now(WARSAW)
    rows = db.fetchall(
        "SELECT channel, config FROM channels WHERE brand_id=%s AND supervised=true AND status='active'",
        (brand_id,))
    st = _state_get("cm_gap_alerts")
    changed = False
    for r in rows:
        for offset in (0, 1):
            day = (now + datetime.timedelta(days=offset)).date()
            if offset == 0 and now.hour >= 19:
                continue  # dnia praktycznie nie ma juz jak wypelnic
            key = f"{r['channel']}:{day.isoformat()}"
            if st.get(key):
                continue
            missing = _expected(r["channel"], r.get("config") or {}, day) - _scheduled(brand_id, r["channel"], day)
            if missing <= 0:
                continue
            _ledger_gap(r["channel"], day, missing)
            made = _propose_for_gap(brand_id, r["channel"], day, missing)
            _send(f"🔔 Subagent [{r['channel']}] zglasza luke w kadencji: {day.strftime('%a %d/%m')} "
                  f"brakuje {missing} publikacji. Wyslalem {made} propozycje - decyzje guzikami powyzej. "
                  f"Nie pasuja? Napisz do CM, wymyslimy inne.")
            st[key] = now.isoformat()
            changed = True
    if changed:
        # stan trzyma tylko biezacy tydzien (sprzatanie starych kluczy)
        cutoff = (now - datetime.timedelta(days=7)).date().isoformat()
        _state_set("cm_gap_alerts", {k: v for k, v in st.items() if k.split(":")[1] >= cutoff})


# ---------------- (B) semi-auto: poranna odprawa ----------------
def morning_nudge(brand_id="AGS"):
    if _work_mode() not in ("semi", "auto"):
        return
    now = datetime.datetime.now(WARSAW)
    h1, m1, h2, m2 = NUDGE_WINDOW
    minutes = now.hour * 60 + now.minute
    if not (h1 * 60 + m1 <= minutes <= h2 * 60 + m2):
        return
    today = now.strftime("%Y-%m-%d")
    st = _state_get("cm_morning_nudge")
    if st.get("date") == today:
        return
    cards = len(pending_items(brand_id))
    drafts = db.fetchone("SELECT COUNT(*) AS n FROM content_items WHERE brand_id=%s AND status='draft'",
                         (brand_id,))["n"]
    proposed = db.fetchone("SELECT COUNT(*) AS n FROM content_items WHERE brand_id=%s AND status='proposed'",
                           (brand_id,))["n"]
    if not (cards or drafts or proposed):
        _state_set("cm_morning_nudge", {"date": today})
        return
    lines = ["☕ Odprawa poranna CM:"]
    if cards:
        lines.append(f"- {cards} materialow czeka na przeglad (karty)")
    if drafts:
        lines.append(f"- {drafts} pomyslow czeka na decyzje intake (Kolejka/Dzis/Odrzuc)")
    if proposed:
        lines.append(f"- {proposed} pozycji planu czeka na akceptacje")
    lines.append("Co odblokowac najpierw? Moge tez cos przesunac albo dorzucic tematy - napisz.")
    kb = {"inline_keyboard": [[{"text": f"🔍 Przegladaj materialy ({cards})", "callback_data": "matnav:first:-"}]]} \
        if cards else None
    _send("\n".join(lines), kb)
    _state_set("cm_morning_nudge", {"date": today})


def tick():
    """Wolane z petli workera (30s); wszystkie funkcje maja wlasne anty-spam stany."""
    try:
        check_gaps()
    except Exception:
        import traceback
        traceback.print_exc()
    try:
        morning_nudge()
    except Exception:
        import traceback
        traceback.print_exc()
