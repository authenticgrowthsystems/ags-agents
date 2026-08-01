-- DDL 037 (01/08/2026): MOST MIEDZY KATALOGAMI NA DYSKU A LEJKIEM.
--
-- POWOD: powstala struktura katalogow klientow (C:\Claude-CoWork\TyNieMusisz\Klienci\<Nazwa>\
-- z podfolderami 01_badania, 02_wyslane, 03_spotkania, 04_oferty). Dotad byly to dwa niezalezne
-- swiaty: pliki na dysku i wiersze w bazie. Trzeba je zwiazac, zanim sie rozjada.
--
-- USTALENIE Z ODCZYTU (01/08), ktore wymusilo ten ksztalt:
--   katalog na dysku      wiersz w lejku              czy da sie wyliczyc
--   StandART              Klub Sportowy StandART      nie (inny czlon wiodacy)
--   Stepownia_Dudzik      Wroclawska Stepownia        NIE - "Dudzik" NIE ISTNIEJE w bazie
--   La_Cultura_Wrobel     Dance Company La Cultura    NIE - "Wrobel" NIE ISTNIEJE w bazie
--   Chwalinski            (brak wiersza)              -
-- Nazwy katalogow niosa NAZWISKO WLASCICIELA, ktorego w bazie nie ma w ogole. Zadna regula
-- transliteracji tego nie odtworzy, wiec sciezke trzeba PRZECHOWAC, a nie liczyc.
--
-- DLACZEGO sales_pipeline, a nie contacts (decyzja Tomasza 01/08): wszyscy czterej klienci
-- z katalogow siedza w lejku. `contacts` to 194 uchwyty z X i LinkedIna z ZEREM maili -
-- kolumna na katalogu bylaby tam pusta, dopoki ktos nie zalozy wierszy rownoleglych do lejka,
-- czyli drugiego zrodla prawdy o tym samym podmiocie.
--
-- Uruchomienie: psql -U n8n -d ags_crd -f 037_katalog_klienta.sql  (idempotentne)

-- Sciezka WZGLEDNA wobec korzenia marki, np. 'Klienci\Chwalinski'. Bez litery dysku, bez
-- korzenia - korzen jest cecha maszyny, nie prospekta, i nie ma czego robic w wierszu.
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS katalog TEXT;

COMMENT ON COLUMN sales_pipeline.katalog IS
  'Sciezka WZGLEDNA do katalogu klienta, np. Klienci\Chwalinski. Ustalana RAZ przy pierwszym kontakcie i nigdy niezmieniana - zmiana rozjechalaby ja z dyskiem, bo system NIGDY nie tworzy ani nie przenosi katalogow. Bez polskich znakow.';

-- Katalog wisi na `id`, nie na nazwie. `prospect_name` NIE MA ograniczenia UNIQUE, wiec dwa
-- wiersze o tej samej nazwie sa dopuszczalne - wiazanie po nazwie pekloby przy pierwszej
-- franczyzie (Egurrola ma w lejku trzy wiersze).
-- Indeks czesciowy: katalogow bedzie garstka wobec 133 wierszy lejka.
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_katalog
  ON sales_pipeline(katalog) WHERE katalog IS NOT NULL;

-- WERYFIKACJA (odczyt, uruchom po migracji):
-- SELECT prospect_name, stage, katalog FROM sales_pipeline
--  WHERE katalog IS NOT NULL ORDER BY prospect_name;
