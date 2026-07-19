# BRIEF BUILDU: CM CZYTA SWIAT - niedzielny artykul (19072026) - budowniczy: BE-SWIAT

Wywolanie sesji (Opus 4.8, nowe okno Cowork):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_CM_CZYTA_SWIAT_19072026.md zbuduj`

## 0. TRYB ROWNOLEGLY (Tomasz 19/07 ~22:45 - NADPISUJE sekwencyjnosc; przeczytaj PRZED praca)

Wszystkie 4 buildy ida ROWNOLEGLE w osobnych oknach. Zasady twarde:
1. PIERWSZY RUCH: utworz WLASNY worktree + galaz od galezi bazowej (NIE pracuj na sb-work!):
   `git -C "C:\Claude-CoWork\AGS\ags-agents" worktree add "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\build-swiat" -b build/czyta-swiat origin/claude/silly-blackwell-dfc32d`
   Wszystkie sciezki i git -C w tej sesji = ten worktree. Committuj na build/czyta-swiat.
2. ZAKAZ deployu: ZERO push na serwer, ZERO rebuild cm-agent, ZERO psql, ZERO zmian n8n
   (gdy brief wymaga DDL - plik db/0NN LEZY w commicie, wykona go INTEGRATOR). Kod + py_compile
   + testy lokalne (parser/regex - jak sie da bez serwera) + commit. Weryfikacje read-only
   (temp webhook) WOLNO.
3. Dotykaj TYLKO plikow z sekcji KONTRAKT swojego briefu - reszta nalezy do rownoleglych
   budowniczych (konflikty rozwiazuje integrator, nie mnoz ich).
4. Model: sesje zaczyna Fable 5 (max 2 prompty: wczytanie + szkielet decyzji), potem Tomasz
   przelacza na Opus 4.8, ktory KONCZY build w tym samym oknie (kontekst zostaje).
5. Zamkniecie: commit na build/czyta-swiat + STATUS w tym briefie + raport per krok; masterprompt
   aktualizuje TYLKO INTEGRATOR (unik konfliktow na wspolnym pliku).

## 1. CO budujemy (definition of done)

KANON 19/07 (Tomasz): niedzielny artykul LinkedIn = insight tygodnia ze swiata AI; robi go
Tomasz RECZNIE, a planer ma zakaz planowania niedzieli - DOPOKI CM nie umie sam czytac swiata.
Ten build = zdolnosc czytania swiata: cotygodniowy digest tego, co sie dzialo w AI, jako
PODKLAD pod artykul (draft do recznej obrobki Tomasza w sobote, NIE auto-publikacja).

Mechanizm (Pareto, na istniejacych organach):
- SOBOTA rano (tick w petli workera, wzorzec weekly_metrics_reminder): CM zleca Researcherowi
  (POST /request na ags-researcher:8088, kontrakt juz istnieje - CM commissions research)
  badanie "najwazniejsze wydarzenia/dyskusje AI ostatnich 7 dni dla ICP solo-founderow"
  (tier medium - CM ma cap <=medium).
- Wynik + schowek tygodnia (inspirations, w tym zlapane posty innych z Idea Bota) + top
  publikacje tygodnia -> synteza (Sonnet): 3 kandydackie tezy artykulu z twardymi liczbami
  i zrodlami.
- SOBOTA ~12:00: wiadomosc do Tomasza: "Podklad pod niedzielny artykul" (tezy + fakty +
  linki zrodel) + przypomnienie o materialach wlasnych. ZERO wpisu do planu/kolejki.

DoD:
- [ ] Sobotni tick wysyla podklad (tap-test: wywolanie reczne "podklad na niedziele")
- [ ] Draft NIE wchodzi do content_items ani post_queue (kanon: niedziela = recznie)
- [ ] Zrodla w podkladzie linkowane (regula prawdy - zero niepodpartych faktow)

## 2. KONTRAKT

- Researcher /request (RESEARCHER_URL w config; wzorzec: research.py w cm-agent),
  inspirations (odczyt), published_posts (top tygodnia), sendMessage (conversation._tg).
- Zero DDL (wyniki Researchera ladowane jego wlasnym obiegiem), zero n8n.
- Stan anty-dublowy w brand_config (wzorzec _state_get/_state_set, klucz cm_sunday_brief).

## 3. Czego NIE dotykac

Planner (zakaz niedzieli ZOSTAJE), gap-filler, bramka tematow, publikacja.

## 4. Stan zastany

Researcher LIVE (5 zrodel, cost-cascade, cap medium dla CM); Idea Bot lapie cudze posty
do inspirations; kanon niedzielny w planner._cadence_text + proactive._expected (19/07).

## 5. Udzial Tomasza

Push + rebuild + tap-test podkladu; w sobote: obrobka podkladu w artykul (jego czesc kanonu).

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_czyta_swiat.md + masterprompt + pamiec + STATUS tu.

STATUS = KOD GOTOWY (build/czyta-swiat, 19/07 Fable5->Opus4.8). Zbudowane:
- app/sunday_brief.py (nowy organ): sobotnia maszyna stanu (brand_config cm_sunday_brief) - zlecenie
  Researcherowi (kontrakt /request, correlation=uuid5 tygodnia, tier auto <=medium) -> polling
  research_jobs.status -> synteza Sonnet (task 'sunday_synth') 3 tez z faktami+LINKAMI ZRODEL ->
  sendMessage do Tomasza; ZERO wpisu do content_items/post_queue; auto_done rozdziela reczny
  tap-test od sobotniego automatu (test nie kasuje soboty); fallback prawdy (research niegotowy o
  13:00 / dead / manual 20 min -> podklad ze schowka+publikacji z jawnym oznaczeniem).
- app/research.py: job_status(), claims_with_sources()/grounding_with_sources() (join claims->
  evidence_items po source_url; UWAGA supporting_evidence=text[] NIE uuid[] jak spec 23/06 -
  join po evidence_id::text; _clean_url tnie artefakt 'arxiv.org/abs/web:').
- app/worker.py: sunday_brief.tick() w petli (obok proactive.tick()).
- app/conversation.py: narzedzie sunday_world_brief (tap-test "podklad na niedziele").
WERYFIKACJA read-only (temp webhook, skasowany): 5 tabel Researchera zyje w ags_crd; evidence 699/699
z source_url (100%); job status 'completed'=terminal-OK; join claims->URL zwraca zrodla; inspirations
22 wpisy/7 dni (telegram/notion/cm_conversation). py_compile OK; _clean_url+uuid5 przetestowane lokalnie.
DO INTEGRATORA: rebuild cm-agent (bez DDL, bez n8n); TAP-TEST: napisz do CM "podklad na niedziele" ->
ma przyjsc zapowiedz, po kilku min 3 tezy z linkami; sprawdz ze content_items/post_queue bez nowych
wierszy. Raport: docs/cm/RAPORT_do_Managera_19072026_czyta_swiat.md. NIE dotykalem masterpromptu (kanon
trybu rownoleglego - robi to INTEGRATOR).
