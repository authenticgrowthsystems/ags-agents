-- 005: SLICE 3 Manager approval-learning tier loop (27/06/2026). Applied as ags_crd_user; idempotent.
-- Manager AGS proposes a synth model_tier per query; Tomasz approves or corrects via Telegram; the decision
-- is logged so that after ~20-30 decisions the Manager can propose per-pattern automation (autonomy earned).
-- See [[manager-decisions-approval-learning]].
--
-- (1) allow a 4th gate_type 'model_selection' on agent_approval_gates. This reuses the existing approval
--     machinery (status pending/approved/rejected/expired, approver, approval_notes, rejection_reason)
--     instead of building a second approval flow.
-- (2) model_decision JSONB = the learning-corpus slot for these gates. Shape:
--     { "query", "query_hash", "complexity", "proposed_tier", "approved_tier",
--       "was_corrected", "rationale", "outcome_cost_pln", "outcome_confidence" }
--     research/build/acceptance gates leave model_decision NULL; model_selection gates leave
--     research_output / build_plan / test_results NULL. Clean separation, clean analytics later.

-- (1) widen the gate_type CHECK. The constraint is inline + unnamed, so find its real name first (robust),
--     drop it, then re-add a named one that includes 'model_selection'. Idempotent on re-run.
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
        CHECK (gate_type IN ('research','build','acceptance','model_selection'));
END $$;

-- (2) learning-corpus slot for model_selection gates.
ALTER TABLE agent_approval_gates ADD COLUMN IF NOT EXISTS model_decision JSONB;
