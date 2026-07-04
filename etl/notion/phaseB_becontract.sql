-- TASK #71 FAZA B czesc 2: be_contracts <- BE Contract Faza 0 v2 (05/07/2026). Idempotentne.
INSERT INTO be_contracts (version, title, content, status, notion_page_id)
SELECT '2', 'AGS BE Contract Faza 0 v2 (18/06/2026) - Approval Gate Process + Researcher Faza 0.5 + Firecrawl',
$n71$# AGS Build Engineer Faza 0 — Kontrakt szczegółowy v2

**Data:** 18/06/2026 (wersja v2 po zatwierdzeniu Zasady 7 canonical)
**Owner:** Manager AGS (interim, Cowork) → przekazanie do Build Engineer (BE) po zatwierdzeniu Tomasza
**Bazuje na:** Blueprint v1.3 (Notion 383c00c90b9381c285c3eaa1e2e50940, workspace AGS_Blueprint_Agent_Architecture_v1_3_18062026.md)
**Status:** DRAFT v2 do review Tomasza, potem wysłanie BE
**Zmiana vs v1:** Nowa sekcja 15 Approval Gate Process per agent plus nowa tabela agent_approval_gates w DDL plus Researcher Faza 0.5 plus Firecrawl integration plus update Faza 0 acceptance criteria plus update timeline

---

## 1. CEL FAZY 0 (rozszerzony v2)

Stworzyć kompletny fundament infrastruktury PostgreSQL plus dokumentacji Notion plus Approval Gate Process żeby Faza 0.5 (Researcher build) mogła zacząć BEZ pytania o szczegóły schematów ani brakujących Chartersów ani procedur approval. Faza 0 musi zostawić BE z deployowalną bazą danych plus 9 Chartersami human-readable plus planem transferu pamięci i wiedzy plus procedurami gate.

Po Fazie 0 stan systemu: PostgreSQL ma 18 tabel (6 LIVE plus 12 nowych w v2), agent_registry zasiedlone wpisami dla wszystkich agentów (X Agent i Idea-bot mają status='active' plus current_gate='active', reszta status='planned' plus current_gate='awaiting_research'), brand_config zasiedlone wartościami canonical, skills_registry zasiedlone core skills per agent typ, 9 Chartersów w Notion plus dedykowany Charter Researcher gotowy do Fazy 0.5 Brama 1, agent_approval_gates pusta tabela gotowa do logging.

---

## 2. TECH STACK (zatwierdzony, plus Firecrawl v2)

| Warstwa | Tool | Status |
|---|---|---|
| Serwer | Mikrus ivy147 (4 GB RAM, 40 GB disk) | LIVE |
| Konteneryzacja | Docker plus Docker Compose plus Watchtower | LIVE |
| Język agentów | Python 3.11 plus | nowy per agent kontener |
| Integracje API | n8n workflows | LIVE plus rozszerzenia per faza |
| Baza danych | PostgreSQL 15.17 (container pg_n8n) | LIVE plus 12 nowych tabel Faza 0 v2 |
| Message bus | agent_messages tabela | nowa Faza 0 |
| Approval Gate Logging | agent_approval_gates tabela | nowa Faza 0 v2 |
| Telegram | python-telegram-bot library | LIVE w X Agent plus idea-bot |
| Modele AI | Anthropic Claude API | LIVE auto-reload |
| Researcher external sources | Gemini API, Manus API, ChatGPT API, **Firecrawl API** (NEW v2), Web Search | wszystkie do integracji w Fazie 0.5 |
| Object storage | TBD parking (Mikrus disk lub Backblaze B2) | dla marketing_knowledge_base PDFów |

---

## 3. POSTGRESQL DDL — 18 TABEL (12 nowych v2, 6 LIVE)

### 3.1 Tabele LIVE od 31/05 (sekcja bez zmian od v1)

contacts, engagement_log, hitl_sessions, published_posts, task_queue, brand_config foundation. Patrz v1 sekcja 3.1.

### 3.2 Tabele tożsamości i konfiguracji (sekcja bez zmian od v1 PLUS update agent_registry)

agent_registry, agent_contracts, skills_registry — patrz v1 sekcja 3.2 z DROBNĄ ZMIANĄ w agent_registry:

