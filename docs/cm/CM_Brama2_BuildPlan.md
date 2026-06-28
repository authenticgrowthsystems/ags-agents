# CM - Brama 2: Plan Budowy (build plan)

**Data:** 28/06/2026. **Autor:** AGS Build Engineer (Opus 4.8). **Wejście:** zablokowana architektura (CM_Architecture_Synthesis_BE.md sekcja 6). **Cel:** konkretny, wykonalny plan -> build 30/06-01/07 -> Brama 3 02/07.
**Stack (jak Researcher):** Python FastAPI + psycopg3/`psycopg_pool` + surowy SQL; n8n adaptery; Postgres `ags_crd` SSOT; sekrety w `app_secrets`; guard `X-Researcher-Secret`-style; sieć `n8n_network`; modele haiku=`claude-haiku-4-5-20251001` / sonnet=`claude-sonnet-4-6` / opus=`claude-opus-4-8`.

## 1. Nowy serwis: `cm-agent/` (sibling do `ags-researcher/`)

```
cm-agent/
  app/
    config.py     # tiery+modele, budżety, helper rejestru kanałów, ścieżki adapterów
    db.py         # psycopg_pool, claim_content_item (FOR UPDATE SKIP LOCKED), helpery
    models.py     # pydantic: ContentItem, ChannelVariant, BrandStrategy
    brand.py      # load brand_config.voice_bible + brand_strategy; blok prompt-cache; voice_hash
    generate.py   # Sonnet: kanoniczny tekst-matka; Haiku: warianty per-kanał
    compliance.py # em-dash/banned-vocab/voice (deterministyczny regex + Haiku fallback)
    channels.py   # rejestr + GENERYCZNY dispatch konektora (active/draft/ready)
    research.py   # zlecenie do Researchera (/request, max medium) + obsługa callbacku
    hitl.py       # Telegram 3 bramy (plan / materiał / publikacja)
    worker.py     # FastAPI /health /metrics /request + pętla state-machine
  db/001_init.sql
  Dockerfile  requirements.txt  .env.example  README
```
Port np. `127.0.0.1:8089` (Researcher ma 8088), sieć `n8n_network`, `.env` = tylko `POSTGRES_DSN`+`N8N_BASE_URL`. Sekrety (anthropic/x/telegram) z `app_secrets` przy starcie.

## 2. DDL (cm-agent/db/001_init.sql, do ags_crd) - 3 nowe tabele + tenant anchor

```sql
-- tenant anchor (lekki rejestr marek; cel FK dla brand_id)
CREATE TABLE IF NOT EXISTS brands (
  brand_id    VARCHAR(50) PRIMARY KEY,           -- 'AGS','TNM','RDC','SDI',...
  brand_name  TEXT NOT NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- mózg treści: jeden kanoniczny obiekt per pomysł/plan
CREATE TABLE IF NOT EXISTS content_items (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id      VARCHAR(50) NOT NULL REFERENCES brands(brand_id),
  master_theme  TEXT NOT NULL,
  canonical_body TEXT,                            -- tekst-matka (Sonnet); NULL dopóki nie wygenerowany
  taxonomy      VARCHAR(30) CHECK (taxonomy IN ('build-report','news','edu')),
  target_channels TEXT[] NOT NULL DEFAULT '{}',   -- np. {x,linkedin}
  research_job_id UUID,                           -- link do research_jobs (Researcher)
  inspiration_id  UUID,                           -- link do inspirations
  status        VARCHAR(30) NOT NULL DEFAULT 'planned'
                  CHECK (status IN ('planned','needs_research','researching','drafting',
                                    'needs_approval','approved','dispatching','published','rejected','failed')),
  scheduled_for TIMESTAMPTZ,
  voice_hash    TEXT,                             -- snapshot wersji głosu przy generacji
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_items_brand   ON content_items(brand_id);
CREATE INDEX IF NOT EXISTS idx_content_items_status  ON content_items(status);

-- strategia per marka (projekcja warstwy Obsidian/Manager; CM czyta przy generacji)
CREATE TABLE IF NOT EXISTS brand_strategy (
  brand_id        VARCHAR(50) PRIMARY KEY REFERENCES brands(brand_id),
  target_audience TEXT,
  content_pillars TEXT[] DEFAULT '{}',
  core_topics     TEXT[] DEFAULT '{}',
  competitor_urls TEXT[] DEFAULT '{}',
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GENERYCZNY rejestr kanałów/subagentów (channel = dowolny string, NIE enum)
CREATE TABLE IF NOT EXISTS channels (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id      VARCHAR(50) NOT NULL REFERENCES brands(brand_id),
  channel       VARCHAR(40) NOT NULL,             -- 'x','linkedin','youtube','facebook','instagram','tiktok',...
  status        VARCHAR(20) NOT NULL DEFAULT 'ready' CHECK (status IN ('active','draft','ready','paused')),
  adapter_path  TEXT,                             -- webhook publish adaptera (NULL dla draft/ready)
  config        JSONB DEFAULT '{}'::jsonb,
  UNIQUE (brand_id, channel)
);
CREATE INDEX IF NOT EXISTS idx_channels_brand ON channels(brand_id);
```
Wszystko `brand_id NOT NULL` + indeks = **RLS-ready** (polityki dodamy przed 2. marką). `post_queue` reuse jako outbox per-wariant (dopiszemy `content_item_id` UUID kolumnę przez ALTER). `published_posts`, `inspirations`, `brand_config` bez zmian.

