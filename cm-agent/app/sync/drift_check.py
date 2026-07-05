# -*- coding: utf-8 -*-
"""Drift check mirrora (FAZA F #71, kontrakt sekcja 6): cron 03:00 UTC + on-demand (test akceptacyjny
'manual edit Notion -> alert'). Trzy kontrole:
(1) zdrowie kolejki: pending >15min albo failed <24h,
(2) integralnosc sekcji mirrora (re_render): callout z sync_mirror_state istnieje i niesie
    md5 ostatniego renderu - recznie edytowany/skasowany = DRIFT,
(3) DB vs stan syncu: checksum wiersza rozny od last_checksum bez wpisu w kolejce = zgubiony trigger.
Uruchomienie: docker run --rm ... cm-agent:latest python -m app.sync.drift_check
Wynik: raport na stdout + Telegram alert (bot #2) TYLKO gdy drift."""
import hashlib

from .. import db, logbot
from . import notion_api, table_registry


def main():
    problems = []

    q = db.fetchone("""SELECT
        (SELECT COUNT(*) FROM sync_queue WHERE status='pending' AND created_at < NOW()-interval '15 minutes') AS stale,
        (SELECT COUNT(*) FROM sync_queue WHERE status='failed' AND processed_at > NOW()-interval '24 hours') AS failed""")
    if q["stale"]:
        problems.append(f"kolejka: {q['stale']} wpisow pending >15min (worker spi?)")
    if q["failed"]:
        problems.append(f"kolejka: {q['failed']} failed w 24h (szczegoly: sync_queue.last_error)")

    states = db.fetchall("""SELECT m.table_name, m.row_key, m.block_ids, m.last_checksum
                            FROM sync_mirror_state m JOIN sync_registry r ON r.table_name=m.table_name
                            WHERE r.enabled AND r.render_pattern='re_render'""")
    for st in states:
        ids = st["block_ids"] or []
        if not ids:
            continue
        try:
            txt = notion_api.get_block_text(ids[0])
        except Exception as e:
            problems.append(f"mirror {st['table_name']}/{st['row_key']}: callout nieosiagalny ({e})")
            continue
        if (st["last_checksum"] or "")[:12] not in txt:
            problems.append(f"mirror {st['table_name']}/{st['row_key']}: callout zmieniony/bez md5 "
                            f"- reczna edycja w Notion (DB jest kanoniczne!)")

    rows = db.fetchall("""SELECT brand_id, config_key, config_value FROM brand_config bc
                          WHERE EXISTS (SELECT 1 FROM sync_registry WHERE table_name='brand_config' AND enabled)""")
    for r in rows:
        key = f"{r['brand_id']}:{r['config_key']}"
        st = db.fetchone("SELECT last_checksum FROM sync_mirror_state WHERE table_name='brand_config' AND row_key=%s",
                         (key,))
        if not st:
            continue  # klucz bez celu w page_map - swiadomie nie mirrorowany
        cur = hashlib.md5((r["config_value"] or "").encode("utf-8")).hexdigest()
        if cur != st["last_checksum"]:
            pend = db.fetchone("""SELECT 1 AS x FROM sync_queue WHERE table_name='brand_config'
                                  AND status IN ('pending','processing') LIMIT 1""")
            if not pend:
                problems.append(f"brand_config {key}: DB zmienione, mirror stary, kolejka pusta (zgubiony trigger?)")

    if problems:
        msg = "🔎 DRIFT CHECK - wykryto rozjazdy:\n- " + "\n- ".join(problems[:15])
        print(msg, flush=True)
        logbot.send(msg[:4000])
    else:
        print("[drift] OK - zero rozjazdow", flush=True)


if __name__ == "__main__":
    main()
