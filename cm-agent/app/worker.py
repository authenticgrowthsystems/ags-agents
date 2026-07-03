"""CM worker: FastAPI (/health /metrics /request /plan /message) + a state-machine loop over content_items.
Event-driven: /request, /plan and /message wake the loop; a 30s poll is the backstop. Mirrors the Researcher
worker. /message = the CM Brain conversation entry (n8n HITL forwards Telegram text here)."""
import datetime
import threading
import traceback

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from . import config, db
from .brand import load_brand
from . import generate, compliance, channels, research, hitl, conversation, logbot, content_memory

api = FastAPI(title="AGS Content Manager")
wake = threading.Event()


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------- FastAPI ----------------
@api.get("/health")
def health():
    try:
        db.fetchone("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@api.get("/metrics")
def metrics():
    return db.fetchone(
        """SELECT
             (SELECT COUNT(*) FROM content_items WHERE status='published' AND updated_at > NOW()-interval '24 hours') AS published_24h,
             (SELECT COUNT(*) FROM content_items WHERE status='needs_approval') AS awaiting_approval,
             (SELECT COUNT(*) FROM content_items WHERE status = ANY(%s)) AS active""",
        (list(config.ACTIONABLE_STATUSES),),
    ) or {}


def _guard(secret):
    if not config.RESEARCHER_WEBHOOK_SECRET or secret != config.RESEARCHER_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")


@api.post("/request", status_code=202)
def request_content(body: dict, x_researcher_secret: str = Header(default="")):
    """Create a content_item (from Manager / idea-bot / any caller) and wake the loop. Same async contract +
    guard as the Researcher. Returns 202 {content_item_id}; the result flows via HITL + dispatch."""
    _guard(x_researcher_secret)
    brand_id = str(body.get("brand_id") or "AGS").strip()
    theme = str(body.get("master_theme") or body.get("theme") or "").strip()
    if not theme:
        raise HTTPException(status_code=400, detail="master_theme required")
    targets = body.get("target_channels") or ["x"]
    status = "needs_research" if body.get("needs_research") else "planned"
    row = db.fetchone(
        """INSERT INTO content_items (brand_id, master_theme, taxonomy, target_channels, status, inspiration_id)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
        (brand_id, theme, body.get("taxonomy"), list(targets), status, body.get("inspiration_id")),
    )
    wake.set()
    return {"accepted": True, "content_item_id": str(row["id"])}


@api.post("/plan", status_code=202)
def plan(body: dict, x_researcher_secret: str = Header(default="")):
    """Cron entrypoint (n8n) for proactive planning. MVP: wake the loop to advance due items."""
    _guard(x_researcher_secret)
    wake.set()
    return {"accepted": True}


@api.post("/message", status_code=202)
def message(body: dict, x_researcher_secret: str = Header(default="")):
    """Conversation entry: n8n HITL forwards a Telegram text {chat_id, text, update_id}. Returns 202
    immediately; a background thread runs the ConversationRouter and replies via sendMessage directly."""
    _guard(x_researcher_secret)
    if not body.get("chat_id"):
        raise HTTPException(status_code=400, detail="chat_id required")
    threading.Thread(target=conversation.handle, args=(body,), daemon=True).start()
    return {"accepted": True}


# ---------------- state machine ----------------
def _draft(item):
    brand = load_brand(item["brand_id"])
    ctx = research.research_context(item.get("research_job_id"))
    canonical, _ = generate.generate_canonical(brand, item["master_theme"], ctx, content_item_id=item["id"])
    canonical = compliance.enforce(brand, canonical, content_item_id=item["id"])
    variants = []
    for ch in channels.active_targets(item["brand_id"], item.get("target_channels")):
        vtext, _ = generate.generate_variant(brand, canonical, ch["channel"], content_item_id=item["id"])
        vtext = compliance.enforce(brand, vtext, content_item_id=item["id"])
        channels.stage_variant(item, ch, vtext)
        variants.append((ch["channel"], vtext))
    db.set_item_status(item["id"], "needs_approval", canonical_body=canonical, voice_hash=brand["voice_hash"])
    hitl.send_approval(item, variants)
    return f"needs_approval({len(variants)} variants)"


def process_item(item):
    st = item["status"]
    if st == "needs_research":
        code, resp = research.request_research(item, item["master_theme"])
        job_id = (resp or {}).get("job_id")
        if code == 202 and job_id:
            db.set_item_status(item["id"], "researching", research_job_id=job_id)
            return "researching"
        return _draft(item)  # research could not be enqueued -> draft without it
    if st in ("planned", "drafting"):
        return _draft(item)
    if st in ("approved", "dispatching"):
        db.set_item_status(item["id"], "dispatching")
        n = channels.dispatch_item(item)
        db.set_item_status(item["id"], "published")
        logbot.send(f"✅ CM opublikowal: {item['master_theme']} ({n} kanalow)")
        return f"published({n})"
    return "noop"


def _welcome_new_channels():
    """Hook R5 (open/closed): swiezo aktywowany kanal (bez znacznika welcomed) dostaje od CM propozycje
    adaptacji najlepszych publikacji z archiwum. Znacznik w channels.config zapobiega powtorkom."""
    rows = db.fetchall(
        "SELECT brand_id, channel FROM channels WHERE status IN ('active','draft') AND supervised = true AND NOT (config ? 'welcomed')")
    for r in rows:
        try:
            note = content_memory.adaptation_candidates_note(r["brand_id"], r["channel"])
            if note:
                chat = hitl._admin_chat_id()
                if chat:
                    conversation._tg("sendMessage", {"chat_id": chat, "text": note[:4096],
                                                     "disable_web_page_preview": True})
        except Exception:
            traceback.print_exc()
        db.execute("UPDATE channels SET config = config || '{\"welcomed\": true}'::jsonb WHERE brand_id=%s AND channel=%s",
                   (r["brand_id"], r["channel"]))


# ---------------- loop ----------------
def loop():
    print("[cm] worker loop started", flush=True)
    while True:
        worked = False
        try:
            research.ingest_research_responses()  # researching -> drafting on Researcher callback
            _welcome_new_channels()               # R5: nowy kanal -> propozycja reuse archiwum
            item = db.claim_content_item()
            if item:
                worked = True
                result = process_item(item)
                print(f"[cm] item {item['id']} ({item['status']}) -> {result}", flush=True)
        except Exception:
            traceback.print_exc()
        if not worked:
            wake.wait(timeout=config.POLL_INTERVAL_S)
            wake.clear()


def _load_secrets():
    for attr, key in (("ANTHROPIC_API_KEY", "anthropic_api_key"),
                      ("RESEARCHER_WEBHOOK_SECRET", "researcher_webhook_secret"),
                      ("TELEGRAM_BOT_TOKEN", "telegram_bot_token"),
                      ("LOG_BOT_TOKEN", "log_bot_token")):
        try:
            v = db.get_secret(key)
            if v:
                setattr(config, attr, v)
        except Exception:
            traceback.print_exc()
    print("[cm] secrets loaded from app_secrets", flush=True)


def main():
    _load_secrets()
    conversation.wake_event = wake  # a material proposed in conversation wakes the loop immediately
    threading.Thread(target=loop, daemon=True).start()
    uvicorn.run(api, host="0.0.0.0", port=config.HTTP_PORT, log_level="info")


if __name__ == "__main__":
    main()
