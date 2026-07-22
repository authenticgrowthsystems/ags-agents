"""Konsument kolejki komentarzy (task_queue task_type='comment') - wariant A semi-auto
(decyzja Managera 10/07, P2 z ZAPYTANIA 09/07) + straznik domykania petli (BE-ENGAGEMENT 20/07).

Zatwierdzony guzikiem [Zatwierdz] komentarz NIE wisi juz jako pending: konsument wysyla Tomaszowi
GOTOWIEC (propozycja + post zrodlowy + kontekst CRM autora) z guzikami odhaczenia. Publikacja
przez API celowo NIE: X write pod cudzymi postami = ryzyko tieru, LinkedIn comment API po App 2
CMA - wklejka reczna jest bezpieczna i natychmiastowa. Guziki cmt:done|skip jada istniejaca
galezia cmt: -> POST /cmt.

STRAZNIK (kanon 19/07, wzorzec _stale_approval_watch): NIC nie ginie i NIC nie zgadujemy.
1) Propozycja bez decyzji >24h (engagement_log status='proposed') -> decyzja guzikami
   [Wyslalem][Pomin][Pokaz jeszcze raz] (decision_type='stale_comment').
2) Zatwierdzona-a-niepotwierdzona >24h (task_queue comment in_progress) -> "wyslales komentarz
   do X?" [Tak, odhacz][Nie, pomin] (decision_type='stale_comment_task').
Throttle w DB jak w stale_approval: jedna otwarta/swieza decyzja per wiersz."""
import datetime
import hashlib
import re
import traceback

from psycopg.types.json import Jsonb

from . import db, decisions, hitl
from .conversation import _tg

_BATCH = 5  # ile zadan na tick (anty-flood)


def consumer_tick():
    """Petla workera: kazde pending zadanie 'comment' -> gotowiec do Tomasza + guziki -> in_progress."""
    try:
        rows = db.fetchall(
            """SELECT id, agent_id, payload, created_at FROM task_queue
               WHERE task_type='comment' AND status='pending'
               ORDER BY created_at LIMIT %s""", (_BATCH,))
    except Exception:
        traceback.print_exc()
        return
    if not rows:
        return
    chat = hitl._admin_chat_id()
    if not chat:
        return
    for r in rows:
        p = r.get("payload") or {}
        src = (p.get("source_post") or "").strip()
        props = (p.get("proposals") or "").strip()
        author = (p.get("author") or "").strip()
        ctx = None
        if p.get("contact_id"):  # BE-ENGAGEMENT 20/07: gotowiec pokazuje kontekst relacji
            from . import crm
            ctx = crm.relation_context(p["contact_id"])
        is_dm = (p.get("kind") == "dm")  # INTAKE-UX 21/07: odpowiedzi na DM jada tym samym torem
        text = (("✉️ ODPOWIEDZ NA DM DO WYSLANIA" if is_dm else "🧾 KOMENTARZ DO WKLEJENIA")
                + f" - konto {r['agent_id']}\n"
                + (f"AUTOR: {author}" + (f" ({ctx})" if ctx else "") + "\n\n" if author else "\n")
                + ((f"W WATKU:\n{src[:400]}\n\n" if is_dm else f"POD POSTEM:\n{src[:400]}\n\n") if src else "")
                + f"PROPOZYCJA (skopiuj i wklej w aplikacji):\n{props[:2800]}\n\n"
                "Po wklejeniu odhacz guzikiem - wykonanie zapisze sie w pamieci konta i na kontakcie.")
        kb = {"inline_keyboard": [[
            {"text": "✅ Wkleilem", "callback_data": f"cmt:done:{r['id']}"},
            {"text": "⏭ Pomin", "callback_data": f"cmt:skip:{r['id']}"},
        ]]}
        resp = _tg("sendMessage", {"chat_id": chat, "text": text[:4000], "reply_markup": kb,
                                   "disable_web_page_preview": True})
        if resp and resp.get("ok"):
            db.execute("UPDATE task_queue SET status='in_progress' WHERE id=%s::uuid", (str(r["id"]),))
        else:
            # Telegram nie przyjal - zostaw pending, sprobujemy w nastepnym ticku; nie zalewaj dalej
            break


