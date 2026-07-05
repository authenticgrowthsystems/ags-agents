# -*- coding: utf-8 -*-
"""TASK #71: silnik ETL Notion -> PostgreSQL SSOT dla zrodel PELNOTEKSTOWYCH (Fazy B-E).
Male/strukturalne zrodla ida statycznymi plikami etl/notion/*.sql; ten skrypt czyta Notion API
bezposrednio na serwerze (wiernosc 1:1, zero przepisywania przez LLM).

URUCHOMIENIE (Tomasz, Mikrus; wymaga notion_api_key w app_secrets):
  cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env \
    -v "$PWD/etl":/etl cm-agent:latest python /etl/notion_etl.py --phase B

Docs-first (zweryfikowane 05/07): rate limit avg 3 req/s; 429/529 z Retry-After -> backoff;
paginacja blocks: page_size=100 + start_cursor/has_more. Payload nie dotyczy (tylko GET)."""
import argparse
import hashlib
import json
import os
import sys
import time

import httpx
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

NOTION = "https://api.notion.com/v1"
VER = "2022-06-28"
_last_req = [0.0]


def db():
    return psycopg.connect(os.environ["POSTGRES_DSN"], row_factory=dict_row)


def get_secret(conn, key):
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM app_secrets WHERE key=%s", (key,))
        r = cur.fetchone()
        return r["value"] if r else None


def _notion_req(token, method, path, params=None, body=None):
    """GET/POST z throttlem ~3 req/s + obsluga 429/529 (Retry-After) + retry sieciowy."""
    for attempt in range(6):
        wait = max(0.0, _last_req[0] + 0.34 - time.time())
        if wait:
            time.sleep(wait)
        _last_req[0] = time.time()
        try:
            r = httpx.request(method, f"{NOTION}{path}", params=params or None, json=body,
                              timeout=30,
                              headers={"Authorization": f"Bearer {token}", "Notion-Version": VER})
        except httpx.HTTPError as e:
            print(f"  [retry {attempt}] network: {e}", flush=True)
            time.sleep(2 ** attempt)
            continue
        if r.status_code in (429, 529):
            ra = float(r.headers.get("Retry-After", 2 ** attempt))
            print(f"  [rate] {r.status_code}, wait {ra}s", flush=True)
            time.sleep(ra)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"notion {method} failed after retries: {path}")


def notion_get(token, path, params=None):
    return _notion_req(token, "GET", path, params=params)


def query_db(token, database_id, limit=None):
    """POST /databases/{id}/query z paginacja. Zwraca liste stron (rows) z properties."""
    rows = []
    cursor = None
    while True:
        body = {"page_size": min(100, limit - len(rows)) if limit else 100}
        if cursor:
            body["start_cursor"] = cursor
        data = _notion_req(token, "POST", f"/databases/{database_id}/query", body=body)
        rows.extend(data.get("results", []))
        if limit and len(rows) >= limit:
            return rows[:limit]
        if not data.get("has_more"):
            return rows
        cursor = data.get("next_cursor")


def prop_val(props, name):
    """Wyciagnij wartosc property Notion (title/rich_text/select/multi_select/date/url/email/number/checkbox)."""
    p = (props or {}).get(name) or {}
    t = p.get("type")
    v = p.get(t)
    if t == "title" or t == "rich_text":
        return _rt(v)
    if t == "select":
        return (v or {}).get("name")
    if t == "multi_select":
        return [x.get("name") for x in (v or [])]
    if t == "date":
        return (v or {}).get("start")
    if t in ("url", "email", "phone_number", "number", "checkbox"):
        return v
    if t == "people":
        return [x.get("name") for x in (v or [])]
    return None


def _rt(rich):
    return "".join(t.get("plain_text", "") for t in (rich or []))


