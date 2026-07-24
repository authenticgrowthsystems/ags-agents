-- Voice Bible, Sekcja 21: nazwa flagi zgodna z rzeczywistym zrodlem danych (24/07/2026).
--
-- Decyzja Managera (mini-brief #1.2, P2): fail-closed przed wykluczeniem z lejka liczy sie
-- z `engagement_log` per `contact_id`, a NIE z kolumny `contacts.dm_history` - takiej kolumny
-- nie ma i celowo jej nie dodajemy (duplikat historii rozjechalby sie z logiem w kilka dni).
-- Flaga w Voice Bible ma mowic prawde o zrodle: `dm_history_checked` ->
-- `engagement_log_checked_for_contact_id`.
--
-- Zmiana jest CHIRURGICZNA: podmieniamy sam token w tresci, nie przepisujemy Voice Bible.
-- Dzieki temu nie trzeba znac calego dokumentu, a bump wersji zostaje zgodny ze wzorcem
-- z db/017 i db/022 (UPDATE + version+1, NIGDY nowy wiersz - brand_config ma
-- UNIQUE (brand_id, config_key), AP-304).
--
-- Wykonanie (SSH, Tomasz):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/voice_bible_sekcja21_24072026.sql

\echo '--- 1) PODGLAD: czy stara nazwa flagi w ogole tam jest ---'
SELECT brand_id, version, LENGTH(config_value) AS znakow,
       (config_value LIKE '%dm_history_checked%')                    AS ma_stara_nazwe,
       (config_value LIKE '%engagement_log_checked_for_contact_id%') AS ma_nowa_nazwe
  FROM brand_config
 WHERE config_key = 'voice_bible'
 ORDER BY brand_id;

\echo '--- 2) PODMIANA (tylko tam, gdzie stara nazwa wystepuje) ---'
UPDATE brand_config
   SET config_value = replace(config_value, 'dm_history_checked',
                              'engagement_log_checked_for_contact_id'),
       version = version + 1,
       updated_by = 'be-24072026',
       updated_at = NOW()
 WHERE config_key = 'voice_bible'
   AND config_value LIKE '%dm_history_checked%';

\echo '--- 3) KONTROLA: nowa nazwa jest, starej nie ma ---'
SELECT brand_id, version,
       (config_value LIKE '%dm_history_checked%')                    AS zostala_stara,
       (config_value LIKE '%engagement_log_checked_for_contact_id%') AS jest_nowa,
       md5(config_value) AS odcisk
  FROM brand_config
 WHERE config_key = 'voice_bible'
 ORDER BY brand_id;

-- UWAGA: jesli krok 1 pokazal ma_stara_nazwe = false dla wszystkich marek, to znaczy, ze
-- Sekcja 21 jeszcze nie weszla do zywej Voice Bible - wtedy nowa nazwa flagi ma trafic do
-- wsadu v2.2 (deploy 26/07) po stronie Managera, a ten plik nic nie zmieni (i tak jest
-- bezpieczny do puszczenia - warunek WHERE nie trafi w zaden wiersz).
