-- CM Brain Faza 1 krok 1g (04/07/2026, ags_crd). Idempotent. Tabele raportow subagentow (R3).
-- Ksztalt engagement_metrics = ujednolicony JSONB (docs/research/LINKEDIN_STATISTICS_API_2026.md sekcja 4).

CREATE TABLE IF NOT EXISTS subagent_daily_reports (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id             VARCHAR(50) NOT NULL,
  channel              VARCHAR(40) NOT NULL,
  report_date          DATE NOT NULL,
  published_count      INTEGER NOT NULL DEFAULT 0,
  engagement_metrics   JSONB NOT NULL DEFAULT '{}'::jsonb,   -- suma dnia w ujednoliconym ksztalcie
  autonomous_decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
  queue_snapshot       JSONB NOT NULL DEFAULT '[]'::jsonb,
  report_text          TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (brand_id, channel, report_date)
);
ALTER TABLE subagent_daily_reports OWNER TO ags_crd_user;

CREATE TABLE IF NOT EXISTS subagent_weekly_reports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id        VARCHAR(50) NOT NULL,
  channel         VARCHAR(40) NOT NULL,
  week_start      DATE NOT NULL,
  metrics_7d      JSONB NOT NULL DEFAULT '{}'::jsonb,
  best_content    JSONB NOT NULL DEFAULT '[]'::jsonb,
  worst_content   JSONB NOT NULL DEFAULT '[]'::jsonb,
  recommendations TEXT,
  report_text     TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (brand_id, channel, week_start)
);
ALTER TABLE subagent_weekly_reports OWNER TO ags_crd_user;
