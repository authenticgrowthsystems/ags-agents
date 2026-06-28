# RAPORT DO MANAGERA AGS - CM Brama 1 + 2 ZALICZONE (28/06/2026, od BE)

Tomasz wkleja do czatu Manager AGS (Cowork). **Jesteśmy przed harmonogramem: Bramy 1 i 2 zrobione dziś wieczorem (plan był na jutro).**

## 1. Jak to poszło (proces)

- Tomasz puścił RĘCZNIE deep research przez najlepsze premium modele (4 raporty: m.in. duży Gemini, Manus). Trafiły do BE (Opus 4.8) - per decyzja Tomasza, technika idzie do BE.
- BE zsyntetyzował 4 raporty z NASZYM realnym stackiem, naprawił ich stack-mismatche (wskazywały nieistniejące u nas modele claude-3-5, psycopg2/SQLAlchemy, klucze w ENV, duplikaty tabel).
- Researcher (medium, automat) = cross-check; potwierdził: do decyzji architektonicznych ręczne premium >> medium.
- Architektura zablokowana przez decyzje Tomasza PUNKT-PO-PUNKCIE (9 decyzji).

## 2. Architektura CM - ZABLOKOWANA

**Wzorzec:** Centralized Content Brain (kanoniczny tekst-matka -> cienkie adaptery kanałowe), FastAPI + n8n + Postgres SSOT.
**Subagenci:** JEDEN generyczny kontrakt async (/request webhook + callback + rejestr) dla WSZYSTKICH subagentów (publishery kanałowe + Researcher + przyszli). CM = generyczny GOSPODARZ - gotowy przyjąć DOWOLNY nowy kanał/subagenta (TikTok, Pinterest, nieznane przyszłe) bez przebudowy rdzenia (open/closed). Kontrakt = ten, który BE zbudował dziś dla Researchera.
**Kanały:** X (auto) + LinkedIn (draft) aktywne od startu; YouTube/Facebook/Instagram/... ready-to-plug (stub do tego samego kontraktu).

## 3. Dziewięć decyzji (D1-D5 architektura, B-D1..B-D4 build)

- **D1** Rdzeń = lean: 1 nowa tabela `content_items` (mózg) + reuse istniejących (post_queue outbox, published_posts, inspirations, brand_config głos).
- **D2** Osobna lean `brand_strategy` (audience/pillars/topics); voice_bible zostaje w brand_config.
- **D3** Multi-tenant: app-level brand_id teraz + schema RLS-ready; RLS przed 2. marką w CM. (Multi-tenant LIVE: AGS, TNM, Royal Dance, SdI.)
- **D4** Migracja Notion -> Postgres = PO MVP (osobny ostrożny krok; żywy X-agent nietknięty).
- **D5** Pełna obiektowa abstrakcja kanałów (generyczny rejestr + kontrakt), bez półśrodków.
- **B-D1** Osobna lekka tabela `brands` (kotwica tenantów + FK).
- **B-D2** HITL CM = gałąź `cm:` w istniejącym handlerze U5pUZjy2yAhR1sWg (jeden bot/webhook).
- **B-D3** Planowanie = n8n cron budzi CM; timed publishing reuse istniejący Scheduler.
- **B-D4** Warianty per-kanał EAGER (przed bramą HITL) - Tomasz zatwierdza faktyczny tekst kanałowy.

**4 nowe tabele:** brands, content_items, brand_strategy, channels. Reszta = reuse.

## 4. Obsidian (Twoja warstwa)

Obsidian = mózg STRATEGICZNY Managera (strategia/why/relacje idei), NIE operacyjny rdzeń CM. Przepływ jednokierunkowy: Obsidian -> Manager destyluje -> Postgres brand_strategy/brand_config -> CM czyta. Projektujemy przy MIGRACJI MANAGERA (krok po CM). Agenci serwerowi nie czytają Obsidiana; voice_bible kanoniczny w Postgresie.

## 5. Następna faza

Build cm-agent (DDL 4 tabel -> serwis Python FastAPI + /request + state machine -> adaptery/HITL n8n) 30/06-01/07 -> **Brama 3 (test E2E) 02/07** -> CM LIVE 02-03/07. Pełne dokumenty BE: `docs/cm/` (synteza+architektura, plan budowy, oba z logami decyzji).

---

*Od: AGS Build Engineer (Opus 4.8). Dokumenty: docs/cm/{CM_Architecture_Synthesis_BE, CM_Brama2_BuildPlan}.md.*
