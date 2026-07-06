-- MULTIMEDIA etap 1 (06/07/2026): zalaczniki materialow (source-descriptor: Telegram teraz,
-- GDrive/inne pozniej - fakty X_MEDIA_API_2026). Idempotent. Ksztalt elementu:
-- {"source":"telegram","file_id":"...","kind":"photo"}.
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS media JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE post_queue  ADD COLUMN IF NOT EXISTS media JSONB NOT NULL DEFAULT '[]'::jsonb;
SELECT column_name FROM information_schema.columns
WHERE table_name IN ('content_items','post_queue') AND column_name='media';
