# AGS System - Mapa przepływu danych i zapisu (living doc)

**Status:** ŻYWY dokument, aktualizowany przy każdej zmianie przepływu. To SUBSTRAT pod docelowy **diagram graficzny** (renderowany, gdy build skończony) - część pakietu sprzedażowego produktu.
**Zasada nadrzędna:** jedno źródło prawdy = PostgreSQL (`ags_crd`). Notion = lustro dla człowieka, nie źródło dla agentów.
**Ostatnia aktualizacja:** 28/06/2026 (Researcher LIVE, 5 źródeł, model selection + pętla nauki tieru; **ingress EVENT-DRIVEN** - webhook `POST /request` budzi workera natychmiast, poll = wolny bezpiecznik). Diagram graficzny Researchera: `docs/researcher-dataflow.svg`.

Legenda: `[W]` = zapis, `[R]` = odczyt.

---

## A. Kręgosłup zapisu - PostgreSQL `ags_crd` (co gdzie żyje)

### A.1 Pipeline treści (LIVE)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `inspirations` | surowe pomysły (tekst/głos/zdjęcie), `metadata` jsonb (m.in. `media`), `research_result` | HITL handler [W/R] |
| `post_queue` | INWENTARZ treści. `content`=EN publikowalny, `brand`, `platform`, `topic`, `status` (review/scheduled/queued/published/held/rejected), `priority`, `scheduled_for` | HITL [W/R], X-agent [R], Scheduler [R] |
| `hitl_sessions` | sesje zatwierdzania. `callback_id`, `status`, `payload` jsonb (draft/draft_pl/draft_en, notionBlockId, topic, priority, media) | X-agent [W], HITL [W/R] |
| `published_posts` | PRAWDA "co opublikowane". `content`, `topic`, `notion_block_id`, `hitl_action`, `published_at` | publishery [W]; dedup [R] |
| `conversation_state` | stan rozmowy idea-bota | HITL [W/R] |
| `voice_notes`, `voice_samples` | pamięć głosu do generacji | HITL [W/R] |
| `brand_config` | key/value per `brand_id`. `voice_bible`, `banned_vocab`, `publish_windows`, `auto_publish_enabled` (=false), itd. ZRODLO GLOSU | generatory [R], Tomasz [W via Telegram] |
| `app_secrets` | sekrety: `telegram_bot_token`, `x_consumer_key/secret`, `x_access_token/secret` | publishery [R przez SQL subselect] |
| `task_queue` | (z oryginalnego buildu) zadania agentowe | - |
| `contacts`, `engagement_log` | relikty CRM | - |

### A.2 Researcher + sieć agentów (Faza 0.5, NOWE 23/06)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `agent_registry` | rejestr agentów: `agent_name`, `agent_type`, `status`, `current_gate` | wszyscy [R]; orchestrator [W] |
| `agent_messages` | szyna agent↔agent: `from/to_agent_id`, `message_type` (request/response/notification/escalation/heartbeat/error), `payload`, `correlation_id`, `status` | każdy agent [W/R] |
| `agent_approval_gates` | log 3 bram per agent: `gate_type` (research/build/acceptance), `status`, `research_output`/`build_plan`/`test_results` jsonb | BE/Manager [W], Tomasz approve |
| `research_jobs` | master per zapytanie: `query_text`, `query_hash`, `query_embedding` VECTOR(1536), `complexity`, `model_tier` (haiku/sonnet/opus, db/004), `status`, `cost_pln`, `confidence_score` | Researcher worker [W/R] |
| `research_runs` | per-source run w ramach job: `source_name`, `status`, `raw_output`, `cost_pln` | worker [W] |
| `evidence_items` | znormalizowane evidence z runs: `source_url`, `content`, `freshness`, `authority` | adaptery/worker [W], synth [R] |
| `claims` | fakty z evidence: `claim_text`, `supporting_evidence` UUID[], `confidence`, `conflict_flag` | synth [W] |
| `options` | 4 strategie decyzji per job: `option_label`, `pros[]`, `cons[]`, `supporting_claims`, `rank_order` | synth [W]; klient [R] |
| `cost_events` | log kosztu API per run: tokeny, `cost_usd`, `cost_pln`, `cached` | BudgetGovernor [W/R] |

---

## B. Pipeline treści - przepływ (LIVE)

