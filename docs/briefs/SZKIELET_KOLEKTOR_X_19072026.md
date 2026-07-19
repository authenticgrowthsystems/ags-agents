# SZKIELET DECYZJI - BUILD KOLEKTOR METRYK X (19/07/2026, Fable 5 prompt 1/2)

Kontynuacja buildu (Opus 4.8): wykonuj krok po kroku wg tego pliku. Brief:
docs/briefs/BRIEF_KOLEKTOR_METRYK_X_19072026.md. Wszystko ponizej wynika z wczytania
masterpromptu, briefu, 3 raportow research (docs/research/x_metrics_19072026/),
reports.py, worker.py, DDL 023, DEPLOY_CHECKLIST i SYSTEM_DATAFLOW.

## D0. Galaz robocza (odstepstwo od komendy z sekcji 0 briefu - intencja zachowana)

Sesja Cowork ma juz WLASNY izolowany worktree `.claude\worktrees\sad-mendel-a94de4`,
wiec zamiast drugiego worktree zrobiony jest checkout galezi **build/kolektor-x**
(od origin/claude/silly-blackwell-dfc32d = 2fa33ed) w tym worktree. Committuj TYLKO tu.
Integrator merguje build/kolektor-x jak w planie - bez zmian dla niego.

## D1. Stan zastany (zweryfikowane w kodzie, nie zgadywane)

- Sekrety OAuth1 w app_secrets: `x_consumer_key`, `x_consumer_secret`, `x_access_token`,
  `x_access_token_secret` (ksztalt potwierdzony: DEPLOY_CHECKLIST.md:87 + SYSTEM_DATAFLOW.md:23;
  zrotowane 02/07, uzywane przez publisher OAuth1 POST /2/tweets - dzialaja).
- Szew: `reports.refresh_metrics` galaz `mode == "x_owned_reads"` -> `return 0` (reports.py:76-80).
- Petla workera: `loop()` w worker.py (~linia 437) wola ticki; wzorzec throttlingu =
  `sync/brand_tokens_pull.py` (`INTERVAL_S` + `_last=[0.0]`), ale dla kolektora dobowy guard
  robimy DURABLE przez DB (patrz D4), nie in-memory.
- channel_metrics_daily istnieje (DDL 023), source ma CHECK z dozwolonym `'x_api'` - pasuje.
- requirements.txt: httpx jest, biblioteki OAuth1 NIE ma -> podpis OAuth 1.0a HMAC-SHA1
  ze stdlib (hmac, hashlib, urllib.parse, secrets, base64, time). Zero nowych zaleznosci.
- published_posts.post_id = tweet_id (publisher zapisuje) - klucz do merge metryk.
- Wolny numer DDL: 025.

## D2. Architektura (Pareto: jeden nowy modul + 2 male szwy)

NOWY plik `cm-agent/app/x_collector.py`:
1. `_oauth1_get(url, params)` - podpis OAuth 1.0a user context (HMAC-SHA1) + httpx.get.
   Parametry query MUSZA wejsc do bazy podpisu (percent-encoding wg RFC 3986).
2. `_user_id(cfg)` - numeryczne id uzytkownika: najpierw z `channels.config.x_user_id`;
   gdy brak -> GET /2/users/me (raz), zapis do channels.config (UPDATE config jsonb_set)
   + zwrot. (Brief: "user id zapisac raz" - decyzja: channels.config celu AGS/x.)
3. `probe(brand_id='AGS', channel='x')` - SONDA (DoD krok 1): 1 request
   GET /2/users/{id}/tweets, max_results=5, pelne tweet.fields (created_at,
   referenced_tweets,public_metrics,non_public_metrics,organic_metrics),
   start_time = now-29d. Drukuje JSON + weryfikuje obecnosc non_public_metrics na
   najswiezszym poscie. Uruchamialna na serwerze:
   `docker exec cm-agent python -m app.x_collector probe`
   (dodac `if __name__ == "__main__"` z argv). NIE zapisuje snapshotow (sonda = read-only).
4. `collect(brand_id, channel)` - dzienny zbior:
   - paginacja GET /2/users/{id}/tweets: max_results=100, start_time=now-29d
     (margines 1 dnia pod ryzyko 400 przy non_public_metrics dla postow ~30d - patrz D6),
     pagination_token az do konca; `exclude=retweets` (retweety nie maja prywatnych metryk;
     wlasne reply ZOSTAJA - to tez tresc).
   - kazdy post -> INSERT do x_post_metric_snapshots (ON CONFLICT (tweet_id, snapshot_date)
     DO UPDATE - idempotencja w ramach doby).
   - licznik zasobow: suma zwroconych postow; **guardrail: >200/dzien -> logbot alert;
     twardy stop paginacji na 500** (spend cap $20 w konsoli = druga linia obrony).
   - followers: GET /2/users/me?user.fields=public_metrics -> followers_count ->
     UPSERT channel_metrics_daily (brand, 'x', dzis, followers_total, source='x_api').
     UWAGA (punkt otwarty do sondy): klasa rozliczenia /2/users/me niepotwierdzona w docs -
     to 1 request/dzien, mieści sie w guardrailu; potwierdzic w konsoli przy sondzie.
   - na koniec: `reports.refresh_metrics(brand_id, channel)` NIE jest wolany stad -
     worker tick wola go po collect (patrz D4).
