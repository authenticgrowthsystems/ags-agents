# -*- coding: utf-8 -*-
"""Sync worker DB -> Notion (FAZA F #71, kontrakt sekcja 6 + decyzje Managera 05/07).
Event-driven: LISTEN ags_sync (trigger DDL 014 robi NOTIFY), poll 60s = backstop.
Kolejka sync_queue: FOR UPDATE SKIP LOCKED, backoff 2/4/8/16/32s, po 5 probach failed + Telegram.
Watchdog: run_forever() restartuje petle po crashu (30s) + alert. Log: logs/sync_worker.log + stdout.
Restart cm-agenta nic nie gubi - kolejka jest durable w DB."""
import datetime
import time
import traceback

import psycopg

from .. import config, db, logbot
from . import table_registry

LOG_PATH = "/app/logs/sync_worker.log"
MAX_ATTEMPTS = 5
POLL_S = 60


def _log(msg):
    line = f"[sync {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _claim(conn):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE sync_queue SET status='processing'
               WHERE id = (SELECT id FROM sync_queue
                           WHERE status='pending' AND next_attempt_at <= NOW()
                           ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
               RETURNING *""")
        row = cur.fetchone()
    conn.commit()
    return row


def _finish(conn, qid, status, info=None):
    with conn.cursor() as cur:
        cur.execute("UPDATE sync_queue SET status=%s, last_error=%s, processed_at=NOW() WHERE id=%s",
                    (status, (info or "")[:2000] or None, qid))
    conn.commit()


def _retry(conn, qrow, err):
    attempts = qrow["attempts"] + 1
    if attempts >= MAX_ATTEMPTS:
        with conn.cursor() as cur:
            cur.execute("UPDATE sync_queue SET status='failed', attempts=%s, last_error=%s, processed_at=NOW() WHERE id=%s",
                        (attempts, err[:2000], qrow["id"]))
        conn.commit()
        logbot.send(f"⚠️ SYNC->NOTION FAILED po {attempts} probach: {qrow['table_name']} "
                    f"(queue id {qrow['id']})\n{err[:400]}")
        _log(f"FAILED id={qrow['id']} {qrow['table_name']}: {err[:200]}")
    else:
        delay = 2 ** attempts
        with conn.cursor() as cur:
            cur.execute("""UPDATE sync_queue SET status='pending', attempts=%s, last_error=%s,
                           next_attempt_at=NOW() + make_interval(secs => %s) WHERE id=%s""",
                        (attempts, err[:2000], delay, qrow["id"]))
        conn.commit()
        _log(f"retry {attempts}/{MAX_ATTEMPTS} za {delay}s id={qrow['id']}: {err[:200]}")


def _drain(conn):
    """Przetwarza kolejke do pusta. Zwraca liczbe obsluzonych wpisow."""
    n = 0
    while True:
        qrow = _claim(conn)
        if not qrow:
            return n
        n += 1
        try:
            status, info = table_registry.dispatch(qrow)
            _finish(conn, qrow["id"], status, info)
            _log(f"{status} id={qrow['id']} {qrow['table_name']}: {info}")
        except Exception as e:
            _retry(conn, qrow, f"{type(e).__name__}: {e}")


def _loop():
    conn = psycopg.connect(config.POSTGRES_DSN, autocommit=False,
                           row_factory=psycopg.rows.dict_row)
    listen = psycopg.connect(config.POSTGRES_DSN, autocommit=True)
    listen.execute("LISTEN ags_sync")
    _log("worker LIVE (LISTEN ags_sync, backstop poll %ss)" % POLL_S)
    _drain(conn)  # cokolwiek czekalo przez restart
    while True:
        try:
            gen = listen.notifies(timeout=POLL_S)
            for _ in gen:
                break  # jedno obudzenie starcza - drain zbiera wszystko
        except Exception:
            pass
        _drain(conn)


def run_forever():
    """Watchdog (nota Managera): crash petli -> alert + restart po 30s."""
    while True:
        try:
            _loop()
        except Exception as e:
            _log(f"CRASH petli: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            logbot.send(f"⚠️ SYNC WORKER crash: {type(e).__name__}: {str(e)[:300]} - restart za 30s")
            time.sleep(30)
