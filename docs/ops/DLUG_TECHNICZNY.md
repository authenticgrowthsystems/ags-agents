# Dlug techniczny AGS (lista zywa)

Rzeczy ZNANE i SWIADOMIE odlozone. Powod istnienia tego pliku (polecenie Managera 26/07):
dlug zapisany z data nie zostaje odkryty powtornie za miesiac jako "nowy blad".

Zasada wpisu: co jest nie tak, gdzie to siedzi (plik:linia), czym grozi, kiedy to bolalo
albo kiedy zabolisz. Wpis znika z listy dopiero razem z poprawka.

---

## D-001 [ZAMKNIETE 02/08/2026]: Regula weekendowa pilnowana tylko w jednym z czterech miejsc

**NAPRAWIONE.** Powstala JEDNA funkcja `slots.day_ok(channels, day, is_article)` i wolaja ja
teraz wszystkie cztery trasy zapisujace slot:

| trasa | jak bylo | jak jest |
|---|---|---|
| `slots.next_slot` | jedyna, ktora znala regule | bez zmian (`_li_ok`) |
| planer | slot od modelu, walidowany TYLKO jako ISO | odrzuca pozycje z `[dzien]` w powodzie |
| guzik "koniec kolejki" | `MAX(slot)+1 dzien` - z PIATKU robil SOBOTE | przesuwa do najblizszego dozwolonego dnia |
| re-slotter | siatka gniazd bez sprawdzenia dnia | pomija dni zakazane |

**Szczegol, ktory latwo bylo przeoczyc:** trasy trzymaja kanal w ROZNYCH ksztaltach - lista
(planer, karta) albo napis (re-slotter). Gdyby `day_ok` przyjmowalo tylko liste, re-slotter
cicho ominalby guard, mimo ze "wywolanie jest". Funkcja przyjmuje oba ksztalty, a test to pilnuje.

Test: `cm-agent/tests/test_regula_dnia.py` (19 asercji), w tym asercja **AP-309** sprawdzajaca
w ZRODLE, ze kazda z czterech tras faktycznie o regule pyta - zeby nastepna nowa trasa nie
powtorzyla tego dlugu po cichu.

Ponizej oryginalny opis, dla historii.


**Zapisany 26/07/2026** (decyzja Managera: nie naprawiac teraz, zapisac).

Sobota jest twardo wycieta dla LinkedIna w `cm-agent/app/slots.py:109-115` (`_li_ok`), ale
`_li_ok` wolane jest WYLACZNIE z `next_slot`. Trzy pozostale drogi zapisujace slot dnia
tygodnia nie znaja:

- **planer** (`planner.py:312-325`) - slot przychodzi od modelu, walidowany tylko jako ISO,
  chroniony samym promptem,
- **guzik "koniec kolejki"** w kartach (`matreview.py:377-390`, `720-722`) - bierze
  `MAX(slot)+1 dzien`, wiec **z piatku robi sobote jednym tapnieciem**,
- **re-slotter** (`reslot.py:116-131`) - kanal z argv.

Zaden straznik nizej ani Scheduler n8n dnia juz nie sprawdza
(`grep getDay|weekday|dayOfWeek n8n-workflows/` = zero trafien).

Dodatkowo `slots.py:135` robi `continue` na CALY dzien, wiec sobotni zakaz LinkedIna zabiera
slot takze kanalowi X przy materiale wielokanalowym.

**Czym grozi:** post LinkedIn w sobote wbrew kanonowi 19/07, bez zadnego ostrzezenia.
**Docelowo:** jedna funkcja `slots.day_ok(channel, day, is_article)` wolana z czterech miejsc
(wzorzec: straznik meta-naglowka w `channels.py:60-64`).

---

## D-002 [ZAMKNIETE 02/08/2026]: Test kadencji pada po zamknieciu okna publikacji