```sql
-- agent_registry update v2: dodanie kolumny current_gate dla quick filter
ALTER TABLE agent_registry ADD COLUMN current_gate VARCHAR(30) NOT NULL DEFAULT 'awaiting_research'
    CHECK (current_gate IN (
        'awaiting_research', 'awaiting_build_approval',
        'awaiting_acceptance', 'active', 'paused', 'retired'
    ));

CREATE INDEX idx_agent_registry_gate ON agent_registry(current_gate);
```

Wartość current_gate jest synchronizowana z status:
- planned → awaiting_research (po wpisie do agent_registry)
- planned → awaiting_build_approval (po Brama 1 approved)
- building → awaiting_acceptance (po Brama 2 approved plus BE rozpoczyna build)
- active → active (po Brama 3 approved)

### 3.3 Tabele komunikacji (sekcja bez zmian od v1)

agent_messages z 6 typami. Patrz v1 sekcja 3.3.

### 3.4 Brand_config (sekcja bez zmian od v1)

brand_config_new pełna struktura plus seed values dla AGS. Patrz v1 sekcje 3.4 plus 4.

### 3.5 Tabele pamięci i logu (sekcja bez zmian od v1)

agent_logs_template per agent, memory_snapshots, hitl_queue. Patrz v1 sekcja 3.5.

### 3.6 Tabele operacyjne (sekcja bez zmian od v1)

content_calendar, inspirations_pool. Patrz v1 sekcja 3.6.

### 3.7 Tabele marketing i reklama (sekcja bez zmian od v1)

marketing_knowledge_base z pgvector, campaigns, ad_creatives. Patrz v1 sekcja 3.7.

### 3.8 Tabele GHL Specialist (sekcja bez zmian od v1)

ghl_rss_feeds, ghl_changelog_log. Patrz v1 sekcja 3.8.

### 3.9 NOWA TABELA v2 — Approval Gates

```sql
-- =================================================================
-- AGENT APPROVAL GATES — historia approvals per agent (3 bramy)
-- Zasada 7 canonical Blueprint v1.3
-- =================================================================
CREATE TABLE agent_approval_gates (
    gate_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id             UUID NOT NULL REFERENCES agent_registry(agent_id),
    gate_type            VARCHAR(20) NOT NULL CHECK (gate_type IN (
                             'research', 'build', 'acceptance'
                         )),
    iteration            INTEGER NOT NULL DEFAULT 1,           -- 1, 2, 3 itd jeśli rejects
    status               VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
                             'pending', 'approved', 'rejected', 'expired'
                         )),
    submitted_by         VARCHAR(100),                          -- 'manager-ags-cowork', 'be-claude-code', 'researcher-server'
    submitted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    research_output      JSONB,                                 -- brama 1: 4+ opcje plus sources plus rekomendacja
    build_plan           JSONB,                                 -- brama 2: model_tier, tools, decision_authority, Charter draft
    test_results         JSONB,                                 -- brama 3: test runs, sample outputs, compliance check
    approver             VARCHAR(100) NOT NULL DEFAULT 'tomasz',
    approved_at          TIMESTAMPTZ,
    approval_notes       TEXT,
    rejection_reason     TEXT,
    next_iteration_due   TIMESTAMPTZ
);

CREATE INDEX idx_agent_approval_gates_agent   ON agent_approval_gates(agent_id);
CREATE INDEX idx_agent_approval_gates_status  ON agent_approval_gates(status);
CREATE INDEX idx_agent_approval_gates_type    ON agent_approval_gates(gate_type, status);
CREATE INDEX idx_agent_approval_gates_submitted ON agent_approval_gates(submitted_at DESC);
```

---

## 4. SEED VALUES dla brand_config (AGS startup) — bez zmian od v1

Patrz v1 sekcja 4.

---

## 5. SEED VALUES dla skills_registry — update v2

Patrz v1 sekcja 5 plus dorzucenie:
- `firecrawl_web_extraction` (Research, core_only, Researcher) — structured web extraction
- `multi_source_synthesis` (Research, core_only, Researcher) — synteza 5 source pluginów do 4+ opcji
- `approval_gate_management` (Operations, core_only, Manager AGS) — orchestracja Bramy 1-2-3
- `research_master_prompt_engineering` (Research, core_only, Researcher plus Manager AGS interim) — generowanie master promptów per source

---

