-- D-009 (02/08/2026): migracja gotowcow mailowych z kanalu 'Other' do 'Email'.
--
-- ============================================================================
-- URUCHOMIC WYLACZNIE PRZY ZATRZYMANYM KONTENERZE cm-agent. Pelna procedura:
--   1) cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest .
--   2) docker stop cm-agent            <- od tej chwili NIKT nie moze wstawic gotowca
--   3) docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_d009_kanal_email_02082026.sql
--   4) docker rm cm-agent && docker run -d --name cm-agent ... (pelna komenda w raporcie)
-- ============================================================================
--
-- DLACZEGO TAK, A NIE "razem w jednym oknie": miedzy rebuildem a UPDATE-em jest okno,
-- w ktorym stary albo nowy kod moze wstawic gotowca. OBIE kolejnosci zostawiaja dziure:
-- wiersz trafia do jednego kanalu, a szukanie idzie do drugiego, wiec poprzedni gotowiec
-- nie zostaje uniewazniony. Dokladnie tak powstala wada StandART z 24/07 (siedem otwartych
-- gotowcow, piec bramek, cztery godziny).
--
-- Zatrzymanie kontenera USUWA okno zamiast wybierac mniejsze zlo. Jest to mozliwe, bo baza
-- stoi w INNYM kontenerze (`pg_n8n`) niz jedyny producent tych wierszy (`cm-agent`,
-- sales.py `_outreach`), wiec migracja dziala przy wylaczonym pisarzu.
--
-- STAN PRZED (odczyt 02/08): engagement_log 347 wierszy; X=170, LinkedIn=169, Other=9.
-- W 'Other' WYLACZNIE gotowce mailowe Sprzedawcy (rejected=7, proposed=1, sent=1).
-- Jedyny zywy 'proposed' to Klub Sportowy StandART z 24/07.

\encoding UTF8
\set ON_ERROR_STOP on

\echo '--- STAN PRZED ---'
SELECT COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log GROUP BY channel ORDER BY 2 DESC;

BEGIN;

-- BRAMKA NA LICZBIE. Przy zatrzymanym cm-agencie liczba MUSI wynosic dokladnie 9.
-- Kazda inna znaczy, ze albo kontener nie zostal zatrzymany, albo stan bazy jest inny
-- niz w odczycie - w obu przypadkach migracja ma sie NIE odbyc. RAISE przerywa transakcje,
-- wiec COMMIT ponizej nic nie zapisze.
DO $$
DECLARE n integer;
BEGIN
  SELECT COUNT(*) INTO n FROM engagement_log
   WHERE channel = 'Other' AND agent = 'AGS:sprzedaz'
     AND COALESCE(notes,'')   ILIKE '%gotowiec outreach%'
     AND COALESCE(content,'') ILIKE 'outreach email:%';
  RAISE NOTICE 'Wierszy do migracji: %', n;
  IF n <> 9 THEN
    RAISE EXCEPTION 'STOP: oczekiwano 9 wierszy, jest %. Czy cm-agent jest zatrzymany? MIGRACJA WYCOFANA, nic nie zapisano.', n;
  END IF;
END $$;

\echo '--- MIGRACJA: gotowce mailowe Other -> Email ---'
-- TRZY PASY, kazdy potrzebny:
--   agent   - odsiewa inne tory zapisu,
--   notes   - odsiewa wiersze Lacznika (RAPORT PRACY), ktore maja TEGO SAMEGO agenta,
--   content - odsiewa wiersze RAPORTU PRACY, ktore wstrzykuja SUROWY TEKST CZLOWIEKA
--             do `notes` (engagement._report_insert). Gdyby ktos napisal w raporcie slowa
--             "gotowiec outreach", dwa pierwsze pasy by go zlapaly. Gotowiec mailowy zawsze
--             zaczyna tresc od "outreach email:" (sales.py sklada f"outreach {channel}: {nazwa}").
UPDATE engagement_log
   SET channel = 'Email'
 WHERE channel = 'Other'
   AND agent = 'AGS:sprzedaz'
   AND COALESCE(notes,'')   ILIKE '%gotowiec outreach%'
   AND COALESCE(content,'') ILIKE 'outreach email:%'
RETURNING id, status, author_display, left(COALESCE(content,''), 40) AS poczatek;

COMMIT;

\echo '--- KONTROLA 1: co zostalo w Other (ma byc PUSTO) ---'
SELECT COALESCE(agent,'(brak)') AS agent, status,
       left(COALESCE(content,''), 45) AS poczatek, COUNT(*) AS n
  FROM engagement_log WHERE channel = 'Other'
 GROUP BY 1,2,3 ORDER BY 4 DESC;

\echo '--- KONTROLA 2: rozklad kanalow (Email ma byc 9) ---'
SELECT COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log GROUP BY channel ORDER BY 2 DESC;

\echo '--- KONTROLA 3 (NAJWAZNIEJSZA): ma zwrocic DOKLADNIE JEDEN wiersz ---'
-- To jest zapytanie, ktorego uzywa `_open_outreach_rows` po zmianie slownika.
--   ZERO  = uniewaznianie poprzednich gotowcow jest zerwane, przy nastepnym gotowcu
--           dla StandART powtorzy sie 24/07. ZATRZYMAJ SIE i zglos.
--   DWA+  = w oknie powstal dodatkowy gotowiec. Odpal:
--             docker exec cm-agent python -m app.outreach_cleanup dry
--           a po sprawdzeniu raportu:
--             docker exec cm-agent python -m app.outreach_cleanup apply
SELECT id, channel, created_at, author_display
  FROM engagement_log
 WHERE agent = 'AGS:sprzedaz' AND status = 'proposed'
   AND COALESCE(notes,'') ILIKE '%gotowiec outreach%'
   AND channel = 'Email'
 ORDER BY created_at;

-- ============================================================================
-- WYCOFANIE (gdyby trzeba bylo cofnac obraz cm-agenta do wersji sprzed zmiany slownika).
-- Odkomentuj i uruchom PRZY ZATRZYMANYM cm-agencie, tak samo jak migracje:
--
-- UPDATE engagement_log SET channel = 'Other'
--  WHERE channel = 'Email' AND agent = 'AGS:sprzedaz'
--    AND COALESCE(notes,'')   ILIKE '%gotowiec outreach%'
--    AND COALESCE(content,'') ILIKE 'outreach email:%';
--
-- UWAGA: cofnie TAKZE wiersze zapisane juz przez nowy kod. To jest poprawne - one rowniez
-- musza wrocic do kubelka, ktorego szuka stary slownik.
-- ============================================================================
