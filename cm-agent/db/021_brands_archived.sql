-- 021 (12/07/2026, task #86): brands.status dostaje 'archived' (soft-delete per brief:
-- /brand_remove zachowuje dane historyczne klienta). Dotychczasowy CHECK: active|paused
-- (dowod pg_get_constraintdef 12/07). Idempotentny. SCHEMA update w tym samym commicie.

ALTER TABLE brands DROP CONSTRAINT IF EXISTS brands_status_check;
ALTER TABLE brands ADD CONSTRAINT brands_status_check
  CHECK (status IN ('active', 'paused', 'archived'));

-- Kontrola
SELECT 'brands' AS co, string_agg(brand_id || ':' || status, ', ' ORDER BY brand_id) AS wynik FROM brands;
