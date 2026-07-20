# Komponent: AGENT SPRZEDAZY (prospect research, outreach HITL, lejek, baza wiedzy)

**STATUS GOTOWOSCI: W BUDOWIE (kod na build/sprzedawca; czeka psql 027 + rebuild cm-agent + patch n8n + tap-testy DoD)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Nowy agent w istniejacym frameworku subagentow: partner strategiczny Tomasza w sprzedazy
(kogo targetowac, jak, kiedy follow-up, kiedy domykac) + wykonawca operacyjny. Zna macierz
gotowosci produktu (co WOLNO sprzedawac), pelny cennik pricing_tiers (Pakiety PL 1-3 =
TOP OFFERING: DFY "system retencji klientow"), sales_playbook, ICP i Voice Bible. Zleca
research prospektow Researcherowi (tier critical = pelna kaskada z Manus), pisze outreach
jako GOTOWIEC (HITL - NIC nie wysyla sie samo), prowadzi lejek sales_pipeline i uczy sie
z materialow Tomasza (sales_knowledge z embeddingami). Frameworki Anthropic sales skills
(draft-outreach, account-research, pipeline-review) zdestylowane w promptcie systemowym.

## Route i wejscia

```
/agents -> pozycja "AGS sprzedaz" (menu n8n buduje sie DYNAMICZNIE z channels
  supervised=true AND status IN ('active','draft'); wiersz AGS/sprzedaz z DDL 027,
  config.agent_kind='sales') -> active_agent='subagent:AGS:sprzedaz'
conversation.handle:
  - sales.try_command PRZED LLM (wzorzec _config_route), z KAZDEGO agenta:
    /prospect <nazwa|URL>  -> research critical + wpis w lejku (deterministycznie)
    /pipeline              -> widok lejka (deterministycznie)
    /oferta                -> pelny cennik; /oferta <prospekt> -> rekomendacja tieru (LLM)
    /add_sales_material [hint] -> uzbrojenie na 2h: nastepny dokument .md/.txt/.pdf
      albo wklejka >=200 znakow -> chunk -> embedding -> sales_knowledge
  - active == 'subagent:AGS:sprzedaz' -> sales.handle_chat (petla agentowa 5 krokow,
    Opus przez cm_tier_sales_chat, paragony narzedzi jak u subagentow)
Dokumenty: n8n document_text (po patchu takze .pdf <=8MB) -> /docmsg ->
  handle_document (PDF: ekstrakcja pypdf) -> [DOKUMENT: nazwa] -> aktywny agent /
  uzbrojony ingest materialu.
```

## Narzedzia (9)

prospect_research (Researcher /request, from='sales-agent', default tier critical -
wpis w agent_registry z 'critical' w allowed_model_tiers; async, wynik tickiem),
prospect_results (claims z linkami), draft_outreach (email/linkedin_dm/x_dm w Voice
Bible; gotowiec = naglowek + CZYSTA WKLEJKA osobna wiadomoscia, wzorzec comment-radar;
zapis engagement_log status 'proposed' + notatka lejka), offer_for (pakiet danych:
lejek+research+cennik -> model rekomenduje OD GORY), pipeline_view, pipeline_add,
pipeline_move (paragon 📊 przy kazdej zmianie), sales_knowledge_search (pgvector,
fallback ILIKE), outreach_sent (propozycja -> 'sent', follow-up +3 dni).

## Wejscia-wyjscia i tabele (DDL 027)

- `sales_pipeline`: id UUID, contact_id FK contacts, prospect_name/url, stage CHECK
  (prospect/qualified/proposal/negotiation/won/lost), offer_tier, value+currency,
  next_followup_at, research_job_id TEXT, notes (append z timestampem, LEFT 4000), source.
- `sales_knowledge`: material_type CHECK (book/technique/case_study/framework/script/
  recording/other), material_name, chunk_no, content_excerpt, embedding vector(1536)
  (OpenAI text-embedding-3-small, jak published_posts; NULL dozwolony), tags[].
- `agent_registry`: wiersz 'sales-agent' z ARRAY['low','medium','critical'].
- `channels`: wiersz (AGS,'sprzedaz','draft',supervised=true, agent_kind='sales',
  welcomed=true) - TYLKO po to, zeby /agents go pokazal. NIE aktywowac w ⚙️ Cele!
- `engagement_log`: outreach drafty (action_type 'other', agent 'AGS:sprzedaz',
  status proposed->sent).
- `brand_config`: sales_pending_material (stan /add_sales_material, TTL 2h),
  cm_tier_sales_chat / cm_tier_sales_outreach / cm_tier_sales_research_summary
  (nadpisania modelu przez /set).

## Punkty zaczepienia w kodzie

- `cm-agent/app/sales.py`: try_command, handle_chat, _dispatch, _prospect_research,
  _draft_outreach, pipeline_text, ingest_material, pdf_text, tick (RESPONSE Researchera
  -> _summarize_research -> Telegram + notatka lejka).
- `cm-agent/app/conversation.py`: hook w handle() (try_command + galaz AGENT_KEY),
  handle_document (galaz PDF), _channels_snapshot (wyklucza agent_kind='sales').
- `cm-agent/app/worker.py`: sales.tick() w petli.
- Wykluczenia agent_kind='sales' takze w: planner._cadence_text, planner (valid_channels),
  reports.run_all, proactive.check_gaps.
- n8n: patch `n8n-workflows/patches/hitl-sales-commands-20072026.cjs` (przepustka
  /prospect /oferta /pipeline /add_sales_material + .pdf w Detect Update Type).

## Kanony ktore go dotycza

- HITL ZAWSZE: zaden outreach/email nie wychodzi sam - gotowiec, Tomasz wysyla recznie.
- NARZEDZIA NIE UJAWNIAMY (GHL): sprzedajemy REZULTAT ("system retencji klientow").
- REGULA PRAWDY: Stage 0-1 - zero zmyslonych case studies/referencji; fakt bez zrodla
  = "(do weryfikacji)". Zero /apply. Waluta: PL=PLN, zagranica=USD.
- Wartosc przed cena; cennik od gory (premium pierwsze). TWARDA ZASADA WYKONANIA
  (paragon narzedzia albo sie nie stalo).

## Znane pulapki

- Wiersz channels 'sprzedaz' pojawia sie w menu ⚙️ Cele (n8n) - NIE wlaczac go jako celu
  publikacji; guardy w kodzie (planner/reports/proactive/snapshot) i tak go ignoruja.
- Research critical dziala SEKWENCYJNIE u Researchera (~10-20 min, kilkanascie PLN/job)
  - /prospect zwraca paragon od razu, wynik przychodzi tickiem; nie czekac w rozmowie.
- PDF ze skanow (obrazy) nie da tekstu - pypdf zwraca pusto, bot melduje jawnie.
- Embeddingi wymagaja openai_api_key w app_secrets - bez niego sales_knowledge dziala
  na fallbacku ILIKE (jawnie oznaczone w paragonie zapisu).
- Level 2 (poza zakresem L1): obsluga hello@ (Gmail API), follow-up automation,
  dashboard metryk konwersji, mirror sales_knowledge do Notion.
