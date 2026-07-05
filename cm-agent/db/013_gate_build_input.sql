-- TASK #71 FAZA E (05/07/2026): agent_approval_gates przyjmuje gate_type 'build_input'
-- (BE Briefing Pack z Notion) + kotwica idempotencji notion_page_id.
-- AP-304: CHECK w zywej bazie (dowod: pg_get_constraintdef przy 1. probie 05/07) =
-- research/build/acceptance/model_selection/critical_escalation ('critical_escalation' dodal
-- researcher db/007 - 1. wersja tego DDL ja pominela i DO-block sie wycofal na "violated by some
-- row"). Nowy CHECK = PELNA lista zywych wartosci + 'build_input'. Wzorzec DO-blocku = db/005.

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
        CHECK (gate_type IN ('research','build','acceptance','model_selection',
                             'critical_escalation','build_input'));
END $$;

ALTER TABLE agent_approval_gates ADD COLUMN IF NOT EXISTS notion_page_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_aag_notion ON agent_approval_gates(notion_page_id)
  WHERE notion_page_id IS NOT NULL;

SELECT pg_get_constraintdef(oid) FROM pg_constraint
WHERE conrelid = 'agent_approval_gates'::regclass AND conname = 'agent_approval_gates_gate_type_check';
