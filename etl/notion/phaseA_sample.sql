-- TASK #71 FAZA A - SAMPLE (04/07/2026): 3 zrodla x probka, dowod pipeline'u przed pelnym ETL.
-- Idempotentne. Zrodla pobrane read-only przez Notion MCP; Blueprint = PELNA tresc z pliku workspace
-- (strona Notion to streszczenie wskazujace plik - hybryda udokumentowana w raporcie Fazy A).

-- 1) agent_blueprints <- Blueprint v1.3 (Kategoria 1)
INSERT INTO agent_blueprints (version, title, content, status, notion_page_id)
SELECT '1.3', 'AGS Blueprint Architektury Agentow AI v1.3 (18/06/2026) - Approval Gate Process + Researcher Faza 0.5',
       $n71$# AGS Blueprint Architektury Agentów AI — wersja 1.3

**Data:** 18/06/2026
**Autor:** Manager AGS (interim, Cowork)
**Status:** ZATWIERDZONY do kontraktu BE v2
**Zmiana vs v1.2:** Nowa Zasada 7 canonical (Approval Gate Process plus deep research per agent). Researcher przesunięty z Fazy 2 do Fazy 0.5. Firecrawl API dorzucony do narzędzi Researchera obok Gemini/Manus/ChatGPT/Web Search.

---

## 1. STRESZCZENIE ZMIAN OD v1.2

**Zasada 7 canonical NEW** — Approval Gate Process. Każdy agent ma trzy bramy przed pójściem LIVE:

1. **Brama 1 Research Gate** — deep research przez Researcher (lub manualnie przez Tomasza plus Manager AGS interim) o najlepszych praktykach, modelach, narzędziach, podejściach. Output minimum 4 opcje z trade-off i sources. Tomasz dostaje syntezę i wybiera kierunek.

2. **Brama 2 Build Approval Gate** — BE proponuje konkretny plan implementacji (model_tier, tools_allowed, decision_authority, escalation_rules, success_metrics, Charter draft). Tomasz zatwierdza plan zanim BE rusza budowę.

3. **Brama 3 Acceptance Gate** — BE pokazuje agent w działaniu (test runs, sample outputs, integration tests). Tomasz zatwierdza i przełącza status w agent_registry z 'building' na 'active'. Bez Tomasz approval agent zostaje w 'building' i nie odbiera realnych zadań.

**Researcher przesunięty do Fazy 0.5** — między Faza 0 (schemat PostgreSQL) a Faza 1 (CM plus social Sub-Agenty plus GHL Specialist). Powód: jeśli każdy agent wymaga deep research przed build, Researcher musi powstać pierwszy żeby automatyzować ten proces. Researcher pierwszego dnia jest sam-przedmiotem deep research (manualnie przez Tomasza plus Manager AGS), potem dla wszystkich kolejnych agentów Researcher robi research automatycznie.

**Firecrawl API NEW** w narzędziach Researchera. Tomasz ma klucz API. Firecrawl daje structured web extraction (GHL official docs, Meta Marketing API docs, Google Ads API docs, Anthropic Skills docs, research papers, blogposts) z lepszą precyzją niż LLM scraping. Researcher używa Firecrawl plus Gemini Deep Research plus Manus Execution Analysis plus ChatGPT synteza plus Web Search built-in jako pięć równoległych źródeł research z różnymi mocnymi stronami.

**Nowa tabela PostgreSQL agent_approval_gates** — log historii approvals per agent. Każdy gate ma swój wpis z timestamp, gate_type (research/build/acceptance), status (pending/approved/rejected), approver (zawsze Tomasz), notes, plus link do research output lub build plan.

**Łącznie 22 plus CHRONOS agentów na serwerze bez zmian od v1.2**. Tylko kolejność budowy się zmieniła (Researcher pierwszy po schemacie).

---

## 2. PEŁNA HIERARCHIA AGENTÓW v1.3 (bez zmian od v1.2)

Hierarchia z v1.2 zostaje identyczna. Zmienia się tylko kolejność build (Researcher pierwszy).

```
Tomasz (Human)
├── CHRONOS (niezależny Cross-Business Coordinator)
└── Manager AGS (Root Orchestrator, Opus 4.8)
    ├── Sekretarka AGS (cross-cutting, Haiku 4.5 plus autonomia)
    ├── Researcher (cross-cutting Specialist, Sonnet 4.6) ← FAZA 0.5
    ├── GHL Specialist (cross-cutting Specialist, Sonnet)
    ├── Content Manager (Business Manager)
    │   ├── X Agent, LinkedIn SM, IG Agent, FB Agent, Idea-bot
    │   └── Twórca Treści Wizualnych (post-M5)
    ├── Marketer (Business Manager)
    ├── Specjalista od Reklamy (Business Manager)
    │   ├── Meta Ads Agent
    │   ├── Google Ads Agent
    │   └── Print/Offline Agent (pluggable)
    ├── Pipeline Agent (Business Manager)
    ├── Sprzedawca (Business Manager)
    │   ├── Proposal Generator
    │   └── Follow-up Sequencer
    └── Opiekun Relacji (Business Manager)
```

