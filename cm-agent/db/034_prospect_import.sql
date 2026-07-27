-- DDL 034 (27/07/2026): nisza i wynik kwalifikacji w lejku - ogniwo 1 maszynki prospektowej.
--
-- Kontekst: kampania wychodzi poza szkoly tanca na cztery rodzaje nisz. Lancuch od niszy
-- do klienta ma osiem ogniw, mielismy cztery. Import listy jest pierwszy, bo definiuje
-- KONTRAKT, w ktory wpinaja sie dwa pozostale: zbieracz z rejestrow musi miec gdzie odlozyc
-- wynik, wysylka musi miec skad wziac adresatow.
--
-- Dwie kolumny, obie potrzebne od pierwszego importu:
--   niche      - ktora rodzina nisz; bez tego 161 szkol tanca i 200 gabinetow to jedna
--                nierozroznialna kupa i nie da sie obudzic "czterdziestu z fizjoterapii".
--   lead_score - deterministyczna kwalifikacja KONTAKTOWALNOSCI (nie jakosci firmy).
--                Odpowiada na jedno pytanie: czy da sie do nich napisac i czy jest do kogo.
--                Ocena wartosci prospekta to robota czlowieka i researchu, nie arytmetyki.
--
-- Idempotentne: ADD COLUMN IF NOT EXISTS.

ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS niche      TEXT;
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS lead_score INTEGER;

COMMENT ON COLUMN sales_pipeline.niche IS
    'Rodzina niszy (sport_dzieci, zdrowie_uroda, uslugi_grafik, wzrost_firmy, taniec). Sluzy do budzenia partiami: "obudz 40 najlepszych z niszy X".';
COMMENT ON COLUMN sales_pipeline.lead_score IS
    'Kwalifikacja KONTAKTOWALNOSCI 0-100 z importu (mail/telefon/www/osoba minus znane problemy). NIE jest ocena wartosci prospekta.';

-- Budzenie partiami czyta po (marka, nisza, etap) i sortuje po wyniku malejaco.
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_niche
    ON sales_pipeline (brand_id, niche, stage, lead_score DESC);

-- ---------- kontrola ----------
SELECT 'kolumna niche' AS co,
       (SELECT COUNT(*)::text FROM information_schema.columns
         WHERE table_name='sales_pipeline' AND column_name='niche') AS n
UNION ALL
SELECT 'kolumna lead_score',
       (SELECT COUNT(*)::text FROM information_schema.columns
         WHERE table_name='sales_pipeline' AND column_name='lead_score')
UNION ALL
SELECT 'indeks niche',
       (SELECT COUNT(*)::text FROM pg_indexes WHERE indexname='idx_sales_pipeline_niche')
UNION ALL
SELECT 'wiersze wg niszy',
       COALESCE(string_agg(COALESCE(niche,'(brak)') || '=' || n::text, ', ' ORDER BY niche), '(pusto)')
  FROM (SELECT niche, COUNT(*) AS n FROM sales_pipeline WHERE brand_id='AGS' GROUP BY niche) s;
