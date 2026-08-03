# -*- coding: utf-8 -*-
"""Przeglad materialow + decyzje intake (feedback Tomasza 05/07, spec docs/cm/CM_UX_FEEDBACK_05072026.md).
S2: material z rozmowy dostaje guziki [Do kolejki]/[Dzis]/[Odrzuc] (matdec:) zamiast cichego 'planned'.
S3: wygenerowane materialy (needs_approval) przegladane KARTA z ⬅️➡️ (matnav:, wzorzec plannav);
    seria osobnych wiadomosci tylko gdy czeka 1 material - od 2 w gore jedna zbiorcza wiadomosc.
S4: niedziela: przypomnienia co 15 min (21:30-23:00), o 23:00 CM sam zatwierdza material na
    poniedzialkowy slot + alert na bocie #2 (rozszerzenie kanonu 11c, 11c bez zmian)."""
import datetime
import json
import traceback
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from . import db, config, logbot, slots
from . import brand as _brand

WARSAW = ZoneInfo("Europe/Warsaw")
REMIND_START = (21, 30)   # niedziela: start okna przypomnien
REMIND_EVERY_MIN = 15
FALLBACK_AT = (23, 0)     # niedziela: autonomiczny wybor materialu


def _tg(method, payload):
    from . import conversation
    return conversation._tg(method, payload)


def _tg_upload_photo(chat_id, png_bytes, caption):
    """Upload bajtow obrazu do Telegrama (multipart). Zwraca file_id (Telegram = magazyn,
    my trzymamy tylko identyfikator) albo None."""
    import httpx
    from . import config
    tok = config.TELEGRAM_BOT_TOKEN
    if not tok:
        return None
    try:
        r = httpx.post(f"https://api.telegram.org/bot{tok}/sendPhoto",
                       data={"chat_id": str(chat_id), "caption": caption[:1000]},
                       files={"photo": ("gen.png", png_bytes, "image/png")}, timeout=60)
        j = r.json()
        photos = ((j.get("result") or {}).get("photo") or [])
        return photos[-1]["file_id"] if photos else None
    except Exception:
        return None


def _tg_send_document(chat_id, filename, text, caption=""):
    """Task #89 (12/07): long-form NIE miesci sie w wiadomosci Telegrama (limit 4096) - artykul
    jedzie jako zalacznik .md (multipart, wzorzec _tg_upload_photo). Zwraca True/False."""
    import httpx
    from . import config
    tok = config.TELEGRAM_BOT_TOKEN
    if not tok:
        return False
    try:
        r = httpx.post(f"https://api.telegram.org/bot{tok}/sendDocument",
                       data={"chat_id": str(chat_id), "caption": caption[:1000]},
                       files={"document": (filename, text.encode("utf-8"), "text/markdown")}, timeout=60)
        return bool(r.json().get("ok"))
    except Exception:
        return False


def log_learning(subagent_id, brand_id, content_item_id, proposed, final, correction_type, notes=None):
    """Task #87 (12/07): petla nauki - KAZDA decyzja Tomasza o tresci laduje w agent_learning_log
    (accepted/edited/rejected/replaced). Czyta ja generacja (generate._learning_digest). Nigdy nie
    wywraca produkcji (tabela przed DDL 020 = cichy pass)."""
    try:
        db.execute(
            """INSERT INTO agent_learning_log
               (subagent_id, brand_id, content_item_id, proposed_content, final_content, diff, correction_type, notes)
               VALUES (%s,%s,%s,%s,%s,NULL,%s,%s)""",
            (str(subagent_id)[:100], str(brand_id)[:50], content_item_id,
             (proposed or "")[:6000], (final or None), correction_type, (notes or None)))
    except Exception:
        traceback.print_exc()  # AP-306: petla nauki (agent_learning_log) nie moze gasnac po cichu


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
def pending_items(brand_id=None):
    # task #83 (12/07): przeglad obejmuje WSZYSTKIE marki (default), filtr per marka opcjonalny
    return db.fetchall(
        """SELECT id, brand_id, master_theme, target_channels, scheduled_for, canonical_body, media
           FROM content_items
           WHERE (%s::text IS NULL OR brand_id=%s) AND status='needs_approval'
           ORDER BY scheduled_for NULLS LAST, created_at""", (brand_id, brand_id))


def _find_done_item(theme_fragment, brand_id="AGS"):
    """Task #89 symptom 4 (12/07): karta NIE otwierala sie dla approved. Szukaj materialu poza
    przegladem (approved/handed_off/published) po fragmencie tematu - widok bez decyzji."""
    if not theme_fragment:
        return None
    return db.fetchone(
        """SELECT id, master_theme, status, target_channels, scheduled_for, canonical_body, media
           FROM content_items
           WHERE brand_id=%s AND status IN ('approved',%s,'published')
             AND master_theme ILIKE %s
           ORDER BY updated_at DESC LIMIT 1""",
        (brand_id, config.STATUS_HANDED_OFF, f"%{theme_fragment}%"))


_VIEW_STATUS_PL = {"approved": "ZATWIERDZONY (czeka na publikacje)",
                   # D-006 (02/08): "W PUBLIKACJI" obiecywalo sekundy, a ten stan normalnie
                   # trwa DNI - material czeka, az WSZYSTKIE wiersze jego serii sie opublikuja.
                   # Manager zglosil 27/07 "zawieszony post"; odczyt pokazal siedem materialow,
                   # wszystkie zdrowe, najstarszy 51 godzin i poprawnie, bo sloty siegaly
                   # 4 sierpnia. Etykieta mowi teraz, CO SIE STALO, a nie co sie wlasnie dzieje.
                   # D-008 (03/08): wartosc w bazie mowi juz to samo, co etykieta - 'handed_off'.
                   config.STATUS_HANDED_OFF: "ROZESLANY DO KOLEJKI", "published": "OPUBLIKOWANY"}

# Stany wiersza KOLEJKI, ktore NIE sa jeszcze terminalne (ta sama lista, co w conversation.py).
# D-008: 'dispatching' ponizej ZOSTAJE - to slownik post_queue, nie content_items.
_PQ_CZEKA = ("review", "held", "scheduled", "queued", "dispatching")


