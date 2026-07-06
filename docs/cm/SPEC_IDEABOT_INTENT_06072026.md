# SPEC: Idea Bot - rozpoznawanie INTENCJI przed triage (backlog e / kanon 11a)

Status: DO WYKONANIA (n8n, wymaga tap-testu Tomasza). Docs-first przed patchem (AP-301).
Data: 06/07/2026. Autor: BE (autonomia).

## Problem (Tomasz 06/07 ~10:20, zgłoszone 2x)
Idea Bot złapał wiadomość **"Poproszę o raport"** jako pomysł na post i zapytał
"Co z tym zrobić?" (triage guziki -> inspirations). Bot nie rozróżnia:
- **KOMENDA / PROŚBA do systemu** ("poproszę o raport", "pokaż kolejkę", "status") — NIE jest pomysłem
- **POMYSŁ na treść** (właściwy materiał do schowka)

## Gdzie to żyje (ustalone docs-first, 06/07)
Idea Bot = **stary tor w n8n** (NIE cm-agent): `Prepare Idea Text -> Save Idea -> triage -> inspirations`
(patrz DEPLOY_CHECKLIST.md:110, CM_BRAIN_DESIGN_v2.md:34). Triage "Co z tym zrobić?" =
węzeł n8n w gałęzi Idea Bota (router `active_agent == 'idea'/DEFAULT`). cm-agent NIE widzi
tego tekstu (idzie do inspirations, nie na /message CM).

## Rozwiązanie (najmniejsza zmiana, Pareto)
Wstawić **filtr intencji PRZED "Save Idea"/triage** w gałęzi Idea Bota:

### Opcja A (REKOMENDOWANA, zero LLM, tanie, deterministyczne)
Węzeł Code (JS) `Intent Guard` tuż po `Prepare Idea Text`, przed `Save Idea`:
- Jeśli tekst pasuje do wzorca komendy/prośby -> NIE zapisuj jako pomysł; odpowiedz krótko
  "To wygląda na prośbę/komendę, nie pomysł. Jeśli chcesz raport - napisz do Content Managera
  (menu /agents -> CM) albo użyj /raport." i zakończ gałąź (no-op do inspirations).
- W innym razie -> przepuść do `Save Idea` jak dziś.

Wzorzec (PL, case-insensitive), słowa-klucze na POCZĄTKU wiadomości:
```
^\s*(poprosz[eę]|prosz[eę]|daj|pokaż|pokaz|wyślij|wyslij|chc[eę]|potrzebuj[eę])\s+
  (o\s+)?(raport|raportu|status|kolejk|plan|metryk|podsumowanie|zestawienie)\b
```
oraz twarde komendy: `^/(raport|status|plan|kolejka|karty|decyzje|schowek)\b`.
UWAGA: wzorzec ma być WĄSKI (tylko wyraźne prośby o dane systemowe) — false-positive
= utrata prawdziwego pomysłu, gorsze niż false-negative.

### Opcja B (LLM klasyfikator, jeśli A za sztywne)
Węzeł HTTP -> cm-agent nowy endpoint `/classify_intent` (haiku, 1 token: `idea|command`),
albo mały prompt w n8n. Droższe + zależność sieciowa; użyć tylko gdy A da za dużo pomyłek.

## Kroki wykonania (następna sesja z Tomaszem)
1. **Docs-first**: pobierz workflow HITL (read-only, N8N_API_KEY z .env), znajdź węzły
   `Prepare Idea Text`, `Save Idea`, triage; zrzuć `typeVersion` DZIAŁAJĄCEGO węzła Code
   w tym workflow (AP-301 — kopiuj z żywego, nie zgaduj).
2. Wstaw `Intent Guard` (Code, ten sam typeVersion) między Prepare Idea Text a Save Idea;
   podłącz gałąź "komenda" do sendMessage (odpowiedź) i zakończ; "pomysł" -> Save Idea.
3. PUT tylko `{name,nodes,connections,settings przefiltrowane}`; **deactivate+activate** po PUT.
4. Tap-test Tomasza: "Poproszę o raport" -> odpowiedź-przekierowanie (BEZ triage, BEZ wpisu
   w inspirations); prawdziwy pomysł ("pomysł na post o tolerancji w tańcu") -> triage jak dziś.
5. Zaktualizuj anti-patterns jeśli wyjdzie nowy przypadek.

## Ryzyka
- AP-301: nowy węzeł Code z typeVersion z martwego wzorca = ciche przepuszczenie/blok.
- Za szeroki regex = zjada pomysły. Trzymać wąsko; logować odrzucenia do agent_logs
  (log_type='idea_intent_filtered') na czas obserwacji.
