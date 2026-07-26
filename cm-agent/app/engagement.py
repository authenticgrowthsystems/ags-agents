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
        # 26/07 (sekcja 4.3 diagnozy): guzik aktualizowal WYLACZNIE engagement_log - nie ustawial
        # terminu nastepnego kontaktu i nie domykal rodzenstwa. Kto odhaczyl guzikiem, ten zostawal
        # z "BRAK nastepnego kroku" w lejku. Obie drogi wolaja teraz jeden rdzen (AP-309).
        from . import sales
        _, opis = sales.mark_outreach_sent(eng_id=eng_id, zrodlo="przypomnienie")
        _tg("sendMessage", {"chat_id": chat, "text": "✅ Odhaczone - " + opis})
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
               "zaproszenie_wysłane": "zaproszenie", "zaproszenie wysłane": "zaproszenie",
               # paczka #1 Managera pkt 1 (24/07): eksport analityczny z panelu kanalu
               "kpi_snapshot": "kpi_snapshot", "kpi snapshot": "kpi_snapshot", "kpi": "kpi_snapshot",
               "metryki": "kpi_snapshot", "metryki_kanalu": "kpi_snapshot",
               "metryki kanalu": "kpi_snapshot", "metryki kanału": "kpi_snapshot"}
def _valid_tiers():
    """Skala tierow trzymana w JEDNYM miejscu (crm.TIERS) - 24/07 doszedl 'Inne' (DDL 031)."""
    from . import crm
    return crm.TIER_KEYS

# ---- pkt 1: liczby z panelu analitycznego (deterministycznie, zero LLM) ----
# Czat na abonamencie widzi panel, ktorego serwer nie widzi (LinkedIn do czasu App 2 CMA,
# X poza zakupionymi odczytami). Przepisane liczby wracaja linia 'kpi_snapshot' i laduja
# w channel_kpi_snapshots (DDL 030). Wartosci NIEROZPOZNANE nie gina - siadaja w raw.
_KPI_ALIASES = {
    "wyswietlenia": "impressions", "wyświetlenia": "impressions", "impressions": "impressions",
    "odslony": "impressions", "odsłony": "impressions", "zasieg": "impressions", "zasięg": "impressions",
    "reakcje": "reactions", "reactions": "reactions", "polubienia": "reactions",
    "zaangazowania": "reactions", "zaangażowania": "reactions", "engagements": "reactions",
    "nowi_obserwujacy": "new_followers", "nowi_obserwujący": "new_followers",
    "new_followers": "new_followers", "nowi": "new_followers",
    "obserwujacy": "followers_total", "obserwujący": "followers_total", "followers": "followers_total",
    "obserwujacy_razem": "followers_total", "obserwujący_razem": "followers_total",
    "odslony_profilu": "profile_views", "odsłony_profilu": "profile_views",
    "wejscia_na_profil": "profile_views", "wejścia_na_profil": "profile_views",
    "profile_views": "profile_views",
}
_KPI_FIELDS = ("impressions", "reactions", "new_followers", "followers_total", "profile_views")
_KPI_PERIODS = {"dzien", "7d", "28d", "90d"}
_KPI_DATE_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_KPI_DATE_PL = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$")


def _kpi_date(raw):
    """'2026-07-24' albo '24.07.2026' / '24/07/2026' -> 'RRRR-MM-DD'. Cokolwiek innego -> None."""
    s = (raw or "").strip()
    m = _KPI_DATE_ISO.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _KPI_DATE_PL.match(s)
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime.date(y, mo, d).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _kpi_num(raw):
    """'1 234' / '1,234' / '1.2K' / '1,2 tys.' -> int. Cokolwiek nieliczbowego -> None
    (pole zostaje puste; NIE zgadujemy zera - to byloby klamstwo w metrykach)."""
    s = re.sub(r"\s", "", str(raw or "")).lower()  # \s lapie tez spacje nierozdzielajaca
    m = re.match(r"^([\d.,]+)(k|tys\.?|m|mln)?$", s)
    if not m:
        return None
    num, suf = m.group(1), (m.group(2) or "")
    mult = 1000 if suf.startswith(("k", "tys")) else (1_000_000 if suf.startswith(("m", "mln")) else 1)
    if not suf and re.match(r"^\d{1,3}([.,]\d{3})+$", num):  # separator tysiecy
        num = re.sub(r"[.,]", "", num)
    try:
        val = float(num.replace(",", ".")) * mult
    except ValueError:
        return None
    return int(round(val)) if 0 <= val < 10 ** 12 else None


