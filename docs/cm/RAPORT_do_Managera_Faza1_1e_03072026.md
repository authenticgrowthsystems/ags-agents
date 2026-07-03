# RAPORT Faza 1 / krok 1e: cm_tasks + router tierów + override + approval-learning - od BE do Managera AGS

**Data:** 03/07/2026. **Status: KOD + GAŁĄŹ n8n GOTOWE (py_compile PASSED, cmtier LIVE w HITL); pełne działanie po DDL 004 + rebuild cm-agent.**

## Co zbudowane
- **`app/tasks.py`** (wzorzec Researcher model_selection): `tier_for(task_type)` czyta LIVE brand_config `cm_tier_<task_type>` (source='config') z defaultami R4 (source='auto'): conversation/planner=opus, canonical/weekly_report/subagent_chat=sonnet, variant/compliance/daily_report=haiku. `log_task` -> ledger `cm_tasks` (tier, model, źródło, tokeny, koszt USD ze stawek). Ledger nigdy nie wywraca produkcji (try/except przed DDL).
- **Wpięte we WSZYSTKIE wywołania LLM CM:** rozmowa CM, rozmowa subagenta, tekst-matka, warianty, compliance-redraft - każde loguje cm_task z content_item_id gdzie dotyczy. `thinking disabled` ujednolicone (podbicie tieru na Sonnet 5 przez config nie włączy niechcący thinkingu).
- **Guziki override (approval-learning):** wiadomość approve materiału ma teraz linię "Model tekstu-matki: <tier>" + rząd 🎚 haiku/sonnet/opus (`cmtier:canonical:<tier>`). Nowa gałąź HITL (5 węzłów, 224 total, PUT+reactivate, zweryfikowana): korekta zapisuje się do **agent_approval_gates** (type 'model_selection', agent content-manager z registry, model_decision jsonb z was_corrected=true) ORAZ do **brand_config cm_tier_<task_type>** (ON CONFLICT version+1) - od następnego zadania nowy tier. Schematy potwierdzone read-only PRZED kodem (agent_registry, agent_approval_gates.model_decision, brand_config upsert z węzła /set).
- **DDL db/004_brain_1e.sql** (do SSH Tomasza): `cm_tasks`, `agent_logs` (JEDNA generyczna tabela per decyzja Managera), `published_posts` +content_item_id +engagement_metrics (przygotowanie 1f). Tabele raportów CZEKAJĄ na wynik Researchera (job 728d02ba) zgodnie z decyzją #2.

## Acceptance criteria (R4)
| Kryterium | Status |
|---|---|
| (a) rozmowa strategiczna -> cm_task tier='opus', wywołanie claude-opus-4-8 | KOD TAK; E2E po DDL+deployu |
| (b) wariant kanałowy na haiku | KOD TAK |
| (c) guzik override zmienia tier + loguje do agent_approval_gates | GAŁĄŹ LIVE; E2E przy następnym materiale |
| (d) /set cm_tier_conversation zmienia default bez deployu | TAK (czytane live per wywołanie) |
| Parking: CM nie automatyzuje wyboru bez nadzoru (Sekcja 4) | TAK (tylko default+config+korekta Tomasza; auto po ~20-30 korektach = osobna decyzja) |

## Commit
Hash w git log (w wiadomości do Tomasza). Skrypt gałęzi: Temp/ags-media-spike/hitl-1e-cmtier.cjs + backup bk_hitl_1e_*.json.

**Next:** DDL 004 + rebuild (Tomasz) -> 1f content_memory (pgvector 0.8.2 potwierdzony; embeddingi do decyzji: OpenAI text-embedding-3-small na istniejącym kluczu). Researcher 728d02ba -> 1g.
