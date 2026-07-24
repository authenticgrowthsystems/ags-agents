# Komponent: RESEARCHER (kaskada zrodel, kontrakt /request, sunday brief)

**STATUS GOTOWOSCI: KOMPLETNY z nota (dowod sobotniego cyklu 26/07 przed sprzedaza)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

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

Kaskada (6 zrodel LIVE): **site** (natywne, bez kosztu, tylko gdy zapytanie niesie adres);
low=+web_search; medium=+firecrawl+gemini_dr;
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

- `research_jobs` (master; UWAGA: klucz to `job_id`, NIE `id`; tresc zapytania = `query_text`, NIE `query`): hash,
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
  /metrics), `sources.py` (SourceClient -> webhooki n8n + zrodla natywne),
  **`site.py`** (24/07: pobranie strony podmiotu, `extract_url`,
  `zapytanie_o_podmiot`, `pobierz`, `run`), `router`, `cache`, `budget`,
  `synth`, `failure`. Adaptery: `n8n-workflows/researcher/`.
- Testy lokalne: `ags-researcher/tests/test_site.py` (stdlib, stub httpx, zero sieci).
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

## Incydent 24/07: joby "failed" mimo policzonego wyniku (cache-hit)

- Objaw: 4 joby prospektowe Sprzedawcy status='failed', cost 0.00, czas ~0.4 s,
  error_message "sequence item 0: expected str instance, NoneType found". Z kazdej paczki
  zlecen konczyl sie TYLKO pierwszy (on szedl pelna sciezka ~90 s), reszta trafiala
  w CACHE (prompty prospektowe roznia sie tylko nazwa firmy = podobienstwo ~1).
- Przyczyna (POTWIERDZONA z kodu i bazy 24/07): opcje maja DWA ksztalty. Swieze z modelu
  niosa klucz `label` (pydantic ResearchOption), a wczytane z cache przez `CacheLayer._load`
  klucz `option_label` (nazwa kolumny). `_callback` czytal tylko `label`, wiec dla KAZDEJ
  opcji z cache dostawal None i `", ".join(...)` wywracalo meldunek PO `set_status(completed)`;
  nadrzedny handler petli nadpisywal status na 'failed'. Dowod w bazie: kazdy job 'failed'
  mial 4 wiersze w `options` i czas ~0-3 s (sciezka cache), a kazdy 'completed' 86-121 s.
- Fix (24/07): join odporny na None/puste + petla NIE cofa statusu 'completed' na 'failed'
  (blad meldunku != blad researchu). Wdrozenie: rebuild kontenera **ags-researcher**.
- DRUGA WARSTWA FIXU (wazniejsza): dla RESEARCHU PROSPEKTA cache SEMANTYCZNY jest wylaczony.
  Prompty prospektowe roznia sie tylko nazwa firmy, wiec podobienstwo przekracza prog 0.92
  i "trafienie" oznaczaloby podanie danych o INNEJ firmie jako research prospekta. Detekcja:
  'prospect research' w pierwszych 120 znakach query. Exact cache (ten sam tekst = ta sama
  firma) dziala dalej.
- SKALA KONTAMINACJI (sonda 24/07, dowod w opisach opcji): 6 jobow dostalo wynik CUDZEJ firmy.
  23/07 18:57 - STC (8516342d), La Cultura (d5565b9a) i StandART (26f65169) dostaly opcje
  Scorpion Dance Team ("oboz Biala 2024"); 24/07 08:44-08:54 - La Cultura (63dee554, dbb72a60)
  i STC (e80741b1) dostaly opcje StandART (@klubsportowystandart). Claims sie NIE kopiowaly,
  wiec skazone dane nie weszly do outreachu (konsumenci czytaja claims) - skazone sa wylacznie
  wiersze `options` tych jobow. Do skasowania recznie (SQL w raporcie 24/07).
- TRZECIA WARSTWA FIXU (24/07 po sondzie): cache-hit kopiuje TAKZE `claims` (+ confidence
  zrodlowego joba), a `_callback` czyta `label` LUB `option_label`. Wczesniej job z cache byl
  'completed' z zerem faktow i Sprzedawca pokazywal "job bez claims" - research formalnie
  gotowy, praktycznie bezuzyteczny. Dowod objawu: job 4c391774 (StandART, 24/07 09:01).
