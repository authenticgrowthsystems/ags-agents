-- 024: model eskalacji + nauki (plan dnia 19/07 krok [2], kanon: eskalacja subagent->CM->Tomasz
-- GUZIKAMI, kazda odpowiedz Tomasza -> nauka, przejscia supervised->semi_autonomous per TYP decyzji).
-- agent_decisions = ledger ustrukturyzowanych decyzji; decision_modes = tryb per (subagent, typ).

CREATE TABLE IF NOT EXISTS agent_decisions (
    id BIGSERIAL PRIMARY KEY,
    subagent_id VARCHAR(100) NOT NULL,        -- 'CM' albo 'AGS:x' itd.
    brand_id VARCHAR(50),
    decision_type VARCHAR(60) NOT NULL,       -- np. 'topic_swap','slot_conflict','mode_transition'
    question TEXT NOT NULL,
    options JSONB NOT NULL,                   -- [{"key":"...","label":"..."}]
    recommendation VARCHAR(40),               -- key rekomendowanej opcji (pierwszy guzik, z gwiazdka)
    context JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
      CHECK (status IN ('pending','answered','auto','expired')),
    answer VARCHAR(40),
    answered_at TIMESTAMPTZ,
    tg_message_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_pending ON agent_decisions(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_type ON agent_decisions(subagent_id, decision_type, created_at DESC);

CREATE TABLE IF NOT EXISTS decision_modes (
    subagent_id VARCHAR(100) NOT NULL,
    decision_type VARCHAR(60) NOT NULL,
    mode VARCHAR(30) NOT NULL DEFAULT 'supervised'
      CHECK (mode IN ('supervised','semi_autonomous')),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(30) DEFAULT 'tomasz',
    PRIMARY KEY (subagent_id, decision_type)
);

-- Kontrola
SELECT 'agent_decisions' AS co, COUNT(*)::text AS n FROM agent_decisions
UNION ALL
SELECT 'decision_modes', COUNT(*)::text FROM decision_modes;
