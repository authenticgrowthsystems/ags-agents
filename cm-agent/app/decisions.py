"""Model eskalacji + nauki (plan dnia 19/07 krok [2]; kanon publikacji 19/07 pkt 3).

Kazde pytanie CM/subagenta do Tomasza = ustrukturyzowana decyzja z GUZIKAMI (nie proza):
ask() zapisuje wiersz agent_decisions i wysyla wiadomosc z inline keyboard (callback
'dec:<id>:<key>'; rekomendacja pierwszym guzikiem z gwiazdka). Odpowiedz wraca przez n8n
(galaz dec:) -> POST /decnav -> handle(): zapis odpowiedzi + wpis do agent_learning_log
(accepted gdy zgodna z rekomendacja, replaced gdy inna) + paragon NOWA wiadomoscia (kanon).

NAUKA: gdy typ decyzji ma >= PROG_MIN odpowiedzi i >= PROG_ZGODY zgodnosci z rekomendacja
w ostatnich 20, CM proponuje przejscie supervised -> semi_autonomous DLA TEGO TYPU - sama
propozycja tez jest decyzja (decision_type='mode_transition', ten sam mechanizm). W trybie
semi_autonomous ask() wybiera rekomendacje SAM (status 'auto'), loguje i wysyla paragon
informacyjny - Tomasz widzi kazda auto-decyzje i moze cofnac tryb (/decyzje -> mode_transition).

UWAGA KANON: to NIE dotyczy zatwierdzania TRESCI do publikacji (niezatwierdzone NIGDY nie
wychodzi samo). Semi-auto obejmuje decyzje OPERACYJNE (sloty, podmiany tematow, modele itd.).
"""
import datetime
import html as _html
import json

import httpx
from psycopg.types.json import Jsonb

from . import config, db

PROG_MIN = 10      # min odpowiedzi danego typu zanim zaproponujemy semi_autonomous
PROG_ZGODY = 0.8   # udzial odpowiedzi zgodnych z rekomendacja (ostatnie 20)
_OKNO = 20

# 22/07 (uwaga Tomasza 00:05: "skad mam wiedziec jaka to decyzja 14? nie potrzebuje znacznikow
# z programu, ma byc wytluszczone"): zgloszenia po ludzku, naglowek pogrubiony (HTML),
# zero [decision_type]/#id w tekscie widocznym. Id zyje tylko w callbackach.
_TYPE_LABEL = {
    "stale_comment": "Komentarz czeka na wyslanie",
    "stale_comment_task": "Komentarz do odhaczenia",
    "stale_outreach": "Outreach czeka na wyslanie",
    "stale_approval": "Material czeka na Twoja decyzje",
    "crm_tier": "Klasyfikacja osoby",
    "intent_menu": "Co robimy z wrzutka",
    "photo_group": "Album zdjec",
    "model_selection": "Wybor modelu",
    "mode_transition": "Zmiana trybu nauki",
    "topic_swap": "Podmiana tematu",
}


def _friendly(decision_type, subagent_id):
    typ = _TYPE_LABEL.get(decision_type, (decision_type or "decyzja").replace("_", " "))
    who = {"CM": "Content Manager"}.get(subagent_id, subagent_id)
    return f"{typ} ({who})"


def _tg(method, payload):
    tok = config.TELEGRAM_BOT_TOKEN
    if not tok:
        return None
    try:
        r = httpx.post(f"https://api.telegram.org/bot{tok}/{method}", json=payload, timeout=20)
        return r.json()
    except Exception:
        return None


def _admin_chat():
    from . import hitl
    return hitl._admin_chat_id()


def _norm_options(options):
    """Przyjmij [{'key','label'}] albo ['label1','label2'] -> zawsze [{'key','label'}]."""
    out = []
    for i, o in enumerate(options or []):
        if isinstance(o, dict) and o.get("key"):
            out.append({"key": str(o["key"])[:40], "label": str(o.get("label") or o["key"])[:60]})
        else:
            out.append({"key": f"opt{i + 1}", "label": str(o)[:60]})
    return out


