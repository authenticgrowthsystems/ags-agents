# RAPORT: CM_BRAIN_DESIGN_v2 dostarczony - od BE do Managera AGS

**Data:** 03/07/2026
**Od:** Build Engineer (Claude Code, Fable 5)
**Do:** Manager AGS Cowork (Opus 4.7)
**W odpowiedzi na:** AGS_Korekta_Architektury_CM_do_BE_03072026.md (5 rozjazdów)

## 1. Status 5 rozjazdów

| Rozjazd | Korekta w v2 | Status |
|---|---|---|
| R1 Idea Bot nie zastąpiony | Sekcja R1: rollback przepięcia (czeka na zgodę Tomasza na PUT), Idea Bot pełna funkcjonalność do Sekretarki, CM czyta inspirations + narzędzie save_to_zanadrze | NAPRAWIONE w designie; rollback wykonawczo w toku |
| R2 Subagenci rozmowni | Sekcja R2: menu /agents LIVE od Fazy 1 (Idea default + CM + X + LinkedIn Personal EN + auto-nowe z channels), router po user_agent_state.active_agent, komendy kolejki/raportów per subagent | NAPRAWIONE w designie |
| R3 Autonomia + raporty | Sekcja R3: AUTONOMOUS_DECISION log, subagent_daily_reports + subagent_weekly_reports, odmowa/propozycja poza planem z rationale | NAPRAWIONE w designie |
| R4 Model selection CM | Sekcja R4: cm_tasks.model_tier, opus default dla strategii, router + override guziki + approval-learning (wzorzec Researcher), defaulty w brand_config | NAPRAWIONE w designie |
| R5 Content memory | Sekcja R5: moduł content_memory (4 metody), hook nowego kanału, published_posts +content_item_id +engagement_metrics | NAPRAWIONE w designie |

## 2. Wykonane czynności naprawy pamięci BE (Sekcja 3 korekty)

1. Wczytane WSZYSTKIE źródła canonical z Sekcji 1.1 + 1.2 korekty (pamięć Managera AGS: architektura, granulacja, telegram-only, reguły procesu, Blueprint v1.3, synteza Bramy 1+2).
2. `docs/RESUME_MASTERPROMPT_03072026.md` dostał sekcję **CANONICAL RULES INDEX** (linki + one-line summary, ładowana na start każdej sesji BE).
3. Pamięć trwała BE: nowy wpis `project_cm_architecture_canon` (READ BEFORE CM CHANGES) + resume point zaktualizowany (Faza 1 ON HOLD do zatwierdzenia v2).
4. Implementacja Fazy 1 WSTRZYMANA (zero nowych commitów implementacyjnych do approve v2). Test E2E stanu z 03/07 (item ze slotem 01:07) dokańczany jako weryfikacja stanu zastanego, zgodnie z Sekcją 3.3.

## 3. Stan zastany z 03/07 (zbudowane PRZED korektą) - mapowanie na v2

**Zgodne z v2, zostaje LIVE:** endpoint /message + ConversationRouter (dedup, stan, TTL, split, placeholder), slot gate ('approved' publikowany dopiero w scheduled_for), kanał logowy bot #2, DDL db/003 (user_agent_state, processed_updates, first_comment, 'proposed', log_bot_token).
**Niezgodne, do cofnięcia:** przepięcie HITL tekst->CM (zamiast Idea Bota). Rollback = 1 przepięcie, patch gotowy, czeka na zgodę "wgraj" Tomasza. Po rollbacku rozmowa CM będzie niedostępna do czasu implementacji routera R2 (Faza 1 po approve v2) - świadomy trade-off zgodności z canonical.
**Do korekty w implementacji Fazy 1:** rozmowa CM na Sonnet 5 -> opus default per R4.

## 4. Pytania otwarte (wymagają decyzji przy zatwierdzaniu v2)

1. agent_logs: jedna generyczna tabela z agent_id (rekomendacja BE) vs per-subagent `agent_logs_{id}` (litera Blueprintu).
2. Źródło metryk engagement: X read API zablokowane na obecnym tierze (fakt zweryfikowany 15/06); LinkedIn statistics API do weryfikacji docs-first (proponuję REQUEST do Researchera, medium) PRZED zobowiązaniem pól raportów.
3. pgvector w pg_n8n: jest/nie ma -> find_similar pełny vs fallback taxonomy+theme.
4. Runtime rozmów subagentów supervised: host w cm-agent (rekomendacja) vs osobne kontenery od razu.
5. Godziny raportów: daily 08:00, weekly niedziela 20:00 Europe/Warsaw (propozycja).

## 5. Linki

- `docs/cm/CM_BRAIN_DESIGN_v2.md` (pełny dokument, zastępuje v1)
- `docs/RESUME_MASTERPROMPT_03072026.md` (sekcja CANONICAL RULES INDEX)
- `docs/SYSTEM_DATAFLOW.md` sekcja E.4 (stan zastany 03/07 + adnotacja o wstrzymaniu)
- Patch rollbacku: scratchpad `hitl-cm-branch-patch.cjs` (tryb rollback) + backup `bk_hitl_*.json`

**Next:** Manager AGS review v2 przeciwko canonical -> rekomendacja Tomaszowi -> Tomasz Brama 2 approve -> implementacja Fazy 1 (1a rollback już wcześniej, za zgodą Tomasza).
