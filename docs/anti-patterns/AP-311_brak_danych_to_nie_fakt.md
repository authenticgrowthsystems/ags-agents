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

## Trzy kolejne odslony (27-29/07) - wzorzec okazal sie szerszy niz zaklada nazwa

4. **Etykieta, ktora klamie o tym, co znaczy (27/07).** "⚠️ BRAK nastepnego kroku" oznaczalo
   naraz "nie wiem, co dalej" (dlug) i "jeszcze do nich nie napisalem" (kolejka). Agent Sprzedazy
   przeczytal to i zaproponowal uspienie osiemnastu prospektow jako "martwego ciezaru" - czyli
   dokladnie to, co Tomasz odrzucil tego samego dnia rano. **Agent nie zrobil bledu rozumowania.
   Przeczytal etykiete.**
5. **Nazwa stanu obiecujaca co innego, niz stan znaczy (27/07).** `dispatching` brzmi jak stan
   przelotny ("wysylam"), a znaczy "czekam az wszystkie wiersze serii sie domkna" - stan
   trwajacy DNI. Manager zglosil zawieszenie posta; odczyt pokazal siedem materialow w tym
   stanie, wszystkie zdrowe, najstarszy 51 godzin i to poprawnie.
6. **Operacja hurtowa niewidzialna dla drugiego agenta (29/07).** Wycofanie 21 materialow przez
   `status='rejected'` jest w bazie NIEODROZNIALNE od odrzucenia przy przegladzie kart miesiac
   temu. Zapytanie "X + rejected + wiecej niz jeden wiersz" zwraca 26, z czego dzisiejszych 21.
   BE wie, co wycofal, bo sam to robil; CM patrzy na te sama baze i nie widzi roznicy.

**Wniosek z szesciu odslon:** regula "sprawdz, czy system mial jak pokazac dane" jest za waska.
Pelniejsza brzmi tak: **sprawdz takze, czy to, co system POKAZUJE, znaczy to, co obiecuje** -
nazwa statusu, tresc etykiety i zakres operacji sa danymi tak samo jak liczby. Cztery z szesciu
przypadkow to nie brak danych, tylko dane wprowadzajace w blad.

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
