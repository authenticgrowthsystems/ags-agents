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
    """Ile publikacji kanal POWINIEN miec danego dnia (kanon 11d + korekta 19/07:
    niedziela LinkedIn = 0 dla automatu - artykul niedzielny robi Tomasz RECZNIE,
    gap-filler nie ma prawa zglaszac niedzielnej luki ani jej wypelniac)."""
    if channel == "x":
        return int(str(cfg.get("posts_per_day", "3")).split("-")[0] or 3)
    if channel.startswith("linkedin"):
        return 0 if day.weekday() in (5, 6) else 1
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
    from . import planner as _pl
    strat = brand.get("strategy") or {}
    meta_left = max(0, _pl.META_MAX_WEEK - _pl._meta_week_count(brand_id))
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
                   f"ZRODLA TEMATOW - KOLEJNOSC (bramka 19/07): 1) FILARY, 2) PROBLEMY ICP, 3) schowek "
                   f"POMOCNICZO. NIE buduj tematow z ostatnich publikacji (to tylko antydubel).\n"
                   f"FILARY/ICP: {json.dumps({'audience': strat.get('target_audience'), 'pillars': strat.get('content_pillars')}, ensure_ascii=False)[:400]}\n"
                   f"BRAMKA META (twarda): tematy o naszym WLASNYM systemie publikacji (kadencja, sloty, "
                   f"kolejka, luki, wlasne narzedzia) - zostalo {meta_left} na ten tydzien; 0 = ZAKAZ. "
                   f"Incydent 13-19/07: petla postow o wlasnych lukach kadencji, 2-8 wyswietlen.\n\n"
                   f"SCHOWEK (wykorzystaj najlepsze POD FILARY):\n{sch_txt}\n\n"
                   f"OSTATNIE PUBLIKACJE (nie dubluj):\n{rec_txt}\n\n"
                   f"JUZ W KOLEJCE/SZKICACH (ZAKAZ tematow podobnych do ponizszych - nawet innym katem):\n{q_txt}\n\n"
                   f"REGULA PRAWDY: tematy WYLACZNIE na faktach ze schowka/archiwum - ZERO zmyslonych "
                   f"anegdot i wydarzen z zycia wlasciciela; brak faktu = ujecie ogolne/hipotetyczne.\n\n"
                   f"Wywolaj emit_themes."}])
    tasks.log_task("planner", tier, model, source, getattr(resp, "usage", None))
    tu = next((b for b in resp.content if getattr(b, "type", "") == "tool_use"), None)
    themes = [str(t).strip() for t in ((tu.input or {}).get("themes") or [])][:n] if tu else []
    made = 0
    meta_budget = meta_left
    for theme in themes:
        if not theme:
            continue
        if _pl._meta_like(theme):  # twarda bramka za promptem
            if meta_budget <= 0:
                continue
            meta_budget -= 1
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
    hold = _state_get("cm_hold_today")  # STOP awaryjny (12/07): 'nic dzis nie publikuj' wycisza tez luki
    for r in rows:
        for offset in (0, 1):
            day = (now + datetime.timedelta(days=offset)).date()
            if offset == 0 and now.hour >= 19:
                continue  # dnia praktycznie nie ma juz jak wypelnic
            if offset == 0 and hold.get("date") == day.isoformat():
                continue  # Tomasz zatrzymal dzisiejsze publikacje - nie proponuj wypelniania dzis
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


DECIDE_TOOL = {
    "name": "emit_decision",
    "description": "Decyzja CM w sprawie propozycji subagenta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "approve": {"type": "boolean"},
            "slot_grid": {"type": ["array", "null"], "items": {"type": "string"},
                          "description": "Zatwierdzona siatka godzin HH:MM (moze byc zmodyfikowana), null gdy odmowa/nie dotyczy."},
            "needs_human": {"type": ["boolean", "null"],
                            "description": ("true gdy prosba wymaga ZASOBU albo DECYZJI Tomasza, ktorych CM sam "
                                            "nie przyzna: dostep do danych/metryk, dane o odbiorcach, budzet, "
                                            "konto/API, integracja. Wtedy NIE odrzucaj - przekażemy Tomaszowi.")},
            "reply": {"type": "string", "description": "Krotka odpowiedz CM do subagenta (po polsku)."},
        },
        "required": ["approve", "reply"],
    },
}


def _log_channel_need(brand_id, channel, topic, proposal, reply):
    """Realna potrzeba subagenta (dane/dostep/budzet), ktorej CM sam nie przyzna -> agent_logs
    CHANNEL_NEED (widoczna w raportach, nie ginie w golym ODRZUCONE). Decyzja Tomasza 06/07 wieczor."""
    try:
        db.execute(
            "INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES (%s,'CHANNEL_NEED',%s,%s::jsonb)",
            (f"{brand_id}:{channel}", (proposal or "")[:400],
             json.dumps({"topic": topic, "cm_reply": (reply or "")[:400], "channel": channel},
                        ensure_ascii=False)))
    except Exception:
        pass


