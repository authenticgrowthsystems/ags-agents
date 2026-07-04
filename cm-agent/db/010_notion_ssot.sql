-- TASK #71 Faza A: Notion -> PostgreSQL SSOT (04/07/2026). Idempotent. Mapping APPROVED przez Tomasza
-- (10/10 kategorii, 04/07) wg kontraktu Managera FEEDBACK_do_BE_Notion_Migration_FULL_04072026.md.
-- 17 nowych tabel + rozszerzenia. Kazda tabela ETL: notion_page_id UNIQUE = kotwica idempotencji.
-- KOREKTY BE (zatwierdzone przy mappingu): content_items +meta_type +statusy draft/brief;
-- agent_contracts = NOWA tabela (nie istniala); brand_config = klucz/wartosc -> canon/ghl/sync jako WIERSZE
-- (wzorzec voice_bible), nie kolumny; channels: first_comment w config jsonb (kontrakt per cel).

-- ===== KATEGORIA 1: DOKTRYNA =====
CREATE TABLE IF NOT EXISTS agent_blueprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version VARCHAR(20) NOT NULL,                 -- '1.3'
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded')),
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE agent_blueprints OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS be_contracts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version VARCHAR(20) NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded')),
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE be_contracts OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS content_distribution_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  rule_name TEXT NOT NULL,
  content TEXT,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE content_distribution_rules OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS icp_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  name TEXT NOT NULL,
  definition TEXT,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE icp_definitions OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS sales_playbook (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  section VARCHAR(60) NOT NULL,   -- sales_bible|hot_lead_scripts|growth_playbook|peer_discovery|validated_patterns|...
  title TEXT,
  content TEXT,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  version VARCHAR(20),
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sales_playbook_section ON sales_playbook(brand_id, section);
ALTER TABLE sales_playbook OWNER TO ags_crd_user;

-- ===== KATEGORIA 2: AGENCI =====
CREATE TABLE IF NOT EXISTS agent_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name VARCHAR(80) NOT NULL,   -- luzny klucz (czesc agentow nie ma wpisu w agent_registry)
  version VARCHAR(20) NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded')),
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_prompts_agent ON agent_prompts(agent_name, status);
ALTER TABLE agent_prompts OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS agent_session_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name VARCHAR(80) NOT NULL UNIQUE,
  state JSONB NOT NULL DEFAULT '{}'::jsonb,
  content TEXT,
  notion_page_id TEXT UNIQUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE agent_session_state OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS agent_contracts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name VARCHAR(80) NOT NULL,
  oversight_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  tool_guidelines JSONB NOT NULL DEFAULT '{}'::jsonb,
  content TEXT,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE agent_contracts OWNER TO ags_crd_user;

-- ===== KATEGORIA 3: ZYWE =====
CREATE TABLE IF NOT EXISTS manager_daily_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  meta_type VARCHAR(40) NOT NULL DEFAULT 'daily_status',  -- daily_status|stan_gry_snapshot|ssot_event
  content TEXT NOT NULL,
  notion_page_id TEXT,          -- wpisy z jednej strony append-only NIE sa unikalne per page
  entry_hash TEXT UNIQUE,       -- md5(content) = kotwica idempotencji per WPIS
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_manager_daily_log_ts ON manager_daily_log(entry_ts);
ALTER TABLE manager_daily_log OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS chat_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_name TEXT NOT NULL,
  platform VARCHAR(40),          -- claude|cowork|chatgpt|...
  purpose TEXT,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE chat_registry OWNER TO ags_crd_user;

-- ===== KATEGORIE 5-6: SPRZEDAZ =====
CREATE TABLE IF NOT EXISTS sales_sequences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  name TEXT NOT NULL,
  steps JSONB NOT NULL DEFAULT '[]'::jsonb,
  content TEXT,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE sales_sequences OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS pricing_tiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  ladder VARCHAR(40) NOT NULL,   -- ags_premium | lokalna_automatyzacja
  tier_name TEXT NOT NULL,
  price TEXT,
  currency VARCHAR(10),
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (brand_id, ladder, tier_name)
);
ALTER TABLE pricing_tiers OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS vendor_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor TEXT NOT NULL,
  category VARCHAR(60),
  brands TEXT[] NOT NULL DEFAULT '{}',
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  notes TEXT,
  notion_page_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (vendor, category)
);
ALTER TABLE vendor_registry OWNER TO ags_crd_user;

-- ===== KATEGORIA 7: INFRA =====
CREATE TABLE IF NOT EXISTS funnel_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  funnel_name TEXT NOT NULL,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  content TEXT,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE funnel_configs OWNER TO ags_crd_user;

-- ===== KATEGORIE 8-9: RAPORTY I DECYZJE =====
CREATE TABLE IF NOT EXISTS manager_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decided_at TIMESTAMPTZ,
  topic TEXT,
  decision TEXT NOT NULL,
  context JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT,
  entry_hash TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE manager_decisions OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS monthly_discovery_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  month DATE NOT NULL,
  report TEXT NOT NULL,
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  notion_page_id TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (brand_id, month)
);
ALTER TABLE monthly_discovery_reports OWNER TO ags_crd_user;

-- ===== KATEGORIA 10: ROADMAP =====
CREATE TABLE IF NOT EXISTS roadmap_milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id VARCHAR(50) NOT NULL DEFAULT 'AGS',
  milestone TEXT NOT NULL,
  campaign VARCHAR(80),
  due_date DATE,
  status VARCHAR(30) NOT NULL DEFAULT 'planned',
  details TEXT,
  notion_page_id TEXT,
  entry_hash TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE roadmap_milestones OWNER TO ags_crd_user;

-- ===== ROZSZERZENIA ISTNIEJACYCH =====
-- contacts: TYLKO brakujace (source/notes/last_interaction_date JUZ ISTNIEJA - audyt DB 04/07)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS pipeline_stage TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS brand_context TEXT[];
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS tags TEXT[];
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS notion_page_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_notion ON contacts(notion_page_id) WHERE notion_page_id IS NOT NULL;

-- content_items: meta_type + statusy migracyjne (KOREKTA BE, approved przy K4)
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS meta_type VARCHAR(40);
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS notion_page_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_content_items_notion ON content_items(notion_page_id) WHERE notion_page_id IS NOT NULL;
ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_status_check;
ALTER TABLE content_items ADD CONSTRAINT content_items_status_check
  CHECK (status IN ('proposed','planned','needs_research','researching','drafting','needs_approval',
                    'approved','dispatching','published','rejected','failed','draft','brief','archived'));

-- brand_config = klucz/wartosc: website_canon/footer_canon/ghl_config/sync_to_notion wchodza jako WIERSZE
-- podczas ETL (INSERT ... ON CONFLICT wzorcem /set). Flaga sprzedawalnosci od razu:
INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
VALUES ('AGS', 'sync_to_notion', 'true', 1, 'task-71', NOW())
ON CONFLICT (brand_id, config_key) DO NOTHING;
