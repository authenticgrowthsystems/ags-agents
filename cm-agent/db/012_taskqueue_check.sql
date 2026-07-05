-- TASK #71 Faza C (05/07): task_queue CHECKs rozszerzone pod import Notion (mapping K3 APPROVED).
-- Definicje odczytane z pg_constraint (docs-first): dokladamy wartosci, niczego nie zawezamy.
ALTER TABLE task_queue DROP CONSTRAINT IF EXISTS task_queue_task_type_check;
ALTER TABLE task_queue ADD CONSTRAINT task_queue_task_type_check
  CHECK (task_type = ANY (ARRAY['publish','comment','warm','research','generate_media','report','backup','notion_task']));
ALTER TABLE task_queue DROP CONSTRAINT IF EXISTS task_queue_status_check;
ALTER TABLE task_queue ADD CONSTRAINT task_queue_status_check
  CHECK (status = ANY (ARRAY['pending','pending_hitl','auto_deferred','auto_approved','in_progress','done','failed','blocked']));
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='task_queue'::regclass AND contype='c';
