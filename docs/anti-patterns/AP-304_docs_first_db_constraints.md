# AP-304: Generated INSERTs into an existing table without reading its CHECK constraints first

**Caught:** 05/07/2026, BE, task #71 Faza C - TWICE in one day: task_queue (`task_type_check` rejected 'notion_task') and contacts (`icp_tier_check` rejected long source labels "Premium $2K+" vs schema enum 'Premium'). Columns/types were audited, constraints were not.
**Why bad:** CHECK violations kill rows one-by-one in multi-statement files; source-document labels rarely match schema enums verbatim; the load LOOKS like it ran.
**Correct (canonical, Manager 05/07):** before generating INSERTs into ANY existing table, dump `SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='<table>'::regclass AND contype='c'` and map source labels onto allowed values (long labels go to free-text columns); extend a CHECK only via reviewed DDL when the value is semantically new. Record the mapping in the ETL report.
**Index:** anti-patterns/library.md
