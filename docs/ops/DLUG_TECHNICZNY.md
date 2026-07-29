# Dlug techniczny AGS (lista zywa)

Rzeczy ZNANE i SWIADOMIE odlozone. Powod istnienia tego pliku (polecenie Managera 26/07):
dlug zapisany z data nie zostaje odkryty powtornie za miesiac jako "nowy blad".

Zasada wpisu: co jest nie tak, gdzie to siedzi (plik:linia), czym grozi, kiedy to bolalo
albo kiedy zabolisz. Wpis znika z listy dopiero razem z poprawka.

---

## D-001: Regula weekendowa pilnowana tylko w jednym z czterech miejsc

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

## D-002: Test kadencji pada po zamknieciu okna publikacji

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

## D-003: Kolumny kontaktowe lejka bez drogi zapisu przez czlowieka

**Zapisany 26/07/2026** (sekcja 4.7 diagnozy; wada realna, dzis USPIONA).

`_zapisz_kontakt` (`sales.py:938-955`) wolany jest wylacznie z automatow, a schematy
`pipeline_add` i `pipeline_move` nie maja pol kontaktowych. Nie da sie recznie dopisac
telefonu, maila ani osoby do wiersza lejka. Do tego `pipeline_text` (`sales.py:142-143`)
nie czyta `contact_person`, wiec "brak kontaktu" zapali sie takze przy wypelnionej osobie.

**Dlaczego dzis nie boli:** sonda 26/07 pokazala `contact_person` NULL we wszystkich
dwunastu wierszach lejka, wiec drugi objaw jeszcze nie wystapil.
**Czym grozi:** adamietz.pl ma ciepla sciezke przez Piotra Hamryszaka i nie ma jej gdzie
zapisac - wiedza o dojsciu zyje poza systemem.

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

## D-006: Status `dispatching` ma nazwe, ktora obiecuje co innego niz znaczy

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

**PRAWDZIWA WADA, ktora zgloszenie odslonilo:**

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
