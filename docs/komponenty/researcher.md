# Komponent: RESEARCHER (kaskada zrodel, kontrakt /request, sunday brief)

## Co robi

Osobny agent-serwis (kontener `ags-researcher`, Mikrus, siec n8n_network):
przyjmuje zapytania researchowe, odpala kaskade zrodel wg zlozonosci,
syntetyzuje evidence w claims + 4 opcje decyzyjne, oddaje wynik callbackiem.
Wzorzec architektury event-driven dla calej sieci agentow.

## Kontrakt /request (SZABLON dla kazdego agenta)

```
POST /request {query, model_tier?, from?, correlation_id?} [X-Researcher-Secret]
  -> enqueue + wake.set() -> 202 {job_id}; wynik NIGDY inline:
  callback = agent_messages RESPONSE + Telegram
Bezpiecznik: poll agent_messages REQUEST co 30s (droga dla agentow piszacych
  prosto do DB + przegapione dzwonki)
```

Kaskada (5 zrodel LIVE): low=[web_search]; medium=+firecrawl+gemini_dr;
critical=+openai_dr+manus (~18 PLN/query). Router klasyfikuje query; 'critical'
wymaga slowa kluczowego (piln/krytyczn/urgent/critical/high-stakes). Twarde
stopy budzetu: 50/100/1500 PLN. Adaptery = workflowy n8n "Researcher - *"
(webhook + guard X-Researcher-Secret PRZED platnym callem + klucz z app_secrets).

Guardy: critical tylko dla agentow z 'critical' w agent_registry
.allowed_model_tiers (manager-ags, tomasz-human); inni -> job PARKUJE
(awaiting_approval) + bramka critical_escalation + guziki crit:<gate>:approve|deny.
Model syntezy per job: jawny payload.model_tier albo auto wg complexity
(low->haiku, medium->sonnet, critical->opus); auto-decyzje logowane jako bramki
model_selection (korekta guzikami mtier:<gate>:<tier>).

## Wejscia-wyjscia i tabele

- `research_jobs` (master; UWAGA: klucz to `job_id`, NIE `id`): query, hash,
  embedding, complexity, model_tier, level_override, status, cost_pln,
  confidence. `research_runs` (per zrodlo): status, raw_output, cost_pln.
- `evidence_items` (znormalizowane, source_url), `claims` (fakty +
  supporting_evidence), `options` (4 strategie), `cost_events` (ledger kosztu).
- Cache: exact SHA-256 po (query_hash, model_tier) + semantic pgvector.

## Konsument: CM czyta swiat (sunday_brief)

Sobota 08:00-12:30 (tick workera cm-agent): CM zleca Researcherowi badanie
tygodnia AI dla ICP (cap medium) -> polling research_jobs -> synteza Sonnet
z 3 zrodel (claims + LINKI z evidence, schowek 7 dni, top publikacje) ->
3 KANDYDACKIE TEZY z liczbami i linkami na Telegram (~11:00-13:00). ZERO wpisow
do content_items/post_queue - to podklad pod RECZNY niedzielny artykul.
Fallback z JAWNYM "research nie dojechal" (REGULA PRAWDY). Tap-test: narzedzie
`sunday_world_brief` ("podklad na niedziele"). Stan anty-dublowy:
brand_config `cm_sunday_brief` (phase=sent blokuje retap w tym samym tygodniu
ISO; retap = wyzerowanie klucza, ksztalt sprawdz w `sunday_brief._state_set`).

## Konfiguracja

- `ags-researcher/app/config.py`: SOURCE_POLICY (kaskada), DEPLOYED_ADAPTERS,
  MODEL_RATES, stopy budzetu, SOURCE_TIMEOUT.
- `agent_registry.allowed_model_tiers` per agent (dostep do critical).
- Sekrety: app_secrets (researcher_webhook_secret, klucze zrodel).

## Punkty zaczepienia w kodzie

- `ags-researcher/app/`: `worker.py` (petla + FastAPI /request /health
  /metrics), `sources.py` (SourceClient -> webhooki n8n), `router`, `cache`,
  `budget`, `synth`, `failure`. Adaptery: `n8n-workflows/researcher/`.
- `cm-agent/app/research.py`: `request_research`, `job_status`,
  `claims_with_sources`, `grounding_with_sources`, `_clean_url`,
  `ingest_research_responses`.
- `cm-agent/app/sunday_brief.py`: `tick`, `trigger_manual`, `_synthesize`,
  `_request`.

## Kanony ktore go dotycza

- Async event-driven: webhook wake, nie cron/poll (cron tylko rutyny).
- Critical-restriction + manager-decisions-approval-learning (bramki).
- REGULA PRAWDY w konsumentach (fallback jawny, fakt bez zrodla =
  "(do weryfikacji)").

## Znane pulapki

- `claims.supporting_evidence` w ZYWEJ bazie = **text[]**, nie uuid[] (spec
  klamal); join: `evidence_id::text = ANY(supporting_evidence)`.
- Evidence bywa z artefaktem `https://arxiv.org/abs/web:<url>` - `_clean_url`
  tnie prefiks.
- AWARIA web_search 28/06-20/07 (3 joby failed, PUSTY error_message - worker
  polykal wyjatki): przyczyna = dynamic filtering domyslne w narzedziu
  web_search_20260209 Anthropic; fix `allowed_callers:['direct']` + widocznosc
  bledow (commit 3f97d90, galaz build/researcher-fix; DoD a PASS). Stan 20/07:
  czeka rebuild ags-researcher + niedzielny tap. Szczegoly:
  docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md.
- Critical dziala dzis SEKWENCYJNIE (DR+Manus blokuja workera ~10 min) -
  parallel dispatch w backlogu.
- Query niedzielne auto-klasyfikuje sie na low (jedno zrodlo = krucho) -
  otwarta decyzja 4d briefu naprawczego: wymusic minimum medium.
