-- D-008 (03/08/2026): migracja wartosci `content_items.status`: 'dispatching' -> 'handed_off'.
--
-- ============================================================================
-- URUCHOMIC WYLACZNIE PRZY ZATRZYMANYCH PISARZACH. Pelna procedura z komendami do wklejenia:
--   docs/ops/OKNO_d008_03082026.md   <- PRZECZYTAJ TO PIERWSZE, nie improwizuj kolejnosci
--
-- PISARZY DO `content_items` SA TRZEJ, nie jeden (ustalenie 03/08, dwa z nich umknely briefowi):
--   1) kontener `cm-agent`            - JEDYNY, ktory pisze migrowana wartosc (worker.py:372)
--   2) n8n "AGS Scheduler v1"         - cron co minute, `UPDATE content_items ... WHERE ci.status=...`
--   3) n8n "AGS HITL Handler v1.0"    - bot Telegram, wezel `Cm Resolve Gate`, z pominieciem cm-agenta
--
-- Nr 3 NIE musi byc gaszony: jego predykat to `WHERE id=... AND status='needs_approval'`, wiec
-- nie potrafi ani utworzyc, ani skonsumowac migrowanej wartosci. Nr 1 i 2 - TAK, oba stoja.
-- ============================================================================
--
-- BRAMKA NA LICZBIE WIERSZY jest tu PARAMETREM, nie liczba wpisana z gory - i to jest celowe.
-- Liczbe odczytuje sie DOPIERO gdy pisarze stoja (inaczej mierzy sie ruchomy cel):
--
--   docker exec -i pg_n8n psql -U n8n -d ags_crd -c \
--     "SELECT COUNT(*) FROM content_items WHERE status='dispatching';"
--
-- a potem podaje ja tutaj:
--
--   docker exec -i pg_n8n psql -U n8n -d ags_crd -v oczekiwana=<LICZBA> \
--     < ~/ags-agents/docs/ops/SQL_d008_handed_off_03082026.sql
--
-- WYMAGANE WCZESNIEJ: `cm-agent/db/042_status_handed_off.sql` (ograniczenie CHECK musi juz znac
-- OBIE wartosci, inaczej UPDATE nie ma jak przebiec).

\encoding UTF8
\set ON_ERROR_STOP on

\if :{?oczekiwana}
\else
\echo 'STOP: brak parametru. Uruchom z  -v oczekiwana=<liczba wierszy odczytana przy stojacych pisarzach>'
\quit 1
\endif

\echo '--- STAN PRZED: rozklad statusow materialow ---'
SELECT status, COUNT(*) AS n FROM content_items GROUP BY status ORDER BY 2 DESC;

BEGIN;

-- BRAMKA. Kazda liczba inna niz odczytana chwile temu znaczy, ze albo ktorys pisarz nadal
-- pracuje, albo stan bazy jest inny niz w odczycie. W obu przypadkach migracja ma sie NIE odbyc.
-- RAISE przerywa transakcje, wiec COMMIT ponizej nic nie zapisze.
--
-- RUNBOOK PUNKT 9: to jest najbardziej prawdopodobny punkt przerwania calej sekwencji. Jesli
-- lancuch `&&` pekl tutaj, PIERWSZA czynnoscia jest podniesienie kontenera i wlaczenie workflow
-- (komendy ratunkowe gotowe w OKNO_d008_03082026.md), a diagnoza DOPIERO potem. Baza jest
-- w tym momencie nietknieta.
DO $$
DECLARE n integer;
BEGIN
  SELECT COUNT(*) INTO n FROM content_items WHERE status = 'dispatching';
  RAISE NOTICE 'Wierszy do migracji: %', n;
  IF n <> :oczekiwana THEN
    RAISE EXCEPTION 'STOP: oczekiwano % wierszy, jest %. Czy cm-agent stoi i czy Scheduler jest wylaczony? MIGRACJA WYCOFANA, nic nie zapisano.', :oczekiwana, n;
  END IF;
END $$;

\echo '--- MIGRACJA: content_items.dispatching -> handed_off ---'
-- JEDEN pas wystarcza i jest to swiadome: `status` to slownik zamkniety ograniczeniem CHECK,
-- a nie tekst pisany przez czlowieka. Nie ma tu ryzyka AP-313 (polskie znaki) ani ryzyka
-- zlapania nie tego wiersza - w przeciwienstwie do D-009, gdzie trzeba bylo trzech pasow.
--
-- `updated_at` NIE jest ruszane celowo: to pole niesie informacje "od kiedy material czeka",
-- ktora czyta alarm zwisu (`worker._dispatch_timeout_alert`). Podbicie go skasowaloby wiek
-- siedmiu materialow i przez dwie godziny zadne z nich nie mogloby zaalarmowac.
UPDATE content_items
   SET status = 'handed_off'
 WHERE status = 'dispatching'
RETURNING id, brand_id, left(master_theme, 55) AS temat, updated_at;

COMMIT;

\echo '--- KONTROLA 1: zero wierszy ze stara wartoscia (INNYM mechanizmem niz migracja) ---'
-- RUNBOOK PUNKT 6: zapytanie kontrolne napisane tym samym wzorcem, co migracja, potwierdza
-- wylacznie samo siebie (dowod: AP-313). Migracja pytala o rownosc `status = 'dispatching'`.
-- Kontrola pyta INACZEJ - o wzorzec tekstowy, ktory zlapie takze warianty typu 'Dispatching'
-- czy 'dispatching ' ze spacja, ktorych rownosc by przepuscila.
-- PROG JAWNY: ma byc DOKLADNIE ZERO wierszy. Jedna to za duzo - ZATRZYMAJ SIE i zglos.
SELECT COUNT(*) AS zostalo_starej_wartosci
  FROM content_items WHERE status ILIKE '%dispatch%';

\echo '--- KONTROLA 2: liczba w nowej wartosci ma sie ZGADZAC z :oczekiwana ---'
SELECT COUNT(*) AS w_handed_off FROM content_items WHERE status = 'handed_off';

\echo '--- KONTROLA 3: rozklad statusow PO migracji ---'
SELECT status, COUNT(*) AS n FROM content_items GROUP BY status ORDER BY 2 DESC;

\echo '--- KONTROLA 4: post_queue NIETKNIETE (dispatching ma tu ZOSTAC) ---'
-- Ta kontrola pilnuje rzeczy odwrotnej niz reszta pliku: gdyby ktos zrobil podmiane "po calej
-- bazie", ta liczba spadlaby do zera i zerwaloby to dopasowanie w kolejce publikacji.
SELECT status, COUNT(*) AS n FROM post_queue GROUP BY status ORDER BY 2 DESC;

-- ============================================================================
-- WYCOFANIE. Uruchomic PRZY ZATRZYMANYCH PISARZACH, tak samo jak migracje, i TYLKO razem
-- z cofnieciem obrazu (`cm-agent:prev-d008`) oraz cofnieciem wezlow n8n do 'dispatching'.
-- Samo cofniecie danych bez cofniecia kodu daje dokladnie te ciche wade, ktorej unikamy.
--
-- UPDATE content_items SET status = 'dispatching' WHERE status = 'handed_off';
--
-- UWAGA: cofnie TAKZE wiersze zapisane juz przez NOWY kod - i to jest poprawne, bo one rowniez
-- musza wrocic do wartosci, ktorej szuka stary kod i stary wezel Schedulera.
-- ============================================================================
