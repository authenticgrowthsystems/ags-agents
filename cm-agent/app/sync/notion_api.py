# -*- coding: utf-8 -*-
"""Klient Notion API dla sync workera (FAZA F #71). Docs-first (05/07):
rate limit avg 3 req/s + 429/529 Retry-After; append children max 100 blokow/call,
position {"type":"start"} = wstawka na gore strony; PATCH bloku podmienia cale rich_text
(max 2000 zn./element); DELETE /v1/blocks = JEDEN blok per call (brak bulk) -> soft-clear
z trackingiem block_ids zamiast masowych delete."""
import time

import httpx

from .. import db

NOTION = "https://api.notion.com/v1"
VER = "2022-06-28"
_last_req = [0.0]
_token = [None]


def token():
    if not _token[0]:
        _token[0] = db.get_secret("notion_api_key")
    return _token[0]


def req(method, path, body=None):
    """Throttle ~3 req/s + retry na 429/529 (Retry-After) + retry sieciowy. Raises po 6 probach."""
    for attempt in range(6):
        wait = max(0.0, _last_req[0] + 0.34 - time.time())
        if wait:
            time.sleep(wait)
        _last_req[0] = time.time()
        try:
            r = httpx.request(method, f"{NOTION}{path}", json=body, timeout=30,
                              headers={"Authorization": f"Bearer {token()}", "Notion-Version": VER})
        except httpx.HTTPError:
            time.sleep(2 ** attempt)
            continue
        if r.status_code in (429, 529):
            time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"notion {method} {path}: failed after retries")


def append_children(parent_id, blocks, position=None):
    """Dopisuje bloki (chunk po 100). position: None=koniec, 'start'=gora strony.
    Zwraca liste id utworzonych blokow (tracking pod soft-clear)."""
    ids = []
    for i in range(0, len(blocks), 100):
        body = {"children": blocks[i:i + 100]}
        if position == "start" and i == 0:
            body["position"] = {"type": "start"}
        elif ids:
            body["position"] = {"type": "after_block", "after_block": {"id": ids[-1]}}
        elif position == "start":
            body["position"] = {"type": "start"}
        data = req("PATCH", f"/blocks/{parent_id}/children", body)
        ids.extend(b["id"] for b in data.get("results", []))
    return ids


def archive_block(block_id):
    try:
        req("DELETE", f"/blocks/{block_id}")
        return True
    except Exception:
        return False  # blok mogl zostac usuniety recznie - nie blokuj syncu


def get_block_text(block_id):
    """Tekst jednego bloku (drift check mirrora)."""
    b = req("GET", f"/blocks/{block_id}")
    v = b.get(b.get("type")) or {}
    return "".join(t.get("plain_text", "") for t in (v.get("rich_text") or []))
