-- =============================================================================
-- 027_sales_agent.sql (BE-SPRZEDAWCA 20/07/2026)
-- Brief: docs/briefs/BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md (Level 1 MVP)
-- Agent Sprzedazy: lejek sprzedazowy (sales_pipeline), baza wiedzy sprzedazowej
-- z embeddingami (sales_knowledge), rejestracja agenta (agent_registry z prawem
-- do tieru critical Researchera) oraz wpis w channels, dzieki ktoremu Sprzedawca
-- POJAWIA SIE w menu /agents (menu n8n buduje sie dynamicznie z channels
-- supervised=true AND status IN ('active','draft') - zero zmian w wezlach menu).
-- config.agent_kind='sales' WYKLUCZA ten wiersz z planera/raportow/gap-fillera
-- (guardy w kodzie w TYM SAMYM commicie); welcomed=true wycisza powitanie kanalu.
-- Idempotentne (IF NOT EXISTS / ON CONFLICT).
-- Wykonanie (SSH, Tomasz, PRZED rebuildem cm-agent):
--   docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/027_sales_agent.sql
-- =============================================================================

-- 1) Lejek sprzedazowy. Kazdy prospekt = wiersz; stage liniowo prospect -> won/lost.
--    contact_id laczy z CRM (#71/026); research_job_id TEXT (id joba Researchera).
CREATE TABLE IF NOT EXISTS sales_pipeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
  prospect_name TEXT NOT NULL,
  prospect_url TEXT,
  stage VARCHAR(20) NOT NULL DEFAULT 'prospect'
    CHECK (stage IN ('prospect','qualified','proposal','negotiation','won','lost')),
  offer_tier TEXT,
  value NUMERIC(12,2),
  currency VARCHAR(10) NOT NULL DEFAULT 'PLN',
  next_followup_at TIMESTAMPTZ,
  research_job_id TEXT,
  notes TEXT,
  source VARCHAR(40) NOT NULL DEFAULT 'manual',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_stage ON sales_pipeline(brand_id, stage);
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_followup ON sales_pipeline(next_followup_at)
  WHERE stage NOT IN ('won','lost');

-- 2) Baza wiedzy sprzedazowej (ksiazki/techniki/case studies Tomasza).
--    Dokument dzielony na kawalki (chunk_no); embedding OpenAI text-embedding-3-small
--    (1536 wymiarow, jak published_posts) - semantic search przy outreach.
--    embedding NULL dozwolony (brak klucza OpenAI = degradacja bez crasha).
CREATE TABLE IF NOT EXISTS sales_knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  material_type VARCHAR(20) NOT NULL DEFAULT 'other'
    CHECK (material_type IN ('book','technique','case_study','framework','script','recording','other')),
  material_name TEXT NOT NULL,
  chunk_no INT NOT NULL DEFAULT 1,
  content_excerpt TEXT NOT NULL,
  source_url TEXT,
  embedding vector(1536),
  tags TEXT[] NOT NULL DEFAULT '{}',
  added_by VARCHAR(40) NOT NULL DEFAULT 'telegram',
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sales_knowledge_name ON sales_knowledge(brand_id, material_name);

-- 3) Rejestracja agenta w sieci + PRAWO DO CRITICAL w Researcherze
--    (worker Researchera sprawdza allowed_model_tiers po agent_name z pola 'from';
--    bez tego job z model_tier='critical' PARKUJE w awaiting_approval).
INSERT INTO agent_registry (agent_name, agent_type, role, model_tier, status, current_gate, allowed_model_tiers)
VALUES ('sales-agent','specialist',
        'Agent Sprzedazy AGS: prospect research (Researcher critical), outreach w Voice Bible (HITL), lejek sales_pipeline',
        'opus-4-8','building','awaiting_acceptance', ARRAY['low','medium','critical'])
ON CONFLICT (agent_name) DO UPDATE SET allowed_model_tiers = EXCLUDED.allowed_model_tiers;

-- 4) Sprzedawca w menu /agents: wiersz channels (NIE-publikacyjny!).
--    status='draft' celowo (NIE aktywowac w ⚙️ Cele - to nie jest cel publikacji);
--    agent_kind='sales' filtruje go z planera/raportow/gap-fillera/snapshotow celow.
INSERT INTO channels (brand_id, channel, status, adapter_path, config, supervised)
VALUES ('AGS','sprzedaz','draft',NULL,
        '{"agent_kind":"sales","welcomed":true,"publish_mode":"none",
          "voice_note":"Agent Sprzedazy - NIE publikuje tresci; rozmowa strategiczna + gotowce outreach (HITL)"}'::jsonb,
        true)
ON CONFLICT (brand_id, channel) DO NOTHING;

-- Kontrola:
SELECT 'sales_pipeline' AS obiekt, COUNT(*)::text AS n FROM sales_pipeline
UNION ALL SELECT 'sales_knowledge', COUNT(*)::text FROM sales_knowledge
UNION ALL SELECT 'agent sales-agent', COUNT(*)::text FROM agent_registry WHERE agent_name='sales-agent'
UNION ALL SELECT 'channel sprzedaz', COUNT(*)::text FROM channels WHERE brand_id='AGS' AND channel='sprzedaz';
