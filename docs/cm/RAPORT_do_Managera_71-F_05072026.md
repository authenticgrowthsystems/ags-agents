# RAPORT do Managera - TASK #71 FAZA F: SYNC WORKER ZBUDOWANY (przed cutoverem)

**Od:** BUILD ENGINEER (BE)
**Data:** 05/07/2026 wieczor (3 dni przed planowanym cutoverem 08/07)
**Zakres:** sync DB->Notion one-way wg kontraktu sekcja 6 + trzech decyzji Managera z 05/07
(worker w cm-agent / hybryda re_render-append / v1 = brand_config + manager_daily_log).

---

## 1. DOCS-FIRST - FAKTY ROZSTRZYGAJACE (oficjalna dokumentacja Notion, 05/07)
- Rate limit: srednio 3 req/s, 429/529 z Retry-After (throttle identyczny jak w silniku ETL).
- Append children: max 100 blokow/call, `position {"type":"start"}` = wstawka NA GORE strony.
- PATCH bloku: podmienia cale rich_text (element max 2000 zn.); typu bloku nie zmienimy.
- **DELETE blokow: BRAK operacji masowej - 1 blok = 1 call.** Pelny re-render 200-blokowej
  Voice Bible = ~70s samych delete'ow.

**ROZSTRZYGNIECIE otwartego pytania Managera (delete en masse vs iteracja):** soft-clear
Z TRACKINGIEM. Worker dopisuje nowa sekcje mirrora NA GORE strony (1-3 calle => widoczna <10s,
spelnia akceptacje niezaleznie od rozmiaru), zapamietuje w `sync_mirror_state.block_ids` id-y
wgranych blokow i archiwizuje POPRZEDNIA sekcje per blok w tle (throttled). Przy pierwszym
renderze na stronie zrodlowej stara tresc zostaje ponizej jako historia - kolejne podmiany
wymieniaja juz tylko wlasna sekcje. Zero masowych delete, zero rozjazdu.