---

## 3. ZASADY OBIEKTOWE FUNDAMENTALNE (7 zasad canonical v1.3)

1. **Obiektowość wymienialna** — tools wymienialne, architektura stała
2. **Modularność plug-and-play** — Sub-Agent dołączalny/odłączalny niezależnie
3. **Sprzedawalność jako produkt** — system dla dowolnego biznesu, Manager kręgosłupem
4. **Autonomia decyzyjna Sub-Agentów** — hot topics autonomicznie z log AUTONOMOUS_DECISION
5. **Sekretarka jako pełnoprawny agent** — Haiku ale traktowana jak człowiek
6. **Cross-business communication FUTURE** — Sekretarki cross-brand plus Managerowie wymiana, post-M5
7. **Approval Gate Process NEW** — każdy agent przechodzi przez trzy bramy (Research → Build Approval → Acceptance) zanim status='active'. Pierwsza brama wymaga deep research z minimum 4 opcji. Tomasz zawsze zatwierdza każdy gate. Bez kompletu trzech approvals agent nie operuje.

---

## 4. RESEARCHER — SZCZEGÓŁY (centralny dla Zasady 7)

### 4.1 Pozycja w hierarchii
Cross-cutting Specialist pod Managerem AGS. Peer-level z Sekretarką i GHL Specialist. Klienci wewnętrzni: wszyscy agenci ekosystemu plus Manager AGS plus Tomasz bezpośrednio (gdy potrzebuje deep research dla strategicznej decyzji).

### 4.2 Tech stack Researcher
- Model: Sonnet 4.6 (synteza analityczna)
- n8n workflows do pięciu source pluginów:
  - **Firecrawl API** (Tomasz ma klucz) — structured web extraction (docs, research papers, blogposts)
  - **Gemini API** — Deep Research z grounding na search results
  - **Manus API** — Execution Analysis (jeśli Manus pozwala API access, alternatywa: n8n controller)
  - **ChatGPT API** (GPT-4o lub successor) — synteza syntetyczna, alternatywne perspective
  - **Web Search** built-in Claude (Anthropic-side)

### 4.3 Workflow standard query Researcher
1. Klient agent wysyła REQUEST do Researcher przez agent_messages z payload zawierającym pytanie research plus context
2. Researcher generuje master prompt per source (Firecrawl URL list, Gemini Deep Research query, Manus task brief, ChatGPT prompt, Web Search query string)
3. n8n odpala 5 równoległych workflows do każdego source
4. Każdy source zwraca wynik plus sources (cytowane URL-e, papers, docs)
5. Researcher synthesizes wszystkie odpowiedzi przez Sonnet 4.6:
   - Konwergencja (co wszystkie źródła potwierdzają)
   - Dywergencja (gdzie source różnią się)
   - Trade-off plus opcje (minimum 4 alternatywne podejścia z plus/minus każdej)
   - Rekomendacja (jeśli pytanie tego wymaga)
6. RESPONSE do klienta agent przez agent_messages plus log w agent_logs

### 4.4 Master prompts cache
Researcher trzyma w marketing_knowledge_base (po post-M5 RAG aktywacja) bibliotekę master promptów per typ query (architecture research, vendor analysis, competitive intel, framework discovery, technical deep-dive). Cache reduces przygotowanie czasu.

### 4.5 Researcher sam jest pierwszym testem Zasady 7
Brama 1 dla Researcher = manual deep research przez Tomasza plus Manager AGS interim. Master prompt to Gemini plus Manus plus ChatGPT plus Firecrawl (Tomasz odpala te queries, kopiuje wyniki). Manager AGS interim syntezuje. Tomasz approves architekturę Researcher. BE buduje. Brama 3 acceptance: Researcher dostaje testowy query "jakie są najlepsze praktyki dla orkiestracji multi-agent systemu na PostgreSQL", produkuje minimum 4 opcje z sources, Tomasz weryfikuje jakość, status='active'.

---

## 5. SEKWENCJA BUDOWY v1.3 (Researcher Faza 0.5)

