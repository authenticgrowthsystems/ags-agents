"""Log channel: publish confirmations + operational notes go to the SEPARATE alert bot #2 (decision D1).
Telegram rate limits (1 msg/s per chat) mean logs must never share the conversation chat's budget."""
import json

import httpx

from . import db, config


def _admin_chat_id():
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='admin_chat_ids' LIMIT 1")
    if r and r.get("config_value"):
        try:
            arr = json.loads(r["config_value"])
            return str(arr[0]) if arr else None
        except Exception:
            return None
    return None


def send(text, silent=True):
    """Fire-and-forget log line to bot #2. Returns True if sent.

    silent=True DOMYSLNIE (UI 24/07, decyzja Tomasza o jednym bocie + wyrazniejszym interfejsie):
    to jest strumien LOGU - raporty dzienne, meldunki publikacji, kontrola driftu o 03:00.
    Ma byc do przeczytania, nie do wybudzania; rzeczy pilne ida glownym botem. Wywolaj
    z silent=False, gdy wpis logu ma zawibrowac (awaria wymagajaca reakcji teraz)."""
    tok = config.LOG_BOT_TOKEN
    chat = _admin_chat_id()
    if not tok or not chat:
        return False
    try:
        httpx.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                   json={"chat_id": chat, "text": text[:4096], "disable_web_page_preview": True,
                         "disable_notification": bool(silent)},
                   timeout=15)
        return True
    except Exception:
        return False