**NAPRAWIONE.** `slots.py` i `reslot.py` dostaly jedno posrednictwo `_teraz()`, ktore w produkcji
zwraca dokladnie to co wczesniej (`datetime.now(WARSAW)`), a w tescie jest podmieniane na staly
moment (sroda 14:00 dla kadencji, sroda 09:00 dla re-slottera). Oba testy nie odwoluja sie juz
**w ogole** do zegara systemowego - zero wystapien `now()`. Zestaw: **18/18 zielonych**,
po raz pierwszy. Ponizej oryginalny opis, dla historii.



**Zapisany 26/07/2026** (zlapany przy uruchamianiu calego zestawu o 23:20).

`cm-agent/tests/test_kadencja_sufit.py:83` sprawdza "2 z 5 zajete dzis -> slot jeszcze dzis",
liczac `datetime.now()`. Okno kanalu X to 13:00-22:00, wiec **po 22:00 test pada zawsze**,
niezaleznie od kodu. Zweryfikowane: pada identycznie na czystym HEAD.

**Czym grozi:** wieczorna sesja widzi czerwony test i traci czas na szukanie regresji, ktorej
nie ma. Albo, gorzej, przyzwyczaja sie do czerwonego i przeoczy prawdziwa.
**Docelowo:** wstrzykiwac "teraz" do `next_slot` w tescie zamiast polegac na zegarze.

**DRUGI PLIK, ta sama wada (dopisane 27/07):** `cm-agent/tests/test_reslot.py`, przypadek
"#4 w przyszlosci, ludzka minuta, w oknie". Pada okolo poludnia i po poludniu, bo siatka gniazd
liczona z okna 13:00-22:00 czesciowo wypada juz w przeszlosci. Zweryfikowane stashem: pada
identycznie na czystym HEAD. Czyli wada dotyka DWOCH plikow testowych (AP-309) i obie naprawy
sa te sama poprawka: wstrzykniecie zegara zamiast `datetime.now()`.

---

## D-003 [ZAMKNIETE 02/08/2026]: Kolumny kontaktowe lejka bez drogi zapisu przez czlowieka

**NAPRAWIONE, oba objawy.**

1. **Etykieta klamala.** `pipeline_text` POBIERALO `contact_person`, ale go NIE POKAZYWALO,
   wiec prospekt z zapisana osoba dostawal "⚠️ brak kontaktu". Ta sama rodzina co AP-312
   i "BRAK nastepnego kroku" z 27/07: dane byly poprawne, klamal WIDOK. Osoba wyswietla sie
   teraz PIERWSZA - dojscie przez czlowieka jest cenniejsze niz numer ze strony.
2. **Nie bylo recznej drogi zapisu.** `pipeline_add` i `pipeline_move` dostaly pola
   `contact_person` / `contact_email` / `contact_phone`. Opis pola mowi wprost, ze mieszka tam
   takze DOJSCIE ("przez Piotra Hamryszaka") - to byl konkretny przypadek, ktory ten dlug zrodzil.

**Wpis byl PRZETERMINOWANY w czesci "dzis uspiona":** notatka z 26/07 mowila, ze `contact_person`
jest NULL we wszystkich dwunastu wierszach. Odczyt z 02/08 pokazal **33 wiersze z wypelniona
osoba** na 133 - czyli drugi objaw byl juz ZYWY i falszywe "brak kontaktu" zdazylo sie pokazac.

Test: `cm-agent/tests/test_kontakt_lejka.py` (14 asercji). Zestaw 21/21.

Ponizej oryginalny opis, dla historii.


**Zapisany 26/07/2026** (sekcja 4.7 diagnozy; wada realna, dzis USPIONA).

`_zapisz_kontakt` (`sales.py:938-955`) wolany jest wylacznie z automatow, a schematy
`pipeline_add` i `pipeline_move` nie maja pol kontaktowych. Nie da sie recznie dopisac
telefonu, maila ani osoby do wiersza lejka. Do tego `pipeline_text` (`sales.py:142-143`)
nie czyta `contact_person`, wiec "brak kontaktu" zapali sie takze przy wypelnionej osobie.

