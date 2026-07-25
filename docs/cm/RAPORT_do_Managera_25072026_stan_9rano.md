# RAPORT DO MANAGERA - stan na 25/07/2026, 9:00 rano

Tomasz poprosil o raport stanu. Ponizej: co zrobione od wczoraj wieczorem, co Tomasz zglosil
dzis rano, i JEDNO cofniecie Twojej decyzji, ktore musze Ci zglosic wprost.

## Zrobione i WDROZONE (24/07 wieczor - 25/07 rano)

Wszystko na sb-work, serwer potwierdzony na commicie po czasie kontenera (nie zalozenie):

1. **Paczka #1 - 8/8 zamknieta**, DDL 030 i 031 na produkcji. Pierwsze kontakty z tierem 'Inne'
   juz w bazie (dowod: stan gry X pokazuje DiogosDiarly90 i Jason jako 'Inne').
2. **Twoj mini-brief #1.2 (P1-P5) wykonany.** BONUS okazal sie wiekszy: ucinanie glosu zylo
   w DZIEWIECIU miejscach, nie jednym. To tlumaczy, czemu kanon v2.1 z 06/07 byl lamany mimo
   obowiazywania - model nie widzial sekcji 4.x, bo szly do niego pierwsze 1200-3000 znakow
   Voice Bible (naglowek pliku). Teraz jeden wspolny blok, caly glos, prompt-cache.
3. **Dlug techniczny 24/07 zamkniety:** zrodlo `site` w Researcherze (kaskada czyta wreszcie
   strone podmiotu - firecrawl wolal endpoint prac naukowych, stad arXiv w researchu o klubie
   tanecznym), adres prospekta bierze domene nie archiwum autora, osoba decyzyjna odrozniana
   od instruktora, Sprzedawca widzi zrzuty ekranu.
4. **Straznik meta-naglowka** (post wyszedl z "# X Adaptation" w tresci - zlapane na zywo).
5. **Cichy except = blad projektowy** (Twoje P5): 17 miejsc uglosnionych, kanon w AP-306.
6. **Audyt subagentow + dwa mechanizmy wejscia do rozmowy.** Sonda pokazala: X nie rozmawial
   od doby, LinkedIn od trzech dni, bo aktywny agent to JEDEN slot i trzymal go Sprzedawca.
   Wdrozone: prefiks `x:`/`li:`/`cm:` (kieruje wiadomosc BEZ zmiany slotu) + meldunek dnia
   subagenta w glownym czacie. Dowod dzialania na zrzutach Tomasza z 8:44 rano.

## Zgloszenia Tomasza z dzis rano (25/07) - stan obslugi

**1. "Po co dzis na X tyle tweetow i jaka spojnosc? To rola CM."**
Diagnoza z kodu: kadencja X to `posts_per_day=3-5` (kanon 11d), ale SERIA z jednego materialu
rozbija sie na osobne sloty NIEZALEZNIE od planera (`channels.stage_variant` wola `next_slot`
prefer_today per czesc). Gdy material-seria trafi na dzien z 3 postami, dokłada 4-5 -> 7-8.
Spojnosc tematyczna JEST (wszystko o architekturze agentow), ale LICZBA wymyka sie CM.
Tomasz ma racje. **Rekomendacja: seria respektuje dzienny limit kadencji** (nadmiar przechodzi
na kolejny dzien). To zmiana w slots/stage_variant, dotyka rdzenia publikacji - pytam Tomasza
guzikami, zanim ruszam (liczba postow dziennie to decyzja wlasciciela, nie inzyniera).

**2. "X nie pobiera metryk, a powinien sam."**
Diagnoza: kolektor X DZIALA (starsze posty maja metryki - 22/07: 66, 75). Zbiera raz na dobe
UTC, wiec swiezy post czeka na cykl. Problem byl w ETYKIECIE: mowila "wpisz w rozmowie
z subagentem" i czytalo sie to jako obowiazek recznego wpisu. NAPRAWIONE: etykieta mowi teraz
prawde ("metryki wejda same przy dobowym zbiorze"). Dodana sonda diagnostyczna, gdyby kolektor
faktycznie stanal (docs/komponenty/metryki.md).

**3. "Grafiki generowane sa slabe - chce robic recznie, dostawac tylko prompty."**
To jest COFNIECIE Twojego P4 (auto_image X ON, ktore wdrozylem wczoraj). Zglaszam wprost, bo
to Twoja decyzja sprzed doby. **Zrobilem po mysli Tomasza** - to feedback wlasciciela o jego
wlasnej marce wizualnej, w tej sprawie jego zdanie bije decyzje z paczki. Auto-generowanie
obrazu wylaczone w OBU torach (przed karta + dispatch); zamiast obrazu material dostaje
SZCZEGOLOWY PROMPT na karcie do recznego wygenerowania. Guzik 🎨 Generuj na zadanie zostaje.
Zapisane jako kanon trwaly. Zniesienie: dopiero dedykowany Agent Wizualny (backlog).

## Co jest OTWARTE u Ciebie (bez zmian od wczoraj)

1. **Zapis `who_is_who`** - kolumna i odczyt gotowe, drogi zapisu nie ma. Propozycja BE: linia
   `kto_jest_kim` w raporcie pracy (ten sam parser co kpi_snapshot). Czeka na Twoja decyzje.
2. **Voice Bible v2.2 + Sekcja 21** - wsad po Twojej stronie (deploy 26/07). Fix ucinania glosu
   ZROBIONY w kodzie (to byl bug loadera, nie tresci); SQL na nazwe flagi gotowy.
3. **Migracja legacy tierow** - swiadomie odlozona post-Adamietz (Twoja decyzja P1).

## Jedna rzecz, ktora chce podniesc do rangi kanonu

Wczoraj i dzis powtorzyl sie ten sam wzorzec: **poprawka w jednym miejscu, gdy ta sama wada
zyje w wielu** (glos ucinany 9x, tier przepisany 4x, cichy except 19x, auto-grafika w 2 torach).
AP-307 mowi o konsumentach kontraktu; to jego blizniak. Proponuje regule: zanim uznasz poprawke
za zrobiona, policz GREPEM, ile miejsc ma te sama wade. Jesli uznasz za osobny numer AP - nadaj.

## Dowody

Testy lokalne dodane od wczoraj (wszystkie PASS, stdlib, bez bazy i sieci): site 26, paczka1 45,
meta-naglowek 29, sales-prospekt 13, subagenci 26, grafiki-prompt 9, dym importow 21.
Serwer na commicie zweryfikowanym po czasie kontenera; kolejka X po sprzataniu bez meta-naglowkow.
