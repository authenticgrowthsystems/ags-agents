# X Agent - DEPRECATED LOCATION

**This folder is deprecated.** X Agent is built in n8n, not standalone TypeScript.

See actual implementation:
- **n8n workflow JSONs:** `../../n8n-workflows/x-agent/`
- **System prompt:** `../../prompts/x-agent/`
- **Memory + performance:** `../../memory/x-agent/`

X Agent is built and operated by **AA X Agent Builder** in n8n on Mikrus ivy147. Charter v1.2 in Notion (page `349c00c90b93814b8768e028b98f8a91`).

The TypeScript scaffold originally planned here was redundant with the n8n implementation. Decision 19/05/2026: TS code only for lightweight utilities (see `packages/shared/`), not full agents.

This folder can be deleted in next cleanup commit.
