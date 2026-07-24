# RAPORT DO MANAGERA - paczka #1, punkty 1, 2, 5, 7, 8 (nazwa pliku wg DoD paczki; praca 24/07 wieczorem)

## Jednym zdaniem

Paczka #1 jest zamknieta w 7 punktach na 8: kod i DDL 030 leza w repo, przetestowane lokalnie
40 przypadkami bez dotykania produkcji; otwarty zostaje pkt 4 (tiery), bo jego zakres wywala
45 zywych wierszy i to nie jest decyzja inzyniera.

## Stan wejsciowy (dowod, nie zalozenie)

Serwer stoi na `a50c927`. Sprawdzone bez pytania Tomasza i bez SSH: zywy stan gry z konektora
Lacznika zawiera etykiete `⚠️ BRAK nastepnego kroku`, ktora do kodu weszla dopiero w tym
commicie (`git log -S`). Metoda taniej diagnozy do zapamietania: wersje kontenera da sie ustalic
po STRINGU, ktory ten kontener wypisuje.

## Co zrobione

### pkt 2 - tozsamosc cross-platform bez wyszukiwarki (LinkedIn v3.2 + X v3.1)

Sekcja mowi czatowi: nie ustalasz tozsamosci wyszukiwarka, prosisz o ZRZUT profilu (bio + link
w bio), a werdykt liczysz z tego, co widac. Werdykt trzema stanami - **potwierdzona /
z zastrzezeniem / niepotwierdzona** - celowo w tej samej skali, co bramka tozsamosci Sprzedawcy.
Jedna rzecz nie moze miec w systemie dwoch jezykow.

Poszlo do OBU masterpromptow, nie tylko do LinkedIn (kanon parytetu). Sekcja niesie tez lekcje
z dowodem: `piapiasilva` = **Pia Silva**, szukamy po nazwisku i firmie, bo handel bywa zmieniany.

### pkt 8 - interpunkcja PL jako flaga

`compliance.pl_comma_flags`: deterministycznie, zero LLM, zero kosztu. Karta materialu dla marek
polskojezycznych (TNM/RDC) pokazuje do 3 miejsc z prawdopodobnie brakujacym przecinkiem przed
`ze / zeby / ktory / gdy / jesli / bo`. Liczone z PELNEJ tresci, nie z przycietego podgladu.

Najwazniejsza decyzja projektowa: heurystyka jest CELOWO ostrozna. Nie zglasza poczatku zdania,
istniejacego przecinka ani zbitek "mimo ze", "nawet jesli", "w ktorym". Flaga, ktora krzyczy przy
kazdej karcie, po tygodniu przestaje byc czytana - i wtedy nie chroni juz niczego.

### pkt 1 - eksport analityczny wraca do bazy

Nowy typ linii raportu pracy: `kpi_snapshot | RRRR-MM-DD | wyswietlenia=... | reakcje=... |
nowi_obserwujacy=... | okres=7d`. Parser bez LLM, aliasy PL i EN, liczby typu "1 234" i "1,2 tys.",
a wartosc nieczytelna NIE staje sie zerem - pole zostaje puste (zero w metrykach to klamstwo).
Nierozpoznane klucze siadaja w `raw`, wiec nic nie ginie po cichu.

OSOBNA TABELA `channel_kpi_snapshots`, nie dopisek do `channel_metrics_daily` (023): tamta ma
klucz (marka, kanal, DATA) i zna wylacznie serie DZIENNE z importu xlsx/API. Czat przepisuje
takze okresy zbiorcze (7d/28d/90d); suma tygodniowa wpisana w wiersz dzienny zafalszowalaby
istniejaca serie na zawsze.

Domkniete kolem: liczby wracaja do czatu sekcja **METRYKI KANALU** w stanie gry. Bez tego
byloby to pisanie do szuflady - czat co sesje pytalby Tomasza o to samo, co sam tam wpisal.

### pkt 5 - contacts.who_is_who (kolumna + odczyt; zapis do decyzji)

