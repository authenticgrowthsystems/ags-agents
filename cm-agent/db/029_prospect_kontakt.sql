-- 029 (24/07/2026): dane kontaktowe prospekta jako KOLUMNY, nie jako proza w notatkach.
--
-- Zgloszenie Tomasza: "research ma tez automatycznie uzupelniac baze danych bo od tego jest".
-- Do dzis telefon i mail zyly wylacznie w tekscie notatek albo w claims researchu, wiec kazdy
-- konsument musial je wyluskiwac regexem, a widok lejka i dziennik klienta nie wiedzialy o nich
-- nic. Struktura zamiast prozy: raz zdjete dane sa dostepne wszedzie.
--
-- Zrodla wypelniania (oba deterministyczne, bez LLM):
--   1. sales.wizytowka() - agent wchodzi na strone prospekta przed researchem i po,
--   2. sales.tick() - po zakonczonym researchu uzupelnia PUSTE pola z claims.
-- Zasada: nadpisujemy tylko puste. Dane potwierdzone recznie przez Tomasza sa nietykalne.
--
-- Kolumny celowo na sales_pipeline (firma), nie na contacts (osoba) - kanon WHO IS WHO mowi,
-- ze contacts to JEDNA OSOBA z mapa tozsamosci per kanal; recepcja@ i telefon centrali to
-- dane PODMIOTU. Osoba decyzyjna, gdy ja poznamy, dostanie wiersz w contacts i link contact_id.
--
-- Idempotentne: ADD COLUMN IF NOT EXISTS.

ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS contact_email   TEXT;
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS contact_phone   TEXT;
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS contact_person  TEXT;
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS site_checked_at TIMESTAMPTZ;

COMMENT ON COLUMN sales_pipeline.contact_email   IS 'mail firmowy prospekta (wizytowka ze strony / research); nadpisujemy tylko gdy puste';
COMMENT ON COLUMN sales_pipeline.contact_phone   IS 'telefon prospekta (wizytowka ze strony / research); nadpisujemy tylko gdy puste';
COMMENT ON COLUMN sales_pipeline.contact_person  IS 'osoba decyzyjna, gdy research ja ustali (imie i nazwisko)';
COMMENT ON COLUMN sales_pipeline.site_checked_at IS 'kiedy agent ostatnio zdjal strone prospekta (sales.wizytowka)';
