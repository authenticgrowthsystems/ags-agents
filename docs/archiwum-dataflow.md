# ARCHIWUM: SYSTEM_DATAFLOW - sekcje historyczne (zrzut 20/07/2026)

To jest ARCHIWUM, nie dokumentacja stanu obecnego. Pelna tresc SYSTEM_DATAFLOW.md
sprzed reformy dokumentacyjnej 20/07/2026 (kanon DOKUMENTACJA ZYJE: dokumentacja
opisuje STAN OBECNY, historia mieszka w raportach i archiwum). Sekcje narastaly
DATAMI (G = dzien 19/07, H = integracja 19/07) i zostaly skompilowane do
dokumentacji komponentowej.

STAN OBECNY czytaj w: docs/komponenty/ (11 plikow per komponent)
oraz docs/SYSTEM_DATAFLOW.md (mapa przeplywu + indeks).

--- PONIZEJ ORYGINALNA TRESC (zrzut sprzed reformy) ---
# AGS System - Mapa przepĹ‚ywu danych i zapisu (living doc)

**Status:** Ĺ»YWY dokument, aktualizowany przy kaĹĽdej zmianie przepĹ‚ywu. To SUBSTRAT pod docelowy **diagram graficzny** (renderowany, gdy build skoĹ„czony) - czÄ™Ĺ›Ä‡ pakietu sprzedaĹĽowego produktu.
**Zasada nadrzÄ™dna:** jedno ĹşrĂłdĹ‚o prawdy = PostgreSQL (`ags_crd`). Notion = lustro dla czĹ‚owieka, nie ĹşrĂłdĹ‚o dla agentĂłw.
**Ostatnia aktualizacja:** 02/07/2026 wieczĂłr (CM + subagenci X/LinkedIn na kontrakcie konektora - sekcja E; rotacja kluczy X + de-hardkod Schedulera; dwukanaĹ‚owe E2E PASSED). Poprzednio 28/06 (Researcher LIVE). Diagram graficzny Researchera: `docs/researcher-dataflow.svg`.

Legenda: `[W]` = zapis, `[R]` = odczyt.

---

## A. KrÄ™gosĹ‚up zapisu - PostgreSQL `ags_crd` (co gdzie ĹĽyje)

### A.1 Pipeline treĹ›ci (LIVE)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `inspirations` | surowe pomysĹ‚y (tekst/gĹ‚os/zdjÄ™cie), `metadata` jsonb (m.in. `media`), `research_result` | HITL handler [W/R] |
| `post_queue` | INWENTARZ treĹ›ci. `content`=EN publikowalny, `brand`, `platform`, `topic`, `status` (review/scheduled/queued/published/held/rejected), `priority`, `scheduled_for` | HITL [W/R], X-agent [R], Scheduler [R] |
| `hitl_sessions` | sesje zatwierdzania. `callback_id`, `status`, `payload` jsonb (draft/draft_pl/draft_en, notionBlockId, topic, priority, media) | X-agent [W], HITL [W/R] |
| `published_posts` | PRAWDA "co opublikowane". `content`, `topic`, `notion_block_id`, `hitl_action`, `published_at` | publishery [W]; dedup [R] |
| `conversation_state` | stan rozmowy idea-bota | HITL [W/R] |
| `voice_notes`, `voice_samples` | pamiÄ™Ä‡ gĹ‚osu do generacji | HITL [W/R] |
| `brand_config` | key/value per `brand_id`. `voice_bible`, `banned_vocab`, `publish_windows`, `auto_publish_enabled` (=false), itd. ZRODLO GLOSU | generatory [R], Tomasz [W via Telegram] |
| `app_secrets` | sekrety (key/value, JEDYNE ĹşrĂłdĹ‚o kluczy): `telegram_bot_token`, `x_consumer_key/secret`, `x_access_token/secret` (ZROTOWANE 02/07), `linkedin_client_id/secret`, `linkedin_access_token` (Token Generator, wygasa ~01/09/2026), `linkedin_author_urn`, `researcher_webhook_secret`, klucze LLM/ĹşrĂłdeĹ‚ | publishery + workery [R przez SQL]; rotacja = UPDATE (Tomasz SSH) |
| `task_queue` | (z oryginalnego buildu) zadania agentowe | - |
| `contacts`, `engagement_log` | relikty CRM | - |