def stale_watch():
    """Wolane z petli workera. Przypomnienia guzikami po 24h ciszy (zero zgadywania)."""
    try:
        _watch_proposed()
        _watch_in_progress()
    except Exception:
        traceback.print_exc()


def _watch_proposed():
    rows = db.fetchall(
        """SELECT id, agent, author_display FROM engagement_log
           WHERE status='proposed' AND created_at < NOW() - interval '24 hours'
           ORDER BY created_at LIMIT 5""")
    for r in rows:
        eid = str(r["id"])
        agent = r.get("agent") or "AGS:x"
        who = r.get("author_display") or "(autor ze zrzutu)"
        # 22/07 (incydent decyzja #14): outreach SPRZEDAWCY to nie komentarz - inny gatunek,
        # inne guziki, ZERO maszynerii komentarzy/intake'u ("Dam zrzut profilu" przy prospekcie
        # przebadanym przez strone to herezja). Zrodlem prawdy o prospekcie jest sales_pipeline.
        if agent.endswith(":sprzedaz"):
            if db.fetchone(
                    """SELECT 1 AS x FROM agent_decisions
                       WHERE decision_type='stale_outreach' AND context->>'engagement_id'=%s
                         AND (status='pending' OR answered_at > NOW() - interval '24 hours') LIMIT 1""",
                    (eid,)):
                continue
            decisions.ask(
                agent, agent.split(":")[0], "stale_outreach",
                f"Gotowiec outreach do {who} czeka na wyslanie ponad 24h. Co z nim?",
                [{"key": "sent", "label": "Wyslalem (odhacz)"},
                 {"key": "wait", "label": "Czekam (przypomnij jutro)"},
                 {"key": "show", "label": "Pokaz tresc"},
                 {"key": "drop", "label": "Rezygnuje"}],
                recommendation=None, context={"engagement_id": eid})
            continue
        if db.fetchone(
                """SELECT 1 AS x FROM agent_decisions
                   WHERE decision_type='stale_comment' AND context->>'engagement_id'=%s
                     AND (status='pending' OR answered_at > NOW() - interval '24 hours') LIMIT 1""",
                (eid,)):
            continue
        decisions.ask(
            agent, agent.split(":")[0], "stale_comment",
            f"Propozycja komentarza dla {who} wisi bez decyzji ponad 24h. Co z nia?",
            [{"key": "sent", "label": "Wyslalem (odhacz)"},
             {"key": "skip", "label": "Pomin"},
             {"key": "show", "label": "Pokaz jeszcze raz"}],
            recommendation="show", context={"engagement_id": eid})


def _watch_in_progress():
    rows = db.fetchall(
        """SELECT id, agent_id, payload FROM task_queue
           WHERE task_type='comment' AND status='in_progress'
             AND created_at < NOW() - interval '24 hours'
           ORDER BY created_at LIMIT 5""")
    for r in rows:
        tid = str(r["id"])
        if db.fetchone(
                """SELECT 1 AS x FROM agent_decisions
                   WHERE decision_type='stale_comment_task' AND context->>'task_id'=%s
                     AND (status='pending' OR answered_at > NOW() - interval '24 hours') LIMIT 1""",
                (tid,)):
            continue
        p = r.get("payload") or {}
        who = (p.get("author") or "").strip() or "(autor ze zrzutu)"
        decisions.ask(
            r.get("agent_id") or "AGS:x", (r.get("agent_id") or "AGS:x").split(":")[0],
            "stale_comment_task",
            f"Zatwierdziles komentarz do {who} ponad 24h temu. Wyslales go?",
            [{"key": "yes", "label": "Tak, odhacz"}, {"key": "no", "label": "Nie, pomin"}],
            recommendation=None,
            context={"task_id": tid, "engagement_id": p.get("engagement_id"),
                     "contact_id": p.get("contact_id")})


