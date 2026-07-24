"""Researcher integration: commission research via its /request webhook (event-driven, the contract built
28/06), and ingest the RESPONSE from agent_messages. CM is capped to <=medium by the critical-restriction."""
import traceback
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
            traceback.print_exc()  # AP-306: ingest wynikow researchu - cisza gubi gotowy, zaplacony wynik
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


# --- source-linked grounding (BE-SWIAT 19/07: niedzielny podklad wymaga LINKOWANYCH zrodel) ---
def job_status(job_id):
    """Status joba Researchera z research_jobs (do pollingu podkladu; None gdy brak)."""
    if not job_id:
        return None
    r = db.fetchone("SELECT status FROM research_jobs WHERE job_id=%s", (job_id,))
    return (r or {}).get("status")


def _clean_url(u):
    """Artefakt normalizacji Researchera: czesc evidence trafila z prefiksem 'https://arxiv.org/abs/web:'
    doklejonym przed prawdziwym URL-em. Odetnij go; prawdziwe arxiv (arxiv.org/abs/<id>) zostaw."""
    import re
    if not u:
        return u
    return re.sub(r'^https?://arxiv\.org/abs/web:(https?://)', r'\1', u.strip())


def claims_with_sources(job_id, limit=10, per_claim_urls=3):
    """REGULA PRAWDY: fakt = claim + jego zrodla (URL-e). Zwraca liste
    {claim, urls} dla ukonczonego joba. supporting_evidence to text[] (nie uuid[] jak w
    spec 23/06 - zweryfikowane na zywej bazie 19/07), stad join po evidence_id::text."""
    if not job_id:
        return []
    rows = db.fetchall(
        """SELECT c.claim_text,
                  (SELECT array_agg(DISTINCT e.source_url)
                   FROM evidence_items e
                   WHERE e.evidence_id::text = ANY(c.supporting_evidence)
                     AND e.source_url IS NOT NULL AND e.source_url <> '') AS urls
           FROM claims c
           WHERE c.job_id=%s
           ORDER BY c.confidence DESC NULLS LAST
           LIMIT %s""",
        (job_id, limit))
    out = []
    for r in rows:
        urls = [_clean_url(u) for u in (r.get("urls") or []) if u][:per_claim_urls]
        out.append({"claim": r["claim_text"], "urls": urls})
    return out


def grounding_with_sources(job_id, limit=10):
    """Blok tekstowy do syntezy: kazdy claim z linkami zrodel (zeby model MOGL zacytowac zrodlo)."""
    parts = []
    for c in claims_with_sources(job_id, limit=limit):
        src = ("  [zrodla: " + " | ".join(c["urls"]) + "]") if c["urls"] else "  [zrodlo: brak URL]"
        parts.append(f"- {c['claim']}\n{src}")
    return "\n".join(parts)
