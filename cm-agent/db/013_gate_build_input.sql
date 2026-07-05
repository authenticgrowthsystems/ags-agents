-- TASK #71 FAZA E (05/07/2026): agent_approval_gates przyjmuje gate_type 'build_input'
-- (BE Briefing Pack z Notion) + kotwica idempotencji notion_page_id.
-- AP-304: CHECK w zywej bazie = research/build/acceptance/model_selection (db researcher 001+005);
-- 'build_input' NIE przechodzi bez tego DDL. Wzorzec DO-blocku = ags-researcher/db/005 (constraint
-- inline/unnamed -> znajdz realna nazwe, drop, add named). Idempotentne.

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
        CHECK (gate_type IN ('research','build','acceptance','model_selection','build_input'));
END $$;

ALTER TABLE agent_approval_gates ADD COLUMN IF NOT EXISTS notion_page_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_aag_notion ON agent_approval_gates(notion_page_id)
  WHERE notion_page_id IS NOT NULL;

SELECT pg_get_constraintdef(oid) FROM pg_constraint
WHERE conrelid = 'agent_approval_gates'::regclass AND conname = 'agent_approval_gates_gate_type_check';
