"""Postgres access for CM: connection pool + content_item claiming. Mirrors the Researcher db layer."""
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import config

pool = ConnectionPool(config.POSTGRES_DSN, min_size=1, max_size=4, open=True,
                      kwargs={"row_factory": dict_row})


def fetchone(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def fetchall(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def execute(sql, params=None):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())


def get_secret(key):
    row = fetchone("SELECT value FROM app_secrets WHERE key=%s", (key,))
    return row["value"] if row else None


def claim_content_item():
    """Atomically claim the oldest content_item the loop can advance (SKIP LOCKED). The state machine itself
    moves the row to its next status, so a claimed item is not re-picked. Returns dict or None."""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT * FROM content_items
               WHERE status = ANY(%s)
               ORDER BY created_at
               FOR UPDATE SKIP LOCKED
               LIMIT 1""",
            (list(config.ACTIONABLE_STATUSES),),
        )
        return cur.fetchone()


def set_item_status(item_id, status, **fields):
    cols = ["status=%s", "updated_at=NOW()"]
    vals = [status]
    for k, v in fields.items():
        cols.append(f"{k}=%s")
        vals.append(Jsonb(v) if isinstance(v, (dict, list)) else v)
    vals.append(item_id)
    execute(f"UPDATE content_items SET {', '.join(cols)} WHERE id=%s", vals)
