# BRIEF BUILDU: INTAKE-UX subagentow (21072026) - budowniczy: BE-INTAKE-UX

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_INTAKE_UX_21072026.md zbuduj`
CZYTAJ NAJPIERW: docs/komponenty/rozmowa-cm.md + engagement-crm.md + decyzje-nauka.md.
Zrodlo wymagan: uwagi Tomasza 21/07 wieczor (screeny sesji z Djordje Klikovac i Dan
Martell) - "toporna obsluga", subagent = partner pilnujacy swojego kanalu.

## 0. Tryb rownolegly

Worktree+galaz `build/intake-ux` od origin/claude/silly-blackwell-dfc32d (PO pushu
Tomasza z 21/07 wieczor - HEAD musi zawierac naprawe incydentu publikacji).
Zero deployu, zero n8n poza ewentualna przepustka komend (patcher z backupem).
DOTYKASZ: conversation.py (sekcje subagentow), engagement.py, matreview (karty).
NIE DOTYKASZ: publikacja/planner/sales.py (rownolegly ruch sprzedazowy na zywo!).

## 1. CO budujemy (4 wady z zywej sesji 21/07)

1. **B1 PAMIEC WATKU SUBAGENTA (najwazniejsze).** Dowod wady: subagent linkedin sam
   stresci DM od Djordje ("DM: Oferuje przeszkolonych setterow..."), a 3 wiadomosci
   pozniej na "Dm" odpowiada "Pokaz mi tresc tej wiadomosci DM - nie mam kontekstu".
   Wymaganie: rozmowa subagenta trzyma okno historii (ostatnie N wymian W TYM swoje
   wlasne odpowiedzi i wyniki intake'u) i odwoluje sie do niego zanim poprosi
   o powtorzenie czegokolwiek. Sprawdz jak trzyma historie CM (conversation) i
   wyrownaj subagentow do tego samego mechanizmu - jeden kontrakt, nie fork.
2. **B2 MENU INTENCJI PO WRZUTCE.** Po zrzucie/zrzutach (album = jeden kontekst,
   media_group_id juz grupuje) subagent NAJPIERW pokazuje JEDNA karte: co widzi
   (nowa osoba X, post nadajacy sie do komentarza, DM, artykul) + co proponuje,
   z GUZIKAMI intencji: [Skomentuj] [Odpowiedz na DM] [Poznaj/intake osoby]
   [Tylko zapisz] [Wszystko po kolei]. Wybor Tomasza -> wykonanie SEKWENCYJNE,
   kazdy watek DOMKNIETY paragonem, po ostatnim dopiero "co dalej?". Zadnego
   rownoleglego floodu kart. Wzorzec guzikow: decisions.ask (dec:<id>:<key>) albo
   matnav - wybierz jeden, nie buduj trzeciego frameworku.
3. **B3 DEDUP WRZUTEK PER OSOBA.** Dowod wady: Djordje dostal 3x karte "Nowa osoba"
   i 2x decyzje crm_tier (#6 i #7). Wymaganie: jedna osoba (match po handle) w oknie
   24h = JEDEN wpis intake + JEDNA decyzja; kolejne zrzuty tej samej osoby DOKLEJAJA
   kontekst do otwartego watku zamiast otwierac nowy.
4. **B4 FORMATOWANIE.** Odpowiedzi subagentow pokazuja surowe `**` w Telegramie.
   Konwersja do parse_mode HTML (albo zdjecie markdownu) w JEDNYM miejscu wysylki -
   tam gdzie idzie kazda wiadomosc subagenta (nie per-handler).

## 2. DoD (tap-testy z Tomaszem)

a) Rozmowa: streszczenie DM -> 3 wiadomosci dalej "odpowiedz na ten DM" dziala BEZ
   proszenia o powtorzenie. b) Album 2 zrzutow (profil+post) -> JEDNA karta z menu
   intencji; wybor 2 pozycji -> wykonane po kolei, 2 paragony, potem "co dalej".
c) Ten sam profil wrzucony 2x -> zero drugiej karty/decyzji. d) Wiadomosc z pogrubieniem
   renderuje sie bez gwiazdek. Dokumentacja (rozmowa-cm.md + engagement-crm.md)
   W TYM SAMYM commicie.

## 3. Kierunek produktowy (NIE ten build - zapisz tylko w docs)

Interfejs = wymienny konektor (kanon SNAPSHOT): Slack = watki natywne, aplikacja
webowa = lista wiszacych zadan z rozwijaniem i domykaniem klikiem (glowny kandydat).
Telegram robi co moze - projektuj B2 tak, zeby intencje/watki byly obiektami w DB
(nie tylko wiadomosciami), wtedy przyszly konektor je tylko inaczej wyswietli.

## 5. Udzial Tomasza
Tap-testy DoD. Decyzje guzikami gdy trzeba wybrac zakres.

## 6. Zamkniecie: raport + komponenty + STATUS tu.

STATUS = DONE (22/07 ~00:35): WDROZONE LIVE, tap-testy DoD 4/4 PASS (a-d, z iteracjami
z zywych tapow: cmt:sent jeden tap, kontrola PL po tresci, jezyk DM = jezyk rozmowcy,
koniec podwojnej linii guzikow). Commity build/intake-ux: 00226bf + 2c5a545 + 5b09cb5 +
b8de7bb, wszystkie zmergowane do silly-blackwell i przebudowane. Zero DDL, zero n8n.
Raporty: docs/cm/RAPORT_do_Managera_21072026_intake_ux.md (wykonawczy) +
docs/cm/RAPORT_dla_BE_22072026_INTAKE_UX_zamkniecie.md (zamkniecie, backlog, next).
Bonus: naprawiony martwy guzik 'Inny kat' (brak importu TRUTH_GUARD od 20/07).
