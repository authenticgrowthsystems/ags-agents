"""Konsument kolejki komentarzy (task_queue task_type='comment') - wariant A semi-auto
(decyzja Managera 10/07, P2 z ZAPYTANIA 09/07).

Zatwierdzony guzikiem [Zatwierdz] komentarz NIE wisi juz jako pending: konsument wysyla Tomaszowi
GOTOWIEC (propozycje + post zrodlowy) z guzikami odhaczenia. Publikacja przez API celowo NIE:
X write pod cudzymi postami = ryzyko tieru, LinkedIn comment API po App 2 CMA - wklejka reczna
jest bezpieczna i natychmiastowa. Zero DDL (statusy pending->in_progress->done/failed sa w CHECK,
dowod 10/07), zero zmian n8n (guziki cmt:done|skip jada istniejaca galezia cmt: -> POST /cmt).
"""
import traceback

from . import db, hitl
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
        text = (f"🧾 KOMENTARZ DO WKLEJENIA - konto {r['agent_id']}\n\n"
                + (f"POD POSTEM:\n{src[:400]}\n\n" if src else "")
                + f"PROPOZYCJE (wybierz jedna, skopiuj i wklej w aplikacji):\n{props[:2800]}\n\n"
                "Po wklejeniu odhacz guzikiem - wykonanie zapisze sie w pamieci konta.")
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