**Dlaczego dzis nie boli:** sonda 26/07 pokazala `contact_person` NULL we wszystkich
dwunastu wierszach lejka, wiec drugi objaw jeszcze nie wystapil.
**Czym grozi:** adamietz.pl ma ciepla sciezke przez Piotra Hamryszaka i nie ma jej gdzie
zapisac - wiedza o dojsciu zyje poza systemem.

**Aktualizacja 31/07:** teczka prospekta domyka POLOWE tego dlugu - `zapisz_tekst` daje czlowiekowi
droge zapisu tresci wysylki oraz nastepnego kroku z terminem (`sales_pipeline.next_step`, DDL 036).
Pol kontaktowych (osoba, telefon, mail przy wierszu lejka) nadal **nie da sie** wypelnic recznie,
wiec dojscie przez Piotra dalej nie ma swojego miejsca. Dlug zostaje otwarty w tej czesci.

---

## D-004: Materialy przygotowane poza baza sa dla agenta niewidzialne

**Zapisany 27/07/2026** (Manager: zapisac jako swiadomy dlug, nie budowac przed pierwsza sprzedaza).

Agent Sprzedazy zaproponowal Tomaszowi przygotowanie gotowca i researchu pod Adamietza na 28/07,
podczas gdy **material dla Piotra istnieje od 25/07**: notatka dla posrednika plus jednostronicowka
do przekazania decydentowi, oparta na pelnym raporcie wywiadowczym. Agent nie mial jak wiedziec -
plik lezy w `docs/research/prospekci/` POZA gitem (celowo, origin jest publiczny) i poza baza.

**Czym grozi:** agent proponuje robote, ktora jest zrobiona, i to akurat przy najwiekszym dealu
w lejku. Kosztuje zaufanie do agenta bardziej niz przeoczenie, bo wyglada na niekompetencje.

**Doraznie (zrobione):** notatka w `sales_pipeline.notes` prospekta plus regula w prompcie
Sprzedawcy: przeczytaj notatki, ZANIM zaproponujesz przygotowanie czegokolwiek.

**Docelowo:** minimalny rejestr materialow per prospekt (co powstalo, gdzie lezy, jaki status).
Warunek wejscia: po pierwszej platnej sprzedazy, zgodnie z kanonem "nie budujemy systemow przed
pierwsza sprzedaza".

## D-006 [ZAMKNIETE 02/08/2026]: Status `dispatching` ma nazwe, ktora obiecuje co innego niz znaczy

**NAPRAWIONA CZESC WIDOKOWA, bez dotykania kontraktu.** Dwie zmiany w `matreview.py`:

1. Etykieta "W PUBLIKACJI" -> **"ROZESLANY DO KOLEJKI"**. Mowi, CO SIE STALO, a nie co sie
   wlasnie dzieje - czyli nie obiecuje juz sekund przy stanie, ktory trwa dniami.
2. Nowy `_stan_rozsylki()` dokleja do karty **ile wierszy czeka z ilu i na kiedy** (najblizszy
   ORAZ ostatni termin - z ostatniego wiadomo, jak dlugo stan jeszcze potrwa). Jedno zapytanie
   na material, nie N+1.

**Sedno:** zgloszenie brzmialo "nie da sie powiedziec, czy wysyla, czy zawisl". Sama nazwa tego
nie rozstrzygnie i rozstrzygnac NIE MOZE. Rozstrzyga liczba wierszy i ich terminy - i teraz sa
widoczne. Przy okazji powstal jedyny przypadek, ktory naprawde wyglada na zawieszenie i da sie
go odroznic: **zero oczekujacych wierszy przy materiale nadal w tym stanie** - karta ostrzega
wprost. Test: `cm-agent/tests/test_stan_rozsylki.py` (13 asercji).

**NIE ZAMYKA D-008** (przemianowanie samej WARTOSCI statusu). To osobna sprawa i osobne okno -
uzasadnienie ponizej w D-008. Zmiana etykiety wyswietlanej NIE dotyka kontraktu miedzy warstwami.

Ponizej oryginalny opis, dla historii.


