"""AGS Researcher worker: poll research_jobs, run the cost cascade, synthesize exactly 4 options.
Orchestration loop lives here (Python), not in n8n. n8n owns the source adapters + ingress + callback.
Also serves /health (container healthcheck) and /metrics."""
import datetime
import threading
import time
import traceback

import httpx
import uvicorn
from fastapi import FastAPI
from psycopg.types.json import Jsonb

from . import config, db
from .budget import BudgetGovernor, BudgetExceeded
from .cache import CacheLayer, _vec_literal
from .failure import FailureHandler
from .prompts import MasterPromptBuilder
from .router import QueryRouter
from .sources import SourceClient
from .synth import Synthesizer

router = QueryRouter()
cache = CacheLayer()
budget = BudgetGovernor()
prompts = MasterPromptBuilder()
failure = FailureHandler()
sources = SourceClient()
_synth = None


def synth() -> Synthesizer:
    global _synth
    if _synth is None:
        _synth = Synthesizer()
    return _synth


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------- FastAPI ----------------
api = FastAPI(title="AGS Researcher")


@api.get("/health")
def health():
    try:
        db.fetchone("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@api.get("/metrics")
def metrics():
    row = db.fetchone(
        """SELECT
             (SELECT COUNT(*) FROM research_jobs WHERE completed_at > NOW() - interval '24 hours')                         AS jobs_24h,
             (SELECT COALESCE(SUM(cost_pln),0) FROM cost_events WHERE timestamp > NOW() - interval '24 hours')             AS cost_24h_pln,
             (SELECT COALESCE(SUM(cost_pln),0) FROM cost_events WHERE timestamp > NOW() - interval '30 days')              AS cost_30d_pln,
             (SELECT COUNT(*) FROM research_jobs WHERE status='partial_failure' AND completed_at > NOW() - interval '24 hours') AS partial_24h,
             (SELECT COUNT(*) FROM research_jobs WHERE status='enqueued')                                                  AS queue_depth"""
    )
    return row or {}


# ---------------- embeddings (only when semantic cache is on) ----------------
def embed(text: str):
    if not config.SEMANTIC_CACHE_ENABLED:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        r = client.embeddings.create(model=config.EMBED_MODEL, input=(text or "")[:8000])
        return r.data[0].embedding
    except Exception:
        return None


# ---------------- persistence helpers ----------------
def _persist_claims(job_id, claims) -> list[str]:
    ids = []
    for c in claims:
        d = c.model_dump() if hasattr(c, "model_dump") else c
        row = db.fetchone(
            """INSERT INTO claims (job_id, claim_text, supporting_evidence, confidence, conflict_flag)
               VALUES (%s,%s,%s,%s,%s) RETURNING claim_id""",
            (job_id, d.get("text"), d.get("supporting_evidence") or [], d.get("confidence"), d.get("conflict_flag", False)),
        )
        ids.append(str(row["claim_id"]))
    return ids


def _persist_options(job_id, options):
    for o in options:
        d = o.model_dump() if hasattr(o, "model_dump") else o
        db.execute(
            """INSERT INTO options (job_id, option_label, description, pros, cons, supporting_claims, rank_order)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                job_id,
                d.get("label") or d.get("option_label"),
                d.get("description"),
                d.get("pros") or [],
                d.get("cons") or [],
                d.get("supporting_claims") or [],
                d.get("rank_order"),
            ),
        )


def _escalate(message: str):
    try:
        db.execute(
            """INSERT INTO agent_messages (from_agent_id, to_agent_id, message_type, payload, status)
               VALUES ((SELECT agent_id FROM agent_registry WHERE agent_name='researcher'),
                       (SELECT agent_id FROM agent_registry WHERE agent_name='manager-ags'),
                       'escalation', %s, 'unread')""",
            (Jsonb({"message": message}),),
        )
    except Exception:
        traceback.print_exc()


def _callback(job, payload: dict):
    """Hand the finished result to the n8n Ingress & Callback workflow (writes agent_messages RESPONSE + Telegram).
    Best-effort: the result is already durable in Postgres regardless."""
    try:
        httpx.post(
            config.N8N_BASE_URL + config.ADAPTER_PATHS["callback"],
            json={"job_id": str(job["job_id"]),
                  "requesting_agent_id": str(job.get("requesting_agent_id") or ""),
                  **payload},
            timeout=20,
        )
    except Exception:
        pass


def _job_cost_pln(job_id) -> float:
    r = db.fetchone(
        """SELECT COALESCE(SUM(ce.cost_pln),0) AS s
           FROM cost_events ce JOIN research_runs r ON r.run_id = ce.run_id
           WHERE r.job_id=%s""",
        (job_id,),
    )
    return float(r["s"] or 0)


# ---------------- core pipeline ----------------
def process_job(job):
    job_id = job["job_id"]
    query = job["query_text"]
    level = router.classify(query)
    db.set_status(job_id, "routing", complexity=level)

    # 1) cache (exact always; semantic only when enabled)
    emb = embed(query)
    hit = cache.get_exact(query) or cache.get_semantic(emb)
    if hit:
        _persist_options(job_id, hit["options"])
        db.set_status(job_id, "completed", completed_at=_now(), cost_pln=0)
        _callback(job, {"cached": True, "options": hit["options"]})
        return "cache_hit"

    # 2) budget hard stops
    try:
        budget.preflight()
    except BudgetExceeded as e:
        db.set_status(job_id, "failed", error_message=str(e), completed_at=_now())
        _escalate(f"budget block: {e}")
        return "budget_blocked"

    # 3) dispatch sources per cost-cascade policy
    db.set_status(job_id, "dispatched")
    evidence_by_source, all_evidence = {}, []
    for src in router.sources(level):
        run = db.fetchone(
            "INSERT INTO research_runs (job_id, source_name, started_at, status) VALUES (%s,%s,NOW(),'running') RETURNING run_id",
            (job_id, src),
        )
        run_id = run["run_id"]
        res = sources.run(src, job_id, run_id, prompts.build(src, query, level))
        ev = res.get("evidence") or []
        for e in ev:
            row = db.fetchone(
                """INSERT INTO evidence_items (run_id, source_url, source_name, content, freshness, authority)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING evidence_id""",
                (run_id, e.get("source_url"), src, e.get("content", ""), e.get("freshness"), e.get("authority")),
            )
            item = dict(e)
            item["evidence_id"] = str(row["evidence_id"])
            item["source_name"] = src
            all_evidence.append(item)
        evidence_by_source[src] = ev
        if res.get("cost_usd") is not None:
            budget.log_cost(run_id, src, str((prompts.build(src, query, level)).get("model") or src),
                            res.get("input_tokens"), res.get("output_tokens"), res.get("cost_usd"))
        db.execute("UPDATE research_runs SET status=%s, completed_at=NOW() WHERE run_id=%s",
                   (res.get("status", "completed"), run_id))

    # 4) failure assessment
    status, cap = failure.assess(evidence_by_source)
    if status == "failed":
        db.set_status(job_id, "failed", error_message="no sources returned evidence", completed_at=_now())
        _escalate(f"research failed (no evidence) job={job_id}")
        return "failed"

    # 5) synthesis (Sonnet 4.6 -> exactly 4 options)
    db.set_status(job_id, "synthesizing")
    synth_run = db.fetchone(
        "INSERT INTO research_runs (job_id, source_name, started_at, status) VALUES (%s,'synthesis',NOW(),'running') RETURNING run_id",
        (job_id,),
    )
    out, usage = synth().synthesize(query, all_evidence, partial=(status == "partial_failure"))
    budget.log_cost(synth_run["run_id"], "synthesis", config.SYNTH_MODEL,
                    getattr(usage, "input_tokens", 0), getattr(usage, "output_tokens", 0),
                    budget.anthropic_cost_usd(usage))
    db.execute("UPDATE research_runs SET status='completed', completed_at=NOW() WHERE run_id=%s", (synth_run["run_id"],))

    # 6) persist + finalize
    _persist_claims(job_id, out.claims)
    _persist_options(job_id, out.options)
    conf = round(failure.cap_confidence(out.overall_confidence, cap), 2)
    total = _job_cost_pln(job_id)
    if config.SEMANTIC_CACHE_ENABLED and emb:
        db.execute("UPDATE research_jobs SET query_embedding=%s::vector WHERE job_id=%s", (_vec_literal(emb), job_id))
    db.set_status(job_id, status, completed_at=_now(), cost_pln=total, confidence_score=conf)

    # 7) callback (agent_messages RESPONSE + Telegram via n8n)
    _callback(job, {
        "options": [o.model_dump() for o in out.options],
        "overall_confidence": conf,
        "cost_pln": total,
        "recommendation": out.recommendation,
        "partial": status == "partial_failure",
    })
    return status


# ---------------- main loop ----------------
def loop():
    print("[researcher] worker loop started", flush=True)
    while True:
        job = None
        try:
            job = db.claim_job()
            if not job:
                time.sleep(config.POLL_INTERVAL_S)
                continue
            print(f"[researcher] job {job['job_id']} claimed", flush=True)
            result = process_job(job)
            print(f"[researcher] job {job['job_id']} -> {result}", flush=True)
        except Exception as e:
            traceback.print_exc()
            if job:
                try:
                    db.set_status(job["job_id"], "failed", error_message=str(e)[:500], completed_at=_now())
                except Exception:
                    pass
            time.sleep(config.POLL_INTERVAL_S)


def main():
    threading.Thread(target=loop, daemon=True).start()
    uvicorn.run(api, host="0.0.0.0", port=config.HTTP_PORT, log_level="info")


if __name__ == "__main__":
    main()
