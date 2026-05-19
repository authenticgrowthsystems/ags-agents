# LinkedIn Agent

Multi-brand LinkedIn content + comment monitoring + DM triage agent.

## Status

Phase 2 - planned start 25-31/05/2026.

## What this agent does

1. Multi-brand content generation with PL/EN routing:
   - AGS (English, US/EU/UK)
   - Personal Tomasz (Polish or English depending on audience)
   - TNM (Polish, when brand canon ready)
   - RDC (Polish, when needed)
2. Comment monitoring on monitored authors + Kategoria C posts (per decision 18/05)
3. DM inbound triage - categorize + draft response or escalate to Tomasz
4. Carousels + long-form posts + comment responses
5. SSI score growth tracking

## Pre-requirements

- Closely Starter account active ($49/mc, LinkedIn ↔ GHL bridge)
- `brand-canon/personal.md` written
- `brand-canon/ags.md` already exists
- Kategoria C commenting rules from `memory/project_linkedin_kategoria_c_komentowanie.md`

## Stack

- Anthropic SDK (TS)
- n8n + Closely API
- Telegram (low-risk HITL: comments) + Dashboard (high-risk HITL: DMs, multi-brand posts)
- LinkedIn API via Closely proxy

## TODO

- [ ] TypeScript scaffold
- [ ] Closely API client wrapper
- [ ] Brand routing logic (PL/EN, persona detection)
- [ ] Comment monitoring loop
- [ ] DM triage classifier
- [ ] Carousel generation pipeline
- [ ] System prompt v1.0 in `prompts/linkedin-agent/system_v1.0.md`
