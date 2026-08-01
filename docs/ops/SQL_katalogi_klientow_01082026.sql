-- OPERACJA JEDNORAZOWA (01/08/2026): powiazanie istniejacych katalogow z lejkiem.
-- NIE jest to migracja - DDL 037 dodaje kolumne, a ten plik wypelnia ja dla czterech klientow,
-- ktorzy mieli katalogi ZANIM kolumna powstala. Nowi beda dostawac katalog przez zapisz_tekst.
--
-- Uruchomienie (SSH, po DDL 037):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/docs/ops/SQL_katalogi_klientow_01082026.sql
--
-- BEZPIECZENSTWO: kazdy UPDATE ma `AND katalog IS NULL`, wiec ponowne uruchomienie NICZEGO
-- nie nadpisze. To ta sama regula, ktora pilnuje kod: katalog ustala sie raz i nigdy nie zmienia.
-- Kazde polecenie ma RETURNING, wiec widzisz dokladnie, co sie stalo, zamiast samego "UPDATE 1".

\encoding UTF8

-- DOPASOWANIA SA ASCII-OWE (bez polskich znakow w warunkach WHERE) i to jest SWIADOME.
-- Nazwy w bazie maja diakrytyki ("Wrocławska Stepownia"), ale ten plik idzie na serwer przez
-- `docker exec -i psql < plik`. Gdyby cokolwiek po drodze przekrecilo kodowanie, porownanie
-- do literalu z ogonkiem trafiloby w ZERO wierszy - i to po cichu, bo UPDATE bez trafien
-- nie jest bledem. Fragment ASCII jest jednoznaczny: sonda 01/08 potwierdzila, ze kazdy
-- z trzech wzorcow ponizej pasuje do DOKLADNIE JEDNEGO wiersza w lejku.

\echo '--- 1. Klub Sportowy StandART -> Klienci\\StandART ---'
UPDATE sales_pipeline SET katalog = 'Klienci\StandART', updated_at = NOW()
 WHERE prospect_name ILIKE '%StandART%' AND katalog IS NULL
RETURNING prospect_name, stage, katalog;

\echo '--- 2. Wroclawska Stepownia -> Klienci\\Stepownia_Dudzik ---'
-- Nazwa katalogu niesie nazwisko wlasciciela (Dudzik), ktorego w bazie NIE MA. Dlatego wlasnie
-- sciezki nie da sie wyliczyc i musi byc przechowana.
UPDATE sales_pipeline SET katalog = 'Klienci\Stepownia_Dudzik', updated_at = NOW()
 WHERE prospect_name ILIKE '%Stepownia%' AND katalog IS NULL
RETURNING prospect_name, stage, katalog;

\echo '--- 3. Dance Company La Cultura -> Klienci\\La_Cultura_Wrobel ---'
UPDATE sales_pipeline SET katalog = 'Klienci\La_Cultura_Wrobel', updated_at = NOW()
 WHERE prospect_name ILIKE '%La Cultura%' AND katalog IS NULL
RETURNING prospect_name, stage, katalog;

\echo '--- 4. Grupa Chwalinski: NOWY wiersz (katalog istnieje, wiersza w lejku nie bylo) ---'
-- Dane z Twojego wlasnego badania: Klienci\Chwalinski\01_badania\BADANIE_Grupa_Chwalinski_31072026.md
-- (KRS 0000033676, grupachwalinski.pl, dealer samochodowy w rejonie Opola, przychod 64,5 mln
-- za 2024 przy stracie netto 2,5 mln). NIC tu nie zmyslilem.
--
-- ETAP 'proposal' PRZYJETY Z FOLDERU, NIE Z BAZY: w 02_wyslane lezy
-- Tomasz_Nawrocki_dla_Grupy_Chwalinski_v1.pdf, a katalog 03_spotkania ma dopiero ANKIETE,
-- bez transkrypcji - w odroznieniu od StandART i La Cultura, gdzie transkrypcje rozmow sa.
-- Czyli: dokument poszedl, rozmowy jeszcze nie bylo. JESLI SIE MYLE, zmien jedno slowo
-- ponizej na 'qualified' PRZED uruchomieniem.
INSERT INTO sales_pipeline (brand_id, prospect_name, prospect_url, stage, niche, source,
                            katalog, notes)
SELECT 'AGS', 'Grupa Chwaliński', 'https://grupachwalinski.pl', 'proposal', 'motoryzacja',
       'manual', 'Klienci\Chwalinski',
       'Zalozony 01/08/2026 przy budowie mostu katalogi-baza. Katalog i materialy powstaly '
       'wczesniej niz wiersz w lejku: badanie 31/07 (Manus), dokument wyslany (02_wyslane), '
       'ankieta spotkania przygotowana. KRS 0000033676.'
 WHERE NOT EXISTS (SELECT 1 FROM sales_pipeline WHERE prospect_name ILIKE '%Chwali%')
RETURNING prospect_name, stage, katalog;

\echo '--- WERYFIKACJA: wszystkie katalogi w lejku ---'
SELECT prospect_name, stage, katalog
  FROM sales_pipeline WHERE katalog IS NOT NULL ORDER BY prospect_name;

\echo '--- KONTROLA: czy ktorys z czterech nie zlapal katalogu (ma byc PUSTO) ---'
SELECT prospect_name, stage, 'BRAK KATALOGU' AS uwaga
  FROM sales_pipeline
 WHERE katalog IS NULL
   AND (prospect_name ILIKE '%StandART%' OR prospect_name ILIKE '%Stepownia%'
        OR prospect_name ILIKE '%La Cultura%' OR prospect_name ILIKE '%Chwali%');

\echo '--- KONTROLA KODOWANIA: nazwa Chwalinskiego ma miec ogonek w "nski" ---'
-- Jesli zamiast "Chwaliński" zobaczysz krzaki, kodowanie sie przekrecilo przy INSERT.
-- Wtedy: NIE uruchamiaj ponownie (wiersz juz jest), tylko zglos mi to - poprawimy nazwe UPDATE-em.
SELECT prospect_name, length(prospect_name) AS znakow, katalog
  FROM sales_pipeline WHERE prospect_name ILIKE '%Chwali%';
