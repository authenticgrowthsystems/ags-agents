"""CacheLayer: 2-tier cache.
Exact (SHA-256) is always on. Semantic (pgvector cosine) stays off until db/002_vector_addon.sql
is applied and SEMANTIC_CACHE_ENABLED=true."""
import hashlib

from . import config, db


def _vec_literal(embedding) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"


class CacheLayer:
    @staticmethod
    def hash_query(query_text: str) -> str:
        norm = " ".join((query_text or "").lower().split())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def get_exact(self, query_text: str, content_class: str = "default", model_tier: str = None):
        # cache is keyed on (query, model_tier): a different tier must NOT return another tier's result
        tier = model_tier or config.DEFAULT_MODEL_TIER
        ttl_days = config.EXACT_TTL_DAYS.get(content_class, config.EXACT_TTL_DAYS["default"])
        row = db.fetchone(
            """SELECT job_id FROM research_jobs
               WHERE query_hash=%s AND status='completed' AND model_tier=%s
                 AND completed_at > NOW() - make_interval(secs => %s)
               ORDER BY completed_at DESC LIMIT 1""",
            (self.hash_query(query_text), tier, ttl_days * 86400.0),
        )
        return self._load(row["job_id"]) if row else None

    def get_semantic(self, embedding, model_tier: str = None):
        if not config.SEMANTIC_CACHE_ENABLED or not embedding:
            return None
        tier = model_tier or config.DEFAULT_MODEL_TIER
        lit = _vec_literal(embedding)
        row = db.fetchone(
            """SELECT job_id, 1 - (query_embedding <=> %s::vector) AS sim
               FROM research_jobs
               WHERE status='completed' AND model_tier=%s AND query_embedding IS NOT NULL
                 AND completed_at > NOW() - make_interval(days => %s)
               ORDER BY query_embedding <=> %s::vector ASC LIMIT 1""",
            (lit, tier, config.SEMANTIC_TTL_DAYS, lit),
        )
        if row and row.get("sim") is not None and float(row["sim"]) >= config.SEMANTIC_THRESHOLD:
            return self._load(row["job_id"])
        return None

    @staticmethod
    def _load(job_id):
        opts = db.fetchall(
            """SELECT option_label, description, pros, cons, supporting_claims, rank_order
               FROM options WHERE job_id=%s ORDER BY rank_order""",
            (job_id,),
        )
        if not opts:
            return None
        # FIX 24/07: cache oddawal SAME OPCJE, bez faktow. Konsumenci (Sprzedawca /prospect,
        # podklad CM) czytaja CLAIMS z linkami zrodel, wiec job z cache wygladal na gotowy,
        # a karta prospekta mowila "job bez claims". Dowod: job 4c391774 (StandART, 24/07 09:01).
        claims = db.fetchall(
            """SELECT claim_text, supporting_evidence, confidence, conflict_flag
               FROM claims WHERE job_id=%s ORDER BY confidence DESC NULLS LAST""",
            (job_id,),
        )
        src = db.fetchone("SELECT confidence_score FROM research_jobs WHERE job_id=%s", (job_id,))
        # confidence_score to NUMERIC -> Decimal w Pythonie, a Decimal NIE serializuje sie do JSON.
        # Trafialo do payloadu meldunku i wywracalo INSERT do agent_messages (cicho, bo wyjatek
        # byl polykany) - job konczyl sie 'completed', a nikt sie o tym nie dowiadywal.
        # Dowod: joby 91d8b597 i b55a9f58 z 24/07 (0 s, 11 claims, ZERO meldunkow).
        _conf = (src or {}).get("confidence_score")
        return {
            "job_id": str(job_id),
            "cached": True,
            "options": opts,
            # ksztalt zgodny z _persist_claims w workerze (klucz 'text', nie 'claim_text')
            "claims": [
                {
                    "text": c.get("claim_text"),
                    "supporting_evidence": c.get("supporting_evidence") or [],
                    "confidence": c.get("confidence"),
                    "conflict_flag": bool(c.get("conflict_flag")),
                }
                for c in claims
            ],
            "confidence": float(_conf) if _conf is not None else None,
        }