## 6. CHARTERS NOTION — 9 NOWYCH AGENTÓW (update Researcher v2)

BE tworzy 9 Charters per v1 sekcja 6. Charter Researcher dostaje update v2 z Firecrawl integration:

### 6.3 Researcher Charter v2 (updated)

**Kim jestem:** Cross-cutting Specialist pod Managerem AGS, dostarczający deep research na zlecenie wszystkich agentów ekosystemu.

**Misja:** Każda strategiczna decyzja w AGS opiera się na rzetelnym, wielo-źródłowym researchu z minimum 4 opcjami i sources, nigdy na jednej opinii lub kompulsywnej decyzji.

**Co robię:**
- Otrzymuję REQUEST przez agent_messages z payload zawierającym pytanie research plus context
- Generuję master prompty per source (5 równoległych pluginów)
- Wywołuję n8n workflows do 5 sources równolegle:
  1. **Gemini API** (Deep Research z grounding na search results)
  2. **Manus API** (Execution Analysis — jeśli Manus pozwala API access, alternatywa: n8n controller przez web automation)
  3. **ChatGPT API** (GPT-4o lub successor, synteza syntetyczna, alternatywne perspective)
  4. **Firecrawl API** (structured web extraction — GHL docs, Meta API docs, research papers, blogposts)
  5. **Web Search** built-in Claude (Anthropic-side fallback)
- Synthesizuję wszystkie wyniki przez Sonnet 4.6:
  - Konwergencja: co wszystkie źródła potwierdzają
  - Dywergencja: gdzie source różnią się
  - Minimum 4 alternatywne opcje z plus/minus każdej
  - Rekomendacja jeśli pytanie tego wymaga
- RESPONSE do klienta agent przez agent_messages plus log w agent_logs

**Czego NIE robię:**
- Nie podejmuję decyzji strategicznych (tylko dostarczam opcje, decyduje klient agent lub Tomasz)
- Nie tworzę treści finalnych do publikacji (od tego CM plus Sub-Agenty)
- Nie buduję infrastruktury (od tego BE)
- Nie zarządzam relacjami z klientami (od tego Opiekun Relacji)

**Gdzie raportuję:**
- agent_messages RESPONSE do klienta inicjującego REQUEST
- agent_logs własna tabela (typ ACTION per query, typ MILESTONE per ukończona synteza)
- weekly retrospective: piątek wieczór do Manager AGS z agregowanymi metrykami (queries served, average synthesis time, cost per query, client satisfaction)

**Gdzie szukam kontekstu (start-of-session checklist):**
- brand_config aktualny stan
- Master prompts library w marketing_knowledge_base (cached templates per query type)
- Ostatnie 20 wpisów w agent_logs siebie (recent queries pattern)
- agent_approval_gates pending (jeśli któryś agent czeka na Brama 1 research, priorytet)

**Moje limity decyzyjne:**
- Sam: wybór sources per query, generowanie master promptów, synteza, format output
- Approval klienta agent: jeśli query wymaga eskalacji budżetu (Firecrawl crawl powyżej 1 USD per query)
- Approval Tomasz: każda zmiana podstawowej listy sources (np. dorzucenie nowego API), zmiana w master prompt templates dla canonical query types

**Tools allowed:**
- Anthropic Claude API (Sonnet 4.6 dla synthesis)
- Gemini API
- Manus API plus alternative web automation
- ChatGPT API
- **Firecrawl API** (klucz Tomasz przekazuje BE do n8n credentials store)
- Web Search built-in
- PostgreSQL read/write (own logs plus master prompts cache)
- agent_messages read/write
- Notion MCP read (canonical docs reference)

**Core skills:**
- deep_research_synthesis
- master_prompt_engineering
- multi_source_synthesis
- firecrawl_web_extraction
- brand_canon_compliance

**Success metrics (trzy KPI):**
- queries_served_weekly (liczba ukończonych REQUEST)
- average_synthesis_time_minutes
- client_satisfaction_score (klient agent po otrzymaniu RESPONSE może rate 1-5)

**Cost limit:**
- Daily: 100 PLN (około 25 USD)
- Monthly: 1500 PLN (około 375 USD)
- Alert do Managera AGS jeśli daily przekroczony, eskalacja do Tomasza jeśli monthly grozi

---

## 7. PLAN TRANSFERU PAMIĘCI MANAGERA (bez zmian od v1)

