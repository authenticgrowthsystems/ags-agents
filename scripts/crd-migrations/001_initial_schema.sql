-- =============================================================================
-- Migration: 001_initial_schema.sql
-- Date: 2026-05-31
-- Version: 1.0.0
-- Description: Initial AGS CRD schema - contacts, engagement_log, hitl_sessions
-- Database: ags_crd
-- Schema: public
-- PostgreSQL: 15+
-- =============================================================================

-- Enable UUID generation via pgcrypto (gen_random_uuid())
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TABLE: contacts
-- AGS Contact Relationship Database - primary contact store
-- =============================================================================
CREATE TABLE IF NOT EXISTS contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE,
  linkedin_url TEXT,
  x_handle VARCHAR(100),
  instagram_handle VARCHAR(100),
  facebook_url TEXT,
  email VARCHAR(255),
  phone VARCHAR(50),
  website TEXT,
  brand_affinity VARCHAR(50) CHECK (brand_affinity IN ('AGS','TNM','RDC','Pierwszy Taniec','Multi')),
  icp_tier VARCHAR(50) CHECK (icp_tier IN ('Premium','Mid','Free','Watch','N/A')),
  status VARCHAR(50) NOT NULL DEFAULT 'Cold' CHECK (status IN ('Cold','Warm','Hot','Customer','Ghosted','Peer','Competitor')),
  source VARCHAR(100) CHECK (source IN ('Inbound DM','Outbound DM','Comment','Mention','Referral','Newsletter','Webinar','Event','Unknown')),
  languages TEXT[] NOT NULL DEFAULT '{}',
  geography VARCHAR(50),
  pain_point TEXT,
  interests TEXT[] NOT NULL DEFAULT '{}',
  narration TEXT,
  first_contact_date DATE,
  last_interaction_date DATE,
  last_interaction_type VARCHAR(50) CHECK (last_interaction_type IN ('Comment','DM','Mention','Reply','Reaction','Email','Call','Post','Follow','Other')),
  next_action TEXT,
  next_action_due DATE,
  next_action_owner VARCHAR(100),
  priority VARCHAR(10) NOT NULL DEFAULT 'P3' CHECK (priority IN ('P0','P1','P2','P3')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE contacts IS 'AGS Contact Relationship Database - primary contact store';
COMMENT ON COLUMN contacts.x_handle IS 'X (Twitter) handle without @ prefix';
COMMENT ON COLUMN contacts.brand_affinity IS 'Primary AGS brand this contact relates to';
COMMENT ON COLUMN contacts.icp_tier IS 'Ideal customer profile tier for offer routing';
COMMENT ON COLUMN contacts.priority IS 'P0=M5 path active, P1=warm priority, P2=standard, P3=watch';

-- =============================================================================
-- TABLE: engagement_log
-- Chronological log of all agent interactions and published content
-- =============================================================================
CREATE TABLE IF NOT EXISTS engagement_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
  action_type VARCHAR(100) NOT NULL CHECK (action_type IN ('x_post','x_reply','x_comment','x_dm','linkedin_post','linkedin_comment','linkedin_dm','email','telegram','call','follow','unfollow','mention','reaction','other')),
  channel VARCHAR(50) CHECK (channel IN ('X','LinkedIn','Instagram','Facebook','Email','Telegram','Phone','Other')),
  agent VARCHAR(100),
  content TEXT,
  content_url TEXT,
  response TEXT,
  platform_id VARCHAR(255),
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE engagement_log IS 'Chronological log of all agent interactions and published content';
COMMENT ON COLUMN engagement_log.platform_id IS 'Platform-specific ID: tweet_id, post_id, etc for metrics lookups';
COMMENT ON COLUMN engagement_log.metrics IS 'JSON: {impression_count, like_count, reply_count, retweet_count, click_count}';

-- =============================================================================
-- TABLE: hitl_sessions
-- n8n Wait node HITL resume sessions - maps callback IDs to workflow resume URLs
-- =============================================================================
CREATE TABLE IF NOT EXISTS hitl_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  callback_id VARCHAR(100) UNIQUE NOT NULL,
  execution_id VARCHAR(255) NOT NULL,
  resume_url TEXT NOT NULL,
  workflow_name VARCHAR(255),
  status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','resolved','timeout','cancelled')),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

COMMENT ON TABLE hitl_sessions IS 'n8n Wait node HITL resume sessions - maps callback IDs to workflow resume URLs';
COMMENT ON COLUMN hitl_sessions.callback_id IS 'Unique ID embedded in Telegram inline keyboard callback_data';
COMMENT ON COLUMN hitl_sessions.resume_url IS 'n8n webhook URL to POST to in order to resume the waiting workflow';
COMMENT ON COLUMN hitl_sessions.payload IS 'Context: insight text, draft, topic, notionBlockId, etc.';

-- =============================================================================
-- INDEXES
-- =============================================================================

-- contacts indexes
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_priority ON contacts(priority);
CREATE INDEX IF NOT EXISTS idx_contacts_x_handle ON contacts(x_handle) WHERE x_handle IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_linkedin_url ON contacts(linkedin_url) WHERE linkedin_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_last_interaction ON contacts(last_interaction_date DESC NULLS LAST);

-- engagement_log indexes
CREATE INDEX IF NOT EXISTS idx_engagement_contact_id ON engagement_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_engagement_created_at ON engagement_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_engagement_action_type ON engagement_log(action_type);
CREATE INDEX IF NOT EXISTS idx_engagement_platform_id ON engagement_log(platform_id) WHERE platform_id IS NOT NULL;

-- hitl_sessions indexes
CREATE INDEX IF NOT EXISTS idx_hitl_callback_id ON hitl_sessions(callback_id);
CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitl_sessions(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_hitl_expires_at ON hitl_sessions(expires_at);

-- =============================================================================
-- TRIGGER: auto-update updated_at on contacts
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contacts_updated_at
  BEFORE UPDATE ON contacts
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- FUNCTION: cleanup_expired_hitl_sessions
-- Purge hitl_sessions rows that expired more than 7 days ago.
-- Call via pg_cron or a scheduled n8n workflow:
--   SELECT cleanup_expired_hitl_sessions();
-- =============================================================================
CREATE OR REPLACE FUNCTION cleanup_expired_hitl_sessions()
RETURNS void AS $$
BEGIN
  DELETE FROM hitl_sessions WHERE expires_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VERIFICATION QUERIES (commented out - run manually to confirm schema)
-- =============================================================================
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT COUNT(*) FROM contacts;
-- SELECT COUNT(*) FROM engagement_log;
-- SELECT COUNT(*) FROM hitl_sessions;
