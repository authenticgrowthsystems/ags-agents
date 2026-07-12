"""HITL: Telegram approval gate. Sends the canonical + per-channel variants with approve/reject buttons
(callback cm:<item_id>:approve|reject). The button is handled by the cm: branch added to the existing n8n
HITL handler (U5pUZjy2yAhR1sWg), which flips content_items.status -> approved | rejected."""
import json

import httpx

from . import db, config, tasks


def _admin_chat_id():
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='admin_chat_ids' LIMIT 1")
    if r and r.get("config_value"):
        try:
            arr = json.loads(r["config_value"])
            return str(arr[0]) if arr else None
        except Exception:
            return None
    return None


def send_approval(item, variants):
    """variants = list of (channel, text). Returns True if sent.
    S3 (feedback 05/07): gdy czeka >=2 materialow, NIE wysylamy osobnej pelnej wiadomosci per material
    (anty-flood) - zamiast tego jedna zbiorcza karta 'N materialow do przegladu' (matreview.batch_note),
    a przeglad idzie kartami matnav: ze strzalkami. Znacznik 11c (approval_requested_at) zawsze ustawiany."""
    tok = config.TELEGRAM_BOT_TOKEN
    chat = _admin_chat_id()
    if not tok or not chat:
        return False
    import datetime
    from . import matreview
    pending = db.fetchone("SELECT COUNT(*) AS n FROM content_items WHERE status='needs_approval'")
    st = matreview._state_get("cm_last_single_approval")
    burst = False
    if st.get("ts"):
        try:
            age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(st["ts"])
            burst = age.total_seconds() < 600  # seria: pojedyncza wiadomosc <10 min temu -> zbijaj do karty
        except Exception:
            burst = False
    if (pending and pending["n"] >= 2) or burst:
        matreview.batch_note()
        db.execute("UPDATE content_items SET approval_requested_at=NOW() WHERE id=%s", (item["id"],))
        return True
    can_tier, _ = tasks.tier_for("canonical")
    lines = [f"CM: nowy material (marka {item['brand_id']}) - {item.get('master_theme')}",
             "", "Ponizej FINALNE teksty do publikacji (jezyk wg celu; AGS = EN):", ""]
    for ch, txt in variants:
        lines.append(f"--- {ch} ---\n{txt}\n")
    if not variants:
        # task #83 (12/07): cel bez AKTYWNEGO kanalu (np. TNM strona przed App 2) = tryb reczny -
        # pokaz tekst-matke zamiast pustego 'FINALNE teksty' (incydent: karta TNM bez tresci)
        canon = (item.get("canonical_body") or "").strip()
        lines.append("--- TRESC (cel bez aktywnego kanalu - publikacja RECZNA; pelna tresc: karty -> 📄) ---\n"
                     + (canon[:2800] if canon else "(tekst w produkcji)") + "\n")
    lines.append(f"Model tekstu-matki: {can_tier} (zmiana guzikiem 🎚 dziala od nastepnego materialu)")
    text = "\n".join(lines)[:3800]
    kb = {"inline_keyboard": [
        [{"text": "✅ Zatwierdz", "callback_data": f"cm:{item['id']}:approve"},
         {"text": "❌ Odrzuc", "callback_data": f"cm:{item['id']}:reject"}],
        [{"text": "✏️ Edytuj tekst", "callback_data": f"matnav:edit:{item['id']}"}],
        # korekta tieru = approval-learning (R4): zapis do agent_approval_gates + brand_config przez galaz cmtier: w HITL
        [{"text": "🎚 haiku", "callback_data": "cmtier:canonical:haiku"},
         {"text": "🎚 sonnet", "callback_data": "cmtier:canonical:sonnet"},
         {"text": "🎚 opus", "callback_data": "cmtier:canonical:opus"}],
    ]}
    try:
        httpx.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                   json={"chat_id": chat, "text": text, "disable_web_page_preview": True, "reply_markup": kb},
                   timeout=15)
        # Task #89 (12/07): long-form nie miesci sie w wiadomosci (uciete artykuly 12/07) -
        # kazdy dlugi wariant dodatkowo jako plik .md (pelna tresc, latwe kopiowanie)
        _longs = list(variants)
        if not variants and len((item.get("canonical_body") or "")) > 2800:
            _longs = [("reczna", item.get("canonical_body") or "")]
        for ch, txt in _longs:
            if len(txt or "") > 2800:
                from . import matreview
                matreview._tg_send_document(chat, f"material_{item['id']}_{ch}.md", txt,
                                            caption=f"📎 PELNA tresc {ch} (wiadomosc wyzej jest ucieta): "
                                                    f"{item.get('master_theme', '')[:100]}")
        # znacznik dla STANU AWARYJNEGO (kanon 11c): od tej chwili liczy sie 24h ciszy
        db.execute("UPDATE content_items SET approval_requested_at=NOW() WHERE id=%s", (item["id"],))
        matreview._state_set("cm_last_single_approval",
                             {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        return True
    except Exception:
        return False
