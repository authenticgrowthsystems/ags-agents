-- CM FAZA 2 (04/07/2026, ags_crd). Idempotent. Wg CM_FAZA2_DESIGN_v1 (decyzje rozstrzygniete).

-- 1) STAN AWARYJNY (kanon 11c): znacznik wyslania prosby o approve - od niego liczy sie 24h ciszy
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMPTZ;

-- 2) planer zapisuje zarys miesiaca do brand_config (cm_month_outline) - grant dla roli workera
GRANT SELECT, INSERT, UPDATE ON brand_config TO ags_crd_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ags_crd_user;

-- 3) kadencja kanoniczna (kanon 11d) w konfiguracji istniejacych celow (nie nadpisuje, gdy juz ustawione)
UPDATE channels SET config = config || '{"posts_per_day": "3-5"}'::jsonb
WHERE brand_id='AGS' AND channel='x' AND NOT (config ? 'posts_per_day');
UPDATE channels SET config = config || '{"weekly_pattern": {"mon-fri": "post", "sat": null, "sun": "article"}}'::jsonb
WHERE channel LIKE 'linkedin%' AND NOT (config ? 'weekly_pattern');
