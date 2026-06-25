-- Vector add-on for semantic cache. Line 1 needs SUPERUSER (role n8n); lines 2-3 run as table owner ags_crd_user.
-- Run after the extension is installed, OR run all 3 as superuser n8n. Idempotent.
-- After this, set SEMANTIC_CACHE_ENABLED=true in .env and restart the worker.
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE research_jobs ADD COLUMN IF NOT EXISTS query_embedding VECTOR(1536);
CREATE INDEX IF NOT EXISTS idx_research_jobs_embedding ON research_jobs USING hnsw (query_embedding vector_cosine_ops);