### A.2 Researcher + sieÄ‡ agentĂłw (Faza 0.5, NOWE 23/06)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `agent_registry` | rejestr agentĂłw: `agent_name`, `agent_type`, `status`, `current_gate`, `allowed_model_tiers` TEXT[] (db/007, dozwolone POZIOMY kaskady; default `['low','medium']`) | wszyscy [R]; orchestrator [W] |
| `agent_messages` | szyna agentâ†”agent: `from/to_agent_id`, `message_type` (request/response/notification/escalation/heartbeat/error), `payload`, `correlation_id`, `status` | kaĹĽdy agent [W/R] |
| `agent_approval_gates` | log bram per agent: `gate_type` (research/build/acceptance/**model_selection**/**critical_escalation**), `status`, `research_output`/`build_plan`/`test_results`/`model_decision`/`escalation_detail` jsonb | BE/Manager/worker [W], Tomasz approve via Telegram |
| `research_jobs` | master per zapytanie: `query_text`, `query_hash`, `query_embedding` VECTOR(1536), `complexity`, `model_tier` (haiku/sonnet/opus, db/004), `level_override` (db/007, ruling HITL: critical/medium), `status`, `cost_pln`, `confidence_score` | Researcher worker [W/R] |
| `research_runs` | per-source run w ramach job: `source_name`, `status`, `raw_output`, `cost_pln` | worker [W] |
| `evidence_items` | znormalizowane evidence z runs: `source_url`, `content`, `freshness`, `authority` | adaptery/worker [W], synth [R] |
| `claims` | fakty z evidence: `claim_text`, `supporting_evidence` UUID[], `confidence`, `conflict_flag` | synth [W] |
| `options` | 4 strategie decyzji per job: `option_label`, `pros[]`, `cons[]`, `supporting_claims`, `rank_order` | synth [W]; klient [R] |
| `cost_events` | log kosztu API per run: tokeny, `cost_usd`, `cost_pln`, `cached` | BudgetGovernor [W/R] |

---

## B. Pipeline treĹ›ci - przepĹ‚yw (LIVE)

### B.1 HITL handler `U5pUZjy2yAhR1sWg` (jedyny konsument bota Telegram)
Capture (tekst/gĹ‚os/zdjÄ™cie) -> triage -> research (GeminiâĄDeepSeek -> Claude synteza) -> Content Creator (draft PL+EN) -> BRAMA TREĹšCI -> publikacja.
- **Brama treĹ›ci:** `Split Into Posts` (seria -> N wierszy 'review') -> `Save To Queue` (`post_queue` status='review') [W] -> per-post podglÄ…d z guzikami. NIC nie auto-publikuje.
- **Akcje callbacku** `ccp:<rowId>:<action>`: `Teraz` (spacing check <3h -> publish lub defer), `Zaplanuj` (next slot 14/18/22), `Watek` (reply-chain), `Do kolejki`/`Odrzuc`.
- **Publish (approve path):** `Post To X Approve` (OAuth1, X v2, opcjonalnie media z Telegram file_id) [czyta app_secrets via Lookup Session] -> `PostgreSQL Save Published Approve` (`published_posts` [W]) -> `Notion Mark Published` (PATCH bullet `[PUBLISHED]`).

### B.2 X-agent `TbHt6ZwfqmMarx18` (cron 14/18/22 Warsaw)
`Notion Get X Queue` (GET bloki `## QUEUE`) [R Notion] -> `Fetch Published Block IDs` (`published_posts.notion_block_id` + pending `hitl_sessions`) [R] -> `Parse Queue Items` (bullety w sekcji, HARD DEDUP po `block.id`) -> `Queue Empty?`.
- Pusto -> `Telegram Queue Empty` (komunikat z liczbÄ… dedup + instrukcjÄ…; poprawiony 24/06).
- Jest Ĺ›wieĹĽy -> `Claude Adapt To X Post` (dual {pl,en}) -> brand canon check -> `Prepare HITL Preview` -> `PostgreSQL Insert HITL Session` [W] -> Telegram preview. Publikacja po approve w HITL handlerze.
- **Dedup = prawda z bazy:** wpis raz opublikowany (`block.id` w `published_posts`) NIGDY nie jest podawany ponownie, niezaleĹĽnie od wizualnego stanu Notion.

### B.3 Scheduler `x1jJEbcWAe3FnpCa` (co minutÄ™)
Every Minute -> `Get Keys` (klucze X + telegram_bot_token z `app_secrets` [R]; de-hardkod 02/07, zero sekretĂłw w definicji) -> `post_queue` status='scheduled' o `scheduled_for` <= now -> publish (OAuth1) -> mark published + Telegram confirm.

### B.4 Znana luka (interim, do migracji)
`Notion Mark Published` ma relikt `$('PostgreSQL Lookup Session').item.json[0]...` (`.json` to obiekt, nie tablica) -> PATCH pada -> bullety nie dostajÄ… `[PUBLISHED]` w Notion -> kolejka Notion nie sprzÄ…ta siÄ™ sama. **Dedup DB chroni przed pÄ™tlÄ…** (re-publish niemoĹĽliwy). PĹ‚ynÄ…cy objaw "pusta kolejka mimo wpisĂłw" = poprawny dedup wyczerpanych wpisĂłw; komunikat bota to teraz tĹ‚umaczy (fix 24/06). PeĹ‚na naprawa = migracja ĹşrĂłdĹ‚a treĹ›ci Notion -> baza (Notion staje siÄ™ tylko lustrem).