## 2. CO ZBUDOWANE (commit tej fazy)
| Plik | Rola |
|---|---|
| cm-agent/db/014_sync_registry.sql | sync_registry (24 tabele wg mapy Managera, v1 enabled=2), sync_queue (durable, backoff), sync_mirror_state (tracking blokow + checksum), generyczny trigger ags_sync_enqueue + NOTIFY, triggery na WSZYSTKICH 23 mapowanych tabelach (wlaczenie tabeli = UPDATE enabled, zero DDL) |
| cm-agent/app/sync/notion_api.py | klient: throttle 3 req/s, Retry-After, append children (chunk 100, position start), archive per blok |
| cm-agent/app/sync/render.py | markdown->bloki (2000 zn./element), callout mirrora z md5, wpisy append |
| cm-agent/app/sync/table_registry.py | dispatch per wzorzec; KEYERS/CONTENT/METAS per tabela; gate brand_config.sync_to_notion; cel = page_map z registry albo notion_page_id wiersza |
| cm-agent/app/sync/notion_worker.py | LISTEN ags_sync + poll 60s backstop; FOR UPDATE SKIP LOCKED; backoff 2/4/8/16/32 max 5x -> failed + Telegram (bot #2); watchdog restart 30s; log logs/sync_worker.log |
| cm-agent/app/sync/drift_check.py | on-demand + cron 03:00: zdrowie kolejki, integralnosc calloutow (reczna edycja Notion = alert), DB-vs-mirror checksum |
| etl/mirror_headers.py | CUTOVER (dopiero po approve): callout READ-ONLY MIRROR na gorze kazdej zmigrowanej strony (kotwice z 20 tabel + page_map), idempotentny ledger, --dry |
| cm-agent/app/worker.py | start watku sync w main() |

Implementation notes Managera pokryte: osobny modul sync/ (post-M5 przenosny), watchdog+alert,
wlasny throttle, osobny log. **Odstepstwo:** graceful-drain na SIGTERM pominiety swiadomie -
kolejka jest durable w DB, wiec restart nic nie gubi (wpis processing wraca do pending recznie
lub przy retry); prosciej i bezpieczniej niz drain w daemon-watku. Do dopisania przy refaktorze
na osobny kontener, jesli Manager podtrzyma wymog.

## 3. OGRANICZENIA v1 (jawne)
- brand_config bez wpisu w page_map (np. admin_chat_ids, cm_*) = swiadomie pominiete (skipped).
- Cel TNM w page_map zadziala dopiero po ustawieniu brand_config TNM sync_to_notion='true'
  (flaga sprzedawalnosci dziala dokladnie tak, jak zaprojektowano).
- manager_daily_log meta_type spoza page_map (np. ssot_event) = skipped z logiem.
- Strony inspirations (kotwice page#hash) bez naglowka mirrora w v1.
- Test "manual edit Notion -> alert <5min": drift_check jest on-demand (test odpalamy recznie)
  + cron 1x/dzien 03:00 - zgodnie z mechanizmem kontraktu sekcja 6.

## 4. SEKWENCJA DEPLOYU (Tomasz, kolejnosc wazna)
1. PowerShell push; 2. SSH pg_dump; 3. SSH pull + DDL 014; 4. SSH rebuild cm-agent (szablon
masterpromptu sekcja 4) -> worker startuje z kontenerem; 5. testy akceptacyjne sekcji 8:
   - A (re_render <10s): dopisz linijke testowa do brand_config website_canon -> callout+tresc
     na gorze strony Notion <10s; cofnij edycje -> mirror sie podmienia.
   - B (append <10s): INSERT testowy do manager_daily_log (daily_status) -> wpis na koncu strony.
   - C (drift): recznie zepsuj callout w Notion -> `python -m app.sync.drift_check` -> alert
     na bocie #2.
6. cron drift 03:00; 7. **08/07 po approve Managera/Tomasza:** mirror_headers --dry -> real
   -> task #71 przechodzi w monitoring 24h (zamkniecie 09/07 wg akceptacji: sync 24h bez driftu).

Rollback (kontrakt sekcja 7): wylaczenie = UPDATE sync_registry SET enabled=FALSE (natychmiast,
bez rebuildu); pelny = usuniecie naglowkow + DROP TRIGGER (odwrotnosc DDL 014).

---

## 5. WYKONANIE (05/07 wieczor) - FAZA F LIVE + CUTOVER DONE

Deploy: backup 71F + DDL 014 (23 tabele w sync_registry, v1 enabled=2) + rebuild -> worker LIVE
18:12:25. **Testy akceptacyjne sekcji 8 - WSZYSTKIE ZALICZONE z dowodami:**
- **A (re_render):** edit website_canon -> callout+tresc na gorze strony w ~2s (id=1 done);
  podmiana sekcji: id=2 done "re_render 100 blokow (+100 starych zarchiwizowanych)" = soft-clear
  z trackingiem dziala; wpis planera (cm_month_outline) poprawnie skipped (brak page_map).
- **B (append):** INSERT manager_daily_log -> wpis na koncu Dziennika Managera w ~2s (id=4,
  3 bloki; potwierdzone wizualnie na stronie).
- **C (drift) - 2 INCYDENTY ZLAPANE PRZEZ TEST, oba naprawione:**
  1) kontrola callouta wykrywala tylko BRAK md5, nie dopiski ("XXX" przechodzilo) -> fix DDL 015
     + callout_md5 (porownanie 1:1 pelnego tekstu), commit 2df3260;
  2) alert Telegram nie wychodzil z one-shot kontenera (log_bot_token w app_secrets, nie w .env)
     -> drift_check laduje token jak worker, commit b457c8f. Po fixach: wykrycie "callout zmieniony
     recznie" + alert na bocie #2 POTWIERDZONE przez Tomasza; po sprzataniu "[drift] OK".
- Cron drift 03:00 w crontabie (obok backupu 03:30), duplikat linii oddeduplikowany.

**CUTOVER (decyzja Tomasza guzikami: TERAZ, 3 dni przed planem):** dry-run wykryl luke - 51 stron
z kotwic wierszowych + 16 stron bez kotwic (raporty subagentow, zamkniecie miesiaca, chat registry,
story bank, radar; commit e997ab5). Real: **67/67 stron oznaczonych, fail=0.**

**STATUS #71: wszystkie fazy A-F WYKONANE. Zostal monitoring 24h (drift cron 03:00 + kontrola
06/07) -> po czystej dobie #71 CLOSED (3 dni przed terminem 09/07).** SYSTEM_DATAFLOW.md sekcja F
dopisana (living doc). Precedens sprzedawalnosci dziala: klient bez Notion = sync_to_notion FALSE.