**Zapisany 27/07/2026** (zgloszenie Managera; polecenie: zapisac jako dlug, nie naprawiac dzis).

**Zgloszenie brzmialo:** "status dispatching nie ma limitu czasu, post z 13:30 wisial ponad pol
godziny i ani system, ani CM nie potrafili powiedziec, czy jest w trakcie wysylki, czy zawisl".
Podejrzana przyczyna: tekst ~2000 znakow odrzucony przez API jako za dlugi.

**ODCZYT PRZED NAPRAWA (27/07, cztery zapytania read-only) OBALIL OBIE HIPOTEZY:**

1. **Zaden post nie wisi.** Siedem materialow w `dispatching`, u kazdego liczba wierszy
   "po terminie ponad 2h" wynosi ZERO. Wszystkie oczekujace wiersze maja sloty w przyszlosci
   (od 27/07 21:02 do 04/08 14:15).
2. **Limit czasu ISTNIEJE:** `worker._dispatch_timeout_alert`, prog `config.DISPATCH_TIMEOUT_H = 2`.
   Liczy od SLOTU WIERSZA, nie od dispatchu - swiadomie, bo poprzednia wersja alarmowala o 15:15
   o postach ze slotami na 20:10, a falszywe alarmy ucza ignorowania prawdziwych (komentarz A6,
   21/07). Nie alarmowal, bo nie mial o czym.
3. **Hipoteza o dlugosci bez poparcia.** X opublikowal przez 10 dni 28 postow, najdluzszy
   556 znakow; najdluzszy `scheduled` w kolejce ma 563. LinkedIn publikowal 1549-2016 znakow,
   w kolejce ma 2392-2621 przy limicie platformy 3000. Zaden wiersz nie przekracza limitu swojej
   platformy. Nie ma tez wiersza ze slotem 13:30.

**PRAWDZIWA WADA, ktora zgloszenie odslonilo** (od 29/07 ma wlasny anty-wzorzec: **AP-312**,
a sama nazwa idzie do przemianowania jako **D-008**):

`dispatching` brzmi jak stan PRZELOTNY ("wysylam"), a znaczy "rozeslane do kolejki, czekam az
WSZYSTKIE wiersze serii osiagna stan terminalny" - czyli stan, ktory normalnie trwa DNI. Szesc
materialow siedzi w nim 51 godzin i jest to poprawne: re-slotter rozrzucil serie na dni, wiec
seria konczaca sie 4 sierpnia bedzie w `dispatching` przez dziewiec dni.

Czlowiek czyta nazwe i spodziewa sie sekund. System ma na mysli tydzien. **To jest AP-311 od
strony NAZEWNICTWA:** nie "stan, ktorego nikt nie potrafi zweryfikowac", tylko stan, ktorego
nazwa wprowadza w blad. Manager wyciagnal rozsadny wniosek z mylacej etykiety - dokladnie tak,
jak Agent Sprzedazy przy "BRAK nastepnego kroku".

**CO ZOSTAJE DO ZROBIENIA (druga polowa zgloszenia, trafna w stu procentach):**

Nigdzie nie widac, OD KIEDY material jest w `dispatching` i NA CO czeka. Poprawka jest tania:
przy kazdej pozycji w tym stanie pokazac liczbe wierszy oczekujacych i najblizszy slot -
"dispatching, czeka 5 wierszy, najblizszy slot 28/07 09:00". Wtedy roznica miedzy "wysylam od
dwoch minut" a "wisi od trzydziestu" jest widoczna bez patrzenia na zegarek.

Rozwazyc takze przemianowanie stanu na cos, co nie klamie ("w kolejce", "rozeslane"), ale to
zmiana kontraktu miedzy tabelami i n8n, wiec osobna decyzja.

**Czym grozi, jesli zostawimy:** przy czterech publikacjach dziennie na dwoch kanalach czlowiek
bedzie regularnie pytal "czy to wisi", a odpowiedz bedzie za kazdym razem wymagala sondy do bazy.
Prawdziwy zwis utonie kiedys w tych falszywych alarmach.

