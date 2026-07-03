# RAPORT Faza 1 / krok 1c: rozmowa CM za menu + save_to_zanadrze + Opus - od BE do Managera AGS

**Data:** 03/07/2026. **Status: KOD GOTOWY (py_compile PASSED), LIVE po rebuild cm-agent (komenda u Tomasza).**

## Co zbudowane (cm-agent)
- **Opus 4.8 dla rozmowy strategicznej (R4):** default CM_CONVERSATION_TIER = 'opus'; tier czytany LIVE per wywołanie z brand_config klucz `cm_tier_conversation` (zmiana przez istniejące `/set cm_tier_conversation sonnet` bez deployu). Pełny cm_tasks + router + override guziki = krok 1e.
- **Narzędzie `save_to_zanadrze` (R1):** pomysł "na później" -> INSERT do inspirations (source='cm_conversation', status='new') BEZ produkcji; wspólna pula z Idea Botem, zasili planer Fazy 2.
- **Kontekst pamięci w rozmowie (zalążek R5):** system prompt dostaje OSTATNIE PUBLIKACJE (5) + licznik ZANADRZA; pełny moduł content_memory (pgvector 0.8.2 potwierdzony przez Managera) = krok 1f.
- **Obsługa active_agent:** /message czyta active_agent z payloadu (fallback: DB); `subagent:*` dostaje uczciwy komunikat "w budowie (1d)" zamiast odpowiedzi w cudzej personie.
- Schematy potwierdzone przed kodem (docs-first): inspirations(source, content, brand, status, metadata) z węzła Save Idea; published_posts NIE ruszane w 1c (kolumny do potwierdzenia przy 1f).

## Acceptance criteria
| Kryterium | Status |
|---|---|
| R1(b) tekst po wyborze CM w menu -> rozmowa CM | KOD TAK; E2E po deployu |
| R1(c) save_to_zanadrze tworzy inspirations row bez produkcji | KOD TAK; E2E po deployu |
| R4(a) rozmowa strategiczna na claude-opus-4-8 | TAK (default opus + live override) |
| R4(d) zmiana tieru bez deployu | TAK (brand_config, /set) |

## Commit
Razem z raportami 1b/1c/rollback w jednym commicie (hash w treści commita widoczny w git log; podany w wiadomości do Tomasza).

**Next:** deploy cm-agent (Tomasz) + tap-test E2E 1b/1c -> krok 1d (rozmowa subagentów). REQUEST do Researchera o LinkedIn statistics API (wymagany PRZED 1g) odpalany równolegle.
