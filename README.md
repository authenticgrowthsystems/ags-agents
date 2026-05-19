# AGS Agents

**Authentic Growth Systems - Agent Factory**

Build in public. Real-time. Zero stock photos, zero "we did this 6 months ago" - everything you see here was built today, this week, this month.

---

## What is this?

This repo is where AGS (Authentic Growth Systems) builds AI agents for solo founders. The goal: prove that a one-person operation can run a multi-agent system that handles content publishing, lead capture, voice conversations, and more.

Agents currently in build:

- **Manager Agent** - orchestrator + brand canon enforcement + decision support
- **X Agent** - autonomous X/Twitter content engine with Telegram HITL approval
- **LinkedIn Agent** - multi-brand content + comment monitoring + DM triage (PL/EN routing)
- **IG Agent** - planned, Phase 3
- **FB Agent** - planned, Phase 3

Voice Agent (Paweł) for Royal Dance Center lives separately in GHL - that's documented in the parent AGS workspace.

---

## Why build in public?

Two reasons:

1. **Proof.** AGS sells AI agent implementation services. If I cannot run agents for my own business, what proof do I have for clients? This repo is the proof.

2. **Content engine.** Every build session generates posts, videos, decisions, lessons learned. Build in public turns the system-building work into marketing reach. No separate content production overhead.

---

## Stack

- **Runtime:** Node.js 22 LTS + TypeScript 5.x
- **Package manager:** pnpm (monorepo workspaces)
- **LLM:** Anthropic Claude (Sonnet 4.6 for reasoning, Haiku 4.5 for high-volume)
- **Orchestration:** n8n self-hosted (v2.5+)
- **HITL approval:** Telegram bots per agent
- **Platforms:** X API v2, LinkedIn (via Closely), Meta Graph API
- **Memory:** JSON files in repo + Notion mirror for human-readable view

---

## Repo structure

```
ags-agents/
├── packages/              monorepo per agent
│   ├── manager/           Agent Factory orchestrator
│   ├── x-agent/           X / Twitter publishing agent
│   ├── linkedin-agent/    LinkedIn content + comment + DM agent
│   └── shared/            shared types, utilities, brand canon loaders
├── prompts/               versioned prompt files per agent (v1.0 → v2.0 etc.)
├── brand-canon/           source of truth for each brand (AGS, TNM, RDC, Personal)
├── memory/                per-agent persistent memory (JSON + learnings.md)
├── anti-patterns/         lessons learned library across all agents
├── skills/                custom Anthropic Skills per agent
├── mcps/                  custom MCP servers if needed (e.g., Closely wrapper)
├── scripts/               one-off scripts (migrations, exports, backups)
├── n8n-workflows/         exported n8n JSON workflows for version control
└── CLAUDE.md              root Cowork mode context
```

---

## Status

| Component | Status | Phase |
|-----------|--------|-------|
| Repo scaffold | DONE | Phase 0 |
| Brand canon centralized | DONE | Phase 0 |
| Anti-pattern library seeded | DONE | Phase 0 |
| Anthropic API setup | TBD | Phase 0 |
| n8n update v2.5+ | TBD | Phase 0 |
| X Agent MVP | TBD | Phase 1 |
| LinkedIn Agent | TBD | Phase 2 |
| IG / FB Agents | TBD | Phase 3 |

---

## Build log

Started: 19/05/2026.

Each significant build session is logged in `memory/build-log.md` with date, decisions made, problems hit, lessons.

---

## License

TBD (likely MIT or Apache 2.0 once stable).

---

## Want updates?

Live tracker: [AGS Build in Public Tracker on Notion](https://notion.so/[TO-BE-ADDED])

X: [@authenticgrowsys](https://x.com/authenticgrowsys) (or your handle)
LinkedIn: [linkedin.com/company/authentic-growth-systems](https://linkedin.com/company/authentic-growth-systems)
