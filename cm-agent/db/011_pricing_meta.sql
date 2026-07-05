-- TASK #71 (decyzja Managera #2, 05/07): pricing_tiers.meta_status.
-- Lokalna Automatyzacja = 'parking_active' (partnerstwo Jacka pending); AGS Premium (Faza D) = 'active'.
ALTER TABLE pricing_tiers ADD COLUMN IF NOT EXISTS meta_status VARCHAR(30) NOT NULL DEFAULT 'active';
UPDATE pricing_tiers SET meta_status = 'parking_active' WHERE ladder = 'lokalna_automatyzacja';
SELECT ladder, tier_name, meta_status FROM pricing_tiers ORDER BY ladder, tier_name;