def blocks_to_text(token, block_id, depth=0):
    """Rekurencyjna konwersja blokow na markdown-ish tekst (paragraph/headings/lists/quote/code/
    table/toggle/callout/divider). Paginacja cursor+100."""
    out = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = notion_get(token, f"/blocks/{block_id}/children", params)
        for b in data.get("results", []):
            t = b.get("type")
            v = b.get(t) or {}
            txt = _rt(v.get("rich_text"))
            pad = "  " * depth
            if t == "paragraph":
                out.append(pad + txt if txt else "")
            elif t in ("heading_1", "heading_2", "heading_3"):
                out.append(pad + "#" * int(t[-1]) + " " + txt)
            elif t == "bulleted_list_item":
                out.append(pad + "- " + txt)
            elif t == "numbered_list_item":
                out.append(pad + "1. " + txt)
            elif t == "quote":
                out.append(pad + "> " + txt)
            elif t == "callout":
                out.append(pad + "[!] " + txt)
            elif t == "code":
                out.append(pad + "```\n" + txt + "\n```")
            elif t == "divider":
                out.append(pad + "---")
            elif t == "to_do":
                out.append(pad + ("[x] " if v.get("checked") else "[ ] ") + txt)
            elif t == "toggle":
                out.append(pad + "> " + txt)
            elif t == "table_row":
                out.append(pad + "| " + " | ".join(_rt(c) for c in v.get("cells", [])) + " |")
            elif t == "child_page":
                out.append(pad + f"[podstrona: {v.get('title', '')}]")
            elif txt:
                out.append(pad + txt)
            if b.get("has_children") and t not in ("child_page", "child_database"):
                out.append(blocks_to_text(token, b["id"], depth + 1))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return "\n".join(x for x in out if x is not None)


def page_title(token, page_id):
    p = notion_get(token, f"/pages/{page_id}")
    for prop in (p.get("properties") or {}).values():
        if prop.get("type") == "title":
            return _rt(prop.get("title"))
    return "(bez tytulu)"


# ---------------- handlery zapisu (idempotentne po notion_page_id) ----------------
def upsert_simple(conn, table, cols, vals, page_id):
    collist = ", ".join(cols) + ", notion_page_id"
    ph = ", ".join(["%s"] * (len(vals) + 1))
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {table} ({collist}) SELECT {ph} "
            f"WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE notion_page_id=%s)",
            (*vals, page_id, page_id))
        n = cur.rowcount
    conn.commit()
    return n