def handle_agent_requests(brand_id="AGS"):
    """AGENCI GADAJA MIEDZY SOBA (Tomasz 06/07: 'on ma to zalatwic z CM sam'): CM czyta
    nieprzeczytane agent_messages typu channel_proposal, DECYDUJE (LLM z kontekstem kadencji),
    wpisuje config, odpowiada subagentowi (response) i melduje Tomaszowi na bocie logowym."""
    from .brand import load_brand
    from .generate import client
    from . import logbot
    cm_id = _agent_id("%content-manager%")
    if not cm_id:
        return
    reqs = db.fetchall(
        """SELECT message_id, from_agent_id, payload FROM agent_messages
           WHERE to_agent_id=%s AND status='unread' AND message_type='request'
             AND payload->>'kind'='channel_proposal' LIMIT 3""", (cm_id,))
    for rq in reqs:
        p = rq["payload"] if isinstance(rq["payload"], dict) else json.loads(rq["payload"])
        db.execute("UPDATE agent_messages SET status='processing', read_at=NOW() WHERE message_id=%s",
                   (rq["message_id"],))
        try:
            brand = load_brand(brand_id)
            ch_row = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s",
                                 (brand_id, p.get("channel")))
            model, tier, source = tasks.model_for("planner")
            resp = client().messages.create(
                model=model, max_tokens=400, thinking={"type": "disabled"},
                system=[{"type": "text", "text": f"Jestes Content Managerem marki {brand_id} - decydujesz "
                                                 f"o strategii kanalow. Kadencja kanoniczna: X 3-5/dzien "
                                                 f"w oknie publikacji; publicznosc AGS = USA/UK. Rozrozniaj: "
                                                 f"STRATEGIA kanalu (siatka/kadencja/okno) = decydujesz sam; "
                                                 f"ZASOB albo decyzja Tomasza (dane o odbiorcach, dostep do "
                                                 f"metryk, budzet, konto, API) = NIE odrzucaj, ustaw "
                                                 f"needs_human=true i przekażemy to Tomaszowi."}],
                tools=[DECIDE_TOOL], tool_choice={"type": "tool", "name": "emit_decision"},
                messages=[{"role": "user", "content":
                           f"Subagent kanalu {p.get('channel')} proponuje ({p.get('topic')}):\n"
                           f"{p.get('proposal', '')[:500]}\n\n"
                           f"Obecna konfiguracja celu: {json.dumps((ch_row or {}).get('config') or {}, ensure_ascii=False)[:400]}\n"
                           f"Ocen propozycje i wywolaj emit_decision. Jesli zatwierdzasz siatke slotow, podaj "
                           f"godziny HH:MM. Jesli subagent prosi o ZASOB/dane/dostep, ktorych sam nie masz - "
                           f"needs_human=true (nie gole ODRZUCONE)."}])
            tasks.log_task("planner", tier, model, source, getattr(resp, "usage", None))
            tu = next((b for b in resp.content if getattr(b, "type", "") == "tool_use"), None)
            dec = (tu.input if tu else {}) or {}
            applied = ""
            need_human = bool(dec.get("needs_human"))
            if dec.get("approve") and p.get("topic") == "slot_grid" and dec.get("slot_grid"):
                db.execute("UPDATE channels SET config = config || %s::jsonb WHERE brand_id=%s AND channel=%s",
                           (json.dumps({"slot_grid": dec["slot_grid"]}), brand_id, p.get("channel")))
                applied = f" Siatka wpisana do configu: {', '.join(dec['slot_grid'])}."
            if need_human:
                # decyzja Tomasza 06/07 wieczor: realna potrzeba subagenta (dane/dostep/budzet) NIE ginie
                # w golym ODRZUCONE - CM loguje ja i przekazuje Tomaszowi (widoczna w raportach).
                _log_channel_need(brand_id, p.get("channel"), p.get("topic"),
                                  p.get("proposal", ""), dec.get("reply", ""))
            db.execute(
                """INSERT INTO agent_messages (from_agent_id, to_agent_id, message_type, payload, correlation_id)
                   VALUES (%s,%s,'response',%s,%s)""",
                (cm_id, rq["from_agent_id"],
                 json.dumps({"kind": "channel_proposal_reply", "channel": p.get("channel"),
                             "approve": bool(dec.get("approve")), "reply": dec.get("reply", ""),
                             "slot_grid": dec.get("slot_grid"), "routed_to_human": need_human}), rq["message_id"]))
            db.execute("UPDATE agent_messages SET status='done' WHERE message_id=%s", (rq["message_id"],))
            if need_human:
                logbot.send(f"📌 SUBAGENT[{p.get('channel')}] POTRZEBUJE (do decyzji Tomasza): "
                            f"{p.get('proposal', '')[:200]}\n   CM: {dec.get('reply', '')[:200]}")
                # domkniecie petli W CZACIE - ale jako PRZEKAZANIE, nie odmowa
                _send(f"📌 [{p.get('channel')}] Zglaszam Tomaszowi potrzebe do JEGO decyzji: "
                      f"{p.get('proposal', '')[:220]}\n   CM: {dec.get('reply', '')[:220]}\n"
                      f"   (zapisane w logu, wroci w raporcie - nie odrzucone).")
            else:
                logbot.send(f"🤝 CM<->[{p.get('channel')}] {p.get('topic')}: "
                            f"{'ZATWIERDZONE' if dec.get('approve') else 'ODRZUCONE'} - "
                            f"{dec.get('reply', '')[:200]}{applied}")
                # domkniecie petli W CZACIE (feedback 06/07): subagent melduje wynik Tomaszowi
                _send(f"📣 [{p.get('channel')}] CM odpowiedzial na moja propozycje ({p.get('topic')}): "
                      f"{'✅ ZATWIERDZONE' if dec.get('approve') else '❌ ODRZUCONE'}. "
                      f"{dec.get('reply', '')[:250]}{applied}")
        except Exception as e:
            msg = str(e)
            transient = any(s in msg for s in ("529", "overloaded", "Overloaded", "rate_limit", "429",
                                               "500", "502", "503", "Timeout", "timeout", "Connection", "APIStatus"))
            attempts = int(p.get("_attempts") or 0) + 1
            if transient and attempts < 6:
                # fix 07/08: API przeciazone/limit (529 overloaded) NIE gubi propozycji - ponow w nastepnym ticku (60s)
                p["_attempts"] = attempts
                db.execute("UPDATE agent_messages SET status='unread', read_at=NULL, payload=%s WHERE message_id=%s",
                           (json.dumps(p, ensure_ascii=False), rq["message_id"]))
                print(f"[cm] agent_request transient error (proba {attempts}), ponawiam: {msg[:120]}", flush=True)
            else:
                db.execute("UPDATE agent_messages SET status='failed' WHERE message_id=%s", (rq["message_id"],))
                logbot.send(f"⚠️ CM nie rozpatrzyl propozycji subagenta ({p.get('topic')}) po {attempts} probach: {msg[:150]}")


