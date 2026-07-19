# RAPORT do Managera AGS - BE-SWIAT (CM czyta swiat) - 19/07/2026

Budowniczy: BE-SWIAT (tryb rownolegly, worktree build-swiat, galaz build/czyta-swiat od
origin/claude/silly-blackwell-dfc32d). Model: start Fable 5, dokonczenie Opus 4.8. Zakaz deployu/psql/n8n
dotrzymany - kod + weryfikacja read-only + commit; skladanie nalezy do INTEGRATORA.

## Co zbudowane (DoD briefu)

KANON 19/07: niedzielny artykul LinkedIn = insight tygodnia ze swiata AI, pisany RECZNIE przez Tomasza;
planer ma zakaz niedzieli DOPOKI CM nie umie czytac swiata. Ten build daje CM te zdolnosc jako PODKLAD
(draft do recznej obrobki), NIE auto-publikacje.

Mechanizm (Pareto, na istniejacych organach, wzorzec weekly_metrics_reminder):
1. Sobota rano (okno 08:00-12:30, tick workera) -> CM zleca Researcherowi (kontrakt POST /request,
   ktory juz istnieje) badanie "najwazniejsze wydarzenia/dyskusje AI ostatnich 7 dni dla ICP
   solo-founderow". Tier: auto po stronie Researchera, CM capped <=medium (guard krytyczny).
2. Polling research_jobs.status (nie blokuje workera - stan w brand_config).
3. Synteza (Sonnet, task 'sunday_synth') z 3 zrodel: research (claims + LINKI zrodel z evidence_items)
   + schowek tygodnia (inspirations 7 dni: inspiracje + cudze posty z Idea Bota) + top publikacje
   tygodnia. Wynik: 3 KANDYDACKIE TEZY z twardymi liczbami i linkami zrodel + przypomnienie o
   materialach wlasnych. Landing ~11:00-13:00.
4. sendMessage do Tomasza. ZERO wpisu do content_items/post_queue.

### Pliki (KONTRAKT briefu - nic poza nim nie ruszone)
- `cm-agent/app/sunday_brief.py` (NOWY organ): maszyna stanu + synteza + wysylka.
- `cm-agent/app/research.py`: `job_status()`, `claims_with_sources()`, `grounding_with_sources()`,
  `_clean_url()`.
- `cm-agent/app/worker.py`: `sunday_brief.tick()` w petli (obok proactive.tick()) + import.
- `cm-agent/app/conversation.py`: narzedzie `sunday_world_brief` (tap-test) + rejestracja + dispatch.
Zero DDL, zero n8n. Stan anty-dublowy: brand_config klucz `cm_sunday_brief`.

## Weryfikacja read-only (temp webhook, utworzony i SKASOWANY)

DOCS-FIRST + dowod z zywej bazy (nie hipoteza). Wynik probe:
- 5 tabel Researchera (`research_jobs`, `research_runs`, `evidence_items`, `claims`, `options`) ZYJE
  w tej samej bazie ags_crd - dostepne z DSN CM (potwierdza to zastane research_context).
- `evidence_items`: 699/699 wierszy z `source_url` (100%) - linkowanie zrodel dziala.
- Statusy `research_jobs`: completed=11, partial_failure=3, failed=4, archived=1 (terminal-OK=completed).
- `inspirations`: 22 wpisy w 7 dni; zrodla telegram/notion/cm_conversation.

### ROZBIEZNOSC SPEC vs ZYWA BAZA (wazne dla przyszlych buildow na Researcherze)
Spec Briefing Pack 23/06 deklaruje `claims.supporting_evidence UUID[]`. ZYWA baza: typ to **text[]**
(`_text`), a wartosci to poprawne UUID-y w tekscie. Naiwny join `evidence_id = ANY(supporting_evidence)`
wywala sie (uuid = text). Poprawka: `evidence_id::text = ANY(supporting_evidence)` - zweryfikowane,
zwraca zrodla. Dodatkowo evidence bywa zapisane z artefaktem `https://arxiv.org/abs/web:<prawdziwy_url>`
- `_clean_url` tnie ten prefiks (prawdziwe arxiv.org/abs/<id> zostaja nietkniete).

## Decyzje projektowe

- **correlation_id = deterministyczny uuid5(tydzien)**: poprawny UUID, wiec zastane
  `ingest_research_responses` znajdzie brak itemu w content_items i tylko oznaczy wiadomosc 'read'
  (bez bledu/zatrucia transakcji). Podklad NIE wplywa na obieg materialow.
- **auto_done rozdziela tap-test od automatu**: reczny podklad w srodku tygodnia NIE zajmuje slotu
  sobotniego (ta sama tydzien ISO). Automat wysyla sie raz/tydzien; reczny na zadanie ile trzeba.
- **REGULA PRAWDY / fallback**: research niegotowy o 13:00 (albo dead, albo manual >20 min) ->
  podklad ze schowka+publikacji z JAWNYM oznaczeniem "research nie dojechal, fakty do weryfikacji".
  Prompt syntezy wymusza pokrycie faktu zrodlem, inaczej "(do weryfikacji)". Zero em-dash (kanon).

## Stan / testy
py_compile 4 plikow OK. Lokalnie przetestowane: `_clean_url` (tnie artefakt, zostawia legalne URL-e),
uuid5 (poprawny, deterministyczny). Sciezka runtime (research->synteza->wysylka) do tap-testu po
rebuildzie u INTEGRATORA (wymaga dzialajacego Researchera + Anthropic).

## Dla INTEGRATORA (skladanie)
- Rebuild cm-agent (bez DDL, bez n8n).
- TAP-TEST DoD: napisz do CM "podklad na niedziele" -> zapowiedz od CM, po kilku min 3 tezy z
  faktami i LINKAMI; potwierdz ze content_items i post_queue nie dostaly nowych wierszy.
- Konflikt: worker.py (import + linia tick) i conversation.py (lista narzedzi + dispatch) sa tez
  dotykane przez inne buildy - merge wg mapy w BRIEF_INTEGRACJA. sunday_brief.py jest wylacznie moj.

## Pytanie do Managera
Query researchu jest ustawiony pod ICP solo-founderow generycznie. Czy chcesz, zeby podklad byl
wezszy tematycznie (np. tylko premiery modeli + zmiany cen), czy szeroki jak teraz? Zostawiam szeroki
do pierwszej soboty; korekta to jedna zmienna SUNDAY_QUERY.
