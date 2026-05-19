# n8n Workflows

Version-controlled JSON exports of n8n workflows running on AGS production instance (Mikrus ivy147).

Every published workflow gets exported here. Treat this folder as the source of truth for "what's running in prod."

## Folder structure

- `system/` - cross-cutting workflows (error handlers, monitoring, backups)
- `x-agent/` - X Publishing Agent workflows (built by AA X Agent Builder)
- `linkedin-agent/` - LinkedIn Agent workflows (Phase 2 build)
- `apply-intake/` - GHL Apply Intake + Lead capture flows
- `voice-agent/` - Voice Agent (Pawel RDC) related workflows if any

## Export convention

When a workflow is published in n8n:

1. Export from n8n UI (Settings → Download workflow JSON)
2. **Strip credentials** - n8n exports include credential references. Remove sensitive fields manually before commit
3. Filename: `{workflow-name}-v{version}.json` (e.g., `error-handler-v1.json`, `apply-intake-v1.json`)
4. Update `CHANGELOG.md` in this folder (TODO: create) with what changed

## Currently in prod (per AA AGS update #2, 19/05/2026)

- `system/error-handler-v1.json` - Error Trigger → Telegram alert. TBD export.
- `apply-intake/apply-intake-v1.json` - GHL Webhook POST → Notion Lead DB → Telegram alert. TBD export.

## TODO

- [ ] Export existing prod workflows (system + apply-intake) from n8n UI
- [ ] Add CHANGELOG.md
- [ ] Establish export script in `../scripts/` to automate (curl n8n API → strip creds → write file)