---

## C. Researcher - przepĹ‚yw (Faza 0.5, **LIVE 26/06**)

**Topologia:** Hub-and-Spoke. Orkiestracja w **kontenerze Python** (`ags-researcher`, Mikrus, sieÄ‡ `n8n_network`); **ingress + callback sÄ… w workerze** (webhook `POST /request` EVENT-DRIVEN, plus poll `agent_messages` REQUEST jako bezpiecznik -> `research_jobs`; RESPONSE + Telegram bezpoĹ›rednio). n8n = **5 adapterĂłw ĹşrĂłdeĹ‚** (read-only): Web Search, Firecrawl, Gemini, OpenAI DR, Manus. Diagram graficzny: `docs/researcher-dataflow.svg`.

```
Agent-klient / Tomasz
   --(A) POST /request {query,model_tier?,from?,correlation_id?} [X-Researcher-Secret] --> worker: enqueue + wake.set() -> 202 {job_id}   (DROGA GĹĂ“WNA, event-driven)
   --(B) REQUEST agent_messages (status unread) --> worker poll co 30s -> enqueue                                                       (BEZPIECZNIK)
   research_jobs(enqueued):
   worker pÄ™tla (FOR UPDATE SKIP LOCKED), budzona przez wake (natychmiast) lub timeout 30s:
     QueryRouter.classify -> CacheLayer (exact SHA-256 [+ semantic pgvector])
       hit  -> options [W] -> completed -> callback
       miss -> BudgetGovernor.preflight -> dispatch adaptery n8n (wg policy low/med/high/critical)
                -> evidence_items [W] + cost_events [W] (per research_run)
                -> FailureHandler.assess
                -> Synthesizer (Sonnet 4.6, prompt cache, structured output = 4 opcje)
                -> claims [W] + options [W] -> research_jobs.completed (+cost_pln,confidence) [W]
                -> [n8n callback] -> agent_messages RESPONSE [W] + Telegram
```
- **Kontrakt async (event-driven, 28/06) - SZABLON dla CM/Sprzedawcy:** kaĹĽdy agent = serwis z webhookiem. ProĹ›ba = `POST /request` na cel -> cel budzi pÄ™tlÄ™ OD RAZU (`threading.Event`), zwraca `202 {accepted, job_id}`; praca leci w tle, wynik callbackiem (`agent_messages` RESPONSE + Telegram), NIGDY inline. `POST /request` audytuje teĹĽ proĹ›bÄ™ w `agent_messages` (status='read', ĹĽeby poll jej nie ssaĹ‚ drugi raz). Guard `X-Researcher-Secret` (ten sam sekret co adaptery). Poll `agent_messages` zszedĹ‚ z 5s na 30s = WOLNY BEZPIECZNIK na przegapione dzwonki + droga dla agentĂłw piszÄ…cych jeszcze prosto do DB. Cron tylko dla rutyn (NIE agentâ†”agent). `enqueue_job()` = jedna Ĺ›cieĹĽka ingestu dla webhooka i pollu. [[async-event-driven-comms]]
- **Critical-restriction (Regula 2, 28/06, [[manager-decisions-approval-learning]]):** kaskada `critical` (DR+Manus, ~18 PLN) tylko dla agentĂłw z `critical` w `agent_registry.allowed_model_tiers` (manager-ags, tomasz-human). Inny agent z zapytaniem sklasyfikowanym jako critical -> worker `_guard_level` PARKUJE job (`status='awaiting_approval'`, claim_job go nie bierze), zakĹ‚ada bramkÄ™ `critical_escalation` (`escalation_detail` jsonb) i wysyĹ‚a Tomaszowi Telegram z guzikami **[âś… Zatwierdz critical] [â¬‡ď¸Ź Daj medium]** (`crit:<gate_id>:approve|deny`). GaĹ‚Ä…Ĺş HITL (`Is Crit?` -> `Crit Resolve Gate` CTE) rozstrzyga bramkÄ™ + ustawia `research_jobs.level_override` (approve->critical / deny->capped medium) + `status='enqueued'`; worker wznawia (bezpiecznik 30s) i leci dokĹ‚adnie tym poziomem. `level_override` honorowany w `process_job` PRZED guardem (decyzja czĹ‚owieka jest ostateczna). NIE dotyczy synth modelu (haiku/sonnet/opus) - tylko poziomu kaskady. manager/tomasz majÄ… full liste -> bez bramki.
- **Co gdzie zapisywane:** job -> `research_jobs`; kaĹĽde ĹşrĂłdĹ‚o -> `research_runs` + `evidence_items` + `cost_events`; synteza -> `claims` + `options`; wynik dla klienta -> `agent_messages` (RESPONSE).
- **Kaskada (stan wdroĹĽony, 5 ĹĽywych ĹşrĂłdeĹ‚):** low=Web Search; medium=+Firecrawl+Gemini; critical=+OpenAI DR+Manus (router nie zwraca `high`). `DEPLOYED_ADAPTERS` w `config.py` = {web_search, firecrawl, gemini_dr, openai_dr, manus}. Router klasyfikuje query researchowe jako `medium`; `critical` wymaga sĹ‚owa (piln/krytyczn/urgent/critical/high-stakes). Twarde stopy: 50/100/1500 PLN (critical ~18 PLN/query, DR drogi). Async DR+Manus dziĹ› SEKWENCYJNIE (critical blokuje workera ~10min) -> parallel dispatch = fast-follow.
- **BezpieczeĹ„stwo adapterĂłw:** kaĹĽdy czyta swĂłj klucz z `app_secrets` (zero literaĹ‚Ăłw w JSON). **Guard:** adapter pobiera teĹĽ `researcher_webhook_secret` i odrzuca call bez/z bĹ‚Ä™dnym nagĹ‚Ăłwkiem `X-Researcher-Secret` (worker go wysyĹ‚a) PRZED pĹ‚atnym callem (zero spendu dla nieautoryzowanych). `saveData` OFF (klucze nie trafiajÄ… do logĂłw n8n).
- **RobustnoĹ›Ä‡:** synteza `max_tokens=8192` + `options`/`overall_confidence` z defaultami (duĹĽy pakiet evidence nie wywala joba); `evidence_items.freshness` -> TEXT, `claims.supporting_evidence` + `options.supporting_claims` -> TEXT[] (migracja `db/003`, bo ĹşrĂłdĹ‚a/LLM zwracajÄ… nie-UUID/nie-timestamp).
- **WybĂłr modelu (model selection, slice 1+2):** synteza dobiera model per-job. `payload.model_tier` (haiku/sonnet/opus) wskazuje jawnie; gdy brak - auto wg complexity (low->haiku, medium->sonnet, high/critical->opus). Tier->model: haiku=`claude-haiku-4-5-20251001`, sonnet=`claude-sonnet-4-6`, opus=`claude-opus-4-8`. Koszt liczony per-model (`MODEL_RATES`; cache write 1.25x / read 0.10x input). RozwiÄ…zany tier zapisywany w `research_jobs.model_tier`; cache rozdzielony po `(query_hash, model_tier)`. Manager bÄ™dzie proponowaĹ‚ tier z zatwierdzeniem Tomasza (slice 3, [[manager-decisions-approval-learning]]). Uwaga: haiku bywa zwraca <4 peĹ‚nych opcji na trudniejszych pytaniach (kompromis lekkiego tieru).
- **PÄ™tla nauki tieru (SLICE 3a-1, async propose-and-run):** worker po domkniÄ™ciu joba z AUTO-tierem (brak jawnego `payload.model_tier`) zapisuje decyzjÄ™ jako bramkÄ™ `gate_type='model_selection'` w `agent_approval_gates` (status 'pending', submitted_by 'manager-ags') z propozycjÄ… + wynikiem w `model_decision` JSONB (`proposed_tier`, `complexity`, `outcome_status`/`_cost_pln`/`_confidence`/`_option_count`; `approved_tier`/`was_corrected` = NULL do korekty). Job NIE czeka. Cache-hit / failed / budget-block NIE sÄ… logowane (tier nie odpaliĹ‚ syntezy). Korekta/zatwierdzenie przez Telegram = 3a-2; wykrywanie wzorcĂłw + automatyzacja po 20-30 = 3b. Migracja `db/005`. [[manager-decisions-approval-learning]]
- **ModuĹ‚y Python:** `router`, `cache`, `budget`, `prompts`, `synth`, `failure`, `sources`; `worker` (pÄ™tla + FastAPI `/health` `/metrics`). Adaptery n8n w repo: `n8n-workflows/researcher/`. Deploy: `ags-researcher/README.md`.

