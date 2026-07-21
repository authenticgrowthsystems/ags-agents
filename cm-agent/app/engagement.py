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
import traceback

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
