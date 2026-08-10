-- AP-315 (10/08/2026): wycofanie publikacji #344 - notatki recenzyjnej CM, ktora wyszla
-- na LinkedIna jako post i zyla tam szesc dni pod nazwiskiem Tomasza (87 wyswietlen).
--
-- ============================================================================
-- CO SIE JUZ STALO POZA BAZA: Tomasz zdjal post recznie z LinkedIna 10/08.
-- Ten plik doprowadza BAZE do zgodnosci z tym faktem. Kolejnosc jest wazna:
-- najpierw znika post ze swiata, potem z ksiegi. Odwrotnie zostawiloby material,
-- ktory "wraca do produkcji", podczas gdy stara wersja nadal wisi publicznie.
--
-- TRZY TABELE, BO PUBLIKACJA ZOSTAWIA SLAD W TRZECH MIEJSCACH:
--   1) published_posts - KSIEGA. Dopoki wiersz tam stoi, post liczy sie jako opublikowany
--      w raportach i w `stan_gry`, a `content_memory.dup_check` porownuje z nim nowe
--      materialy - czyli poprawiona wersja tego samego tematu zostalaby oflagowana
--      jako duplikat samej siebie.
--   2) post_queue #344 - WIERSZ KOLEJKI. Zostaje wycofany na 'rejected', bo `stage_variant`
--      przy ponownym pisaniu robi INSERT nowego wiersza, a nie UPDATE starego. Bez tego
--      material mialby dwa wiersze i drugi z nich moglby wyjsc.
--   3) content_items - MATERIAL. Wraca do 'drafting', wiec CM napisze tekst od nowa
--      na tym samym temacie. `scheduled_for` na NULL, zeby dostal swiezy slot.
--
-- WYMAGANE WCZESNIEJ (RUNBOOK zasada 1 - kopia, ktora DA SIE rozpakowac):
--   mkdir -p ~/backups && docker exec pg_n8n pg_dump -U n8n -d ags_crd \
--     | gzip > ~/backups/ags_crd_ap315_$(date +%Y%m%d_%H%M).sql.gz \
--     && gunzip -t ~/backups/ags_crd_ap315_*.sql.gz && echo 'KOPIA OK'
--
-- URUCHOMIENIE:
--   docker exec -i pg_n8n psql -U n8n -d ags_crd \
--     < ~/ags-agents/docs/ops/SQL_wycofanie_344_10082026.sql
--
-- PISARZY NIE TRZEBA GASIC. To nie jest migracja klasy wierszy, tylko jeden material,
-- ktory jest juz w stanie terminalnym ('published') - zaden pisarz go nie dotyka.
-- ============================================================================

\encoding UTF8
\set ON_ERROR_STOP on

\echo '--- STAN PRZED: wiersz kolejki, material i wpis w ksiedze ---'
SELECT pq.id AS kolejka, pq.status AS wiersz, ci.id AS material, ci.status AS stan_materialu,
       left(ci.master_theme, 60) AS temat, left(pq.content, 90) AS poczatek_tresci
  FROM post_queue pq JOIN content_items ci ON ci.id = pq.content_item_id
 WHERE pq.id = 344;

SELECT id, platform, post_url, published_at FROM published_posts
 WHERE post_url = 'https://www.linkedin.com/feed/update/urn:li:share:7490406444618387458';

BEGIN;

