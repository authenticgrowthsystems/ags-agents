-- 020 (12/07/2026, task #87): execution_mode 3-poziomowy per cel + agent_learning_log (petla nauki).
-- Canonical Tomasza 12/07 (Q2): supervised / semi_autonomous / autonomous z learning loopem.
-- KOREKTA do briefu (AP-304): content_items.id = UUID (dowod: materialy 9f341eca...), nie BIGINT.
-- Idempotentny. DDL => wpisy w docs/db/SCHEMA_ags_crd.md w TYM SAMYM commicie (regula 08/07).

ALTER TABLE channels ADD COLUMN IF NOT EXISTS execution_mode VARCHAR(30) NOT NULL DEFAULT 'supervised';
DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'channels_execution_mode_check') THEN
    ALTER TABLE channels ADD CONSTRAINT channels_execution_mode_check
      CHECK (execution_mode IN ('supervised', 'semi_autonomous', 'autonomous'));
  END IF;
END $do$;

CREATE TABLE IF NOT EXISTS agent_learning_log (
    id BIGSERIAL PRIMARY KEY,
    subagent_id VARCHAR(100) NOT NULL,
    brand_id VARCHAR(50) NOT NULL,
    content_item_id UUID REFERENCES content_items(id),
    proposed_content TEXT NOT NULL,
    final_content TEXT,
    diff TEXT,
    correction_type VARCHAR(30) NOT NULL
      CHECK (correction_type IN ('accepted', 'edited', 'rejected', 'replaced')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_learning_log_subagent ON agent_learning_log(subagent_id, created_at DESC);

-- Kontrola
SELECT 'execution_mode' AS co, COUNT(*)::text AS celow FROM channels WHERE execution_mode = 'supervised'
UNION ALL
SELECT 'learning_log', COUNT(*)::text FROM agent_learning_log;
