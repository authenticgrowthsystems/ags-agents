# BRIEF BUILDU: NAPRAWA RESEARCHERA - adapter web_search (20/07/2026) - budowniczy: BE-RESEARCHER-FIX

Wywolanie sesji (rownolegle okno, "dziala z boku" - decyzja Tomasza 20/07):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md zbuduj`

## 0. Zasady sesji (rownolegly tryb - INNE prawa niz buildy 19/07)

- Wlasny worktree+galaz od origin/claude/silly-blackwell-dfc32d (NIE pracuj na sb-work):
  `git -C "C:\Claude-CoWork\AGS\ags-agents" fetch origin && git -C "C:\Claude-CoWork\AGS\ags-agents" worktree add ".claude/worktrees/build-researcher-fix" -b build/researcher-fix origin/claude/silly-blackwell-dfc32d`
- WYJATEK od zakazu n8n: ta sesja MA prawo do workflowow n8n RESEARCHERA (rodzina
  "Researcher - *"). HITL `U5pUZjy2yAhR1sWg` NIE WOLNO dotykac. Po KAZDYM PUT
  deactivate+activate (AP: project_n8n_reactivate_after_put). PUT tylko
  {name,nodes,connections,settings przefiltrowane}. Backup JSON przed patchem
  (wzorzec: C:\Users\Admin\AppData\Local\Temp\ags-media-spike\hitl-*.cjs).
- WYJATEK od zakazu deployu: wolno rebuildowac kontener `ags-researcher` (przez Tomasza SSH;
  i tak jest zepsuty, gorzej nie bedzie). Kontenera `cm-agent` NIE dotykac.
- DB zapisy = Tomasz SSH (podajesz SQL); odczyt read-only przez docker exec psql u Tomasza
  albo temp webhook (wzorzec Temp/ags-media-spike/verify-*.cjs; skasuj po uzyciu).
- Sekrety: TYLKO app_secrets (tabela w ags_crd). Env n8n lokalnie:
  `set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:/Claude-CoWork/AGS/ags-agents/.env" | sed 's/\r$//') && set +a && node skrypt.cjs`
- DOCS-FIRST: przed zmiana requestu do api.anthropic.com przeczytaj AKTUALNA dokumentacje
  narzedzia web search w Messages API (WebFetch docs.anthropic.com). Nie zgaduj formatu.
- Decyzje Tomasza guzikami (AskUserQuestion), pelne sciezki i komendy, zero em-dash,
  py_compile przed commitem, raport docs/cm/RAPORT_do_Managera_<data>_researcher_fix.md.

## 1. OBJAW (dowody zebrane 20/07 rano przez BE-INTEGRATORA, wszystko z zywej bazy)

- Tap-test "podklad na niedziele" (CM czyta swiat) -> Researcher przyjal job, po ~2 min FAILED:
  - research_jobs job_id=45af415e-32d7-418f-9c59-d76a19828334: complexity=low, model_tier=haiku,
    status=failed, error_message="no sources returned evidence", cost_pln NULL,
    created 2026-07-20 07:25:11 UTC, completed 07:27:20.
  - research_runs run_id=7799917d-a91c-4c38-b1c8-e836bfb70084 (jedyny run): source_name=web_search,
    status=error, error_message PUSTY, raw_output PUSTY, czas 07:25:15 -> 07:27:20 (~2 min = timeout?).
- HISTORIA: research_jobs 3 ostatnie joby WSZYSTKIE failed: 20/07, 03/07 18:15, 28/06 16:39.
  Wczesniej (do ~27/06) bylo completed=11. Czyli web_search zepsul sie ok. 27-28/06 i nikt
  nie zauwazyl, bo nikt nie wolal Researchera przez 3 tygodnie.
- Kontener `ags-researcher` Up 2 weeks (healthy). Logi: "[researcher] job ... claimed" ->
  "[researcher] job ... -> failed", MIEDZY nimi ZERO linii bledu (worker polyka wyjatek
  albo adapter zwraca pusto bez logowania). To osobny defekt do naprawy (pkt 4c).

## 2. ARCHITEKTURA (fakty z kodu, stan sb-work HEAD >= ba06906)

- Kod Researchera: `ags-researcher/app/` w tym repo (FastAPI, kontener ags-researcher,
  port wewn.; endpointy /request /health). Worker: app/worker.py; adaptery wolane przez
  app/sources.py (SourceClient) -> webhooki n8n.
- Kaskada kosztowa (app/config.py ~115): low=[web_search]; medium=[web_search, firecrawl,
  gemini_dr]; high=[+openai_dr]; critical=[+manus]. DEPLOYED_ADAPTERS = wszystkie 5.
  Sciezka web_search: N8N_BASE_URL + `/webhook/researcher-web-search`.
