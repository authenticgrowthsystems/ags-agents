# RAPORT do Managera - BUILD KOLEKTOR METRYK X (19/07/2026, BE-KOLEKTOR, tryb rownolegly)

Galaz: **build/kolektor-x** (od origin/claude/silly-blackwell-dfc32d = 2fa33ed).
Commity: baf3793 (szkielet decyzji) -> cedde3c (DDL 025 + SCHEMA) -> fbb23fc (kolektor +
szwy) -> a352a86 (testy 16/16) -> ten raport + STATUS.
Zgodnie z sekcja 0 briefu: ZERO deployu, ZERO psql, ZERO n8n z tej sesji - sklada INTEGRATOR.

## 1. Co zbudowano (per DoD briefu)

| DoD | Stan | Jak |
|---|---|---|
| Sonda: 1 request pelne pola -> non_public_metrics obecne | KOD GOTOWY, wykonanie u Tomasza po deployu | `x_collector.probe()`: max_results=5, pelne tweet.fields, BEZ zapisu; drukuje PASS/FAIL na obecnosci non_public_metrics |
| Developer Console potwierdza Owned Read PRZED cronem | CZEKA NA TOMASZA | sekwencja wlaczenia wymusza to: stats_mode NIE jest ustawiany przez DDL ani kod - dopiero reczny UPDATE po potwierdzeniu ceny |
| DDL 025 x_post_metric_snapshots + zapis channel_metrics_daily | DONE | cm-agent/db/025_x_post_metric_snapshots.sql (UNIQUE tweet_id+snapshot_date, 3 namespaces jsonb + raw) + SCHEMA_ags_crd.md w tym samym commicie; followers dziennie -> channel_metrics_daily (source 'x_api', new_followers = diff vs poprzedni dzien, merge nie nadpisuje danych z innych zrodel) |
| Dzienny tick w petli workera | DONE | worker._x_collector_tick (wzorzec _brand_tokens_tick, lazy import); guard dobowy DURABLE po MAX(snapshot_date) w DB - restart kontenera nie powtarza platnego zbioru; throttle zapytan o cele 10 min |
| refresh_metrics 'x_owned_reads' zasila engagement_metrics | DONE | reports.py: galaz wola x_collector.refresh_published_metrics - najnowszy snapshot per post merge'owany do published_posts.engagement_metrics (match post_id=tweet_id, source 'x_api'); ZERO platnych odczytow przy raportach - placimy tylko w collect() raz na dobe |
| Guardrail kosztow | DONE | alert logbot >200 zasobow/dzien (z szacunkiem kosztu), twardy stop paginacji na 500; 3. linia = Spend Cap $20/cykl w konsoli (decyzja Tomasza 19/07) |

## 2. Decyzje techniczne (z dowodami)

- **OAuth 1.0a HMAC-SHA1 ze stdlib** - zero nowych zaleznosci (requirements bez zmian).
  Podpis zweryfikowany testem na ZYWYM wektorze z docs.x.com "Creating a signature"
  (WebFetch 19/07: URL api.x.com/1.1, oczekiwany podpis Ls93hJiZbQ3akF3HF3x1Bz8/zU4= -
  nasza implementacja daje identyczny). Query string budowany tym samym enkodowaniem co
  baza podpisu (rozjazd = 401).
- **Parametry endpointu potwierdzone docs-first** (WebFetch docs.x.com/x-api/users/get-posts):
  pagination_token, start_time UTC, exclude=retweets, max_results 5-100, wszystkie 3
  namespaces w tweet.fields, auth "UserToken (OAuth)" = user context.
- **start_time = now-29d** (nie 30): margines 1 dnia na ryzyko 400, gdy post przekroczy
  30 dni miedzy stronami paginacji przy zadanych non_public_metrics (ograniczenie 30 dni
  potwierdzone w 3 raportach DR; zachowanie graniczne do obejrzenia na sondzie).
- **Zadnego GET /2/tweets** (Owned Read niepotwierdzony - zakaz briefu respektowany w kodzie:
  jedyne endpointy to /2/users/{id}/tweets i /2/users/me).
- **x_user_id**: raz z /2/users/me, cache w channels.config.x_user_id (brief dawal wybor
  brand_config albo channels.config; wybrane channels.config bo to atrybut CELU, nie marki).
- **Retweety wykluczone** (brak prywatnych metryk), wlasne reply ZOSTAJA (tez tresc).
- **Koszt dzienny**: ~150 postow + 1 users/me = ~151 zasobow = ~$0.15/dzien = ~$4.53/mies
  (zgodne z prognoza briefu $4.50).

## 3. Testy lokalne (bez serwera, zakaz deployu respektowany)

`python cm-agent/tests/test_x_collector.py` = **16/16 PASS** (stdlib only, stuby
db/logbot/httpx): podpis OAuth1 na oficjalnym wektorze, RFC3986 pct (spacja %20, ! %21,
unreserved, dwukropek timestampu), mapowanie snapshot->engagement_metrics (priorytet
non_public impression_count, fallback public, reshares=retweet+quote, engagement_rate,
zera przy brakach), paginacja 2 stron, twardy stop na 500 + alert, HTTP!=200 rzuca
wyjatek. Plus py_compile wszystkich dotknietych plikow.

## 4. Dla INTEGRATORA (BRIEF_INTEGRACJA)

- Merge build/kolektor-x: konflikty mozliwe TYLKO w worker.py (1 nowy def + 1 linia w loop()
  za _brand_tokens_tick) i ewentualnie SCHEMA_ags_crd.md (nowa sekcja przed TODO).
  reports.py dotkniety wylacznie w galezi x_owned_reads (5 linii). x_collector.py, 025,
  testy, szkielet = nowe pliki, bezkonfliktowe.
- Paczka deploy: psql 025 + rebuild cm-agent (DDL bezpieczny przed wlaczeniem - tabela
  po prostu czeka pusta; tick spi dopoki stats_mode nie zostanie ustawiony).

## 5. Dla Tomasza (kolejnosc PO deployu integratora - DoD wymusza te sekwencje)

1. SSH sonda: `docker exec cm-agent python -m app.x_collector probe`
   (oczekiwane: HTTP 200, posty z non_public_metrics, [probe] PASS).
2. Developer Console -> sekcja kosztow: potwierdz, ze request rozliczono jako
   **Owned Read $0.001** (nie inna klasa). Przy okazji: klasa rozliczenia /2/users/me
   (punkt otwarty - 1 read/dzien, mieści sie w guardrailu niezaleznie od wyniku).
3. Wlaczenie (SSH psql):
   `UPDATE channels SET config = jsonb_set(config,'{stats_mode}','"x_owned_reads"') WHERE brand_id='AGS' AND channel='x';`
   Tick rusza sam z petli (pierwszy zbior od razu, potem raz na dobe UTC).
4. Nastepnego dnia sprawdz raport dzienny CM - sekcja per-post X powinna zasilic sie
   sama (koniec recznego wpisu; set_manual_metrics zostaje jako fallback).

## 6. Punkty otwarte / ryzyka

- Klasa rozliczenia /2/users/me nieudokumentowana wprost - do odczytu z konsoli po sondzie.
- Zachowanie 400 przy postach na granicy 30 dni: mitygacja start_time=29d; gdyby sonda
  lub pierwszy collect pokazaly 400, pierwszy podejrzany = ten margines (zmniejszyc do 28).
- Prywatne metryki nie sa odtwarzalne wstecz - kazdy dzien zwloki we wlaczeniu = stracone
  non_public dla postow starszych niz okno. Sonda + wlaczenie najlepiej od razu po deployu.