### Faza 0 — Kontrakt plus schemat (TERAZ)
Manager AGS dostarcza kontrakt BE v2 z DDL 18 tabel (17 z v1.2 plus nowa agent_approval_gates) plus Charters 9 nowych agentów plus seed values plus Approval Gate Process per agent specification.

### Faza 0.5 — Researcher build (NEW v1.3)
- Day 1: Brama 1 Research Gate dla Researcher (manualnie Tomasz plus Manager AGS używając Gemini Deep Research, Manus, ChatGPT, Firecrawl)
- Day 2: Tomasz Brama 2 approval architektury Researcher
- Day 3-4: BE buduje Researcher container (Sonnet 4.6, n8n workflows do 5 sources, master prompt builder, synteza framework)
- Day 5: Brama 3 acceptance test — Researcher dostaje próbne query, Tomasz weryfikuje jakość, status='active'

### Faza 1 — CM plus migracja Sub-Agentów social plus GHL Specialist
Każdy agent przechodzi przez 3 gates. Researcher już LIVE więc gate 1 automatyczny. Plus parallel CHRONOS Faza 1.1.

### Faza 1.5 — CHRONOS minimal viable równolegle z Fazą 1
### Faza 2 — Manager AGS server plus Sekretarka
(Researcher już LIVE od Fazy 0.5)
### Faza 3 — Pipeline plus Sprzedawca plus Opiekun Relacji plus Marketer plus Specjalista od Reklamy
### Faza 4 — M5 First Client plus CHRONOS rozszerzenie
### Faza 5 — Twórca Treści Wizualnych plus TNM cross-business orkiestra

---

## 6. APPROVAL GATE PROCESS — operational details

### 6.1 Brama 1 Research Gate
- Klient agent (Manager AGS lub Tomasz) inicjuje brief research o agencie X
- Researcher otrzymuje REQUEST przez agent_messages albo (interim do Fazy 0.5) Manager AGS przygotowuje master prompty manualnie
- Output zapisany w `agent_approval_gates` z gate_type='research', status='pending', research_output JSON (4+ opcje z trade-off i sources)
- Tomasz dostaje HITL notification przez Telegram plus link do output
- Tomasz approves konkretną opcję (lub rejects z prośbą o pogłębienie, lub edits z dorzuceniem wytycznych)
- Status='approved' z timestamp i notes

### 6.2 Brama 2 Build Approval Gate
- BE drafts plan implementacji bazując na approved research opcji (Charter draft, model_tier, tools_allowed, success_metrics, escalation_rules)
- BE wstawia wpis `agent_approval_gates` gate_type='build', status='pending', build_plan JSON
- Tomasz dostaje HITL notification przez Telegram plus link do planu
- Tomasz approves plan (lub rejects z prośbą o korekty)
- BE rusza budowę

### 6.3 Brama 3 Acceptance Gate
- BE skończył build, agent jest deployed ale status='building'
- BE przeprowadza test runs (sample queries, integration tests, brand canon compliance check)
- BE wstawia wpis `agent_approval_gates` gate_type='acceptance', status='pending', test_results JSON
- Tomasz dostaje HITL notification plus link do test results
- Tomasz approves (lub rejects z prośbą o poprawki)
- Status w agent_registry zmieniony z 'building' na 'active'. Agent zaczyna odbierać realne zadania.

### 6.4 Reject path
Jeśli Tomasz reject na którejkolwiek bramie:
- Wpis `agent_approval_gates` ma status='rejected' z notes (powód)
- BE plus Manager AGS adresują uwagi
- Nowy wpis approval gate z status='pending' (kolejna iteracja)
- Agent zostaje w status='planned' (brama 1 reject) lub 'building' (brama 2 lub 3 reject)

---

## 7. MODEL DANYCH DELTA v1.3

### Nowa tabela agent_approval_gates

```sql
CREATE TABLE agent_approval_gates (
    gate_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id             UUID NOT NULL REFERENCES agent_registry(agent_id),
    gate_type            VARCHAR(20) NOT NULL CHECK (gate_type IN (
                             'research', 'build', 'acceptance'
                         )),
    iteration            INTEGER NOT NULL DEFAULT 1,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
                             'pending', 'approved', 'rejected', 'expired'
                         )),
    submitted_by         VARCHAR(100),
    submitted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    research_output      JSONB,
    build_plan           JSONB,
    test_results         JSONB,
    approver             VARCHAR(100) NOT NULL DEFAULT 'tomasz',
    approved_at          TIMESTAMPTZ,
    approval_notes       TEXT,
    rejection_reason     TEXT,
    next_iteration_due   TIMESTAMPTZ
);

CREATE INDEX idx_agent_approval_gates_agent   ON agent_approval_gates(agent_id);
CREATE INDEX idx_agent_approval_gates_status  ON agent_approval_gates(status);
CREATE INDEX idx_agent_approval_gates_type    ON agent_approval_gates(gate_type, status);
```