## D-008: Status `dispatching` do przemianowania

**Zapisany 29/07/2026** (decyzja Managera: "nie dzis, ale dopisz do listy z data").
Bezposrednia konsekwencja ustanowienia **AP-312**.

`content_items.dispatching` brzmi jak stan PRZELOTNY ("wysylam"), a znaczy "rozeslane do kolejki,
czekam az WSZYSTKIE wiersze serii osiagna stan terminalny" - stan, ktory normalnie trwa DNI.
Manager zglosil 27/07 zawieszony post; odczyt pokazal siedem materialow w tym stanie, wszystkie
zdrowe, najstarszy 51 godzin i poprawnie, bo jego sloty siegaly 4 sierpnia.

Czlowiek czyta nazwe i spodziewa sie sekund. System ma na mysli tydzien.

**Kandydaci na nazwe:** `w_kolejce`, `rozeslane`, `czeka_na_sloty`. Ostatni jest najdluzszy
i najuczciwszy - mowi doslownie, na co stan czeka.

**Dlaczego nie dzis:** to zmiana KONTRAKTU miedzy trzema warstwami naraz. Wartosc wystepuje
w `content_items.status`, w filtrach Pythona (`worker.reconcile_publications` pyta
`WHERE status='dispatching'`, `slots.assign_if_needed` i dwie trasy `conversation` maja ja
w liscie `status IN (...)`) oraz w SQL wezlow n8n. Przemianowanie w polowie zostawi system,
ktory czesciowo szuka starej wartosci, a czesciowo nowej - i to bedzie gorsze niz mylaca nazwa.

**Warunek wykonania:** osobna decyzja, osobne okno, komplet grepem PRZED zmiana (AP-309),
oraz migracja danych i PUT do n8n z rytualem backup / PUT / deactivate+activate.

**Powiazane:** D-006 (widok nie pokazuje, od kiedy material wisi i na co czeka) - te dwie
naprawy warto zrobic razem, bo obie dotykaja tego samego stanu i tej samej niejasnosci.

## D-007: Operacja hurtowa nie zostawia sladu czytelnego dla DRUGIEGO agenta

**Zapisany 29/07/2026** (zgloszenie Managera, szosta odslona AP-311).

Wycofalem 29/07 dwadziescia jeden materialow X (99 wierszy) ustawiajac im `status='rejected'`.
Content Manager zapytal, **po czym ma je rozpoznac** - i mial racje, bo bez tego zgaduje.

**Problem nie jest w tym, ze danych brakuje. Jest w tym, ze sa nieodroznialne.** Ja wiem, co
wycofalem, bo sam to robilem. CM patrzy na te sama baze i widzi materialy w statusie `rejected`
- **te same, co odrzucone przy przegladzie kart miesiac temu**. Sprawdzone: zapytanie
"platforma X, status rejected, wiecej niz jeden wiersz" zwraca **26** materialow, z czego
dzisiejszych jest **21**. Piec to stare odrzucenia bez zwiazku z operacja.

Doraznie ratuje to `updated_at::date`, ale to jest proteza: dziala tylko dopoki nikt inny nie
dotknie tych wierszy tego samego dnia i tylko dopoki pamietamy date operacji.

**Czym grozi:** kazda operacja hurtowa (sprzatanie gotowcow 27/07, import listy 27/07,
wycofanie serii 29/07) jest dla pozostalych agentow niewidzialna jako operacja. Widza SKUTEK,
nie widza PRZYCZYNY ani ZAKRESU. Przy trzech agentach czytajacych te sama baze to jest
mnozenie sie nieporozumien, a nie brak wygody.

**Docelowo (rozszerzenie sladu audytowego z DDL 035):** slad ma obejmowac nie tylko KTO ustawil
slot, ale takze **kto zmienil status i w ramach jakiej operacji**. Ksztalt do rozstrzygniecia:
kolumna `status_source` symetryczna do `slot_source`, albo etykieta operacji (np.
`op='wycofanie-serii-29072026'`) pozwalajaca wyciac dokladny zbior jednym warunkiem.