def apply_stale_comment(row, key, chat):
    """Akcja decyzji 'stale_comment': sent = odhacz + stadium; skip = pomin; show = wyslij ponownie
    propozycje z guzikami cmt: (ten sam wiersz, decyzja dalej otwarta)."""
    ctx = row.get("context") or {}
    eng_id = ctx.get("engagement_id")
    if not eng_id:
        return
    e = db.fetchone(
        """SELECT id, agent, author_display, content, response, contact_id
           FROM engagement_log WHERE id=%s::uuid""", (eng_id,))
    if not e:
        _tg("sendMessage", {"chat_id": chat, "text": "Nie znajduje juz tej propozycji w bazie."})
        return
    stamp = datetime.datetime.now().strftime("%d/%m %H:%M")
    if key == "sent":
        db.execute("UPDATE engagement_log SET status='sent', notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | WYSLANE (przypomnienie {stamp})", eng_id))
        if e.get("contact_id"):
            from . import crm
            crm.bump_stage(str(e["contact_id"]), "commented")
        _tg("sendMessage", {"chat_id": chat, "text": "✅ Odhaczone - zapisane w pamieci konta i na kontakcie."})
    elif key == "skip":
        db.execute("UPDATE engagement_log SET status='skipped', notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | POMINIETE (przypomnienie {stamp})", eng_id))
        _tg("sendMessage", {"chat_id": chat, "text": "⏭ Pominiete - propozycja zamknieta."})
    elif key == "show":
        agent = e.get("agent") or "AGS:x"
        brand, _, channel = agent.partition(":")
        from .conversation import _send_author_proposal
        # ponowna wysylka tej samej tresci = NOWY wiersz z guzikami; stary zamykamy jako zastapiony
        db.execute("UPDATE engagement_log SET status='rejected', notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | POKAZANE PONOWNIE {stamp} (nowy wiersz)", eng_id))
        _send_author_proposal(chat, brand or "AGS", channel or "x",
                              e.get("author_display") or "(autor ze zrzutu)",
                              e.get("content") or "", e.get("response") or "")


def apply_stale_outreach(row, key, chat):
    """Akcja decyzji 'stale_outreach' (22/07): gotowce sprzedawcy. sent = odhacz (sent);
    wait = czekamy (np. na telefon rodziny) - przypomnienie wroci; show = SAMA TRESC
    czysta wklejka (zero intake'u/komentarzowej maszynerii); drop = rezygnacja."""
    ctx = row.get("context") or {}
    eng_id = ctx.get("engagement_id")
    if not eng_id:
        return
    e = db.fetchone(
        """SELECT id, agent, author_display, content, response FROM engagement_log
           WHERE id=%s::uuid""", (eng_id,))
    if not e:
        _tg("sendMessage", {"chat_id": chat, "text": "Nie znajduje juz tego gotowca w bazie."})
        return
    stamp = datetime.datetime.now().strftime("%d/%m %H:%M")
    who = e.get("author_display") or (e.get("content") or "")[:60]
    if key == "sent":
        db.execute("UPDATE engagement_log SET status='sent', notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | WYSLANE (przypomnienie {stamp})", eng_id))
        _tg("sendMessage", {"chat_id": chat, "text": f"✅ Odhaczone - outreach do {who} zapisany jako wyslany."})
    elif key == "wait":
        db.execute("UPDATE engagement_log SET notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | CZEKAMY ({stamp})", eng_id))
        _tg("sendMessage", {"chat_id": chat, "text": f"⏳ Jasne, czekamy - przypomne jutro o {who}."})
    elif key == "drop":
        db.execute("UPDATE engagement_log SET status='skipped', notes = COALESCE(notes,'') || %s WHERE id=%s::uuid",
                   (f" | REZYGNACJA ({stamp})", eng_id))
        _tg("sendMessage", {"chat_id": chat, "text": f"⏭ Zamkniete - outreach do {who} wycofany."})
    elif key == "show":
        _tg("sendMessage", {"chat_id": chat,
                            "text": f"📋 OUTREACH do {who} - ponizej czysta wklejka (po wyslaniu tapnij "
                                    f"'Wyslalem' na przypomnieniu albo napisz sprzedawcy):"})
        _tg("sendMessage", {"chat_id": chat, "text": (e.get("response") or e.get("content") or "")[:4096],
                            "disable_web_page_preview": True})


