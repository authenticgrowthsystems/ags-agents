-- TASK #71 FAZA F (05/07/2026): sync DB -> Notion one-way. Idempotent.
-- Decyzje Managera (approve 05/07): worker w cm-agent; hybryda re_render/append wg mapy;
-- v1 enabled = brand_config + manager_daily_log, reszta wpisana enabled=FALSE (dolaczenie
-- = UPDATE sync_registry, zero rebuildu). Triggery zalozone na WSZYSTKICH mapowanych tabelach -
-- enqueue i tak sprawdza registry.enabled.

-- (1) rejestr tabel synchronizowanych (wzorzec: nowa tabela = INSERT, wlaczenie = UPDATE enabled)
CREATE TABLE IF NOT EXISTS sync_registry (
  table_name     VARCHAR(80) PRIMARY KEY,
  enabled        BOOLEAN NOT NULL DEFAULT FALSE,
  render_pattern VARCHAR(20) NOT NULL CHECK (render_pattern IN ('re_render','append')),
  priority       INTEGER NOT NULL DEFAULT 5,        -- 1=canonical low-freq, 9=append high-freq
  config         JSONB NOT NULL DEFAULT '{}'::jsonb, -- m.in. page_map: klucz wiersza -> notion_page_id
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE sync_registry OWNER TO ags_crd_user;

-- (2) kolejka zmian (durable ledger; NOTIFY = wake, poll = backstop)
CREATE TABLE IF NOT EXISTS sync_queue (
  id              BIGSERIAL PRIMARY KEY,
  table_name      VARCHAR(80) NOT NULL,
  op              VARCHAR(10) NOT NULL,              -- INSERT|UPDATE
  payload         JSONB NOT NULL,                    -- row_to_json(NEW)
  status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','processing','done','failed','skipped')),
  attempts        INTEGER NOT NULL DEFAULT 0,
  last_error      TEXT,
  next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_sync_queue_pending ON sync_queue(status, next_attempt_at);
ALTER TABLE sync_queue OWNER TO ags_crd_user;

-- (3) stan mirrora per cel (soft-clear z trackingiem: id-y blokow ostatniego renderu,
--     zeby nastepny update podmienil DOKLADNIE swoja sekcje, bez masowych delete)
CREATE TABLE IF NOT EXISTS sync_mirror_state (
  table_name     VARCHAR(80) NOT NULL,
  row_key        TEXT NOT NULL,                      -- np. 'AGS:voice_bible' albo uuid wiersza
  notion_page_id TEXT NOT NULL,
  block_ids      JSONB NOT NULL DEFAULT '[]'::jsonb, -- bloki naszej sekcji mirrora na stronie
  last_checksum  TEXT,                               -- md5 ostatnio zsynchronizowanej tresci
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (table_name, row_key)
);
ALTER TABLE sync_mirror_state OWNER TO ags_crd_user;

-- (4) generyczny trigger enqueue: pisze do kolejki TYLKO gdy tabela enabled w registry; NOTIFY budzi workera
CREATE OR REPLACE FUNCTION ags_sync_enqueue() RETURNS trigger AS $fn$
BEGIN
  IF EXISTS (SELECT 1 FROM sync_registry WHERE table_name = TG_TABLE_NAME AND enabled) THEN
    INSERT INTO sync_queue (table_name, op, payload)
    VALUES (TG_TABLE_NAME, TG_OP, to_jsonb(NEW));
    PERFORM pg_notify('ags_sync', TG_TABLE_NAME);
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

-- (5) triggery na wszystkich mapowanych tabelach (idempotentnie)
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'brand_config','agent_blueprints','be_contracts','agent_prompts','sales_playbook',
    'icp_definitions','content_distribution_rules','pricing_tiers','vendor_registry',
    'roadmap_milestones','channels','contacts','chat_registry','funnel_configs','sales_sequences',
    'agent_contracts','manager_daily_log','manager_decisions','monthly_discovery_reports',
    'subagent_daily_reports','subagent_weekly_reports','agent_approval_gates','inspirations']
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_ags_sync ON %I', t);
    EXECUTE format('CREATE TRIGGER trg_ags_sync AFTER INSERT OR UPDATE ON %I
                    FOR EACH ROW EXECUTE FUNCTION ags_sync_enqueue()', t);
  END LOOP;
END $$;

-- (6) seed rejestru wg mapy Managera (v1 enabled: brand_config + manager_daily_log)
INSERT INTO sync_registry (table_name, enabled, render_pattern, priority, config) VALUES
  ('brand_config', TRUE, 're_render', 1, '{"page_map": {
      "AGS:voice_bible": "38cc00c90b9381049a2cc0e3b669b6ad",
      "AGS:website_canon": "320c00c90b938119bd5ff118ff95b5c8",
      "AGS:footer_canon": "34dc00c90b938140b4b7c4c9870065dd",
      "AGS:ghl_config_subaccount_limitation": "358c00c90b93812cb270f1e5d2e9792d",
      "AGS:ghl_config_dns_pattern": "358c00c90b9381158072f8d70d36e9ca",
      "TNM:ghl_config_isolation_pattern": "34ac00c90b9381a4b967ebb7fff8ab54"}}'::jsonb),
  ('manager_daily_log', TRUE, 'append', 9, '{"page_map": {
      "daily_status": "341c00c90b938130876ef0fce279babc",
      "stan_gry_snapshot": "381c00c90b9381d09a7dc579fbb4dfda"}}'::jsonb),
  ('agent_prompts', FALSE, 're_render', 2, '{}'::jsonb),
  ('agent_approval_gates', FALSE, 'append', 6, '{}'::jsonb),
  ('manager_decisions', FALSE, 'append', 6, '{}'::jsonb),
  ('pricing_tiers', FALSE, 're_render', 2, '{}'::jsonb),
  ('vendor_registry', FALSE, 're_render', 2, '{}'::jsonb),
  ('roadmap_milestones', FALSE, 're_render', 3, '{}'::jsonb),
  ('agent_blueprints', FALSE, 're_render', 2, '{}'::jsonb),
  ('be_contracts', FALSE, 're_render', 2, '{}'::jsonb),
  ('sales_playbook', FALSE, 're_render', 3, '{}'::jsonb),
  ('icp_definitions', FALSE, 're_render', 3, '{}'::jsonb),
  ('content_distribution_rules', FALSE, 're_render', 3, '{}'::jsonb),
  ('channels', FALSE, 're_render', 3, '{}'::jsonb),
  ('contacts', FALSE, 're_render', 4, '{}'::jsonb),
  ('chat_registry', FALSE, 're_render', 4, '{}'::jsonb),
  ('funnel_configs', FALSE, 're_render', 4, '{}'::jsonb),
  ('sales_sequences', FALSE, 're_render', 4, '{}'::jsonb),
  ('agent_contracts', FALSE, 're_render', 4, '{}'::jsonb),
  ('monthly_discovery_reports', FALSE, 'append', 7, '{}'::jsonb),
  ('subagent_daily_reports', FALSE, 'append', 8, '{}'::jsonb),
  ('subagent_weekly_reports', FALSE, 'append', 7, '{}'::jsonb),
  ('inspirations', FALSE, 'append', 8, '{}'::jsonb)
ON CONFLICT (table_name) DO NOTHING;

SELECT table_name, enabled, render_pattern FROM sync_registry ORDER BY priority, table_name;
