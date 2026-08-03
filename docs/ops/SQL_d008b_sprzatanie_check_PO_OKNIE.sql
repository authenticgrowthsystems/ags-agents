-- D-008b: usuniecie starej wartosci 'dispatching' z ograniczenia CHECK na `content_items.status`.
--
-- ############################################################################
-- ##  NIE URUCHAMIAC W TYM SAMYM OKNIE, CO MIGRACJE DANYCH.                 ##
-- ##  Decyzja Tomasza z 03/08/2026: to jest OSOBNE OKNO, INNEGO DNIA.       ##
-- ############################################################################
--
-- DLACZEGO OSOBNO. Migracja danych i zwezenie slownika to dwie rozne operacje o roznym
-- profilu ryzyka. Migracja jest odwracalna jednym UPDATE-em. Zwezenie CHECK-a odbiera
-- systemowi mozliwosc powrotu: po nim stary obraz `cm-agent:prev-d008` NIE DA SIE juz
-- podniesc bezpiecznie, bo jego `worker.py:372` probowalby zapisac wartosc, ktorej baza
-- juz nie przyjmuje. Dopoki ta wartosc siedzi w ograniczeniu, droga odwrotu istnieje.
--
-- WARUNEK WEJSCIA (wszystkie naraz):
--   1) migracja danych wykonana i potwierdzona (zero wierszy w starej wartosci),
--   2) minal co najmniej jeden pelny cykl publikacji na nowym obrazie - czyli material
--      przeszedl approved -> handed_off -> published BEZ recznej pomocy,
--   3) nikt nie planuje juz cofac obrazu do `cm-agent:prev-d008`.
--
-- Uruchomienie:
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql

\encoding UTF8
\set ON_ERROR_STOP on

-- LIMIT CZASU BLOKADY (polecenie Tomasza 03/08). ALTER TABLE bierze ACCESS EXCLUSIVE i przy
-- zajetej tabeli ustawilby sie w kolejce, blokujac za soba KAZDE nastepne zapytanie - lacznie
-- z odczytami bota. Wolimy czysty blad po pieciu sekundach niz zakleszczona aplikacja.
SET lock_timeout = '5s';

\echo '--- BRAMKA: nie zwezaj slownika, dopoki ktokolwiek siedzi w starej wartosci ---'
DO $$
DECLARE n integer;
BEGIN
  SELECT COUNT(*) INTO n FROM content_items WHERE status = 'dispatching';
  IF n <> 0 THEN
    RAISE EXCEPTION 'STOP: % wierszy nadal ma stara wartosc. Najpierw migracja danych.', n;
  END IF;
END $$;

ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_status_check;
ALTER TABLE content_items ADD CONSTRAINT content_items_status_check
  CHECK (status IN ('proposed','planned','needs_research','researching','drafting','needs_approval',
                    'approved','handed_off','published','rejected','failed',
                    'draft','brief','archived'));

\echo '--- KONTROLA: ograniczenie zna juz TYLKO nowa wartosc ---'
SELECT pg_get_constraintdef(oid) AS ograniczenie
  FROM pg_constraint WHERE conname = 'content_items_status_check';

-- PO URUCHOMIENIU zaktualizuj takze pliki DDL w repozytorium - w kazdym z nich stoi dzis
-- komentarz wskazujacy na ten plik:
--   cm-agent/db/001_init.sql
--   cm-agent/db/003_brain_phase1.sql
--   cm-agent/db/010_notion_ssot.sql
--   cm-agent/db/042_status_handed_off.sql
-- i zamknij wpis D-008b w docs/ops/DLUG_TECHNICZNY.md.