---

## E. Content Manager + subagenci kanaĹ‚Ăłw (LIVE 02/07, SZKIELET WYKONAWCZY ~10%)

**Topologia:** CM = kontener Python (`cm-agent`, port 8089, wzorzec Researchera: FastAPI `/request` `/plan` `/health` + pÄ™tla state-machine budzona wake/30s). Subagenci kanaĹ‚Ăłw = workflowy n8n na KONTRAKCIE KONEKTORA (webhook + guard + klucze z `app_secrets` + publish + callback). Zasada produktu: **subagent = obiekt per KONTO/CEL** (nie per platforma), toggle `channels.supervised`.

**Kontrakt WAKE (kanon event-driven 28/06, domkniÄ™ty 10/07):** `POST /wake` [X-Researcher-Secret] na cm-agent:8089 budzi pÄ™tlÄ™ natychmiast. KaĹĽdy, kto ZAPISUJE coĹ› dla CM do DB (agent_messages request, task_queue, callback publikacji w post_queue), woĹ‚a po zapisie `/wake`. WewnÄ…trz procesu: eskalacja subagenta (`escalate_to_cm`), decyzje cmt i zatwierdzenie planu ustawiajÄ… `wake_event` bezpoĹ›rednio. Poll 30s pÄ™tli = wolny BACKSTOP, nie Ĺ›cieĹĽka podstawowa. TODO n8n: publishery po callbacku woĹ‚ajÄ… `/wake` (dziĹ› meldunek po publikacji czeka do 30 s na poll - do domkniÄ™cia przy najbliĹĽszej sesji n8n z tapem).

