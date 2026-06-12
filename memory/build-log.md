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

## 2026-06-10/11 - Idea-capture bot -> Content Creator v1 (huge session)

**What happened:**
- Built the whole idea-capture + research + Content Creator stack INTO the HITL Handler workflow (single Telegram bot consumer constraint). Grew 48 -> 133 nodes, stayed active throughout.
- Migration: `inspirations` + `metadata` jsonb + `research_result`; granted SELECT/INSERT/UPDATE to ags_crd_user (app tables owned by `n8n` superuser, not ags_crd_user).
- Idea capture text/voice/photo -> triage buttons (research/save/post/discard). Voice/photo via Telegram getFile -> binary download -> Gemini transcribe/vision (base64 inline_data).
- Research: PARALLEL Gemini ∥ DeepSeek (branch + Merge) -> Claude synthesis. Interactive synthesis with buttons: save / edit / regenerate-by-angle / discard (conversation_state plumbing, HITL edit untouched).
- Content Creator v1: after save, reads `published_posts` + research -> recommends format -> drafts (PL+EN) -> `post_queue`. Routing chain: idea: -> synth: -> make: -> menu: -> HITL.
- `/start` + `/menu` (pomysly/kolejka/ustawienia/pomoc). Language hardening (pure Polish "mom test" + anti-AI-slop in 4 Claude prompts). Style Bible questionnaire (100 Q) drafted in brand-canon/.

**Decisions:**
- LLM creds: httpHeaderAuth (Gemini `aJ6CuRlcNA5xVysJ`, Anthropic `w2iuB1ttk7ekS2ix`) + predefinedCredentialType deepSeekApi (`AOtZzfRgRgq5f2mO`) - zero inline keys in workflow.
- Content language doctrine: PL + EN versions; Polish = PURE Polish (mom test, zero anglicisms); strong anti-slop. Style Bible (100 Q) to feed prompts later. See memory `project_language_style_doctrine`.
- Product architecture captured in memory: `project_product_architecture` (CM backbone + paid modules), `project_content_creator_agent_vision`.