Manager 29/07: *"Ty wiesz, co wycofales, bo sam to robiles. CM patrzy na te sama baze i nie
widzi roznicy miedzy materialem wycofanym a odrzuconym przy przegladzie miesiac temu."*

## D-005: Karty decyzji wygaszone PRZED 27/07 zostaja klikalne

**Zapisany 27/07/2026.**

Do commita `f4e88e1` klawiature z karty zdejmowal wylacznie `decisions.handle` po odpowiedzi
guzikiem. Bramki wygaszone skryptem albo recznym SQL zostawialy w Telegramie karte z zywo
wygladajacymi guzikami. Tomasz tapnal taka 27/07 i dostal "Decyzja #161 juz rozstrzygnieta",
majac w czacie siedem prawie identycznych kart o tym samym prospekcie.

Poprawka dziala od `f4e88e1` w PRZOD. **Karty wygaszone wczesniej (m.in. #152-156, #161) zostaja
martwe i klikalne** - nie mamy juz ich identyfikatorow w reku w momencie wygaszania.

**Czym grozi:** kolejne tapniecie w stara karte i komunikat "juz rozstrzygnieta". Nieszkodliwe,
mylace. Znikna z pola widzenia same, gdy czat sie przewinie.

---

## D-009 [ZAMKNIETE 02/08/2026]: Gotowiec mailowy w kanale `Other`, tekst z teczki w `Email`

**NAPRAWIONE, commit ea13447 + migracja przy zatrzymanym cm-agencie.** Slownik `email -> Email`
i dziewiec istniejacych wierszy w JEDNYM oknie wdrozeniowym. Okno usuniete przez zatrzymanie
kontenera (baza stoi w innym kontenerze niz pisarz), nie przez wybor mniejszego zla.
Wyszlo przy okazji: `channel` outreachu nie byl walidowany - dolozona bramka. Ponizej oryginal.


**Zapisany 31/07/2026** (stan zastany, zauwazony przy budowie teczki prospekta).

`sales.py:802` mapuje kanaly gotowcow tak: `_ENG_CHANNEL = {"email": "Other", "linkedin_dm":
"LinkedIn", "x_dm": "X"}`. Wartosc `'Email'` istnieje w ograniczeniu `engagement_log` od DDL 001,
ale tor gotowcow z niej nie korzysta. `teczka.zapisz` zapisuje maile poprawnie jako `'Email'`,
wiec od 31/07 ten sam kanal ma w ksiedze **dwie rozne etykiety** zaleznie od tego, kto pisal.

**Dlaczego nie poprawilem od reki:** `_ENG_CHANNEL` jest KLUCZEM w `_open_outreach_rows`, ktore
domyka poprzednie gotowce w tym samym kanale. Podmiana wartosci rozjechalaby dopasowanie
z wierszami juz lezacymi w bazie i zywe gotowce przestalyby sie unieważniac - to ta sama wada,
ktora 24/07 zrobila StandART siedem wierszy i piec bramek. Poprawka wymaga migracji istniejacych
wierszy razem ze zmiana slownika, w jednym kroku.

**Czym grozi:** nie rozbija niczego dzisiaj (teczka laczy wpisy po `pipeline_id`, nie po kanale),
ale **kazde liczenie wysylki per kanal bedzie klamac** - maile rozpadna sie na dwie kupki.

---

## D-010: `contacts` ma TRZY kolumny na stan tej samej osoby

**Zapisany 01/08/2026** (polecenie Tomasza: nie ruszac, zgłosic po moscie).

- `relationship_stage` varchar(20) NOT NULL, CHECK na 7 wartosci - zywa, wypelniona zawsze
  (cold 121, commented 69, dm 4).
- `status` varchar(50) NOT NULL, CHECK na 7 INNYCH wartosci (Cold/Warm/Hot/Customer/...).
- `pipeline_stage` **text, BEZ ograniczenia, wypelniony w 45 wierszach** - pozostalosc,
  ktorej nikt nie pilnuje i nic nie waliduje.

**Czym grozi:** dwa pierwsze da sie obronic (relacja kontra temperatura), trzeci jest czystym
dlugiem - tekst bez slownika, ktory przy pierwszym odczycie przez agenta zostanie wzięty za
zrodlo prawdy o etapie. To AP-312 czekajace na wywolanie.

---

## D-011 [ZAMKNIETE 02/08/2026 - NIE BYLO WADY]: "61 sierot" w `engagement_log`

**Zapisany 01/08/2026 przeze mnie. Zamkniety 02/08 po odczycie, ktory obalil wlasna przeslanke.
Zero zmian w kodzie i w bazie - i to jest wlasciwy wynik tego zadania.**

### Co pokazal odczyt

1. **Wszystkie 61 wierszy ma PUSTE `author_display`.** Nie ma czego dopinac. Zero pasuje
   do `contacts`, zero do `sales_pipeline` - nie dlatego, ze nazwy sie roznia, tylko dlatego,
   ze nazwy NIE MA. Normalizacja ogonkow (AP-313), ktora zapisalem jako narzedzie naprawy,
   nie ma tu czego normalizowac.
2. **To nie sa osierocone interakcje, tylko zapisy WLASNEJ aktywnosci.** Probka tresci:
   `"test draft"`, `"Raw insights queue for X Agent v1.0"`, `"Opis: Obrazek przedstawia posty
   na LinkedIn"`, `"My AI agent said 'published.'"`. Opublikowane posty, analizy zrzutow ekranu,
   wewnetrzne znaczniki kolejki. Wszystkie 61 maja `status='logged'`, czyli "zapisuje fakt".
   **One nie maja drugiej strony - i nie powinny miec.**
3. **Zaden licznik ich nie widzi.** Oba zapytania zliczajace (`crm.py:137` i `crm.py:178,181`)
   sa zawezone `WHERE contact_id=...`, wiec wiersz bez kontaktu jest z nich wykluczony.
   W `n8n` tej tabeli nie czyta nic. Nie istnieje zadne globalne `COUNT(*)` bez zawezenia.

### Dlaczego to trafilo na liste dlugu

Zdanie "zajmuja miejsce w licznikach (348 wpisow)" bylo **moje** i bylo nieprawdziwe: 348 to
liczba z MOJEJ sondy, nie z zadnego widoku systemu. Zapisalem brak powiazania jako wade,
nie sprawdzajac, czy cokolwiek tego powiazania POTRZEBUJE.

**To jest AP-311 zastosowane na opak.** Anty-wzorzec mowi: brak danych nie jest faktem, dopoki
nie sprawdzisz, ze system moglby je pokazac. Symetrycznie: **obecnosc danych nie jest problemem,
dopoki nie sprawdzisz, ze cokolwiek je czyta.**

### Co z tego zostaje naprawde (drobne, nie dlug operacyjny)

Wiersze `x_post` i `linkedin_post` w `engagement_log` dubluja to, co ma wlasna tabele
`published_posts`. To zapach modelowania, nie usterka: nic sie przez to nie psuje, zaden odczyt
nie klamie. Odnotowane, zeby nie odkrywac tego trzeci raz.

---

## D-012: Nic nie mapuje marki na korzen katalogu

**Zapisany 01/08/2026** (wyszlo przy budowie mostu katalogi-baza).

`sales_pipeline.katalog` trzyma sciezke WZGLEDNA (`Klienci\Chwalinski`) i to jest poprawne -
korzen jest cecha maszyny, nie prospekta. Ale **korzen nie jest nigdzie zapisany**. Ustalenie
Tomasza brzmi "korzen wynika z brand_id", tyle ze:

- wszystkie 134 wiersze maja dzis `brand_id='AGS'`,
- katalogi tych czterech leza pod `C:\Claude-CoWork\TyNieMusisz`,
- czyli mapowanie marka -> korzen dalo by dzis ZLY wynik, gdyby ktos je napisal doslownie.

**Czym grozi:** dopoki sciezke sklada czlowiek, nic sie nie dzieje. Pierwsze narzedzie, ktore
zechce OTWORZYC plik z teczki, bedzie musialo ten korzen skads wziac - i zgadnie.
**Docelowo:** `brands.katalog_korzen` albo wpis w `brand_config`, wypelniony razem
z przejsciem kodu na wielomarkowosc (patrz D-013).

---

## D-013: Kod jest jednomarkowy - wielomarkowosc czeka na pierwsza sprzedaz

**Zapisany 01/08/2026 (decyzja Tomasza, wariant drugi).**

**107 miejsc w `cm-agent/app/` filtruje `brand_id='AGS'`, w tym 13 w samym `sales.py`.**
Przepiecie 24 polskich wierszy na marke TNM wypchneloby je z widoku lejka, ze straznika
terminow i z generowania gotowcow - po cichu, bo zapytanie bez wynikow nie jest bledem.

**Decyzja:** dane NIE sa przepinane. Powstaje ETYKIETA `sales_pipeline.marka_docelowa`
(DDL 038), ktorej **zaden kod nie czyta**, zeby przyszle przepiecie bylo jednym UPDATE-em,
a nie ponownym rozstrzyganiem 24 przypadkow z pamieci.

**Warunek wejscia buildu wielomarkowego:** PO pierwszej zamknietej sprzedazy, nie wczesniej.
Uzasadnienie Tomasza: *"Wielomarkowosc nie przybliza do pierwszej faktury, a przepiecie danych
bez gotowego kodu ja oddala"*.

---

## D-014 [ZAMKNIETE 02/08/2026]: `action_type` mowi co innego niz `channel` dla tego samego maila

**NAPRAWIONE. Przyczyna byla WSPOLNA z D-009:** para (action_type, channel) miala DWA zrodla -
kanal ze slownika, typ literalem w INSERT - wiec miala jak sie rozjechac i rozjechala sie
dwukrotnie. Od 02/08 para siedzi w jednym slowniku `_ENG_KANALY`, w tym samym ksztalcie co
`teczka._KANALY`. Migracja: `docs/ops/SQL_d014_action_type_02082026.sql`.

**Odczyt pokazal, ze to ETYKIETA, nie klucz** (inaczej niz przy D-009): jedyne zapytanie
filtrujace po `action_type` (crm.py:180) jest zawezone do `contact_id`, a wszystkie dziewiec
gotowcow ma je puste; w calej bazie zero wierszy pasuje do `action_type ILIKE %dm%`. Dlatego
zatrzymywanie kontenera NIE bylo tu potrzebne - powiedziane wprost, zamiast powtarzania
ciezszej procedury dla powagi. Ponizej oryginal.


**Zapisany 02/08/2026** (znaleziony przez adwersarzy przy naprawie D-009).

`sales.py` wstawia gotowca z literalem `action_type='other'` **dla kazdego kanalu**, podczas gdy
`teczka.py` mapuje maila na `action_type='email'`. Obie kolumny lezą w tej samej tabeli i sa
pokazywane na tej samej osi czasu w teczce prospekta.

**Dlaczego NIE naprawilem tego razem z D-009:** to druga kolumna, wiec druga migracja. Wciagniecie
jej do tego samego okna podwoiloby zakres zmiany, ktora dotyka klucza dopasowania gotowcow -
a wlasnie ten klucz jest miejscem, gdzie blad kosztuje najwiecej. Regula "slownik i migracja
w jednym kroku" nie znaczy "wszystkie slowniki naraz".

**Czym grozi:** dzis niczym operacyjnie - `action_type` nie filtruje zadnego zapytania w torze
outreachu. Ale kazdy przyszly raport typu "ile maili wyszlo" da inny wynik zaleznie od tego,
czy policzy po `channel` czy po `action_type`.

**Docelowo:** `action_type` z tego samego slownika co `channel` + migracja istniejacych wierszy,
w jednym kroku. Rozroznik ten sam, trzypasowy, co przy D-009.