Patrz v1 sekcja 7.

---

## 8. PLAN TRANSFERU WIEDZY MARKETERA (bez zmian od v1)

Patrz v1 sekcja 8.

---

## 9. CONTINUITY MODEL — INTERIM EQUILIBRIUM (bez zmian od v1)

Patrz v1 sekcja 9.

---

## 10. PHASED ROLLOUT v2 — Faza 0 plus 0.5 plus Approval Gate

### Faza 0 acceptance criteria v2 (update z v1)

- [ ] PostgreSQL ma 12 nowych tabel utworzonych zgodnie z DDL sekcji 3 (11 z v1 plus agent_approval_gates nowa)
- [ ] agent_registry zaktualizowane z kolumną current_gate
- [ ] brand_config_new zasiedlone wpisem dla brand_id='ags' z wartościami canonical
- [ ] skills_registry zasiedlone minimum 29 core skills (25 z v1 plus 4 nowe v2: firecrawl_web_extraction, multi_source_synthesis, approval_gate_management, research_master_prompt_engineering)
- [ ] agent_registry zasiedlone 23 wpisami z odpowiednim current_gate:
  - X Agent: status='active', current_gate='active' (retroactive approval LIVE od 31/05)
  - Idea-bot: status='active', current_gate='active' (retroactive approval LIVE od 11-12/06)
  - Reszta 21 wpisów: status='planned', current_gate='awaiting_research'
- [ ] 9 Charters Notion utworzonych pod hub AGENCI Charters & Protokoły (z Researcher Charter v2 zawierający Firecrawl plus 5 sources spec)
- [ ] Memory transfer manifest gotowy
- [ ] Dashboard live artifact updated z statusem "Faza 0 complete, Faza 0.5 ready to start"

### Faza 0.5 acceptance criteria NEW v2

**Day 1 — Brama 1 Research dla Researcher (manual interim):**
- [ ] Manager AGS przygotował master prompty do 4 sources (Gemini DR, Manus, ChatGPT, Firecrawl URL list)
- [ ] Tomasz odpalił queries równolegle
- [ ] Wyniki zebrane plus Manager AGS syntezuje plus 4+ opcji architektury Researcher z trade-off i sources
- [ ] Wpis w agent_approval_gates: agent_id=Researcher, gate_type='research', status='pending', research_output JSONB
- [ ] Tomasz approves wybraną opcję, status='approved', approved_at timestamp

**Day 2 — Brama 2 Build Approval dla Researcher:**
- [ ] BE drafts plan implementacji: model_tier='sonnet-4-6', tools_allowed=['Gemini API', 'Manus API', 'ChatGPT API', 'Firecrawl API', 'Web Search'], decision_authority full per scope, success_metrics 3 KPI, Charter draft v2 jak sekcja 6 wyżej
- [ ] Wpis w agent_approval_gates: agent_id=Researcher, gate_type='build', iteration=1, build_plan JSONB
- [ ] Tomasz approves plan, status='approved'

**Day 3-4 — BE buduje Researcher container:**
- [ ] Docker container z Python 3.11 plus Anthropic SDK plus PostgreSQL driver
- [ ] n8n workflows utworzone i przetestowane per source:
  - "Researcher - Gemini DR Query"
  - "Researcher - Manus Execution Query"
  - "Researcher - ChatGPT Query"
  - "Researcher - Firecrawl Scrape" (z kluczem API od Tomasza w credentials store)
  - "Researcher - Web Search"
- [ ] Master prompt builder framework (Python module)
- [ ] Synteza framework (Sonnet 4.6 call z dedykowaną instrukcją output 4+ opcji)
- [ ] Researcher container deployed, status w agent_registry='building', current_gate='awaiting_acceptance'

**Day 5 — Brama 3 Acceptance Gate dla Researcher:**
- [ ] BE odpala test query: "Najlepsze praktyki dla orkiestracji multi-agent systemu na PostgreSQL: 4+ opcji architekturalnych z trade-off i sources"
- [ ] Researcher odbiera REQUEST, generuje master prompty, odpala 5 sources równolegle, syntezuje
- [ ] Test results JSONB: czas trwania, koszt API, jakość syntezy, sources cited, brand canon compliance (sprawdza Manager AGS)
- [ ] Wpis w agent_approval_gates: agent_id=Researcher, gate_type='acceptance', test_results JSONB
- [ ] Tomasz weryfikuje jakość, approves, status w agent_registry='active', current_gate='active'

