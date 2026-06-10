# AGS Agents Build Log

Chronological log of build sessions. Each entry includes: date, what was done, decisions, problems, lessons.

This file is the canonical "what happened when" - update it after every significant session.

---

## 2026-05-19 - Repo bootstrap + strategic pivot

**What happened:**
- Tomasz strategic pivot: "build in public" reframe of system-building work as content engine + revenue activity (not Stage 0-1 anti-pattern)
- Created `ags-agents` GitHub repo (authenticgrowthsystems/ags-agents, public)
- Scaffolded monorepo: packages (manager, x-agent, linkedin-agent, shared), prompts, brand-canon, memory, anti-patterns, skills, mcps, n8n-workflows
- Copied AGS Brand Canon v1.2 to `brand-canon/ags.md`
- Seeded `anti-patterns/library.md` with 11 entries from Voice Agent tests + content + strategic doctrine
- Established CLAUDE.md root for Cowork mode context

**Decisions:**
- Stack: Node.js 22 LTS + TypeScript 5.7 + pnpm monorepo
- License: TBD (UNLICENSED until stable, then likely MIT or Apache 2.0)
- Visibility: public from day 1 (build in public = repo public)
- Build in Public Content Loop (BIPCL): each session output drafted in 3 formats (X + LinkedIn post + article excerpt)
- AA X Agent Builder reactivated from PARKED status, Charter v1.2 → v2.0 to be written

**Problems hit:**
- WebFetch of royaldance.pl/polkolonie returned empty (likely JS-rendered) - resolved by manual screenshot paste from Tomasz
- Sandbox bash cannot git from Windows mount - Tomasz handles git push manually

**Lessons:**
- Surface conflict between current decision and prior doctrine BEFORE executing (Manager AGS caught Stage 0-1 anti-pattern vs pivot today)
- When user gives strategic instruction, check existing inventory (Notion docs, prior agent reports) BEFORE assuming greenfield

**Next:**
- Tomasz: git push initial scaffold from Windows side
- Anthropic API paid credits setup (deadline 15/06)
- AA X Agent Builder reactivation in Notion Build Workspace
- Anti-pattern screening utility in shared package

---

## 2026-05-31 to 06-02 - X Agent v1.0 build + first production deploy

**What happened:**
- Built all 15 deliverables via multi-agent workflow: main n8n workflow JSON, HITL handler, analytics, adapter + brand-canon prompts, PostgreSQL CRD schema (contacts + engagement_log + hitl_sessions), Python helpers (crd + notion), 4 test scripts, SETUP.md, CHANGELOG
- Deployed to Mikrus n8n (ivy147): ran migration SQL, created 6 credentials, imported 3 workflows
- First tweet published end-to-end on @tomasz_ags after long debug chain
- Original architecture: main workflow WAITS at Wait-for-HITL-Response node, HITL handler resumes via webhook-waiting URL

**Decisions:**
- PostgreSQL = primary operational store (Notion = docs only). Notion API timed out as a DB.
- Claude Haiku 4.5 for adapt + brand-canon check (cost). HITL hard gate (no auto-publish in Etap 1).
- Free X API tier, max 5 posts/day enforced.

**Problems hit (the long tail):**
- n8n credentials created via API got `__n8n_BLANK_VALUE__` (silent break) - fix: re-enter via UI
- n8n Code node sandbox blocks `require('crypto')`, `require('https')`, and `fetch()` - all unavailable by default
- Solution: set `NODE_FUNCTION_ALLOW_BUILTIN=crypto,https` in n8n Docker env, then OAuth1 signing works in Code node
- Telegram messages were landing on @ags_alerts_bot (wrong credential tGR43g6h3hJIQ2Fk) instead of @ags_social_bot (cOUqADDFf7oDwlJ0) - two bots, easy to mix
- X API `xOAuth1Api`/`twitterOAuth1Api` credential does NOT extend generic `oAuth1Api` - HTTP Request node rejects it. Worked around with Code-node OAuth1.
- Typographic quotes from generated code broke JS parsing in Code nodes
- webhook-waiting resume only accepts GET, not POST

**Lessons:**
- Credentials live in `AGS_Credentials_Internal.md` (gitignored) - read it, do not SSH-decrypt from n8n DB to rediscover values
- Claude Code must NEVER manually call the webhook-waiting URL - it consumes the webhook before the human clicks, causing 404 in the HITL handler

**Next (became the June rebuild):**
- Eliminate the Wait-node fragility
- Add buttons, edit flow, reject-with-reason

---

## 2026-06-06 to 06-09 - Manus + CM architecture rebuild

**What happened:**
- Manus + Content Manager re-architected the whole agent. See memory `project_x_agent_architecture_10062026` for the full node-level map.
- New shape: main workflow is FIRE-AND-FORGET (no Wait node). It stores everything in `hitl_sessions` and ends. The HITL Handler became the standalone PUBLISHER (Post To X + Save + Notion Mark Published + Telegram Confirm), plus full edit flow and `/queue` command.
- Added Input Guard (blocks empty / literal "undefined" / <3 char), dedup via PostgreSQL Lookup Recent Posts, Claude error handling.
- Schema grew to 9 tables: added `post_queue`, `published_posts`, `brand_config`, `conversation_state`, `inspirations`, `task_queue`. Published tweets now go to `published_posts`, not the old `engagement_log`.
- n8n upgraded 2.22.6 to 2.23.4 (watchtower).

