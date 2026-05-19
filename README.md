# AGS Agents

**Authentic Growth Systems - Documentation hub + n8n workflow version control + lightweight CLI utilities**

This repo is the source of truth for AGS agent infrastructure. The agents themselves run on Mikrus ivy147 (n8n self-hosted) and Anthropic Console workspaces. This repo holds:

- **Brand canons** (AGS, TNM, RDC, Personal) - the voice + positioning every agent must respect
- **Versioned system prompts** for each agent (audit trail for what changed when)
- **n8n workflow JSON exports** (version control for production workflows)
- **Anti-pattern library** (lessons learned, screened against during agent generation)
- **Build log** (chronological session notes, decisions, problems hit)
- **Lightweight TS utilities** for CLI tasks (brand screening, content drafting, prompt versioning)

What this repo is NOT: a runtime for autonomous agents. The runtime is n8n + AA agent hierarchy.

---

## Agent hierarchy

```
Tomasz Nawrocki (decision maker)
  ↓
MANAGER AGS (Cowork mode - strategist + brand enforcer + brake on heavy decisions)
  ↓
AA - 00 - AGS Core (operational - n8n / GHL / Notion infra builds)
  ↓ ↓
AA X Agent Builder      AA TNM Builder         AA Voice Agent Builder
(X workflows in n8n)    (TNM site + content)   (Pawel RDC voice agent)
```

Each AA agent operates in its own scope. MANAGER AGS coordinates + enforces brand canon. This repo is the shared library they all read from.

---

## Build in public

Every significant build session generates content (X post + LinkedIn post + article excerpt). The infrastructure here IS the product demo for AGS Voice AI Builder + future agent productization. Build in public = sales proof.

Live tracker: [Notion AGS Build in Public Tracker - TBD link]

---

## Stack (production)

- **Runtime:** n8n self-hosted on Mikrus ivy147 (https://ivy147-20147.mikrus.cloud)
- **Database:** PostgreSQL (containerized alongside n8n)
- **Auto-update:** Watchtower (Docker)
- **Monitoring:** Uptime Kuma (http://ivy147.mikrus.xyz:30147) + Telegram alerts
- **LLM:** Anthropic Claude (Haiku 4.5 default, Sonnet for complex tasks) - workspace "AGS", auto-reload $10/$2/$30 cap
- **Telegram bot:** @ags_alerts_bot (Chat ID 2106351328) for alerts + HITL approvals
- **Backups:** Backblaze B2 cloud (rclone v1.74.1) - currently BLOCKED on SSL cert ticket
- **CRM:** GHL (shared sub-account AGS + RDC)
- **Payments:** GHL Payments → Stripe (under Royal Dance Company, temporary until US AGS entity)

## Stack (this repo)

- **Language:** TypeScript 5.x (for utilities only)
- **Runtime:** Node.js 22 LTS
- **Package manager:** pnpm (monorepo workspaces)
- **Used for:** CLI tools, parsers, screening utilities - NOT full agent runtimes

---

## Repo structure

```
ags-agents/
├── brand-canon/           # Source of truth: AGS, TNM, RDC, Personal voice canons
├── prompts/               # Versioned system prompts per agent (v1.0 → v2.0)
├── n8n-workflows/         # JSON exports of production workflows (version control)
├── anti-patterns/         # Lessons learned across all agents
├── memory/                # Build log + per-agent persistent state
├── skills/                # Custom Anthropic Skills (if we build any)
├── mcps/                  # Custom MCP servers (if we build any)
├── scripts/               # One-off scripts (workflow export automation, migrations)
├── packages/
│   ├── manager/           # Lightweight CLI utilities for MANAGER AGS
│   └── shared/            # Shared parsers / validators
└── CLAUDE.md              # Cowork mode context for this repo
```

---

## Status (19/05/2026)

| Component | Status |
|-----------|--------|
| Repo scaffold | DONE |
| AGS Brand Canon v1.2 centralized | DONE |
| Anti-pattern library seeded (11 entries) | DONE |
| Build log started | DONE |
| n8n production infrastructure | DONE (managed by AA AGS Core, runs on Mikrus) |
| AGS Apply Intake v1 + Error Handler v1 | DONE (published in n8n, JSON export TBD) |
| Wave 0.5 GHL Pipeline Rebuild | IN PROGRESS (Faza 0, Tomasz building products in GHL Payments) |
| X Agent build | PARKED (AA X Agent Builder Charter v1.2, reactivation pending) |
| LinkedIn Agent build | BACKLOG |
| Voice AI Pawel (Royal Dance) | DEPLOYED (separate from this repo, lives in GHL) |

---

## Active priorities

1. **P0 Wave 0.5 GHL Pipeline Rebuild** - 4-tier funnel (Free Guide / $97 / $297 / $2K+). Direct revenue path.
2. **P1 AGS Agent Factory (this repo + AA X Agent Builder reactivation)** - parallel system-as-content track
3. **P2 Free Guide + $97 product content** (PL for TNM, EN for AGS) - feeds Wave 0.5
4. **P3 Backup strategy** - BLOCKED on Backblaze SSL ticket

---

## License

UNLICENSED (private until stable, then likely MIT or Apache 2.0).
