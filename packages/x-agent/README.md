# X Agent

Autonomous X / Twitter publishing agent with Telegram HITL approval.

## Status

Phase 1 - planned start 20-24/05/2026. Builds on AA X Agent Builder Charter v1.2 (Notion: 349c00c90b93814b8768e028b98f8a91), to be updated to v2.0 reflecting build-in-public pivot.

## What this agent does

1. Cron 06:00 daily - generate 5-10 X post variants from:
   - AGS Weekly Intel insights
   - AI weekly digest (Gemini Deep Research)
   - X API trending search results
2. Brand-review each variant against `brand-canon/ags.md` + `anti-patterns/library.md`
3. Send to Telegram bot `@ags_x_agent_bot` for HITL preview
4. Tomasz approves with reaction → agent queues for publish
5. Publish 10:00-16:00 CEST, spaced 30-90 min apart
6. After 24h - pull X analytics, log to `memory/x-agent/performance.json`
7. Weekly: Manager reviews performance, updates brand canon based on what works

## Stack

- Anthropic SDK (TS) - generation + brand review
- n8n - cron + workflow orchestration
- Twitter API v2 (Basic $100/mc or Free tier for MVP testing)
- Telegram Bot API - HITL channel
- JSON memory in `memory/x-agent/`

## TODO

- [ ] TypeScript scaffold
- [ ] Twitter API v2 client wrapper
- [ ] Telegram HITL flow
- [ ] Brand canon loader integration
- [ ] Performance analytics logger
- [ ] System prompt v1.0 in `prompts/x-agent/system_v1.0.md`
