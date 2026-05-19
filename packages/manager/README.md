# Manager Agent

The orchestrator. Coordinates other agents, enforces brand canon, drafts content from build sessions, escalates strategic decisions to Tomasz.

## Status

Phase 0 - scaffold only. Code TBD.

## What this agent does (when implemented)

- Loads `brand-canon/*.md` and exposes brand-aware generation
- Watches `prompts/` for changes, deploys updates to sub-agents
- Aggregates `memory/*/learnings.md` into cross-agent insights
- Drafts content (X + LinkedIn + article) from session logs
- Escalates conflicts (current decision vs prior doctrine) to Tomasz
- Schedules and rate-limits sub-agent runs

## What this agent does NOT do

- Generate platform-specific content (X Agent / LinkedIn Agent do that)
- Send to platforms directly (sub-agents handle)
- Make heavy strategic decisions without Tomasz approval

## TODO

- [ ] TypeScript scaffold
- [ ] Brand canon loader
- [ ] Anti-pattern screening utility
- [ ] Content draft generator (3-format output)
- [ ] Telegram HITL bridge