### B.1 HITL handler `U5pUZjy2yAhR1sWg` (jedyny konsument bota Telegram)
Capture (tekst/głos/zdjęcie) -> triage -> research (Gemini∥DeepSeek -> Claude synteza) -> Content Creator (draft PL+EN) -> BRAMA TREŚCI -> publikacja.
- **Brama treści:** `Split Into Posts` (seria -> N wierszy 'review') -> `Save To Queue` (`post_queue` status='review') [W] -> per-post podgląd z guzikami. NIC nie auto-publikuje.
- **Akcje callbacku** `ccp:<rowId>:<action>`: `Teraz` (spacing check <3h -> publish lub defer), `Zaplanuj` (next slot 14/18/22), `Watek` (reply-chain), `Do kolejki`/`Odrzuc`.
- **Publish (approve path):** `Post To X Approve` (OAuth1, X v2, opcjonalnie media z Telegram file_id) [czyta app_secrets via Lookup Session] -> `PostgreSQL Save Published Approve` (`published_posts` [W]) -> `Notion Mark Published` (PATCH bullet `[PUBLISHED]`).

### B.2 X-agent `TbHt6ZwfqmMarx18` (cron 14/18/22 Warsaw)
`Notion Get X Queue` (GET bloki `## QUEUE`) [R Notion] -> `Fetch Published Block IDs` (`published_posts.notion_block_id` + pending `hitl_sessions`) [R] -> `Parse Queue Items` (bullety w sekcji, HARD DEDUP po `block.id`) -> `Queue Empty?`.
- Pusto -> `Telegram Queue Empty` (komunikat z liczbą dedup + instrukcją; poprawiony 24/06).
- Jest świeży -> `Claude Adapt To X Post` (dual {pl,en}) -> brand canon check -> `Prepare HITL Preview` -> `PostgreSQL Insert HITL Session` [W] -> Telegram preview. Publikacja po approve w HITL handlerze.
- **Dedup = prawda z bazy:** wpis raz opublikowany (`block.id` w `published_posts`) NIGDY nie jest podawany ponownie, niezależnie od wizualnego stanu Notion.

### B.3 Scheduler `x1jJEbcWAe3FnpCa` (co minutę)
`post_queue` status='scheduled' o `scheduled_for` <= now -> publish (OAuth1) -> `published_posts` [W].

### B.4 Znana luka (interim, do migracji)
`Notion Mark Published` ma relikt `$('PostgreSQL Lookup Session').item.json[0]...` (`.json` to obiekt, nie tablica) -> PATCH pada -> bullety nie dostają `[PUBLISHED]` w Notion -> kolejka Notion nie sprząta się sama. **Dedup DB chroni przed pętlą** (re-publish niemożliwy). Płynący objaw "pusta kolejka mimo wpisów" = poprawny dedup wyczerpanych wpisów; komunikat bota to teraz tłumaczy (fix 24/06). Pełna naprawa = migracja źródła treści Notion -> baza (Notion staje się tylko lustrem).

---

## C. Researcher - przepływ (Faza 0.5, **LIVE 26/06**)

**Topologia:** Hub-and-Spoke. Orkiestracja w **kontenerze Python** (`ags-researcher`, Mikrus, sieć `n8n_network`); **ingress + callback są w workerze** (webhook `POST /request` EVENT-DRIVEN, plus poll `agent_messages` REQUEST jako bezpiecznik -> `research_jobs`; RESPONSE + Telegram bezpośrednio). n8n = **5 adapterów źródeł** (read-only): Web Search, Firecrawl, Gemini, OpenAI DR, Manus. Diagram graficzny: `docs/researcher-dataflow.svg`.