def mode_for(subagent_id, decision_type):
    r = db.fetchone("SELECT mode FROM decision_modes WHERE subagent_id=%s AND decision_type=%s",
                    (subagent_id, decision_type))
    return (r or {}).get("mode") or "supervised"


def _learn(subagent_id, brand_id, question, answer_label, accepted, notes):
    """Kazda odpowiedz (i auto-decyzja) -> agent_learning_log; z tego liczy sie _learning_digest."""
    try:
        db.execute(
            """INSERT INTO agent_learning_log (subagent_id, brand_id, proposed_content, final_content,
                                               correction_type, notes)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (subagent_id, brand_id or "AGS", question[:2000], answer_label[:2000],
             "accepted" if accepted else "replaced", notes))
    except Exception:
        pass


def ask(subagent_id, brand_id, decision_type, question, options, recommendation=None,
        context=None, chat_id=None):
    """Eskaluj decyzje. Zwraca tekst-wynik dla wolajacego (tool CM / modul). W trybie
    semi_autonomous z rekomendacja: decyzja zapada SAMA + paragon informacyjny."""
    opts = _norm_options(options)
    if not opts:
        return "Decyzja bez opcji - podaj przynajmniej dwie opcje."
    keys = [o["key"] for o in opts]
    reco = recommendation if recommendation in keys else None
    chat = chat_id or _admin_chat()
    mode = mode_for(subagent_id, decision_type)
    if mode == "semi_autonomous" and reco and decision_type != "mode_transition":
        row = db.fetchone(
            """INSERT INTO agent_decisions (subagent_id, brand_id, decision_type, question, options,
                                            recommendation, context, status, answer, answered_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'auto',%s,NOW()) RETURNING id""",
            (subagent_id, brand_id, decision_type, question, Jsonb(opts), reco,
             Jsonb(context or {}), reco))
        label = next(o["label"] for o in opts if o["key"] == reco)
        _learn(subagent_id, brand_id, question, label, True, f"auto:semi_autonomous dec:{row['id']}")
        _tg("sendMessage", {"chat_id": chat, "parse_mode": "HTML", "text":
            f"🤖 <b>Decyzja podjeta sama: {_html.escape(_friendly(decision_type, subagent_id))}</b>\n"
            f"{_html.escape(question[:500])}\n➡️ {_html.escape(label)}\n"
            f"(Tryb nadales przez wczesniejsze odpowiedzi; cofniesz go odpowiadajac "
            f"inaczej przy nastepnych pytaniach tego typu.)"})
        return f"Decyzja podjeta automatycznie (semi_autonomous): {label}."
    # supervised: guziki do Tomasza, rekomendacja pierwsza z gwiazdka
    row = db.fetchone(
        """INSERT INTO agent_decisions (subagent_id, brand_id, decision_type, question, options,
                                        recommendation, context)
           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (subagent_id, brand_id, decision_type, question, Jsonb(opts), reco, Jsonb(context or {})))
    ordered = ([o for o in opts if o["key"] == reco] + [o for o in opts if o["key"] != reco]) if reco else opts
    kb = [[{"text": ("⭐ " if o["key"] == reco else "") + o["label"],
            "callback_data": f"dec:{row['id']}:{o['key']}"}] for o in ordered]
    r = _tg("sendMessage", {"chat_id": chat, "parse_mode": "HTML",
                            "text": f"🔔 <b>{_html.escape(_friendly(decision_type, subagent_id))}</b>\n"
                                    f"{_html.escape(question[:3500])}",
                            "reply_markup": {"inline_keyboard": kb}})
    mid = ((r or {}).get("result") or {}).get("message_id")
    if mid:
        db.execute("UPDATE agent_decisions SET tg_message_id=%s WHERE id=%s", (mid, row["id"]))
    return f"Wyslalem Tomaszowi decyzje #{row['id']} z guzikami ({len(opts)} opcji). Czekamy na tapniecie."


