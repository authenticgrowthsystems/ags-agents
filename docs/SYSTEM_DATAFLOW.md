# AGS System - Mapa przepływu danych i zapisu (living doc)

**Status:** ŻYWY dokument, aktualizowany przy każdej zmianie przepływu. To SUBSTRAT pod docelowy **diagram graficzny** (renderowany, gdy build skończony) - część pakietu sprzedażowego produktu.
**Zasada nadrzędna:** jedno źródło prawdy = PostgreSQL (`ags_crd`). Notion = lustro dla człowieka, nie źródło dla agentów.
**Ostatnia aktualizacja:** 02/07/2026 wieczór (CM + subagenci X/LinkedIn na kontrakcie konektora - sekcja E; rotacja kluczy X + de-hardkod Schedulera; dwukanałowe E2E PASSED). Poprzednio 28/06 (Researcher LIVE). Diagram graficzny Researchera: `docs/researcher-dataflow.svg`.

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
| `app_secrets` | sekrety (key/value, JEDYNE źródło kluczy): `telegram_bot_token`, `x_consumer_key/secret`, `x_access_token/secret` (ZROTOWANE 02/07), `linkedin_client_id/secret`, `linkedin_access_token` (Token Generator, wygasa ~01/09/2026), `linkedin_author_urn`, `researcher_webhook_secret`, klucze LLM/źródeł | publishery + workery [R przez SQL]; rotacja = UPDATE (Tomasz SSH) |
| `task_queue` | (z oryginalnego buildu) zadania agentowe | - |
| `contacts`, `engagement_log` | relikty CRM | - |