Kolumna JSONB z kontraktem role / influence_level / relationship_stage / source_of_data / notes.
Rozroznienie pilnowane w dokumentacji: `handles` to tozsamosc per KANAL (kanon WHO IS WHO),
`who_is_who` to pozycja czlowieka w ORGANIZACJI klienta. Odczyt wpiety w `crm.relation_context`,
czyli rola i wplyw pojawiaja sie w naglowku propozycji i gotowca - tam, gdzie sie pisze
do czlowieka, a nie w osobnym raporcie, ktory trzeba pamietac otworzyc.

**Otwarte i wymaga Twojej decyzji: kto to ZAPISUJE.** Dzis tylko SQL Tomasza z sesji Sales
Managera L1. Propozycja BE: linia `kto_jest_kim | osoba | rola=... | wplyw=... | zrodlo=...`
w raporcie pracy, tym samym deterministycznym parserem co `kpi_snapshot`. Kolumna bez drogi
zapisu zostanie pusta, a pusta kolumna klamie tak samo jak jej brak.

### pkt 7 - fail-closed przed wykluczeniem z lejka

Regula stoi na `engagement_log`, nie na nowej kolumnie `contacts.dm_history`. Powod jest
kanoniczny: duplikat historii rozjezdza sie z logiem w tygodnie, a potem nie wiadomo, ktora
kopia klamie.

Mechanizm: przy proponowaniu tieru wykluczajacego z lejka (Competitor, out_of_icp) system liczy
historie rozmow. Jest historia - **rekomendacja znika**, a karta niesie dowod: ile wpisow DM,
kiedy ostatni, jakie stadium relacji.

Efekt uboczny jest wazniejszy niz sama karta i celowy: `decisions.ask` bez rekomendacji NIE
podejmuje decyzji sam nawet w trybie semi_autonomous. A `crm_tier` jest na semi od 22/07
(decyzja #90). Bez tej poprawki system mogl SAM wykluczyc z lejka czlowieka, z ktorym Tomasz
juz rozmawial - i tylko poinformowac go o tym po fakcie.

Wpiete w OBA miejsca, ktore proponuja tier (karta z raportu pracy i karta ze zrzutu profilu) -
AP-307 mowi, ze zmiana kontraktu obowiazuje kazdego zywego konsumenta w tym samym buildzie.
Sprawdzone: to sa jedyne dwa takie miejsca, a icp_tier zapisuje sie w jednym.

## Dowody

`python cm-agent/tests/test_paczka1.py` - **40 przypadkow, wszystkie PASS**, stdlib only,
bez bazy i bez serwera (wzorzec test_x_collector.py):
- interpunkcja: 6 pozytywnych, 10 negatywnych (w tym tekst angielski i zbitki), 3 brzegowe,
- parser KPI: aliasy, separatory tysiecy, okres domyslny, brak pola = None, nieczytelna liczba
  = pole puste, komentarz w tym samym raporcie dalej parsowany,
- fail-closed: 7 przypadkow (tier wykluczajacy z historia i bez, tier neutralny, stadium offer
  bez wpisow DM, brak kontaktu).

`python -m py_compile` na piatce zmienionych modulow - OK.

## Czego NIE zrobilem i dlaczego

- **pkt 4 (piaty tier "Inne")** - twarde sciecie do 5 wartosci wywala 45 zywych wierszy
  (Watch 37, Premium 7, Mid 1). Rekomendacja bez zmian: DODAC 'Inne', legacy zostawic jako
  historie. To decyzja Tomasza, nie inzyniera - pytanie idzie do niego guzikami.
- **Zapis who_is_who** - patrz wyzej, czeka na Twoja decyzje o zrodle.
- **Wdrozenie** - DDL 030 i rebuild wykonuje Tomasz. Do tego czasu sekcja METRYKI KANALU jest
  po prostu cicha (brak tabeli = pusta lista, nie awaria), a reszta zmian nie rusza produkcji.

## Nastepny krok

push -> `psql 030` PRZED rebuildem -> rebuild cm-agent -> tap-testy: (a) linia kpi_snapshot
przez narzedzie Lacznika, (b) karta TNM/RDC z flaga interpunkcji, (c) karta tieru dla osoby
z historia DM (ma przyjsc BEZ gwiazdki rekomendacji).
