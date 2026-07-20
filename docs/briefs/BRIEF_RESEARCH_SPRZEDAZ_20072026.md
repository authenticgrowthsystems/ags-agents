# BRIEF BUILDU: DEEP RESEARCH SPRZEDAZOWY (20072026) - budowniczy: BE-RESEARCH-SPRZEDAZ

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_RESEARCH_SPRZEDAZ_20072026.md zbuduj`
CZYTAJ: brief Managera C:\Claude-CoWork\AGS\BE_BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md (SEKCJA 4)
+ docs/komponenty/researcher.md.

## 0. Tryb rownolegly
Worktree+galaz `build/research-sprzedaz` od origin/claude/silly-blackwell-dfc32d.
Research w tle, NIE blokuje buildow B/C. Zero zmian kodu/n8n poza zleceniami do Researchera.

## 1. CO robisz

**KOREKTA TOMASZA 20/07 ~15:30 (nadpisuje tiery ponizej): tier critical NIE idzie przez API**
(koszt ~18 PLN/job). Podzial pracy:
- **critical = RECZNIE Tomasz** na wlasnych abonamentach (Manus Pro / Gemini / ChatGPT DR);
  wyniki dostarcza jako pliki do `docs/research/sprzedaz_20072026/` (konwencja intake:
  README.md w tym folderze). Dotyczy zwlaszcza tematu 1 (konkurencja).
- **API Researchera = TYLKO tier medium** (tematy rynkowe 2-4). Zadnych jobow critical z API.

Zlecasz Researcherowi (LIVE po naprawie 20/07; kontrakt POST /request na ags-researcher:8088,
wzorzec zlecania: docs/komponenty/researcher.md; secret z app_secrets; tier: WYLACZNIE medium)
rownolegle badania, konsumujesz reczne zrzuty Tomasza z folderu, potem SYNTETYZUJESZ
w decyzyjne dokumenty docs/research/sprzedaz_20072026/:

1. **KONKURENCJA "GHL setup/retention dla malych firm"** (critical = RECZNIE Tomasz,
   zrzuty w folderze; BE tylko syntetyzuje): kto sprzedaje (PL i US),
   ceny setup/abonament, delivery, gdzie sie promuja (FB Groups, Reddit, YT, LinkedIn).
   Wynik: tabela + luka pozycjonowania dla AGS (my: rezultat-retencja, nie narzedzie).
2. **AI sales agent tools** (medium): Clay, Instantly, HeyReach, Attio AI - co robia, ceny,
   czy cokolwiek warto SPIAC zamiast budowac (Pareto; nasz Agent Sprzedazy = partner+HITL,
   nie mass-mailer - ocen pod tym katem).
3. **Payment processing PL/US dla tego modelu** (medium): Stripe vs GHL invoicing vs
   Przelewy24/inne - dla setup one-time PLN i USD; co najszybciej uruchomic DZIS
   (rekomendacja z krokami; deep research najpierw - docs-first, zadnych zalozen).
4. **Kanaly dotarcia do malych firm PL "uszczelnienie klientow"** (medium): gdzie realnie
   siedzi ICP (grupy FB, lokalne sieci, Oferteo/Useme?), jak wyglada skuteczny pierwszy
   kontakt bez spamu.

DoD: 4 dokumenty syntez z LINKAMI zrodel (regula prawdy) + JEDEN plik
REKOMENDACJE_SPRZEDAZ_20072026.md (max 1 strona: 5 decyzji do podjecia przez Tomasza/
Managera, kazda z opcjami i rekomendacja). Koszty jobow raportujesz (cost_pln z ledgera).

## 5. Udzial Tomasza
Reczny research critical na abonamentach (Manus Pro / Gemini / ChatGPT DR) -> pliki do
docs/research/sprzedaz_20072026/ wg README. Poza tym: przeczytanie rekomendacji.

## 6. Zamkniecie: raport + STATUS tu. STATUS = READY (20/07 ~13:20)