### A.2 Researcher + sieć agentów (Faza 0.5, NOWE 23/06)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `agent_registry` | rejestr agentów: `agent_name`, `agent_type`, `status`, `current_gate`, `allowed_model_tiers` TEXT[] (db/007, dozwolone POZIOMY kaskady; default `['low','medium']`) | wszyscy [R]; orchestrator [W] |
| `agent_messages` | szyna agent↔agent: `from/to_agent_id`, `message_type` (request/response/notification/escalation/heartbeat/error), `payload`, `correlation_id`, `status` | każdy agent [W/R] |
| `agent_approval_gates` | log bram per agent: `gate_type` (research/build/acceptance/**model_selection**/**critical_escalation**), `status`, `research_output`/`build_plan`/`test_results`/`model_decision`/`escalation_detail` jsonb | BE/Manager/worker [W], Tomasz approve via Telegram |
| `research_jobs` | master per zapytanie: `query_text`, `query_hash`, `query_embedding` VECTOR(1536), `complexity`, `model_tier` (haiku/sonnet/opus, db/004), `level_override` (db/007, ruling HITL: critical/medium), `status`, `cost_pln`, `confidence_score` | Researcher worker [W/R] |
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
Every Minute -> `Get Keys` (klucze X + telegram_bot_token z `app_secrets` [R]; de-hardkod 02/07, zero sekretów w definicji) -> `post_queue` status='scheduled' o `scheduled_for` <= now -> publish (OAuth1) -> mark published + Telegram confirm.

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
- **Critical-restriction (Regula 2, 28/06, [[manager-decisions-approval-learning]]):** kaskada `critical` (DR+Manus, ~18 PLN) tylko dla agentów z `critical` w `agent_registry.allowed_model_tiers` (manager-ags, tomasz-human). Inny agent z zapytaniem sklasyfikowanym jako critical -> worker `_guard_level` PARKUJE job (`status='awaiting_approval'`, claim_job go nie bierze), zakłada bramkę `critical_escalation` (`escalation_detail` jsonb) i wysyła Tomaszowi Telegram z guzikami **[✅ Zatwierdz critical] [⬇️ Daj medium]** (`crit:<gate_id>:approve|deny`). Gałąź HITL (`Is Crit?` -> `Crit Resolve Gate` CTE) rozstrzyga bramkę + ustawia `research_jobs.level_override` (approve->critical / deny->capped medium) + `status='enqueued'`; worker wznawia (bezpiecznik 30s) i leci dokładnie tym poziomem. `level_override` honorowany w `process_job` PRZED guardem (decyzja człowieka jest ostateczna). NIE dotyczy synth modelu (haiku/sonnet/opus) - tylko poziomu kaskady. manager/tomasz mają full liste -> bez bramki.
- **Co gdzie zapisywane:** job -> `research_jobs`; każde źródło -> `research_runs` + `evidence_items` + `cost_events`; synteza -> `claims` + `options`; wynik dla klienta -> `agent_messages` (RESPONSE).
- **Kaskada (stan wdrożony, 5 żywych źródeł):** low=Web Search; medium=+Firecrawl+Gemini; critical=+OpenAI DR+Manus (router nie zwraca `high`). `DEPLOYED_ADAPTERS` w `config.py` = {web_search, firecrawl, gemini_dr, openai_dr, manus}. Router klasyfikuje query researchowe jako `medium`; `critical` wymaga słowa (piln/krytyczn/urgent/critical/high-stakes). Twarde stopy: 50/100/1500 PLN (critical ~18 PLN/query, DR drogi). Async DR+Manus dziś SEKWENCYJNIE (critical blokuje workera ~10min) -> parallel dispatch = fast-follow.
- **Bezpieczeństwo adapterów:** każdy czyta swój klucz z `app_secrets` (zero literałów w JSON). **Guard:** adapter pobiera też `researcher_webhook_secret` i odrzuca call bez/z błędnym nagłówkiem `X-Researcher-Secret` (worker go wysyła) PRZED płatnym callem (zero spendu dla nieautoryzowanych). `saveData` OFF (klucze nie trafiają do logów n8n).
- **Robustność:** synteza `max_tokens=8192` + `options`/`overall_confidence` z defaultami (duży pakiet evidence nie wywala joba); `evidence_items.freshness` -> TEXT, `claims.supporting_evidence` + `options.supporting_claims` -> TEXT[] (migracja `db/003`, bo źródła/LLM zwracają nie-UUID/nie-timestamp).
- **Wybór modelu (model selection, slice 1+2):** synteza dobiera model per-job. `payload.model_tier` (haiku/sonnet/opus) wskazuje jawnie; gdy brak - auto wg complexity (low->haiku, medium->sonnet, high/critical->opus). Tier->model: haiku=`claude-haiku-4-5-20251001`, sonnet=`claude-sonnet-4-6`, opus=`claude-opus-4-8`. Koszt liczony per-model (`MODEL_RATES`; cache write 1.25x / read 0.10x input). Rozwiązany tier zapisywany w `research_jobs.model_tier`; cache rozdzielony po `(query_hash, model_tier)`. Manager będzie proponował tier z zatwierdzeniem Tomasza (slice 3, [[manager-decisions-approval-learning]]). Uwaga: haiku bywa zwraca <4 pełnych opcji na trudniejszych pytaniach (kompromis lekkiego tieru).
- **Pętla nauki tieru (SLICE 3a-1, async propose-and-run):** worker po domknięciu joba z AUTO-tierem (brak jawnego `payload.model_tier`) zapisuje decyzję jako bramkę `gate_type='model_selection'` w `agent_approval_gates` (status 'pending', submitted_by 'manager-ags') z propozycją + wynikiem w `model_decision` JSONB (`proposed_tier`, `complexity`, `outcome_status`/`_cost_pln`/`_confidence`/`_option_count`; `approved_tier`/`was_corrected` = NULL do korekty). Job NIE czeka. Cache-hit / failed / budget-block NIE są logowane (tier nie odpalił syntezy). Korekta/zatwierdzenie przez Telegram = 3a-2; wykrywanie wzorców + automatyzacja po 20-30 = 3b. Migracja `db/005`. [[manager-decisions-approval-learning]]
- **Moduły Python:** `router`, `cache`, `budget`, `prompts`, `synth`, `failure`, `sources`; `worker` (pętla + FastAPI `/health` `/metrics`). Adaptery n8n w repo: `n8n-workflows/researcher/`. Deploy: `ags-researcher/README.md`.

---

## E. Content Manager + subagenci kanałów (LIVE 02/07, SZKIELET WYKONAWCZY ~10%)

**Topologia:** CM = kontener Python (`cm-agent`, port 8089, wzorzec Researchera: FastAPI `/request` `/plan` `/health` + pętla state-machine budzona wake/30s). Subagenci kanałów = workflowy n8n na KONTRAKCIE KONEKTORA (webhook + guard + klucze z `app_secrets` + publish + callback). Zasada produktu: **subagent = obiekt per KONTO/CEL** (nie per platforma), toggle `channels.supervised`.

