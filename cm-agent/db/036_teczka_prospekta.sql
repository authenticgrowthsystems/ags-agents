-- DDL 036 (31/07/2026): TECZKA PROSPEKTA - para zapisz_tekst + teczka jako JEDEN kontrakt.
--
-- POWOD (zadanie Managera): maile sprzedazowe pisane w Cowork ladowaly wylacznie w czacie.
-- Zero sladu w bazie, wiec nie dalo sie iterowac, policzyc ani wczytac w nowej rozmowie.
--
-- USTALENIE Z ODCZYTU PRODUKCJI (31/07, sonda jednorazowa):
--   contacts        194 wierszy, 0 z mailem  - uchwyty z X i LinkedIna (radar komentarzy)
--   sales_pipeline  133 wiersze,  0 z contact_id - prospekty kampanii (szkoly tanca)
--   pokrycie po nazwie: 1 na 133
-- To sa DWIE ROZLACZNE POPULACJE. Prospekt kampanii NIE MA wiersza w contacts i nie bedzie
-- go mial, bo kanon z 22/07 mowi: zrodlem prawdy o prospekcie jest sales_pipeline. Dlatego
-- engagement_log dostaje DRUGI klucz obcy (pipeline_id) zamiast dosypywania contacts.
--
-- Uruchomienie: psql -U postgres -d ags_crd -f 036_teczka_prospekta.sql  (idempotentne)

-- 1) STATUS 'draft'. SWIADOMIE NOWA WARTOSC, nie recykling 'proposed'.
--    'proposed' jest konsumowane przez engagement._watch_proposed (gotowce Sprzedawcy) - kazdy
--    mail pisany w Cowork zrodzilby po dobie bramke "Outreach czeka na wyslanie". Szkic Managera
--    to NIE jest gotowiec czekajacy na tapniecie, wiec musi byc dla straznikow martwy.
DO $$
BEGIN
  ALTER TABLE engagement_log DROP CONSTRAINT IF EXISTS engagement_log_status_check;
  ALTER TABLE engagement_log ADD CONSTRAINT engagement_log_status_check
    CHECK (status IN ('logged','proposed','approved','rejected','sent','skipped','draft'));
END $$;

-- 2) KANALY 'SMS' i 'WhatsApp'.
--    Manager podal kanaly email|sms|dm|telefon. 'SMS' dokladamy wprost z kontraktu, 'WhatsApp'
--    dokladamy dlatego, ze kanon zimnej wysylki z 27/07 mowi "WhatsApp nie SMS" - bez tej wartosci
--    wiadomosc wyslana faktycznym kanalem kampanii musialaby byc zapisana klamliwie jako SMS.
DO $$
BEGIN
  ALTER TABLE engagement_log DROP CONSTRAINT IF EXISTS engagement_log_channel_check;
  ALTER TABLE engagement_log ADD CONSTRAINT engagement_log_channel_check
    CHECK (channel IN ('X','LinkedIn','Instagram','Facebook','Email','Telegram','Phone','Other',
                       'SMS','WhatsApp'));
END $$;

-- 3) DRUGI KLUCZ OBCY: wpis moze wisiec przy prospekcie z lejka, nie tylko przy kontakcie.
--    Dotad jedynym wiazaniem gotowca z prospektem bylo author_display (tekst z nazwa) - dopasowanie
--    po napisie, ktore pekalo przy kazdej literowce. Od teraz wiazanie jest kluczem.
ALTER TABLE engagement_log
  ADD COLUMN IF NOT EXISTS pipeline_id UUID REFERENCES sales_pipeline(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_engagement_log_pipeline
  ON engagement_log(pipeline_id, created_at DESC) WHERE pipeline_id IS NOT NULL;

-- 4) NASTEPNY KROK Z TRESCIA.
--    sales_pipeline mial wylacznie next_followup_at - sama DATE, bez zdania co ma sie wydarzyc.
--    contacts.next_action istnieje od DDL 001 i przez caly ten czas NIE ZAPISAL GO NIKT (0 wierszy),
--    wiec nie jest to kolumna, na ktorej mozna oprzec odczyt. Teczka ma zwracac "ostatni ustalony
--    next step z data", wiec tresc kroku dostaje miejsce przy dacie, ktora juz dziala.
ALTER TABLE sales_pipeline ADD COLUMN IF NOT EXISTS next_step TEXT;

COMMENT ON COLUMN engagement_log.pipeline_id IS
  'Prospekt z lejka, do ktorego odnosi sie wpis. Rozlaczne z contact_id: contacts to uchwyty spolecznosciowe, sales_pipeline to prospekty kampanii.';
COMMENT ON COLUMN sales_pipeline.next_step IS
  'Tresc nastepnego ustalonego kroku. Data tego kroku siedzi w next_followup_at.';

-- 5) BACKFILL istniejacych gotowcow Sprzedawcy: dopasowanie DOKLADNE po nazwie (bez zgadywania).
--    Wpisy, ktore sie nie dopasuja, zostaja z pipeline_id NULL - lepiej puste niz podpiete blednie.
UPDATE engagement_log e
   SET pipeline_id = s.id
  FROM sales_pipeline s
 WHERE e.pipeline_id IS NULL
   AND COALESCE(e.author_display,'') <> ''
   AND lower(btrim(e.author_display)) = lower(btrim(s.prospect_name));

-- WERYFIKACJA (odczyt, uruchom po migracji):
-- SELECT COUNT(*) FILTER (WHERE pipeline_id IS NOT NULL) AS podpiete_do_lejka,
--        COUNT(*) FILTER (WHERE contact_id IS NOT NULL)  AS podpiete_do_kontaktu,
--        COUNT(*) AS wszystkie
--   FROM engagement_log;
