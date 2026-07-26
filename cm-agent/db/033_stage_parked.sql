-- DDL 033 (27/07/2026): etap 'parked' w lejku sprzedazy.
--
-- Decyzja Managera 27/07: dziewieciu prospektow bez nastepnego kroku i bez danych
-- kontaktowych parkujemy JAWNIE. Warunek Managera: "parkowanie ma byc ETAPEM, nie
-- usunieciem - dane zostaja, wiersze wypadaja z widoku i z licznikow". Piec z dziewieciu
-- to szkoly tanca, czyli rdzen ICP; wracamy do nich po Adamietzu, nie kasujemy.
--
-- Powod: lejek pokazywal dwanascie otwartych pozycji, gdy realnie gralismy trzema.
-- System, ktory zawyza wlasny lejek, twierdzi ze dziala. To dokladnie ta klasa
-- nieprawdy, przeciwko ktorej zbudowane jest pozycjonowanie AGS.
--
-- 'parked' NIE jest tym samym co 'lost': lost znaczy przegrane albo odrzucone,
-- parked znaczy "swiadomie odlozone, wroci". Rozroznienie jest potrzebne w raporcie -
-- zliczanie parkowanych jako przegranych falszowaloby skutecznosc.
--
-- Idempotentne: mozna puscic drugi raz bez skutkow.

-- ---------- 1) CHECK dopuszcza nowy etap ----------
DO $$
DECLARE
  con_name text;
BEGIN
  SELECT conname INTO con_name FROM pg_constraint
   WHERE conrelid = 'sales_pipeline'::regclass
     AND contype = 'c'
     AND pg_get_constraintdef(oid) ILIKE '%stage%'
   LIMIT 1;
  IF con_name IS NOT NULL AND
     (SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = con_name) NOT ILIKE '%parked%'
  THEN
    EXECUTE format('ALTER TABLE sales_pipeline DROP CONSTRAINT %I', con_name);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                  WHERE conrelid = 'sales_pipeline'::regclass
                    AND pg_get_constraintdef(oid) ILIKE '%parked%') THEN
    ALTER TABLE sales_pipeline ADD CONSTRAINT sales_pipeline_stage_check
      CHECK (stage IN ('prospect','qualified','proposal','negotiation','won','lost','parked'));
  END IF;
END $$;

-- ---------- 2) Indeks terminow pomija parkowane ----------
-- Straznik terminow (sales.followup_watch, 26/07) pyta o wiersze poza won/lost/parked.
-- Indeks czesciowy musi pasowac do predykatu zapytania, inaczej planer go nie uzyje.
DROP INDEX IF EXISTS idx_sales_pipeline_followup;
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_followup ON sales_pipeline(next_followup_at)
  WHERE stage NOT IN ('won','lost','parked');

-- ---------- 3) Kontrola ----------
SELECT 'check dopuszcza parked' AS co,
       (SELECT COUNT(*)::text FROM pg_constraint
         WHERE conrelid = 'sales_pipeline'::regclass
           AND pg_get_constraintdef(oid) ILIKE '%parked%') AS n
UNION ALL
SELECT 'indeks followup bez parked',
       (SELECT COUNT(*)::text FROM pg_indexes
         WHERE indexname = 'idx_sales_pipeline_followup'
           AND indexdef ILIKE '%parked%')
UNION ALL
SELECT 'wiersze wg etapu', string_agg(stage || '=' || n::text, ', ' ORDER BY stage)
  FROM (SELECT stage, COUNT(*) AS n FROM sales_pipeline WHERE brand_id='AGS' GROUP BY stage) s;

-- ---------- 4) Parkowanie dziewieciu (WYKONAC OSOBNO, po przegladzie kontroli wyzej) ----------
-- Swiadomie NIE robimy tego automatem w tym pliku: to zmiana zywych danych kampanii,
-- a AP-308 kaze najpierw pokazac, co sie stanie. Ponizsze najpierw jako SELECT.
--
-- PODGLAD (kto zostanie zaparkowany):
--   SELECT id, prospect_name, stage, created_at FROM sales_pipeline
--    WHERE brand_id='AGS' AND stage='prospect'
--      AND next_followup_at IS NULL
--      AND COALESCE(contact_email,'')='' AND COALESCE(contact_phone,'')=''
--    ORDER BY prospect_name;
--
-- WYKONANIE (dopiero gdy lista wyzej sie zgadza):
--   UPDATE sales_pipeline
--      SET stage='parked',
--          notes = COALESCE(notes,'') || E'\n27/07 zaparkowany (decyzja Managera): brak kroku
--   i brak kontaktu; wracamy po Adamietzu',
--          updated_at=NOW()
--    WHERE brand_id='AGS' AND stage='prospect'
--      AND next_followup_at IS NULL
--      AND COALESCE(contact_email,'')='' AND COALESCE(contact_phone,'')='';
