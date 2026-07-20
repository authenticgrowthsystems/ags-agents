# RAPORT do Managera: naprawa Researchera (web_search) - 20/07/2026

Sesja: BE-RESEARCHER-FIX (rownolegle okno, brief docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md)
Galaz: claude/badacz-naprawa-d324bd (baza: sb-work 471b7da; worktree utworzony przez Cowork pod ta nazwa
zamiast build/researcher-fix - funkcjonalnie to samo, merge do sb-work robi BE-INTEGRATOR)

## 1. DIAGNOZA (dowody, kolejnosc wg briefu H1-H4)

Executions n8n z 20/07 07:25 nie istnieja - workflow mial saveDataErrorExecution='none',
wiec zaden pad nie zostawial sladu w n8n. Diagnoza poszla przez reprodukcje tymczasowymi
workflowami n8n (wzorzec verify-*.cjs, wszystkie skasowane po uzyciu):

- H2 (klucz Anthropic niewazny): OBALONE. Replika produkcyjnego requestu (klucz z app_secrets)
  zwrocila HTTP 200 z wynikami.
- H3 (workflow nieaktywny / zly path): OBALONE. Workflow oxwcD1iuVpn26C1o aktywny, webhook odpowiada.
- H1 (zmiana wymagan narzedzia web search od konca czerwca): POTWIERDZONE jako przyczyna systemowa,
  w zlagodzonej formie. DOCS-FIRST (platform.claude.com, aktualna dokumentacja web search tool):
  typ `web_search_20260209` ma od pewnego momentu domyslne `allowed_callers=["code_execution_20260120"]`
  (dynamic filtering) - wyszukiwanie biegnie przez code execution. Pomiar na zywym kluczu:
  wywolanie produkcyjne = 51-110 s (bylo ~15 s przed zmiana). Zbiega sie z data padow
  (wszystkie joby od 28/06 failed, do 27/06 completed).
- H4 (timeout w sources.py): run 20/07 trwal ~125 s i skonczyl sie status=error z PUSTYM
  error_message. Wzorzec czasowy pasuje do 3 prob z retry (tenacity: 30 s + 60 s odstepu)
  na TransportError. Dokladnego bledu transportowego z 07:25 NIE DA SIE odtworzyc, bo:
  (a) n8n nie zapisywal executions, (b) worker WYRZUCAL tresc bledu (zapisywal tylko status),
  (c) Normalize zamienial kazdy blad API na cicha pusta odpowiedz. Potrojne polykanie bledow -
  naprawione w tym buildzie (pkt DoD c), kazdy przyszly pad zostawi slad.

WNIOSEK: czerwcowa zmiana Anthropic (dynamic filtering domyslnie) wydluzyla wywolanie 4-7x
i dodala nowe tryby padu w oknie 50-110+ s; laczna niezawodnosc sciezki spadla na tyle,
ze 3 kolejne joby (28/06, 03/07, 20/07) padly, a slepota na bledy ukryla przyczyne.

## 2. NAPRAWA (co zmienione)

a) Zywy workflow n8n "Researcher - Web Search" (oxwcD1iuVpn26C1o) - PUT z backupem
   (scratchpad backup-websearch-oxwcD1iuVpn26C1o-20260720.json), po PUT deactivate+activate (AP):
   - narzedzie: `allowed_callers: ['direct']` - klasyczne wyszukiwanie bez code_execution;
     zmierzone 23-28 s zamiast 110 s, kształt odpowiedzi klasyczny (top-level web_search_tool_result);
   - Normalize: przepuszcza bledy (blad API Anthropic, blad HTTP, web_search_tool_result_error,
     pusty wynik ze stop_reason) w polu `error` + liczy `cost_usd` z usage (tokeny wg stawek
     sonnet-4-6 3/15 USD/MTok + 10 USD/1k wyszukiwan) -> research_runs dostana koszt;
   - settings: saveDataErrorExecution='all' (pad zostawia execution w n8n).
   Kopia repo n8n-workflows/researcher/web-search.json zaktualizowana; zweryfikowano przez API,
   ze body/Normalize/Guard/settings w repo == zywa definicja (4x match:true).

b) ags-researcher/app/sources.py: kazda sciezka bledu zwraca tresc w `error`
   (pusty/nie-JSON response adaptera, async start bez provider_job_id, timeout pollingu).