**Decisions:**
- Confirmed direction: PostgreSQL = single source of truth, Notion = read-only mirror. `post_queue` table created as migration target. NOT executed yet (separate project).
- Auto-publish-on-timeout DISABLED (HITL Timeout Checker deactivated) - hard human gate retained.

**Problems hit:**
- Watchtower auto-update wiped `NODE_FUNCTION_ALLOW_BUILTIN` env vars - must persist in the docker run command, not just the running container
- `undefined` leaked into data (one hitl_sessions.callback_id, one published post content) from pre-fix code

**Lessons:**
- Two-sources-of-truth (Notion + Postgres) caused half the bugs (header "Cel" caught as insight, bullet parsing, undefined from block). Drives the Postgres-only direction.

---

## 2026-06-10 - Architecture audit + repo backup + security catch

**What happened:**
- Full read-only audit of production n8n (after Manus temporarily out): mapped both workflows, all 9 DB tables, recent executions. Confirmed agent works end-to-end on cron (08/12/16/20).
- CM fixed the last bug live: `Notion Mark Published` URL built from a bad path (`$('PostgreSQL Lookup Session').item.json[0].payload.notionBlockId` -> undefined, silent Success). Fixed to `$json.notion_block_id_esc`. Agent now self-cleans: publishes, marks [PUBLISHED], removes from Notion queue. 0 of 4 bugs remain.
- P0 backup: exported all 4 production workflows to repo (was 8 days stale), removed junk temp files.
- P1 cleanup: marked 5 zombie pending HITL sessions as expired, verified Input Guard blocks bad input.

**Problems hit:**
- CRITICAL near-miss: production workflow JSONs have secrets HARDCODED (Telegram bot token in HTTP URLs, full X OAuth1 keys in the Post-To-X Code node). Plus N8N_CREDENTIALS_SETUP.md and SETUP.md held live tokens. Repo is public on GitHub. Caught at staging, before any push.

**Decisions:**
- Sanitize all workflow JSONs for git (secrets -> `__PLACEHOLDER__`). Structure is the IP worth versioning; secrets stay in n8n + gitignored credentials file.
- gitignore `.claude/`, `N8N_CREDENTIALS_SETUP.md`, any `AGS_Credentials_Internal.md`.

**Lessons:**
- Before committing exported n8n workflows, ALWAYS scan for hardcoded secrets - n8n Code-node OAuth and direct-API HTTP nodes embed live keys inline.
- Secrets hardcoded in production workflows is a real (non-git) risk too. Future refactor: move them to n8n credentials. Not urgent (n8n instance is private).

**Next:**
- P3a: PostgreSQL source-of-truth migration (repoint Notion Get X Queue to SELECT from post_queue)
- P3c: expand publisher to full "X worker" (feed/buyer-lane, comment proposals, insight gathering)

---

## 2026-06-10 (later) - Auto-publish for HIGH priority enabled

**What happened:**
- Tomasz directive: reduce his clicking to zero, his role = decisions from manager reports, not button-clicking. Future: approval moves to Content Manager.
- Enabled auto-publish but scoped to [HIGH] priority only (his choice from 4 options): HIGH auto-publishes 30 min after preview if not approved; MED/LOW require manual Approve (12h window) and never auto-publish.
- Implementation: threaded `priority` ('high'/'normal'/'low') through Prepare HITL Preview -> Prepare HITL Insert Data -> hitl_sessions.payload. Conditional TTL in PostgreSQL Insert (HIGH=30min, else=12h). Timeout Checker "Fetch Expired Sessions" query filtered to `payload->>'priority' = 'high'`. Activated HITL Timeout Checker (runs every 5 min).

**Decisions:**
- HIGH only for auto-publish (safest insights auto, control retained on rest). Brand canon check already gates BEFORE the session exists, so auto-published content has passed canon.
- TTL: HIGH 30min, MED/LOW 12h manual window.

**Conflict surfaced (per doctrine):**
- CM had disabled auto-publish "until clean cycles." Surfaced to Tomasz; he confirmed proceed given recent clean cycles + Input Guard now blocking the undefined-content bug class. Chose HIGH-only as the safe middle path.

**Lessons:**
- In Prepare HITL Preview, `extractData` is const-scoped inside a try block - cannot reference it in the return. Declare `let priority` at top level, assign inside try (mirror how `topic` is handled).
- n8n public-API PUT rejects `settings.callerPolicy` / `settings.binaryMode` (not in PUT schema). Send only executionOrder/saveManualExecutions/errorWorkflow/timezone; n8n re-applies the rest server-side.

**Next:**
- Watch first HIGH auto-publish cycle. If clean over several days, consider widening or moving approval to Content Manager.
- P3b superseded: auto-publish now live (HIGH); full "CM pre-approves at queue entry" model still future.

---

## Template for future entries

```
## YYYY-MM-DD - [session title]

**What happened:**
- bullet
- bullet

**Decisions:**
- bullet
- bullet

**Problems hit:**
- bullet

**Lessons:**
- bullet

**Next:**
- bullet
```