def h_sales_playbook(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    title = page_title(token, src["page_id"])
    return upsert_simple(conn, "sales_playbook",
                         ["brand_id", "section", "title", "content", "version"],
                         ["AGS", src["section"], title, text, src.get("version")], src["page_id"])


def h_brand_config_row(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
               VALUES (%s,%s,%s,1,'task-71-etl',NOW())
               ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
                 version=brand_config.version+1, updated_by=EXCLUDED.updated_by, updated_at=NOW()""",
            (src.get("brand_id", "AGS"), src["config_key"], text))
    conn.commit()
    return 1


def h_agent_prompt(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    title = page_title(token, src["page_id"])
    return upsert_simple(conn, "agent_prompts",
                         ["agent_name", "version", "title", "content", "status"],
                         [src["agent_name"], src.get("version", "1"), title, text,
                          src.get("status", "active")], src["page_id"])


def h_session_state(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO agent_session_state (agent_name, state, content, notion_page_id)
               VALUES (%s,%s,%s,%s)
               ON CONFLICT (agent_name) DO UPDATE SET content=EXCLUDED.content, updated_at=NOW()""",
            (src["agent_name"], Jsonb({}), text, src["page_id"]))
    conn.commit()
    return 1


def h_agent_contract(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    return upsert_simple(conn, "agent_contracts",
                         ["agent_name", "oversight_config", "tool_guidelines", "content"],
                         [src["agent_name"], Jsonb(src.get("oversight", {})),
                          Jsonb(src.get("tools", {})), text], src["page_id"])


def h_channels_config_key(conn, token, src):
    """Standard (np. first_comment) do channels.config wskazanych celow."""
    text = blocks_to_text(token, src["page_id"])
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE channels SET config = config || %s WHERE channel LIKE %s",
            (Jsonb({src["config_key"]: {"standard": text[:4000], "notion_page_id": src["page_id"]}}),
             src.get("channel_like", "linkedin%")))
        n = cur.rowcount
    conn.commit()
    return n


def h_manager_daily_log(conn, token, src):
    """Append-only: strona dzielona na wpisy po naglowkach/dividerach; kotwica = entry_hash(md5)."""
    text = blocks_to_text(token, src["page_id"])
    entries, cur_e = [], []
    for line in text.split("\n"):
        if line.startswith(("#", "---")) and cur_e:
            entries.append("\n".join(cur_e).strip())
            cur_e = [line] if line.startswith("#") else []
        else:
            cur_e.append(line)
    if cur_e:
        entries.append("\n".join(cur_e).strip())
    n = 0
    with conn.cursor() as cur:
        for e in entries:
            if len(e) < 20:
                continue
            h = hashlib.md5(e.encode("utf-8")).hexdigest()
            cur.execute(
                """INSERT INTO manager_daily_log (meta_type, content, notion_page_id, entry_hash)
                   VALUES (%s,%s,%s,%s) ON CONFLICT (entry_hash) DO NOTHING""",
                (src.get("meta_type", "daily_status"), e, src["page_id"], h))
            n += cur.rowcount
    conn.commit()
    return n


def h_content_item(conn, token, src):
    text = blocks_to_text(token, src["page_id"])
    title = page_title(token, src["page_id"])
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO content_items (brand_id, master_theme, canonical_body, status, meta_type, notion_page_id)
               SELECT %s,%s,%s,%s,%s,%s
               WHERE NOT EXISTS (SELECT 1 FROM content_items WHERE notion_page_id=%s)""",
            (src.get("brand_id", "AGS"), title[:500], text, src.get("status", "archived"),
             src.get("meta_type"), src["page_id"], src["page_id"]))
        n = cur.rowcount
    conn.commit()
    return n


_PRIO = {"P0 (teraz)": 0, "P1 (ten tydzień)": 1, "P2 (ten miesiąc)": 2, "P3 (później)": 3}
_TSTAT = {"⬜ Do zrobienia": "pending", "🟡 W trakcie": "in_progress", "✅ Done": "done", "🔴 Blocked": "blocked"}


def h_task_tracker(conn, token, src):
    """Task Tracker DB -> task_queue (mapping APPROVED K3: owner='manager-ags').
    Schemat zweryfikowany docs-first 05/07: Zadanie(title)/Status/Priorytet/Kategoria/Milestone/Owner/
    Deadline(date)/Notatki. Idempotencja: payload->>'notion_page_id'."""
    rows = query_db(token, src["database_id"], limit=src.get("limit"))
    n = 0
    with conn.cursor() as cur:
        for r in rows:
            props = r.get("properties") or {}
            title = prop_val(props, "Zadanie") or "(bez tytulu)"
            payload = {
                "title": title,
                "kategoria": prop_val(props, "Kategoria"),
                "milestone": prop_val(props, "Milestone"),
                "owner": prop_val(props, "Owner"),
                "notatki": prop_val(props, "Notatki"),
                "notion_status": prop_val(props, "Status"),
                "notion_page_id": r.get("id"),
            }
            cur.execute(
                """INSERT INTO task_queue (agent_id, task_type, payload, scheduled_for, priority, status)
                   SELECT 'manager-ags', 'notion_task', %s, %s, %s, %s
                   WHERE NOT EXISTS (SELECT 1 FROM task_queue WHERE payload->>'notion_page_id' = %s)""",
                (Jsonb(payload), prop_val(props, "Deadline"),
                 _PRIO.get(prop_val(props, "Priorytet"), 3),
                 _TSTAT.get(prop_val(props, "Status"), "pending"), r.get("id")))
            n += cur.rowcount
    conn.commit()
    return n


def h_inspirations_split(conn, token, src):
    """Strona z wieloma wpisami (np. Content Intelligence Radar) -> inspirations, wpis per naglowek.
    Kotwica: notion_page_id = page#md5-12 tresci wpisu."""
    text = blocks_to_text(token, src["page_id"])
    entries, cur_e = [], []
    for line in text.split("\n"):
        if line.startswith("#") and cur_e:
            entries.append("\n".join(cur_e).strip())
            cur_e = [line]
        else:
            cur_e.append(line)
    if cur_e:
        entries.append("\n".join(cur_e).strip())
    n = 0
    with conn.cursor() as cur:
        for e in entries:
            if len(e) < 40:
                continue
            h = hashlib.md5(e.encode("utf-8")).hexdigest()[:12]
            anchor = f"{src['page_id']}#{h}"
            cur.execute(
                """INSERT INTO inspirations (source, content, brand, status, notion_page_id, metadata)
                   SELECT 'notion', %s, %s, %s, %s, %s
                   WHERE NOT EXISTS (SELECT 1 FROM inspirations WHERE notion_page_id = %s)""",
                (e[:4000], src.get("brand", "AGS"), src.get("status", "new"), anchor,
                 Jsonb({"meta_type": src.get("meta_type", "note")}), anchor))
            n += cur.rowcount
    conn.commit()
    return n


HANDLERS = {"sales_playbook": h_sales_playbook, "brand_config_row": h_brand_config_row,
            "agent_prompt": h_agent_prompt, "session_state": h_session_state,
            "agent_contract": h_agent_contract, "channels_config_key": h_channels_config_key,
            "manager_daily_log": h_manager_daily_log, "content_item": h_content_item,
            "task_tracker": h_task_tracker,
            "inspirations_split": h_inspirations_split}

# ---------------- rejestr zrodel per faza (mapping APPROVED 04/07) ----------------
SOURCES = [
    # FAZA B - K1 pelnotekstowe (Sales Bible wyjety: decyzja Managera #1 = content z pliku workspace,
    # statyczny SQL phaseB_salesbible.sql; Website Canon zostaje w silniku - brak pliku workspace)
    {"phase": "B", "handler": "brand_config_row", "page_id": "320c00c90b938119bd5ff118ff95b5c8",
     "config_key": "website_canon"},
    # FAZA B - K2 agenci
    {"phase": "B", "handler": "agent_prompt", "page_id": "36fc00c90b93813a9bc8ec024a295466",
     "agent_name": "content-manager", "version": "2.0"},
    {"phase": "B", "handler": "agent_prompt", "page_id": "353c00c90b93814c86c8fbb992d5b126",
     "agent_name": "x-comment-specialist", "version": "4"},
    {"phase": "B", "handler": "agent_prompt", "page_id": "34bc00c90b9381079394c91b54216ffc",
     "agent_name": "x-comment-specialist", "version": "1.1", "status": "superseded"},
    {"phase": "B", "handler": "agent_prompt", "page_id": "342c00c90b9381739371db864b1a823a",
     "agent_name": "content-engine", "version": "1.0"},
    {"phase": "B", "handler": "agent_prompt", "page_id": "320c00c90b9381c68b31ef9adf1a9780",
     "agent_name": "website-funnels", "version": "1"},
    {"phase": "B", "handler": "agent_prompt", "page_id": "34cc00c90b9381a5a2c8d9afbd2b0883",
     "agent_name": "infographic-reframe-specialist", "version": "2.1"},
    {"phase": "B", "handler": "session_state", "page_id": "36ac00c90b9381369ea0c39f84c343e9",
     "agent_name": "linkedin-sm"},
    {"phase": "B", "handler": "agent_contract", "page_id": "357c00c90b93819e8eead0bb4d5eb285",
     "agent_name": "comment-radar", "oversight": {"type": "cm_oversight", "version": "1.0"}},
    {"phase": "B", "handler": "agent_contract", "page_id": "352c00c90b9381d58987e71f743418ef",
     "agent_name": "content-creator-image", "tools": {"tool": "higgsfield"}},
    {"phase": "B", "handler": "channels_config_key", "page_id": "34fc00c90b9381efb1d6c1f53caeff81",
     "config_key": "first_comment", "channel_like": "linkedin%"},
    {"phase": "B", "handler": "brand_config_row", "page_id": "34dc00c90b938140b4b7c4c9870065dd",
     "config_key": "footer_canon"},
    # FAZA C2 - koncowki C (audit-first: Founders List = metodologia -> sales_playbook)
    {"phase": "C2", "handler": "sales_playbook", "page_id": "353c00c90b9381569394f780eabd10ac",
     "section": "founders_list_guide", "version": "1"},
    {"phase": "C2", "handler": "inspirations_split", "page_id": "33cc00c90b9381119968efd19fdd92fe",
     "meta_type": "competitor_observation"},
    # TEST HANDLERA BAZ (rekomendacja Managera 05/07): 5 wierszy Task Trackera PRZED pelna Faza C
    {"phase": "TESTDB", "handler": "task_tracker", "database_id": "d8c99e6459c444dc894364e31b2f8fb0",
     "limit": 5},
    # FAZA C - K3 zywe (Task Tracker PELNY; idempotencja pominie 5 testowych)
    {"phase": "C", "handler": "task_tracker", "database_id": "d8c99e6459c444dc894364e31b2f8fb0"},
    # FAZA C - K3 zywe (start; reszta K3/K4/K5 dopisywana per faza)
    {"phase": "C", "handler": "manager_daily_log", "page_id": "341c00c90b938130876ef0fce279babc",
     "meta_type": "daily_status"},
    {"phase": "C", "handler": "manager_daily_log", "page_id": "381c00c90b9381d09a7dc579fbb4dfda",
     "meta_type": "stan_gry_snapshot"},
    # FAZA C - K4 content pelnotekstowy
    {"phase": "C", "handler": "content_item", "page_id": "37fc00c90b9381c5928bea483dca7841",
     "meta_type": "longform", "brand_id": "AGS"},
    {"phase": "C", "handler": "content_item", "page_id": "37fc00c90b93814e8f59d8484b8967b8",
     "meta_type": "longform", "brand_id": "TNM"},
    {"phase": "C", "handler": "content_item", "page_id": "36fc00c90b93812bb595f9172f89c840",
     "meta_type": "newsletter", "brand_id": "AGS"},
    {"phase": "C", "handler": "content_item", "page_id": "36fc00c90b93812e95d5f9d454fc70bf",
     "meta_type": "longform", "brand_id": "AGS"},
    {"phase": "C", "handler": "content_item", "page_id": "376c00c90b938145a0b2dc4f6f069257",
     "meta_type": "longform", "brand_id": "TNM"},
    {"phase": "C", "handler": "content_item", "page_id": "37fc00c90b9381c895e8c99dfa514546",
     "meta_type": "lead_magnet", "brand_id": "TNM"},
    {"phase": "C", "handler": "content_item", "page_id": "363c00c90b938142be60d6699b8bedcb",
     "meta_type": "campaign", "brand_id": "AGS"},
    {"phase": "C", "handler": "content_item", "page_id": "34bc00c90b93816a91cce2a588a5a97f",
     "meta_type": "brief_master", "brand_id": "AGS", "status": "brief"},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, help="B|C|D|E albo ALL")
    ap.add_argument("--dry", action="store_true", help="tylko fetch + liczby, zero INSERT")
    args = ap.parse_args()
    conn = db()
    token = get_secret(conn, "notion_api_key")
    if not token:
        print("BRAK notion_api_key w app_secrets - dodaj i uruchom ponownie.")
        sys.exit(1)
    todo = [s for s in SOURCES if args.phase.upper() in ("ALL", s["phase"])]
    print(f"[etl] faza {args.phase}: {len(todo)} zrodel", flush=True)
    report = []
    for src in todo:
        sid = (src.get("page_id") or src.get("database_id") or "?")[:8]
        try:
            if args.dry:
                if "database_id" in src:
                    rows = query_db(token, src["database_id"], limit=src.get("limit"))
                    report.append((src["handler"], sid, f"dry rows={len(rows)}"))
                else:
                    text = blocks_to_text(token, src["page_id"])
                    report.append((src["handler"], sid, f"dry len={len(text)}"))
            else:
                n = HANDLERS[src["handler"]](conn, token, src)
                report.append((src["handler"], sid, f"rows={n}"))
            print(f"  OK {src['handler']} {sid} {report[-1][2]}", flush=True)
        except Exception as e:
            report.append((src["handler"], sid, f"ERROR {e}"))
            print(f"  ERROR {src['handler']} {sid}: {e}", flush=True)
    print("\n[etl] RAPORT:", flush=True)
    for h, p, r in report:
        print(f"  {h:22s} {p}  {r}", flush=True)


if __name__ == "__main__":
    main()
