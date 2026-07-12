# RAPORT do Managera - 12/07/2026: Task #88 IdeaBot dispatcher-level intercept fix

Od: BUILD ENGINEER | Status: **WDROZONE NA PRODUKCJI (n8n LIVE, przed terminem 13/07 12:00)**

## Diagnoza (docs-first, z zywego workflow)

Realne wartosci active_agent (odczytane z Parse Agsel Callback, NIE z briefu - brief zgadywal
'content_manager'/'subagent_x'): **'idea' | 'cm' | 'subagent:<brand>:<channel>'**. Bramka
z 08/07 (Photo Route Decide) kierowala do rozmowy TYLKO subagent:* - active_agent='cm'
wpadal w galaz default = triage Idea Bota. Stad 4 karty "Zlapane" podczas produkcji artykulu.

## Fix (Opcja A, ZERO nowych wezlow - AP-301 safe)

Edycja parametrow 3 istniejacych wezlow HITL (U5pUZjy2yAhR1sWg, 247 wezlow):
- **Photo Route Decide**: 3-drozna logika: subagent:* -> conversation ('skomentuj ostatni
  zrzut'); **cm -> conversation ('przeslalem ci zrzut ekranu (masz go w schowku)')**;
  idea/puste -> triage. Tryb ➕ Media (madd swiezy) dalej ma pierwszenstwo.
- **Is Photo For Subagent?**: warunek 'subagent' -> 'conversation' (wspolna galaz).
- **Photo To Subagent**: jsonBody text dynamiczny z Decide.
+ prompt CM (commit 0dda670): na 'przeslalem ci zrzut' CM pyta JEDNYM zdaniem o intencje
  (dopiac do materialu / publikacja zewnetrzna / inne), chyba ze kontekst juz padl.

Patcher: Temp/ags-media-spike/hitl-88-photo-cm.cjs (backup bk_hitl_task88_*.json).
PUT 200 + deactivate+activate (gotcha n8n) + weryfikacja parametrow: PASSED.

## Tap-test (Tomasz, ~1 min)

1. /agents -> Content Manager -> wyslij dowolny zrzut -> CM (nie Idea Bot!) pyta co z nim zrobic.
2. /agents -> Idea Bot -> wyslij zrzut -> normalne "Zlapane" (triage bez zmian).
3. /agents -> AGS x -> zrzut cudzego posta -> propozycje komentarzy (bez zmian).

Opcja B (osobny @ags_ideabot) = post-M5 per brief, bez zmian.