def _stan_rozsylki(item_id):
    """Ile wierszy materialu jeszcze czeka i na kiedy najblizszy (D-006).

    Sedno zgloszenia Managera z 27/07: "ani system, ani CM nie potrafili powiedziec, czy jest
    w trakcie wysylki, czy zawisl". Sama nazwa stanu tego nie rozstrzyga i rozstrzygnac nie moze.
    Rozstrzyga to, ILE WIERSZY zostalo i KIEDY maja pojsc. Jedno zapytanie, nie N+1."""
    try:
        r = db.fetchone(
            f"""SELECT COUNT(*) AS wszystkie,
                       COUNT(*) FILTER (WHERE status IN {_PQ_CZEKA}) AS czeka,
                       MIN(scheduled_for) FILTER (WHERE status IN {_PQ_CZEKA}) AS najblizszy,
                       MAX(scheduled_for) FILTER (WHERE status IN {_PQ_CZEKA}) AS ostatni
                  FROM post_queue WHERE content_item_id=%s::uuid""", (str(item_id),))
    except Exception:
        traceback.print_exc()
        return ""
    if not r or not int(r.get("wszystkie") or 0):
        return ""
    czeka = int(r.get("czeka") or 0)
    if not czeka:
        # Zero oczekujacych przy tym statusie to JEDYNY przypadek, ktory naprawde wyglada
        # na zawieszenie - i dopiero teraz da sie go odroznic od zdrowego czekania.
        return (f"\n⚠️ wszystkie {r['wszystkie']} wpisow ma juz stan koncowy, a material nadal "
                f"czeka - to wyglada na zawieszenie, zglos")
    czesci = [f"czeka {czeka} z {r['wszystkie']} wpisow"]
    for etykieta, klucz in (("najblizszy", "najblizszy"), ("ostatni", "ostatni")):
        d = r.get(klucz)
        if d:
            czesci.append(f"{etykieta} {d.astimezone(WARSAW).strftime('%d/%m %H:%M')}")
    return "\n⏳ " + ", ".join(czesci)


def _view_card(it, brand_id="AGS"):
    """Karta PODGLADU materialu po decyzji (view-only): bez guzikow decyzji, z pelna trescia
    na zadanie (guzik 📄 -> matnav:fulltext)."""
    from .planner import _DAYS_PL, _target_label
    dt = it["scheduled_for"].astimezone(WARSAW) if it.get("scheduled_for") else None
    when = f"{_DAYS_PL[dt.weekday()]} {dt.strftime('%d/%m %H:%M')}" if dt else "-"
    ch = " + ".join(_target_label(brand_id, c) for c in (it.get("target_channels") or []))
    body = (it.get("canonical_body") or "(brak tresci)").strip()
    n_media = sum(1 for m in (it.get("media") or []) if (m or {}).get("file_id"))
    # D-006: przy stanie rozsylki sama etykieta nie wystarcza - dokladamy, ile wierszy czeka
    # i na kiedy. To jest roznica miedzy "wysylam od dwoch minut" a "wisi od trzydziestu".
    rozsylka = _stan_rozsylki(it["id"]) if it.get("status") == config.STATUS_HANDED_OFF else ""
    text = (f"🔒 {_VIEW_STATUS_PL.get(it['status'], it['status'].upper())} - podglad, bez decyzji"
            f"{rozsylka}\n\n"
            f"🕐 {when}\n📣 {ch}" + (f"\n🖼 zalaczniki: {n_media}" if n_media else "") + "\n"
            f"📌 {it['master_theme'][:200]}\n\n{body[:500]}"
            + ("..." if len(body) > 500 else ""))
    kb = {"inline_keyboard": [[{"text": "📄 Pokaz pelna tresc (do skopiowania)",
                                "callback_data": f"matnav:fulltext:{it['id']}"}]]}
    return text, kb


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


def _match_day(it, day):
    """(d): czy material celuje w 'today'/'tomorrow' wg scheduled_for (czas WAW)."""
    dt = it.get("scheduled_for")
    if not dt:
        return False
    d = dt.astimezone(WARSAW).date()
    today = datetime.datetime.now(WARSAW).date()
    if day == "today":
        return d == today
    if day == "tomorrow":
        return d == today + datetime.timedelta(days=1)
    return False


def send_review_card(chat_id=None, theme_fragment=None, only_with_media=False, day=None):
    """SWIEZA karta przegladu na dole czatu. v2 (feedback 06/07 'pokaz mi TE karte'):
    theme_fragment / only_with_media / day = karta KONKRETNEGO materialu, nie 1/N od poczatku.
    day (d): 'karty jutro'/'karty dzis' skacze do pierwszego materialu z tego dnia."""
    chat = chat_id or _admin_chat()
    if not chat:
        return False
    # fix 12/07 23:52: ZERO pending = NIE wysylaj pustej karty 'Przeglad zakonczony' (mylila
    # Tomasza i narzedzie raportowalo sukces) - zwroc False, wolajacy powie prawde
    if not pending_items():
        return False
    item_id = None
    if theme_fragment or only_with_media or day:
        for it in pending_items():
            if theme_fragment and theme_fragment.lower() not in (it.get("master_theme") or "").lower():
                continue
            if only_with_media and not any((m or {}).get("file_id") for m in (it.get("media") or [])):
                continue
            if day and not _match_day(it, day):
                continue
            item_id = str(it["id"])
            break
        if item_id is None:
            # Task #89: nie ma w przegladzie -> szukaj w approved/handed_off/published (view-only)
            done = _find_done_item(theme_fragment)
            if not done:
                return False
            vtext, vkb = _view_card(done)
            r = _tg("sendMessage", {"chat_id": chat, "text": vtext[:4000], "reply_markup": vkb})
            _send_media_preview(chat, done)
            return bool(r and r.get("ok"))
    text, kb, it = _card(item_id)
    body = {"chat_id": chat, "text": text[:4000]}
    if kb:
        body["reply_markup"] = kb
    r = _tg("sendMessage", body)
    _send_media_preview(chat, it)
    return bool(r and r.get("ok"))


def add_style_rule(rule):
    """Regula stylu podana WPROST przez Tomasza w rozmowie ('zapamietaj na zawsze') -> style_learned
    (trwale; kazda generacja dostaje regulki w prompcie)."""
    rule = (rule or "").strip()
    if not rule:
        return 0
    cur = _state_get("style_learned")
    arr = (cur.get("rules") or []) if isinstance(cur, dict) else []
    if rule not in arr:
        arr = (arr + [rule])[-30:]
        _state_set("style_learned", {"rules": arr})
    return len(arr)