Plus drobna zmiana w agent_registry: dodać kolumnę `current_gate VARCHAR(30)` z value 'awaiting_research' / 'awaiting_build_approval' / 'awaiting_acceptance' / 'active' dla quick filter.

---

## 8. FIRECRAWL INTEGRATION (NEW v1.3)

Firecrawl API jako jeden z pięciu source pluginów Researchera. Setup:

- Klucz API: Tomasz ma (przekazuje BE do n8n credentials store podczas Fazy 0.5 build)
- n8n workflow: "Researcher - Firecrawl Scrape" z trigger od agent_messages REQUEST type='research_web_extract'
- Workflow nodes: webhook trigger → Firecrawl Scrape (URL list lub crawl seed) → response parsing → JSON output do RESPONSE
- Use cases:
  - GHL Specialist potrzebuje pull docs z gohighlevel.com/docs → Firecrawl scrape strukturyzuje
  - Specjalista od Reklamy potrzebuje pull Meta Marketing API docs → Firecrawl scrape
  - Marketer potrzebuje pull research paper PDF link → Firecrawl scrape converts do markdown
  - Researcher sam crawl-uje vendor websites dla competitive intel

Firecrawl koszt: per usage (Tomasz monitoruje). Per Firecrawl pricing typical: free tier hobby dla research workflow startowego, paid gdy wolumen rośnie.

---

## 9. ROZSZERZENIA FUTURE (bez zmian od v1.2)

Plus dorzucamy w v1.3:
- **Researcher subscription model** — po post-M5 stabilizacji Researcher może być sprzedawany jako "wynajmij researchera z bazą 5 sources" (Firecrawl plus Gemini DR plus Manus plus ChatGPT plus Web Search) dla klientów AGS którzy chcą deep research automatyzowany. Plus consultant subskrypcja jak GHL Specialist i Marketer.

---

## 10. CO ROBIMY DALEJ

1. Tomasz zatwierdza v1.3 i nową Zasadę 7 (lub daje uwagi)
2. Manager AGS update kontrakt BE z v1 do v2 z nową sekcją Approval Gate Process plus nową tabelą agent_approval_gates plus Researcher Faza 0.5 plus Firecrawl integration
3. Day 1 Faza 0.5: deep research o Researcher (manualnie Tomasz plus Manager AGS używając Gemini DR plus Manus plus ChatGPT plus Firecrawl)
4. Manager AGS prepares 4 master prompty do każdego source (Gemini DR, Manus, ChatGPT prompt, Firecrawl URL list architektur multi-agent)
5. Tomasz odpala każdy source równolegle
6. Wyniki wracają, Manager AGS syntezuje, 4+ opcje architektury Researcher dla Tomasz decyzji

Manager AGS koniec wersji 1.3 blueprintu.
$n71$, 'active', '383c00c90b9381c285c3eaa1e2e50940'
WHERE NOT EXISTS (SELECT 1 FROM agent_blueprints WHERE notion_page_id = '383c00c90b9381c285c3eaa1e2e50940');

-- 2.1) inspirations <- Story Bank #1 (Kategoria 1; kotwica = page_id#s01)
INSERT INTO inspirations (source, content, brand, status, notion_page_id, metadata)
SELECT 'notion', '[Story Bank #1: 37 Faxes and One Sentence] Moved to Opole for a job that never materialized. 140zl/month after rent. Sent 37 faxes to kindergartens (przedszkola) in Opole offering dance classes for children. One kindergarten replied. That reply launched a 20-year career. His mentor told him ''I will never respect you'' - broke his need for permission. | Key quote: Nobody is coming to save you. So move.', 'AGS', 'new',
       '331c00c90b9381eeb995cc757bfc89a4#s01', '{"meta_type": "story_bank", "story_number": 1, "title": "37 Faxes and One Sentence", "pillar": "Authenticity", "sensitivity": "MEDIUM", "key_quote": "Nobody is coming to save you. So move."}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM inspirations WHERE notion_page_id = '331c00c90b9381eeb995cc757bfc89a4#s01');

