# RAPORT do Managera: METRYKI - krok [1] planu dnia (19/07/2026)

Od: BE. Kontekst: korekta kanonu 19/07 (zatwierdzone publikuje sie zawsze, niezatwierdzone
nigdy samo) + koniec slepoty metrycznej. Brief: docs/briefs/BRIEF_METRYKI_19072026.md.

## Co zbudowane (kod gotowy, czeka na deploy)

1. **DDL 023** (cm-agent/db/023_channel_metrics.sql): channel_metrics_daily (dzienne metryki
   kanalu, UNIQUE brand/channel/date, COALESCE-merge przy ponownym imporcie) +
   channel_audience_snapshots (demografia jsonb per import). SCHEMA_ags_crd.md w tym samym commicie.
2. **app/metrics_import.py**: parser AggregateAnalytics xlsx POZYCYJNY po ksztalcie arkusza
   (odporny na locale PL/EN naglowkow) + zapis do DB + merge per-post do
   published_posts.engagement_metrics (match po URN ugcPost-/share-<digits>) + paragon na czat.
   REGULA PRAWDY: kazda sciezka bledu konczy sie wiadomoscia, zero cichych porazek.
3. **worker.py**: POST /metrics/xlsx (guard sekretem, 202 + watek tla; wzorzec /message).
4. **reports.py**: sekcja PROFIL w raporcie dziennym i tygodniowym (wyswietlenia/reakcje/nowi
   obserwujacy 7d + lacznie; gdy dane starsze niz 3 dni - prosba o swiezy eksport). Plus szew
   kolektora X: stats_mode 'x_owned_reads' (implementacja po raportach RESEARCH_X_METRICS_*.md).
5. **requirements.txt**: + openpyxl==3.1.5.
6. **n8n HITL LIVE**: galaz document_xlsx (Detect Update Type -> Route -> Doc Secret -> Doc
   Metrics Fire -> /metrics/xlsx). Patcher z backupem bk_hitl_docmetrics_*.json; PUT z filtrem
   settings (binaryMode NIETKNIETY - zweryfikowane po PUT); deactivate+activate wykonane.
   Inne dokumenty niz .xlsx -> 'other' (NoOp), bez zmian zachowania.

## Dowody

- Parser przetestowany na OBU zywych eksportach (docs/evidence/screeny_13-19_07/):
  28 dni metryk 22/06-19/07, 39 postow (18 z kompletem wysw+reakcje), followers_total 488,
  demografia 40 wierszy. Drugi plik (7 dni): 7/7 dni, 19 postow.
- n8n po patchu: 249 wezlow, active=true, rule idx 13 -> Doc Secret -> Doc Metrics Fire,
  settings z binaryMode=separate.
- py_compile OK (metrics_import, worker, reports).

## Analiza dowodow tygodnia 13-19/07 (commit 787238f, evidence w repo)

Autopilot publikowal tez na LinkedIn (nie tylko X); meta-tresc o systemie = 2-44 wysw. vs
2331 narracja biznesowa 5/07; zasieg LI -90% bez obecnosci Tomasza; X 613 postow/10 followers
= problem dystrybucji, nie wolumenu; demografia LI = ICP trafiony (13% zalozyciele, 15%
wlasciciele, 26% firmy 2-10 os.).

## Udzial Tomasza (deploy po krokach [2]-[3], jedna paczka)

1. SSH: `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/023_channel_metrics.sql`
2. Push + rebuild cm-agent (szablony: masterprompt sekcja 8).
3. Tap-test: wyslac AggregateAnalytics_*.xlsx jako dokument na Telegram HITL -> paragon
   "Import metryk LinkedIn" -> potem raport dzienny pokaze sekcje PROFIL.
