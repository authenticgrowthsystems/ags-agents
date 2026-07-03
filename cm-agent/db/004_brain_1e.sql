-- CM Brain Faza 1 kroki 1e+1f (03/07/2026, ags_crd). Idempotent. Apply as superuser n8n via SSH.
-- 1e: cm_tasks (ledger model selection, R4). 1f: published_posts + content_item_id/engagement_metrics (R5).
-- 1g (czesc zdecydowana): agent_logs JEDNA generyczna tabela (decyzja Managera 03/07).
-- Tabele raportow (subagent_daily_reports/weekly) CZEKAJA na wynik Researchera o LinkedIn statistics API.

-- 1e) ledger operacji CM per task z tierem modelu
CREATE TABLE IF NOT EXISTS cm_tasks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_type       VARCHAR(40) NOT NULL,   -- conversation|subagent_chat|canonical|variant|compliance|planner|daily_report|weekly_report
  content_item_id UUID REFERENCES content_items(id),
  model_tier      VARCHAR(20) NOT NULL,
  model           VARCHAR(60) NOT NULL,
  tier_source     VARCHAR(20) NOT NULL DEFAULT 'auto',  -- auto|config|override
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  cost_usd        NUMERIC(10,5),
  status          VARCHAR(20) NOT NULL DEFAULT 'done',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cm_tasks_type ON cm_tasks(task_type, created_at);
ALTER TABLE cm_tasks OWNER TO ags_crd_user;

-- 1g czesc) generyczny log decyzji agentow (AUTONOMOUS_DECISION i przyszle typy)
CREATE TABLE IF NOT EXISTS agent_logs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id   VARCHAR(80) NOT NULL,        -- 'AGS:x' (brand:channel) albo 'cm'
  log_type   VARCHAR(40) NOT NULL,        -- 'AUTONOMOUS_DECISION' | ...
  rationale  TEXT,
  context    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_id, log_type, created_at);
ALTER TABLE agent_logs OWNER TO ags_crd_user;

-- 1f) published_posts: link do content_items + metryki (pola metryk per platforma doprecyzuje wynik Researchera)
ALTER TABLE published_posts ADD COLUMN IF NOT EXISTS content_item_id UUID REFERENCES content_items(id);
ALTER TABLE published_posts ADD COLUMN IF NOT EXISTS engagement_metrics JSONB;
CREATE INDEX IF NOT EXISTS idx_published_posts_item ON published_posts(content_item_id);