- REGRESJA 24/07 (wprowadzona i naprawiona tego samego dnia): do payloadu meldunku wszedl
  `overall_confidence` czytany z `research_jobs.confidence_score` (NUMERIC), czyli `Decimal`.
  `Decimal` nie serializuje sie do JSON, wiec INSERT do `agent_messages` leci wyjatkiem,
  wyjatek byl POLYKANY, a job konczyl sie `completed` bez powiadomienia kogokolwiek.
  Dowod: joby 91d8b597 i b55a9f58 (0 s, 11 claims, ZERO meldunkow). Fix dwuwarstwowy:
  `_json_safe()` sanityzuje CALY payload (Decimal -> float, daty -> ISO, reszta -> str),
  a nieudany zapis meldunku eskaluje zamiast milczec. **Lekcja: cichy `except` na sciezce
  powiadamiania zamienia awarie w niewidzialna cisze.**
- MELDUNEK SUROWY (Telegram z `_callback`): NIE idzie, gdy zleceniodawca to `sales-agent` -
  Sprzedawca wysyla wlasna karte prospekta, wiec Tomasz dostawal dwie wiadomosci, a pierwsza
  nie mowila nawet, ktorej firmy dotyczy (trzy zlecenia = trzy nierozroznialne meldunki).
  Dla pozostalych zleceniodawcow meldunek niesie teraz poczatek zapytania. RESPONSE do
  `agent_messages` leci ZAWSZE (to on budzi konsumenta) - milknie tylko powiadomienie.
- Wniosek ogolny: cache semantyczny ma sens dla pytan TEMATYCZNYCH, nie dla zapytan o KONKRETNY
  PODMIOT. Przy nowych klasach zapytan sprawdz, czy podobienstwo tekstu = podobienstwo tresci.
  Detekcja po frazie 'prospect research' to plaster - kazdy nowy szablon zapytania o podmiot
  (inny agent, inne brzmienie) omija ja i kontaminacja wraca (AP-307).

## ZAMKNIETE 24/07 wieczorem: kaskada CZYTA strone badanego podmiotu (zrodlo `site`)

Dodane natywne zrodlo `site` (`ags-researcher/app/site.py`): pobiera strone podmiotu SAMO,
w Pythonie, bez n8n, bez klucza i bez kosztu. Stoi PIERWSZE w kaskadzie na kazdym poziomie
i uruchamia sie WYLACZNIE wtedy, gdy zapytanie niesie adres (`strona: <url>` albo goly link) -
pytania tematyczne nie tworza nawet wiersza w `research_runs` (`router.sources(level, query)`).

Jak dziala: warianty adresu (www/bez, https/http - gola domena prospekta bywa bez wpisu DNS),
strona glowna + do 3 podstron pasujacych do `kontakt|cennik|zapisy|grafik|instruktor|o-nas|about`,
usuniecie znacznikow HTML, a nastepnie DWA rodzaje dowodow:
1. **wyciag kontaktowy** (mail, telefon, NIP) jako PIERWSZY dowod - krotki, wiec zawsze miesci
   sie w limicie 1200 znakow na dowod, ktory synteza tnie. Bez tego numer z naglowka gubil sie
   w dlugim tekscie strony.
2. **tresc strony w kawalkach** po ~1100 znakow, z adresem w tresci dowodu.
Kazdy dowod ma `authority = 1.0` i `source_name = 'site'`, a prompt syntezy mowi wprost:
dane z wlasnej strony podmiotu sa PEWNE, nie wolno przy nich pisac "brak danych kontaktowych".
Bledy nie wywracaja joba: brak adresu = `skipped`, strona nie odpowiada = `empty` z powodem.

Testy (stdlib, zero sieci): `python ags-researcher/tests/test_site.py` - 26 przypadkow.
Obejscie w sprzedazy (`sales.wizytowka`) ZOSTAJE: ono wypelnia KOLUMNY lejka (DDL 029), a to
inna funkcja niz dowody dla syntezy. Roznica wzgledem `firecrawl`: tamten adapter wola
`api.firecrawl.dev/v2/search/research/papers`, czyli wyszukiwarke prac naukowych - stad arXiv
w wynikach o klubie tanecznym. To NIE jest crawler zadanego adresu i nigdy nim nie byl.