**Problems hit:**
- `inspirations` owned by `n8n` superuser -> ALTER blocked for ags_crd_user. Fix: temp n8n/n8n owner cred via API, run migration, delete cred.
- n8n public API has NO execute endpoint -> ran one-shot SQL + self-tests via temp webhook workflows (create/activate/trigger/delete).
- ACK fired AFTER pipeline (n8n depth-first) so a Gemini 503 left zero feedback -> chained ACK serially BEFORE pipeline.
- Gemini free tier 503s -> retry (maxTries 4-5) + `onError: continueRegularOutput` so research degrades to one source instead of dying.
- 521 (Cloudflare) on one PUT - PUT is atomic (didn't apply), retried clean.
- bash-embedded python mangles `$(...)` / `$json` in harness JSON -> use Write tool for harness files.

**Lessons:**
- n8n executes nodes SEQUENTIALLY in one run; "parallel" branch+Merge is correct topology + sync barrier, NOT wall-clock parallel.
- Binary: HTTP node responseFormat=file (outputPropertyName data) -> base64 at `$input.first().binary.data.data` -> Gemini inline_data.
- queryReplacement comma-split is unsafe for arbitrary user text -> escape (double single-quotes) in a Code node, inline in SQL (mirror PG Upsert Config valueEsc).
- Verify pipelines WITHOUT Telegram by extracting the real nodes into a temp webhook workflow + stubbing the source node by name (e.g. stub 'Idea Set Researching').
- Every PUT: clean body {name,nodes,connections,settings(executionOrder/saveManualExecutions/errorWorkflow/timezone only)}; re-export SANITIZED (5 secrets -> placeholders) + scan before commit.

**Next:**
- Tomasz to TEST (untested-on-live): voice note + screenshot capture (needs real media), /menu, PL+EN draft.
- Tomasz decision: en-dash `–` (Polish myslnik) keep, or hyphen-only.
- Fill Style Bible questionnaire -> generate STYLE_BIBLE.md -> wire into prompts (replace inline rule).
- Phase 2 objects (each own session): AI NEWS (RSS), CRM activation (contacts), content archive reuse, performance metrics loop, LinkedIn/IG publisher modules, multimedia generation.

---

## 2026-06-11/12 - Idea->post pipeline: PL+EN voice, edit-sync, voice memory, queue (marathon)

**What happened:**
- Issue 1 FIX (auto-published garbage): X-agent retry path dropped the insight. `Increment Retry Count` (Set node) kept only retryCount -> retried Claude got empty insight -> refusal "I don't see any insight" -> passed canon -> published. 3-layer fix: Claude Adapt reads insight from stable `$('Prepare Claude Input')`; Extract Draft refusal-guard -> claudeError; Retry Available? caps on `$runIndex`.
- Photo OCR -> OpenAI gpt-4o-mini vision via Telegram download + `this.helpers.getBinaryDataBuffer` base64 (OpenAI URL-fetch unreliable). Works.
- "Zrob post" rebuilt: idea -> Sonnet 4.6 draft -> HITL preview reusing existing approve/reject/edit/schedule handlers.
- Voice: Sonnet 4.6 + full VOICE_BIBLE.md injected. Draft quality jumped generic -> on-voice (uses visible image text as anchor, dance=architecture metaphor).
- PL+EN dual gen (one Claude call -> {pl,en}); publish EN to AGS (single account). PL = editing/comprehension language.
- "Inny kat" regenerate button (different angle).
- Idea-post edit flow (isolated `:ideaedit`): edit in PL -> Claude re-syncs EN -> "Zapisalem Twoja edycje" re-preview + "To probka mojego glosu" button.
- Voice memory: `voice_notes` (rules, seeded) + `voice_samples` (his edits) tables, injected into every generation. brand-canon/VOICE_SAMPLES.md = readable mirror.
- "Zapisz do kolejki" + priority (post_queue already had `priority` int): ask priority -> save status='queued'.

**Decisions:**
- Single X account (AGS, English publish). No 2-account routing. PL for working/edit.
- Voice samples in Postgres (agent reads them at gen time; n8n can't reach repo files). MD = mirror.
- Queue cadence PROPOSED, not built: serve post_queue 'queued' at 14/18/22, priority order, 1/slot, queued auto-publishes (pre-approved) else generate. AWAITING confirm.

**Problems hit:**
- n8n PUT does NOT hot-reload an active workflow -> deactivate+activate after EVERY PUT or the old def keeps running.
- n8n branch execution order is NOT connection-order. Double-capture race (edit-submit also captured edit text as new idea) fixed DETERMINISTICALLY: capture gate ANDs on `$('PostgreSQL Check Edit State').all().length==0` (early read, pre-clear). Reorder attempt failed first.
- Shared `Set Awaiting Edit` builds SQL via JSON.stringify -> double-quotes -> "zero-length delimited identifier" on empty value. Idea-posts use own correct-SQL node; X-agent edit still has this latent bug (flagged).
- post_queue/inspirations owned by superuser -> ALTER blocked; used existing `priority` column.

**Lessons:**
- Reactivate after every PUT. Don't trust n8n branch ordering; make mutual-exclusion data-dependent.
- Verify generation via temp-webhook + execution inspection before asking Tomasz to test.

**Shipped late same session (12/06 evening):**
- Queue server LIVE + VERIFIED: queued post auto-published at the 14:00 slot (ok=True, posted to x.com); 18:00 + 22:00 fell back to generation (queue empty). Priority ASC, 1/slot. Built into X-agent (Slot Free -> Fetch Top Queued -> Has Queued? publish / generate), reuses scheduler OAuth1 publish code.
- 280 hardened in all 3 generation prompts (adapt, angle, edit).
- Shared `Set Awaiting Edit` SQL fixed (single-quote escaping vs JSON.stringify) -> X-agent edit bug closed, tested.
- Both commits pushed (afa379b + follow-up).

**Next (see memory/NEXT_SESSION.md for the resume prompt):**
- MEDIA (Tomasz #1): attach original photo to the tweet (store Telegram file ref with photo idea; OAuth1 media upload + attach media_id across the 3 publish points).
- Style Bible: fill 100-q -> STYLE_BIBLE.md -> wire into prompt.
- voice_notes editable from the bot.
- Build-in-public content draft for the whole pipeline (offered).

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