### E.1 Tabele CM (owner ags_crd_user)
| Tabela | Co trzyma | Kto pisze / czyta |
|---|---|---|
| `brands` | rejestr marek (AGS; docelowo TNM, RDC, personal) | CM [R] |
| `brand_strategy` | `target_audience`, `content_pillars`, `core_topics` per brand | CM [R] |
| `content_items` | state machine treĹ›ci: planned->[needs_research->researching]->drafting->needs_approval->approved->dispatching->published/rejected; `master_theme`, `canonical_body` (tekst-matka), `target_channels[]`, `taxonomy`, `voice_hash`, `research_job_id` | CM [W/R], HITL (cm: guziki) [W] |
| `channels` | rejestr celĂłw publikacji per brand: `channel`, `status` (active/draft/ready), **`supervised`** (toggle CM on/off), `adapter_path`, `config` jsonb (`publish_mode`: webhook/post_queue/draft) | CM [R], Tomasz [W SQL] |
| `post_queue.content_item_id` | link wariantĂłw kanaĹ‚owych do content_item | CM [W], subagenci [W status] |

### E.2 PrzepĹ‚yw dwukanaĹ‚owy (E2E PASSED 02/07 22:08, item 66c6357e)
```
Tomasz/Manager --POST /request {brand_id,master_theme,target_channels,taxonomy}--> CM (202 {content_item_id})
CM pÄ™tla: planned -> generate_canonical (Sonnet 5, thinking disabled, voice z brand_config + cache) -> compliance (em-dash filter + banned vocab)
   -> per kanaĹ‚ SUPERVISED+active/draft: generate_variant (Haiku, CHANNEL_GUIDE) -> stage do post_queue (status='review')
   -> needs_approval + Telegram guziki cm:<id>:approve|reject (HITL handler U5pUZjy2yAhR1sWg)
approve -> CM dispatch per publish_mode:
   webhook  -> POST adapter subagenta [X-Researcher-Secret] -> subagent publikuje -> callback: post_queue 'published' + agent_messages RESPONSE {ok,url}
   post_queue -> status 'scheduled' (Scheduler co minutÄ™)   |   draft -> status 'held' (rÄ™cznie)
```

### E.3 Subagenci LIVE
| Subagent | Workflow | Publikacja | Klucze (app_secrets) |
|---|---|---|---|
| **X** (`x-agent`) | `Subagent X Publisher` G3nEIt5lIkiKemiK, `/webhook/subagent-x-publish` | OAuth1 `POST /2/tweets` | `x_consumer_key/secret`, `x_access_token/secret` |
| **LinkedIn profil osobisty** (`linkedin-agent`) | `Subagent LinkedIn Publisher` Uv9TvUMI8MRSqCLz, `/webhook/subagent-linkedin-publish` | Bearer `POST /v2/ugcPosts` (Share on LinkedIn, w_member_social) | `linkedin_access_token` + `linkedin_author_urn`; **GENERYCZNY per cel**: `secret_prefix` w payloadzie (default 'linkedin'); strona firmowa = nowy prefix + wiersz `channels`, zero kodu |
| (pomocniczy) | `LinkedIn OAuth Callback` qvznauoY3FXIttMI, `/webhook/li-oauth-callback` | 3-legged exchange + zapis tokenu/URN | wymaga poprawnego `linkedin_client_secret` (dziĹ› zĹ‚y; token brany z portalowego Token Generatora) |

