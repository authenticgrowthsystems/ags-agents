-- 007: critical-restriction + human-in-the-loop critical escalation (28/06/2026). Applied as ags_crd_user; idempotent.
-- Regula 2 (Manager AGS canonical 28/06): the critical cascade (OpenAI DR + Manus, ~18 PLN/query) is reserved
-- for manager-ags + tomasz-human. Any OTHER agent whose query classifies as 'critical' does NOT run critical
-- and is NOT silently downgraded: the job PARKS (research_jobs.status='awaiting_approval') and Tomasz decides via
-- Telegram buttons -> approve (run critical) or give-medium (run medium). See [[async-event-driven-comms]].
-- NOTE: "tier" here = cascade LEVEL (low/medium/high/critical = which sources + cost), NOT the synth model
-- (haiku/sonnet/opus). The guard limits the cascade level per agent, never the synth model.

-- (1) per-agent allow-list of cascade LEVELS. DEFAULT ['low','medium'] so every NEW agent (CM, Sprzedawca, future
--     autonomous agents) is capped on INSERT and cannot reach the expensive critical cascade without a human gate.
ALTER TABLE agent_registry ADD COLUMN IF NOT EXISTS allowed_model_tiers TEXT[] NOT NULL DEFAULT ARRAY['low','medium'];
UPDATE agent_registry SET allowed_model_tiers = ARRAY['low','medium','high','critical']
 WHERE agent_name IN ('manager-ags','tomasz-human');

-- (2) per-job level override that the HITL decision writes back: 'critical' (approved) or 'medium' (given medium).
--     When set, the worker guard HONOURS it instead of re-evaluating the allow-list (the human already ruled),
--     so the resumed job runs exactly the level Tomasz chose.
ALTER TABLE research_jobs ADD COLUMN IF NOT EXISTS level_override TEXT
    CHECK (level_override IN ('low','medium','high','critical'));

-- (3) a dedicated gate_type for the escalation (keeps the model_selection learning corpus clean for slice 3b) +
--     a JSONB slot for its context. Same robust drop-by-real-name + re-add pattern as db/005 (constraint is
--     inline + unnamed historically; find its real name, drop, re-add a named superset). Idempotent on re-run.
DO $$
DECLARE cname text;
BEGIN
    SELECT conname INTO cname
    FROM pg_constraint
    WHERE conrelid = 'agent_approval_gates'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) LIKE '%gate_type%'
    LIMIT 1;
    IF cname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE agent_approval_gates DROP CONSTRAINT %I', cname);
    END IF;
    ALTER TABLE agent_approval_gates
        ADD CONSTRAINT agent_approval_gates_gate_type_check
        CHECK (gate_type IN ('research','build','acceptance','model_selection','critical_escalation'));
END $$;

-- escalation_detail JSONB shape (critical_escalation gates):
--   { "requesting_agent", "query", "query_hash", "requested_level", "capped_level", "est_cost_pln" }
-- The decision result lands in the existing gate columns (status approved/rejected, approver, approved_at,
-- approval_notes) + research_jobs.level_override. model_selection learning-corpus column stays untouched.
ALTER TABLE agent_approval_gates ADD COLUMN IF NOT EXISTS escalation_detail JSONB;