# ---------------- LACZNIK (22/07): parser RAPORT PRACY czat -> serwer, BEZ LLM ----------------
# Kontrakt 1 konceptu docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md: czatowy agent na
# abonamencie konczy sesje blokiem [RAPORT PRACY v1]; Tomasz wkleja go do Telegrama (albo
# wrzuca .md przez handle_document) -> deterministyczny route w conversation.handle ->
# apply_work_report. Idempotencja: sha256 znormalizowanej linii w engagement_log.notes
# ('sync:<hash>') - podwojna wklejka = zero dubli. ZERO DDL, zero LLM.

_REPORT_HEAD_RE = re.compile(
    r"\[RAPORT\s+PRACY(?:\s+v\d+)?\]\s*(?:kana[lł]\s*:\s*([A-Za-z_]+))?"
    r"(?:\s*\|\s*data\s*:\s*(\S+))?", re.IGNORECASE)
_REPORT_END_RE = re.compile(r"\[KONIEC\s+RAPORTU\]", re.IGNORECASE)
_CHANNEL_ALIASES = {"x": "x", "twitter": "x", "linkedin": "linkedin", "li": "linkedin",
                    "sprzedaz": "sprzedaz"}
_ENG_CHANNEL = {"x": "X", "linkedin": "LinkedIn", "sprzedaz": "Other"}
_LINE_TYPES = {"komentarz": "komentarz", "dm_wyslany": "dm_wyslany", "dm wyslany": "dm_wyslany",
               "dm_odebrany": "dm_odebrany", "dm odebrany": "dm_odebrany", "reakcja": "reakcja",
               "nowa_osoba": "nowa_osoba", "nowa osoba": "nowa_osoba", "obserwacja": "obserwacja",
               # rozszerzenie 22/07 (wsad masterpromptow LinkedIn): zaproszenia do sieci
               "zaproszenie": "zaproszenie", "zaproszenie_wyslane": "zaproszenie",
               "zaproszenie wyslane": "zaproszenie",
               # aliasy z polskimi znakami - agent czatowy potrafi je napisac mimo instrukcji
               "dm_wysłany": "dm_wyslany", "dm wysłany": "dm_wyslany",
               "zaproszenie_wysłane": "zaproszenie", "zaproszenie wysłane": "zaproszenie"}
_VALID_TIERS = {"buyer": "Buyer", "peer": "Peer", "competitor": "Competitor", "partner": "Partner"}


def _line_hash(channel, line):
    """Znormalizowana linia (male litery, sklejone biale znaki) + kanal -> sha256[:16].
    Ta sama linia w tym samym kanale wkleona drugi raz = duplikat."""
    norm = re.sub(r"\s+", " ", (line or "")).strip().lower()
    return hashlib.sha256(f"{channel}|{norm}".encode("utf-8")).hexdigest()[:16]


def _hash_seen(h):
    try:
        return bool(db.fetchone("SELECT 1 AS x FROM engagement_log WHERE notes LIKE %s LIMIT 1",
                                (f"%sync:{h}%",)))
    except Exception:
        traceback.print_exc()
        return False


