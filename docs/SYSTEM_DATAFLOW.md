# AGS System - Mapa przepływu danych i zapisu (living doc)

**Status:** ŻYWY dokument, aktualizowany przy każdej zmianie przepływu. To SUBSTRAT pod docelowy **diagram graficzny** (renderowany, gdy build skończony) - część pakietu sprzedażowego produktu.
**Zasada nadrzędna:** jedno źródło prawdy = PostgreSQL (`ags_crd`). Notion = lustro dla człowieka, nie źródło dla agentów.
**Ostatnia aktualizacja:** 24/06/2026.

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
| `research_jobs` | master per zapytanie: `query_text`, `query_hash`, `query_embedding` VECTOR(1536), `complexity`, `status`, `cost_pln`, `confidence_score` | Researcher worker [W/R] |
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

## C. Researcher - przepływ (Faza 0.5, w budowie)

**Topologia:** Hub-and-Spoke async. Orkiestracja w **kontenerze Python** (`ags-researcher`), n8n = adaptery źródeł + ingress + status polling.

```
Agent-klient / Tomasz --(REQUEST agent_messages)--> [n8n Ingress] --INSERT--> research_jobs(enqueued)
   worker poll (FOR UPDATE SKIP LOCKED):
     QueryRouter.classify -> CacheLayer (exact SHA-256 [+ semantic pgvector])
       hit  -> options [W] -> completed -> callback
       miss -> BudgetGovernor.preflight -> dispatch adaptery n8n (wg policy low/med/high/critical)
                -> evidence_items [W] + cost_events [W] (per research_run)
                -> FailureHandler.assess
                -> Synthesizer (Sonnet 4.6, prompt cache, structured output = 4 opcje)
                -> claims [W] + options [W] -> research_jobs.completed (+cost_pln,confidence) [W]
                -> [n8n callback] -> agent_messages RESPONSE [W] + Telegram
```
- **Co gdzie zapisywane:** job -> `research_jobs`; każde źródło -> `research_runs` + `evidence_items` + `cost_events`; synteza -> `claims` + `options`; wynik dla klienta -> `agent_messages` (RESPONSE).
- **Eskalacja kosztowa:** low=WebSearch; medium=+Firecrawl; high=+OpenAI DR (o4-mini); critical=+o3/Manus/Gemini. Twarde stopy: 50/100/1500 PLN.
- **Moduły Python:** `router`, `cache`, `budget`, `prompts`, `synth`, `failure`, `sources`; `worker` (pętla + FastAPI `/health` `/metrics`). Szczegóły w `ags-researcher/`.

---

## D. Do udokumentowania dalej
- [ ] 6 workflowów n8n Researchera (5 adapterów + ingress/callback) - node-by-node (Day 3).
- [ ] HITL handler: pełny graf capture->triage->research->content gate (rozwinąć z węzłów).
- [ ] **Diagram graficzny całości** (gdy build skończony) - cel sprzedażowy.
