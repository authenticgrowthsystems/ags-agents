-- 003: relax heterogeneous / LLM-emitted columns to honest types (applied 26/06/2026 as ags_crd_user).
-- WHY:
--  * evidence_items.freshness  - sources emit human strings (web_search page_age = "3 days ago" / a date),
--                                not parseable timestamps -> TIMESTAMPTZ insert would crash the job.
--  * claims.supporting_evidence / options.supporting_claims - these are LLM-emitted references, NOT
--    guaranteed to be valid DB UUIDs (and options.supporting_claims references claims that have no id
--    in the synth schema at all) -> UUID[] insert would crash. TEXT[] keeps the provenance verbatim.
-- Tables are empty at apply time, so the USING casts are trivial. Safe to re-run.
ALTER TABLE evidence_items ALTER COLUMN freshness          TYPE TEXT   USING freshness::text;
ALTER TABLE claims         ALTER COLUMN supporting_evidence TYPE TEXT[] USING supporting_evidence::text[];
ALTER TABLE options        ALTER COLUMN supporting_claims   TYPE TEXT[] USING supporting_claims::text[];
