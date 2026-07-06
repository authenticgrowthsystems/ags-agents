# -*- coding: utf-8 -*-
"""Przeglad materialow + decyzje intake (feedback Tomasza 05/07, spec docs/cm/CM_UX_FEEDBACK_05072026.md).
S2: material z rozmowy dostaje guziki [Do kolejki]/[Dzis]/[Odrzuc] (matdec:) zamiast cichego 'planned'.
S3: wygenerowane materialy (needs_approval) przegladane KARTA z ⬅️➡️ (matnav:, wzorzec plannav);
    seria osobnych wiadomosci tylko gdy czeka 1 material - od 2 w gore jedna zbiorcza wiadomosc.
S4: niedziela: przypomnienia co 15 min (21:30-23:00), o 23:00 CM sam zatwierdza material na
    poniedzialkowy slot + alert na bocie #2 (rozszerzenie kanonu 11c, 11c bez zmian)."""
import datetime
import json
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import db, config, logbot

WARSAW = ZoneInfo("Europe/Warsaw")
REMIND_START = (21, 30)   # niedziela: start okna przypomnien
REMIND_EVERY_MIN = 15
FALLBACK_AT = (23, 0)     # niedziela: autonomiczny wybor materialu


def _tg(method, payload):
    from . import conversation
    return conversation._tg(method, payload)


def _admin_chat():
    from . import hitl
    return hitl._admin_chat_id()


# ---------------- stan (brand_config, klucz per funkcja) ----------------
def _state_get(key):
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key=%s", (key,))
    try:
        return json.loads(r["config_value"]) if r and r.get("config_value") else {}
    except Exception:
        return {}


def _state_set(key, obj):
    db.execute(
        """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
           VALUES ('AGS',%s,%s,1,'cm-matreview',NOW())
           ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
             version=brand_config.version+1, updated_by='cm-matreview', updated_at=NOW()""",
        (key, json.dumps(obj, ensure_ascii=False)))


# ---------------- S2: intake (matdec:) ----------------
def send_intake_buttons(item_id, theme):
    """Po zapisie materialu z rozmowy: decyzja Tomasza jednym tapnieciem."""
    chat = _admin_chat()
    if not chat:
        return False
    kb = {"inline_keyboard": [[
        {"text": "📥 Do kolejki", "callback_data": f"matdec:{item_id}:queue"},
        {"text": "🚀 Dzis", "callback_data": f"matdec:{item_id}:now"},
        {"text": "❌ Odrzuc", "callback_data": f"matdec:{item_id}:drop"},
    ]]}
    _tg("sendMessage", {"chat_id": chat,
                        "text": f"Decyzja dla materialu:\n\"{theme[:300]}\"\n\nKolejka = produkcja + publikacja "
                                f"w slocie; Dzis = produkcja od razu, publikacja zaraz po Twoim zatwierdzeniu.",
                        "reply_markup": kb})
    return True


# ---------------- S3: paczka + karty (matnav:) ----------------
def pending_items(brand_id="AGS"):
    return db.fetchall(
        """SELECT id, master_theme, target_channels, scheduled_for, canonical_body, media FROM content_items
           WHERE brand_id=%s AND status='needs_approval'
           ORDER BY scheduled_for NULLS LAST, created_at""", (brand_id,))


def batch_note():
    """Jedna zbiorcza wiadomosc 'N materialow do przegladu' (edytowana w miejscu przy kazdym nowym).
    Wywolywana z hitl.send_approval gdy czeka >=2 materialow."""
    chat = _admin_chat()
    if not chat:
        return False
    n = len(pending_items())
    today = datetime.datetime.now(WARSAW).strftime("%Y-%m-%d")
    text = (f"📦 Materialy do przegladu: {n}\n"
            f"Przegladasz kartami (strzalki ⬅️➡️), decyzja per material na karcie.")
    kb = {"inline_keyboard": [[{"text": f"🔍 Przegladaj ({n})", "callback_data": "matnav:first:-"}],
                              [{"text": f"✅ Zatwierdz wszystkie ({n})", "callback_data": "matnav:all:-"}]]}
    st = _state_get("cm_matnav_batch")
    if st.get("date") == today and st.get("message_id"):
        r = _tg("editMessageText", {"chat_id": st.get("chat_id") or chat, "message_id": st["message_id"],
                                    "text": text, "reply_markup": kb})
        if r and r.get("ok"):
            _state_set("cm_matnav_batch", {**st, "count": n})
            return True
    r = _tg("sendMessage", {"chat_id": chat, "text": text, "reply_markup": kb})
    if r and r.get("ok"):
        _state_set("cm_matnav_batch",
                   {"date": today, "chat_id": chat, "message_id": r["result"]["message_id"], "count": n})
    return True


