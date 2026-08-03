-- CM Agent init schema (30/06/2026, ags_crd). Idempotent. Apply as superuser n8n via SSH; the OWNER TO
-- statements hand the new tables to ags_crd_user (the role the worker + n8n connect as), so the CM service
-- has full DML like the Researcher tables. brand_id = VARCHAR(50) tenant key (matches brand_config.brand_id,
-- e.g. 'AGS'). Every brand_id NOT NULL + indexed = RLS-ready (policies added before the 2nd brand in CM).

-- 1) tenant anchor (lightweight brand registry; FK target for brand_id)
CREATE TABLE IF NOT EXISTS brands (
  brand_id    VARCHAR(50) PRIMARY KEY,
  brand_name  TEXT NOT NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE brands OWNER TO ags_crd_user;

-- 2) content brain: one canonical content object per idea/plan
CREATE TABLE IF NOT EXISTS content_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id        VARCHAR(50) NOT NULL REFERENCES brands(brand_id),
  master_theme    TEXT NOT NULL,
  canonical_body  TEXT,                            -- Sonnet tekst-matka; NULL until generated
  taxonomy        VARCHAR(30) CHECK (taxonomy IN ('build-report','news','edu')),
  target_channels TEXT[] NOT NULL DEFAULT '{}',    -- e.g. {x,linkedin}
  research_job_id UUID,                            -- link to research_jobs (Researcher)
  inspiration_id  UUID,                            -- link to inspirations
  -- D-008 (03/08/2026): 'handed_off' zastapilo 'dispatching' (AP-312 - nazwa obiecywala stan
  -- przelotny, a stan trwa DNI). Stara wartosc stoi tu PRZEJSCIOWO, zeby droga odwrotu istniala;
  -- znika w osobnym oknie: docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql.
  -- Zrodlo prawdy dla tego ograniczenia na produkcji: cm-agent/db/042_status_handed_off.sql.
  status          VARCHAR(30) NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('planned','needs_research','researching','drafting',
                                      'needs_approval','approved','handed_off','dispatching',
                                      'published','rejected','failed')),
  scheduled_for   TIMESTAMPTZ,
  voice_hash      TEXT,                            -- voice snapshot version at generation
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_items_brand  ON content_items(brand_id);
CREATE INDEX IF NOT EXISTS idx_content_items_status ON content_items(status);
ALTER TABLE content_items OWNER TO ags_crd_user;

-- 3) per-brand strategy (operational projection of the Obsidian/Manager layer; CM reads it at generation)
CREATE TABLE IF NOT EXISTS brand_strategy (
  brand_id        VARCHAR(50) PRIMARY KEY REFERENCES brands(brand_id),
  target_audience TEXT,
  content_pillars TEXT[] DEFAULT '{}',
  core_topics     TEXT[] DEFAULT '{}',
  competitor_urls TEXT[] DEFAULT '{}',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE brand_strategy OWNER TO ags_crd_user;

-- 4) GENERIC channel/subagent registry (channel = any string, NOT an enum -> open/closed: new channel = new row)
CREATE TABLE IF NOT EXISTS channels (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id     VARCHAR(50) NOT NULL REFERENCES brands(brand_id),
  channel      VARCHAR(40) NOT NULL,               -- 'x','linkedin','youtube','facebook','instagram','tiktok',...
  status       VARCHAR(20) NOT NULL DEFAULT 'ready' CHECK (status IN ('active','draft','ready','paused')),
  adapter_path TEXT,                               -- publish-adapter webhook (NULL for post_queue/draft/ready modes)
  config       JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g. {"publish_mode":"post_queue|webhook|draft"}
  UNIQUE (brand_id, channel)
);
CREATE INDEX IF NOT EXISTS idx_channels_brand ON channels(brand_id);
ALTER TABLE channels OWNER TO ags_crd_user;

-- 5) outbox link: a post_queue row (per-channel variant) traces back to its content_item. ags_crd_user already
--    has DML on post_queue (the live content pipeline uses it); only the column add needs superuser if owned by n8n.
ALTER TABLE post_queue ADD COLUMN IF NOT EXISTS content_item_id UUID REFERENCES content_items(id);
CREATE INDEX IF NOT EXISTS idx_post_queue_content_item ON post_queue(content_item_id);
