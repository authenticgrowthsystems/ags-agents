# AGS Researcher - n8n source adapters

The n8n workflows that the AGS Researcher Python worker calls as its multi-source research
backends (cost cascade: `web_search -> firecrawl -> gemini` today; `openai_dr`, `manus` are
fast-follow). Exported sanitized from the live n8n on Mikrus. **READ-ONLY**: every adapter only
reads the world + the DB, never writes.

## Files
| file | webhook (POST) | source |
|---|---|---|
| `web-search.json` | `/webhook/researcher-web-search` | Anthropic `web_search` tool (claude-sonnet-4-6) |
| `firecrawl.json`  | `/webhook/researcher-firecrawl`  | Firecrawl research index (`/v2/search/research/papers`) |
| `gemini.json`     | `/webhook/researcher-gemini-dr`  | Gemini 2.5 Flash + Google Search grounding |

## Chain (identical in every adapter)
`Webhook -> Get Key (Postgres) -> Guard (Code) -> <source HTTP> -> Normalize`
Normalize returns `{status, source, evidence_count, evidence:[{source_url, source_name, content, freshness, authority}]}`.

## Security (no secrets live in these JSON files)
- **API keys** live in DB `app_secrets` (`firecrawl_api_key` / `anthropic_api_key` / `gemini_api_key`).
  The "Get Key" Postgres node reads its key at runtime, so there are **zero key literals** in the JSON.
- **Shared-secret guard**: the same Postgres node also fetches `researcher_webhook_secret`; the Guard
  Code node rejects any request whose `X-Researcher-Secret` header does not match (the worker sends it
  from `app_secrets`). Unauthorized calls are dropped **before** the paid source HTTP call - no spend.
- Execution-data saving is OFF (`settings.saveDataSuccessExecution/ErrorExecution = none`) so keys
  never reach n8n execution logs.

## Import into a fresh n8n
1. Import each JSON.
2. Remap the Postgres credential (nodes reference an instance-specific credential id).
3. Ensure `app_secrets` holds the relevant key rows + `researcher_webhook_secret`.
4. Activate. The worker calls these via `N8N_BASE_URL + /webhook/<path>` with the `X-Researcher-Secret` header.