c) ags-researcher/app/worker.py (DoD c - widocznosc bledow):
   - zapis `error` zrodla do research_runs.error_message + log "[researcher] job X source Y status=... error=..." do stdout;
   - przy totalnym padzie research_jobs.error_message = "no sources returned evidence: web_search=error (...)" -
     zagregowane przyczyny per zrodlo (koniec diagnozy w 4 miejscach);
   - _run_source lapie wyjatki per-zrodlo (ostatnia linia obrony).
   py_compile OK. UWAGA: zmiany w workerze wymagaja rebuildu kontenera ags-researcher (Tomasz SSH).

## 3. DOWODY per DoD

- DoD a (testowy job): job 854de5b8-182a-40f6-982a-6312c0c6de76, POST /request przyjety 202,
  query "top 3 AI model releases last 7 days", complexity low -> web_search.
  WYNIK (wiersze z zywej bazy, odczyt read-only): status=completed, complexity=low,
  model_tier=haiku, cost_pln=0.7435, created 08:11:42 UTC -> completed 08:12:44 UTC (62 s);
  runy: web_search=completed, synthesis=completed; evidence_items=18 (przyklady:
  llm-stats.com/llm-updates, aireleasetracker.com/latest, llm-stats.com/ai-news); options=4.
  DoD a SPELNIONE W CALOSCI (completed + evidence z source_url + cost_pln wypelniony).
  Uwaga: przeszlo na STARYM obrazie kontenera - naprawa adaptera w n8n wystarczyla do
  przywrocenia dzialania; rebuild potrzebny tylko dla widocznosci bledow (DoD c).
- Adapter E2E (z Guardem i sekretem, przed jobem): status completed, 10-13 evidence z source_url,
  cost_usd 0.084745 (18950 in / 1193 out tokenow), 22.8 s.
- DoD b (sciezka niedzielna): wymaga Tomasza (SQL reset stanu tygodnia + reczny tap) - patrz sekcja 4.
- DoD c: kod wdrozony na galezi; efekt w kontenerze po rebuildzie.
- DoD e: kopia repo zaktualizowana w tym samym commicie co kod (3f97d90).

## 4. CO ZOSTAJE DLA TOMASZA (pelne komendy)

1) Rebuild kontenera ags-researcher (SSH na Mikrus, katalog compose projektu):
   docker compose build ags-researcher && docker compose up -d ags-researcher
   docker logs -f ags-researcher    (oczekiwane: "[researcher] secrets loaded from app_secrets")

2) Reset stanu tygodnia niedzielnego (zeby tap-test w TYM tygodniu przeszedl mimo phase=sent),
   przez docker exec psql na serwerze:
   UPDATE brand_config SET config_value='{}', version=version+1, updated_by='researcher-fix-test', updated_at=NOW()
   WHERE brand_id='AGS' AND config_key='cm_sunday_brief';

3) Tap-test: w Telegramie do CM napisac "podklad na niedziele" -> podklad ma zawierac TEZY I LINKI
   (nie fallback "research nie dojechal").

## 5. STATUS TESTOW

- Replika requestu produkcyjnego (dynamic filtering): 200, 51-110 s - dziala, ale wolno. [PRZED naprawa]
- Wariant allowed_callers=['direct']: 200, 27.8 s, klasyczny kształt odpowiedzi. [dowod na fix]
- Zywy adapter E2E po patchu (Guard+sekret): completed, 10 evidence, cost_usd 0.084745, 22.8 s.
- Testowy job przez /request: completed w 62 s, 18 evidence, 4 opcje, cost_pln 0.7435. [DoD a PASS]
- Kopia repo == zywa definicja (body/Normalize/Guard/settings match:true przez API).
- Sprzatanie: 0 workflowow TEMP w n8n po sesji (weryfikacja przez API).
- DoD b (tap niedzielny): CZEKA na kroki Tomasza z sekcji 4.
- DoD c: kod na galezi (commit 3f97d90), efekt po rebuildzie kontenera.

## 6. Sprzatanie

Wszystkie tymczasowe workflowy n8n (diag/diag2/diag3/diag4 + check) utworzone i SKASOWANE
w tej sesji (kazdy przez try/finally deactivate+delete). HITL U5pUZjy2yAhR1sWg nietkniety.
Inne adaptery nietkniete. Zero DDL, zero zmian w cm-agent (pkt 4d czeka na decyzje guzikami).