def handle(body, wake=None):
    """POST /decnav: raw='dec:<id>:<key>'. Zapis + nauka + paragon nowa wiadomoscia + ew. propozycja
    przejscia trybu. Kazda sciezka konczy sie wiadomoscia (REGULA PRAWDY)."""
    raw = str(body.get("raw") or "")
    chat = body.get("chat_id") or _admin_chat()
    try:
        _, dec_id, key = raw.split(":", 2)
        dec_id = int(dec_id)
    except (ValueError, AttributeError):
        _tg("sendMessage", {"chat_id": chat, "text": f"❌ Nieczytelny callback decyzji: {raw[:60]}"})
        return
    row = db.fetchone("SELECT * FROM agent_decisions WHERE id=%s", (dec_id,))
    if not row:
        _tg("sendMessage", {"chat_id": chat, "text": f"❌ Decyzja #{dec_id} nie istnieje."})
        return
    if row["status"] != "pending":
        _tg("sendMessage", {"chat_id": chat,
                            "text": f"Decyzja #{dec_id} juz rozstrzygnieta ({row['status']}: {row.get('answer')})."})
        return
    opts = row["options"] if isinstance(row["options"], list) else json.loads(row["options"])
    label = next((o["label"] for o in opts if o["key"] == key), key)
    db.execute("UPDATE agent_decisions SET status='answered', answer=%s, answered_at=NOW() WHERE id=%s",
               (key, dec_id))
    accepted = bool(row.get("recommendation")) and key == row["recommendation"]
    _learn(row["subagent_id"], row.get("brand_id"), row["question"], label, accepted, f"dec:{dec_id}")
    if row.get("tg_message_id"):  # zdejmij guziki z oryginalu, zeby nie dalo sie kliknac drugi raz
        _tg("editMessageReplyMarkup", {"chat_id": chat, "message_id": row["tg_message_id"],
                                       "reply_markup": {"inline_keyboard": []}})
    _tg("sendMessage", {"chat_id": chat, "parse_mode": "HTML",  # potwierdzenie NOWA wiadomoscia (kanon 05/07)
                        "text": f"✅ <b>{_html.escape(label)}</b> - "
                                f"{_html.escape(_friendly(row['decision_type'], row['subagent_id']))}: "
                                f"{_html.escape((row.get('question') or '')[:120])}"
                                + ("" if accepted else "\n(inaczej niz rekomendacja - zapamietane)")})
    if row["decision_type"] == "mode_transition":
        _apply_mode_transition(row, key, chat)
    else:
        _apply_action(row, key, chat)
        _maybe_propose_transition(row["subagent_id"], row.get("brand_id"), row["decision_type"], chat)
    if wake is not None:
        wake.set()


def _apply_action(row, key, chat):
    """Akcje domenowe po odpowiedzi (rejestr per typ; typy bez akcji = sama nauka).
    stale_approval (kanon 19/07): show/reject/wait. BE-ENGAGEMENT (20/07): crm_tier,
    stale_comment, stale_comment_task, photo_group (importy lokalne - bez cykli)."""
    dt = row["decision_type"]
    if dt == "crm_tier":
        from . import crm
        crm.apply_tier(row, key, chat)
        return
    if dt == "stale_comment":
        from . import engagement
        engagement.apply_stale_comment(row, key, chat)
        return
    if dt == "stale_comment_task":
        from . import engagement
        engagement.apply_stale_task(row, key, chat)
        return
    if dt == "stale_outreach":
        from . import engagement
        engagement.apply_stale_outreach(row, key, chat)
        return
    if dt == "photo_group":
        from . import conversation
        conversation.apply_photo_group(row, key, chat)
        return
    if dt == "intent_menu":
        # INTAKE-UX (21/07): menu intencji po wrzutce zrzutu - wykonanie sekwencyjne z paragonami
        from . import conversation
        conversation.apply_intent_menu(row, key, chat)
        return
    if dt != "stale_approval":
        return
    item_id = (row.get("context") or {}).get("content_item_id")
    if not item_id:
        return
    if key == "show":
        from . import matreview
        it = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (item_id,))
        matreview.send_review_card(chat, theme_fragment=(it or {}).get("master_theme", "")[:60] or None)
    elif key == "reject":
        db.execute("UPDATE content_items SET status='rejected', updated_at=NOW() "
                   "WHERE id=%s AND status='needs_approval'", (item_id,))
        _tg("sendMessage", {"chat_id": chat, "text": f"🗑 Material odrzucony (decyzja #{row['id']})."})
    # 'wait' = nic; watcher przypomni po 24h nowa decyzja


