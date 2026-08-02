-- D-009 (02/08/2026): migracja gotowcow mailowych z kanalu 'Other' do 'Email'.
--
-- MUSI ZOSTAC URUCHOMIONE **PO** REBUILDZIE cm-agent, W TYM SAMYM OKNIE.
-- Regula Tomasza z 02/08: "slownik i migracja istniejacych wierszy ida w jednym kroku
-- albo nie ida wcale". Powod: wartosc kanalu jest KLUCZEM DOPASOWANIA w
-- `sales._open_outreach_rows` - kod i dane rozjechane znacza, ze nowy gotowiec nie znajduje
-- starego i go nie uniewaznia. Dokladnie tak powstala wada StandART z 24/07.
--
-- DLACZEGO PO REBUILDZIE, A NIE PRZED: miedzy dwoma krokami jest okno, w ktorym ktos moze
-- napisac gotowca. Jesli UPDATE pojdzie PIERWSZY, taki gotowiec wpadnie do starego 'Other'
-- i zostanie tam na zawsze - nikt go juz nie przeniesie. Jesli UPDATE idzie OSTATNI, zgarnia
-- rowniez to, co powstalo w oknie. Ta kolejnosc czyni okno SAMONAPRAWIALNYM.
--
-- STAN PRZED (odczyt 02/08): engagement_log ma 347 wierszy; kanaly X=170, LinkedIn=169,
-- Other=9. W 'Other' siedza WYLACZNIE gotowce mailowe Sprzedawcy (rejected=7, proposed=1,
-- sent=1), kazdy z trescia zaczynajaca sie od "outreach email:". Jedyny zywy 'proposed'
-- to Klub Sportowy StandART z 24/07.
--
-- Uruchomienie (SSH):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_d009_kanal_email_02082026.sql

\encoding UTF8

\echo '--- STAN PRZED ---'
SELECT COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log GROUP BY channel ORDER BY 2 DESC;

\echo '--- MIGRACJA: gotowce mailowe Other -> Email ---'
-- Rozroznik jest ten sam, ktorego uzywa `_open_outreach_rows`: agent + znacznik w notes.
-- Filtr po notes trzyma nas z dala od wierszy Lacznika (RAPORT PRACY), ktore maja tego samego
-- agenta. Warunek na tresc jest TRZECIM pasem: gotowiec mailowy zawsze zaczyna sie od
-- "outreach email:" (sales.py buduje content jako f"outreach {channel}: {nazwa}").
UPDATE engagement_log
   SET channel = 'Email'
 WHERE channel = 'Other'
   AND agent = 'AGS:sprzedaz'
   AND COALESCE(notes,'') ILIKE '%gotowiec outreach%'
   AND COALESCE(content,'') ILIKE 'outreach email:%'
RETURNING id, status, author_display, left(COALESCE(content,''), 40) AS poczatek;

\echo '--- KONTROLA 1: co zostalo w Other (ma byc PUSTO albo same NIE-maile) ---'
SELECT COALESCE(agent,'(brak)') AS agent, status,
       left(COALESCE(content,''), 45) AS poczatek, COUNT(*) AS n
  FROM engagement_log WHERE channel = 'Other'
 GROUP BY 1,2,3 ORDER BY 4 DESC;

\echo '--- KONTROLA 2: rozklad kanalow po migracji (Email ma byc 9) ---'
SELECT COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log GROUP BY channel ORDER BY 2 DESC;

\echo '--- KONTROLA 3: NAJWAZNIEJSZA - czy zywy gotowiec StandART jest odnajdywalny ---'
-- To jest dokladnie zapytanie, ktorego uzywa `_open_outreach_rows` po zmianie slownika.
-- Ma zwrocic JEDEN wiersz. Zero oznacza, ze uniewaznianie poprzednich gotowcow jest zerwane
-- i przy nastepnym gotowcu dla StandART powtorzy sie sytuacja z 24/07.
SELECT id, channel, created_at, author_display
  FROM engagement_log
 WHERE agent = 'AGS:sprzedaz' AND status = 'proposed'
   AND COALESCE(notes,'') ILIKE '%gotowiec outreach%'
   AND channel = 'Email'
 ORDER BY created_at;
