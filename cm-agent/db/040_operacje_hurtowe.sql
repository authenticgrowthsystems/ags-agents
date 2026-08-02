-- DDL 040 (02/08/2026): D-007 - operacja hurtowa zostawia slad czytelny dla DRUGIEGO agenta.
--
-- PROBLEM (zgloszenie Managera 29/07, szosta odslona AP-311): nie brakuje danych - dane sa
-- NIEODROZNIALNE. Wycofanie 21 materialow ustawilo im `status='rejected'`, czyli dokladnie to
-- samo, co odrzucenie przy przegladzie kart miesiac temu. Zapytanie "X + rejected + wiecej niz
-- jeden wiersz" zwraca 26 materialow, z czego z tamtej operacji jest 21.
--
-- Cytat Managera: "Ty wiesz, co wycofales, bo sam to robiles. CM patrzy na te sama baze i nie
-- widzi roznicy miedzy materialem wycofanym a odrzuconym przy przegladzie miesiac temu."
--
-- DLACZEGO REJESTR, A NIE SAMA KOLUMNA `status_source`: kolumna symetryczna do `slot_source`
-- powiedzialaby, JAKIEGO RODZAJU pisarz ustawil status ('karta', 'planner', 'skrypt').
-- To za malo. Drugi agent potrzebuje wyciac DOKLADNY ZBIOR jednym warunkiem ORAZ przeczytac,
-- CO to byla za operacja i na jakim warunku dzialala. Rejestr daje oba; kolumna tylko pierwsze
-- i to nieprecyzyjnie (dwie operacje tego samego rodzaju znowu byly by nieodroznialne).
--
-- Uruchomienie: psql -U n8n -d ags_crd -f 040_operacje_hurtowe.sql

\encoding UTF8
\set ON_ERROR_STOP on

-- 1) REJESTR OPERACJI. Identyfikator jest CZYTELNY DLA CZLOWIEKA i nadawany recznie
--    (np. 'wycofanie-serii-29072026') - to nie jest uuid, bo ma sie pojawiac w rozmowie
--    i w zapytaniach pisanych z pamieci.
CREATE TABLE IF NOT EXISTS bulk_operations (
  op_id        TEXT PRIMARY KEY,
  kiedy        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  kto          TEXT NOT NULL,               -- 'BE', 'AGS:sprzedaz', 'skrypt outreach_cleanup'
  opis         TEXT NOT NULL,               -- po ludzku: co i DLACZEGO
  warunek      TEXT,                        -- predykat SQL uzyty do wyboru wierszy
  wierszy      INTEGER,                     -- ile faktycznie dotknieto
  brand_id     VARCHAR(50) NOT NULL DEFAULT 'AGS'
);

COMMENT ON TABLE bulk_operations IS
  'Rejestr operacji HURTOWYCH (D-007). Kazda zmiana dotykajaca wielu wierszy naraz ma tu wiersz, a dotkniete wiersze niosa jego op_id. Bez tego druga agent widzi SKUTEK, ale nie widzi PRZYCZYNY ani ZAKRESU.';

-- 2) ZNACZNIK NA WIERSZACH. Puste = wiersz zmieniony normalnym trybem (karta, rozmowa, planer).
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS op_id TEXT REFERENCES bulk_operations(op_id);
ALTER TABLE post_queue    ADD COLUMN IF NOT EXISTS op_id TEXT REFERENCES bulk_operations(op_id);

CREATE INDEX IF NOT EXISTS idx_content_items_op ON content_items(op_id) WHERE op_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_post_queue_op    ON post_queue(op_id)    WHERE op_id IS NOT NULL;

COMMENT ON COLUMN content_items.op_id IS
  'Operacja hurtowa, ktora ostatnio dotknela tego wiersza (bulk_operations). NULL = zmiana normalnym trybem, przez czlowieka albo agenta.';
COMMENT ON COLUMN post_queue.op_id IS
  'Jak content_items.op_id.';

-- 3) RETROAKTYWNE OZNACZENIE WYCOFANIA Z 29/07 - ROBIONE TERAZ, BO PROTEZA WYGASA.
--    Rozroznikiem jest `updated_at::date` i sam wpis w dlugu mowi wprost, ze to proteza
--    dzialajaca "tylko dopoki pamietamy date operacji". Utrwalamy ja, POKI JESZCZE WIEMY -
--    za miesiac tej wiedzy juz nie bedzie i zbior przestanie byc odtwarzalny.
INSERT INTO bulk_operations (op_id, kiedy, kto, opis, warunek, wierszy)
SELECT 'wycofanie-serii-29072026', '2026-07-29 00:00:00+02', 'BE',
       'Wycofanie 21 materialow X bedacych seriami wieloczesciowymi. Decyzja Managera: X dostaje '
       'JEDEN wpis na material, koniec serii. Materialy czekaja, az CM wyprodukuje w nowej formie '
       '(lista: docs/cm/PRZEKAZANIE_do_CM_29072026_serie_do_przerobienia.md).',
       'content_items: brand X, status rejected, updated_at::date = 2026-07-29, >1 wiersz kolejki',
       NULL
 WHERE NOT EXISTS (SELECT 1 FROM bulk_operations WHERE op_id = 'wycofanie-serii-29072026');

\echo '--- ILE WIERSZY ZOSTANIE OZNACZONYCH (ma byc 21) ---'
SELECT COUNT(*) AS materialow FROM content_items
 WHERE status = 'rejected' AND updated_at::date = DATE '2026-07-29'
   AND 'x' = ANY(target_channels) AND op_id IS NULL;

UPDATE content_items SET op_id = 'wycofanie-serii-29072026'
 WHERE status = 'rejected' AND updated_at::date = DATE '2026-07-29'
   AND 'x' = ANY(target_channels) AND op_id IS NULL;

UPDATE bulk_operations SET wierszy = (SELECT COUNT(*) FROM content_items
                                       WHERE op_id = 'wycofanie-serii-29072026')
 WHERE op_id = 'wycofanie-serii-29072026';

\echo '--- KONTROLA: teraz da sie wyciac zbior JEDNYM warunkiem ---'
SELECT o.op_id, o.kiedy::date AS kiedy, o.wierszy,
       (SELECT COUNT(*) FROM content_items c WHERE c.op_id = o.op_id) AS policzone_teraz
  FROM bulk_operations o;

\echo '--- KONTROLA: ile rejected NIE nalezy do tej operacji (to sa stare odrzucenia) ---'
-- Przed DDL 040 te dwa zbiory byly nieodroznialne. Teraz roznica jest jednym warunkiem.
SELECT COUNT(*) AS stare_odrzucenia_bez_operacji
  FROM content_items WHERE status = 'rejected' AND op_id IS NULL;
