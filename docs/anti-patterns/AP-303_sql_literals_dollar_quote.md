# AP-303: SQL string literals in generated ETL without dollar-quoting

**Caught:** 05/07/2026, BE, task #71 Faza B (canonical-bio INSERT failed live: `syntax error at or near "choreograf"` - hand-escaped only SOME apostrophes; 20 sibling INSERTs passed, so the miss was silent).
**Why bad:** hand-escaping free text is guaranteed to miss quotes eventually; a failed statement inside a multi-statement file does NOT stop the file, so partial loads look successful.
**Correct (canonical, Manager 05/07 - ALL future AGS/client migrations and ETL):** EVERY free-text literal in generated SQL goes through dollar-quoting (`$tag$...$tag$` + `assert tag not in text`) or bind parameters. Verify loads by row-count SELECT, never by absence of visible errors.
**Index:** anti-patterns/library.md
