# CM BRAIN - projekt architektury v2 (03/07/2026)

**Zastępuje CM_BRAIN_DESIGN_v1.md w całości** (pełny dokument z podbitą wersją, reguła full-prompts-versioned).
**Fundament:** v1 (research Gemini+Manus + stan LIVE) + **KOREKTA ARCHITEKTURY od Managera AGS** (`C:\Claude-CoWork\AGS\AGS_Korekta_Architektury_CM_do_BE_03072026.md`) - 5 rozjazdów domkniętych w sekcjach R1-R5.
**Status:** DO ZATWIERDZENIA przez Tomasza (Brama 2 dla mózgu CM). Implementacja Fazy 1 WSTRZYMANA do approve.

## 0. Decyzje wejściowe (obowiązujące)
- n8n = TYLKO transport; logika konwersacji w Pythonie (cm-agent). [v1, utrzymane]
- JEDEN bot interaktywny dla wszystkich agentów + osobny kanał logowy (bot #2, token LIVE w app_secrets od 03/07). [D1 z 02/07]
- Model "jednego approve": dyskusja/plan hurtem -> materiał jednym tapnięciem -> publikacja automatycznie w slocie. [D2 z 02/07]
- Subagent = obiekt per KONTO/CEL z toggle supervised (reguła "bardzo bardzo ważna"). [canonical: reference_subagent_granularity_per_account]
- **Idea Bot żyje** jako niezależny agent do czasu Sekretarki (Blueprint v1.3 hierarchia). [KOREKTA R1]
- **Subagenci są rozmowni** i menu wyboru agentów LIVE od Fazy 1. [KOREKTA R2]
- **Autonomia subagentów + raporty daily/weekly z metrykami.** [KOREKTA R3, Blueprint zasada 4]
- **CM na Opus 4.8 dla strategii, model selection per task z nadzorem Tomasza.** [KOREKTA R4]
- **Pamięć cross-channel z published_posts (reuse na nowe kanały).** [KOREKTA R5, wzorzec Centralized Content Brain]
- **Język komunikacji i język publikacji = dwa osobne ustawienia konfiguracji** (sprzedawalność). [UZUPEŁNIENIE R6, Tomasz 03/07]

## 1. Werdykt z researchu (przejęte z v1, bez zmian)
- Architektura "DB-Queue Distributed": router/gateway cienki, stan FSM i kolejki w PostgreSQL, każdy agent osobnym workerem. Nasz istniejący wzorzec, mózg go rozszerza.
- Biblioteka (gdy powstanie osobny gateway): aiogram 3.x; PTB odpada (issue #5225).
- UX: Reply Keyboard jako stała kotwica + Inline Keyboard do akcji + setMyCommands(BotCommandScopeChat) per czat.
- Konwersacyjny HITL: stany w PG, ForceReply, /cancel i "anuluj" z każdego stanu, TTL resetuje stan.
- Higiena: dedup update_id, split >4096 na akapitach, placeholder edytowany wynikiem.
- Limity Telegram: logi na osobny kanał (bot #2), nigdy do czatu rozmowy.

## 2. Architektura docelowa mózgu (v2)
```
Telegram bot @ags_social_bot (JEDEN interaktywny)
  └─ webhook -> n8n HITL U5pUZjy2yAhR1sWg (TRANSPORT):
       ├─ guziki cm:/crit:/mtier:/ccp:/idea... -> istniejące gałęzie (bez zmian)
       ├─ komenda /agents + guzik "🤖 Zmień agenta" -> menu wyboru -> zapis user_agent_state.active_agent
       └─ TEKST (bez stanu edycji/synth) -> ROUTER po user_agent_state.active_agent:
            ├─ 'idea' (DEFAULT) -> stary tor Idea Bota: Prepare Idea Text -> Save Idea -> triage -> inspirations  [R1]
            ├─ 'cm' -> POST cm-agent /message (ConversationRouter, zbudowany 03/07)
            └─ 'subagent:<brand>:<channel>' -> POST cm-agent /message (kontekst subagenta)  [R2]
  cm-agent (Python, host rozmów supervised):
    ConversationRouter (per active_agent):
      ├─ CM: intencje plan/pokaż/zmień/pomysł/status + swobodna dyskusja (model wg R4)
      │    + narzędzia: propose_material, show_queue, save_to_schowek (inspirations INSERT), content_memory.*
      ├─ Subagent: pokaż/edytuj kolejkę, dodaj ad-hoc, usuń pozycję, wyjaśnij decyzję autonomiczną,
      │    pokaż raport dzienny/tygodniowy (kontekst = kolejka + historia publikacji + agent_logs subagenta)
      └─ odpowiedzi: sendMessage bezpośrednio, placeholder+edit, split 4096
    Planner (Faza 2): cron /plan -> propozycja tygodnia z brand_strategy + channels.config -> pozycje 'proposed'
    content_memory (R5): archiwum published_posts + top-performing + sugestie adaptacji cross-channel
    pętla: claim 'approved' DOPIERO gdy scheduled_for <= NOW() (slot gate, LIVE 03/07)
      └─ dispatch (istniejący kontrakt webhook) -> subagenci -> callback -> potwierdzenie na bot #2 (LIVE 03/07)
    raporty (R3): daily 08:00 + weekly niedziela per subagent -> Telegram push + tabele raportowe
```
Gateway aiogram jako osobny serwis wchodzi przy migracji Managera na serwer; kontrakt /message się nie zmienia.
Rozmowy subagentów supervised HOSTUJE proces cm-agent (wspólny runtime, osobne logiczne konteksty per konto/cel z channels.config). Tryb STANDALONE (własny bot + własna pętla) = osobny runtime, dalsza faza produktu (reference_subagent_product_object_canonical).

## R1. Idea Bot LIVE równolegle z CM (korekta rozjazdu 1, KRYTYCZNY)
**Canonical:** Blueprint v1.3 sekcja 2 (Idea-bot = niezależny agent pod CM; Sekretarka zastępuje Idea-bota w Fazie 2, nie CM); zasada 2 modularność plug-and-play; Tomasz 03/07 "Idea Bot ma żyć".
- **Rollback NATYCHMIAST** przepięcia z 03/07: wyjście TRUE `Idea Not Editing?` wraca do `Prepare Idea Text` (stary tor tekst -> triage -> inspirations). Węzły CM Get Secret / CM Conversation Message zostają w workflow (odłączone) do czasu implementacji routera R2.
- Idea Bot = pełna funkcjonalność (tekst + głos + foto -> triage -> inspirations pool) do Fazy 2 Blueprintu (Sekretarka LIVE).
- CM CZYTA inspirations pool (planner Fazy 2 + narzędzie rozmowy "pokaż schowek"), NIE zastępuje mechanizmu zapisu.
- "Dyskusja o kącie" w rozmowie CM = DODATKOWA funkcjonalność dostępna po przełączeniu na CM w menu, nie substytut Idea Bota. Rozmowa CM dostaje też narzędzie `save_to_schowek` (INSERT do inspirations bez uruchamiania produkcji).
**Acceptance criteria:** (a) tekst do bota bez przełączania (default 'idea') -> triage guziki -> wiersz w inspirations, zachowanie identyczne jak przed 03/07; (b) po wyborze CM w menu tekst idzie do rozmowy CM; (c) "zapisz do schowka" w rozmowie CM tworzy inspirations row; (d) głos/foto działają bez zmian.

## R2. Subagenci rozmowni per KONTO + menu wyboru LIVE od Fazy 1 (korekta rozjazdu 2, KRYTYCZNY)
**Canonical:** Tomasz 03/07 "z każdym z subagentów muszę mieć możliwość porozmawiać i sprawdzić co mają w kolejce"; reference_subagent_granularity_per_account; reference_content_via_telegram_only; Blueprint zasada 4 (dialog potrzebny do "dlaczego" przy decyzjach autonomicznych).
- Menu wyboru agentów LIVE od dziś: **Idea Bot (default) + CM + Subagent X @tomasz_ags + Subagent LinkedIn Personal EN** + automatycznie każdy nowy wiersz channels (LinkedIn TNM PL / AGS EN / RDC PL, future FB/IG/YT per konto) + miejsce na Manager AGS (migracja Faza 2).
- Mechanika: `/agents` (i guzik "🤖 Zmień agenta") -> inline lista z channels + agenci systemowi -> tap zapisuje `user_agent_state.active_agent` ('idea' | 'cm' | 'subagent:<brand>:<channel>') -> każdy kolejny tekst trafia do aktywnego agenta. setMyCommands per czat pokazuje komendy aktywnego agenta.
- Komendy rozmowy subagenta: "pokaż kolejkę", "edytuj kolejkę", "usuń pozycję", "dodaj pozycję ad-hoc", "wyjaśnij decyzję autonomiczną", "pokaż raport dzienny", "pokaż raport tygodniowy" + swobodne pytania z kontekstem kolejki i historii publikacji.
- Kontekst subagenta = channels.config (język, narracja, cele per konto) + post_queue (platform=kanał) + published_posts + agent_logs (jego decyzje). Persona per konto/cel, nie generyczna per platforma.
**Acceptance criteria:** (a) /agents pokazuje minimum 4 pozycje (Idea Bot, CM, X, LinkedIn Personal EN); (b) wybór X + "pokaż kolejkę" zwraca pozycje post_queue platform='x' (scheduled/review/held); (c) wybór LinkedIn + pytanie o ostatnią publikację zwraca dane z published_posts; (d) dodanie wiersza channels (np. LinkedIn TNM PL) pojawia się w menu bez zmian kodu (open/closed).

## R3. Autonomia subagenta + raporty daily/weekly (korekta rozjazdu 3, KRYTYCZNY)
**Canonical:** Tomasz 03/07 (autonomia poza ramy CM z uzasadnieniem w raportach z metrykami); Blueprint zasada 4 (własna wola, log AUTONOMOUS_DECISION); reference_subagent_product_object_canonical (standalone wymaga własnej woli + raportowania).
- Subagent może: ODMÓWIĆ publikacji z planu CM (z uzasadnieniem, np. konflikt czasowy) oraz ZAPROPONOWAĆ publikację poza planem (np. trending topic). Każda taka decyzja -> log AUTONOMOUS_DECISION (rationale + context) + widoczna w rozmowie ("wyjaśnij decyzję") i w raportach.
- **Raport dzienny** per subagent (Telegram push, tabela `subagent_daily_reports`): publikacje wczoraj, metryki engagement (impressions/likes/comments/shares per platforma, na miarę dostępności API - patrz pytania otwarte), decyzje autonomiczne + rationale, kolejka dziś/jutro.
- **Raport tygodniowy** per subagent (niedziela wieczór, tabela `subagent_weekly_reports`): metryki 7 dni (impressions, engagement rate, follower growth, konwersje jeśli tracking), best/worst content + analiza dlaczego, rekomendacje strategii dla CM na następny tydzień (subagent proponuje, CM + Tomasz decydują).
- Generacja raportu: zadanie cm_tasks tier 'haiku' (routine) na cron n8n; treść z DB + LLM podsumowanie w głosie operacyjnym.
**Acceptance criteria:** (a) wpis AUTONOMOUS_DECISION powstaje przy odmowie/propozycji poza planem i jest zwracany przez "wyjaśnij decyzję"; (b) raport dzienny przychodzi na Telegram o stałej godzinie i ma 4 sekcje; (c) raport tygodniowy w niedzielę z rekomendacjami; (d) wiersze w obu tabelach raportowych per subagent per okres.

## R4. Model selection dla CM: Opus 4.8 default dla strategii (korekta rozjazdu 4)
**Canonical:** Tomasz 03/07 ("CM ma pracować na Opus 4.8, tu mam mieć możliwość wyboru modelu"); wzorzec Researcher model_selection LIVE (slices 1+2+3a); Blueprint zasada 1 (model = zmiana operatora, nie redesign); Sekcja 4 korekty (CM sam NIE wybiera modelu bez nadzoru do czasu ~20-30 korekt, jak slice 3b).
- Tabela `cm_tasks` z kolumną `model_tier` (rejestr operacji CM, analogia do research_jobs):
  - **'opus'** default: planer tygodnia/2 miesięcy, dyskusja strategiczna o kącie, rozmowa CM
  - **'sonnet'**: tekst-matka (generate_canonical), synteza raportu tygodniowego
  - **'haiku'**: warianty per kanał, zarządzanie kolejką, callbacki, raport dzienny
- Router klasyfikuje task -> tier automatycznie (analogia QueryRouter); Tomasz może override przez guziki Telegram (wzorzec mtier:<id>:<tier>); korekty logowane do agent_approval_gates type 'model_selection' (approval-learning jak Researcher; auto-automatyzacja dopiero po ~20-30 korektach, osobna decyzja).
- Zmiana defaultów bez deployu: klucze brand_config `cm_tier_<task_type>` czytane live (env fallback).
**Acceptance criteria:** (a) rozmowa strategiczna tworzy cm_task z model_tier='opus' i faktycznie woła claude-opus-4-8; (b) wariant kanałowy leci na haiku; (c) guzik override zmienia tier i loguje korektę do agent_approval_gates; (d) `/set cm_tier_conversation sonnet` zmienia default bez deployu.

## R5. Content memory cross-channel (korekta rozjazdu 5)
**Canonical:** Tomasz 03/07 (pamięć opublikowanego, reuse gdy dojdą IG/FB); project_cm_architecture_locked_28062026 (Centralized Content Brain, multi-kanałowa reuse = fundament wzorca); published_posts LIVE od 31/05.
- Moduł `content_memory.py` w cm-agent:
  - `get_published_by_brand(brand_id, days_ago=90)` - archiwum per marka
  - `get_top_performing(brand_id, channel=None, metric='engagement', top_n=20)` - top posty per kanał lub cross-channel
  - `find_similar(content_item_id, threshold=0.85)` - podobieństwo semantyczne (pgvector jeśli dostępny; fallback: taxonomy + theme matching, patrz pytania otwarte)
  - `suggest_adaptation(content_item_id, target_channel)` - propozycja adaptacji starej treści na nowy kanał
- Rozmowa CM i planner używają content_memory (np. "co najlepiej zagrało w tym miesiącu?", "adaptuj tamten post na IG").
- Hook nowego kanału: aktywacja wiersza channels -> CM proaktywnie proponuje kandydatów do adaptacji ("Masz N wysoko performujących postów X+LinkedIn z 90 dni. Zasugerować 5 do karuzeli IG?").
- Schema: `published_posts` + `content_item_id` FK (jeśli brak) + `engagement_metrics` JSONB (aktualizowane przez subagentów przy raportach). Cross-channel reuse = explicit funkcja plannera Fazy 2.
**Acceptance criteria:** (a) get_top_performing zwraca posortowane posty z metrykami; (b) pytanie w rozmowie CM o najlepsze posty odpowiada danymi z archiwum; (c) aktywacja testowego kanału wywołuje propozycję adaptacji; (d) published_posts ma content_item_id + engagement_metrics.

## R6. Konfiguracja języka: komunikacji i publikacji (uzupełnienie Tomasza 03/07, po E2E)
**Canonical:** Tomasz 03/07 ("agent ma być sprzedawalny, więc muszę mieć w konfiguracji wybór języka komunikacji ORAZ języka publikacji"); project_language_style_doctrine (PL = czysta polszczyzna); cross-posting protocol PL/EN per brand.
- **Dwa OSOBNE ustawienia:**
  - `language_comm` - język ROZMOWY bota z użytkownikiem (menu, rozmowa CM, rozmowy subagentów, raporty, potwierdzenia). Poziom instalacji/marki: klucz brand_config `language_comm` (Tomasz: 'pl'; klient wybiera przy wdrożeniu). Rozmowa czyta live, zero hardkodu języka w promptach.
  - `channels.config.language_publish` - język PUBLIKACJI per cel (generate_variant + CHANNEL_GUIDE po tym języku; first_comment tak samo).
- **Domyślne wartości (Tomasz 03/07):**

| Cel | language_publish |
|---|---|
| X AGS (@tomasz_ags) | en |
| LinkedIn AGS (strona firmowa) | en |
| LinkedIn profil prywatny Tomasza | en |
| LinkedIn TNM | pl |
| LinkedIn Royal Dance Center | pl |
- Reguła jakości: publikacja PL = czysta polszczyzna bez anglicyzmów ("mom test"), publikacja EN = brand voice EN; oba z Voice Bible.
- Sprzedawalność: nowy klient = ustawienie language_comm przy onboardingu + language_publish per każdy jego cel, zero zmian kodu.
**Acceptance criteria:** (a) `/set language_comm en` przełącza język rozmowy bota bez deployu; (b) wariant dla LinkedIn TNM wychodzi po polsku, dla LinkedIn personal po angielsku, z tego samego tekstu-matki; (c) raporty subagentów przychodzą w language_comm; (d) seed channels.config dla 5 celów z tabeli powyżej.

## 3. Zmiany w DB (v2, addytywne)
| Tabela | Zmiana | Status |
|---|---|---|
| `user_agent_state`, `processed_updates`, `content_items.first_comment`, status 'proposed', `app_secrets.log_bot_token` | fundament rozmowy | **DONE 03/07** (db/003) |
| `cm_tasks` (NOWA) | id, task_type, content_item_id NULL, model_tier, status, tokens/cost, created_at | R4 |
| `subagent_daily_reports` (NOWA) | brand_id, channel, report_date, published_count, engagement_metrics JSONB, autonomous_decisions JSONB, queue_snapshot JSONB | R3 |
| `subagent_weekly_reports` (NOWA) | brand_id, channel, week_start, metrics_7d JSONB, best_content JSONB, worst_content JSONB, recommendations TEXT | R3 |
| `agent_logs` (NOWA lub istniejąca - pytanie otwarte #1) | agent_id/channel, log_type ('AUTONOMOUS_DECISION',...), rationale, context JSONB, created_at | R3 |
| `published_posts` | +content_item_id FK (jeśli brak), +engagement_metrics JSONB (jeśli brak) | R5 |
| `channels.config` | klucze per cel: **language_publish** (R6, seed 5 celów), narrative, goals, posts_per_week, slots, first_comment on/off | v1 + R6 |
| `brand_config` | +klucz `language_comm` (język rozmowy bota, R6) + klucze `cm_tier_<task_type>` (R4) | R4 + R6 |
DDL finalny po zatwierdzeniu v2 (jeden plik db/004, idempotentny, OWNER ags_crd_user).

## 4. Fazy budowy v2 (każda = działająca wartość, testowalna E2E)
**Faza 1 - Rozmowa multi-agent + kolejka z jednym approve (POSZERZONA per korekta):**
1a. **Rollback Idea Bota** (natychmiast, przed resztą) [R1]
1b. Router active_agent w HITL + menu /agents + setMyCommands (Idea default, CM, X, LinkedIn) [R2]
1c. Rozmowa CM za menu (moduł z 03/07 + narzędzia save_to_schowek i content_memory) [R1+R5]
1d. Rozmowa subagentów (kolejka, wyjaśnij decyzję, raporty na żądanie) [R2]
1e. cm_tasks + router tierów + override guziki + approval-learning [R4]
1f. content_memory moduł + published_posts kolumny [R5]
1g. agent_logs AUTONOMOUS_DECISION + raporty daily/weekly (tabele + cron + push) [R3]
1h. Język: language_comm w rozmowie + language_publish w generate_variant (seed 5 celów) [R6]
Elementy z 03/07 już LIVE i ZGODNE z v2 (zostają): /message + ConversationRouter, slot gate 'approved', kanał logowy bot #2, dedup, user_agent_state.
**Faza 2 - Proaktywny planer:** cron /plan -> propozycja tygodnia (brand_strategy + cadence + schowek Idea Bota + content_memory) jedną wiadomością -> akceptacja/korekta w rozmowie -> pozycje 'proposed'->'planned' -> generacja wyprzedzająca T-24h -> pojedyncze approve.
**Faza 3 - Pierwszy komentarz:** first_comment z wariantem (w language_publish celu); X = reply OAuth1; LinkedIn = socialActions (ZWERYFIKOWAĆ docs). (Język przeniesiony do Fazy 1 jako 1h per R6.)
**Faza 4 - Media:** X v2 chunked upload (fakty w reference_x_media_api_2026), LinkedIn assets API.

## 5. Czego NIE robimy (parking świadomy, Sekcja 4 korekty)
1. CM standalone mode (bez subagentów) - post-Faza 1 dyskusja.
2. Multi-user (RLS ready, nieaktywowane; jeden Tomasz jeden ekosystem do M5).
3. CM sam wybiera model bez nadzoru - dopiero po ~20-30 korektach (analogia slice 3b), do wtedy Tomasz confirms/override.

## 6. Pytania otwarte (do Managera AGS / Tomasza przy zatwierdzaniu)
1. **agent_logs:** Blueprint mówi `agent_logs_{subagent_id}` (tabela per subagent); rekomendacja BE = JEDNA tabela `agent_logs` z kolumną agent_id + indeks (RLS-ready, mniej migracji przy każdym nowym subagencie). Zatwierdzić wariant.
2. **Źródło metryk engagement:** X read API (GET /2/tweets) jest ZABLOKOWANE na obecnym tierze aplikacji (zweryfikowane 15/06, resource-not-found); pełne impressions/likes wymagają wyższego tieru albo innego źródła. LinkedIn statistics API = do weryfikacji docs-first (Researcher medium) PRZED zobowiązaniem pól raportu. Raporty Fazy 1 startują z tym co mamy pewne (publikacje, decyzje, kolejka) + metryki dochodzą po weryfikacji źródeł.
3. **pgvector:** czy rozszerzenie jest w pg_n8n? Jeśli nie: find_similar startuje na taxonomy+theme matching, pgvector jako upgrade.
4. **Runtime rozmów subagentów:** hostowane w cm-agent (supervised, rekomendacja na teraz) vs osobne kontenery od razu (standalone tier przyszłość). Rekomendacja BE: host teraz, kontrakt /message niezmienny, wydzielenie przy standalone.
5. **Godziny raportów:** daily 08:00, weekly niedziela 20:00 Europe/Warsaw (do potwierdzenia).

## 7. Wzorce do skopiowania (z researchu, bez zmian z v1)
- telegramify-markdown (bezpieczny split MarkdownV2) - jeśli wyjdziemy poza plain text.
- pavel-molyanov/telegram-ai-agent - live stream (edycja jednej wiadomości postępem) + config per wątek.
- langchain-ai/social-media-agent - pełny cykl HITL (wzorzec, nie kod).
- vlymar1/aiogram-bot-template / BushlanovDev/aiogram-fastapi-bot-template - szkielet gatewaya (przy wydzielaniu).
