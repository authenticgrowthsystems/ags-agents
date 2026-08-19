# AI Content Manager - Deployment Playbook (v3)

> **Last verified against the codebase: 19/08/2026.** v2 was written 10/06 and had drifted in two ways
> that would have broken or endangered a fresh install: it told the installer to apply **8** migrations
> when there are **42**, and to set `publish_mode` to a value this project has **banned since 22/07**
> (it ignores scheduling - see AP-307). Both corrected below.
>
> **Rule: when you change publishing behaviour, change this file in the SAME commit.** A stale install
> playbook is worse than none, because it gets followed.

A complete, repeatable path to install this system for a new operator. Written so the installer can walk
a client through it step by step, and so the client understands exactly where their data lives.

Product in one paragraph: a multi-agent content system you operate ENTIRELY from Telegram. A Content
Manager brain (Claude, model selectable per task) discusses ideas with you, keeps an idea stash, writes
platform-native drafts in your brand voice, sends you ONE approve button, publishes at the scheduled slot
through per-account channel subagents (X, LinkedIn - more pluggable), archives every publication with
engagement metrics, files every autonomous decision with a rationale, and pushes daily/weekly reports to
a separate log channel. Every fact lives in one relational PostgreSQL database - so any future interface
(web app, mobile, Slack) reads the same live data.

---

## Part 0 - What you need (summary)

| Need | Required | Who provides |
|------|----------|--------------|
| Linux VPS with Docker (2 GB RAM min, 4 GB rec.) | Yes | Client |
| Domain + HTTPS for webhooks | Yes | Client |
| PostgreSQL 15+ with pgvector (bundled in stack) | Yes | Installer |
| n8n self-hosted (transport layer) | Yes | Installer |
| Anthropic API key (the brain) | Yes | Client |
| OpenAI API key (voice transcription + archive embeddings) | Yes | Client |
| X (Twitter) Developer App, Read+Write | For X publishing | Client |
| LinkedIn Developer App(s) | For LinkedIn | Client |
| Telegram: TWO bots (conversation + log channel) | Yes | Client (5 min with @BotFather) |
| Notion integration | Optional (content source) | Client |

## Part 1 - Client prepares (before install day)

### 1A. Infrastructure
- [ ] VPS with Docker + Docker Compose, SSH access.
- [ ] Subdomain pointed at the VPS with HTTPS (Caddy/Traefik/Cloudflare). Webhooks need public HTTPS.

### 1B. Anthropic (the brain)
- [ ] Account at console.anthropic.com, API key (`sk-ant-...`), billing with a spend cap.
- Models used: Opus (strategy conversation), Sonnet (canonical drafts, subagent chat, weekly analysis),
  Haiku (channel variants, compliance, daily reports). Per-task tier is configurable at runtime and the
  system keeps a cost ledger (`cm_tasks`) - the client sees what every AI call cost.

### 1C. OpenAI (supporting)
- [ ] API key. Used for: Whisper voice-note transcription + text-embedding-3-small (semantic archive search,
  ~$0.02 per 1M tokens - negligible).

### 1D. X (Twitter) Developer App
- [ ] developer.x.com -> Project -> App, permissions **Read and Write** set BEFORE generating tokens.
- [ ] Save: API Key + Secret (consumer), Access Token + Secret (generated AFTER Read+Write), Bearer.
- Note: publishing works on the pay-per-use/free tier; READ endpoints (metrics) may require a paid tier -
  the system supports manual metric entry through chat for X.

### 1E. LinkedIn Developer App(s)
- [ ] App with products: "Share on LinkedIn" + "Sign In with LinkedIn" (publishing to personal profile).
- [ ] For statistics and company pages: apply for the Community Management API product (review takes days
  to weeks). Post statistics scopes: `r_member_postAnalytics` (personal), `rw_organization_admin` (pages).
- [ ] Access token: portal Token Generator (fastest) or 3-legged OAuth (a callback workflow ships with the
  system). Save the member URN (`urn:li:person:...`).

### 1F. Telegram - two bots (5 minutes)
- [ ] @BotFather -> `/newbot` x2: (1) conversation bot - the single window the operator lives in;
  (2) log bot - publish confirmations + scheduled reports, so the conversation stays clean.
- [ ] Copy both tokens EXACTLY (format `1234567890:AA...`, no brackets or spaces around them).
- [ ] Every approver sends `/start` to BOTH bots once; capture their numeric chat_id (getUpdates).

### 1G. Decisions the client makes (become runtime config, all changeable later from chat)
- [ ] Brand voice rules ("voice bible") + banned vocabulary
- [ ] Publication targets - PER ACCOUNT, not per platform (e.g. "LinkedIn personal EN", "LinkedIn company PL"):
      for each - language of publication, posting cadence, metrics mode (api/manual)
- [ ] Language of conversation with the bot (`language_comm`: pl/en/...)
- [ ] Report hours (default: daily 08:00, weekly Sunday 20:00, local timezone)
- [ ] Who approves (chat ids)

## Part 2 - Install (installer runs, ~1 hour)

