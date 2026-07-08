# RAPORT do Managera AGS - sesja 06-08/07/2026 (BE)

**Gałąź:** claude/silly-blackwell-dfc32d (worktree lokalny: sb-work). **HEAD:** 832206a.
**Baza porównania:** ffa9360 (master prompt 06/07). **29 commitów.** Wszystko py_compile OK.
**Weryfikacja:** `git log --oneline ffa9360..HEAD` + deploye per rebuild cm-agent (curl /health ok).

Manager: proszę porównać z zadaniami zleconymi (#75, #71, backlog a-o) i wymaganiami zgłaszanymi
przez Tomasza w trakcie. Poniżej ZLECONE vs DOSTARCZONE + statusy + dowody.

---

## 1. ZADANIA ZLECONE FORMALNIE

### Task #75 - Voice Bible v2.1 deploy (Manager, termin 07/07 wieczór) - ✅ WYKONANE
Sekwencja 6 kroków z pliku:
- Krok 1 voice_bible->v2.1 (version 2->3, md5 3d745ba9): **db/017** (ffd995d), dollar-quoted,
  idempotentny. Zweryfikowane na produkcji (UPDATE 1, version=3).
- Krok 2 brand_config_history (2->3, manager-ags): ✅ (INSERT 0 1).
- Krok 3 agent_prompts RE_INTRO_LINE_PROMPT: ✅ (INSERT 0 1). UWAGA: app CM NIE czyta agent_prompts -
  to rejestr kanoniczny; egzekucja compliance w kodzie.
- Krok 4 cache: automatyczny (voice_bible czytany LIVE, brak cache) - brak akcji.
- Krok 5 Notion mirror: automatyczny (brand_config w sync_registry).
- Krok 6 test 3 postów: Re-Intro check kodowy (85e7084) = WARN+log faza 1 (decyzja Tomasza: nie
  hard-block przed 1. postem; hard-block po weryfikacji). W testach wyszło, że generacja nie zawsze
  wplatała Re-Intro -> **wzmocniono** jawną instrukcją w CHANNEL_GUIDE (fcdb932).
- Dowód luki dokumentacji: brand_config/history NIE były w repo -> dopisano **docs/db/SCHEMA_ags_crd.md**.

### Task #71 - Notion->PG SSOT (kontynuacja) - ✅ CLOSED + Zadanie 1
- #71 formalnie CLOSED 06/07 (3 dni przed terminem): drift.log OK, sync_queue bez failed, 24h clean.
- Sync Zadanie 1: `agent_prompts` enabled w sync_registry (brand_config + manager_daily_log + agent_prompts).
- ZOSTAJE: Zadania 2-6 (agent_approval_gates -> ... ) wg SYNC_ENABLE_PLAN, gdy potrzeba (channels
  jeszcze NIE w sync - do rozważenia przy widoczności zasad kont w Notion).

### Backlog a-o (z masterpromptu 06/07)
- (b) meldunek publikacji PO CALLBACKU nie przy delegacji - ✅ 05ce8c7 (+reconcile_publications,
  timeout zwis). ZWERYFIKOWANE w AGS Alerts (cały dzień „wysłał->opublikował" per kanał).
- (d) nagłówek dnia na kartach + „karty jutro/dzis" - ✅ 04e9f62.
- (o) reschedule_material (przesuwanie slotu z rozmowy) - ✅ d8146b7.
- (e) Idea Bot intencje - SPEC docs-first (2f0c6b7); wykonanie = n8n (patrz sekcja 4).
- (a) X obraz w tweecie - rozwiązany pośrednio: fix (b) surfacuje realny wynik; osobno LinkedIn slot
  rozjazd naprawiony (niżej).

---

## 2. WYMAGANIA ZGŁOSZONE PRZEZ TOMASZA W TRAKCIE (feedback-driven) - DOSTARCZONE

| Zgłoszone przez Tomasza | Dostarczone | Commit |
|---|---|---|
| „CM to nie realny dialog, zero propozycji" | CM = partner strategiczny + **pętla agentowa** (tool_result wraca do modelu; find_similar -> propozycja+podmiana) | a57fb7d, 837c590 |
| Podmiana bliskiego duplikatu zamiast listy | replace_material (podmiana zaplanowanego postu, slot zostaje) | 0b97038 |
| Runda doprecyzowania przed zapisem | prompt: pokaż kąt + spytaj „doprecyzować?" | d6b5623 |
| Personal LinkedIn nie ma ujawniać maszyny | głos per konto (personal=człowiek, strona=firma; voice_note w config) | d7773d4 |
| Subagent ma znać swoje kanały + strategię | D: TWOJE POWIERZCHNIE + STRATEGIA CM w kontekście subagenta | 57417f6 |
| Przegląd pełnej treści + edycja u subagenta | subagent_show_post + subagent_edit_post (+dwuetapowo, deterministyczny „edytuj #id") | fcdb932, 9b87259, be054b5 |
| Odpowiednik PL do przeglądu (komunikacja PL, publikacja EN) | T8: publikuj native EN + review_pl w media; edycja PL->EN | df42119 |
| Komentarz do posta z ANALIZY OBRAZU (per autor) | #3: Claude vision na zrzucie -> komentarz per autor; pamięć engagement | 3a7b0c5 |
| „Przenieść ustalenia z czatu do bazy" | ZASADY KONTA (subagent_remember_rule -> channels.config.rules -> subagent+generacja) | b040379 |
| LinkedIn planowany 10:00 mimo okna US 13-18 | 3 warstwy: planer nie hardkoduje 10:00 + assign_if_needed sync post_queue + cleanup UPDATE 7 | a6e9a85, 8599843 |
| Subagent „halucynował" sloty (KOREKTA: nie, rozjazd danych) | truth-guard slotów; realna przyczyna = pq<->ci desync (naprawione) | 4ee9dfc, 8599843 |
| Realna potrzeba subagenta ginęła w ❌ | needs_human -> log CHANNEL_NEED + przekazanie Tomaszowi | bb0121a |
| Pusta karta „" | guard master_theme<4 | 56a9768 |
| 529 Overloaded gubił propozycję subagenta | max_retries=5 + retry przejściowych błędów (nie failed) | 085ef85 |

---

## 3. TESTY SUBAGENTÓW (plan + wyniki iteracyjnie z Tomaszem)
Docs: SUBAGENT_TEST_PLAN_07072026.md + SUBAGENT_TEST_RESULTS_07072026.md (T1-T12).
- ✅ DZIAŁA: T1 świadomość kanałów, T3 generacja ad-hoc (znakomity post), T4 sloty, T5 publikacja+callback,
  T8 język (PL komunikacja default + publikacja per platforma), T12 dialog. T2 przegląd+edycja i
  T8b dwujęzyczność - ZBUDOWANE i potwierdzone.
- ❌->BUDOWA: T6 multimedia (decyzja: DEDYKOWANE subagenty grafiki/wideo/głosu, nie media w subagencie
  kanału); T9 comment-radar z wizji (ZBUDOWANE cm-agent; routing obrazu = n8n follow-up).
- Negocjacja X<->CM (rozszerzenie siatki do 14/16/18/20/22, jitter) zadziałała wzorcowo (subagent
  egzekwuje, strategiczne eskaluje do CM, CM zatwierdza+wpisuje config).

---

## 4. OTWARTE / ODŁOŻONE / ZABLOKOWANE
- **n8n: zdjęcie do aktywnego agenta, nie do Idea Bota** - SPEC gotowy (SPEC_PHOTO_ROUTING_ACTIVE_AGENT_
  08072026.md, 832206a); wykonanie = patch AGS HITL Handler v1.0 (240 węzłów, AP-301, tap-test) - następna sesja.
- **Idea Bot intencje (e)** - spec gotowy; ten sam patch n8n.
- **Dedykowane subagenty wizualne (grafika/wideo/głos + awatar + klon głosu ElevenLabs)** - osobny agent
  (chip task_324d9ea5), RESEARCH-FIRST (VISUALIZATION_BRANCH_MASTERPROMPT_07072026.md).
- **ZABLOKOWANE zewnętrznie:** aktywacja stron LinkedIn (AGS/TNM/RDC) + metryki LinkedIn = App 2 CMA;
  X read API (comment radar auto / metryki) = płatny tier - decyzja kosztowa Tomasza.
- **Sync #71 Zadania 2-6** - gdy potrzeba widoczności w Notion (channels do sync_registry).
- **Deploy pending:** b040379 (zasady) + 085ef85 (529) czekają na rebuild.

---

## 5. CONTENT / BIP (build-in-public zadziałał E2E)
Opublikowano na X (+LI-profil) klaster o wnętrznościach agentów/obserwowalności (m.in. „One agent, one
decision, one verifiable output", „agent goes silent / observability", „Architektura: logi i observability
fundament") - bezpośrednio z naprawy (b). Stan awaryjny 24h sam poukładał zaległości. Bohater BIP = zasada
„agent raportuje rzeczywistość, nie intencję".

## 6. UWAGI DLA MANAGERA
- Dokumentacja schematu bazy była LUKĄ (tabele bazowe bez DDL w repo) - naprawione docs/db/SCHEMA_ags_crd.md;
  REGUŁA: każda zmiana DDL = aktualizacja tego pliku (Tomasz ostro to podkreślił).
- Lekcja jakości: diagnoza z DOWODU (join pq<->ci), nie z jednej tabeli - raz orzekłem „halucynacja"
  przedwcześnie, skorygowane po dowodzie.
