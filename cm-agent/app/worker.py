"""CM worker: FastAPI (/health /metrics /request /plan) + a state-machine loop over content_items.
Event-driven: /request and /plan wake the loop; a 30s poll is the backstop. Mirrors the Researcher worker."""
import datetime
import threading
import traceback

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from . import config, db
from .brand import load_brand
from . import generate, compliance, channels, research, hitl

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


# ---------------- state machine ----------------
def _draft(item):
    brand = load_brand(item["brand_id"])
    ctx = research.research_context(item.get("research_job_id"))
    canonical, _ = generate.generate_canonical(brand, item["master_theme"], ctx)
    canonical = compliance.enforce(brand, canonical)
    variants = []
    for ch in channels.active_targets(item["brand_id"], item.get("target_channels")):
        vtext, _ = generate.generate_variant(brand, canonical, ch["channel"])
        vtext = compliance.enforce(brand, vtext)
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
        return f"published({n})"
    return "noop"


# ---------------- loop ----------------
def loop():
    print("[cm] worker loop started", flush=True)
    while True:
        worked = False
        try:
            research.ingest_research_responses()  # researching -> drafting on Researcher callback
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
                      ("TELEGRAM_BOT_TOKEN", "telegram_bot_token")):
        try:
            v = db.get_secret(key)
            if v:
                setattr(config, attr, v)
        except Exception:
            traceback.print_exc()
    print("[cm] secrets loaded from app_secrets", flush=True)


def main():
    _load_secrets()
    threading.Thread(target=loop, daemon=True).start()
    uvicorn.run(api, host="0.0.0.0", port=config.HTTP_PORT, log_level="info")


if __name__ == "__main__":
    main()
