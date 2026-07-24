-- Sprzatanie po naprawie straznika meta-naglowka (24/07/2026).
--
-- Zgloszenie Tomasza (zrzut z okna edycji posta na X): opublikowany post zaczynal sie od
-- linii "# X Adaptation". Model opisywal, CO robi, a opis szedl do kolejki doslownie.
-- Kod naprawiony (compliance.strip_meta_header wpiety w channels.stage_variant - jedyne
-- miejsce zapisu do post_queue), ale wiersze WYPRODUKOWANE PRZED poprawka maja naglowek
-- dalej. Kanon "zalegle dane po naprawie": po naprawieniu kanalu wyjsciowego przejrzyj to,
-- co juz w nim lezy.
--
-- Wykonanie (SSH, Tomasz): najpierw PODGLAD, potem UPDATE.
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/meta_naglowki_kolejki_24072026.sql

\echo '--- 1) PODGLAD: wiersze kolejki z meta-naglowkiem (nic nie zmieniam) ---'
SELECT id, platform, status, left(content, 60) AS poczatek
  FROM post_queue
 WHERE status IN ('review', 'scheduled', 'queued', 'held')
   AND content ~ '^\s*#{1,6}\s+\S'
 ORDER BY id;

\echo '--- 2) PODGLAD: to samo w tekstach-matkach (content_items przed publikacja) ---'
SELECT id, status, left(canonical_body, 60) AS poczatek
  FROM content_items
 WHERE status IN ('planned', 'needs_research', 'researching', 'drafting', 'needs_approval', 'approved')
   AND canonical_body ~ '^\s*#{1,6}\s+\S'
 ORDER BY updated_at DESC;

\echo '--- 3) NAPRAWA kolejki: zdejmij PIERWSZA linie naglowka (tylko krotka, tylko meta) ---'
-- Warunek celowo waski: naglowek do 60 znakow zawierajacy slowo meta (adaptation/wersja/post...).
-- Hasztag nie pasuje, bo po '#' musi stac spacja.
UPDATE post_queue
   SET content = regexp_replace(content, '^\s*#{1,6}\s+[^\n]{0,60}\n+', '')
 WHERE status IN ('review', 'scheduled', 'queued', 'held')
   AND content ~* '^\s*#{1,6}\s+[^\n]{0,60}(adaptation|adaptacj|wersj|version|wariant|draft|post|tweet|thread|nitk|linkedin|twitter|\mx\M)[^\n]{0,60}\n';

\echo '--- 4) NAPRAWA tekstow-matek (te same reguly) ---'
UPDATE content_items
   SET canonical_body = regexp_replace(canonical_body, '^\s*#{1,6}\s+[^\n]{0,60}\n+', ''),
       updated_at = NOW()
 WHERE status IN ('planned', 'needs_research', 'researching', 'drafting', 'needs_approval', 'approved')
   AND canonical_body ~* '^\s*#{1,6}\s+[^\n]{0,60}(adaptation|adaptacj|wersj|version|wariant|draft|post|tweet|thread|nitk|linkedin|twitter|\mx\M)[^\n]{0,60}\n';

\echo '--- 5) KONTROLA: powinno byc zero ---'
SELECT COUNT(*) AS kolejka_z_naglowkiem
  FROM post_queue
 WHERE status IN ('review', 'scheduled', 'queued', 'held')
   AND content ~* '^\s*#{1,6}\s+[^\n]{0,60}(adaptation|adaptacj|wersj|version|wariant|draft|post|tweet|thread|nitk|linkedin|twitter|\mx\M)';

\echo '--- 6) INFORMACYJNIE: co juz OPUBLIKOWANE z naglowkiem (poprawa tylko recznie w aplikacji) ---'
SELECT id, platform, published_at, post_url, left(content, 60) AS poczatek
  FROM published_posts
 WHERE published_at > NOW() - interval '14 days'
   AND content ~ '^\s*#{1,6}\s+\S'
 ORDER BY published_at DESC;
