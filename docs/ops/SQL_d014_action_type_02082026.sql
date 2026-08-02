-- D-014 (02/08/2026): `action_type` gotowcow mailowych z 'other' na 'email'.
--
-- ============================================================================
-- PROCEDURA WEDLUG docs/ops/RUNBOOK_migracje.md. Przed startem:
--   gunzip -t ~/backups/<swieza kopia>.sql.gz && echo "KOPIA OK"    <- punkt 1 runbooka
-- Komenda ratunkowa (punkt 2 runbooka) ma byc PRZYGOTOWANA, zanim zatrzymasz kontener.
-- ============================================================================
--
-- CZYM SIE ROZNI OD D-009: tam wartosc byla KLUCZEM DOPASOWANIA i rozjazd kodu z danymi
-- oznaczalby cicha wade. Tu `action_type` NIKOGO NIE FILTRUJE - sprawdzone odczytem:
--   * jedyne zapytanie z `action_type` (crm.py:180,183, liczenie DM-ow) jest zawezone
--     do `e.contact_id = c.id`, a WSZYSTKIE dziewiec gotowcow ma `contact_id` PUSTE;
--   * w calej bazie ZERO wierszy pasuje do `action_type ILIKE '%dm%'`.
-- Dlatego zatrzymywanie cm-agenta NIE JEST tu konieczne: rozjazd kodu z danymi przez
-- kilka minut nie ma konsumenta, ktory by go zauwazyl. Mowie to wprost, zamiast powtarzac
-- ciezsza procedure dla powagi.
--
-- CO NAPRAWIAMY: `sales.py` wpisywal `action_type` LITERALEM 'other' dla kazdego kanalu,
-- podczas gdy kanal szedl ze slownika. Dwa zrodla dla jednej pary rozjechaly sie dwukrotnie
-- (D-009 na kanale, D-014 na typie). Od 02/08 para siedzi w jednym slowniku `_ENG_KANALY`.
--
-- CZEGO NIE RUSZAMY: `action_type='other'` w torze komentarzy i DM-ow (conversation.py,
-- 217 wierszy) jest SWIADOMY - komentarz przy INTAKE-UX z 21/07 mowi to wprost.
-- D-014 dotyczy WYLACZNIE dziewieciu wierszy Agenta Sprzedazy.
--
-- Uruchomienie (SSH):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_d014_action_type_02082026.sql

\encoding UTF8
\set ON_ERROR_STOP on

\echo '--- STAN PRZED ---'
SELECT action_type, COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log WHERE agent = 'AGS:sprzedaz'
 GROUP BY 1,2 ORDER BY 3 DESC;

BEGIN;

-- Bramka na liczbie (punkt 4 runbooka): przy 9 wierszach idziemy dalej, przy kazdej innej
-- liczbie transakcja sie wycofuje i nic nie zostaje zapisane.
DO $$
DECLARE n integer;
BEGIN
  SELECT COUNT(*) INTO n FROM engagement_log
   WHERE action_type = 'other' AND channel = 'Email' AND agent = 'AGS:sprzedaz'
     AND COALESCE(notes,'')   ILIKE '%gotowiec outreach%'
     AND COALESCE(content,'') ILIKE 'outreach email:%';
  RAISE NOTICE 'Wierszy do migracji: %', n;
  IF n <> 9 THEN
    RAISE EXCEPTION 'STOP: oczekiwano 9, jest %. MIGRACJA WYCOFANA, nic nie zapisano.', n;
  END IF;
END $$;

\echo '--- MIGRACJA: action_type other -> email (tylko gotowce mailowe) ---'
-- CZTERY pasy. Trzy jak przy D-009 (agent + notes + content) plus `channel='Email'`,
-- ktory po D-009 jednoznacznie wskazuje maile. Bez niego warunek zlapalby przyszle
-- gotowce DM, ktore maja miec 'linkedin_dm'/'x_dm', a nie 'email'.
UPDATE engagement_log
   SET action_type = 'email'
 WHERE action_type = 'other'
   AND channel = 'Email'
   AND agent = 'AGS:sprzedaz'
   AND COALESCE(notes,'')   ILIKE '%gotowiec outreach%'
   AND COALESCE(content,'') ILIKE 'outreach email:%'
RETURNING id, action_type, channel, status, author_display;

COMMIT;

\echo '--- KONTROLA 1: gotowce sprzedazy wg typu (ma byc email=9, other=0) ---'
SELECT action_type, COALESCE(channel,'(null)') AS kanal, COUNT(*) AS n
  FROM engagement_log
 WHERE agent = 'AGS:sprzedaz' AND COALESCE(notes,'') ILIKE '%gotowiec outreach%'
 GROUP BY 1,2 ORDER BY 3 DESC;

\echo '--- KONTROLA 2: tor komentarzy NIETKNIETY (other ma zostac 217) ---'
-- Jesli ta liczba spadnie, migracja wyszla poza swoj zakres i ruszyla decyzje z INTAKE-UX.
SELECT COUNT(*) AS other_poza_sprzedaza
  FROM engagement_log
 WHERE action_type = 'other' AND agent <> 'AGS:sprzedaz';

\echo '--- KONTROLA 3: para typ-kanal spojna dla wszystkich gotowcow ---'
-- Ma byc PUSTO. Kazdy wiersz tutaj to para, ktora sie rozjechala.
SELECT id, action_type, channel, author_display
  FROM engagement_log
 WHERE agent = 'AGS:sprzedaz' AND COALESCE(notes,'') ILIKE '%gotowiec outreach%'
   AND NOT ((action_type = 'email'       AND channel = 'Email')
         OR (action_type = 'linkedin_dm' AND channel = 'LinkedIn')
         OR (action_type = 'x_dm'        AND channel = 'X'));

-- ============================================================================
-- WYCOFANIE (zakomentowane):
-- UPDATE engagement_log SET action_type = 'other'
--  WHERE action_type = 'email' AND channel = 'Email' AND agent = 'AGS:sprzedaz'
--    AND COALESCE(notes,'') ILIKE '%gotowiec outreach%';
-- ============================================================================