def _kpi_fields(parts):
    """Pola linii kpi_snapshot: data (goly token albo data=...), okres, znane metryki.
    Nieznany klucz albo nieczytelna liczba ida do 'extra' - w bazie wyladuja w raw."""
    out = {"metric_date": None, "period": "dzien", "extra": {}}
    out.update({f: None for f in _KPI_FIELDS})
    for raw in parts or []:
        p = (raw or "").strip()
        if not p:
            continue
        if "=" not in p and ":" not in p:
            out["metric_date"] = _kpi_date(p) or out["metric_date"]
            continue
        sep = "=" if "=" in p else ":"
        key, _, val = p.partition(sep)
        k = re.sub(r"\s+", "_", key.strip().lower())
        v = val.strip()
        if k in ("okres", "period"):
            per = v.lower().replace("dzień", "dzien").replace("dziennie", "dzien")
            out["period"] = per if per in _KPI_PERIODS else "dzien"
            continue
        if k in ("data", "date"):
            out["metric_date"] = _kpi_date(v) or out["metric_date"]
            continue
        field = _KPI_ALIASES.get(k)
        n = _kpi_num(v)
        if field and n is not None:
            out[field] = n
        else:
            out["extra"][k[:40]] = v[:120]
    return out


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
    from . import crm as _crm
    tier = _valid_tiers().get((tier_raw or "").strip().lower())
    # pkt 7 paczki #1 (24/07): fail-closed przed wykluczeniem z lejka - patrz crm.fail_closed_note.
    wolno, fc_note = _crm.fail_closed_note(contact_id, tier or tier_raw)
    decisions.ask(
        f"{brand}:{channel}", brand, "crm_tier",
        f"Klasyfikacja ICP dla {disp} (z RAPORTU PRACY):\n"
        + (f"NOTKA: {bio}\n" if bio else "")
        + (f"Propozycja z raportu: {tier}" if tier else "Raport bez propozycji tieru - wybierz.")
        + (f"\n{fc_note}" if fc_note else ""),
        list(_crm.TIER_OPTIONS),
        recommendation=((tier or "").lower() if (wolno and tier) else None),
        context={"contact_id": str(contact_id), "fail_closed": (not wolno)})
    return (f"karta tieru dla {disp} ponizej (guziki)"
            + (" - bez rekomendacji, jest historia rozmow" if not wolno else ""))


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
           "nowa_osoba": 0, "znana_osoba": 0, "obserwacja": 0, "zaproszenie": 0,
           "kpi_snapshot": 0}
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
            elif typ == "kpi_snapshot":
                # pkt 1 paczki #1: liczby z panelu analitycznego (czat je WIDZI, serwer nie).
                # Kolejny wpis o tej samej dacie i okresie NADPISUJE tylko pola, ktore przyszly
                # (COALESCE) - korekta jest mozliwa, a stara wartosc nie znika przez przeoczenie.
                f = _kpi_fields(parts)
                mdate = f["metric_date"] or _kpi_date(stamp) or datetime.date.today().strftime("%Y-%m-%d")
                extra = dict(f.get("extra") or {})
                extra["linia"] = raw_line[:300]
                db.execute(
                    """INSERT INTO channel_kpi_snapshots
                           (brand_id, channel, metric_date, period, impressions, reactions,
                            new_followers, followers_total, profile_views, source, raw)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'raport_pracy',%s)
                       ON CONFLICT (brand_id, channel, metric_date, period) DO UPDATE SET
                           impressions     = COALESCE(EXCLUDED.impressions, channel_kpi_snapshots.impressions),
                           reactions       = COALESCE(EXCLUDED.reactions, channel_kpi_snapshots.reactions),
                           new_followers   = COALESCE(EXCLUDED.new_followers, channel_kpi_snapshots.new_followers),
                           followers_total = COALESCE(EXCLUDED.followers_total, channel_kpi_snapshots.followers_total),
                           profile_views   = COALESCE(EXCLUDED.profile_views, channel_kpi_snapshots.profile_views),
                           raw             = EXCLUDED.raw,
                           updated_at      = NOW()""",
                    (brand, channel, mdate, f["period"], f["impressions"], f["reactions"],
                     f["new_followers"], f["followers_total"], f["profile_views"], Jsonb(extra)))
                _report_insert("other", channel, agent, raw_line, None,
                               base_note + f" | KPI kanalu {mdate} ({f['period']})",
                               None, "logged", None)
                cnt["kpi_snapshot"] += 1
        except Exception:
            traceback.print_exc()
            rep["bad"].append(raw_line)
    labels = [("komentarz", "komentarze"), ("dm_wyslany", "DM wyslane"),
              ("dm_odebrany", "DM odebrane"), ("reakcja", "reakcje"),
              ("zaproszenie", "zaproszenia"), ("nowa_osoba", "nowe osoby"),
              ("znana_osoba", "znane osoby zaktualizowane"), ("obserwacja", "obserwacje do radaru"),
              ("kpi_snapshot", "wpisy metryk kanalu")]
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