```
Agent-klient / Tomasz
   --(A) POST /request {query,model_tier?,from?,correlation_id?} [X-Researcher-Secret] --> worker: enqueue + wake.set() -> 202 {job_id}   (DROGA GŁÓWNA, event-driven)
   --(B) REQUEST agent_messages (status unread) --> worker poll co 30s -> enqueue                                                       (BEZPIECZNIK)
   research_jobs(enqueued):
   worker pętla (FOR UPDATE SKIP LOCKED), budzona przez wake (natychmiast) lub timeout 30s:
     QueryRouter.classify -> CacheLayer (exact SHA-256 [+ semantic pgvector])
       hit  -> options [W] -> completed -> callback
       miss -> BudgetGovernor.preflight -> dispatch adaptery n8n (wg policy low/med/high/critical)
                -> evidence_items [W] + cost_events [W] (per research_run)
                -> FailureHandler.assess
                -> Synthesizer (Sonnet 4.6, prompt cache, structured output = 4 opcje)
                -> claims [W] + options [W] -> research_jobs.completed (+cost_pln,confidence) [W]
                -> [n8n callback] -> agent_messages RESPONSE [W] + Telegram
```
- **Kontrakt async (event-driven, 28/06) - SZABLON dla CM/Sprzedawcy:** każdy agent = serwis z webhookiem. Prośba = `POST /request` na cel -> cel budzi pętlę OD RAZU (`threading.Event`), zwraca `202 {accepted, job_id}`; praca leci w tle, wynik callbackiem (`agent_messages` RESPONSE + Telegram), NIGDY inline. `POST /request` audytuje też prośbę w `agent_messages` (status='read', żeby poll jej nie ssał drugi raz). Guard `X-Researcher-Secret` (ten sam sekret co adaptery). Poll `agent_messages` zszedł z 5s na 30s = WOLNY BEZPIECZNIK na przegapione dzwonki + droga dla agentów piszących jeszcze prosto do DB. Cron tylko dla rutyn (NIE agent↔agent). `enqueue_job()` = jedna ścieżka ingestu dla webhooka i pollu. [[async-event-driven-comms]]
- **Co gdzie zapisywane:** job -> `research_jobs`; każde źródło -> `research_runs` + `evidence_items` + `cost_events`; synteza -> `claims` + `options`; wynik dla klienta -> `agent_messages` (RESPONSE).
- **Kaskada (stan wdrożony, 5 żywych źródeł):** low=Web Search; medium=+Firecrawl+Gemini; critical=+OpenAI DR+Manus (router nie zwraca `high`). `DEPLOYED_ADAPTERS` w `config.py` = {web_search, firecrawl, gemini_dr, openai_dr, manus}. Router klasyfikuje query researchowe jako `medium`; `critical` wymaga słowa (piln/krytyczn/urgent/critical/high-stakes). Twarde stopy: 50/100/1500 PLN (critical ~18 PLN/query, DR drogi). Async DR+Manus dziś SEKWENCYJNIE (critical blokuje workera ~10min) -> parallel dispatch = fast-follow.
- **Bezpieczeństwo adapterów:** każdy czyta swój klucz z `app_secrets` (zero literałów w JSON). **Guard:** adapter pobiera też `researcher_webhook_secret` i odrzuca call bez/z błędnym nagłówkiem `X-Researcher-Secret` (worker go wysyła) PRZED płatnym callem (zero spendu dla nieautoryzowanych). `saveData` OFF (klucze nie trafiają do logów n8n).
- **Robustność:** synteza `max_tokens=8192` + `options`/`overall_confidence` z defaultami (duży pakiet evidence nie wywala joba); `evidence_items.freshness` -> TEXT, `claims.supporting_evidence` + `options.supporting_claims` -> TEXT[] (migracja `db/003`, bo źródła/LLM zwracają nie-UUID/nie-timestamp).
- **Wybór modelu (model selection, slice 1+2):** synteza dobiera model per-job. `payload.model_tier` (haiku/sonnet/opus) wskazuje jawnie; gdy brak - auto wg complexity (low->haiku, medium->sonnet, high/critical->opus). Tier->model: haiku=`claude-haiku-4-5-20251001`, sonnet=`claude-sonnet-4-6`, opus=`claude-opus-4-8`. Koszt liczony per-model (`MODEL_RATES`; cache write 1.25x / read 0.10x input). Rozwiązany tier zapisywany w `research_jobs.model_tier`; cache rozdzielony po `(query_hash, model_tier)`. Manager będzie proponował tier z zatwierdzeniem Tomasza (slice 3, [[manager-decisions-approval-learning]]). Uwaga: haiku bywa zwraca <4 pełnych opcji na trudniejszych pytaniach (kompromis lekkiego tieru).
- **Pętla nauki tieru (SLICE 3a-1, async propose-and-run):** worker po domknięciu joba z AUTO-tierem (brak jawnego `payload.model_tier`) zapisuje decyzję jako bramkę `gate_type='model_selection'` w `agent_approval_gates` (status 'pending', submitted_by 'manager-ags') z propozycją + wynikiem w `model_decision` JSONB (`proposed_tier`, `complexity`, `outcome_status`/`_cost_pln`/`_confidence`/`_option_count`; `approved_tier`/`was_corrected` = NULL do korekty). Job NIE czeka. Cache-hit / failed / budget-block NIE są logowane (tier nie odpalił syntezy). Korekta/zatwierdzenie przez Telegram = 3a-2; wykrywanie wzorców + automatyzacja po 20-30 = 3b. Migracja `db/005`. [[manager-decisions-approval-learning]]
- **Moduły Python:** `router`, `cache`, `budget`, `prompts`, `synth`, `failure`, `sources`; `worker` (pętla + FastAPI `/health` `/metrics`). Adaptery n8n w repo: `n8n-workflows/researcher/`. Deploy: `ags-researcher/README.md`.

---

## D. Do udokumentowania dalej
- [x] Researcher LIVE: diagram graficzny (`docs/researcher-dataflow.svg`) + 3 adaptery w repo (`n8n-workflows/researcher/`) + deploy/README.
- [ ] OpenAI DR + Manus adaptery (fast-follow) - dopisać gdy zbudowane (+ do `DEPLOYED_ADAPTERS`).
- [ ] HITL handler: pełny graf capture->triage->research->content gate (rozwinąć z węzłów).
- [ ] **Diagram graficzny CAŁOŚCI** (pipeline treści + Researcher + sieć agentów) - cel sprzedażowy.
