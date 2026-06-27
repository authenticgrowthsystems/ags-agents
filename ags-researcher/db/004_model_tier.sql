-- 004: per-job synth MODEL SELECTION tier (27/06/2026). Applied as ags_crd_user; idempotent.
-- The worker writes haiku | sonnet | opus from the REQUEST payload.model_tier (default 'sonnet').
-- The synth model and its cost rates are resolved from this tier (config.TIER_MODELS / MODEL_RATES);
-- the exact + semantic cache is keyed on (query_hash, model_tier) so a re-run at a different tier
-- does not return another tier's cheaper/pricier result.
ALTER TABLE research_jobs ADD COLUMN IF NOT EXISTS model_tier VARCHAR(20) DEFAULT 'sonnet';
