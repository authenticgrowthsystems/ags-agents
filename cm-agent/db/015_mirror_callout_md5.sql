-- TASK #71 FAZA F fix (05/07, test C Tomasza): drift check wykrywal tylko BRAK md5 w callout,
-- nie wykrywal DOPISKOW (XXX obok md5 przechodzilo). Kotwica: md5 pelnego tekstu callouta.
ALTER TABLE sync_mirror_state ADD COLUMN IF NOT EXISTS callout_md5 TEXT;
SELECT column_name FROM information_schema.columns WHERE table_name='sync_mirror_state' ORDER BY ordinal_position;