def send_review_card(chat_id=None):
    """SWIEZA karta przegladu na dole czatu (feedback 06/07: 'musialem scrollowac na gore').
    Wolane z rozmowy (/karty, narzedzie LLM) - zero szukania starych wiadomosci."""
    chat = chat_id or _admin_chat()
    if not chat:
        return False
    text, kb = _card()
    body = {"chat_id": chat, "text": text[:4000]}
    if kb:
        body["reply_markup"] = kb
    r = _tg("sendMessage", body)
    return bool(r and r.get("ok"))


def _card(item_id=None, brand_id="AGS"):
    """(text, kb) karty materialu; item_id=None -> pierwszy czekajacy."""
    from .planner import _DAYS_PL, _target_label
    items = pending_items(brand_id)
    if not items:
        return "📦 Przeglad zakonczony - brak materialow do decyzji.", None
    idx = 0
    if item_id:
        for i, it in enumerate(items):
            if str(it["id"]) == str(item_id):
                idx = i
                break
    it = items[idx]
    now = datetime.datetime.now(WARSAW)
    dt = it["scheduled_for"].astimezone(WARSAW) if it.get("scheduled_for") else None
    when = f"{_DAYS_PL[dt.weekday()]} {dt.strftime('%d/%m %H:%M')}" if dt else "zaraz po zatwierdzeniu"
    stale = "\n⚠️ SLOT MINAL - po 'Zatwierdz' CM sam przydzieli najblizszy wolny slot (okna+kadencja)." \
        if dt and dt < now else ""
    ch = " + ".join(_target_label(brand_id, c) for c in (it.get("target_channels") or []))
    body = (it.get("canonical_body") or "(tekst w produkcji)").strip()
    if len(body) > 2500:
        body = body[:2500] + "\n[...]"
    n_media = len(it.get("media") or [])
    med = f"\n🖼 zalaczniki: {n_media}" if n_media else ""
    text = (f"📦 Material {idx + 1} z {len(items)}\n\n🕐 {when}{stale}\n📣 {ch}{med}\n"
            f"📌 {it['master_theme'][:200]}\n\n{body}")
    iid = str(it["id"])
    prev_id = str(items[idx - 1]["id"]) if idx > 0 else iid
    next_id = str(items[idx + 1]["id"]) if idx < len(items) - 1 else iid
    kb = {"inline_keyboard": [
        [{"text": "✅ Zatwierdz", "callback_data": f"matnav:ok:{iid}"},
         {"text": "✅⏭ Na koniec kolejki", "callback_data": f"matnav:okq:{iid}"}],
        [{"text": "❌ Odrzuc", "callback_data": f"matnav:no:{iid}"},
         {"text": "🔄 Inny kat", "callback_data": f"matnav:angle:{iid}"}],
        [{"text": "⬅️", "callback_data": f"matnav:show:{prev_id}"},
         {"text": f"{idx + 1}/{len(items)}", "callback_data": "matnav:pos:-"},
         {"text": "➡️", "callback_data": f"matnav:show:{next_id}"}],
        [{"text": f"✅ Zatwierdz WSZYSTKIE ({len(items)})", "callback_data": "matnav:all:-"}],
    ]}
    return text, kb


def _end_of_queue_slot(item_id, brand_id="AGS"):
    """Koniec kolejki = dzien PO ostatnim zaplanowanym slocie, o godzinie z oryginalnego slotu
    (fallback 10:00). Dokladne dopasowanie kadencji robi planer/rozmowa ('przesun na czwartek 14')."""
    row = db.fetchone(
        """SELECT MAX(scheduled_for) AS m FROM content_items
           WHERE brand_id=%s AND scheduled_for IS NOT NULL
             AND status IN ('planned','drafting','needs_approval','approved','dispatching')""", (brand_id,))
    now = datetime.datetime.now(WARSAW)
    m = row.get("m") if row else None
    base = m.astimezone(WARSAW) if m and m > now else now
    orig = db.fetchone("SELECT scheduled_for FROM content_items WHERE id=%s", (item_id,))
    o = orig["scheduled_for"].astimezone(WARSAW) if orig and orig.get("scheduled_for") else None
    hh, mm = (o.hour, o.minute) if o else (10, 0)
    return (base + datetime.timedelta(days=1)).replace(hour=hh, minute=mm, second=0, microsecond=0)


