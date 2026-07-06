# Plan iteracyjnego wlaczania tabel do sync_registry (kolejnosc Managera, 05/07/2026)

**Zasada:** 1 tabela dziennie. **Kryterium enable nastepnej: 24h monitoringu poprzedniej BEZ
drift alertu** (drift cron 03:00 + Telegram bot #2 czyste). Wlaczenie = 1 UPDATE w sync_registry,
zero rebuildu workera. Start: po formalnym CLOSED #71 (06/07 wieczor, 24h clean po cutoverze).

Kontrola przed kazdym enable (SSH):
```
tail -5 ~/ags-agents/cm-agent/logs/drift.log
docker exec pg_n8n psql -U n8n -d ags_crd -c "SELECT status, COUNT(*) FROM sync_queue GROUP BY status;"
```

## Harmonogram (komendy SSH, jedna dziennie)

**Zadanie 1 - 07/07 (pon): agent_prompts** (canonical, rzadka zmiana ale major)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='agent_prompts'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

**Zadanie 2 - 08/07 (wt): agent_approval_gates** (audit trail, append)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='agent_approval_gates'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

**Zadanie 3 - 09/07 (sr): manager_decisions** (append, wazne cross-brand)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='manager_decisions'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

**Zadanie 4 - 10/07 (czw): pricing_tiers** (canonical, sales-critical)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='pricing_tiers'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

**Zadanie 5 - 11/07 (pt): vendor_registry** (canonical, affiliate revenue tracking)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='vendor_registry'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

**Zadanie 6 - 12/07 (sob): roadmap_milestones** (canonical, roadmap public)
```
docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='roadmap_milestones'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"
```

## UWAGA techniczna do zadan 1-6 (BE)
Tabele re_render bez wpisu w page_map uzywaja `notion_page_id` WIERSZA jako celu (fallback w
table_registry). agent_prompts/pricing_tiers/vendor_registry/roadmap_milestones maja kotwice
wierszowe = cel jest. Tabele append (gates/decisions) bez page_map beda logowac 'skipped' dla
NOWYCH wierszy bez notion_page_id - przed Zadaniem 2 i 3 BE dopisze page_map (strona docelowa
dziennika gate'ow/decyzji w Notion) albo handler append-to-row-page. Ocena przy Zadaniu 1.

## Po planie
- Reszta canonical (blueprints/be_contracts/doctrines/playbooks) = bump-only mirror (edycja pliku
  workspace + Postgres; sync jednorazowy po version bump).
- subagent_daily/weekly_reports = high volume, test rate limitow PRZED enable.
- contacts + inspirations = mieszane, po ustabilizowaniu canonical.
- NIGDY nie synchronizowane (parking canonical): agent_session_state, cost_events,
  research_jobs/runs/evidence/claims/options, cm_tasks, task_queue processed rows, app_secrets.