def _apply_mode_transition(row, key, chat):
    ctx = row.get("context") or {}
    target_type = ctx.get("target_type")
    if not target_type:
        return
    mode = "semi_autonomous" if key == "semi" else "supervised"
    db.execute(
        """INSERT INTO decision_modes (subagent_id, decision_type, mode, updated_at, updated_by)
           VALUES (%s,%s,%s,NOW(),'tomasz')
           ON CONFLICT (subagent_id, decision_type) DO UPDATE SET mode=EXCLUDED.mode,
             updated_at=NOW(), updated_by='tomasz'""",
        (row["subagent_id"], target_type, mode))
    _tg("sendMessage", {"chat_id": chat,
                        "text": f"🎛 Tryb decyzji [{target_type}] dla {row['subagent_id']}: {mode}."})


def _maybe_propose_transition(subagent_id, brand_id, decision_type, chat):
    """Prog nauki: >=PROG_MIN odpowiedzi i >=PROG_ZGODY zgodnosci w ostatnich _OKNO -> zaproponuj
    semi_autonomous (sama propozycja = decyzja mode_transition, ten sam mechanizm guzikow)."""
    if mode_for(subagent_id, decision_type) != "supervised":
        return
    rows = db.fetchall(
        """SELECT answer, recommendation FROM agent_decisions
           WHERE subagent_id=%s AND decision_type=%s AND status='answered' AND recommendation IS NOT NULL
           ORDER BY answered_at DESC LIMIT %s""",
        (subagent_id, decision_type, _OKNO))
    if len(rows) < PROG_MIN:
        return
    agree = sum(1 for r in rows if r["answer"] == r["recommendation"]) / len(rows)
    if agree < PROG_ZGODY:
        return
    if db.fetchone(
            """SELECT 1 AS x FROM agent_decisions WHERE subagent_id=%s AND decision_type='mode_transition'
               AND context->>'target_type'=%s AND status='pending' LIMIT 1""",
            (subagent_id, decision_type)):
        return
    ask(subagent_id, brand_id, "mode_transition",
        f"Typ decyzji [{decision_type}]: {len(rows)} ostatnich odpowiedzi, {agree:.0%} zgodnych z moja "
        f"rekomendacja. Przelaczyc ten typ na semi_autonomous (decyduje sam + paragon po fakcie)?",
        [{"key": "semi", "label": "Przelacz na semi-auto"}, {"key": "keep", "label": "Zostaw supervised"}],
        recommendation="semi", context={"target_type": decision_type}, chat_id=chat)


def pending_text():
    """Lista czekajacych decyzji (do /decyzje w rozmowie CM)."""
    rows = db.fetchall(
        "SELECT id, subagent_id, decision_type, question, created_at FROM agent_decisions "
        "WHERE status='pending' ORDER BY created_at LIMIT 20")
    if not rows:
        return "(zero czekajacych decyzji ustrukturyzowanych)"
    return "\n".join(f"#{r['id']} [{r['decision_type']}] {r['subagent_id']}: {r['question'][:100]}" for r in rows)