### E.4 MĂłzg CM FAZA 1 - KOMPLET LIVE Z E2E (04/07/2026, wg CM_BRAIN_DESIGN_v2, raporty krokow w docs/cm/)
```
Telegram @ags_social_bot -> n8n HITL U5pUZjy2yAhR1sWg (224 wÄ™zĹ‚y, TYLKO transport):
  guziki: cm:(approve/reject) | cmtier:(korekta modelu -> agent_approval_gates + brand_config) | agsel:(wybĂłr agenta
          -> user_agent_state.active_agent + setMyCommands per czat) | crit:/mtier:/idea:/synth:/ccp: (bez zmian)
  /agents -> menu inline z channels (supervised, open/closed: nowy wiersz = nowa pozycja)
  TEKST (bez stanu edycji/synth) -> Get Active Agent (COALESCE 'idea') -> Active Is Idea?
    TRUE  -> IDEA BOT (tor sprzed 03/07: Prepare Idea Text -> Save Idea -> triage -> inspirations)  [R1]
    FALSE -> POST cm-agent /message {chat_id, text, update_id, active_agent} [X-Researcher-Secret]
  gĹ‚os/foto -> stary tor Idea Bota (bez zmian)
cm-agent /message (202 + wÄ…tek) -> ConversationRouter:
  dedup update_id (processed_updates) | historia PER AGENT (user_agent_state.fsm_data.histories, TTL 30 min)
  'cm' -> rozmowa CM: model z routera R4 (default OPUS 4.8, brand_config cm_tier_conversation live) w jÄ™zyku
     brand_config.language_comm; narzÄ™dzia: propose_material | save_to_schowek (inspirations) |
     show_archive | find_similar_published (pgvector) | adapt_published
  'subagent:<brand>:<channel>' -> rozmowa subagenta (sonnet default): kolejka #id | remove/reschedule
     (sync content_items.scheduled_for) | ad-hoc przez approve | subagent_set_metrics (rÄ™czne, X) |
     raport na ĹĽÄ…danie | decyzje poza planem -> agent_logs AUTONOMOUS_DECISION  [R2+R3]
JEDEN APPROVE (D2): approve -> pÄ™tla claimuje 'approved' DOPIERO gdy scheduled_for<=NOW() -> dispatch
  -> subagent publikuje -> callback: post_queue 'published' + **INSERT published_posts (post_id/URL)** +
     agent_messages RESPONSE -> potwierdzenie na KANAĹ LOGOWY bot #2
GENERACJA: canonical (tier R4) -> compliance -> warianty per cel W JÄZYKU channels.config.language_publish [R6]
CONTENT MEMORY [R5]: published_posts + embedding vector(1536) (OpenAI text-embedding-3-small, backfill leniwy);
  hook nowego kanaĹ‚u (welcomed) -> propozycja adaptacji archiwum
RAPORTY [R3]: cron 'CM Reports Cron' ERweY5vHomrpw1SC (08:00 daily / nd 20:00 weekly, Europe/Warsaw)
  -> POST /reports/<kind> -> per supervised cel: zbiĂłr + UPSERT subagent_daily/weekly_reports + push bot #2;
  metryki: stats_mode per cel = manual (X, rÄ™czne w rozmowie) | member_api | org_api (LinkedIn po App 2 CMA)
```
| Tabele/kolumny mĂłzgu (DDL db/003..007, wszystkie LIVE) | Co trzymajÄ… |
|---|---|
| `user_agent_state` | aktywny agent + historia rozmowy per agent per czat (TTL 30 min) |
| `processed_updates` | dedup Telegram update_id |
| `cm_tasks` | ledger operacji LLM: task_type, tier, model, ĹşrĂłdĹ‚o tieru, tokeny, koszt USD |
| `agent_logs` | AUTONOMOUS_DECISION subagentĂłw (rationale + context) - jedna generyczna tabela |
| `subagent_daily_reports` / `subagent_weekly_reports` | raporty per cel per okres (UPSERT) |
| `published_posts` +content_item_id +engagement_metrics +embedding | archiwum publikacji = pamiÄ™Ä‡ cross-channel |
| `content_items.first_comment` + status 'proposed' | pod FazÄ™ 3 (komentarz) i FazÄ™ 2 (plan) |
| `channels.config` | publish_mode, supervised, language_publish, stats_mode, welcomed, (narrative/goals - Faza 2) |
| `brand_config` | voice_bible, language_comm, cm_tier_<task_type>, admin_chat_ids |
| `app_secrets` | wszystkie klucze (anthropic, x_, linkedin_, openai, telegram_bot_token, log_bot_token, guard) |

### E.5 Czego dalej NIE ma (Fazy 2-4 + otwarte)
Proaktywny planer (Faza 2: cron /plan -> propozycja tygodnia z brand_strategy+schowek+content_memory -> 'proposed' -> generacja T-24h), pierwszy komentarz (Faza 3), media (Faza 4), strony firmowe LinkedIn + metryki LinkedIn (token ze scope po review App 2 CMA), FB/IG/YT, tryb standalone subagentĂłw, multi-brand aktywny, peĹ‚ne i18n staĹ‚ych komunikatĂłw bota (przy 1. instalacji EN). Otwarte kosmetyki/dĹ‚ugi: tekst HITL po approve ("X scheduled, LinkedIn draft"), rotacja tokena Telegram (hardkody w starych wÄ™zĹ‚ach HITL), linkedin_client_secret w DB bĹ‚Ä™dny (token z Token Generatora, wygasa ~01/09/2026). **WARUNEK BRAMY 3 (Tomasz 04/07): jasna Ĺ›cieĹĽka wdroĹĽenia u osoby trzeciej (playbook instalacji sprzedawalnej) + diagram graficzny przepĹ‚ywu danych.**