### Historia problemu (dowod z jobu 7411d0ba)

Research prospekta (medium, 3 zrodla, 52 dowody, 1,24 PLN) orzekl "brak danych kontaktowych",
a na stronie glownej klubu stoi telefon. Sonda pokazala, ze to wada POBIERANIA, nie syntezy:

- `web_search`: 5 wynikow z domeny podmiotu, wszystkie to TYTULY po 22-52 znaki, zero tresci.
- `firecrawl` (adapter od pobierania stron): ani jednego trafienia w domene podmiotu; osiem
  wynikow z arXiv i blogow o "prospectingu AI", z artefaktem prefiksu `arxiv.org/abs/`
  (ten sam, ktory tnie `_clean_url` w cm-agent). Adapter zachowuje sie jak wyszukiwarka
  akademicka, nie jak crawler zadanego adresu.
- Najdluzszy dowod calego jobu: praca naukowa (1073 znaki).

Wniosek: dla zapytan o KONKRETNY PODMIOT kaskada musi miec krok "pobierz strone tego
podmiotu" (adres jest w zapytaniu jako `strona:`), a nie tylko wyszukiwanie tematyczne.
WYKONANE 24/07 wieczorem - patrz sekcja wyzej (zrodlo `site`).

## Cache semantyczny: GLOBALNIE OFF (decyzja Managera P3, 24/07)

Bilans plastra na fraze 'prospect research': 0 korzysci, 6 jobow z danymi cudzej firmy.
Decyzja: `SEMANTIC_CACHE_ENABLED=false` w `~/ags-agents/ags-researcher/.env` (restart
kontenera). Cache EXACT (ten sam tekst zapytania = ten sam podmiot) dziala dalej.

Druga warstwa w kodzie, na wypadek ponownego wlaczenia: `site.zapytanie_o_podmiot(query)`
odsiewa z cache semantycznego KAZDE pytanie o konkretny podmiot - po ADRESIE w zapytaniu,
nie po frazie. Fraza byla plastrem, ktory omijal kazdy nowy szablon zapytania (AP-307);
adres niesie kazde pytanie o firme, niezaleznie od tego, ktory agent je uloży.

## Znane pulapki

- `claims.supporting_evidence` w ZYWEJ bazie = **text[]**, nie uuid[] (spec
  klamal); join: `evidence_id::text = ANY(supporting_evidence)`.
- Evidence bywa z artefaktem `https://arxiv.org/abs/web:<url>` - `_clean_url`
  tnie prefiks.
- AWARIA web_search 28/06-20/07 (3 joby failed, PUSTY error_message - worker
  polykal wyjatki): przyczyna = dynamic filtering domyslne w narzedziu
  web_search_20260209 Anthropic; NAPRAWIONE 20/07 - fix
  `allowed_callers:['direct']` + widocznosc bledow, LIVE po rebuildzie
  (galaz claude/badacz-naprawa-d324bd; serwer przestawic na sb-work po merge).
  Otwarte: wymuszenie medium dla query niedzielnego (4e65278) czeka na rebuild
  cm-agent. Szczegoly: docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md.
- Critical dziala dzis SEKWENCYJNIE (DR+Manus blokuja workera ~10 min) -
  parallel dispatch w backlogu.
- Query niedzielne auto-klasyfikowalo sie na low (jedno zrodlo = krucho) -
  wymuszenie minimum medium w kodzie (4e65278), wchodzi z rebuildem cm-agent.

## Podklad niedzielny - persist + plik (fix split-brain 20/07)

Incydent: podklad wyszedl na czat z workera, mozg ROZMOWY CM go nie widzial (out-of-band
nie wchodzi do historii) i twierdzil "research nie wrocil"; tresc nie byla zapisana.
Fix: _do_send (a) persystuje pelny podklad w brand_config `cm_sunday_brief_last`
(wersjonowanie bump), (b) wysyla DODATKOWO plik .md (gotowiec dla przegladarkowego CM),
(c) modes_snapshot pokazuje CM stan podkladu (dostarczony/w toku) w kazdym prompcie.
Poprawka tieru guzikiem (mtier) uczy Managera NA PRZYSZLOSC - nie przerabia wykonanego
joba (propose-and-run); minimum medium dla query niedzielnego wymusza sunday_brief (4d).
