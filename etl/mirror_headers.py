# -*- coding: utf-8 -*-
"""FAZA F #71 - CUTOVER: naglowek '🔒 READ-ONLY MIRROR' na gorze KAZDEJ zmigrowanej strony Notion.
Uruchamiac DOPIERO po approve cutover przez Tomasza (kontrakt sekcja 7: naglowek = ostatni krok,
rollback = usuniecie naglowka + wylaczenie workera). Idempotentne: pomija strony juz oznaczone
(ledger w brand_config klucz mirror_headers_done). --dry = tylko lista.

Uruchomienie (Mikrus):
  cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env \
    -v "$PWD/etl":/etl cm-agent:latest python /etl/mirror_headers.py --dry
"""
import argparse
import datetime
import json
import os
import time

import httpx
import psycopg
from psycopg.rows import dict_row

NOTION = "https://api.notion.com/v1"
VER = "2022-06-28"
_last = [0.0]

# tabele z kotwicami notion_page_id (import #71) - kazda unikalna strona dostaje naglowek
ANCHOR_SQL = """
  SELECT DISTINCT notion_page_id FROM (
    SELECT notion_page_id FROM agent_blueprints UNION ALL SELECT notion_page_id FROM be_contracts
    UNION ALL SELECT notion_page_id FROM content_distribution_rules UNION ALL SELECT notion_page_id FROM icp_definitions
    UNION ALL SELECT notion_page_id FROM sales_playbook UNION ALL SELECT notion_page_id FROM agent_prompts
    UNION ALL SELECT notion_page_id FROM agent_session_state UNION ALL SELECT notion_page_id FROM agent_contracts
    UNION ALL SELECT notion_page_id FROM chat_registry UNION ALL SELECT notion_page_id FROM sales_sequences
    UNION ALL SELECT notion_page_id FROM pricing_tiers UNION ALL SELECT notion_page_id FROM vendor_registry
    UNION ALL SELECT notion_page_id FROM funnel_configs UNION ALL SELECT notion_page_id FROM monthly_discovery_reports
    UNION ALL SELECT notion_page_id FROM roadmap_milestones UNION ALL SELECT notion_page_id FROM manager_decisions
    UNION ALL SELECT notion_page_id FROM manager_daily_log UNION ALL SELECT notion_page_id FROM content_items
    UNION ALL SELECT notion_page_id FROM contacts UNION ALL SELECT notion_page_id FROM agent_approval_gates
  ) t WHERE notion_page_id IS NOT NULL AND notion_page_id NOT LIKE '%#%'
"""


def req(token, method, path, body=None):
    for attempt in range(6):
        wait = max(0.0, _last[0] + 0.34 - time.time())
        if wait:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = httpx.request(method, f"{NOTION}{path}", json=body, timeout=30,
                              headers={"Authorization": f"Bearer {token}", "Notion-Version": VER})
        except httpx.HTTPError:
            time.sleep(2 ** attempt)
            continue
        if r.status_code in (429, 529):
            time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
            continue
        return r
    raise RuntimeError(f"notion {path} failed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    conn = psycopg.connect(os.environ["POSTGRES_DSN"], row_factory=dict_row)
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM app_secrets WHERE key='notion_api_key'")
        token = cur.fetchone()["value"]
        cur.execute("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='mirror_headers_done'")
        r = cur.fetchone()
        done = set(json.loads(r["config_value"])) if r else set()
        cur.execute(ANCHOR_SQL)
        pages = [x["notion_page_id"] for x in cur.fetchall()]
        # strony zmigrowane BEZ kotwicy notion_page_id w wierszach (klucze naturalne / kotwice
        # strona#wpis): raporty subagentow (12), zamkniecie miesiaca, chat registry, story bank, radar
        pages += [
            "34ac00c90b938170ac25d951c2567ed8", "34cc00c90b9381a1a28ddfd566ebf172",
            "350c00c90b93817d84ccc337f5db98d2", "351c00c90b9381d89671d6ea065177f2",
            "352c00c90b93817890a5e9d105b22ca2", "34bc00c90b9381919c7ed258ce2c3fc1",
            "34fc00c90b938196912ade6b8ea15325", "353c00c90b9381a996d8db6cf87d1ba3",
            "34fc00c90b9381df8d72cacac08fe745",  # 9x daily (CM/X/LinkedIn)
            "34ec00c90b9381f4b5e5e2a2d94c6983", "34ec00c90b9381cd9e3dd4112c685d56",
            "36bc00c90b9381e0aba1d98fea359374",  # 3x weekly
            "352c00c90b938125b41dfcc7ba839807",  # RAPORT ZAMKNIECIA Kwiecien (merge do monthly)
            "31fc00c90b9381078595cfa7451596f6",  # Chat Registry (kotwice strona#slug)
            "331c00c90b9381eeb995cc757bfc89a4",  # Story Bank (kotwice strona#sNN)
            "33cc00c90b9381119968efd19fdd92fe",  # Content Intelligence Radar (inspirations split)
        ]
        # + cele z sync_registry.page_map (brand_config nie ma kolumny notion_page_id)
        cur.execute("SELECT config FROM sync_registry")
        for row in cur.fetchall():
            pages.extend(((row["config"] or {}).get("page_map") or {}).values())
        pages = sorted(set(pages))
    todo = [p for p in pages if p not in done]
    print(f"[headers] stron z kotwica: {len(pages)}, oznaczonych: {len(done)}, do zrobienia: {len(todo)}", flush=True)
    if args.dry:
        return
    ts = datetime.datetime.now().strftime("%d/%m/%Y")
    ok, fail = 0, 0
    for p in todo:
        body = {"children": [{"object": "block", "type": "callout", "callout": {
            "icon": {"type": "emoji", "emoji": "\U0001F512"},
            "color": "red_background",
            "rich_text": [{"type": "text", "text": {"content":
                f"READ-ONLY MIRROR OD {ts} - zrodlem prawdy jest PostgreSQL (ags_crd). "
                f"Zmiany wprowadzone tutaj NIE wracaja do systemu i zostana nadpisane."}}]}}],
            "position": {"type": "start"}}
        r = req(token, "PATCH", f"/blocks/{p}/children", body)
        if r.status_code == 200:
            ok += 1
            done.add(p)
        else:
            fail += 1
            print(f"  FAIL {p}: {r.status_code} {r.text[:120]}", flush=True)
        if ok % 25 == 0 and ok:
            _save(conn, done)
            print(f"  ...{ok}/{len(todo)}", flush=True)
    _save(conn, done)
    print(f"[headers] DONE ok={ok} fail={fail}", flush=True)


def _save(conn, done):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
               VALUES ('AGS','mirror_headers_done',%s,1,'faza-f',NOW())
               ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
                 version=brand_config.version+1, updated_at=NOW()""",
            (json.dumps(sorted(done)),))
    conn.commit()


if __name__ == "__main__":
    main()
