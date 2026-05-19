# Shared - Lightweight TS Utilities

Shared TypeScript code used by `packages/manager/` CLI tools. Reusable parsers, validators, type definitions.

NOT shared by full agents (X Agent / LinkedIn Agent live in n8n, see `n8n-workflows/`). Shared is for CLI tooling.

## Planned modules (build only when needed)

- `brand-canon/` - parser for `../../brand-canon/*.md` to typed object (BrandCanon with positioning, voice, anti-patterns, examples)
- `anti-patterns/` - string screener against `../../anti-patterns/library.md` rules
- `prompts/` - prompt file parser + version bumper logic
- `markdown/` - utilities for markdown parsing common to all packages

## Status

Phase 0 - scaffold only. Build modules when CLI tools in `packages/manager/` need them.

## Why TS not Python

Per decision 19/05/2026 - TypeScript stack chosen for consistency with Node.js ecosystem (n8n custom nodes, Anthropic TS SDK, pnpm monorepo).
