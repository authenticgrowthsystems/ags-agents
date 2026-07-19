# BRIEF BUILDU: BRAMKA DUPLIKACJI (19072026) - budowniczy: BE-DEDUP

Wywolanie sesji (Opus 4.8, nowe okno Cowork):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_BRAMKA_DUPLIKACJI_19072026.md zbuduj`

## 0. TRYB ROWNOLEGLY (Tomasz 19/07 ~22:45 - NADPISUJE sekwencyjnosc; przeczytaj PRZED praca)

Wszystkie 4 buildy ida ROWNOLEGLE w osobnych oknach. Zasady twarde:
1. PIERWSZY RUCH: utworz WLASNY worktree + galaz od galezi bazowej (NIE pracuj na sb-work!):
   `git -C "C:\Claude-CoWork\AGS\ags-agents" worktree add "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\build-dedup" -b build/dedup origin/claude/silly-blackwell-dfc32d`
   Wszystkie sciezki i git -C w tej sesji = ten worktree. Committuj na build/dedup.
2. ZAKAZ deployu: ZERO push na serwer, ZERO rebuild cm-agent, ZERO psql, ZERO zmian n8n
   (gdy brief wymaga DDL - plik db/0NN LEZY w commicie, wykona go INTEGRATOR). Kod + py_compile
   + testy lokalne (parser/regex - jak sie da bez serwera) + commit. Weryfikacje read-only
   (temp webhook) WOLNO.
3. Dotykaj TYLKO plikow z sekcji KONTRAKT swojego briefu - reszta nalezy do rownoleglych
   budowniczych (konflikty rozwiazuje integrator, nie mnoz ich).
4. Model: sesje zaczyna Fable 5 (max 2 prompty: wczytanie + szkielet decyzji), potem Tomasz
   przelacza na Opus 4.8, ktory KONCZY build w tym samym oknie (kontekst zostaje).
5. Zamkniecie: commit na build/dedup + STATUS w tym briefie + raport per krok; masterprompt
   aktualizuje TYLKO INTEGRATOR (unik konfliktow na wspolnym pliku).

## 1. CO budujemy (definition of done)

Twarda bramka duplikacji TEZY przy generacji materialu: zanim karta pojdzie do Tomasza,
canonical porownywany embeddingiem z OPUBLIKOWANYMI (content_memory, pgvector juz dziala)
- wysokie podobienstwo NIE blokuje, ale karta przychodzi z ostrzezeniem.

DOWOD POTRZEBY (incydent 19/07): material "Orkiestracja agentow" zdublowal slowo w slowo
teze posta X z 11/07 ("Single agent hits a wall fast..."); lista ostatnich publikacji w
prompcie planera NIE wystarczyla (LLM zignorowal); wykryla to dopiero zewnetrzna bramka
(przegladarkowy CM) + potwierdzenie w published_posts.

DoD:
- [ ] Przy worker._draft po wygenerowaniu canonicala: embedding vs published (14-30 dni),
      prog ~0.85 cosine -> flaga w content_items.media (kind='dup_warning', text='podobienstwo
      0.92 do "<head>" z <data>') i OSTRZEZENIE na karcie (matreview._card pokazuje ⚠️ linie).
- [ ] Zero blokowania: decyzja ZAWSZE u Tomasza (kanon 19/07); bramka tylko INFORMUJE.
- [ ] py_compile + tap-test: material o tezie z ostatnich dni -> karta z ⚠️.

## 2. KONTRAKT wpiecia w szyne

- content_memory: uzyj istniejacego wyszukiwania podobienstwa (pgvector, embeddingi OpenAI -
  find_similar_published juz istnieje jako tool rozmowy; wywolaj te sama warstwe z workera).
- Zapis: TYLKO descriptor w content_items.media (zero DDL). Karta: matreview._card.
- Zero n8n, zero nowych endpointow.

## 3. Czego NIE dotykac

Planner/bramka tematow (dziala), decisions.py, Scheduler, publikacja. Zadnego auto-odrzucania.

## 4. Stan zastany

content_memory.get_published + pgvector LIVE; reguly stylu #11/#12 (dedup + twarda liczba)
zapisane w style_learned - bramka jest ich mechanicznym domknieciem.

## 5. Udzial Tomasza

Push + rebuild + jeden tap-test (karta z ⚠️).

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_dedup.md + masterprompt + pamiec + STATUS tu.

STATUS = READY (brief 19/07, tryb awaryjny - handoff na Opus 4.8)