def parse_work_report(text):
    """Wyciagnij (channel, data, [(typ, czesci, surowa_linia)], zle_linie) z bloku RAPORT PRACY.
    channel=None gdy naglowek bez kanalu (wolajacy podstawia kanal aktywnego subagenta)."""
    m = _REPORT_HEAD_RE.search(text or "")
    if not m:
        return None
    channel = _CHANNEL_ALIASES.get((m.group(1) or "").strip().lower()) if m.group(1) else None
    rdate = (m.group(2) or "").strip() or None
    body = text[m.end():]
    endm = _REPORT_END_RE.search(body)
    if endm:
        body = body[:endm.start()]
    entries, bad = [], []
    for raw in body.split("\n"):
        line = raw.strip()
        # tap-test d (22/07): agent czatowy potrafi wydrukowac linie BEZ '- ' na poczatku -
        # myslnik jest mile widziany, ale decyduje pierwszy token (typ) przed '|'
        dashed = line.startswith(("-", "•", "*"))
        if dashed:
            line = line.lstrip("-•*").strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        typ = _LINE_TYPES.get(re.sub(r"\s+", " ", parts[0].lower()))
        if typ and (typ == "obserwacja" or len(parts) >= 2):
            entries.append((typ, parts[1:], line))
        elif dashed or "|" in line:
            # linia, ktora MIALA byc akcja (myslnik albo separator pol) - jawnie do "niezrozumianych";
            # zwykla proza bez '|' jest ignorowana po cichu (np. zdanie zamykajace agenta)
            bad.append(line)
    return {"channel": channel, "date": rdate, "entries": entries, "bad": bad}


