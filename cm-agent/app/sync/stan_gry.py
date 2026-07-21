# -*- coding: utf-8 -*-
"""LACZNIK (22/07): strona Notion "Stan gry AGS" - preferowana droga pakietu kontekstu
(decyzja Tomasza 21/07: stan gry przez LINK, nie wklejke). Jedna strona NADPISYWANA
(soft-clear table_registry._re_render, nie append); tresc = reports.kontekst_text('all'),
czyli dokladnie to samo co /kontekst. Odswiezenie tickiem z petli sync workera po zmianie
stanu (publikacja / lejek / kontakt / decyzje / plan), throttle max 1 update / 15 min.
Gdy Notion timeoutuje (znane z #71) - trudno: blad w logu, fallback /kontekst, NIC innego
nie jest blokowane. Konfiguracja: brand_config AGS 'stan_gry_page_id' (id strony Notion
z Connection integracji - AP-305). ZERO DDL: stan w brand_config 'stan_gry_state'."""
import datetime
import hashlib
import traceback

from .. import db

PAGE_KEY = "stan_gry_page_id"    # id strony Notion (zaklada Tomasz, SQL w komponencie)
STATE_KEY = "stan_gry_state"     # {"sig": ..., "ts": iso ostatniej PROBY}
THROTTLE_MIN = 15


def _cfg(key):
    r = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key=%s", (key,))
    return (r or {}).get("config_value")


def _signature():
    """Odcisk stanu: max znaczniki czasu tabel, ktore zmieniaja stan gry. Rowny odcisk = zero
    zapisu do Notion (checksum w _re_render i tak by to zlapal, ale nie skladamy tekstu)."""
    r = db.fetchone(
        """SELECT md5(concat(
             (SELECT COALESCE(MAX(published_at)::text,'') FROM published_posts),
             (SELECT COALESCE(MAX(updated_at)::text,'') FROM sales_pipeline),
             (SELECT COALESCE(MAX(updated_at)::text,'') FROM contacts),
             (SELECT COALESCE(MAX(created_at)::text,'') FROM engagement_log),
             (SELECT COALESCE(MAX(created_at)::text,'') FROM agent_decisions),
             (SELECT COALESCE(MAX(updated_at)::text,'') FROM content_items)
           )) AS sig""")
    return (r or {}).get("sig")


def tick():
    """Wolane z petli sync workera (notion_worker._loop, co <=60 s). Kazdy blad = log,
    nigdy wyjatek na zewnatrz (stan gry nie moze wywrocic mirrora)."""
    try:
        page = (_cfg(PAGE_KEY) or "").strip()
        if not page:
            return  # nie skonfigurowane - organ spi (Tomasz poda strone przy tap-tescie c)
        import json
        try:
            st = json.loads(_cfg(STATE_KEY) or "{}")
        except Exception:
            st = {}
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            last = datetime.datetime.fromisoformat(st.get("ts"))
            if (now - last).total_seconds() < THROTTLE_MIN * 60:
                return
        except (TypeError, ValueError):
            pass
        sig = _signature()
        if sig and sig == st.get("sig"):
            return
        from .. import reports
        text = reports.kontekst_text("all")
        checksum = hashlib.md5(text.encode("utf-8")).hexdigest()
        from . import table_registry
        # ts PRZED proba zapisu: porazka Notion tez zuzywa okno throttle (nie mlocimy API)
        _save_state({"sig": st.get("sig"), "ts": now.isoformat()})
        status, info = table_registry._re_render("stan_gry", "AGS", page, text, checksum)
        _save_state({"sig": sig, "ts": now.isoformat()})
        print(f"[stan_gry] {status}: {info}", flush=True)
    except Exception as e:
        traceback.print_exc()
        print(f"[stan_gry] tick padl: {type(e).__name__}: {e}", flush=True)


def _save_state(obj):
    import json
    db.execute(
        """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
           VALUES ('AGS',%s,%s,1,'stan-gry',NOW())
           ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
             version=brand_config.version+1, updated_by='stan-gry', updated_at=NOW()""",
        (STATE_KEY, json.dumps(obj, ensure_ascii=False)))
