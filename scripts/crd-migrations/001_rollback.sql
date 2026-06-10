-- =============================================================================
-- Rollback: 001_rollback.sql
-- Date: 2026-05-31
-- Paired with: 001_initial_schema.sql
-- =============================================================================
-- DANGER: This script is DESTRUCTIVE and IRREVERSIBLE.
-- Running this will permanently DROP all tables, triggers, and functions
-- created by migration 001_initial_schema.sql, including ALL DATA in:
--   - hitl_sessions
--   - engagement_log
--   - contacts
-- Do NOT run this against production unless you have a verified backup.
-- =============================================================================

-- Drop trigger before dropping the function it depends on
DROP TRIGGER IF EXISTS contacts_updated_at ON contacts;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS cleanup_expired_hitl_sessions();

-- Drop tables (CASCADE drops dependent foreign keys and indexes automatically)
DROP TABLE IF EXISTS hitl_sessions CASCADE;
DROP TABLE IF EXISTS engagement_log CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;

-- NOTE: pgcrypto extension is NOT dropped here.
-- It may be used by other schemas or migrations. To remove it manually:
--   DROP EXTENSION IF EXISTS "pgcrypto";
-- Only do this if you are certain no other objects depend on it.