1. **Docker stack:** n8n + PostgreSQL (with `CREATE EXTENSION vector`) + reverse proxy. Then two worker
   containers built from this repo: `cm-agent` (port 8089) and `ags-researcher` (port 8088, optional
   research module), both on the same Docker network as n8n and Postgres, ports bound to 127.0.0.1.
   Worker `.env` carries ONLY `POSTGRES_DSN` + `N8N_BASE_URL` - no API keys in env files, ever.
2. **n8n env (critical):** `NODE_FUNCTION_ALLOW_BUILTIN=crypto,https` (signed API calls in Code nodes);
   `GENERIC_TIMEZONE` set to client timezone; executions retention (`EXECUTIONS_DATA_MAX_AGE=168`).
3. **Database bootstrap - ONE command:** apply `cm-agent/db/*.sql` **in numeric order, 001 through 042**
   (the count grows - use `ls cm-agent/db/*.sql | sort` rather than a number memorised from this file).
   All migrations are idempotent; together they create the full relational schema: brands, content_items,
   channels, post_queue, published_posts (+embeddings), inspirations, contacts + engagement_log (CRM layer),
   cm_tasks (cost ledger), agent_logs, report tables, user_agent_state, app_secrets, agent_registry,
   sales_pipeline, bulk_operations (+ the research module tables).
   **Then apply `docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql`** - `042` deliberately leaves BOTH
   the old and new status values in the CHECK constraint (it is the record of a migration window);
   only the d008b script narrows the dictionary to what production actually runs.
4. **Secrets onboarding - into `app_secrets` table only** (single source; never in code, env, or workflow
   JSON): anthropic_api_key, openai_api_key, x_consumer_key/secret, x_access_token/secret,
   linkedin_access_token + linkedin_author_urn (+ client_id/secret for OAuth re-auth),
   telegram_bot_token, log_bot_token, researcher_webhook_secret (generate a fresh random guard per install).
   Paste values WITHOUT surrounding brackets/whitespace; verify each with the length+shape check query
   (ships in the repo) before going live.
5. **Import n8n workflows** (from `n8n-workflows/` export set): HITL Handler (the Telegram transport),
   Subagent X Publisher, Subagent LinkedIn Publisher, Scheduler, CM Reports Cron, LinkedIn OAuth Callback.
   For each: swap the two credentials (PostgreSQL, Telegram conversation bot) to the client's, verify the
   webhook paths, then ACTIVATE. Rule: after ANY workflow edit via API - deactivate+activate to refresh
   the live snapshot.
6. **Register targets:** one row in `brands`, one row in `channels` PER publication account with config:
   **`publish_mode` = `post_queue`**, `supervised` (true = under CM), `language_publish`, `stats_mode`
   (manual | member_api | org_api), `secret_prefix` (which token set to use - adding a second LinkedIn page
   = new secrets under a new prefix + one row here, ZERO code changes).

   > **DO NOT set `publish_mode` to `webhook`.** v2 of this playbook did, and it is the single most
   > dangerous line it contained. The webhook path DELEGATES at dispatch and **ignores slots entirely**.
   > On 20/07/2026 that produced, in one hour: 4-5 X posts fired back to back, media lost (the delegate
   > contract has no chunked upload), a Polish post published on an English-only LinkedIn profile, and
   > a callback that marked EVERY row of the item `published` - including rows scheduled hours later -
   > so the database lied about system state. Full account: `anti-patterns/library.md` AP-307.
   > `post_queue` is the mode both live channels use; `draft` (manual paste) stays available per channel.
   >
   > **Since 19/08/2026 the code enforces this, so you cannot get it wrong by following a stale doc**
   > (debt D-020): `config.sprawdz_tryb_publikacji` raises on any attempt to set `webhook` through CM
   > (`target_update`, `target_create`), and channels created by `/brand_add` or `target_create` now
   > default to `draft` instead of `webhook`. Lifting the block is deliberate and lives outside the
   > repo: worker env `PUBLISH_WEBHOOK_ODBLOKOWANY=AP-307-callback-naprawiony` plus a restart.
   > The block covers SETTING the mode - it does not read `channels` rows that already exist, so an
   > install migrating an old database still has to check them:
   > `SELECT brand_id, channel, config->>'publish_mode' FROM channels;`
7. **Seed `brand_config`:** voice_bible, banned_vocab, language_comm, admin_chat_ids, optional per-task
   model tiers (`cm_tier_<task>`).
8. **Telegram wiring:** point the conversation bot webhook at n8n; run setMyCommands sync so the command
   menu matches the active agent.

## Part 3 - Verify (test cycle, before handover)

- [ ] `curl /health` on both workers -> `{"status":"ok"}`; both load secrets from app_secrets on boot.
- [ ] `/agents` in the conversation bot -> menu shows Idea Bot + Content Manager + one entry per channels row.
- [ ] Plain text (no agent selected) -> Idea Bot triage buttons -> row lands in `inspirations`.
- [ ] Switch to Content Manager -> discuss an idea -> confirm with a slot 10 minutes ahead -> draft arrives
      with ONE approve button + model-tier buttons -> approve -> NOTHING publishes early -> at the slot the
      post goes live on every target in its own language -> log bot confirms -> `published_posts` has the row
      with URL and post id.