def _report_insert(action_type, channel, agent, content, response, notes, contact_id, status, author):
    db.execute(
        """INSERT INTO engagement_log (action_type, channel, agent, content, response, notes,
                                       contact_id, status, author_display)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (action_type, _ENG_CHANNEL.get(channel, "Other"), agent, (content or "")[:1000],
         (response or None), notes, contact_id, status, (author or None)))


def _report_tier_card(contact_id, disp, bio, tier_raw, brand, channel):
    """JEDNA karta crm_tier per osoba/24h (mechanizm z INTAKE-UX B3, wzorzec
    crm.process_profile_photo). Zwraca notke do potwierdzenia.
    22/07 (obowiazek klasyfikacji): kontakt z JUZ nadanym tierem nie dostaje karty -
    backfill klasyfikacyjny nie moze flodowac kartami bazy #71 ani re-pytac o Buyerow."""
    cur = db.fetchone("SELECT icp_tier FROM contacts WHERE id=%s::uuid", (str(contact_id),))
    if (cur or {}).get("icp_tier"):
        return f"{disp}: tier juz nadany ({cur['icp_tier']})"
    dup = db.fetchone(
        """SELECT id, status, answer FROM agent_decisions
           WHERE decision_type='crm_tier' AND context->>'contact_id'=%s
             AND (status='pending' OR answered_at > NOW() - interval '24 hours')
           ORDER BY created_at DESC LIMIT 1""", (str(contact_id),))
    if dup:
        return (f"karta tieru dla {disp} juz czeka" if dup["status"] == "pending"
                else f"tier {disp} rozstrzygniety w ostatnich 24h ({dup.get('answer')})")
    tier = _VALID_TIERS.get((tier_raw or "").strip().lower())
    decisions.ask(
        f"{brand}:{channel}", brand, "crm_tier",
        f"Klasyfikacja ICP dla {disp} (z RAPORTU PRACY):\n"
        + (f"NOTKA: {bio}\n" if bio else "")
        + (f"Propozycja z raportu: {tier}" if tier else "Raport bez propozycji tieru - wybierz."),
        [{"key": "buyer", "label": "Buyer"}, {"key": "peer", "label": "Peer"},
         {"key": "competitor", "label": "Competitor"}, {"key": "partner", "label": "Partner"}],
        recommendation={"Buyer": "buyer", "Peer": "peer", "Competitor": "competitor",
                        "Partner": "partner"}.get(tier),
        context={"contact_id": str(contact_id)})
    return f"karta tieru dla {disp} ponizej (guziki)"


def apply_work_report(chat_id, text, active_agent=None):
    """Route '[RAPORT PRACY' (conversation.handle): parsuj -> INSERTy -> POTWIERDZENIE z licznikami.
    Kazda sciezka konczy sie tekstem (REGULA PRAWDY); zero LLM."""
    from . import crm
    rep = parse_work_report(text)
    if not rep:
        return "Widze '[RAPORT PRACY', ale nie moge odczytac naglowka - format: [RAPORT PRACY v1] kanal: X"
    channel = rep["channel"]
    if not channel and (active_agent or "").startswith("subagent:"):
        channel = active_agent.split(":", 2)[2] if active_agent.count(":") >= 2 else None
    channel = channel or "x"
    brand = "AGS"
    agent = f"{brand}:{channel}"
    stamp = rep["date"] or datetime.date.today().strftime("%Y-%m-%d")
    cnt = {"komentarz": 0, "dm_wyslany": 0, "dm_odebrany": 0, "reakcja": 0,
           "nowa_osoba": 0, "znana_osoba": 0, "obserwacja": 0, "zaproszenie": 0}
    dupes = 0
    tier_notes = []
    for typ, parts, raw_line in rep["entries"]:
        h = _line_hash(channel, raw_line)
        if _hash_seen(h):
            dupes += 1
            continue
        base_note = f"sync:{h} | RAPORT PRACY {stamp} (praca reczna na abonamencie)"
        try:
            if typ == "komentarz":
                who = parts[0]
                link = parts[1] if len(parts) > 1 else ""
                tresc = " | ".join(parts[2:]) if len(parts) > 2 else ""
                contact_id, _new = crm.ensure_contact(who, brand, channel)
                fam = channel.split("_")[0]
                _report_insert(f"{fam}_comment" if fam in ("x", "linkedin") else "other",
                               channel, agent, link or raw_line,
                               tresc or None, base_note + " | komentarz wklejony recznie",
                               contact_id, "sent", crm.clean_author(who) or who)
                if contact_id:
                    crm.bump_stage(contact_id, "commented")
                cnt["komentarz"] += 1
            elif typ in ("dm_wyslany", "dm_odebrany"):
                who = parts[0]
                tresc = " | ".join(parts[1:])
                contact_id, _new = crm.ensure_contact(who, brand, channel)
                _report_insert("other", channel, agent, tresc, None,
                               base_note + (" | [DM] wyslany recznie" if typ == "dm_wyslany"
                                            else " | [DM] odebrany (streszczenie)"),
                               contact_id, "sent" if typ == "dm_wyslany" else "logged",
                               crm.clean_author(who) or who)
                if contact_id:
                    crm.bump_stage(contact_id, "dm")
                cnt[typ] += 1
            elif typ == "reakcja":
                who = parts[0]
                rest = " | ".join(parts[1:])
                contact_id, _new = crm.ensure_contact(who, brand, channel)
                _report_insert("other", channel, agent, rest or raw_line, None,
                               base_note + " | reakcja", contact_id, "logged",
                               crm.clean_author(who) or who)
                cnt["reakcja"] += 1
            elif typ == "zaproszenie":
                # 22/07 (praca LinkedIn): '- zaproszenie | @handle | wyslane/przyjete | notka'.
                # Stadium bez zmian ('connected' nie istnieje w skali; awans robia dopiero
                # komentarz/dm) - zapis samego faktu + kontakt w CRM.
                who = parts[0]
                kierunek = " | ".join(parts[1:]) or "wyslane"
                contact_id, _new = crm.ensure_contact(who, brand, channel)
                _report_insert("other", channel, agent, kierunek, None,
                               base_note + f" | zaproszenie ({kierunek[:60]})", contact_id,
                               "logged", crm.clean_author(who) or who)
                cnt["zaproszenie"] += 1
            elif typ == "nowa_osoba":
                who = parts[0]
                bio = parts[1] if len(parts) > 1 else ""
                tier_raw = parts[2] if len(parts) > 2 else ""
                contact_id, is_new = crm.ensure_contact(who, brand, channel)
                disp = crm.clean_author(who) or who
                if contact_id and bio:
                    db.execute(
                        "UPDATE contacts SET narration = COALESCE(narration,'') || %s WHERE id=%s::uuid",
                        (f" | [raport {stamp}] {bio[:400]}", contact_id))
                _report_insert("other", channel, agent, bio or raw_line, None,
                               base_note + " | nowa osoba (poznana recznie)", contact_id,
                               "logged", disp)
                cnt["nowa_osoba" if is_new else "znana_osoba"] += 1
                if contact_id:
                    tier_notes.append(_report_tier_card(contact_id, disp, bio, tier_raw,
                                                        brand, channel))
            elif typ == "obserwacja":
                notka = " | ".join(parts)
                db.execute(
                    """INSERT INTO inspirations (source, content, brand, status, metadata)
                       VALUES ('raport_pracy', %s, %s, 'new', %s)""",
                    (notka[:2000], brand, Jsonb({"channel": channel, "via": "raport_pracy",
                                                 "date": stamp})))
                _report_insert("other", channel, agent, notka, None,
                               base_note + " | obserwacja radaru (kopia w inspirations)",
                               None, "logged", None)
                cnt["obserwacja"] += 1
        except Exception:
            traceback.print_exc()
            rep["bad"].append(raw_line)
    labels = [("komentarz", "komentarze"), ("dm_wyslany", "DM wyslane"),
              ("dm_odebrany", "DM odebrane"), ("reakcja", "reakcje"),
              ("zaproszenie", "zaproszenia"), ("nowa_osoba", "nowe osoby"),
              ("znana_osoba", "znane osoby zaktualizowane"), ("obserwacja", "obserwacje do radaru")]
    saved = [f"{lbl}: {cnt[k]}" for k, lbl in labels if cnt[k]]
    lines = [f"📥 POTWIERDZENIE - RAPORT PRACY zapisany (kanal {channel}, {stamp}):",
             ("zapisane: " + ", ".join(saved)) if saved else "zapisane: nic nowego",
             f"pominiete duplikaty: {dupes}"]
    if rep["bad"]:
        lines.append("NIEZROZUMIANE LINIE (nie zapisane - popraw i wklej ponownie tylko je):")
        lines += [f"- {b[:160]}" for b in rep["bad"][:8]]
    if tier_notes:
        lines.append("Tiery: " + "; ".join(tier_notes))
    if not rep["entries"] and not rep["bad"]:
        lines.append("(raport bez linii akcji - miedzy naglowkiem a [KONIEC RAPORTU] nic nie znalazlem)")
    return "\n".join(lines)


def apply_stale_task(row, key, chat):
    """Akcja decyzji 'stale_comment_task': yes = task done + sent + stadium; no = task failed + skip."""
    ctx = row.get("context") or {}
    tid, eng_id = ctx.get("task_id"), ctx.get("engagement_id")
    if not tid:
        return
    if key == "yes":
        db.execute("UPDATE task_queue SET status='done', resolved_at=NOW() WHERE id=%s::uuid", (tid,))
        if eng_id:
            db.execute("UPDATE engagement_log SET status='sent' WHERE id=%s::uuid", (eng_id,))
        if ctx.get("contact_id"):
            from . import crm
            crm.bump_stage(str(ctx["contact_id"]), "commented")
        _tg("sendMessage", {"chat_id": chat, "text": "✅ Odhaczone - komentarz zaliczony, kontakt zaktualizowany."})
    else:
        db.execute("UPDATE task_queue SET status='failed', resolved_at=NOW() WHERE id=%s::uuid", (tid,))
        if eng_id:
            db.execute("UPDATE engagement_log SET status='skipped' WHERE id=%s::uuid", (eng_id,))
        _tg("sendMessage", {"chat_id": chat, "text": "⏭ Pominiete - zadanie zamkniete bez wykonania."})
