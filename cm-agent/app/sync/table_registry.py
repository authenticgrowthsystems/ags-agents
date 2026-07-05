# -*- coding: utf-8 -*-
"""Rejestr renderow per tabela (decyzja Managera 05/07: hybryda re_render/append).
Nowa tabela w przyszlosci: INSERT do sync_registry (DDL 014) + ewentualny wpis KEYERS/METAS
ponizej gdy klucz/etykieta niestandardowe. Worker: dispatch(row_kolejki) -> (status, info)."""
import datetime
import hashlib
import json

from .. import db
from . import notion_api, render


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# klucz wiersza (do page_map i mirror_state) per tabela; default = id
KEYERS = {
    "brand_config": lambda p: f"{p.get('brand_id')}:{p.get('config_key')}",
    "manager_daily_log": lambda p: p.get("meta_type") or "daily_status",
}

# tresc wiersza do renderu; default = pole 'content'
CONTENT = {
    "brand_config": lambda p: p.get("config_value") or "",
    "manager_daily_log": lambda p: p.get("content") or "",
}

# etykieta wpisu append
METAS = {
    "manager_daily_log": lambda p: p.get("meta_type") or "",
}


def _registry(table):
    return db.fetchone("SELECT enabled, render_pattern, config FROM sync_registry WHERE table_name=%s",
                       (table,))


def _brand_sync_on(payload):
    brand = payload.get("brand_id") or "AGS"
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key='sync_to_notion'",
                    (brand,))
    return bool(r and str(r["config_value"]).strip().lower() == "true")


def _target_page(table, cfg, payload, row_key):
    """Cel: page_map z sync_registry.config (klucz wiersza), fallback notion_page_id wiersza."""
    page = ((cfg or {}).get("page_map") or {}).get(row_key)
    return page or payload.get("notion_page_id")


def dispatch(qrow):
    """Przetwarza jeden wpis kolejki. Zwraca (status, info): done/skipped albo rzuca (retry/backoff)."""
    table, payload = qrow["table_name"], qrow["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    reg = _registry(table)
    if not reg or not reg["enabled"]:
        return "skipped", "tabela wylaczona w sync_registry"
    if not _brand_sync_on(payload):
        return "skipped", "brand sync_to_notion != true"
    row_key = KEYERS.get(table, lambda p: str(p.get("id")))(payload)
    page = _target_page(table, reg["config"], payload, row_key)
    if not page:
        return "skipped", f"brak celu Notion dla {table}/{row_key} (page_map/notion_page_id)"
    content = CONTENT.get(table, lambda p: p.get("content") or "")(payload)
    checksum = hashlib.md5((content or "").encode("utf-8")).hexdigest()
    if reg["render_pattern"] == "re_render":
        return _re_render(table, row_key, page, content, checksum)
    return _append(table, row_key, page, payload, content, checksum)


def _re_render(table, row_key, page, content, checksum):
    """Soft-clear z trackingiem: nowa sekcja na GORE strony (widoczna <10s), potem archiwizacja
    blokow POPRZEDNIEGO renderu (id-y z sync_mirror_state). Zero masowych delete."""
    st = db.fetchone("SELECT block_ids, last_checksum FROM sync_mirror_state WHERE table_name=%s AND row_key=%s",
                     (table, row_key))
    if st and st["last_checksum"] == checksum:
        return "done", "checksum bez zmian"
    blocks = [render.mirror_callout(_now(), checksum)] + render.md_to_blocks(content)
    new_ids = notion_api.append_children(page, blocks, position="start")
    old_ids = (st and st["block_ids"]) or []
    archived = sum(1 for b in old_ids if notion_api.archive_block(b))
    db.execute(
        """INSERT INTO sync_mirror_state (table_name, row_key, notion_page_id, block_ids, last_checksum, updated_at)
           VALUES (%s,%s,%s,%s::jsonb,%s,NOW())
           ON CONFLICT (table_name, row_key) DO UPDATE SET notion_page_id=EXCLUDED.notion_page_id,
             block_ids=EXCLUDED.block_ids, last_checksum=EXCLUDED.last_checksum, updated_at=NOW()""",
        (table, row_key, page, json.dumps(new_ids), checksum))
    return "done", f"re_render {len(new_ids)} blokow (+{archived} starych zarchiwizowanych)"


def _append(table, row_key, page, payload, content, checksum):
    """Append-only: wpis dopisany na koncu strony; idempotencja po checksumie ostatniego wpisu klucza."""
    st = db.fetchone("SELECT last_checksum FROM sync_mirror_state WHERE table_name=%s AND row_key=%s",
                     (table, f"{row_key}:{checksum}"))
    if st:
        return "done", "wpis juz zsynchronizowany (checksum)"
    meta = METAS.get(table, lambda p: "")(payload)
    ids = notion_api.append_children(page, render.entry_blocks(_now(), meta, content))
    db.execute(
        """INSERT INTO sync_mirror_state (table_name, row_key, notion_page_id, block_ids, last_checksum, updated_at)
           VALUES (%s,%s,%s,%s::jsonb,%s,NOW()) ON CONFLICT (table_name, row_key) DO NOTHING""",
        (table, f"{row_key}:{checksum}", page, json.dumps(ids), checksum))
    return "done", f"append {len(ids)} blokow"