- [ ] Switch to a subagent -> "kolejka"/"queue" lists items with #ids -> "raport"/"report" returns the
      on-demand report -> reschedule one item -> `AUTONOMOUS_DECISION` row appears in `agent_logs`.
- [ ] Fire `POST /reports/daily` manually -> report rows upserted + pushed to the log bot.

### Safety layers - verify them with BAD input, not by reading the code (AP-314)

Three guards stand between the model and the client's public profile. A guard nobody has seen refuse
anything is an assumption. Each check below takes seconds and is run against the RUNNING container:

- [ ] **Genre guard** - `docker exec cm-agent python -c "from app import compliance as c; print(c.bezpiecznik_gatunku('I have reviewed the canonical text and Voice Bible, strong content.'))"`
      must return a non-empty pair, and a normal sentence must return `([], [])`.
- [ ] **Filter output gate** - `docker exec cm-agent python -c "from app import compliance as c; print(c.PROG_POKRYCIA_FILTRA)"`
      returns the threshold; a model reply that shares almost no words with its input must score near 0.
- [ ] **Learned-rule language filter** - `docker exec cm-agent python -c "from app import generate as g; print(repr(g._learned_style('AGS','en')))"`
      must NOT contain style rules written in another language than the channel publishes in.
- [ ] **Publication time** - approve one item and confirm the bot reports `max(plan slot, queue time)`,
      then confirm the post actually goes out at that time, not earlier.

Why this section exists: on 04/08/2026 a post carrying the model's own review note instead of content
stayed live on a personal LinkedIn profile for six days. It had passed four separate content checks -
each asked a different question, none asked what the text WAS. `docs/anti-patterns/AP-315_*.md`.

## Part 4 - Handover & security (client-facing)

- [ ] **Rotate ALL tokens as post-install step 1** (X portal, LinkedIn token, both Telegram bots via
      BotFather) and update `app_secrets` - the installer must not retain working credentials.
- [ ] Backups: daily `pg_dump` cron with 7-day rotation + weekly copy OFF the server. The database is the
      entire system state - workflows and code are re-importable, the data is not.
- [ ] Show the client the data map (`docs/SYSTEM_DATAFLOW.md` + the data-flow diagram): what is stored in
      which table, what leaves the server (only API calls to Anthropic/OpenAI/X/LinkedIn/Telegram), and that
      secrets live in one table on THEIR server.
- [ ] Known limitation to state honestly: fixed bot labels are Polish today (LLM replies follow
      `language_comm`); full string i18n lands with the first English-first install.

## Part 5 - Day-to-day (what the operator actually does)

Everything from Telegram: talk to the CM about ideas ("save to stash", "what performed best?",
"adapt #12 for LinkedIn"), tap ONE approve per piece, correct the model tier with one tap when you care,
talk to any subagent about its queue, dictate X metrics in chat, read the daily/weekly reports on the log
bot. Two commands an operator will not guess but will need: `wklejone <id>` closes a manual-paste item
from the queue, and `wyszlo <channel> <link>` records a publication that bypassed the system entirely -
without it the daily report says the system published nothing, which is true about the system and false
about the world. No dashboards to log into; the system asks when it needs a decision and stays quiet otherwise.

---

## Appendix A - Credential sheet (fill per install)

```
ANTHROPIC_API_KEY=            OPENAI_API_KEY=
X_API_KEY=                    X_API_SECRET=
X_ACCESS_TOKEN=               X_ACCESS_TOKEN_SECRET=        X_BEARER_TOKEN=
LINKEDIN_ACCESS_TOKEN=        LINKEDIN_AUTHOR_URN=
LINKEDIN_CLIENT_ID=           LINKEDIN_CLIENT_SECRET=
TELEGRAM_BOT_TOKEN=           LOG_BOT_TOKEN=
APPROVER_CHAT_ID(S)=          WEBHOOK_GUARD_SECRET=(generate per install)
POSTGRES_PASSWORD=            SERVER_DOMAIN=
```

## Appendix B - What runs where (inventory per install)

| Piece | Kind | Role |
|---|---|---|
| n8n | container | transport: Telegram webhook, button routing, publish adapters, crons |
| PostgreSQL (+pgvector) | container | THE system state: 30+ relational tables, single source of truth |
| cm-agent | container (Python/FastAPI) | the brain: conversation router, generation, slot loop, reports |
| ags-researcher | container (Python/FastAPI) | optional: 6-source deep research on demand (cost cascade) |
| HITL Handler | n8n workflow | all Telegram in/out + button families |
| Subagent X / LinkedIn Publisher | n8n workflows | per-account publish + archive callback |
| Scheduler + CM Reports Cron | n8n workflows | minute publisher + 08:00/Sunday report triggers |
| LinkedIn OAuth Callback | n8n workflow | 3-legged token exchange for re-auth |
| Lacznik Chat Tools | n8n workflow | optional: MCP tools so an operator's chat can read state and file work reports |
