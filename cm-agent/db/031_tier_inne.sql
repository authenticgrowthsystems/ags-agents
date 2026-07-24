-- 031 (24/07/2026): paczka #1 Managera pkt 4 - piaty tier 'Inne'.
-- Decyzja Tomasza (guziki, 24/07): DODAC 'Inne' do istniejacej listy, legacy ZOSTAWIC.
--
-- Dlaczego nie twarde sciecie do 5 wartosci, jak proponowala paczka: sonda 24/07 (177
-- kontaktow) pokazala 45 zywych wierszy na wartosciach legacy (Watch 37, Premium 7, Mid 1).
-- CHECK ograniczony do piatki wywalilby te wiersze przy pierwszym UPDATE, a informacja
-- "ten kontakt przyszedl z bazy #71 jako Watch" zniknelaby bez sladu. Konsolidacja obu skal
-- to znany dlug (audyt 04/07 pkt 3, "konsolidacja contacts przed agentem CRM") - osobna
-- decyzja, nie efekt uboczny dokladania jednej wartosci.
--
-- Nazwa wiezow ustalona w db/026 (contacts_icp_tier_check) - stad DROP po nazwie.
-- Idempotentne: mozna puscic drugi raz.

ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_icp_tier_check;
ALTER TABLE contacts ADD CONSTRAINT contacts_icp_tier_check
  CHECK (icp_tier IS NULL OR icp_tier IN
         -- doktryna ICP #71 + 'Inne' (24/07: czlowiek spoza czterech kategorii)
         ('Buyer','Peer','Competitor','Partner','Inne',
          -- legacy z 001 / bazy #71 - historia, nikt jej nie migruje
          'Premium','Mid','Free','Watch','N/A'));

COMMENT ON CONSTRAINT contacts_icp_tier_check ON contacts IS
  'Buyer/Peer/Competitor/Partner + Inne (24/07) + legacy Premium/Mid/Free/Watch/N/A (45 zywych wierszy z bazy #71, zostawione jako historia)';

-- Kontrola
SELECT conname, pg_get_constraintdef(oid) AS definicja
  FROM pg_constraint WHERE conname = 'contacts_icp_tier_check';
SELECT COALESCE(icp_tier, '(puste)') AS tier, COUNT(*)::text AS n
  FROM contacts GROUP BY 1 ORDER BY 2 DESC;
