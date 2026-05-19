# LinkedIn Agent - DEPRECATED LOCATION

**This folder is deprecated.** LinkedIn Agent will be built in n8n + Closely integration, not standalone TypeScript.

See actual implementation (when built):
- **n8n workflow JSONs:** `../../n8n-workflows/linkedin-agent/`
- **System prompt:** `../../prompts/linkedin-agent/`
- **Memory + performance:** `../../memory/linkedin-agent/`

LinkedIn Agent will be built post-X Agent validation, in parallel with Wave 0.5 GHL Pipeline Rebuild. Stack: n8n + Closely API + Telegram HITL (low-risk comments) + Dashboard HITL (high-risk DMs, multi-brand posts).

The TypeScript scaffold originally planned here was redundant with planned n8n implementation. Decision 19/05/2026: TS code only for lightweight utilities (see `packages/shared/`), not full agents.

This folder can be deleted in next cleanup commit.