def _card(item_id=None, brand_id=None, full=False):
    """(text, kb, item) karty materialu; item_id=None -> pierwszy czekajacy.
    v7 (feedback 06/07 11:35): Rozwin/Zwin = pierwszy SZEROKI guzik; ➕/🗑 Media na karcie;
    zdjecia pokazywane AUTOMATYCZNIE pod karta (handle -> _send_media_preview).
    #83: karty wszystkich marek, etykieta marki przy nie-AGS."""
    from .planner import _DAYS_PL, _target_label
    items = pending_items(brand_id)
    if not items:
        return "📦 Przeglad zakonczony - brak materialow do decyzji.", None, None
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
    # (d): nagłówek dnia - DZIŚ/JUTRO/nazwa dnia, do szybkiego skanowania kart
    if dt:
        _dd = dt.date()
        _today = now.date()
        if _dd == _today:
            day_hdr = "📅 DZIŚ"
        elif _dd == _today + datetime.timedelta(days=1):
            day_hdr = "📅 JUTRO"
        else:
            day_hdr = f"📅 {_DAYS_PL[dt.weekday()]} {dt.strftime('%d/%m')}"
    else:
        day_hdr = "📅 bez terminu"
    stale = "\n⚠️ SLOT MINAL - po 'Zatwierdz' CM sam przydzieli najblizszy wolny slot (okna+kadencja)." \
        if dt and dt < now else ""
    it_brand = it.get("brand_id") or "AGS"
    ch = " + ".join(_target_label(it_brand, c) for c in (it.get("target_channels") or []))
    body = (it.get("canonical_body") or "(tekst w produkcji)").strip()
    cap = 3300 if full else 500  # v6: Calosc = w TYM SAMYM okienku (limit Telegrama), Zwin wraca
    truncated = len(body) > cap
    if truncated:
        body = body[:cap] + ("\n[koniec podgladu - pelny tekst przy ✏️ Edytuj]" if full else "...")
    media_all = it.get("media") or []
    n_media = sum(1 for m in media_all if (m or {}).get("file_id"))
    hint = next((m.get("text") for m in media_all if (m or {}).get("kind") == "suggestion"), None)
    # KANON 25/07: zamiast auto-obrazu material niesie SZCZEGOLOWY PROMPT (kind='visual_prompt') -
    # Tomasz generuje grafike recznie. Guzik 📋 Prompt wysle go w calosci; tu skrot na karcie.
    vprompt = next((m.get("text") for m in media_all if (m or {}).get("kind") == "visual_prompt"), None)
    med = f"\n🖼 zalaczniki: {n_media}" if n_media else ""
    if hint:
        med += f"\n🎨 propozycja wizualu: {hint[:220]}"
    if vprompt:
        med += (f"\n📋 SZCZEGOLOWY PROMPT (wygeneruj grafike recznie, pelny pod guzikiem 📋 Prompt):\n"
                f"{vprompt[:400]}" + ("..." if len(vprompt) > 400 else ""))
    dup = next((m.get("text") for m in media_all if (m or {}).get("kind") == "dup_warning"), None)
    if dup:
        med += f"\n⚠️ DUPLIKACJA: {dup[:250]}"
    # paczka #1 Managera pkt 8 (24/07): interpunkcja PL jako FLAGA (nie blokada) dla marek
    # polskojezycznych. Liczona z PELNEJ tresci, nie z przycietego podgladu.
    if it_brand.lower() in ("tnm", "rdc"):
        from . import compliance
        pflags = compliance.pl_comma_flags(it.get("canonical_body") or "", limit=3)
        if pflags:
            med += "\n⚠️ INTERPUNKCJA (sprawdz przecinki): " + "; ".join(pflags)[:300]
    if not n_media:
        med += "\n➕ dodasz: wyslij zdjecie botowi i napisz 'dolacz ostatnie zdjecie'"
    brand_hdr = f"   ·   🏷 {it_brand}" if it_brand != "AGS" else ""
    text = (f"{day_hdr}   ·   📦 Material {idx + 1} z {len(items)}{brand_hdr}\n\n🕐 {when}{stale}\n📣 {ch}{med}\n"
            f"📌 {it['master_theme'][:200]}\n\n{body}")
    iid = str(it["id"])
    # zawijanie (fix 06/07): ⬅️ z pierwszej karty = ostatnia, ➡️ z ostatniej = pierwsza
    prev_id = str(items[(idx - 1) % len(items)]["id"])
    next_id = str(items[(idx + 1) % len(items)]["id"])
    rows = []
    # v7: rozwijanie = PIERWSZY szeroki guzik (wzorzec 'pionowej kreski')
    if full:
        rows.append([{"text": "▲ Zwin tresc ▲", "callback_data": f"matnav:show:{iid}"}])
    elif truncated:
        rows.append([{"text": "▼ Rozwin cala tresc ▼", "callback_data": f"matnav:full:{iid}"}])
    rows.append([{"text": "✅ Zatwierdz", "callback_data": f"matnav:ok:{iid}"},
                 {"text": "✅⏭ Na koniec kolejki", "callback_data": f"matnav:okq:{iid}"}])
    rows.append([{"text": "❌ Odrzuc", "callback_data": f"matnav:no:{iid}"},
                 {"text": "🔄 Inny kat", "callback_data": f"matnav:angle:{iid}"},
                 {"text": "✏️ Edytuj", "callback_data": f"matnav:edit:{iid}"}])
    media_row = [{"text": "➕ Media", "callback_data": f"matnav:madd:{iid}"},
                 {"text": "🎨 Generuj", "callback_data": f"matnav:gen:{iid}"},
                 {"text": "📋 Prompt", "callback_data": f"matnav:iprompt:{iid}"}]
    if n_media:
        media_row.append({"text": f"🗑 Media ({n_media})", "callback_data": f"matnav:mdel:{iid}"})
    rows.append(media_row)
    rows.append([{"text": "⬅️", "callback_data": f"matnav:show:{prev_id}"},
                 {"text": f"{idx + 1}/{len(items)}", "callback_data": "matnav:pos:-"},
                 {"text": "➡️", "callback_data": f"matnav:show:{next_id}"}])
    rows.append([{"text": f"✅ Zatwierdz WSZYSTKIE ({len(items)})", "callback_data": "matnav:all:-"}])
    return text, {"inline_keyboard": rows}, it


def _send_media_preview(chat_id, item):
    """v7: multimedia widoczne OD RAZU pod karta (bez klikania). Anty-powtorka: nie wysylaj
    ponownie dla tego samego materialu z rzedu."""
    if not item:
        return
    files = [(m["file_id"], (m or {}).get("kind", "photo")) for m in (item.get("media") or [])
             if (m or {}).get("file_id")][:4]
    if not files:
        return
    st = _state_get("cm_last_media_preview")
    if st.get("item_id") == str(item["id"]):
        return
    for fid, kind in files:
        if kind == "video":
            _tg("sendVideo", {"chat_id": chat_id, "video": fid,
                              "caption": f"🎬 POLECI Z POSTEM: {(item.get('master_theme') or '')[:140]}"})
        else:
            _tg("sendPhoto", {"chat_id": chat_id, "photo": fid,
                              "caption": f"🖼 POLECI Z POSTEM: {(item.get('master_theme') or '')[:140]}"})
    _state_set("cm_last_media_preview", {"item_id": str(item["id"])})