def handle(payload, wake_event=None):
    """Callbacki matdec:<id>:<akcja> + matnav:<akcja>:<arg> (n8n = transport, galaz mat*)."""
    raw = str(payload.get("raw") or "")
    chat_id = payload.get("chat_id")
    message_id = payload.get("message_id")

    def edit(text, kb=None):
        body = {"chat_id": chat_id, "message_id": message_id, "text": text[:4000]}
        if kb:
            body["reply_markup"] = kb
        r = _tg("editMessageText", body)
        if not (r and r.get("ok")):
            _tg("sendMessage", {"chat_id": chat_id, "text": text[:4000], **({"reply_markup": kb} if kb else {})})

    parts = raw.split(":", 2)
    family = parts[0]
    if family == "matdec" and len(parts) == 3:
        item_id, act = parts[1], parts[2]
        row = db.fetchone("SELECT master_theme, status FROM content_items WHERE id=%s", (item_id,))
        if not row or row["status"] != "draft":
            edit("Ten material zostal juz rozstrzygniety.")
            return
        if act == "queue":
            db.set_item_status(item_id, "planned")
            if wake_event:
                wake_event.set()
            edit(f"📥 W kolejce: \"{row['master_theme'][:200]}\" - produkcja rusza, publikacja w slocie.")
        elif act == "now":
            db.execute("UPDATE content_items SET scheduled_for=NULL, updated_at=NOW() WHERE id=%s", (item_id,))
            db.set_item_status(item_id, "planned")
            if wake_event:
                wake_event.set()
            edit(f"🚀 Na dzis: \"{row['master_theme'][:200]}\" - produkcja od razu; po zatwierdzeniu "
                 f"tekstu CM przydzieli najblizszy wolny slot (dzis, w oknie publikacji).")
        elif act == "drop":
            db.set_item_status(item_id, "rejected")
            edit(f"❌ Odrzucony: \"{row['master_theme'][:200]}\".")
        return

    # matnav
    action = parts[1] if len(parts) > 1 else ""
    arg = parts[2] if len(parts) > 2 else ""
    if action == "pos":
        return
    if action in ("first", "show"):
        text, kb = _card(arg if action == "show" else None)
        edit(text, kb)
        return
    if action == "all":
        items = pending_items()
        for it in items:
            db.set_item_status(it["id"], "approved")
        if wake_event:
            wake_event.set()
        edit(f"✅ Zatwierdzone wszystkie: {len(items)} materialow idzie do publikacji w slotach.")
        return
    if action in ("ok", "no"):
        db.set_item_status(arg, "approved" if action == "ok" else "rejected")
        if action == "ok" and wake_event:
            wake_event.set()
        head = "✅ Zatwierdzony -> publikacja w slocie.\n\n" if action == "ok" else "❌ Odrzucony.\n\n"
        text, kb = _card()
        edit(head + text, kb)
        return
    if action == "okq":
        # feedback Tomasza 05/07 v2: 'zatwierdz, ale przerzuc na koniec kolejki' (minione sloty!)
        slot = _end_of_queue_slot(arg)
        db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s", (slot, arg))
        db.set_item_status(arg, "approved")
        if wake_event:
            wake_event.set()
        when = f"{slot.strftime('%d/%m %H:%M')}"
        text, kb = _card()
        edit(f"✅⏭ Zatwierdzony na koniec kolejki -> publikacja {when}.\n\n" + text, kb)
        return
    if action == "angle":
        # v3 (feedback 06/07): Tomasz SAM mowi jaki kat i co ma byc w tresci - CM czeka na wiadomosc.
        # Material parkuje jako 'draft' (znika z kart, nie lapie go stan awaryjny) do czasu wskazowek.
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (arg,))
        db.set_item_status(arg, "draft")
        _state_set("cm_pending_angle", {"item_id": str(arg),
                                        "ts": datetime.datetime.now(WARSAW).isoformat()})
        text, kb = _card()
        edit(f"🔄 OK - napisz mi teraz JEDNA wiadomoscia: jaki kat i co ma byc w tresci dla:\n"
             f"\"{(row or {}).get('master_theme', '')[:150]}\"\n"
             f"(albo napisz 'auto' - sam przeformuluje). Material czeka poza kolejka.\n\n" + text, kb)
        return


def pending_angle():
    """Czy CM czeka na wskazowki kata od Tomasza (okno 45 min)? Zwraca item_id albo None."""
    st = _state_get("cm_pending_angle")
    iid, ts = st.get("item_id"), st.get("ts")
    if not (iid and ts):
        return None
    age = datetime.datetime.now(WARSAW) - datetime.datetime.fromisoformat(ts)
    return iid if age.total_seconds() < 45 * 60 else None