### E.1 Tabele CM (owner ags_crd_user)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `brands` | rejestr marek (AGS; docelowo TNM, RDC, personal) | CM [R] |
| `brand_strategy` | `target_audience`, `content_pillars`, `core_topics` per brand | CM [R] |
| `content_items` | state machine treści: planned->[needs_research->researching]->drafting->needs_approval->approved->dispatching->published/rejected; `master_theme`, `canonical_body` (tekst-matka), `target_channels[]`, `taxonomy`, `voice_hash`, `research_job_id` | CM [W/R], HITL (cm: guziki) [W] |
| `channels` | rejestr celów publikacji per brand: `channel`, `status` (active/draft/ready), **`supervised`** (toggle CM on/off), `adapter_path`, `config` jsonb (`publish_mode`: webhook/post_queue/draft) | CM [R], Tomasz [W SQL] |
| `post_queue.content_item_id` | link wariantów kanałowych do content_item | CM [W], subagenci [W status] |

### E.2 Przepływ dwukanałowy (E2E PASSED 02/07 22:08, item 66c6357e)
```
Tomasz/Manager --POST /request {brand_id,master_theme,target_channels,taxonomy}--> CM (202 {content_item_id})
CM pętla: planned -> generate_canonical (Sonnet 5, thinking disabled, voice z brand_config + cache) -> compliance (em-dash filter + banned vocab)
   -> per kanał SUPERVISED+active/draft: generate_variant (Haiku, CHANNEL_GUIDE) -> stage do post_queue (status='review')
   -> needs_approval + Telegram guziki cm:<id>:approve|reject (HITL handler U5pUZjy2yAhR1sWg)
approve -> CM dispatch per publish_mode:
   webhook  -> POST adapter subagenta [X-Researcher-Secret] -> subagent publikuje -> callback: post_queue 'published' + agent_messages RESPONSE {ok,url}
   post_queue -> status 'scheduled' (Scheduler co minutę)   |   draft -> status 'held' (ręcznie)
```

### E.3 Subagenci LIVE
| Subagent | Workflow | Publikacja | Klucze (app_secrets) |
|---|---|---|---|
| **X** (`x-agent`) | `Subagent X Publisher` G3nEIt5lIkiKemiK, `/webhook/subagent-x-publish` | OAuth1 `POST /2/tweets` | `x_consumer_key/secret`, `x_access_token/secret` |
| **LinkedIn profil osobisty** (`linkedin-agent`) | `Subagent LinkedIn Publisher` Uv9TvUMI8MRSqCLz, `/webhook/subagent-linkedin-publish` | Bearer `POST /v2/ugcPosts` (Share on LinkedIn, w_member_social) | `linkedin_access_token` + `linkedin_author_urn`; **GENERYCZNY per cel**: `secret_prefix` w payloadzie (default 'linkedin'); strona firmowa = nowy prefix + wiersz `channels`, zero kodu |
| (pomocniczy) | `LinkedIn OAuth Callback` qvznauoY3FXIttMI, `/webhook/li-oauth-callback` | 3-legged exchange + zapis tokenu/URN | wymaga poprawnego `linkedin_client_secret` (dziś zły; token brany z portalowego Token Generatora) |

