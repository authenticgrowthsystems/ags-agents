# BRIEF BUILDU: PORZADKI DETERMINISTYCZNE (19072026) - budowniczy: BE-PORZADKI

Wywolanie sesji (Opus 4.8, nowe okno Cowork):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_PORZADKI_DETERMINISTYCZNE_19072026.md zbuduj`

## 0. TRYB ROWNOLEGLY (Tomasz 19/07 ~22:45 - NADPISUJE sekwencyjnosc; przeczytaj PRZED praca)

Wszystkie 4 buildy ida ROWNOLEGLE w osobnych oknach. Zasady twarde:
1. PIERWSZY RUCH: utworz WLASNY worktree + galaz od galezi bazowej (NIE pracuj na sb-work!):
   `git -C "C:\Claude-CoWork\AGS\ags-agents" worktree add "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\build-porzadki" -b build/porzadki origin/claude/silly-blackwell-dfc32d`
   Wszystkie sciezki i git -C w tej sesji = ten worktree. Committuj na build/porzadki.
2. ZAKAZ deployu: ZERO push na serwer, ZERO rebuild cm-agent, ZERO psql, ZERO zmian n8n
   (gdy brief wymaga DDL - plik db/0NN LEZY w commicie, wykona go INTEGRATOR). Kod + py_compile
   + testy lokalne (parser/regex - jak sie da bez serwera) + commit. Weryfikacje read-only
   (temp webhook) WOLNO.
3. Dotykaj TYLKO plikow z sekcji KONTRAKT swojego briefu - reszta nalezy do rownoleglych
   budowniczych (konflikty rozwiazuje integrator, nie mnoz ich).
4. Model: sesje zaczyna Fable 5 (max 2 prompty: wczytanie + szkielet decyzji), potem Tomasz
   przelacza na Opus 4.8, ktory KONCZY build w tym samym oknie (kontekst zostaje).
5. Zamkniecie: commit na build/porzadki + STATUS w tym briefie + raport per krok; masterprompt
   aktualizuje TYLKO INTEGRATOR (unik konfliktow na wspolnym pliku).

## 1. CO budujemy (trzy male, powiazane naprawy - jeden build)

(A) DETERMINISTYCZNY ROUTE KOMEND KONFIGURACYJNYCH. Incydent 19/07: CM odpowiedzial
"Zrobione. AGS LinkedIn ma teraz okno 16:00-18:00" BEZ wywolania target_update (DB
niezmienione, brak paragonu ⚙️; naprawa recznym SQL-em). Prompt z TWARDA ZASADA nie
wystarcza. Fix: regex route w conversation.handle (PRZED LLM, wzorzec _KARTY_RE) dla
najczestszych komend: "ustaw okno publikacji dla <brand> <channel> na HH:MM-HH:MM" i
"ustaw <key> dla <brand> <channel> na <value>" -> wprost _target_update -> paragon ⚙️.
Nierozpoznane frazy ida do LLM jak dotad.

(B) ODRZUCENIE KARTY KASUJE WIERSZE KOLEJKI. Dowod: wiersz pq 245 odrzuconego artykulu
zostal w 'review' na zawsze (nie publikuje sie, ale smieci i myli podglady). Fix 1 linia
w matreview.handle akcja 'no' (po set_item_status): UPDATE post_queue SET status='rejected'
WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued').

(C) SQL SPRZATAJACY istniejace sieroty (podac Tomaszowi do SSH):
UPDATE post_queue pq SET status='rejected' FROM content_items ci
WHERE ci.id=pq.content_item_id AND pq.status='review' AND ci.status IN ('rejected','archived');

DoD: py_compile; tap-testy: "ustaw okno publikacji dla AGS x na 13:00-21:00" -> paragon ⚙️
+ DB zmienione (verify read-only); odrzucenie karty -> pq wiersze rejected; sieroty = 0.

## 2. KONTRAKT

conversation.py (route przed LLM), matreview.py (akcja no), zero DDL, zero n8n.

## 3. Czego NIE dotykac

/set (n8n allowlista - osobna sciezka, dziala), decisions.py, planner.

## 5. Udzial Tomasza

SQL (C) + push + rebuild + 2 tap-testy.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_porzadki.md + masterprompt + pamiec + STATUS tu.

STATUS = READY (brief 19/07, tryb awaryjny - handoff na Opus 4.8)
