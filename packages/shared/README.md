# Shared

Shared types, utilities, brand canon loaders, anti-pattern screening logic, common LLM client wrappers.

Used by all agents (manager, x-agent, linkedin-agent, future ig-agent / fb-agent).

## Status

Phase 0 - scaffold only.

## What lives here (when implemented)

- `types/` - TypeScript types for common entities (Post, Comment, BrandCanon, AntiPattern, etc.)
- `brand-canon/` - loader utility reads `../../brand-canon/*.md` and parses to typed object
- `anti-patterns/` - screener that checks string against `../../anti-patterns/library.md`
- `llm/` - thin wrapper around Anthropic SDK with default config (model, temperature, max tokens)
- `telegram/` - reusable Telegram bot client for HITL flows
- `analytics/` - common logging interface to per-agent JSON memory

## TODO

- [ ] TypeScript scaffold
- [ ] Brand canon parser
- [ ] Anti-pattern screener
- [ ] Anthropic SDK wrapper with retry + cost logging
- [ ] Telegram HITL helper
