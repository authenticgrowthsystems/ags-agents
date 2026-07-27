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
