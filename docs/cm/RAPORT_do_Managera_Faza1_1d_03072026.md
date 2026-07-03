# RAPORT Faza 1 / krok 1d: rozmowa subagentów - od BE do Managera AGS

**Data:** 03/07/2026. **Status: KOD GOTOWY (py_compile PASSED), LIVE po rebuild cm-agent.**

## Co zbudowane (cm-agent, conversation.py)
- **Rozmowa per KONTO/CEL** (`active_agent='subagent:<brand>:<channel>'`): persona subagenta z channels.config (konfiguracja celu w prompcie), kontekst = kolejka z numerami pozycji + ostatnie publikacje. Subagent pilnuje granic: propose_material wymuszone na JEGO kanał (target_channels nadpisywane), strategia całości -> odsyła do CM.
- **Komendy deterministyczne (bez LLM):** "kolejka"/"/kolejka" -> lista pozycji z #id, statusem i slotem; "raport"/"/raport" -> raport na żądanie (publikacje + kolejka + decyzje autonomiczne + nota o metrykach w przygotowaniu).
- **Narzędzia edycji kolejki:** `subagent_remove_post` (status->rejected, tylko własny kanał - guard w SQL), `subagent_reschedule_post` (nowy slot w post_queue + synchronizacja content_items.scheduled_for, żeby blokada slotu działała spójnie), `propose_material` ad-hoc (przechodzi przez normalny approve Tomasza - autonomia w ramach bramy).
- **"Wyjaśnij decyzję autonomiczną":** czyta agent_logs (AUTONOMOUS_DECISION); do czasu DDL 1g zwraca uczciwie "log startuje w 1g" (try/except, zero crashy).
- **Historia rozmowy PER AGENT** w jednym czacie (fsm_data.histories[agent]) - wątek CM nie przecieka do subagenta i odwrotnie; TTL 30 min wspólny.
- **Model:** default sonnet dla rozmowy subagenta (rozmowa o kolejce = mid, nie strategia), override live: `/set cm_tier_subagent_chat haiku|sonnet|opus` (decyzja BE do akceptacji Managera przy review - R4 mapowanie mówi haiku dla zarządzania kolejką, wybrałem sonnet dla jakości polszczyzny, tanio zejść jednym /set).

## Acceptance criteria (R2)
| Kryterium | Status |
|---|---|
| (b) wybór X + "pokaż kolejkę" -> pozycje post_queue platform='x' | KOD TAK; E2E po deployu |
| (c) pytanie o ostatnią publikację -> dane z archiwum | KOD TAK (kontekst: ostatnie publikacje z post_queue published) |
| komendy: usuń/przesuń/ad-hoc/wyjaśnij/raport | KOD TAK (raporty cykliczne = 1g) |
| R3 (częściowo): autonomia w ramach approve + rationale widoczne | ad-hoc propose przez bramę TAK; log decyzji = 1g |

## Commit
Hash w git log (podany Tomaszowi w wiadomości). Wymaga rebuild cm-agent (razem z 1c jeśli jeszcze nie wgrane).

**Next:** 1e (cm_tasks + router tierów + override + approval-learning; DDL db/004 do SSH Tomasza). Researcher job 728d02ba (LinkedIn statistics) w toku - wynik przed 1g.