def _end_of_queue_slot(item_id, brand_id="AGS"):
    """Koniec kolejki = dzien PO ostatnim zaplanowanym slocie, o godzinie z oryginalnego slotu
    (fallback 10:00). Dokladne dopasowanie kadencji robi planer/rozmowa ('przesun na czwartek 14')."""
    row = db.fetchone(
        """SELECT MAX(scheduled_for) AS m FROM content_items
           WHERE brand_id=%s AND scheduled_for IS NOT NULL
             AND status IN ('planned','drafting','needs_approval','approved',%s)""",
        (brand_id, config.STATUS_HANDED_OFF))
    now = datetime.datetime.now(WARSAW)
    m = row.get("m") if row else None
    base = m.astimezone(WARSAW) if m and m > now else now
    orig = db.fetchone("SELECT scheduled_for, target_channels FROM content_items WHERE id=%s",
                       (item_id,))
    o = orig["scheduled_for"].astimezone(WARSAW) if orig and orig.get("scheduled_for") else None
    hh, mm = (o.hour, o.minute) if o else (10, 0)
    kand = (base + datetime.timedelta(days=1)).replace(hour=hh, minute=mm, second=0, microsecond=0)
    # D-001: ten guzik robil z PIATKU SOBOTE jednym tapnieciem, bo brał MAX(slot)+1 dzien
    # i nie pytal o dzien tygodnia. Przesuwamy do najblizszego DOZWOLONEGO dnia.
    kanaly = (orig or {}).get("target_channels") or []
    for _ in range(8):
        if slots.day_ok(kanaly, kand, is_article=False):
            return kand
        kand = kand + datetime.timedelta(days=1)
    return kand


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
            # 'message is not modified' = ta sama tresc (np. 1 karta w kolejce) - NIE duplikuj (fix 06/07)
            if "not modified" in str((r or {}).get("description", "")):
                return
            _tg("sendMessage", {"chat_id": chat_id, "text": text[:4000], **({"reply_markup": kb} if kb else {})})

    def card_bottom(prefix=""):
        """Feedback Tomasza 19/07 ('musze przewijac na gore do okienka z postami'): po decyzji
        NASTEPNA karta przychodzi NOWA wiadomoscia NA DOLE czatu (przy polu pisania), a stara
        karta zostaje wyzej jako martwy znacznik bez guzikow."""
        text, kb, it = _card()
        _tg("sendMessage", {"chat_id": chat_id, "text": (prefix + text)[:4000],
                            **({"reply_markup": kb} if kb else {})})
        _send_media_preview(chat_id, it)

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
    if action == "fulltext":
        # Task #89 (12/07): PELNA tresc materialu (dowolny status) do skopiowania - kawalkami
        # (limit Telegrama 4096), a dlugie/[ARTYKUL] dodatkowo jako plik .md (long-form delivery).
        row = db.fetchone("SELECT id, master_theme, status, canonical_body FROM content_items WHERE id=%s", (arg,))
        if not row:
            edit("Nie znajduje tego materialu.")
            return
        body = (row.get("canonical_body") or "(brak tresci)").strip()
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"📄 PELNA TRESC [{row['status']}]: {row['master_theme'][:150]}"})
        rest = body
        while rest:
            cut = rest.rfind("\n\n", 0, 3900)
            if cut < 1900:
                cut = min(3900, len(rest))
            _tg("sendMessage", {"chat_id": chat_id, "text": rest[:cut]})
            rest = rest[cut:].lstrip()
        if len(body) > 3900 or str(row.get("master_theme") or "").startswith("[ARTYKUL]"):
            _tg_send_document(chat_id, f"material_{row['id']}.md", body,
                              caption=f"📎 Ta sama tresc jako plik (latwiejsze kopiowanie): {row['master_theme'][:120]}")
        return
    if action in ("first", "show"):
        text, kb, it = _card(arg if action == "show" else None)
        edit(text, kb)
        _send_media_preview(chat_id, it)
        return
    if action == "edit":
        # feedback 06/07: 'edytuj tekst' - bot wysyla PELNY tekst, Tomasz odsyla poprawiony,
        # agent podmienia + przegenerowuje warianty + UCZY SIE z roznicy (VOICE_EDIT)
        row = db.fetchone("SELECT master_theme, canonical_body FROM content_items WHERE id=%s", (arg,))
        body = ((row or {}).get("canonical_body") or "").strip()
        if not body:
            edit("Ten material nie ma jeszcze tekstu do edycji.")
            return
        db.set_item_status(arg, "draft")  # poza kartami/awaryjnym na czas edycji
        _state_set("cm_pending_edit", {"item_id": str(arg),
                                       "ts": datetime.datetime.now(WARSAW).isoformat()})
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"✏️ EDYCJA: \"{(row or {}).get('master_theme', '')[:150]}\"\n"
                                    f"Ponizej pelny tekst-matka. Skopiuj, popraw i ODESLIJ CALOSC jedna "
                                    f"wiadomoscia - podmienie tekst, przegeneruje warianty kanalow z Twojej "
                                    f"wersji i zapamietam poprawki (ucze sie Twojego stylu). 'anuluj' = wycofaj."})
        for i in range(0, len(body), 3900):
            _tg("sendMessage", {"chat_id": chat_id, "text": body[i:i + 3900]})
        return
    if action == "pic":
        # 🖼 Podglad (06/07 'gdzie jest zdjecie?'): wyslij zalaczniki pod karte (file_id dziala
        # w sendPhoto bezposrednio - Telegram trzyma pliki trwale)
        row = db.fetchone("SELECT master_theme, media FROM content_items WHERE id=%s", (arg,))
        files = [m["file_id"] for m in ((row or {}).get("media") or []) if (m or {}).get("file_id")][:4]
        if not files:
            edit("Ten material nie ma zalacznikow.")
            return
        for fid in files:
            _tg("sendPhoto", {"chat_id": chat_id, "photo": fid,
                              "caption": f"🖼 Zalacznik: {(row or {}).get('master_theme', '')[:120]}"})
        return
    if action == "madd":
        # v10 (feedback Tomasza 19/07: 'wyswietlanie szesciu ostatnich jest bez sensu'): ➕ Media
        # = OD RAZU tryb "wyslij zdjecie, dopne automatycznie"; galeria schowka TYLKO na zadanie
        # guzikiem (mgal). Okno trybu 10 min z auto-wyjsciem bez zmian.
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (arg,))
        n_photos = (db.fetchone(
            "SELECT COUNT(*) AS n FROM inspirations WHERE metadata->'media'->>'file_id' IS NOT NULL") or {}).get("n") or 0
        _state_set("cm_pending_madd", {"item_id": str(arg),
                                       "ts": datetime.datetime.now(WARSAW).isoformat()})
        kb_rows = []
        if n_photos:
            kb_rows.append([{"text": f"🖼 Pokaz ostatnie ze schowka ({min(n_photos, 6)})",
                             "callback_data": f"matnav:mgal:{arg}"}])
        kb_rows.append([{"text": "✖ Anuluj", "callback_data": "matnav:mcancel:-"}])
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"➕ Wyslij mi teraz zdjecie (zwykla wiadomosc z foto) - dopne je "
                                    f"automatycznie do:\n\"{(row or {}).get('master_theme', '')[:150]}\"\n"
                                    f"(tryb zamknie sie sam po 10 min)",
                            "reply_markup": {"inline_keyboard": kb_rows}})
        return
    if action == "mgal":
        # galeria schowka NA ZADANIE (v10): album ostatnich 6 + guziki wyboru numeru
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (arg,))
        photos = db.fetchall(
            """SELECT id, content, metadata FROM inspirations
               WHERE metadata->'media'->>'file_id' IS NOT NULL ORDER BY created_at DESC LIMIT 6""")
        if not photos:
            _tg("sendMessage", {"chat_id": chat_id, "text": "Schowek bez zdjec - wyslij zdjecie wprost."})
            return
        album = [{"type": ("video" if p["metadata"]["media"].get("kind") == "video" else "photo"),
                  "media": p["metadata"]["media"]["file_id"],
                  "caption": f"{i + 1}. {(p.get('content') or '')[:80]}"}
                 for i, p in enumerate(photos)]
        _tg("sendMediaGroup", {"chat_id": chat_id, "media": album})
        pick_row = [{"text": str(i + 1), "callback_data": f"matnav:mpick:{arg}:{p['id']}"}
                    for i, p in enumerate(photos)]
        kb = {"inline_keyboard": [pick_row, [{"text": "✖ Anuluj", "callback_data": "matnav:mcancel:-"}]]}
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"Wybierz numer dla: \"{(row or {}).get('master_theme', '')[:120]}\" "
                                    f"(albo po prostu wyslij nowe zdjecie).", "reply_markup": kb})
        return
    if action == "mpick":
        # wybor z galerii: matnav:mpick:<item_id>:<inspiration_id>
        import json as _json
        item_id, insp_id = (arg.split(":", 1) + [""])[:2]
        photo = db.fetchone("SELECT id, metadata FROM inspirations WHERE id=%s", (insp_id,))
        item = db.fetchone("SELECT master_theme, media FROM content_items WHERE id=%s", (item_id,))
        if not (photo and item):
            edit("Nie znajduje tego zdjecia albo materialu.")
            return
        fid = photo["metadata"]["media"]["file_id"]
        if any((mm or {}).get("file_id") == fid for mm in (item.get("media") or [])):
            edit(f"To zdjecie jest juz dopiete do: \"{item['master_theme'][:120]}\".")
            return
        desc = {"source": "telegram", "file_id": fid,
                "kind": photo["metadata"]["media"].get("kind", "photo"), "inspiration_id": photo["id"]}
        db.execute("UPDATE content_items SET media = media || %s::jsonb, updated_at=NOW() WHERE id=%s",
                   (_json.dumps([desc]), item_id))
        db.execute("UPDATE post_queue SET media = media || %s::jsonb WHERE content_item_id=%s AND status IN ('review','held','scheduled')",
                   (_json.dumps([desc]), item_id))
        _state_set("cm_pending_madd", {})
        _state_set("cm_last_media_preview", {})
        _note_attach(item["master_theme"])
        edit(f"🖼 Dopiete do: \"{item['master_theme'][:150]}\" - poleci razem z publikacja. "
             f"Chcesz wiecej? Tap ➕ Media na karcie jeszcze raz.")
        return
    if action == "gen":
        # ETAP 2a (06/07): 🎨 Generuj - obraz z sugestii wizualu (OpenAI), podglad NA Telegramie
        # staje sie magazynem (file_id z sendPhoto = zalacznik). ~pol minuty.
        import json as _json
        row = db.fetchone("SELECT master_theme, canonical_body, media FROM content_items WHERE id=%s", (arg,))
        if not row:
            edit("Nie znajduje materialu.")
            return
        hint = next((m.get("text") for m in (row.get("media") or [])
                     if (m or {}).get("kind") == "suggestion"), "")
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"🎨 Generuje obraz (~pol minuty): {(hint or row['master_theme'])[:150]}"})
        from .generate import generate_image, generate_image_prompt
        from .brand import load_brand as _lb
        # 10/07 (feedback Tomasza 'ma byc premium, prompt bardzo szczegolowy'): pelny prompt pisze
        # Sonnet; stary jednolinijkowy szablon zostaje TYLKO jako fallback awaryjny.
        try:
            prompt = generate_image_prompt(_lb("AGS"), row["master_theme"], row.get("canonical_body"),
                                           hint, content_item_id=arg)
        except Exception:
            traceback.print_exc()
            prompt = (f"Social media graphic for a tech build-in-public post. Visual idea: "
                      f"{hint or 'clean conceptual illustration of the post theme'}. Post theme: "
                      f"{row['master_theme'][:300]}. Style: clean, professional, modern tech aesthetic, "
                      f"high contrast, no watermarks, no fake photographs of real events, "
                      f"no real people's faces; illustration/diagram/typographic style welcome.")
        try:
            png = generate_image(prompt)
        except Exception as e:
            _tg("sendMessage", {"chat_id": chat_id, "text": f"🎨 Generowanie nie wyszlo: {str(e)[:200]}"})
            return
        fid = _tg_upload_photo(chat_id, png,
                               f"🎨 WYGENEROWANE - POLECI Z POSTEM: {row['master_theme'][:120]}")
        if not fid:
            _tg("sendMessage", {"chat_id": chat_id, "text": "Nie udalo sie wgrac obrazu na Telegram."})
            return
        desc = {"source": "telegram", "file_id": fid, "kind": "photo", "generated": True,
                "image_prompt": prompt[:3400]}  # 19/07: prompt zapamietany - guzik 📋 Prompt go wysle
        db.execute("UPDATE content_items SET media = media || %s::jsonb, updated_at=NOW() WHERE id=%s",
                   (_json.dumps([desc]), arg))
        db.execute("UPDATE post_queue SET media = media || %s::jsonb WHERE content_item_id=%s AND status IN ('review','held','scheduled')",
                   (_json.dumps([desc]), arg))
        _note_attach(row["master_theme"])
        _state_set("cm_last_media_preview", {"item_id": str(arg)})
        text, kb, it = _card(arg)
        edit(text, kb)
        return
    if action == "iprompt":
        # 19/07 (feedback Tomasza 'potrzebuje prompt do wklejenia do dowolnego modelu'): 📋 Prompt
        # = pelny prompt graficzny (kanon barw/typografii) jako wiadomosc do skopiowania. Bierze
        # zapamietany z ostatniej generacji; brak = pisze swiezy (Sonnet). Wynik z zewnetrznego
        # generatora dopinasz przez ➕ Media.
        row = db.fetchone("SELECT master_theme, canonical_body, media FROM content_items WHERE id=%s", (arg,))
        if not row:
            edit("Nie znajduje materialu.")
            return
        stored = next((m.get("image_prompt") for m in reversed(row.get("media") or [])
                       if (m or {}).get("image_prompt")), None)
        if stored:
            prompt = stored
        else:
            hint = next((m.get("text") for m in (row.get("media") or [])
                         if (m or {}).get("kind") == "suggestion"), "")
            _tg("sendMessage", {"chat_id": chat_id, "text": "📋 Pisze prompt graficzny (~15 s)..."})
            from .generate import generate_image_prompt
            from .brand import load_brand as _lb
            try:
                prompt = generate_image_prompt(_lb("AGS"), row["master_theme"], row.get("canonical_body"),
                                               hint, content_item_id=arg)
            except Exception as e:
                _tg("sendMessage", {"chat_id": chat_id, "text": f"📋 Nie wyszlo: {str(e)[:180]}"})
                return
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"📋 PROMPT DO WKLEJENIA (dowolny generator; wynik dopnij przez ➕ Media):"})
        for i in range(0, len(prompt), 3900):
            _tg("sendMessage", {"chat_id": chat_id, "text": prompt[i:i + 3900]})
        return
    if action == "mnew":
        _state_set("cm_pending_madd", {"item_id": str(arg),
                                       "ts": datetime.datetime.now(WARSAW).isoformat()})
        edit("📤 Wyslij mi teraz zdjecie (zwykla wiadomosc z foto) - dopne je automatycznie. "
             "Tryb zamknie sie sam po 10 min.")
        return
    if action == "mcancel":
        _state_set("cm_pending_madd", {})
        edit("✖ Tryb dodawania mediow zamkniety.")
        return
    if action == "mdel":
        # v7: 🗑 Media - zdejmij zalaczniki (sugestia wizualu zostaje)
        import json as _json
        row = db.fetchone("SELECT media FROM content_items WHERE id=%s", (arg,))
        kept = [m for m in ((row or {}).get("media") or []) if not (m or {}).get("file_id")]
        db.execute("UPDATE content_items SET media=%s::jsonb, updated_at=NOW() WHERE id=%s",
                   (_json.dumps(kept), arg))
        db.execute("UPDATE post_queue SET media='[]'::jsonb WHERE content_item_id=%s AND status IN ('review','held','scheduled')",
                   (arg,))
        _state_set("cm_last_media_preview", {})
        text, kb, it = _card(arg)
        edit("🗑 Zalaczniki usuniete.\n\n" + text, kb)
        return
    if action == "full":
        # v6 (feedback): Calosc w TYM SAMYM okienku karty (+ Zwin); osobne wiadomosci tylko przy Edytuj
        text, kb, it = _card(arg, full=True)
        edit(text, kb)
        return
    if action == "all":
        items = pending_items()
        for it in items:
            db.set_item_status(it["id"], "approved")
            log_learning(f"cm:{it.get('brand_id', 'AGS')}", it.get("brand_id", "AGS"), it["id"],
                         it.get("canonical_body") or "", it.get("canonical_body") or "",
                         "accepted", notes="karta matnav (zatwierdz wszystkie)")  # #87
        if wake_event:
            wake_event.set()
        edit(f"✅ Zatwierdzone wszystkie: {len(items)} materialow idzie do publikacji w slotach.")
        _tg("sendMessage", {"chat_id": chat_id,  # paragon tez na dole (19/07: zero przewijania)
                            "text": f"✅ Zatwierdzone wszystkie: {len(items)} materialow idzie do publikacji w slotach."})
        return
    if action in ("ok", "no"):
        db.set_item_status(arg, "approved" if action == "ok" else "rejected")
        if action == "no":
            # PORZADKI 19/07 (B): odrzucenie karty sprzata tez wiersze kolejki - dowod: pq 245
            # odrzuconego artykulu wisial w 'review' na zawsze (nie publikowal sie, ale smiecil
            # podglady i liczniki slotow).
            db.execute("UPDATE post_queue SET status='rejected' "
                       "WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued')",
                       (arg,))
        if action == "ok" and wake_event:
            wake_event.set()
        # BUG-FIX 12/07 ('kliknalem odrzuc i nic sie nie stalo'): _card() zwraca 3 wartosci od v7 -
        # rozpakowanie do 2 wybuchalo PO zapisie statusu, wyjatek ginal w watku, zero feedbacku.
        row = db.fetchone("SELECT master_theme, brand_id, canonical_body FROM content_items WHERE id=%s", (arg,))
        log_learning(f"cm:{(row or {}).get('brand_id', 'AGS')}", (row or {}).get("brand_id", "AGS"), arg,
                     (row or {}).get("canonical_body") or "",
                     ((row or {}).get("canonical_body") if action == "ok" else None),
                     "accepted" if action == "ok" else "rejected", notes="karta matnav")
        theme = ((row or {}).get("master_theme") or "")[:120]
        # PARAGON DECYZJI (wymog Tomasza 12/07): potwierdzenie ZAWSZE nowa wiadomoscia na dole -
        # edycja karty bywa zawodna i NIE jest kanalem potwierdzenia.
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": (f"✅ Zatwierdzone: \"{theme}\" - publikacja w slocie."
                                     if action == "ok" else f"❌ Odrzucone: \"{theme}\" - decyzja zapisana.")})
        # stara karta = martwy znacznik (edit bez reply_markup zdejmuje guziki); nastepna NA DOL (19/07)
        edit(("✅ " if action == "ok" else "❌ ") + f"\"{theme}\" - rozstrzygniete, karta ponizej.")
        card_bottom()
        return
    if action == "okq":
        # feedback Tomasza 05/07 v2: 'zatwierdz, ale przerzuc na koniec kolejki' (minione sloty!)
        slot = _end_of_queue_slot(arg)
        db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s", (slot, arg))
        db.set_item_status(arg, "approved")
        if wake_event:
            wake_event.set()
        when = f"{slot.strftime('%d/%m %H:%M')}"
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (arg,))
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"✅⏭ Zatwierdzone na koniec kolejki: "
                                    f"\"{((row or {}).get('master_theme') or '')[:120]}\" - publikacja {when}."})
        edit(f"✅⏭ \"{((row or {}).get('master_theme') or '')[:120]}\" - rozstrzygniete, karta ponizej.")
        card_bottom()
        return
    if action == "angle":
        # v3 (feedback 06/07): Tomasz SAM mowi jaki kat - CM czeka na wiadomosc. v4: prosba o
        # wskazowki idzie NOWA wiadomoscia NA DOL czatu (nie w gore historii), karta w miejscu
        # przechodzi do nastepnego materialu.
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (arg,))
        db.set_item_status(arg, "draft")
        _state_set("cm_pending_angle", {"item_id": str(arg),
                                        "ts": datetime.datetime.now(WARSAW).isoformat()})
        edit(f"🔄 \"{(row or {}).get('master_theme', '')[:120]}\" - czeka na Twoj kat, karta ponizej.")
        card_bottom()  # 19/07: nastepna karta na dol; prosba o kat POD nia (najblizej pola pisania)
        _tg("sendMessage", {"chat_id": chat_id,
                            "text": f"🔄 Napisz mi teraz JEDNA wiadomoscia: jaki kat i co ma byc w tresci dla:\n"
                                    f"\"{(row or {}).get('master_theme', '')[:180]}\"\n"
                                    f"(albo 'auto' - sam przeformuluje). Material czeka poza kolejka; "
                                    f"po Twojej odpowiedzi potwierdze nowy temat i pojdzie do produkcji."})
        return