---

## F. Notion = READ-ONLY MIRROR + sync worker DB->Notion (LIVE 05/07/2026, task #71)

**SSOT = PostgreSQL `ags_crd`.** Cala doktryna/prompty/raporty/decyzje/cennik/vendor/roadmapa
zmigrowane Fazami A-E (17 nowych tabel DDL 010-013; kotwice `notion_page_id` / `entry_hash` /
klucze naturalne). 67 stron Notion oznaczonych czerwonym calloutem "READ-ONLY MIRROR OD 05/07/2026"
(`etl/mirror_headers.py`, ledger: brand_config `mirror_headers_done`). Nowe wpisy WYLACZNIE przez
agentow do PostgreSQL; Notion odbija.

**Sync one-way DB->Notion (DDL 014+015 + `cm-agent/app/sync/`):**
- trigger `ags_sync_enqueue` (23 tabele) -> `sync_queue` + NOTIFY `ags_sync`;
- worker (watek w cm-agent, watchdog, log `logs/sync_worker.log`): LISTEN + poll 60s backstop,
  FOR UPDATE SKIP LOCKED, throttle 3 req/s, backoff 2..32s max 5 prob -> alert bot #2;
- wzorce: `re_render` (canonical; SOFT-CLEAR z trackingiem - nowa sekcja na gorze <10s,
  id-y blokow w `sync_mirror_state`, stara sekcja archiwizowana per blok) i `append` (dzienniki);
- sterowanie: `sync_registry` (enable tabeli = UPDATE, zero rebuildu; page_map dla brand_config)
  + flaga sprzedawalnosci `brand_config.sync_to_notion` per marka (v1: AGS on);
