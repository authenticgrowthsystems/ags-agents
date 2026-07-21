# BRIEF BUILDU: LACZNIK SYNCHRONIZACYJNY czat<->serwer (22072026) - budowniczy: BE-LACZNIK

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_LACZNIK_22072026.md zbuduj`
ZRODLO WYMAGAN (czytaj W CALOSCI): docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md
(koncept ZATWIERDZONY guzikami 21/07 + decyzja Tomasza: stan gry przez LINK Notion).
CZYTAJ TEZ: docs/komponenty/engagement-crm.md + rozmowa-cm.md + sync-notion.md +
docs/cm/RAPORT_dla_BE_22072026_INTAKE_UX_zamkniecie.md (swieze zmiany w conversation).

## 0. Tryb rownolegly

Worktree+galaz `build/lacznik` od origin/claude/silly-blackwell-dfc32d (PO pushu -
HEAD musi zawierac zamkniecie INTAKE-UX 94c0362). Zero deployu (integrator).
n8n: TYLKO ewentualna przepustka komendy /kontekst (patcher z backupem, wzorzec
hitl-sales-commands). DOTYKASZ: engagement.py, conversation.py (sekcje intake/route),
reports.py, sync_notion. NIE DOTYKASZ: publikacja, planner, sales.py, decisions core.

## 0.5 MINI-PORZADKI NA START (30-45 min, zalecenie raportu zamkniecia INTAKE-UX)

Przed wlasciwym buildem, w TYM oknie (osobny commit "mini-porzadki po INTAKE-UX"):
a) sales.py: wysylka odpowiedzi przez conversation._send_rendered (koniec surowych **
   u Sprzedawcy) - JEDYNY dozwolony dotyk sales.py w tym buildzie.
b) "paragon" -> "potwierdzenie" w komunikatach WIDOCZNYCH dla Tomasza
   (decisions/conversation/matreview); doktryna w docs zostaje "paragonem".
c) Potwierdzenie po [Wyslalem]/[Wkleilem] NOWA wiadomoscia zamiast nadpisywania -
   kontrola PL zostaje widoczna w czacie (drobiazg 6 z raportu zamkniecia).

## 1. CO budujemy (etap 1 konceptu, 4 klocki)

1. **Parser RAPORT PRACY (bez LLM).** Deterministyczny route na `[RAPORT PRACY` w
   rozmowie (i plik .md przez handle_document): linie
   `- typ | @handle | link/tresc | ...` (typy: komentarz, dm_wyslany, dm_odebrany,
   reakcja, nowa_osoba, obserwacja - pelny format w koncepcie) ->
   INSERT engagement_log (status wg typu) + contacts (clean_author z INTAKE-UX!,
   stadium wg akcji: komentarz->commented, dm_*->dm) + inspirations dla 'obserwacja'.
   NOWE osoby: JEDNA karta crm_tier (mechanizm z INTAKE-UX, 1/24h). POTWIERDZENIE
   z licznikami ("zapisane: 3 komentarze, 1 DM, 2 nowe osoby, pominiete duplikaty: 1").
   UWAGA JEZYKOWA: w tekstach do Tomasza slowo "potwierdzenie", nie "paragon".
   Idempotencja: sha256 znormalizowanej linii w engagement_log.notes ('sync:<hash>');
   przed INSERT sprawdz hash - podwojna wklejka = zero dubli. ZERO nowych DDL.
2. **Komenda /kontekst [x|linkedin|sprzedaz|all]** (route deterministyczny + przepustka
   n8n): zwarty stan gry BEZ LLM - plan tygodnia (sloty+statusy), ostatnie publikacje
   (published_posts + metryki), kontakty w grze (stadium != cold, ostatnia interakcja),
   otwarte decyzje, lejek sprzedazy (sales_pipeline), notatki radaru. Wysylka: tekst
   do 4096 albo plik .md (wzorzec _tg_send_document). To jest FALLBACK stanu gry.
3. **Stan gry przez LINK (preferencja Tomasza):** strona Notion "Stan gry AGS"
   (jedna strona, NADPISYWANA - nie append; sync_registry/page_map wzorzec) odswiezana
   przez sync-notion po publikacji / zmianie lejka / nowym kontakcie (tick, throttle
   max 1 update/15 min). Tresc = to samo co /kontekst. Gdy Notion timeout - trudno,
   fallback /kontekst (NIE blokowac niczym innym; timeouts znane z #71).
4. **MASTERPROMPTY CZATOWE (docs/product/masterprompty-czat/):** Tomasz na starcie
   buildu wklei swoje robocze masterprompty (X, LinkedIn, ew. sprzedaz). Przerabiasz
   je na STALE wersje: tozsamosc+glos (Voice Bible, regula prawdy, zero em-dash),
   obowiazek konczenia sesji blokiem [RAPORT PRACY v1], instrukcja "stan gry czytasz
   z linku: <link do strony Notion>" + fallback "popros o /kontekst". Wersjonowane
   pliki w repo (pelne pliki przy iteracji, nie diffy).

## 2. DoD (tap-testy z Tomaszem)

a) Wklejka przykladowego RAPORTU PRACY (5 linii, w tym 1 duplikat i 1 nowa osoba) ->
   potwierdzenie z licznikami, wpisy w DB (sonda read-only), karta tieru dla nowej osoby;
   druga wklejka tego samego -> "pominiete duplikaty: 5".
b) /kontekst x -> stan gry zgodny z baza (zweryfikowany sonda).
c) Strona Notion "Stan gry AGS" istnieje i odswieza sie po zmianie (dowod: timestamp).
d) Masterprompt czatowy X: Tomasz otwiera czat na abonamencie, wkleja masterprompt,
   agent czyta stan gry z linku i konczy sesje poprawnym blokiem RAPORT PRACY.
Dokumentacja W TYM SAMYM commicie: nowy komponent docs/komponenty/lacznik.md +
aktualizacja engagement-crm.md i sync-notion.md + masterprompt (sekcja 6 backlog).

## 3. Czego NIE robic

Etap 2 (MCP/endpoint read-only dla czatu) = NIE TERAZ. Zadnego LLM w parserze ani
w /kontekst. Zadnych zmian w publikacji/planner/sales POZA mini-porzadkami 0.5
(a: jedna linia wysylki w sales.py; b: slownictwo; c: potwierdzenie nowa wiadomoscia).
NIE buduj bez sygnalu (raport zamkniecia pkt 3): ujednolicanie zdjec przy CM do karty
intencji, scalanie starych stubow contacts - zamrozone do decyzji Tomasza.

## 5. Udzial Tomasza
Wklejka masterpromptow na starcie; link/strona-matka Notion (gdzie zalozyc "Stan gry");
tap-testy a-d.

## 6. Zamkniecie: raport + komponent + STATUS tu. STATUS = READY (22/07 ~00:50)
