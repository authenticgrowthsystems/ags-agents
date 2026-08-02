-- DDL 041 (02/08/2026): pole formatu w kolejce (polecenie Managera, odblokowane 02/08).
--
-- KONTEKST: 29/07 Manager zdecydowal "X dostaje JEDEN wpis na material, koniec serii".
-- Dane wyczyszczono tego samego dnia (21 materialow wycofanych), ale KOD zostal - `channels.py`
-- nadal rozbijal wariant X dluzszy niz 600 znakow na serie. Kolejka byla pusta, wiec nikt tego
-- nie zauwazyl. DDL 041 i towarzyszaca zmiana kodu domykaja te decyzje.
--
-- `format` rozroznia dwa ksztalty publikacji, o ktorych mowil Manager:
--   'post'    - zwykly wpis, podlega limitowi znakow kanalu,
--   'article' - dlugi material (LinkedIn Article, niedziela wg kanonu 19/07), inny limit.
--
-- Uruchomienie: psql -U n8n -d ags_crd -f 041_format_i_limit.sql  (idempotentne)

\encoding UTF8
\set ON_ERROR_STOP on

ALTER TABLE post_queue ADD COLUMN IF NOT EXISTS format TEXT NOT NULL DEFAULT 'post';

DO $$
BEGIN
  ALTER TABLE post_queue DROP CONSTRAINT IF EXISTS post_queue_format_check;
  ALTER TABLE post_queue ADD CONSTRAINT post_queue_format_check
    CHECK (format IN ('post', 'article'));
END $$;

COMMENT ON COLUMN post_queue.format IS
  'Ksztalt publikacji: post (limit znakow kanalu) albo article (LinkedIn Article, niedziela wg kanonu 19/07). Dwie wartosci, swiadomie - trzecia oznaczalaby, ze wrocila seria, ktora Manager zniosl 29/07.';

\echo '--- KONTROLA: rozklad formatow (wszystko ma byc post) ---'
SELECT format, COUNT(*) AS n FROM post_queue GROUP BY format ORDER BY 2 DESC;
