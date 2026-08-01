-- DDL 038 (01/08/2026): ETYKIETA marki docelowej. NIE JEST TO FILTR.
--
-- DECYZJA TOMASZA 01/08, wariant drugi: NIE przepinamy `brand_id`, bo z tego lejka toczy sie
-- dzis sprzedaz. Powod w jego slowach: "wypchniecie 24 wierszy poza widok lejka, poza straznika
-- terminow i poza generowanie gotowcow, w tygodniu, w ktorym mam trzy otwarte rozmowy i wyslany
-- material do dealera, to jest kupowanie porzadku za sprzedaz".
--
-- RACHUNEK, KTORY ZA TYM STOI (odczyt 01/08): **107 miejsc w `cm-agent/app/` filtruje
-- `brand_id='AGS'`, w tym 13 w samym `sales.py`**. Kod jest jednomarkowy. Zmiana `brand_id`
-- na 'TNM' wypchnelaby te wiersze z widoku lejka, ze straznika terminow i z generowania
-- gotowcow - po cichu, bo zapytanie bez wynikow nie jest bledem.
--
-- DLATEGO: `marka_docelowa` to CZYSTA ETYKIETA. Zaden kod jej nie czyta i czytac nie ma.
-- Jej jedyne zadanie: kiedy kod bedzie wielomarkowy, przepiecie ma byc JEDNYM UPDATE-em,
-- a nie ponownym rozstrzyganiem dwudziestu czterech przypadkow z pamieci pol roku pozniej.
--
-- REGULA, ktora ta kolumna utrwala (obowiazujaca od 01/08/2026):
--   polski rynek i polski jezyk        -> TNM
--   anglojezyczne kontakty z X i LinkedIna -> AGS
--
-- Uruchomienie: psql -U n8n -d ags_crd -f 038_marka_docelowa.sql  (idempotentne)

ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS marka_docelowa TEXT;

COMMENT ON COLUMN sales_pipeline.marka_docelowa IS
  'ETYKIETA, NIE FILTR. Docelowa marka wiersza wedlug reguly z 01/08/2026 (polski rynek = TNM, anglojezyczne kontakty z X i LinkedIna = AGS). ZADEN KOD JEJ NIE CZYTA - brand_id pozostaje jedynym filtrem, dopoki kod nie stanie sie wielomarkowy. Sluzy do tego, zeby przyszle przepiecie bylo jednym UPDATE-em zamiast ponownego rozstrzygania kazdego przypadku.';

-- SWIADOMIE BEZ ograniczenia CHECK i BEZ indeksu: kolumna niczego nie filtruje, wiec indeks
-- byloby martwym kosztem, a CHECK zamrozilby liste marek, ktora nie jest jeszcze ustalona
-- (RDC, Pierwszy Taniec i inne moga dojsc).

-- WERYFIKACJA (odczyt):
-- SELECT COALESCE(marka_docelowa,'(brak)') AS marka, stage, COUNT(*)
--   FROM sales_pipeline GROUP BY 1,2 ORDER BY 1,2;