5. `tick()` - wolany z petli workera co obieg, TANI:
   - cele: SELECT z channels WHERE config->>'stats_mode'='x_owned_reads' AND status='active'.
   - dobowy guard DURABLE: SELECT MAX(snapshot_date) z x_post_metric_snapshots dla celu;
     jesli >= dzisiejsza data UTC -> skip (restart kontenera nie robi drugiego zbioru;
     zadnego stanu in-memory). Po granicy doby UTC -> collect() + refresh.
   - throttle zapytan do DB: in-memory `_last` 10 min jak brand_tokens_pull (zeby nie
     odpytywac channels co 2s) - polaczenie obu wzorcow.

SZEW 1 - `worker.py` loop(): jedna linia `x_collector.tick()` obok `_brand_tokens_tick()`
(lazy import w funkcji, wzorzec _brand_tokens_tick; konflikt merge w worker.py rozwiazuje
integrator - zmiana = 1 linia + 1 maly def).

SZEW 2 - `reports.py` galaz `x_owned_reads`: ZERO wywolan API. Czyta NAJNOWSZY snapshot
per tweet_id z x_post_metric_snapshots (30 dni) i merguje do
published_posts.engagement_metrics po post_id=tweet_id. Mapowanie:
- impressions = non_public.impression_count (fallback public.impression_count)
- reactions = public.like_count; comments = public.reply_count
- reshares = public.retweet_count + public.quote_count
- clicks = non_public.url_link_clicks; + profile_clicks = non_public.user_profile_clicks
- engagement_rate liczony jak w set_manual_metrics; source='x_api', fetched_at=now.
Zwraca liczbe zaktualizowanych wierszy (koniec `return 0`).

## D3. DDL 025 - `cm-agent/db/025_x_post_metric_snapshots.sql`

```sql
CREATE TABLE IF NOT EXISTS x_post_metric_snapshots (
    id BIGSERIAL PRIMARY KEY,
    brand_id VARCHAR(50) NOT NULL,
    channel VARCHAR(40) NOT NULL DEFAULT 'x',
    tweet_id VARCHAR(30) NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')::date,
    observed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at_x TIMESTAMPTZ,
    public_metrics JSONB,
    non_public_metrics JSONB,
    organic_metrics JSONB,
    raw JSONB,
    UNIQUE (tweet_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS idx_xpms_tweet ON x_post_metric_snapshots(tweet_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_xpms_brand_date ON x_post_metric_snapshots(brand_id, snapshot_date DESC);
```
+ kontrolny SELECT COUNT jak w 023. DDL NIE przelacza stats_mode (patrz D5).
TEN SAM COMMIT: aktualizacja docs/db/SCHEMA_ags_crd.md (regula twarda masterpromptu).

## D4. Kolejnosc wykonania (Opus, w tym oknie)

1. DDL 025 + SCHEMA (commit 1).
2. x_collector.py (OAuth1 + probe + collect + tick) + linia w worker.py + galaz w reports.py
   (commit 2).
3. Testy lokalne BEZ serwera (commit 3): py_compile wszystkiego; test podpisu OAuth1 na
   wektorze z dokumentacji X/Twitter (znany przyklad HMAC-SHA1); test parsera odpowiedzi
   na sztywnym JSON-ie (namespaces obecne/nieobecne); test mapowania metryk szwu 2.
   Test runner: prosty `python cm-agent/tests/test_x_collector.py` (assert, bez pytest -
   pytest nie ma w requirements).
4. STATUS w briefie + raport docs/cm/RAPORT_do_Managera_19072026_kolektor_x.md
   (per krok DoD; commit 4). Masterpromptu NIE dotykac (integrator).

## D5. Sekwencja wlaczenia (dla INTEGRATORA i Tomasza - wpisac do raportu)

1. Integrator: merge + psql 025 + rebuild (paczka zbiorcza).
2. Tomasz (SSH): `docker exec cm-agent python -m app.x_collector probe` -> sprawdza
   non_public_metrics w output + w Developer Console klase rozliczenia = Owned Read $0.001.
3. DOPIERO PO potwierdzeniu (DoD: konsola PRZED cronem) Tomasz wlacza cel jedna komenda SQL:
   `UPDATE channels SET config = jsonb_set(config,'{stats_mode}','"x_owned_reads"') WHERE brand_id='AGS' AND channel='x';`
   Od nastepnego obiegu petli tick() rusza (pierwszy zbior od razu - guard dobowy pusty).
4. Fallback set_manual_metrics ZOSTAJE bez zmian.

## D6. Punkty otwarte (rozstrzygnac docs-first w trakcie buildu, NIE zgadywac)

- (a) Czy /2/users/me jest Owned Read czy inna klasa - potwierdzic przy sondzie w konsoli.
- (b) Znane zachowanie API: zadanie non_public_metrics dla postow >30 dni potrafi dac 400
  na calym requescie. Mitygacja w szkielecie: start_time=now-29d. Przy buildzie sprawdzic
  docs.x.com (get-posts + metrics) czy start_time wystarcza; jesli docs mowia inaczej -
  dostosowac (np. dwa przebiegi: pelne pola dla <29d).
- (c) 150 aktywnych postow -> 2 strony paginacji; upewnic sie ze pagination_token
  wchodzi do podpisu OAuth1 poprawnie (kazdy param query musi byc w bazie podpisu).

## D7. Czego NIE dotykac (z briefu, przypomnienie)

Publikacja X (Scheduler/OAuth1 publish w n8n) bez zmian. Zadnego GET /2/tweets.
Zadnego scrapingu. Zero deployu/psql/n8n z tej sesji. Tylko pliki: x_collector.py (nowy),
worker.py (1 szew), reports.py (1 galaz), db/025 (nowy), SCHEMA_ags_crd.md, tests (nowy),
brief STATUS, raport (nowy).
