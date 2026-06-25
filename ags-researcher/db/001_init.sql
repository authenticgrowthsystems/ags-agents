-- AGS Researcher init schema (applied 23/06/2026 as ags_crd_user on db ags_crd).
-- 3 Phase 0-lite tables + 6 Researcher tables. query_embedding + hnsw live in 002_vector_addon.sql.

CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name    VARCHAR(80) NOT NULL UNIQUE,
    agent_type    VARCHAR(40) NOT NULL,
    role          TEXT,
    model_tier    VARCHAR(40),
    status        VARCHAR(20) NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('planned','building','active','paused','retired')),
    current_gate  VARCHAR(30) NOT NULL DEFAULT 'awaiting_research'
                    CHECK (current_gate IN ('awaiting_research','awaiting_build_approval','awaiting_acceptance','active','paused','retired')),
    last_seen     TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_registry_gate   ON agent_registry(current_gate);
CREATE INDEX IF NOT EXISTS idx_agent_registry_status ON agent_registry(status);

CREATE TABLE IF NOT EXISTS agent_messages (
    message_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent_id  UUID REFERENCES agent_registry(agent_id),
    to_agent_id    UUID REFERENCES agent_registry(agent_id),
    message_type   VARCHAR(20) NOT NULL
                     CHECK (message_type IN ('request','response','notification','escalation','heartbeat','error')),
    payload        JSONB NOT NULL DEFAULT '{}'::jsonb,
    status         VARCHAR(20) NOT NULL DEFAULT 'unread'
                     CHECK (status IN ('unread','read','processing','done','failed')),
    correlation_id UUID,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at        TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_agent_messages_to_status ON agent_messages(to_agent_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_messages_corr      ON agent_messages(correlation_id);

CREATE TABLE IF NOT EXISTS agent_approval_gates (
    gate_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id           UUID NOT NULL REFERENCES agent_registry(agent_id),
    gate_type          VARCHAR(20) NOT NULL CHECK (gate_type IN ('research','build','acceptance')),
    iteration          INTEGER NOT NULL DEFAULT 1,
    status             VARCHAR(20) NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending','approved','rejected','expired')),
    submitted_by       VARCHAR(100),
    submitted_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    research_output    JSONB,
    build_plan         JSONB,
    test_results       JSONB,
    approver           VARCHAR(100) NOT NULL DEFAULT 'tomasz',
    approved_at        TIMESTAMPTZ,
    approval_notes     TEXT,
    rejection_reason   TEXT,
    next_iteration_due TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_aag_agent  ON agent_approval_gates(agent_id);
CREATE INDEX IF NOT EXISTS idx_aag_status ON agent_approval_gates(status);
CREATE INDEX IF NOT EXISTS idx_aag_type   ON agent_approval_gates(gate_type, status);

CREATE TABLE IF NOT EXISTS research_jobs (
    job_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requesting_agent_id UUID REFERENCES agent_registry(agent_id),
    query_text          TEXT NOT NULL,
    query_hash          VARCHAR(64) NOT NULL,
    complexity          VARCHAR(20) CHECK (complexity IN ('low','medium','high','critical')),
    status              VARCHAR(20) NOT NULL DEFAULT 'enqueued',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    cost_pln            NUMERIC(10,4),
    confidence_score    NUMERIC(3,2),
    callback_url        TEXT,
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS research_runs (
    run_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id        UUID NOT NULL REFERENCES research_jobs(job_id),
    source_name   VARCHAR(50) NOT NULL,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    status        VARCHAR(20) NOT NULL,
    raw_output    JSONB,
    cost_pln      NUMERIC(10,4),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS evidence_items (
    evidence_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       UUID NOT NULL REFERENCES research_runs(run_id),
    source_url   TEXT,
    source_name  VARCHAR(50),
    content      TEXT NOT NULL,
    freshness    TIMESTAMPTZ,
    authority    NUMERIC(3,2),
    extracted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID NOT NULL REFERENCES research_jobs(job_id),
    claim_text          TEXT NOT NULL,
    supporting_evidence UUID[] NOT NULL,
    confidence          NUMERIC(3,2),
    conflict_flag       BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS options (
    option_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id            UUID NOT NULL REFERENCES research_jobs(job_id),
    option_label      VARCHAR(50) NOT NULL,
    description       TEXT NOT NULL,
    pros              TEXT[],
    cons              TEXT[],
    supporting_claims UUID[],
    rank_order        INTEGER
);

CREATE TABLE IF NOT EXISTS cost_events (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        UUID REFERENCES research_runs(run_id),
    source_name   VARCHAR(50) NOT NULL,
    api_endpoint  TEXT,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    cost_usd      NUMERIC(10,4),
    cost_pln      NUMERIC(10,4),
    cached        BOOLEAN DEFAULT FALSE,
    timestamp     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_jobs_hash   ON research_jobs(query_hash);
CREATE INDEX IF NOT EXISTS idx_research_jobs_status ON research_jobs(status);
CREATE INDEX IF NOT EXISTS idx_research_runs_job    ON research_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_evidence_run         ON evidence_items(run_id);
CREATE INDEX IF NOT EXISTS idx_cost_events_run      ON cost_events(run_id);
CREATE INDEX IF NOT EXISTS idx_cost_events_ts       ON cost_events(timestamp DESC);

INSERT INTO agent_registry (agent_name, agent_type, role, model_tier, status, current_gate) VALUES
 ('manager-ags','orchestrator','Root orchestrator (interim Cowork)','opus-4-8','active','active'),
 ('researcher','specialist','Cross-cutting multi-source research','sonnet-4-6','building','awaiting_acceptance'),
 ('tomasz-human','human','Human principal',NULL,'active','active')
ON CONFLICT (agent_name) DO NOTHING;