def weekly_metrics_reminder(brand_id="AGS"):
    """Poniedzialek 09:30-11:30: subagent x UPOMINA SIE o metryki tygodnia (decyzja Tomasza 06/07:
    recznie raz w tygodniu; wpis przez rozmowe z subagentem, narzedzie subagent_set_metrics).
    20/07: monit TYLKO gdy cel realnie potrzebuje wpisu recznego (stats_mode='manual') - kolektor
    Owned Reads zbiera X sam, a przypomnienie i tak wyszlo (relikt; zgloszenie Tomasza 10:10)."""
    ch = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel='x'", (brand_id,))
    if ((ch or {}).get("config") or {}).get("stats_mode", "manual") != "manual":
        return
    now = datetime.datetime.now(WARSAW)
    if now.weekday() != 0:
        return
    minutes = now.hour * 60 + now.minute
    if not (9 * 60 + 30 <= minutes <= 11 * 60 + 30):
        return
    week = now.strftime("%G-%V")
    st = _state_get("cm_metrics_reminder")
    if st.get("week") == week:
        return
    pub = db.fetchall(
        """SELECT id, left(content, 60) AS c FROM post_queue
           WHERE brand=%s AND platform='x' AND status='published'
             AND published_at > NOW() - interval '8 days' ORDER BY id DESC LIMIT 10""", (brand_id,)) \
        if _column_exists("post_queue", "published_at") else db.fetchall(
        """SELECT id, left(content, 60) AS c FROM post_queue
           WHERE brand=%s AND platform='x' AND status='published' ORDER BY id DESC LIMIT 10""", (brand_id,))
    lst = "\n".join(f"- #{r['id']} {r['c']}" for r in pub) or "(brak publikacji)"
    _send(f"🐦 [x] Poniedzialkowa prosba subagenta: wgraj metryki zeszlego tygodnia.\n"
          f"Przelacz /agents na AGS x i wpisz np. \"metryki #34: impressions 250, engagement 12\".\n"
          f"Publikacje:\n{lst}")
    _state_set("cm_metrics_reminder", {"week": week})


def _column_exists(table, col):
    r = db.fetchone("SELECT 1 AS x FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
                    (table, col))
    return bool(r)


def tick():
    """Wolane z petli workera (30s); wszystkie funkcje maja wlasne anty-spam stany."""
    for fn in (check_gaps, morning_nudge, handle_agent_requests, weekly_metrics_reminder):
        try:
            fn()
        except Exception:
            import traceback
            traceback.print_exc()
