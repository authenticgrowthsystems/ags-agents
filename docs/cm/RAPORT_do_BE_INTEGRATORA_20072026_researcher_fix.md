# RAPORT do BE-INTEGRATORA: galaz researcher-fix GOTOWA do merge (20/07/2026)

Od: BE-RESEARCHER-FIX (sesja rownolegla wg BRIEF_NAPRAWA_RESEARCHERA_20072026)
Pelny raport merytoryczny: docs/cm/RAPORT_do_Managera_20072026_researcher_fix.md

## Co merge'ujesz

Galaz: `claude/badacz-naprawa-d324bd` na origin (baza: sb-work 471b7da, 6 commitow):
- 3f97d90 - naprawa web_search (allowed_callers direct + widocznosc bledow w sources/worker
  + kopia repo n8n-workflows/researcher/web-search.json)
- ab579ae - raport + STATUS briefu
- 4e65278 - 4d: sunday_brief wymusza minimum medium (decyzja Tomasza guzikami)
- e945982, 555d3e2 - aktualizacje raportu (4d, DoD b PASS)

Merge do sb-work (claude/silly-blackwell-dfc32d). Konflikty: nie powinno byc (pliki tykane
tylko przez ta sesje: ags-researcher/app/{sources,worker}.py, cm-agent/app/sunday_brief.py,
n8n-workflows/researcher/web-search.json, docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md,
docs/cm/RAPORT_*researcher_fix.md).

## Stan zastany po tej sesji (WAZNE)

1. ZYWY n8n "Researcher - Web Search" (oxwcD1iuVpn26C1o) juz ZAPATCHOWANY (PUT + deactivate/
   activate wykonane; backup przedpatchowy w scratchpadzie sesji). Kopia repo == zywa definicja
   (zweryfikowane przez API: body/Normalize/Guard/settings match). NIE nadpisuj zywego workflowu
   stara kopia.
2. Kontener ags-researcher PRZEBUDOWANY i LIVE z kodem galezi (docker run standalone
   z ~/ags-agents/ags-researcher, NIE compose). Healthy, DoD a+b przetestowane na zywo.
3. SERWEROWY klon ~/ags-agents stoi na galezi `claude/badacz-naprawa-d324bd` (checkout przy
   rebuildzie). PO MERGE przestaw serwer na docelowa galaz (git checkout + pull), zanim ktos
   zrobi kolejny rebuild z zaskoczenia.
4. cm-agent NIE przebudowany (celowo): zmiana 4d (minimum medium dla sunday_brief) wchodzi
   w zycie dopiero po rebuildzie cm-agenta - osobna, swiadoma decyzja deployowa Tomasza.
5. Stan tygodnia cm_sunday_brief zostal wyzerowany do tap-testu i po tescie ma phase=sent
   (reczny tap nie zajmuje slotu automatu - sobotni automat wg kodu zadziala normalnie).
6. HITL U5pUZjy2yAhR1sWg nietkniety. Zero DDL. Zero zmian w innych adapterach. Zero workflowow
   TEMP pozostawionych w n8n (weryfikacja przez API po sesji: 0).

## Sedno naprawy (1 akapit)

Anthropic ok. konca czerwca wlaczyl w `web_search_20260209` domyslne dynamic filtering
(allowed_callers=code_execution): wywolanie adaptera 15s -> 50-110s + nowe tryby padu; przy
potrojnym polykaniu bledow (Normalize/worker/brak executions) Researcher padal cicho od 28/06.
Fix: `allowed_callers:['direct']` (22-28s) + pelna widocznosc bledow + cost_usd z usage.
Lekcja do anti-patterns: adapter LLM nigdy nie polyka tresci bledu; szczegoly w pamieci
project_researcher_awaria_websearch_20072026.

STATUS = GOTOWE DO MERGE (20/07 ~11:00)