-- BRAMKA. Sprawdza TOZSAMOSC, nie tylko liczbe wierszy - bo numer 344 sam w sobie niczego
-- nie dowodzi (numery kolejki sa ponownie uzywalne w rozmowie, a nie w bazie, ale pomylka
-- przy przepisywaniu numeru z czatu jest realna). Warunek trzeci pyta o TRESC: ten wiersz
-- ma zawierac frazy, przez ktore w ogole go wycofujemy. Jesli ich tam nie ma - to nie jest
-- ten wiersz i nic sie nie dzieje.
--
-- KAZDY WARUNEK PADA ZAMKNIETY (AP-314): puste zapytanie daje NULL, a NULL w `IF` to NIE-prawda,
-- czyli cichy przelot. Dlatego liczby ida przez COUNT(*) (nigdy NULL), a nie przez SELECT wartosci.
--
-- UWAGA dla nastepnego czytajacego: tutaj `DO $$` jest bezpieczne, bo w srodku sa WYLACZNIE
-- literaly. Gotcha z D-008 dotyczy zmiennych psql (`:nazwa`) - tych w bloku dolarowym psql
-- NIE podstawia i blok wywala sie skladniowo, zanim cokolwiek sprawdzi. Nie przerabiaj tego
-- pliku na parametry bez przeniesienia liczby przez tabele tymczasowa.
DO $$
DECLARE n_kolejka integer; n_ksiega integer; n_frazy integer;
BEGIN
  SELECT COUNT(*) INTO n_kolejka FROM post_queue WHERE id = 344 AND status = 'published';
  SELECT COUNT(*) INTO n_ksiega FROM published_posts
   WHERE post_url = 'https://www.linkedin.com/feed/update/urn:li:share:7490406444618387458';
  SELECT COUNT(*) INTO n_frazy FROM post_queue
   WHERE id = 344
     AND content ILIKE '%reviewed%' AND content ILIKE '%Voice Bible%'
     AND content ILIKE '%flag%';

  RAISE NOTICE 'kolejka=% ksiega=% frazy=%', n_kolejka, n_ksiega, n_frazy;

  IF n_kolejka <> 1 THEN
    RAISE EXCEPTION 'STOP: wiersz 344 nie jest opublikowanym wierszem kolejki (znaleziono %). NIC NIE ZMIENIONO.', n_kolejka;
  END IF;
  IF n_ksiega <> 1 THEN
    RAISE EXCEPTION 'STOP: w ksiedze nie ma DOKLADNIE jednego wpisu o tym URL (znaleziono %). NIC NIE ZMIENIONO.', n_ksiega;
  END IF;
  IF n_frazy <> 1 THEN
    RAISE EXCEPTION 'STOP: tresc wiersza 344 nie zawiera fraz, przez ktore go wycofujemy. To nie ten wiersz. NIC NIE ZMIENIONO.';
  END IF;
END $$;

\echo '--- 1/3 KSIEGA: wpis publikacji znika (post zdjety z LinkedIna 10/08) ---'
DELETE FROM published_posts
 WHERE post_url = 'https://www.linkedin.com/feed/update/urn:li:share:7490406444618387458'
RETURNING id, platform, published_at, left(content, 60) AS poczatek;

\echo '--- 2/3 KOLEJKA: wiersz #344 wycofany ---'
-- 'rejected' to wartosc uzywana przy sprzataniu wierszy wycofanych (dowod 19-20/07), a nie
-- nowy stan wymyslony na te okazje. `scheduled_for` zostaje - niesie informacje, kiedy to wyszlo.
UPDATE post_queue SET status = 'rejected' WHERE id = 344
RETURNING id, status, platform, scheduled_for;

\echo '--- 3/3 MATERIAL: wraca do produkcji, tekst pisany od nowa ---'
-- 'drafting', nie 'needs_approval': tekst jest do WYRZUCENIA, nie do poprawienia. Temat,
-- grafika i pozycja w planie zostaja - to one byly dobre.
UPDATE content_items SET status = 'drafting', scheduled_for = NULL, updated_at = NOW()
 WHERE id = (SELECT content_item_id FROM post_queue WHERE id = 344)
RETURNING id, status, left(master_theme, 60) AS temat;

COMMIT;

\echo '--- KONTROLA 1: ksiega nie zna juz tego posta (pytane INNYM wzorcem niz kasowanie) ---'
-- Kasowanie pytalo o rownosc pelnego URL. Kontrola pyta o fragment URN, wiec zlapie takze
-- wpis z innym prefiksem czy ze spacja na koncu, ktorego rownosc by przepuscila (lekcja AP-313).
-- PROG JAWNY: ma byc DOKLADNIE ZERO.
SELECT COUNT(*) AS zostalo_w_ksiedze FROM published_posts WHERE post_url ILIKE '%7490406444618387458%';

\echo '--- KONTROLA 2: material stoi w drafting i nie ma slotu ---'
SELECT ci.id, ci.status, ci.scheduled_for, left(ci.master_theme, 60) AS temat
  FROM content_items ci
 WHERE ci.id = (SELECT content_item_id FROM post_queue WHERE id = 344);

\echo '--- KONTROLA 3: material NIE MA zadnego zywego wiersza kolejki ---'
-- Gdyby zostal wiersz w 'review'/'scheduled', nowa produkcja dolozylaby drugi i material
-- moglby wyjsc dwa razy. Ma byc ZERO.
SELECT COUNT(*) AS zywe_wiersze FROM post_queue
 WHERE content_item_id = (SELECT content_item_id FROM post_queue WHERE id = 344)
   AND status IN ('review', 'scheduled', 'queued', 'held', 'dispatching');

-- ============================================================================
-- WYCOFANIE TEGO WYCOFANIA nie istnieje jako skrypt i to jest swiadome: wpis w ksiedze
-- zostal skasowany, a nie oznaczony. Droga powrotu prowadzi przez kopie z naglowka pliku.
-- Jesli kiedykolwiek bedziemy wycofywac publikacje regularnie, wtedy - i dopiero wtedy -
-- ksiega dostanie kolumne stanu zamiast kasowania wierszy.
-- ============================================================================