Po Fazie 0.5: Researcher LIVE plus gotowy do automatyzacji Bramy 1 dla wszystkich kolejnych agentów Fazy 1 plus.

### Fazy 1-5 acceptance criteria

Każdy agent Fazy 1 plus przechodzi przez 3 bramy:
- **Brama 1**: BE delegate REQUEST do Researcher z pytaniem "architektura agenta X" → Researcher zwraca 4+ opcje → Tomasz approves
- **Brama 2**: BE drafts build plan bazując na approved opcji → Tomasz approves
- **Brama 3**: BE przeprowadza test runs → Tomasz approves → status='active'

Czas per agent: 2-3 dni (1 dzień research, 0.5 dnia approval iterations, 1-1.5 dnia build, 0.5 dnia testing/acceptance). Parallel build kilku agentów jednocześnie redukuje total time.

---

## 11. REPORTING PROTOCOL BE → MANAGER AGS (bez zmian od v1)

Patrz v1 sekcja 11.

---

## 12. DEPENDENCIES PLUS BLOKERY v2 (update z v1)

**Dependencies do Faza 0**:
- Jak w v1
- **NEW**: Firecrawl API klucz od Tomasza przekazany do n8n credentials store (Day 1 Faza 0.5)

**Potential blokery**:
- Jak w v1
- **NEW**: Manus API access — jeśli Manus.im nie pozwala API direct, BE buduje workaround przez n8n web automation lub używa Manus tylko interactively. Manager AGS researches alternative path podczas Fazy 0.5 Day 1.
- **NEW**: Researcher cost overrun — jeśli pierwsze testy pokazują że 5 sources per query kosztuje powyżej 1 USD, optymalizacja przez cache plus selective source activation per query type.

---

## 13. ESTIMATED TIMELINE v2

- **Faza 0**: 3-5 dni (DDL plus seed plus 9 Charters plus 1 nowa tabela vs v1)
- **Faza 0.5**: 5 dni (Day 1 manual research plus Day 2 approval plus Day 3-4 build plus Day 5 acceptance)
- **Razem przed Fazą 1**: 8-10 dni

Faza 1 plus z gates per agent: 7-10 dni dla 5 agentów (CM plus LinkedIn SM plus IG plus FB plus GHL Specialist parallel).

---

## 14. ZIELONE ŚWIATŁO (bez zmian od v1)

Tomasz potwierdza ten kontrakt v2. Po zatwierdzeniu Manager AGS:
1. Wysyła link BE via Telegram z prośbą o potwierdzenie acceptance i ETA Dnia 1 Fazy 0
2. Update task #56 do completed
3. Update Master TODO i MANAGER Daily Status
4. Update dashboard live artifact "Faza 0 kontrakt v2 sent to BE, awaiting acceptance"
5. Manager AGS rozpoczyna przygotowanie master promptów dla Researcher Day 1 Faza 0.5 (manual research)

---

## 15. NEW v2 — APPROVAL GATE PROCESS — operational details

### 15.1 Brama 1 Research Gate

**Trigger**: Manager AGS lub Tomasz inicjuje brief research o agencie X (lub krytyczna decyzja strategiczna).

**Interim do Fazy 0.5** (manual):
- Manager AGS Cowork pisze master prompty do każdego source
- Tomasz odpala queries plus zbiera wyniki
- Manager AGS syntezuje plus 4+ opcji z trade-off
- Wpis w agent_approval_gates manualnie przez Cowork Manager (lub Tomasz przez Telegram bot komendy /research_submit)

**Post Fazy 0.5** (automatic):
- Klient agent (Manager AGS, lub bezpośrednio od Tomasza) wysyła REQUEST do Researcher przez agent_messages
- Researcher odpala 5 sources równolegle przez n8n workflows
- Researcher syntezuje plus 4+ opcji
- Researcher tworzy wpis w agent_approval_gates: agent_id=target_agent, gate_type='research', research_output JSONB
- Telegram notification do Tomasza z linkiem

