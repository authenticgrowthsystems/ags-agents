# RAPORT AKTUALIZACYJNY DO MANAGERA - 25/07/2026 popoludnie

Uzupelnienie raportu porannego (docs/cm/RAPORT_do_Managera_25072026_stan_9rano.md). Ponizej
to, co domkniete OD 9 rano: wykonanie kadencji, sprzatniecie kolejki X i wdrozony audyt
subagentow. Plus jeden nowy kanon dla przyszlych buildow.

## Jednym zdaniem

Kolejka X (64 posty) jest posprzatana do 4/dzien z zachowaniem spojnosci serii, subagenci
dostali wejscie do dnia Tomasza, a caly epizod dal regule, ktora warto miec na przyszlosc:
masowa zmiana zywych danych zawsze przez deterministyczny podglad.

## 1. Kadencja X: sufit + sprzatanie (zgloszenie Tomasza "po co tyle tweetow")

**Sufit (przyszlosc):** `slots._daily_cap` - twardy limit publikacji na dobe per kanal
(X = gorna granica posts_per_day, LinkedIn = 1). Seria z jednego materialu nie rozlewa sie
juz ponad kadencje - gdy dzien osiagnie limit, kolejna czesc idzie na nastepny dzien.

**Sprzatanie (przeszlosc):** sonda pokazala, ze kolejka X urosla do **64 wierszy** przez ~2
tygodnie, z dniami po 7-9 postow (serie rozlewaly sie ZANIM powstal sufit). Narzedzie
`app.reslot` (dry/apply) przeplanowalo cala kolejke: **cale serie w ciaglych blokach, czesci
w kolejnosci narracyjnej, 4 posty/dzien** (wybor Tomasza guzikami - kompromis miedzy gestoscia
a dlugoscia kolejki). Efekt: 25/07-09/08 rowno po 4, hook przed rozwinieciem, grafiki nietkniete.

Kolejnosc czesci serii biore z `id` (kolejnosc wstawiania przez stage_variant), nie ze
`scheduled_for` - ten rozprasza sie miedzy re-slotami. Dla swiezo rozbitych serii (identyczny
slot) `id` to jedyna informacja o kolejnosci; jesli gdzies wyjdzie nie po kolei, to bedzie ten
przypadek i poprawimy recznie.

## 2. Subagenci dostali wejscie do dnia (audyt + dwa mechanizmy)

Osobny watek dzis rano: Tomasz zauwazyl, ze **nie rozmawia z subagentami X i LinkedIn**. Audyt
(kod + sonda) pokazal przyczyne STRUKTURALNA, nie kosmetyczna: aktywny agent to JEDEN slot na
czat, trzymal go Sprzedawca (kampania), wiec X nie rozmawial od doby, LinkedIn od trzech dni
(9 i 8 sesji w calej historii). Wdrozone:
- **prefiks adresujacy** `x:` / `li:` / `cm:` / `sprzedaz:` - kieruje wiadomosc do wskazanego
  agenta BEZ zmiany aktywnego slotu (Sprzedawca zostaje w kampanii, content dostaje glos
  jednym slowem); dowod dzialania na zrzutach Tomasza,
- **meldunek dnia subagenta** w glownym czacie (20-21:30, wlasny badge, trzy rzeczy: co poszlo,
  co czeka, czego trzeba) - zamiast cichego raportu na bocie #2, ktory nie wybudzal.

Pelny audyt: docs/cm/AUDYT_SUBAGENCI_24072026.md.

## 3. Grafiki i metryki (przypomnienie z raportu porannego)

- **GRAFIKI: auto-obraz WYLACZONY** (feedback Tomasza powtorzony) - material dostaje SZCZEGOLOWY
  PROMPT do recznej roboty, zero auto-generowania. **To cofa P4** (auto_image X ON). Decyzja
  wlasciciela o jego marce wizualnej; zniesienie dopiero po dedykowanym Agencie Wizualnym.
- **METRYKI X:** kolektor dziala (raz na dobe), etykieta "wpisz recznie" myla i zostala
  poprawiona na prawde ("metryki wejda same przy dobowym zbiorze").

## Nowy kanon na przyszlosc: AP-308

Epizod re-slottera dal regule warta zapisania (docs/anti-patterns/AP-308): **masowa zmiana
zywych danych = deterministyczny dry-run PRZED apply.** Dry-run zlapal DWA bledy, ktore apply
wypuscilby na produkcje (rozproszenie serii; siatka 3/dzien zamiast 5, bo gniazda hardkodowane
poza oknem kanalu) - kosztem zera na produkcji. Skladniki reguly: wynik deterministyczny
(inaczej apply != dry), idempotencja jako test, nie hardkoduj tego co w configu, nie zakladaj
skali (sonda: 64 nie 15). To blizniak AP-307 z innej strony: tam kontrakt i jego konsumenci,
tu zapis i jego podglad.

## Stan techniczny

HEAD sb-work: b5c34e8 (czeka push + rebuild). Testy lokalne dodane dzis (wszystkie PASS, bez
bazy i sieci): grafiki-prompt 9, kadencja-sufit 11, reslot 20+ (grupowanie serii, kolejnosc
narracyjna, siatka z okna, gestosc, idempotencja), subagenci 26. Dokumentacja zaktualizowana
w tym samym rytmie (kolejka-publikacja, grafika, metryki, rozmowa-cm, SYSTEM_DATAFLOW,
AP-308).

## Otwarte u Ciebie (bez zmian)

1. Zapis `who_is_who` - kolumna i odczyt sa, droga zapisu czeka na Twoja decyzje.
2. Voice Bible v2.2 + Sekcja 21 - wsad po Twojej stronie (deploy 26/07); SQL na flage gotowy.
3. Migracja legacy tierow - odlozona post-Adamietz.