-- 2.2) inspirations <- Story Bank #2 (Kategoria 1; kotwica = page_id#s02)
INSERT INTO inspirations (source, content, brand, status, notion_page_id, metadata)
SELECT 'notion', '[Story Bank #2: The Mentor Who Never Showed Up] The most important mentor was the one who never existed. From grandfather building furniture from scraps to Dr. Dziura who said: ''Take what you have, package it beautifully, and sell that.'' Those words became his operating system. | Key quote: Stop chasing what you wish you had. Take what you have, package it beautifully, and sell that.', 'AGS', 'new',
       '331c00c90b9381eeb995cc757bfc89a4#s02', '{"meta_type": "story_bank", "story_number": 2, "title": "The Mentor Who Never Showed Up", "pillar": "Simplicity", "sensitivity": "LOW", "key_quote": "Stop chasing what you wish you had. Take what you have, package it beautifully, and sell that."}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM inspirations WHERE notion_page_id = '331c00c90b9381eeb995cc757bfc89a4#s02');

-- 2.10) inspirations <- Story Bank #10 (Kategoria 1; kotwica = page_id#s10)
INSERT INTO inspirations (source, content, brand, status, notion_page_id, metadata)
SELECT 'notion', '[Story Bank #10: The Full Circle Pivot] Studied Electronics and Telecommunications. Master''s thesis: intelligent building management system (client-server). Declined a PhD. Worked in a building materials warehouse while teaching dance after hours. When dance outearned the salary, opened a studio. Dance was Plan B that became 20 years. Now returning to systems with AI at 45. He was a programmer and systems architect FIRST. Engineer''s mind, artist''s soul. CANONICAL BIO: never ''dance teacher who learned AI''; correct: ''systems architect who spent 20 years on a dance floor''. | Key quote: The shaking doesn''t mean you''re not ready. It means you''re about to grow.', 'AGS', 'new',
       '331c00c90b9381eeb995cc757bfc89a4#s10', '{"meta_type": "story_bank", "story_number": 10, "title": "The Full Circle Pivot", "pillar": "Visibility", "sensitivity": "MEDIUM", "key_quote": "The shaking doesn''t mean you''re not ready. It means you''re about to grow."}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM inspirations WHERE notion_page_id = '331c00c90b9381eeb995cc757bfc89a4#s10');

-- 3) pricing_tiers <- Cennik Lokalna Automatyzacja (Kategoria 6)
INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id)
VALUES ('AGS', 'lokalna_automatyzacja', 'Pakiet 1: Strona WWW', '2000-3000 PLN jednorazowo', 'PLN', '{"scope": ["strona www do 5 podstron", "responsywny design", "formularz kontaktowy", "Google Maps", "podstawowe SEO", "30 dni gwarancji"], "delivery_days": "5-7"}'::jsonb,
        '31bc00c90b93812bbfc6ee549b6580cc')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

-- 3) pricing_tiers <- Cennik Lokalna Automatyzacja (Kategoria 6)
INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id)
VALUES ('AGS', 'lokalna_automatyzacja', 'Pakiet 2: Strona + Podstawowa Automatyzacja', '3000-5000 PLN jednorazowo + $97/mies GHL', 'PLN', '{"scope": ["wszystko z Pakietu 1", "rezerwacje online", "SMS/email przypomnienia", "auto-odpowiedz", "pipeline sprzedazowy", "dashboard"], "delivery_days": "7-10"}'::jsonb,
        '31bc00c90b93812bbfc6ee549b6580cc')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

-- 3) pricing_tiers <- Cennik Lokalna Automatyzacja (Kategoria 6)
INSERT INTO pricing_tiers (brand_id, ladder, tier_name, price, currency, features, notion_page_id)
VALUES ('AGS', 'lokalna_automatyzacja', 'Pakiet 3: Kompletny System', '5000-8000 PLN jednorazowo + $97-297/mies GHL', 'PLN', '{"scope": ["wszystko z Pakietu 2", "pelny CRM", "follow-up sekwencje", "chatbot AI 24/7", "system opinii Google", "kampanie SMS/email", "raportowanie", "2h szkolenia", "30 dni gwarancji + 1 mies wsparcia"], "delivery_days": "10-14"}'::jsonb,
        '31bc00c90b93812bbfc6ee549b6580cc')
ON CONFLICT (brand_id, ladder, tier_name) DO NOTHING;

-- WERYFIKACJA (wyniki wklej do raportu dla Managera):
SELECT 'agent_blueprints' AS t, COUNT(*) AS n, MAX(length(content)) AS max_len FROM agent_blueprints
UNION ALL SELECT 'inspirations_notion', COUNT(*), MAX(length(content)) FROM inspirations WHERE source='notion'
UNION ALL SELECT 'pricing_tiers', COUNT(*), NULL FROM pricing_tiers;
