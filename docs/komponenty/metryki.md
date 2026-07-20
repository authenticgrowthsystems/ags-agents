# Komponent: METRYKI (kolektor X, import LinkedIn, raporty PROFIL)

## Co robi

Konczy slepote metryczna: zbiera metryki kanalow i postow do bazy i podaje je
w raportach subagentow. Trzy zrodla danych, jeden konsument (reports).

1. **Kolektor X Owned Reads (LIVE od 20/07)**: raz na dobe (UTC) pobiera
   WLASNE posty z prywatnymi metrykami (GET /2/users/{id}/tweets, OAuth1,
   Owned Read $0.001/odczyt, ~$4.50/mies) i utrwala snapshoty. Prywatne
   metryki X sa dostepne tylko <30 dni wstecz - snapshot ratuje historie.
2. **Import LinkedIn xlsx**: Tomasz wysyla eksport AggregateAnalytics jako
   dokument na Telegram -> parser -> metryki dzienne + demografia + merge
   per-post.
3. **Reczny wpis X** (fallback): `subagent_set_metrics` w rozmowie subagenta.

## Wejscia-wyjscia i tabele

- `x_post_metric_snapshots` (DDL 025): snapshot per (tweet_id, snapshot_date);
  public/non_public/organic_metrics jsonb 1:1 z API + raw.
- `channel_metrics_daily` (DDL 023): dzienne metryki kanalu (impressions,
  reactions, new_followers, followers_total); UNIQUE (brand, channel, date);
  COALESCE-merge - ponowny import nie nadpisuje danych innego zrodla;
  source: linkedin_xlsx / x_manual / x_api / linkedin_api.
- `channel_audience_snapshots` (DDL 023): demografia obserwujacych per import.
- `published_posts.engagement_metrics`: merge per-post (LinkedIn: match po URN
  ugcPost-/share-<digits>; X: match post_id=tweet_id, najnowszy snapshot,
  ZERO platnych odczytow przy raportach - placimy tylko w collect()).
- Raporty: cron n8n 08:00 daily / nd 20:00 weekly -> POST /reports/<kind> ->
  per supervised cel -> subagent_daily/weekly_reports + push na bot #2;
  sekcja PROFIL z channel_metrics_daily (>3 dni bez danych = prosba o eksport).

## Konfiguracja

- `channels.config.stats_mode` per cel: manual / member_api / org_api /
  x_owned_reads. Wlaczenie kolektora = RECZNY UPDATE stats_mode PO sondzie
  probe i potwierdzeniu klasy rozliczenia w Developer Console (kod nigdy nie
  wlacza sam). Dla AGS/x: 'x_owned_reads' od 20/07.
- `channels.config.x_user_id`: cache id konta (sonda zapisuje sama).
- Guardraile kosztow: alert logbot >200 zasobow/dzien, twardy stop paginacji
  500, Spend Cap $20/cykl w konsoli X.
- LinkedIn API (member_api/org_api) czeka na App 2 CMA - do tego czasu xlsx.

## Punkty zaczepienia w kodzie

- `cm-agent/app/x_collector.py`: `collect` (zbior dzienny), `tick` (guard
  durable po MAX(snapshot_date) - restart kontenera nie powtarza platnego
  zbioru), `probe` (sonda: `docker exec cm-agent python -m app.x_collector
  probe`), `oauth1_signature` (HMAC-SHA1 stdlib, wektor z docs.x.com),
  `refresh_published_metrics`, `snapshot_to_metrics`, `_followers`.
- `cm-agent/app/metrics_import.py`: `handle_telegram_xlsx`,
  `parse_aggregate_xlsx` (parser POZYCYJNY po ksztalcie arkusza,
  locale-odporny PL/EN), `import_linkedin_xlsx`.
- `cm-agent/app/reports.py`: `refresh_metrics` (galezie per stats_mode),
  `_profile_lines` (sekcja PROFIL), `daily_report`, `weekly_report`, `run_all`,
  `set_manual_metrics`.
- `cm-agent/app/worker.py`: `_x_collector_tick` (petla), `POST /metrics/xlsx`.
- n8n HITL: galaz document_xlsx (Doc Secret -> Doc Metrics Fire).

## Kanony ktore go dotycza

- REGULA PRAWDY: kazda sciezka bledu importu konczy sie wiadomoscia; raport
  mowi wprost gdy dane sa stare.
- Docs-first: parametry endpointow X potwierdzone z docs.x.com przed kodem;
  zadnego GET /2/tweets (klasa rozliczenia niepotwierdzona).

## Znane pulapki

- Kazdy dzien zwloki we wlaczeniu kolektora = BEZPOWROTNIE stracone
  non_public metryki postow starszych niz okno 30 dni.
- start_time = now-29d (margines na 400 przy postach na granicy 30 dni;
  gdyby 400 - pierwszy podejrzany, zmniejszyc do 28).
- Retweety wykluczone (brak prywatnych metryk); wlasne reply zostaja.
- Poniedzialkowy monit o reczne metryki X wyciszony gdy stats_mode != manual
  (commit 6876b46; wchodzi z nastepnym rebuildem - do tego czasu ignorowac).
- Klasa rozliczenia /2/users/me nieudokumentowana wprost (1 read/dzien,
  miesci sie w guardrailu).
