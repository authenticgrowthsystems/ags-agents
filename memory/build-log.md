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