- v1 enabled: brand_config + manager_daily_log; drift check cron 03:00 (`app.sync.drift_check`,
  wykrywa reczne edycje callouta po md5 i zgubione triggery; alert Telegram bot #2).

**Zapis czego gdzie:** `sync_queue` (ledger zmian), `sync_mirror_state` (block_ids + last_checksum
+ callout_md5 per cel), `sync_registry` (konfiguracja). Raporty: docs/cm/RAPORT_do_Managera_71-{A..F}_*.

---

## G. Dzien 19/07/2026 - kanon publikacji + metryki + eskalacja (co gdzie zapisane)

**Kanon 19/07:** zatwierdzone publikuje sie ZAWSZE; niezatwierdzone NIGDY samo
(_emergency_promote USUNIETY z worker.py; >24h ciszy = decyzja 'stale_approval' guzikami).

| Przeplyw | Droga | Zapis |
|---|---|---|
| Metryki LinkedIn (xlsx) | Telegram dokument .xlsx -> HITL galaz document_xlsx -> Doc Secret -> Doc Metrics Fire -> POST /metrics/xlsx -> app/metrics_import.py (parser pozycyjny, locale-odporny) | `channel_metrics_daily` (dzienne; DDL 023), `channel_audience_snapshots` (demografia), merge per-post do `published_posts.engagement_metrics` (match URN); paragon na czat |
| Raporty subagenta | reports._profile_lines czyta channel_metrics_daily | sekcja PROFIL w raporcie dziennym/tygodniowym (>3 dni bez danych = prosba o eksport) |
| Decyzje ustrukturyzowane | tool escalate_decision / decisions.ask -> wiadomosc z guzikami dec:<id>:<key> -> HITL galaz dec: -> Dec Secret -> Dec Fire -> POST /decnav -> decisions.handle | `agent_decisions` + `decision_modes` (DDL 024) + wpis `agent_learning_log`; paragon nowa wiadomoscia; progi 10 odp./80% zgody -> propozycja semi-auto (mode_transition, tap Tomasza) |
| Watcher ciszy | worker._stale_approval_watch (petla) | decyzja stale_approval (Pokaz karte/Odrzuc/Przypomnij jutro), throttle w agent_decisions |
| Bramka tematow | planner (prompt: FILARY+ICP pierwsze, meta licznik) + twardy regex _meta_like + _enforce_plan_cap(20, wypycha NAJDALSZE sloty) + gap-filler na tym samym budzecie | odrzucenia RAPORTOWANE w wiadomosci planu; pusty plan NIGDY cichy (lista [meta]/[cel]/[slot]) |
| Ludzkie minuty | slots.humanize_slot przy KAZDYM wpisie slotu do post_queue (stage_variant + assign_if_needed) | pq = czas +/-15 min bez kwadransow; content_items = czysty slot planu (roznica ZAMIERZONA) |
| Dokumenty tekstowe | Telegram .md/.txt <=120KB -> HITL galaz document_text -> POST /docmsg -> conversation.handle_document | tresc jako [DOKUMENT: nazwa] do rozmowy aktywnego agenta (user_agent_state) |
| Grafika | gpt-image-2 (bump z image-1, docs-first) + prompt Sonneta zapamietywany w media[].image_prompt; guzik karty đź“‹ Prompt wysyla go do skopiowania (zewnetrzny generator -> âž• Media) | media jsonb w content_items/post_queue |
| UX kart | po decyzji nastepna karta NOWA wiadomoscia na dole (card_bottom); âž• Media bez floodu galeria (mgal na zadanie) | - |

Voice Bible: zderzenie Notion vs brand_config -> docs/cm/ZDERZENIE_VOICE_BIBLE_19072026.md
(sprzecznosc walutowa; rekomendacja brand_config=SSOT + voice_dna_core + mirror).

---

## H. Integracja 19/07 wieczor - 4 rownolegle buildy zmergowane (BE-INTEGRATOR)

Galezie build/kolektor-x + build/dedup + build/porzadki + build/czyta-swiat -> merge do
claude/silly-blackwell-dfc32d jedna paczka (raport: docs/cm/RAPORT_do_Managera_19072026_integracja.md).

| Przeplyw | Droga | Zapis |
|---|---|---|
| Kolektor metryk X (Owned Reads $0.001) | worker._x_collector_tick (raz na dobe UTC, durable guard po MAX(snapshot_date)) -> x_collector.collect: GET /2/users/{id}/tweets, OAuth1 HMAC-SHA1 ze stdlib, start_time=now-29d, exclude=retweets, paginacja z guardrail (alert >200, twardy stop 500) | `x_post_metric_snapshots` (DDL 025; UNIQUE tweet_id+snapshot_date, 3 namespaces jsonb) + followers -> `channel_metrics_daily` (source x_api, new_followers=diff); reports refresh_metrics 'x_owned_reads' merguje NAJNOWSZY snapshot do `published_posts.engagement_metrics` bez platnych odczytow. Tick SPI dopoki `channels.config.stats_mode` != 'x_owned_reads' (reczny UPDATE po sondzie + potwierdzeniu ceny w konsoli). x_user_id cache w channels.config |
| Bramka duplikacji tezy | worker._draft (za compliance.enforce) -> content_memory.dup_check: embedding canonicala vs OPUBLIKOWANE ostatnich 30 dni (pgvector cosine), prog 0.85 (override: /set cm_dup_threshold) | descriptor `{kind:'dup_warning'}` w `content_items.media` -> karta matreview pokazuje âš ď¸Ź DUPLIKACJA; INFORMUJE, nie blokuje; regeneracja czysci stary warning; degradacja bez crashy (brak klucza/dopasowania = brak linii) |
| Route komend configu (porzadki A) | conversation.handle: regex PRZED LLM - _USTAW_OKNO_RE ("ustaw okno dla <brand> <channel> na HH:MM-HH:MM") + _USTAW_KEY_RE (allowlista _CONFIG_KEYS: publish_windows, publish_mode, language_publish, posts_per_day, follower_count, thread_enabled, voice_note, secret_prefix, emergency_publish) | _target_update -> `channels.config` + paragon âš™ď¸Ź; klucz spoza allowlisty na istniejacym celu = szczera odmowa (koniec "Zrobione" bez wykonania) |
| Odrzucenie karty sprzata kolejke (porzadki B) | matreview akcja 'no' po set_item_status | `post_queue` wiersze materialu (review/held/scheduled/queued) -> rejected; sieroty historyczne = SQL w raporcie porzadkow (wykonuje Tomasz) |
| CM czyta swiat (sobotni podklad) | worker sunday_brief.tick (sobota 08:00-12:30) -> Researcher POST /request (tier cap medium) -> polling research_jobs -> synteza Sonnet: claims + LINKI zrodel (join `evidence_id::text = ANY(supporting_evidence)` - zywa baza ma text[], nie uuid[]) + schowek 7 dni + top publikacje | sendMessage: 3 kandydackie tezy z liczbami i linkami (landing ~11:00-13:00); ZERO wpisu do content_items/post_queue; stan anty-dublowy `brand_config.cm_sunday_brief`; tap-test: narzedzie sunday_world_brief ("podklad na niedziele"); fallback z JAWNYM "research nie dojechal" |

---

## D. Do udokumentowania dalej
- [x] Researcher LIVE: diagram graficzny (`docs/researcher-dataflow.svg`) + 3 adaptery w repo (`n8n-workflows/researcher/`) + deploy/README.
- [ ] OpenAI DR + Manus adaptery (fast-follow) - dopisaÄ‡ gdy zbudowane (+ do `DEPLOYED_ADAPTERS`).
- [ ] HITL handler: peĹ‚ny graf capture->triage->research->content gate (rozwinÄ…Ä‡ z wÄ™zĹ‚Ăłw).
- [ ] **Diagram graficzny CAĹOĹšCI** (pipeline treĹ›ci + Researcher + sieÄ‡ agentĂłw) - cel sprzedaĹĽowy.
