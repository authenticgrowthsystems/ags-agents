# Komponent: SYNC NOTION (mirror DB->Notion, drift check, brand_tokens)

**STATUS GOTOWOSCI: KOMPLETNY** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

SSOT = PostgreSQL `ags_crd`. Notion = READ-ONLY MIRROR dla czlowieka (67 stron
oznaczonych czerwonym calloutem "READ-ONLY MIRROR OD 05/07/2026"). Sync worker
w cm-agent odbija zmiany z bazy do Notion jednokierunkowo; drift check pilnuje,
zeby nikt nie edytowal mirrora recznie. JEDYNY wyjatek od kierunku DB->Notion:
brand_tokens (tam SSOT = baza Notion "Brand Config", puller ciagnie DO bazy -
patrz grafika.md).

## Przeplyw

```
Zmiana wiersza (23 tabele) -> trigger ags_sync_enqueue -> sync_queue
  + NOTIFY ags_sync
Worker (watek w cm-agent, watchdog, log logs/sync_worker.log):
  LISTEN + poll 60s backstop -> FOR UPDATE SKIP LOCKED -> dispatch wg
  sync_registry -> Notion API (throttle 3 req/s, backoff 2..32s max 5 prob
  -> alert bot #2)
Wzorce renderu:
  re_render - canonical strony (SOFT-CLEAR z trackingiem: nowa sekcja na
    gorze <10s, id-y blokow w sync_mirror_state, stara sekcja archiwizowana)
  append - dzienniki (dopisywanie wpisow)
Drift check (cron n8n 03:00, app.sync.drift_check): wykrywa reczne edycje
  callouta po md5 + zgubione triggery -> alert Telegram bot #2
```

## Wejscia-wyjscia i tabele

- `sync_queue`: ledger zmian do odbicia (status, retry info).
- `sync_mirror_state`: block_ids + last_checksum + callout_md5 per cel.
- `sync_registry`: KONFIGURACJA per tabela - enable = UPDATE wiersza, zero
  rebuildu; page_map dla brand_config (ktory klucz -> ktora strona Notion).
- Flaga sprzedawalnosci: `brand_config.sync_to_notion` per marka (v1: AGS on).
- v1 enabled: brand_config + manager_daily_log; reszta tabel czeka na wlaczenie
  w sync_registry (plan: docs/cm/SYNC_ENABLE_PLAN.md).

## Strona "Stan gry AGS" (LACZNIK 22/07)

Wyjatek od mirrora per-tabela: JEDNA strona Notion skladana z WIELU tabel
(tresc = reports.kontekst_text('all'), to samo co /kontekst). Odswieza ja
`sync/stan_gry.py:tick()` wolany z petli notion_workera po kazdym drainie:
throttle 15 min + odcisk stanu (md5 max timestampow published_posts / sales_pipeline /
contacts / engagement_log / agent_decisions / content_items) -> zmiana ->
`table_registry._re_render('stan_gry','AGS', page, ...)` (ten sam soft-clear
i sync_mirror_state co mirror tabel; bez wpisu w sync_registry - tick woła render
bezposrednio). Konfiguracja: brand_config AGS `stan_gry_page_id` (SQL, /set nie zna
klucza); stan throttla w `stan_gry_state`. Konsument: czatowy agent na abonamencie
czyta strone z linku (komponent [lacznik.md](lacznik.md)).

## Konfiguracja

- `sync_registry` (enable/disable tabel, page_map) - sterowanie bez deployu.
- `brand_config.sync_to_notion` per marka.
- `app_secrets.notion_api_key`; Connection integracji na KAZDEJ stronie/bazie
  docelowej (AP-305 - bez Connection API nie widzi strony).
- brand_tokens puller: `/set brand_tokens_notion_db <database_id>`.

## Punkty zaczepienia w kodzie

- `cm-agent/app/sync/notion_worker.py`: `run_forever`, `_loop`, `_claim`,
  `_retry` (backoff), `_drain`.
- `cm-agent/app/sync/table_registry.py`: `dispatch`, `_re_render`, `_append`,
  `_target_page` (routing wiersz -> strona).
- `cm-agent/app/sync/render.py`: `md_to_blocks` (markdown -> bloki Notion,
  max 280), `mirror_callout` (naglowek z checksum).
- `cm-agent/app/sync/drift_check.py`: `main` (cron 03:00).
- `cm-agent/app/sync/notion_api.py` (klient), `brand_tokens_pull.py`
  (kierunek odwrotny).
- `etl/mirror_headers.py`: jednorazowe oznaczenie 67 stron (ledger:
  brand_config `mirror_headers_done`).

## Kanony ktore go dotycza

- SSOT = PostgreSQL; nowe wpisy WYLACZNIE przez agentow do bazy, Notion odbija
  (doktryna #71, 05/07).
- Kanoniczne decyzje w Notion AGS Hub wpisuje Tomasz RECZNIE przez UI
  (API na AGS Hub timeoutuje - patrz pulapki).

## Znane pulapki

- Notion API potrafi timeoutowac na duzych stronach (AGS Hub) - dlatego
  Manager/BE NIE pisze do Notion bezposrednio; sync worker ma retry+backoff,
  reczne wpisy kanoniczne robi Tomasz w UI.
- AP-305: brak Connection integracji na stronie/bazie = API jej NIE WIDZI
  (najczestsza przyczyna "pusto mimo poprawnego id").
- Reczna edycja strony-mirrora = drift; wykryje go cron 03:00 po md5
  callouta, ale poprawka to ponowny re_render, nie scalanie - edycje reczne
  GINA. Edytowac zrodlo w bazie.
- Wlaczenie kolejnej tabeli = UPDATE sync_registry, ale najpierw sprawdz
  wzorzec renderu (re_render vs append) i page_map.