def apply_angle_guidance(text, wake_event=None):
    """Wiadomosc Tomasza po 'Inny kat': przeformuluj temat WG JEGO wskazowek (kat + wymagana tresc
    laduja w temacie-matce, ktory jest promptem generatora) -> produkcja."""
    iid = pending_angle()
    if not iid:
        return None
    _state_set("cm_pending_angle", {})
    row = db.fetchone("SELECT master_theme, brand_id FROM content_items WHERE id=%s", (iid,))
    if not row:
        return "Nie znajduje juz tego materialu - odpal karty jeszcze raz."
    if text.strip().lower() in ("auto", "sam", "sam wybierz"):
        from .planner import _reangle_theme
        _reangle_theme(iid, row["brand_id"])
    else:
        from .brand import load_brand
        from .generate import client
        from . import tasks
        brand = load_brand(row["brand_id"])
        model, tier, source = tasks.model_for("plan_angle")
        resp = client().messages.create(
            model=model, max_tokens=400, thinking={"type": "disabled"},
            system=[{"type": "text", "text": f"Glos marki (skrot):\n{brand['voice_bible'][:1500]}"}],
            messages=[{"role": "user", "content":
                       f"Przeformuluj temat-matke posta wg WSKAZOWEK wlasciciela (jego kat jest "
                       f"nadrzedny; wymagania tresci wpisz do tematu, bo temat = prompt generatora). "
                       f"Zachowaj ewentualny prefiks [ARTYKUL]. Zwroc TYLKO nowy temat.\n\n"
                       f"OBECNY TEMAT: {row['master_theme']}\n\nWSKAZOWKI: {text.strip()[:800]}"}])
        tasks.log_task("plan_angle", tier, model, source, getattr(resp, "usage", None), iid)
        new_theme = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        if new_theme:
            db.execute("UPDATE content_items SET master_theme=%s, updated_at=NOW() WHERE id=%s",
                       (new_theme, iid))
    db.set_item_status(iid, "planned")
    if wake_event:
        wake_event.set()
    nrow = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (iid,))
    return (f"🔄 Przyjete. Nowy temat: \"{(nrow or {}).get('master_theme', '')[:200]}\"\n"
            f"Material wraca do produkcji - przyjdzie jako karta do zatwierdzenia.")


# ---------------- S4: niedzielne przypomnienia + fallback 23:00 ----------------
def sunday_guard():
    """Wolane z petli workera (30s). Niedziela: paczka needs_approval bez decyzji ->
    przypomnienie co 15 min w oknie 21:30-23:00; o 23:00 CM sam zatwierdza material
    z najblizszym slotem (wstepnie poniedzialek) + alert na bocie #2. Kanon 11c bez zmian."""
    now = datetime.datetime.now(WARSAW)
    if now.weekday() != 6:
        return
    n = len(pending_items())
    if not n:
        return
    today = now.strftime("%Y-%m-%d")
    minutes = now.hour * 60 + now.minute
    start = REMIND_START[0] * 60 + REMIND_START[1]
    fallback = FALLBACK_AT[0] * 60 + FALLBACK_AT[1]

    if start <= minutes < fallback:
        st = _state_get("cm_sunday_remind")
        last = st.get("last") if st.get("date") == today else None
        if last is None or (now - datetime.datetime.fromisoformat(last)).total_seconds() >= REMIND_EVERY_MIN * 60:
            chat = _admin_chat()
            if chat:
                kb = {"inline_keyboard": [[{"text": f"🔍 Przegladaj ({n})", "callback_data": "matnav:first:-"}]]}
                _tg("sendMessage", {"chat_id": chat,
                                    "text": f"⏰ Sprawdz i zatwierdz: {n} materialow czeka na decyzje. "
                                            f"O {FALLBACK_AT[0]}:00 wybiore material na poniedzialek sam.",
                                    "reply_markup": kb})
            _state_set("cm_sunday_remind", {"date": today, "last": now.isoformat()})
        return

    if minutes >= fallback:
        st = _state_get("cm_sunday_fallback")
        if st.get("date") == today:
            return
        items = pending_items()
        # preferuj material z PRZYSZLYM slotem (wstepnie poniedzialkowy); miniony slot po approve
        # publikowalby sie OD RAZU w nocy - przy samych minionych przypinamy poniedzialek 10:00
        pick = next((it for it in items if it.get("scheduled_for")
                     and it["scheduled_for"].astimezone(WARSAW) > now), None)
        if pick is None:
            pick = items[0]
            monday = (now + datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s",
                       (monday, pick["id"]))
        db.set_item_status(pick["id"], "approved")
        try:
            db.execute(
                "INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES ('cm','AUTONOMOUS_DECISION',%s,%s)",
                (f"Niedzielny fallback 23:00: brak przegladu paczki ({n} szt.) - wybieram material na "
                 f"najblizszy slot: {pick['master_theme'][:70]}",
                 Jsonb({"content_item_id": str(pick["id"]), "trigger": "sunday_2300_fallback"})))
        except Exception:
            pass
        logbot.send(f"⚠️ NIEDZIELA 23:00: paczka bez przegladu ({n} materialow). Zatwierdzilem sam material "
                    f"na najblizszy slot: {pick['master_theme'][:80]}. Reszta czeka na Twoja decyzje.")
        _state_set("cm_sunday_fallback", {"date": today, "picked": str(pick["id"])})
