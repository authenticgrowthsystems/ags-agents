# AP-311: Brak danych to nie fakt o swiecie, dopoki nie sprawdzisz, czy system mial jak je pokazac

**Ustanowiony 27/07/2026 (Manager AGS, po ustaleniu o dwunastu odrzuconych duplikatach).**
Blizniak AP-309 od strony DIAGNOZY: tam jedna wada w wielu miejscach, tu jeden brak wzięty
za wlasciwosc rzeczywistosci.

## Wzorzec

Widok systemu pokazuje pustke - "brak kontaktu", "zero wysylek", "nie ma tego w bazie" -
i ta pustka zostaje potraktowana jako FAKT, na ktorym buduje sie decyzje. Tymczasem pustka
w widoku ma dwie mozliwe przyczyny i tylko jedna z nich jest faktem o swiecie:

1. **Danych naprawde nie ma** (fakt o swiecie),
2. **Dane sa, ale system nie mial ich jak pokazac** - byly poza jego zasiegiem, w pliku,
   w innej kolumnie, odrzucone przez filtr albo nigdy nie zapisane, bo brakowalo drogi zapisu.

Roznica jest zasadnicza, bo w przypadku drugim decyzja podjeta "wobec danych" jest
**poprawna proceduralnie i falszywa merytorycznie**, a winny jest system, nie czlowiek.

## Dowod: trzy przypadki w jednym tygodniu

1. **Voice Bible (25/07).** Manager oczekiwal, ze nowa wersja pojdzie na `version=4`. Sonda
   pokazala, ze czworke zajela juz stara v2.2 z db/022. Stan w glowie kontra stan w bazie.
2. **StandART (26/07).** Pamiec projektu twierdzila: "gotowiec wyslany 24/07". Sonda: siedem
   wierszy `proposed`, ZERO `sent`. Nie wyszlo nic. Stan w glowie kontra stan w bazie.
3. **Dwanascie odrzuconych duplikatow (27/07).** Lejek pokazywal przy dziewieciu prospektach
   "⚠️ brak kontaktu", wiec uznano ich za nieobslugiwalnych i zapadla decyzja o zaparkowaniu.
   Mail i telefon kazdego z nich **lezaly w pliku na dysku Tomasza od 23/07**, a import
   wyrzucil je jako duplikaty, bo pytal wylacznie "czy nazwa jest juz w lejku", a nie
   "czy ten rekord wnosi cos, czego lejek nie ma".

We wszystkich trzech przypadkach czlowiek dzialal racjonalnie na tym, co widzial. We wszystkich
trzech to, co widzial, bylo niepelne z winy systemu.

## Granica z AP-312 (rozstrzygnieta przez Managera 29/07)

Ten anty-wzorzec dotyczy WYLACZNIE sytuacji, w ktorej **widok milczy o stanie, ktory baza zna**.
Przypadki, w ktorych dane BYLY, ale ich nazwa albo etykieta wprowadzala w blad, naleza do
**AP-312** i tam sa opisane. BE proponowal 29/07 zlaczenie obu w jeden szerszy wzorzec; Manager
je rozdzielil i mial racje - to sa dwie rozne diagnozy i dwie rozne naprawy.

Test rozstrzygajacy, gdy nie wiesz, ktory to przypadek: **czy dane w bazie byly?**
Nie byly, albo byly poza zasiegiem systemu - to AP-311. Byly i widok je pokazal, tylko pod nazwa,
ktora znaczy co innego - to AP-312.

## Why bad

- Decyzja wyglada na ugruntowana w danych, wiec nikt jej nie kwestionuje.
- Wina laduje na czlowieku ("zaniedbane prospekty"), a nalezy sie systemowi ("nigdy nie podal
  adresow"). To psuje nie tylko decyzje, ale i ocene wlasnej pracy.
- Pustka jest cicha: brakujaca kolumna nie rzuca wyjatku, odrzucony rekord nie zostawia sladu,
  a filtr, ktory cos wyciol, wyglada dokladnie jak filtr, ktory nie mial czego wyciac.

## Correct

1. **Zanim uznasz brak za fakt, zapytaj: czy system mial JAK to pokazac?** Konkretnie:
   czy istnieje droga zapisu? czy istnieje odczyt? czy jakis filtr mogl to wyciac po drodze?
   Trzy pytania, kilkanascie sekund.
2. **Odrzucone rekordy musza zostawiac slad.** Kazdy filtr, ktory cos usuwa ze zbioru, ma
   powiedziec ILE i DLACZEGO. Import mowi "duplikaty: 12" wlasnie po to - i to ta liczba
   pozwolila znalezc wade.
3. **Duplikat nie jest smieciem.** Rekord, ktory pokrywa sie kluczem, moze niesc pola, ktorych
   docelowy wiersz nie ma. Zanim odrzucisz, sprawdz, co wnosi.
4. **Kolumna bez drogi zapisu to kolumna martwa.** `contacts.who_is_who` istniala cztery dni
   z odczytem i bez wejscia - widok pokazywal pustke, ktora nie miala prawa sie zapelnic.
   Przy kazdym nowym polu: gdzie to sie WPISUJE, nie tylko gdzie sie czyta.
5. **Gdy stan w glowie rozjezdza sie ze stanem w bazie, wygrywa sonda.** Nie pamiec, nie
   dokumentacja, nie raport sprzed dwoch dni. Odczyt.


---

## AP-311 NA OPAK (ustanowione 02/08/2026, decyzja Managera)

**Obecnosc danych nie jest problemem, dopoki nie sprawdzisz, ze cokolwiek je czyta.**

Anty-wzorzec w pierwotnym brzmieniu chroni przed uznaniem BRAKU za fakt. Symetryczna pomylka
kosztuje tyle samo: uznanie OBECNOSCI za problem.

**Dowod (D-011, 02/08/2026).** Zapisalem w dlugu: "61 sierot w engagement_log - wiersze bez
kontaktu i bez prospekta, zajmuja miejsce w licznikach (348 wpisow), nie da sie ich przypisac
do zadnej sprawy". Brzmialo jak wada. Odczyt pokazal trzy rzeczy:

1. Wszystkie 61 ma PUSTE `author_display` - nie ma czego dopinac.
2. To nie sa osierocone interakcje, tylko zapisy WLASNEJ aktywnosci: "test draft",
   opisy zrzutow ekranu, nasze wlasne opublikowane posty. **Nie maja drugiej strony
   i nie powinny jej miec.**
3. **Zaden licznik ich nie widzi** - oba zapytania zliczajace sa zawezone `WHERE contact_id=...`.

**Liczba "348 wpisow" pochodzila z MOJEJ WLASNEJ SONDY, nie z zadnego widoku systemu.**
Zmierzylem cos, czego nikt nie oglada, i zapisalem pomiar jako dlug.

**Zasada:** zanim nazwiesz obecnosc danych wada, znajdz KONSUMENTA. Jesli zaden odczyt ich nie
dotyka, nie ma wady - jest co najwyzej zapach modelowania. Naprawa czegos, czego nikt nie czyta,
to czysty koszt i nowe ryzyko.
