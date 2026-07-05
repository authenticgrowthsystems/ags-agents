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
    pending = db.fetchone("SELECT COUNT(*) AS n FROM content_items WHERE status='needs_approval'")
    if pending and pending["n"] >= 2:
        from . import matreview
        matreview.batch_note()
        db.execute("UPDATE content_items SET approval_requested_at=NOW() WHERE id=%s", (item["id"],))
        return True
    can_tier, _ = tasks.tier_for("canonical")
    lines = [f"CM: nowy material (marka {item['brand_id']}) - {item.get('master_theme')}", ""]
    for ch, txt in variants:
        lines.append(f"--- {ch} ---\n{txt}\n")
    lines.append(f"Model tekstu-matki: {can_tier} (zmiana guzikiem 🎚 dziala od nastepnego materialu)")
    text = "\n".join(lines)[:3800]
    kb = {"inline_keyboard": [
        [{"text": "✅ Zatwierdz", "callback_data": f"cm:{item['id']}:approve"},
         {"text": "❌ Odrzuc", "callback_data": f"cm:{item['id']}:reject"}],
        # korekta tieru = approval-learning (R4): zapis do agent_approval_gates + brand_config przez galaz cmtier: w HITL
        [{"text": "🎚 haiku", "callback_data": "cmtier:canonical:haiku"},
         {"text": "🎚 sonnet", "callback_data": "cmtier:canonical:sonnet"},
         {"text": "🎚 opus", "callback_data": "cmtier:canonical:opus"}],
    ]}
    try:
        httpx.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                   json={"chat_id": chat, "text": text, "disable_web_page_preview": True, "reply_markup": kb},
                   timeout=15)
        # znacznik dla STANU AWARYJNEGO (kanon 11c): od tej chwili liczy sie 24h ciszy
        db.execute("UPDATE content_items SET approval_requested_at=NOW() WHERE id=%s", (item["id"],))
        return True
    except Exception:
        return False
