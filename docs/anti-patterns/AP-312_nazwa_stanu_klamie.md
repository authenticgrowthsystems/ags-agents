# AP-312: Nazwa stanu albo tresc etykiety obiecuje cos innego, niz znaczy

**Ustanowiony 29/07/2026 (Manager AGS).** Blizniak AP-311, ale odwrotny: tam widok MILCZY
o stanie, ktory baza zna. Tu widok MOWI - i mowi cos innego, niz jest.

**Nazwa jest dana tak samo jak liczba, i tak samo moze klamac.**

## Wzorzec

Stan, etykieta albo status dostaje nazwe, ktora jest skrotem myslowym AUTORA. Autor wie, co za
nia stoi, bo pisal kod. Kazdy inny - czlowiek albo drugi agent - czyta samo slowo i wyciaga
z niego wniosek zgodny z jego potocznym znaczeniem. Wniosek jest **racjonalny** i **falszywy**.

Kluczowa cecha: **nikt nie popelnia bledu**. Dane sa poprawne, kod dziala zgodnie ze specyfikacja,
czytajacy rozumuje bez zarzutu. Klamie warstwa miedzy nimi.

## Cztery przypadki, wszystkie z jednego tygodnia (27-29/07/2026)

1. **Etykieta znaczaca naraz dwie rozne rzeczy.** "⚠️ BRAK nastepnego kroku" w widoku lejka
   oznaczalo jednoczesnie "nie wiem, co z tym dalej" (prawdziwy dlug) oraz "jeszcze do nich nie
   napisalem" (normalna kolejka do zrobienia). Po imporcie listy tych drugich zrobilo sie
   osiemnascie i **wlasny Agent Sprzedazy** zaproponowal ich uspienie jako "martwego ciezaru" -
   czyli dokladnie to, co wlasciciel odrzucil tego samego dnia rano. Agent nie zrobil bledu
   rozumowania. Przeczytal etykiete. Naprawa: rozdzielenie na `⚪ do pierwszego kontaktu`
   i `⚠️ BRAK nastepnego kroku`.
2. **Status obiecujacy stan przelotny, a znaczacy dni.** `content_items.dispatching` brzmi jak
   "wysylam", a znaczy "rozeslane do kolejki, czekam az WSZYSTKIE wiersze serii osiagna stan
   terminalny". Manager zglosil zawieszony post; odczyt pokazal siedem materialow w tym stanie,
   **wszystkie zdrowe**, najstarszy 51 godzin i poprawnie, bo jego sloty siegaly 4 sierpnia.
3. **Karta z zywymi guzikami przy decyzji wygaszonej dobe wczesniej.** Sprzatanie wygasilo szesc
   bramek w bazie, ale klawiature z kart Telegrama zdejmowal wylacznie handler odpowiedzi
   guzikiem. W czacie zostalo siedem prawie identycznych kart, z ktorych zywa byla jedna,
   i **zaden sposob, zeby je odroznic**. Tomasz tapnal martwa.
4. **Status nieodroznialny miedzy dwiema roznymi sprawami.** Wycofanie hurtowe 21 materialow
   zapisane jako `status='rejected'` jest w bazie identyczne z odrzuceniem przy przegladzie kart
   miesiac temu. Zapytanie "X + rejected + wiecej niz jeden wiersz" zwraca 26 materialow, z czego
   z tej operacji jest 21. Autor operacji wie, co wycofal; drugi agent nie ma jak.

## Why bad

- **Blad jest niewidzialny dla obu stron.** Autor nazwy nie widzi problemu, bo dla niego nazwa
  jest oczywista. Czytajacy nie widzi problemu, bo wyciagnal poprawny wniosek z tego, co
  przeczytal. Nie ma momentu, w ktorym ktos zauwaza rozjazd - dopoki nie zapadnie zla decyzja.
- **Skaluje sie razem z liczba agentow.** Przy jednym czlowieku i jednym kodzie skrot autora
  wystarcza. Przy trzech agentach czytajacych te sama baze kazda mylaca nazwa mnozy sie na
  wszystkich czytajacych.
- **Testy tego nie lapia.** Nazwa jest poprawna technicznie, dane sa poprawne, przeplyw dziala.
  Nie ma czego asertowac.

## Correct: regula operacyjna

**Przy kazdej nowej etykiecie stanu zadaj jedno pytanie, ZANIM ja nazwiesz: czy ktos, kto
zobaczy to slowo bez dostepu do kodu, zrozumie je tak samo jak ja. Jesli nie, to nie jest nazwa,
tylko skrot dla autora.**

Praktycznie:

1. **Jedna etykieta = jedno znaczenie.** Gdy przy jednej nazwie dasz sie wymienic dwie rozne
   sytuacje, masz dwa stany, nie jeden. Rozdziel je (przypadek 1).
2. **Nazwa ma oddawac czas trwania.** Stan liczony w dniach nie moze nazywac sie jak stan
   liczony w sekundach (przypadek 2).
3. **Stan wygaszony musi wygladac na wygaszony** wszedzie, gdzie byl widoczny - takze poza baza,
   w interfejsie (przypadek 3).
4. **Operacja hurtowa ma zostawiac slad, ktory ja identyfikuje**, a nie tylko skutek nie do
   odroznienia od innych (przypadek 4).
5. Gdy nazwa jest juz w uzyciu i klamie, **poprawka nazwy jest tansza niz kolejna diagnoza** -
   ale kazda zmiana kontraktu miedzy tabelami, kodem i n8n idzie jako osobna decyzja, nie
   w ramach innego zadania.

## Konsekwencja przyjeta 29/07

`dispatching` idzie do przemianowania (nie natychmiast, zapisane z data jako dlug **D-008**).