- Workflow n8n "Researcher - Web Search" (kopia repo: n8n-workflows/researcher/web-search.json;
  ZYWA definicja w n8n moze sie ROZNIC - najpierw GET z API n8n i porownaj!):
  Webhook -> Get Anthropic Key (Postgres, app_secrets) -> Web Search (httpRequest POST
  https://api.anthropic.com/v1/messages) -> Normalize (code) -> Guard (code).
  Czyli "web_search" = Claude z narzedziem web search po stronie Anthropic API.
- sources.py: responseMode=lastNode; _unwrap toleruje bare object/list; sync zrodla
  zwracaja evidence inline. Timeout/_post w app/sources.py (sprawdz wartosc).
- CM->Researcher: cm-agent/app/research.py + sunday_brief.py (kontrakt POST /request,
  correlation_id uuid5 tygodnia). TEN kontrakt DZIALA (job powstal) - NIE ruszac.

## 3. HIPOTEZY (do weryfikacji W TEJ KOLEJNOSCI, kazda z dowodem zanim ruszysz dalej)

H1. Zywy workflow n8n zwraca blad z api.anthropic.com, ktory Normalize/Guard zamienia
    na pusta odpowiedz: najczestsze od konca czerwca = zmiana wymagan narzedzia web search
    (nazwa/typ narzedzia, wersja beta-header, model). SPRAWDZ: n8n API GET executions
    workflowu "Researcher - Web Search" z 20/07 07:25 UTC - zobacz WPROST co zwrocil
    wezel Web Search (status HTTP, body bledu Anthropic). To jeden strzal diagnostyczny,
    ktory prawdopodobnie rozstrzyga wszystko.
H2. Klucz Anthropic w app_secrets niewazny/wyczerpany (401/403 z API).
H3. Workflow nieaktywny albo webhook path rozjechany (wtedy sources._post dostaje 404 -
    ale to zwykle dawaloby error_message; run ma pusty = raczej H1/H2).
H4. Timeout po stronie sources.py (~2 min miedzy started a failed sugeruje mozliwy timeout
    requestu do n8n, a n8n dalej mieli; wtedy w executions n8n bedzie SUKCES po czasie).
NIE zaczynaj od przepisywania workflowu. Najpierw dowod z executions (H1) - dopiero potem patch.

## 4. ZAKRES NAPRAWY (DoD)

a) web_search DZIALA: testowy job przez POST /request (query proste, np. "top 3 AI model
   releases last 7 days"), complexity low -> status completed, >=1 evidence_items z
   source_url, cost_pln wypelniony. Dowod: wiersze z bazy + wpis executions n8n.
b) Sciezka niedzielna E2E: reczny tap "podklad na niedziele" u Tomasza -> podklad z TEZAMI
   I LINKAMI (nie fallback). UWAGA: stan tygodnia w brand_config `cm_sunday_brief` ma
   phase=sent dla week 2026-30 - do ponownego tap-testu w TYM tygodniu Tomasz musi
   wyzerowac klucz (podaj mu SQL: UPDATE brand_config SET config_value='{}' ... zgodnie
   z realnym ksztaltem; sprawdz kod sunday_brief._state_set zanim podasz).
c) Widocznosc bledow: naprawa "cichego failed" - worker/sources maja zapisywac przyczyne
   do research_runs.error_message i research_jobs.error_message oraz logowac do stdout
   (docker logs). Kazdy przyszly pad ma zostawiac slad. (Dzis: run.error_message PUSTY -
   to przez to diagnoza wymagala grzebania w 4 miejscach.)
d) OPCJONALNIE (guziki z Tomaszem, osobna decyzja): zapytanie niedzielne (sunday_brief)
   wymusza minimum medium zamiast auto->low (jedna zmienna w payload /request; plik
   cm-agent/app/sunday_brief.py _request_research). Wieksza kaskada = wiecej zrodel =
   odpornosc na pad jednego adaptera. Koszt ~1-3 PLN/tydzien. UWAGA: zmiana w cm-agent =
   commit na galezi build/researcher-fix, deploy cm-agenta skoordynuj z Tomaszem
   (rebuild cm-agent robi Tomasz swiadomie, nie w pakiecie z ags-researcher).
e) Jesli naprawa wymaga zmiany w n8n: zaktualizuj TEZ kopie repo
   n8n-workflows/researcher/web-search.json (jeden commit z kodem) + raport.

## 5. CZEGO NIE ROBISZ

- Nie dotykasz HITL (U5pUZjy2yAhR1sWg), cm-agent poza pkt 4d, DDL (zaden), post_queue/
  content_items, innych adapterow (firecrawl/gemini/openai_dr/manus) poza odczytem.
- Nie zmieniasz kaskady SOURCE_POLICY ani tierow globalnie.
- Nie wlaczasz zadnych cronow. Zamrozone rzeczy zostaja zamrozone.

## 6. Zamkniecie

Raport docs/cm/RAPORT_do_Managera_<data>_researcher_fix.md (dowody per DoD) + STATUS w tym
briefie + commit na build/researcher-fix + pamiec trwala (project_researcher_build - dopisac
awarie i naprawe). Merge do sb-work robi BE-INTEGRATOR / sesja glowna (zglos gotowosc).

STATUS = NAPRAWIONE (20/07 ~10:30, BE-RESEARCHER-FIX). Przyczyna: zmiana Anthropic ok. konca
czerwca - web_search_20260209 domyslnie dynamic filtering przez code_execution (15s -> 50-110s
+ nowe tryby padu); do tego potrojne polykanie bledow (Normalize/worker/brak executions).
Fix: allowed_callers:['direct'] w zywym workflow (22-28s) + Normalize przepuszcza bledy i liczy
cost_usd + saveDataErrorExecution:'all' + worker/sources zapisuja error_message (commit 3f97d90).
DoD a PASS (job 854de5b8: completed, 18 evidence, 4 opcje, cost_pln 0.7435, 62s - na starym
obrazie, sama naprawa n8n wystarczyla). CZEKA: rebuild ags-researcher (DoD c w kontenerze),
reset cm_sunday_brief + tap-test niedzielny (DoD b), decyzja 4d.
Raport: docs/cm/RAPORT_do_Managera_20072026_researcher_fix.md