### E.4 Mózg CM FAZA 1 - KOMPLET LIVE Z E2E (04/07/2026, wg CM_BRAIN_DESIGN_v2, raporty krokow w docs/cm/)
```
Telegram @ags_social_bot -> n8n HITL U5pUZjy2yAhR1sWg (224 węzły, TYLKO transport):
  guziki: cm:(approve/reject) | cmtier:(korekta modelu -> agent_approval_gates + brand_config) | agsel:(wybór agenta
          -> user_agent_state.active_agent + setMyCommands per czat) | crit:/mtier:/idea:/synth:/ccp: (bez zmian)
  /agents -> menu inline z channels (supervised, open/closed: nowy wiersz = nowa pozycja)
  TEKST (bez stanu edycji/synth) -> Get Active Agent (COALESCE 'idea') -> Active Is Idea?
    TRUE  -> IDEA BOT (tor sprzed 03/07: Prepare Idea Text -> Save Idea -> triage -> inspirations)  [R1]
    FALSE -> POST cm-agent /message {chat_id, text, update_id, active_agent} [X-Researcher-Secret]
  głos/foto -> stary tor Idea Bota (bez zmian)
cm-agent /message (202 + wątek) -> ConversationRouter:
  dedup update_id (processed_updates) | historia PER AGENT (user_agent_state.fsm_data.histories, TTL 30 min)
  'cm' -> rozmowa CM: model z routera R4 (default OPUS 4.8, brand_config cm_tier_conversation live) w języku
     brand_config.language_comm; narzędzia: propose_material | save_to_schowek (inspirations) |
     show_archive | find_similar_published (pgvector) | adapt_published
  'subagent:<brand>:<channel>' -> rozmowa subagenta (sonnet default): kolejka #id | remove/reschedule
     (sync content_items.scheduled_for) | ad-hoc przez approve | subagent_set_metrics (ręczne, X) |
     raport na żądanie | decyzje poza planem -> agent_logs AUTONOMOUS_DECISION  [R2+R3]
JEDEN APPROVE (D2): approve -> pętla claimuje 'approved' DOPIERO gdy scheduled_for<=NOW() -> dispatch
  -> subagent publikuje -> callback: post_queue 'published' + **INSERT published_posts (post_id/URL)** +
     agent_messages RESPONSE -> potwierdzenie na KANAŁ LOGOWY bot #2
GENERACJA: canonical (tier R4) -> compliance -> warianty per cel W JĘZYKU channels.config.language_publish [R6]
CONTENT MEMORY [R5]: published_posts + embedding vector(1536) (OpenAI text-embedding-3-small, backfill leniwy);
  hook nowego kanału (welcomed) -> propozycja adaptacji archiwum
RAPORTY [R3]: cron 'CM Reports Cron' ERweY5vHomrpw1SC (08:00 daily / nd 20:00 weekly, Europe/Warsaw)
  -> POST /reports/<kind> -> per supervised cel: zbiór + UPSERT subagent_daily/weekly_reports + push bot #2;
  metryki: stats_mode per cel = manual (X, ręczne w rozmowie) | member_api | org_api (LinkedIn po App 2 CMA)
```
| Tabele/kolumny mózgu (DDL db/003..007, wszystkie LIVE) | Co trzymają |
|---|---|
| `user_agent_state` | aktywny agent + historia rozmowy per agent per czat (TTL 30 min) |
| `processed_updates` | dedup Telegram update_id |
| `cm_tasks` | ledger operacji LLM: task_type, tier, model, źródło tieru, tokeny, koszt USD |
| `agent_logs` | AUTONOMOUS_DECISION subagentów (rationale + context) - jedna generyczna tabela |
| `subagent_daily_reports` / `subagent_weekly_reports` | raporty per cel per okres (UPSERT) |
| `published_posts` +content_item_id +engagement_metrics +embedding | archiwum publikacji = pamięć cross-channel |
| `content_items.first_comment` + status 'proposed' | pod Fazę 3 (komentarz) i Fazę 2 (plan) |
| `channels.config` | publish_mode, supervised, language_publish, stats_mode, welcomed, (narrative/goals - Faza 2) |
| `brand_config` | voice_bible, language_comm, cm_tier_<task_type>, admin_chat_ids |
| `app_secrets` | wszystkie klucze (anthropic, x_, linkedin_, openai, telegram_bot_token, log_bot_token, guard) |

### E.5 Czego dalej NIE ma (Fazy 2-4 + otwarte)
Proaktywny planer (Faza 2: cron /plan -> propozycja tygodnia z brand_strategy+schowek+content_memory -> 'proposed' -> generacja T-24h), pierwszy komentarz (Faza 3), media (Faza 4), strony firmowe LinkedIn + metryki LinkedIn (token ze scope po review App 2 CMA), FB/IG/YT, tryb standalone subagentów, multi-brand aktywny, pełne i18n stałych komunikatów bota (przy 1. instalacji EN). Otwarte kosmetyki/długi: tekst HITL po approve ("X scheduled, LinkedIn draft"), rotacja tokena Telegram (hardkody w starych węzłach HITL), linkedin_client_secret w DB błędny (token z Token Generatora, wygasa ~01/09/2026). **WARUNEK BRAMY 3 (Tomasz 04/07): jasna ścieżka wdrożenia u osoby trzeciej (playbook instalacji sprzedawalnej) + diagram graficzny przepływu danych.**

---

## D. Do udokumentowania dalej
- [x] Researcher LIVE: diagram graficzny (`docs/researcher-dataflow.svg`) + 3 adaptery w repo (`n8n-workflows/researcher/`) + deploy/README.
- [ ] OpenAI DR + Manus adaptery (fast-follow) - dopisać gdy zbudowane (+ do `DEPLOYED_ADAPTERS`).
- [ ] HITL handler: pełny graf capture->triage->research->content gate (rozwinąć z węzłów).
- [ ] **Diagram graficzny CAŁOŚCI** (pipeline treści + Researcher + sieć agentów) - cel sprzedażowy.
