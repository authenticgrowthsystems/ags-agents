# BRIEF BUILDU: METRYKI (19072026)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_METRYKI_19072026.md zbuduj`
(Build wykonany w sesji dnia 19/07 na polecenie Tomasza - plan dnia krok [1].)

## 1. CO budujemy (definition of done)

Koniec slepoty metrycznej LinkedIn: Tomasz wysyla plik AggregateAnalytics_*.xlsx (eksport
LinkedIn -> Dane analityczne) jako dokument na Telegram HITL -> CM parsuje i zapisuje do DB
-> raporty subagenta pokazuja metryki profilu. Plus struktura kolektora X (szew pod wytrych
po researchu) - reczny wpis per post juz istnieje (set_manual_metrics, tool subagenta).

DoD (dowody):
- [ ] DDL 023 wgrany (channel_metrics_daily + channel_audience_snapshots) + SCHEMA w tym samym commicie
- [ ] Tomasz wysyla xlsx na Telegram -> paragon CM z podsumowaniem importu (ile dni, ile postow dopasowanych)
- [ ] verify-SQL: SELECT count(*) FROM channel_metrics_daily WHERE brand_id='AGS' AND channel='linkedin' > 0
- [ ] Raport dzienny/tygodniowy zawiera sekcje PROFIL (wyswietlenia dnia/7 dni, obserwujacy)
- [ ] Per-post wyswietlenia/reakcje z xlsx dopisane do published_posts.engagement_metrics (match po URN)

## 2. KONTRAKT wpiecia w szyne

- Tabele: NOWE channel_metrics_daily (brand_id, channel, metric_date UNIQUE-triplet, impressions,
  reactions, new_followers, followers_total, source, raw jsonb) + channel_audience_snapshots
  (demografia jsonb per import). Pisze tez published_posts.engagement_metrics (merge ||, source
  'linkedin_xlsx'). DDL = 023 + docs/db/SCHEMA_ags_crd.md w tym samym commicie.
- Endpointy: POST /metrics/xlsx {chat_id, file_id, file_name} (guard x_researcher_secret,
  202 + watek tla; wzorzec /message). Odpowiedz paragonem przez sendMessage.
- Sekrety: zadnych nowych (TELEGRAM_BOT_TOKEN juz jest).
- Telegram/n8n: HITL Detect Update Type + Route By Update Type + NOWY wezel HTTP Document To CM
  (message.document -> /metrics/xlsx). Patcher z backupem bk_*.json + deactivate/activate + tap.
- Zaleznosc: openpyxl w requirements.txt (parsowanie xlsx w kontenerze).

## 3. Czego NIE dotykac

- Zadnych zmian w planner.py, matreview.py, hitl.py, generate.py, Schedulerze.
- Zadnych zmian w _emergency_promote (to krok [3] planu dnia, osobny build).
- Kolektor X: TYLKO szew (stats_mode 'x_owned_reads' -> None + komentarz do researchu);
  implementacja po raportach RESEARCH_X_METRICS_*.md.

## 4. Zaleznosci i stan zastany

- reports.py: refresh_metrics (stats_mode manual/member_api/org_api), set_manual_metrics (X reczny,
  tool w conversation.py:1890), daily_report/weekly_report + subagent_daily/weekly_reports.
- Format xlsx rozpoznany na zywych plikach: docs/evidence/screeny_13-19_07/AggregateAnalytics_*.xlsx
  (arkusze PL: ODKRYWANIE, REAKCJE, NAJPOPULARNIEJSZE PUBLIKACJE, OBSERWUJACY, DANE DEMOGRAFICZNE;
  daty D.M.YYYY; liczby jako teksty; naglowki moga byc EN przy innym locale - parsowac pozycyjnie
  po ksztalcie arkusza, nie po nazwach kolumn).
- Match per-post: URL zawiera ugcPost-<digits> lub share-<digits> -> published_posts.post_id
  LIKE '%<digits>'.
- Telegram getFile limit 20MB (xlsx ma ~20KB - OK), wzorzec _fetch_telegram_image.

## 5. Udzial Tomasza

1. SSH: psql db/023 (komenda w raporcie).
2. Push + SSH rebuild cm-agent (szablony masterprompt sekcja 8).
3. Tap-test: wyslac AggregateAnalytics_*.xlsx na Telegram, sprawdzic paragon.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_19072026_metryki.md + aktualizacja RESUME_MASTERPROMPT
+ pamiec + STATUS tutaj.

STATUS = DONE-CODE (19/07, sesja dnia): kod + n8n LIVE (galaz document_xlsx, backup
bk_hitl_docmetrics_*.json, binaryMode zweryfikowany po PUT); parser przetestowany na obu
zywych eksportach (28 dni, 39 postow, demografia). CZEKA: psql 023 + rebuild + tap-test
(paczka deploy po krokach [2]-[3]). Raport: docs/cm/RAPORT_do_Managera_19072026_metryki.md
