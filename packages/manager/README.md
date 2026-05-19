# Manager - Lightweight CLI Utilities

This package holds lightweight TypeScript CLI tools used by MANAGER AGS (Tomasz + Cowork) for repeatable tasks. NOT a full autonomous agent.

The actual MANAGER AGS runtime lives in Cowork mode + Notion + AA AGS Core in n8n. This `packages/manager/` is a supplementary toolbox.

## Planned utilities (when needed)

- `generate-content-draft` - takes a build session note, outputs X + LinkedIn + article draft (3 formats per BIPCL doctrine)
- `brand-canon-screen` - validates a string against `../../brand-canon/ags.md` rules (em dash detection, anti-pattern matching)
- `prompt-version-bump` - automates bumping `prompts/{agent}/system_v{N.N}.md` with changelog entry
- `notion-export` - exports a Notion page to markdown into `memory/` (for offline reference)

## Status

Phase 0 - scaffold only. Build utilities one at a time, only when manual workflow becomes painful.

## Why not full agent code

MANAGER role is strategic + brand enforcement + content draft + brake on heavy decisions. That work happens in Cowork mode (Claude as MANAGER AGS) + AA AGS Core (operational in n8n). Coding MANAGER as TypeScript runtime would duplicate Cowork + AA AGS work.

Lightweight CLI tools = useful complement for repeatable tasks. Full TS agent = waste.
