-- Pakiet naprawczy relacji (04/07/2026, ags_crd). Idempotentny. Wg docs/db/DB_AUDIT_04072026.md sekcja 3.
-- NIE zawiera konsolidacji contacts (osobna decyzja przy projekcie warstwy CRM).

-- 1) NAPRAWA zerwanej relacji schowek -> produkcja:
--    content_items.inspiration_id bylo UUID, inspirations.id jest BIGINT (typy niezgodne = FK niemozliwy).
--    Kolumna jest dzis pusta (weryfikacja ponizej zatrzyma migracje, gdyby jednak nie byla).
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM content_items WHERE inspiration_id IS NOT NULL) > 0 THEN
    RAISE EXCEPTION 'content_items.inspiration_id ma dane - migracja wymaga mapowania, przerwano';
  END IF;
END $$;
ALTER TABLE content_items DROP COLUMN IF EXISTS inspiration_id;
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS inspiration_id BIGINT REFERENCES inspirations(id);
CREATE INDEX IF NOT EXISTS idx_content_items_inspiration ON content_items(inspiration_id);

-- 2) brand/platform przestaja byc luznym tekstem: FK NOT VALID = pilnuje NOWYCH zapisow,
--    starych wierszy nie blokuje (walidacja calosci osobnym krokiem po sprzataniu danych legacy).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_post_queue_brand') THEN
    ALTER TABLE post_queue ADD CONSTRAINT fk_post_queue_brand
      FOREIGN KEY (brand) REFERENCES brands(brand_id) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_post_queue_channel') THEN
    ALTER TABLE post_queue ADD CONSTRAINT fk_post_queue_channel
      FOREIGN KEY (brand, platform) REFERENCES channels(brand_id, channel) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_published_posts_brand') THEN
    ALTER TABLE published_posts ADD CONSTRAINT fk_published_posts_brand
      FOREIGN KEY (brand) REFERENCES brands(brand_id) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_published_posts_channel') THEN
    ALTER TABLE published_posts ADD CONSTRAINT fk_published_posts_channel
      FOREIGN KEY (brand, platform) REFERENCES channels(brand_id, channel) NOT VALID;
  END IF;
END $$;

-- 3) wymagany cel dla FK zlozonego: unikalnosc (brand_id, channel) juz istnieje (UNIQUE w channels).
-- Walidacja calosci (po ewentualnym sprzataniu legacy):
--   ALTER TABLE post_queue VALIDATE CONSTRAINT fk_post_queue_brand;  (itd.)
