# RAPORT Faza 1 / krok: ROLLBACK R1 - od BE do Managera AGS

**Data:** 03/07/2026. **Krok:** rollback przepięcia tekst->CM (korekta R1). **Status: WYKONANY + ZWERYFIKOWANY LIVE.**

## Co zrobione
- PUT na HITL U5pUZjy2yAhR1sWg (status 200) + deactivate/activate (200/200, gotcha n8n) - za zgodą Tomasza (guzik "Wgraj rollback", przed formalnym Brama 2 approve; korekta R1 mówiła "natychmiast").
- Weryfikacja read-only na live snapshocie: `Idea Not Editing?` TRUE -> `Prepare Idea Text` -> `Save Idea` (stary tor triage -> inspirations). Węzły `CM Get Secret` + `CM Conversation Message` zostały w workflow ODŁĄCZONE (użyje ich router 1b).
- Backup pełnego workflow sprzed rollbacku: scratchpad `bk_hitl_rollback_*.json`.

## Acceptance criteria (R1)
| Kryterium | Status |
|---|---|
| (a) Tekst do bota (default) -> triage guziki -> inspirations, jak przed 03/07 | TAK (routing przywrócony 1:1; tor niezmieniony od 02/07) |
| (b) Tekst do rozmowy CM po wyborze w menu | N/D w tym kroku (wchodzi w 1b/1c) |
| (c) save_to_zanadrze w rozmowie CM | N/D (1c) |
| (d) Głos/foto bez zmian | TAK (gałęzie idea_voice/idea_photo nietknięte przez cały cykl) |

## Commit
Brak zmian w repo (operacja czysto n8n). Kontekst udokumentowany w `docs/cm/RAPORT_do_Managera_CM_BRAIN_v2_03072026.md` sekcja 6 (commit d55f377).

**Next:** krok 1b (router active_agent + menu /agents + setMyCommands).
