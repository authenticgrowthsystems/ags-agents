"""Postgres access: connection pool + atomic job claiming (FOR UPDATE SKIP LOCKED)."""
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import config

pool = ConnectionPool(
    config.POSTGRES_DSN,
    min_size=1,
    max_size=4,
    open=True,
    kwargs={"row_factory": dict_row},
)


def claim_job():
    """Atomically claim one enqueued job (worker-safe via SKIP LOCKED). Returns dict or None."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE research_jobs SET status='routing', started_at=NOW()
            WHERE job_id = (
                SELECT job_id FROM research_jobs
                WHERE status='enqueued'
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING *
            """
        )
        return cur.fetchone()


def fetchall(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def fetchone(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())


def set_status(job_id, status, **fields):
    """Update a research_jobs row's status plus optional columns."""
    cols = ["status=%s"]
    vals = [status]
    for k, v in fields.items():
        cols.append(f"{k}=%s")
        vals.append(Jsonb(v) if isinstance(v, (dict, list)) else v)
    vals.append(job_id)
    execute(f"UPDATE research_jobs SET {', '.join(cols)} WHERE job_id=%s", vals)