## 3. Generyczny kontrakt konektora subagenta (open/closed)

Jeden kontrakt dla WSZYSTKICH subagentów (kanały + Researcher + przyszli):
- **Dispatch:** CM POST na webhook subagenta `{brand_id, content_item_id, channel, payload, correlation_id, callback}` -> subagent 202.
- **Praca async** -> callback POST z wynikiem -> CM aktualizuje stan. Księga w `agent_messages`.
- **Kanał** = subagent rodzaju "publisher". `channels.status`: `active` -> generuj wariant (Haiku) + publish przez `adapter_path`; `draft` -> generuj wariant + zapis do `post_queue` jako draft (publikacja ręczna); `ready` -> pomiń (moduł nie wpięty). Dodanie kanału = INSERT do `channels` + implementacja adaptera n8n do tego samego wywołania. ZERO zmian w CM core.
- X = istniejący adapter (OAuth1 publish). LinkedIn = `draft`. YT/FB/IG/TikTok/... = `ready`.

## 4. Pętla CM (worker.py, state machine)

`claim_content_item` (SKIP LOCKED) -> wg `status`:
`planned` -> (jeśli target wymaga dowodów) `needs_research` -> zleć Researcher (/request medium), zapisz `research_job_id`, `researching`; po callbacku -> `drafting`.
`drafting` -> `generate.canonical` (Sonnet, blok prompt-cache: tools->system->voice_bible[cache_control]->dynamiczny kontekst; zapisz `voice_hash`) -> `compliance` (em-dash/banned/voice; fail -> Haiku redraft) -> `needs_approval`.
`needs_approval` -> HITL brama (Telegram, guziki) -> approve -> `approved` / reject -> `rejected`.
`approved` -> `dispatching`: dla każdego `target_channels` -> `channels.dispatch` (active publish / draft store) -> `published_posts` log -> `published`.
Event-driven: `/request` budzi pętlę (wake event, jak Researcher); poll 30s backstop. Cron (n8n) tylko do planowania due items.

## 5. Workflowy n8n

- **Reuse:** X publish adapter (istnieje), HITL handler `U5pUZjy2yAhR1sWg` - dodać gałąź callbacku `cm:<...>` (wzorzec jak `crit:`/`mtier:` z dziś).
- **Nowe:** CM content-planning scheduler (cron -> due content_items -> budzi CM); LinkedIn draft = bez adaptera (CM pisze do post_queue). YT/FB/IG = stub adaptery (placeholder webhook zwracający 'not_implemented') do czasu aktywacji.

## 6. Plan testów (Brama 3, 02/07)

1. Apply DDL (Tomasz SSH). Seed: `brands`(AGS), `brand_strategy`(AGS pillars/audience), `channels`(AGS: x=active, linkedin=draft, youtube/facebook/instagram=ready), agent_registry `content-manager` (`allowed_model_tiers=['low','medium']`).
2. Deploy kontener cm-agent (build+run, /health ok).
3. E2E: utwórz `content_item` (temat, target {x,linkedin}) -> CM Sonnet kanoniczny -> (opcj. Researcher medium) -> compliance (zero em-dash) -> HITL Telegram approve -> dispatch: X wariant (Haiku) auto-publish + LinkedIn wariant draft do post_queue -> published_posts log -> status `published`.
4. Weryfikacja: brand-aware głos (voice_hash zapisany), 3 bramy HITL działają, X publikuje, LinkedIn draft powstaje, dodanie nowego kanału = sam INSERT do channels (test open/closed na stub TikTok).

## 7. Otwarte decyzje build-planu (do potwierdzenia punkt-po-punkcie)

- **B-D1:** tenant anchor `brands` (osobna lekka tabela, FK dla brand_id - rekomendacja) vs brand_id jako walidowany TEXT bez FK.
- **B-D2:** HITL CM - rozszerzyć istniejący handler `U5pUZjy2yAhR1sWg` (gałąź `cm:`) vs osobny CM HITL handler.
- **B-D3:** planowanie - n8n cron budzi CM (spójne z "n8n=egzekutor") vs APScheduler w serwisie CM.
- **B-D4:** wariant kanałowy - generowany przy dispatch (lazy, świeży) vs przy approval (cache'owany w post_queue wcześniej).