def modes_snapshot():
    """Migawka stanu trybow dla ROZMOWY CM (fix 06/07: LLM twierdzil 'nie dopialem zadnego
    zdjecia' sekunde przed prawdziwym przypieciem przez straznika). Zwraca tekst PL.
    20/07 (split-brain podkladu): stan podkladu niedzielnego TEZ tu - CM nie ma prawa twierdzic
    'research nie wrocil', gdy podklad juz dostarczony i lezy w brand_config."""
    lines = []
    sb = _state_get("cm_sunday_brief")
    if sb.get("phase") == "sent":
        row = db.fetchone("SELECT LEFT(config_value, 160) AS head, updated_at FROM brand_config "
                          "WHERE brand_id='AGS' AND config_key='cm_sunday_brief_last'")
        if row:
            lines.append(f"- PODKLAD NIEDZIELNY DOSTARCZONY ({row['head'][:120]}...) - pelna tresc "
                         f"w brand_config 'cm_sunday_brief_last' + plik .md na czacie; NIE mow ze "
                         f"'research nie wrocil', tylko odeslij Tomasza do dostarczonego podkladu")
    elif sb.get("phase") == "polling":
        lines.append("- PODKLAD NIEDZIELNY: research W TOKU (job zlecony, czekamy) - tak mow, nie zgaduj")
    st = _state_get("cm_pending_madd")
    if st.get("item_id"):
        row = db.fetchone("SELECT master_theme FROM content_items WHERE id=%s", (st["item_id"],))
        lines.append(f"- TRYB ➕ MEDIA AKTYWNY: czekam na zdjecie dla \"{(row or {}).get('master_theme', '?')[:80]}\" "
                     f"(przypne AUTOMATYCZNIE do ~30 s od wyslania - jesli Tomasz pyta, powiedz to, NIE zgaduj)")
    if _state_get("cm_pending_edit").get("item_id"):
        lines.append("- TRYB ✏️ EDYCJA AKTYWNY: czekam na poprawiona wersje tekstu od Tomasza")
    if _state_get("cm_pending_angle").get("item_id"):
        lines.append("- TRYB 🔄 INNY KAT AKTYWNY: czekam na wskazowki kata od Tomasza")
    la = _state_get("cm_last_attach")
    if la.get("theme"):
        lines.append(f"- OSTATNIE PRZYPIECIE ZDJECIA: \"{la['theme'][:80]}\" o {la.get('ts', '?')[11:16]}")
    return "\n".join(lines) or "(zadnych aktywnych trybow)"


