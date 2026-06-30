"""Researcher integration: commission research via its /request webhook (event-driven, the contract built
28/06), and ingest the RESPONSE from agent_messages. CM is capped to <=medium by the critical-restriction."""
import httpx

from . import config, db


def request_research(item, query):
    """POST the Researcher /request. correlation_id = content_item id so the RESPONSE maps back. No model_tier
    pinned -> Researcher auto-tier (medium query -> sonnet); CM cannot reach critical regardless (guard)."""
    body = {"query": query, "from": "content-manager", "correlation_id": str(item["id"])}
    try:
        r = httpx.post(config.RESEARCHER_URL + "/request", json=body,
                       headers={"X-Researcher-Secret": config.RESEARCHER_WEBHOOK_SECRET}, timeout=20)
        data = {}
        if r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
        return r.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


def ingest_research_responses():
    """Poll agent_messages for Researcher RESPONSEs to content-manager; flip the matching researching item to
    drafting. The research payload itself is read later from the Researcher tables via research_job_id."""
    rows = db.fetchall(
        """SELECT message_id, correlation_id FROM agent_messages
           WHERE to_agent_id=(SELECT agent_id FROM agent_registry WHERE agent_name='content-manager')
             AND message_type='response' AND status='unread'
           ORDER BY created_at LIMIT 10"""
    )
    flipped = []
    for r in rows:
        corr = r.get("correlation_id")
        try:
            if corr:
                item = db.fetchone("SELECT id, status FROM content_items WHERE id=%s", (corr,))
                if item and item["status"] == "researching":
                    db.execute("UPDATE content_items SET status='drafting', updated_at=NOW() WHERE id=%s", (corr,))
                    flipped.append(str(corr))
            db.execute("UPDATE agent_messages SET status='read', read_at=NOW() WHERE message_id=%s", (r["message_id"],))
        except Exception:
            pass
    return flipped


def research_context(job_id):
    """Build a compact grounding block from the Researcher's claims + options for a finished job."""
    if not job_id:
        return ""
    parts = []
    claims = db.fetchall("SELECT claim_text FROM claims WHERE job_id=%s LIMIT 12", (job_id,))
    if claims:
        parts.append("Key claims:\n" + "\n".join("- " + c["claim_text"] for c in claims))
    opts = db.fetchall("SELECT option_label, description FROM options WHERE job_id=%s ORDER BY rank_order", (job_id,))
    if opts:
        parts.append("Options:\n" + "\n".join(f"- {o['option_label']}: {o['description']}" for o in opts))
    return "\n\n".join(parts)
