-- OPERACJA JEDNORAZOWA (01/08/2026), po DDL 038.
--   1. Uzupelnienie wiersza Grupy Chwalinski danymi od Tomasza.
--   2. Nadanie etykiety `marka_docelowa='TNM'` aktywnemu lejkowi.
--
-- Uruchomienie (SSH):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_marka_i_chwalinski_01082026.sql

\encoding UTF8

-- ============================================================================
-- 1. GRUPA CHWALINSKI: dane od Tomasza
-- ============================================================================
-- Wiersz zalozylem wczesniej z etapem 'proposal', wywnioskowanym z zawartosci folderu
-- (dokument w 02_wyslane, w 03_spotkania sama ankieta bez transkrypcji). Tomasz rozstrzygnal:
-- 'qualified'. Jego dane maja pierwszenstwo nad moim wnioskiem z plikow.
--
-- AP-313: wzorzec to 'Chwali', NIE 'Chwalin'. W slowie "Chwaliński" nie ma zwyklego `n`
-- (C-h-w-a-l-i-ń-s-k-i), wiec '%Chwalin%' nie trafia NIGDY.
\echo '--- 1. Grupa Chwalinski: etap qualified + dane kontaktowe ---'
UPDATE sales_pipeline
   SET stage          = 'qualified',
       niche          = 'motoryzacja dealer',
       contact_person = 'Jan Szuta',
       contact_email  = 'jszuta@chwalinski.com.pl',
       contact_phone  = '694 147 748',
       prospect_url   = 'https://grupachwalinski.pl',
       updated_at     = NOW()
 WHERE prospect_name ILIKE '%Chwali%'
RETURNING prospect_name, stage, niche, contact_person, contact_email, contact_phone, katalog;

-- ============================================================================
-- 2. ETYKIETA MARKI dla aktywnego lejka
-- ============================================================================
-- Zbior = wszystko, co NIE jest zaparkowane. Odczyt 01/08 potwierdzil, ze to DOKLADNIE
-- 24 wiersze: 19 prospektow (w tym Dance Company La Cultura), 3 qualified (adamietz.pl,
-- StandART, Wroclawska Stepownia), 1 proposal (Chwalinski, po pkt 1 juz qualified)
-- i 1 lost (Scorpion Dance Team).
--
-- UWAGA, ODCHYLENIE OD LISTY TOMASZA, ZGLOSZONE JAWNIE: Tomasz wymienil "19 szkol + StandART
-- + Stepownia + La Cultura + Adamietz + Chwalinski". La Cultura JEST JUZ wewnatrz tych 19,
-- a wiersz, ktorego nie wymienil, to **Scorpion Dance Team** ze stanem 'lost'. To rowniez
-- polska szkola tanca, wiec regula "polski rynek = TNM" obejmuje go tak samo. Jesli ma zostac
-- bez etykiety, dopisz `AND stage <> 'lost'` do warunku ponizej PRZED uruchomieniem.
\echo '--- 2. marka_docelowa = TNM dla aktywnego lejka ---'
UPDATE sales_pipeline
   SET marka_docelowa = 'TNM', updated_at = NOW()
 WHERE stage <> 'parked' AND marka_docelowa IS DISTINCT FROM 'TNM'
RETURNING prospect_name, stage, marka_docelowa;

\echo '--- KONTROLA: rozklad etykiety ---'
SELECT COALESCE(marka_docelowa, '(brak)') AS marka, stage, COUNT(*) AS n
  FROM sales_pipeline GROUP BY 1, 2 ORDER BY 1, 2;

\echo '--- KONTROLA: brand_id ma pozostac NIETKNIETY (ma byc AGS: 134) ---'
-- Gdyby tu pojawilo sie cokolwiek innego niz AGS, znaczy to, ze ktos przepiał filtr
-- zamiast etykiety - i lejek wlasnie zniknal sprzedawcy z oczu.
SELECT brand_id, COUNT(*) AS n FROM sales_pipeline GROUP BY brand_id;

\echo '--- KONTROLA: cztery katalogi nadal na miejscu ---'
SELECT prospect_name, stage, katalog, marka_docelowa
  FROM sales_pipeline WHERE katalog IS NOT NULL ORDER BY prospect_name;