def _note_attach(theme):
    _state_set("cm_last_attach", {"theme": (theme or "")[:120],
                                  "ts": datetime.datetime.now(WARSAW).isoformat()})


def media_attach_watch():
    """Straznik petli workera (v7, ➕ Media): po tapnieciu Tomasz wysyla zdjecie -> laduje w schowku
    (HITL/vision) -> tu wykrywamy SWIEZA inspiracje z file_id i przypinamy do wskazanego materialu."""
    import json as _json
    st = _state_get("cm_pending_madd")
    iid, ts = st.get("item_id"), st.get("ts")
    if not (iid and ts):
        return
    if (datetime.datetime.now(WARSAW) - datetime.datetime.fromisoformat(ts)).total_seconds() > 10 * 60:
        # v9: auto-wyjscie po 10 min ('rozne rzeczy moga sie w zyciu dziac') + powiadomienie
        _state_set("cm_pending_madd", {})
        chat = _admin_chat()
        if chat:
            _tg("sendMessage", {"chat_id": chat, "text": "⌛ Tryb dodawania mediow zamknal sie sam (10 min bez zdjecia)."})
        return
    photo = db.fetchone(
        """SELECT id, metadata FROM inspirations
           WHERE metadata->'media'->>'file_id' IS NOT NULL AND created_at > %s::timestamptz
           ORDER BY created_at DESC LIMIT 1""", (ts,))
    if not photo:
        return
    _state_set("cm_pending_madd", {})
    item = db.fetchone("SELECT master_theme, media FROM content_items WHERE id=%s", (iid,))
    if not item:
        return
    fid = photo["metadata"]["media"]["file_id"]
    if any((m or {}).get("file_id") == fid for m in (item.get("media") or [])):
        return
    desc = {"source": "telegram", "file_id": fid,
            "kind": photo["metadata"]["media"].get("kind", "photo"), "inspiration_id": photo["id"]}
    db.execute("UPDATE content_items SET media = media || %s::jsonb, updated_at=NOW() WHERE id=%s",
               (_json.dumps([desc]), iid))
    db.execute("UPDATE post_queue SET media = media || %s::jsonb WHERE content_item_id=%s AND status IN ('review','held','scheduled')",
               (_json.dumps([desc]), iid))
    _note_attach(item.get("master_theme"))
    chat = _admin_chat()
    if chat:
        _tg("sendMessage", {"chat_id": chat,
                            "text": f"🖼 Przypiete do: \"{(item.get('master_theme') or '')[:150]}\" - "
                                    f"poleci razem z publikacja."})


