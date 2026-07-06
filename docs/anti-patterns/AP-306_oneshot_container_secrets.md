# AP-306: One-shot container assumes worker-loaded secrets and fails silently

**Anti-pattern (05-06/07/2026, BE, TWICE in two days):**
1. `drift_check` (one-shot `docker run ... python -m app.sync.drift_check`) called `logbot.send` -
   alert went nowhere because `log_bot_token` lives in app_secrets and only the MAIN worker loads it
   at startup (`worker._load_secrets`); the one-shot env has just POSTGRES_DSN.
2. `bulk_polish` (one-shot) called the Anthropic client - every LLM rewrite silently returned the
   original text (exceptions swallowed), reported "DONE" with 1/37 fixed; looked like the filter
   worked when it never ran.

**Why bad:** the failure is INVISIBLE - the tool prints success-shaped output while doing nothing;
wasted run, false confidence, user-facing gap (no alert / no correction).

**Correct:** every `python -m app.<tool>` one-shot MUST load its own secrets from app_secrets at
the top of main() (mirror `worker._load_secrets` for exactly the keys it needs) and FAIL LOUDLY
(print + exit) when a required key is missing. When adding a new one-shot, grep it for
`config.<ANY>_KEY/_TOKEN` usage and cover each. Never assume container env == worker env.
