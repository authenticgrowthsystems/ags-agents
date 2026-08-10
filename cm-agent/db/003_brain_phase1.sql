-- CM Brain Phase 1 (03/07/2026, ags_crd). Idempotent. Apply as superuser n8n via SSH.
-- Adds: conversation state (user_agent_state), webhook dedup (processed_updates),
-- content_items.first_comment + status 'proposed', app_secrets.log_bot_token (bot #2, log channel).

-- 1) per-chat conversation state (ConversationRouter; FSM in PG per research verdict)
CREATE TABLE IF NOT EXISTS user_agent_state (
  chat_id      BIGINT PRIMARY KEY,
  active_agent VARCHAR(40) NOT NULL DEFAULT 'cm',
  fsm_state    VARCHAR(40) NOT NULL DEFAULT 'idle',
  fsm_data     JSONB NOT NULL DEFAULT '{}'::jsonb,   -- conversation history + pending context
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE user_agent_state OWNER TO ags_crd_user;

-- 2) Telegram update dedup (webhook retries must not double-process; cleaned >24h by the worker)
CREATE TABLE IF NOT EXISTS processed_updates (
  update_id    BIGINT PRIMARY KEY,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE processed_updates OWNER TO ags_crd_user;

-- 3) content_items: first_comment (approved together with the material; published under the post in Phase 3)
--    + status 'proposed' (plan position before plan acceptance; used by the Phase 2 planner)
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS first_comment TEXT;
-- D-008 (03/08/2026): 'handed_off' zastapilo 'dispatching' (AP-312). **D-008b WYKONANE 10/08/2026**
-- (okno potwierdzone dwoma pelnymi cyklami publikacji): stara wartosc zdjeta z ograniczenia,
-- obraz `cm-agent:prev-d008` nie jest juz droga odwrotu.
-- UWAGA: `post_queue.status` ma WLASNA wartosc 'dispatching' i tam ZOSTAJE - inny slownik.
-- Zrodlo prawdy dla tego ograniczenia na produkcji: cm-agent/db/042_status_handed_off.sql.
ALTER TABLE content_items DROP CONSTRAINT IF EXISTS content_items_status_check;
ALTER TABLE content_items ADD CONSTRAINT content_items_status_check
  CHECK (status IN ('proposed','planned','needs_research','researching','drafting',
                    'needs_approval','approved','handed_off',
                    'published','rejected','failed'));

-- 4) log channel: token of the EXISTING alert bot #2 (decision D1). Tomasz pastes the real token
--    in place of the placeholder BEFORE running; never commit the real value.
INSERT INTO app_secrets (key, value)
VALUES ('log_bot_token', '<WKLEJ_TOKEN_BOTA_2>')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