def resend_intake(brand_id="AGS", limit=6):
    """Przywolaj NA DOL czatu guziki decyzji dla wszystkich czekajacych draftow (komenda 'decyzje') -
    koniec szukania starych wiadomosci intake w historii."""
    rows = db.fetchall(
        """SELECT id, master_theme FROM content_items WHERE brand_id=%s AND status='draft'
           ORDER BY updated_at DESC LIMIT %s""", (brand_id, limit))
    for r in rows:
        send_intake_buttons(r["id"], r["master_theme"])
    return len(rows)


def pending_edit():
    """Czy CM czeka na poprawiona wersje tekstu od Tomasza (okno 60 min)? item_id albo None."""
    st = _state_get("cm_pending_edit")
    iid, ts = st.get("item_id"), st.get("ts")
    if not (iid and ts):
        return None
    age = datetime.datetime.now(WARSAW) - datetime.datetime.fromisoformat(ts)
    return iid if age.total_seconds() < 60 * 60 else None


def apply_edit(new_text, wake_event=None):
    """Poprawiona wersja od Tomasza: podmien tekst-matke, ZALOGUJ pare przed/po (VOICE_EDIT -
    korpus nauki stylu), skasuj stare warianty i przegeneruj z JEGO wersji -> needs_approval.
    Guard #60 (10/07): polecenie nie moze zostac wziete za tresc; 'TRESC:' wymusza doslownosc."""
    from psycopg.types.json import Jsonb as _Jsonb
    iid = pending_edit()
    if not iid:
        return None
    from . import compliance as _cmp
    if (new_text or "").upper().startswith(("TRESC:", "TREŚĆ:")):
        new_text = new_text.split(":", 1)[1].strip()
    elif _cmp.looks_like_instruction(new_text):
        return ("To brzmi jak POLECENIE, nie gotowa tresc - NIE podmieniam (lekcja #60). Jesli to MA byc "
                "doslowna tresc, wyslij ja jeszcze raz zaczynajac od 'TRESC:'. Jesli to polecenie - "
                "napisz 'anuluj' i wydaj je normalnie.")
    _state_set("cm_pending_edit", {})
    item = db.fetchone("SELECT * FROM content_items WHERE id=%s", (iid,))
    if not item:
        return "Nie znajduje juz tego materialu."
    from . import compliance, generate, channels, hitl
    from .brand import load_brand
    brand = load_brand(item["brand_id"])
    old = (item.get("canonical_body") or "").strip()
    new = compliance.fix_dashes(new_text.strip())
    log_learning(f"cm:{item.get('brand_id', 'AGS')}", item.get("brand_id", "AGS"), iid,
                 old, new, "edited", notes="edycja tekstu-matki (VOICE_EDIT)")  # #87 petla nauki
    rules = _distill_style_rules(brand, old, new, iid)
    try:
        db.execute(
            "INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES ('cm','VOICE_EDIT',%s,%s)",
            (f"Reczna korekta Tomasza: {item['master_theme'][:80]}",
             _Jsonb({"content_item_id": str(iid), "before": old[:4000], "after": new[:4000],
                     "rules": rules})))
    except Exception:
        traceback.print_exc()  # AP-306: zapis edycji Tomasza
    db.execute("UPDATE content_items SET canonical_body=%s, updated_at=NOW() WHERE id=%s", (new, iid))
    db.execute("DELETE FROM post_queue WHERE content_item_id=%s AND status='review'", (iid,))
    item["canonical_body"] = new
    for ch in channels.active_targets(item["brand_id"], item.get("target_channels")):
        vtext, _ = generate.generate_variant(brand, new, ch["channel"], content_item_id=iid)
        vtext = compliance.enforce(brand, vtext, content_item_id=iid, channel=ch["channel"])
        channels.stage_variant(item, ch, vtext)
    # EDYCJA = AKCEPTACJA (Tomasz 06/07): poprawiony material NIE wraca do przegladu
    db.set_item_status(iid, "approved")
    if wake_event:
        wake_event.set()
    dt = item.get("scheduled_for")
    when = dt.astimezone(WARSAW).strftime("%a %d/%m %H:%M") if dt else "najblizszy wolny slot (CM przydzieli)"
    extra = ("\n📚 Wyuczone z tej korekty: " + "; ".join(rules)) if rules else ""
    return (f"✏️ Przyjete i ZATWIERDZONE (Twoja edycja = akceptacja). Warianty kanalow "
            f"przegenerowane z Twojej wersji, publikacja: {when}.{extra}")


