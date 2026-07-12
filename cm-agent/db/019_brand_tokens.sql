-- 019 (12/07/2026, task #84): brand_tokens - tokeny wizualne marek (Notion SSOT -> PG mirror).
-- Zrodlo architektury: brief 12/07 Opcja C (research Manus #85). Notion baza "Brand Config"
-- (kolumny Token_Name / Token_Type / <BRAND>_Value) -> puller w cm-agent (sync worker, poll 10 min)
-- -> ta tabela -> agenci grafiki czytaja tokens PRZED generowaniem obrazu.
-- Idempotentny. DDL => wpis w docs/db/SCHEMA_ags_crd.md w TYM SAMYM commicie (regula 08/07).

CREATE TABLE IF NOT EXISTS brand_tokens (
    brand_id   VARCHAR(50) PRIMARY KEY REFERENCES brands(brand_id),
    tokens     JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    source     VARCHAR(50) DEFAULT 'notion_sync'
);

-- Kontrola
SELECT 'brand_tokens' AS co, COUNT(*)::text AS wierszy FROM brand_tokens;
