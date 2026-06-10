# Changelog - AGS Agents

Format: [version] - date - description per keepachangelog.com spec.

## [Unreleased]
### Planned
- AGS LinkedIn Agent v1 (Etap 2, pending n8n LinkedIn node fix)
- X Agent v1.1: media/image posts
- X Agent Etap 2: auto-comment on selected accounts (Tomasz-approved list only)
- CRD full Notion-to-PostgreSQL sync CLI
- Manager Agent: n8n workflow execution (packages/manager/)
- GHL integration for revenue pipeline automation

---

## [1.0.0] - 2026-05-31

### AGS X Agent v1.0 - Initial Production Release

**Summary:** First production agent in AGS Agent Factory. Automates X posting workflow from Notion queue to publish, with Telegram HITL approval and PostgreSQL CRD logging.

### Added

#### n8n Workflows
- `n8n-workflows/x-agent/ags-x-agent-v1.json` - Main X posting pipeline
  - Cron trigger: daily 09:00 CET
  - Manual trigger for on-demand processing
  - Reads X Content Queue from Notion (page 371c00c90b9381a0bc29e1dc22e5c244)
  - Claude Haiku 4.5 adapter: raw insight to X post (max 280 chars)
  - Brand canon checker: em dash ban, empty enthusiasm screen, char count, fabricated metrics
  - Telegram HITL with inline keyboard (Approve / Reject / Edit)
  - 4h HITL timeout with auto-archive
  - X API v2 publish via OAuth 1.0a (POST /2/tweets)
  - Free tier enforcement: max 5 posts/day
  - Notion status updates: queued to published/rejected/failed/archived
  - PostgreSQL engagement_log INSERT on publish
  - Error alerts to Telegram on every failure

- `n8n-workflows/x-agent/ags-hitl-handler-v1.json` - Telegram callback router
  - Always-on Telegram trigger for callback queries
  - PostgreSQL session lookup (hitl_sessions table)
  - n8n Wait node resume via webhook call
  - /queue command handler: shows daily post count + pending approvals

- `n8n-workflows/x-agent/ags-analytics-v1.json` - Daily metrics digest
  - Daily 10:00 CET cron
  - X API v2 public_metrics fetch per published tweet
  - PostgreSQL metrics update (engagement_log.metrics JSONB)
  - Telegram morning digest: impressions, likes, replies, retweets

#### System Prompts
- `prompts/x-agent/adapter-system-v1.md` - Claude Haiku adapter prompt v1.0
  - AGS brand voice rules embedded
  - Em dash ban enforced (RULE 1)
  - Peer-to-peer tone, no guru posture
  - 3 before/after examples
  
- `prompts/x-agent/brand-canon-check-v1.md` - Claude Haiku brand checker prompt v1.0
  - Structured JSON output schema
  - 8 violation codes with clear definitions
  - Pass/fail examples for few-shot calibration

#### Database
- `scripts/crd-migrations/001_initial_schema.sql` - PostgreSQL 15 CRD schema
  - contacts table: 28 fields per AGS CRD schema v1.0
  - engagement_log table: FK to contacts, JSONB metrics
  - hitl_sessions table: n8n Wait node HITL mechanism
  - 9 performance indexes
  - updated_at auto-trigger on contacts
  
- `scripts/crd-migrations/001_rollback.sql` - Clean rollback

#### Python Helpers
- `packages/shared/crd-helpers/` - PostgreSQL CRD operations
  - contacts.py: get_contact_by_handle, create_contact, update_contact, search_contacts
  - engagement.py: append_engagement, update_engagement_metrics, count_today_posts
  - client.py: CRDClient context manager, get_connection

- `packages/shared/notion-helpers/` - Notion API utilities
  - x_content_queue.py: read_x_content_queue, update_queue_entry
  - crd_sync.py: search_crd_page, append_crd_log_entry
  - client.py: NotionClient with rate limit retry

#### Test Scripts
- `n8n-workflows/x-agent/test-scripts/test-telegram.py`
- `n8n-workflows/x-agent/test-scripts/test-x-api.py`
- `n8n-workflows/x-agent/test-scripts/test-notion.py`
- `n8n-workflows/x-agent/test-scripts/test-end-to-end.py`

#### Documentation
- `n8n-workflows/x-agent/SETUP.md` - Full deployment guide with checklist
- `CHANGELOG.md` - This file

### Architecture Decisions
- **PostgreSQL as CRD primary store** (not Notion DB): Notion API has timeout issues at 200+ records. PostgreSQL on same Docker network as n8n = zero-latency queries.
- **Notion CRD page = documentation only**: operational data in PostgreSQL, Notion page documents the schema.
- **HITL via n8n Wait node + Telegram callbacks + PostgreSQL sessions**: Clean decoupling. Main workflow pauses, HITL handler (separate always-on workflow) resolves the session via n8n's webhook resume mechanism.
- **Claude Haiku 4.5 default**: Cost-optimized for high-volume adapt + check calls. Sonnet 4.6 available as fallback if specified in prompt.
- **Free tier X API only**: 1,500 posts/month = 50/day. Workflow enforces 5/day hard limit (10x safety margin).

### Known Constraints (Etap 1)
- Text-only posts (no images/media - Etap 2 scope)
- No LinkedIn (n8n LinkedIn node broken 2026 - confirmed anti-pattern in library.md)
- No auto-comment, no auto-reply, no cold DM - Tomasz manual per doctrine
- HITL approval required for every post - no autonomous publishing in Etap 1
- Telegram chat ID: must be configured manually post-import (dynamic at runtime)

---

## [0.0.2] - 2026-05-31
### Changed
- Refactored: ags-agents as docs hub, not standalone agents
- Reflects AA hierarchy + n8n runtime

## [0.0.1] - 2026-05-30
### Added
- Initial scaffold Phase 0 foundation (build in public start)
- Repository structure: packages/, prompts/, brand-canon/, anti-patterns/, memory/, n8n-workflows/
- brand-canon/ags.md v1.2
- anti-patterns/library.md (11 entries)
- memory/build-log.md