def _distill_style_rules(brand, old, new, item_id):
    """Nauka poziom 2 (06/07): z pary przed/po destyluj 1-3 regulki stylu i doloz do
    brand_config 'style_learned' (ostatnie 30) - kazda generacja dostaje je w prompcie."""
    if not old or not new or old == new:
        return []
    try:
        from .generate import client
        from . import tasks
        model, tier, source = tasks.model_for("compliance")
        resp = client().messages.create(
            model=model, max_tokens=250, thinking={"type": "disabled"},
            messages=[{"role": "user", "content":
                       "Porownaj wersje PRZED (agenta) i PO (reczna korekta wlasciciela). Wypisz 1-3 "
                       "KROTKIE regulki stylu, ktore wynikaja z korekty (np. 'zamiast X pisze Y', "
                       "'unika slowa Z', 'lagodzi kategoryczne tezy'). Tylko regulki przenosne na inne "
                       "teksty, po polsku, kazda w nowej linii z '- '. Zero komentarza.\n\n"
                       f"PRZED:\n{old[:2500]}\n\nPO:\n{new[:2500]}"}])
        tasks.log_task("style_distill", tier, model, source, getattr(resp, "usage", None), item_id)
        rules = [ln.lstrip("- ").strip() for ln in
                 "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").split("\n")
                 if ln.strip().startswith("-")][:3]
        if rules:
            cur = _state_get("style_learned")
            arr = (cur.get("rules") or []) if isinstance(cur, dict) else []
            arr = (arr + rules)[-30:]
            _state_set("style_learned", {"rules": arr})
        return rules
    except Exception:
        return []


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
            system=[_brand.voice_block(brand)],  # 24/07: CALY glos (rdzen + Voice Bible), nie wycinek
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
                # UI 24/07: PIERWSZE przypomnienie dnia wybudza, powtorki (co 15 min do 23:00)
                # przychodza cicho. Dwadziescia wibracji tej samej prosby uczy ignorowac bota,
                # a wtedy przestaje dzialac takze wtedy, gdy naprawde cos pilnego.
                _tg("sendMessage", {"chat_id": chat,
                                    "text": f"⏰ Sprawdz i zatwierdz: {n} materialow czeka na decyzje. "
                                            f"O {FALLBACK_AT[0]}:00 wybiore material na poniedzialek sam.",
                                    "reply_markup": kb,
                                    "disable_notification": last is not None})
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
            traceback.print_exc()  # AP-306: straznik niedzielny
        logbot.send(f"⚠️ NIEDZIELA 23:00: paczka bez przegladu ({n} materialow). Zatwierdzilem sam material "
                    f"na najblizszy slot: {pick['master_theme'][:80]}. Reszta czeka na Twoja decyzje.")
        _state_set("cm_sunday_fallback", {"date": today, "picked": str(pick["id"])})