**Tomasz response options:**
- Approve opcję X (status='approved', approved_at, approval_notes=które opcje wybrane)
- Reject z prośbą o pogłębienie (status='rejected', rejection_reason, next_iteration_due, Researcher iteracja 2)
- Edit z dorzuceniem własnych wytycznych (status='approved' plus approval_notes z modyfikacjami)

**Po approval**: target_agent.current_gate w agent_registry zmienia się z 'awaiting_research' na 'awaiting_build_approval'.

### 15.2 Brama 2 Build Approval Gate

**Trigger**: Brama 1 approved.

**BE actions:**
- BE drafts Charter (Notion) plus konkretny plan implementacji JSONB:
  - model_tier (opus-4-6, opus-4-8, sonnet-4-6, haiku-4-5)
  - tools_allowed (lista konkretnych API i MCP)
  - decision_authority (per action_type: auto/notify/approve)
  - escalation_rules JSONB
  - success_metrics (3 KPI)
  - cost_limit_daily_pln plus cost_limit_monthly_pln
  - core_skills plus skills_enabled
  - Sub-Agents do utworzenia (jeśli applicable)
  - Docker container spec plus n8n workflows do utworzenia
- BE tworzy wpis w agent_approval_gates: gate_type='build', iteration=1, build_plan JSONB
- Telegram notification do Tomasza z linkiem do Charter Notion plus build_plan

**Tomasz response options:**
- Approve plan (status='approved', BE rusza build)
- Reject z prośbą o korekty (status='rejected', rejection_reason, BE iteracja 2)
- Edit (np. "model Sonnet zamiast Opus", "dodaj Skill X do skills_enabled", status='approved' z modyfikacjami)

**Po approval**: target_agent.current_gate zmienia się na 'awaiting_acceptance', target_agent.status zmienia się na 'building'.

### 15.3 Brama 3 Acceptance Gate

**Trigger**: BE skończył build, agent deployed jako container plus n8n workflows ready.

**BE actions:**
- BE odpala test runs zgodnie z success_metrics z Charter:
  - Sample queries / sample tasks per scope
  - Integration tests z task_queue plus agent_messages
  - Brand canon compliance check (em dash, banned vocab, voice adjectives audit przez Manager AGS lub CM)
  - Cost test (1-2 sample queries z monitoring API spend)
- BE tworzy wpis w agent_approval_gates: gate_type='acceptance', test_results JSONB
- Telegram notification do Tomasza z linkiem do test_results plus przykładowych outputów

**Tomasz response options:**
- Approve (status='approved', agent.status='active' plus current_gate='active', agent zaczyna odbierać realne zadania)
- Reject z prośbą o poprawki (status='rejected', rejection_reason, BE iteracja 2 build adjustments)

**Po approval**: agent operuje w produkcji. Manager AGS plus CM mogą delegować zadania.

### 15.4 Reject path plus iteracje

Jeśli reject na którejkolwiek bramie:
- Wpis agent_approval_gates ma status='rejected' z rejection_reason
- Następny wpis tworzony z iteration+1
- Statusy w agent_registry zostają na poprzednim stadium (np. brama 2 reject → agent.status='planned', current_gate='awaiting_build_approval')
- BE plus Manager AGS adresują uwagi
- Re-submission iteration+1

### 15.5 Special case: agenci LIVE od dawna (X Agent plus Idea-bot)

Faza 0 retroactive approval dla X Agent (LIVE od 31/05) plus Idea-bot (LIVE od 11-12/06):
- BE tworzy retroactive wpisy w agent_approval_gates per agent: 3 gates każdy z status='approved' plus approval_notes='retroactive approval pre Zasada 7 — agent already in production with proven track record'
- agent_registry: status='active', current_gate='active'

Nie wymagamy od X Agent ani Idea-bot przechodzenia przez Bramy 1-2-3 wstecznie — działają i są wartościowe. Zasada 7 obowiązuje od momentu zatwierdzenia (Blueprint v1.3, 18/06/2026) dla wszystkich NOWYCH agentów.

---

**Manager AGS koniec kontraktu BE Faza 0 v2. Czeka na zielone światło Tomasza.**
$n71$, 'active', '383c00c90b93818a8ac2d44b42333f77'
WHERE NOT EXISTS (SELECT 1 FROM be_contracts WHERE notion_page_id = '383c00c90b93818a8ac2d44b42333f77');

SELECT version, length(content) AS len FROM be_contracts;
