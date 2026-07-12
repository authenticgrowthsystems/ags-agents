"""Task #84 (12/07/2026): puller Notion -> brand_tokens (Opcja C, SSOT w Notion).

Notion baza "Brand Config": Token_Name (Title) / Token_Type (Select: color/font/spacing/motyw/
zakaz) / <BRAND>_Value (Rich text; kolumn moze byc wiele: AGS_Value, TNM_Value, RDC_Value...).
Puller sklada per marka JSON {token_name: {type, value}} i upsertuje brand_tokens.

Decyzja BE (odstepstwo od n8n-triggera z briefu, rationale w raporcie #84): dziala w istniejacym
sync workerze cm-agent (klucz notion_api_key JUZ w app_secrets), poll co 10 min - tokeny marki
zmieniaja sie rzadko, trigger 'Watch' w n8n i tak polluje. Zero nowych credentiali.

Konfiguracja (bez deployu): /set brand_tokens_notion_db <database_id> po utworzeniu bazy w Notion
+ Connection integracji na bazie (AP-305!). Brak klucza konfiguracyjnego = puller spi.
"""
import json
import time
import traceback

import httpx

from .. import db

INTERVAL_S = 600
_NOTION_VER = "2022-06-28"
_last = [0.0]


def _cfg(key):
    r = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key=%s ORDER BY version DESC LIMIT 1",
        (key,))
    return ((r or {}).get("config_value") or "").strip()


def _notion_key():
    r = db.fetchone("SELECT value FROM app_secrets WHERE key='notion_api_key'")
    return ((r or {}).get("value") or "").strip()


def _plain(prop):
    """Tekst z property Notion (title/rich_text) albo nazwa selecta."""
    if not prop:
        return ""
    t = prop.get("type")
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in (prop.get(t) or [])).strip()
    if t == "select":
        return ((prop.get("select") or {}).get("name") or "").strip()
    return ""


def pull_once():
    """Jednorazowy pelny odczyt bazy Notion -> upsert brand_tokens. Zwraca dict {brand: n_tokenow}."""
    db_id = _cfg("brand_tokens_notion_db")
    if not db_id:
        return None  # baza jeszcze nie skonfigurowana - puller spi
    key = _notion_key()
    if not key:
        raise RuntimeError("brak notion_api_key w app_secrets")
    H = {"Authorization": f"Bearer {key}", "Notion-Version": _NOTION_VER, "Content-Type": "application/json"}
    per_brand = {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = httpx.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=H,
                       json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        for page in data.get("results", []):
            props = page.get("properties") or {}
            name = ""
            ttype = ""
            values = {}
            for pname, prop in props.items():
                if prop.get("type") == "title":
                    name = _plain(prop)
                elif pname == "Token_Type":
                    ttype = _plain(prop)
                elif pname.endswith("_Value"):
                    v = _plain(prop)
                    if v:
                        values[pname[:-6].upper()] = v  # AGS_Value -> AGS
            if not name:
                continue
            for brand, val in values.items():
                per_brand.setdefault(brand, {})[name] = {"type": ttype or "other", "value": val}
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    for brand, tokens in per_brand.items():
        if not db.fetchone("SELECT 1 AS x FROM brands WHERE brand_id=%s", (brand,)):
            print(f"[brand_tokens] pomijam kolumne {brand}_Value - brak marki w brands", flush=True)
            continue
        db.execute(
            """INSERT INTO brand_tokens (brand_id, tokens, updated_at, source)
               VALUES (%s, %s::jsonb, NOW(), 'notion_sync')
               ON CONFLICT (brand_id) DO UPDATE
                 SET tokens = EXCLUDED.tokens, updated_at = NOW(), source = 'notion_sync'""",
            (brand, json.dumps(tokens, ensure_ascii=False)))
    return {b: len(t) for b, t in per_brand.items()}


def tick():
    """Petla workera: poll co INTERVAL_S; brak konfiguracji = cisza, blad = log bez wywracania petli."""
    if time.time() - _last[0] < INTERVAL_S:
        return
    _last[0] = time.time()
    try:
        res = pull_once()
        if res:
            print(f"[brand_tokens] sync z Notion: {res}", flush=True)
    except Exception:
        traceback.print_exc()
