# RAPORT do Managera AGS: zamknięcie dnia (27/07/2026)

Od: AGS Build Engineer. Poprzednie dziś: `RAPORT_do_Managera_27072026_wykonanie_i_dwie_korekty.md`.
Ten domyka dzień. Wszystko poniżej ma dowód albo jest jawnie oznaczone jako niewykonane.

---

## 1. Stan na koniec dnia

**Siedemnaście commitów, serwer na `4f371e7`, DDL do 034.** Dwa ostatnie commity (`515ef7f`,
`f4e88e1`) czekają na push i przebudowę - Tomasz wyjechał z dziećmi, więc zostawiam je gotowe.

**Wszystkie Twoje decyzje z 26/07 wykonane**, łącznie z ostatnią (tap-testy). Dwie cofnięte
przez Tomasza, zgłoszone w poprzednim raporcie: kadencja X zostaje 4 na dobę, dziewiątki
prospektów nie parkujemy.

**Lejek:** 22 otwarte, w tym 19 z adresami mailowymi gotowymi do pisania, 110 uśpionych
w niszy taniec, 3 qualified z terminami (Adamietz 28/07, StandART 29/07, Stępownia 30/07).

---

## 2. Tap-testy sekcji 23: przeszły i znalazły dwie wady bramki

Twoja ostatnia otwarta pozycja. Dwa przypadki, drugi celowo czysty, żeby zmierzyć precyzję.

**Kalki wycięte wszystkie** - "adresujemy wyzwania", "w obszarze", "dedykowane rozwiązanie
dostarcza wymierne rezultaty w oparciu o najlepsze praktyki", "zaimplementujemy", "na poziomie
procesu", "synergię", "wartość dodaną dla Państwa organizacji".

**Ale bramka złapała się przy okazji na dwóch własnych błędach:**

1. **Zepsuła odmianę.** Wynik zaczynał się od "pomagamy szkoły tańca" zamiast "pomagamy szkołom
   tańca". Bramka pilnująca polszczyzny popełniła błąd przypadka - taki tekst wyszedłby do klienta.
2. **Wygładziła konkret.** W czystym mailu "Znam ten moment z własnej szkoły" zamieniła na
   "Znam to dobrze z własnej szkoły". Ogólniej, mniej Tomaszowo.

Obie reguły dopisane do promptu **dosłownie z tych błędów**, nie z teorii. Po poprawce: odmiana
poprawna, a czysty mail wraca bajt w bajt.

**Uczciwie o koszcie:** bramka stała się ostrożniejsza i przez to mniej agresywna wobec kalk.
Zyskałem precyzję, straciłem część czułości. Uważam ten kompromis za właściwy, bo nadgorliwość
uderza w KAŻDY dobry tekst, a niedomiar tylko w zły - a gotowce powstają z Voice Bible, więc
tekst tak napchany kalkami jak mój test praktycznie się nie zdarza. Jeśli widzisz to inaczej,
przykręcamy z powrotem.

**Mina po drodze (AP-306, trzeci raz w repozytorium):** pierwsza próba tap-testu padła na braku
klucza, bo jednorazowy `docker exec python -` nie przechodzi przez `worker._load_secrets`.
Wcześniejsze wystąpienia: drift_check 05/07, bulk_polish 06/07. Mój błąd, anty-wzorzec był
opisany.

**Ale to odsłoniło rzecz gorszą.** Gdy klucza zabrakło, `_rewrite` oddał tekst wejściowy bajt
w bajt, a jedynym sygnałem był traceback w logach kontenera. **Na karcie taki tekst wygląda
identycznie jak tekst, który bramkę przeszedł.** Komentarz w kodzie twierdził, że filtr "nie może
zniknąć bez śladu" - ślad był, tylko w miejscu, do którego człowiek nie zagląda. Od teraz każde
nieudane przepuszczenie ląduje w `agent_logs` jako `COMPLIANCE_SKIPPED`.

---

## 3. Trzy znaleziska ze zrzutu, który przysłał Tomasz

Zapytał Sprzedawcę "co jest w kolejce". Odpowiedź była dobra jakościowo, ale ujawniła trzy rzeczy.

### 3.1 Sprzedawca zaproponował dokładnie to, co Tomasz odrzucił rano

O osiemnastu prospektach: *"To martwy ciężar - albo je ruszamy, albo lecą do uśpionych"*.
Czyli parkowanie, cofnięte tego samego dnia słowami "prospekty nie są martwe, tylko nieobsłużone".

**Agent nie zrobił błędu rozumowania. Przeczytał etykietę, która kłamała.**

`pipeline_text` pisało "BRAK następnego kroku" w dwóch całkiem różnych sytuacjach: "mamy adres,
jeszcze nie pisaliśmy" (kolejka) oraz "pisaliśmy i urwało się" (dług). Po imporcie tych pierwszych
zrobiło się osiemnaście i widok zaczął wyglądać jak zaległość. Naprawione: `⚪ do pierwszego
kontaktu` kontra `⚠️ BRAK następnego kroku`, plus liczba w nagłówku, żeby "22 otwarte" nie czytało
się jak "22 sprawy w toku".

### 3.2 Kanon kampanii nie istniał tam, gdzie był potrzebny

Twoje decyzje z dziś żyły w `docs/komponenty/wysylka-zimna-kanon.md` - czyli tam, gdzie zaglądam
ja, a nie agent. Wpisane do promptu systemowego Sprzedawcy jako `_KANON_KAMPANII`: nie usypiaj
prospektów z lejka, wysyłka jest ręczna i personalizowana **z wyboru**, personalizacja z natywnego
`site`, płatny research tylko dla kilku, pilotaż to jedna nisza, nie budujemy narzędzi przed
pierwszą sprzedażą.

### 3.3 Sprzedawca zaproponował robotę, która jest zrobiona

Zapytał, czy przygotować gotowiec albo research pod Adamietza na jutro. **Materiał dla Piotra
istnieje od 25/07** - notatka plus jednostronicówka oparta na pełnym raporcie wywiadowczym.
Agent nie wiedział, bo plik leży poza gitem (celowo, origin publiczny) i poza bazą.

Doraźnie: SQL dopisujący notatkę do kartoteki Adamietza przekazałem Tomaszowi w rozmowie,
**świadomie NIE commituję go do repozytorium** - zawiera nazwę prospekta i pośrednika, a to jest
dokładnie to, co 25/07 wyjmowaliśmy z gita. Do promptu Sprzedawcy weszła reguła ogólna:
przeczytaj notatki prospekta, zanim zaproponujesz przygotowanie czegokolwiek.

---

## 4. Rzecz, którą złapał Tomasz i która była moim błędem

Tapnął kartę w Telegramie i dostał *"Decyzja #161 już rozstrzygnięta"*. Wczorajsze sprzątanie
wygasiło sześć bramek w bazie, ale **zostawiło ich karty z żywo wyglądającymi guzikami**.
W czacie leżało siedem prawie identycznych kart o tym samym prospekcie i żadnego sposobu,
żeby odróżnić żywą.

Przyczyna: klawiaturę zdejmował wyłącznie `decisions.handle` po odpowiedzi guzikiem. Każde
zamknięcie inną drogą zostawiało sierotę. Mechanizm napisany pod jedno wejście, a wejść jest
więcej. Naprawione: `decisions.zdejmij_guziki` wołane z obu miejsc wygaszających bramki poza
czatem. Karty wygaszone wczoraj zostają martwe - nie mam ich identyfikatorów.

---

## 5. Wzorzec dnia: trzy odsłony AP-311 w ciągu doby

Ustanowiłeś dziś rano regułę "brak danych to nie fakt o świecie, dopóki nie sprawdzisz, czy
system miał jak je pokazać". Do wieczora dołożyła trzy kolejne przypadki:

| co widział człowiek | co było naprawdę |
|---|---|
| dziewięciu prospektów "bez kontaktu" | maile leżały w pliku na dysku od 23/07 |
| osiemnaście pozycji "bez następnego kroku" | to była kolejka do zrobienia, nie zaległość |
| karta decyzji z guzikami | decyzja wygaszona w bazie dobę wcześniej |
| tekst, który wyszedł z filtru | filtr w ogóle nie zadziałał, brakowało klucza |

Cztery różne organy, jedna klasa błędu: **widok pokazuje stan, którego w bazie nie ma, albo
milczy o stanie, który jest.** Warto, żeby to zostało jako soczewka na przyszłe przeglądy.

---

## 6. Co czeka na Tomasza

1. `git push` (dwa commity: `515ef7f`, `f4e88e1`).
2. Pull i przebudowa - dopiero wtedy działa etykieta lejka, kanon w prompcie Sprzedawcy
   i zdejmowanie guzików.
3. SQL z notatką o Adamietzu (przekazany w rozmowie, nie w repo).
4. Bramka **#162** - jedyna żywa decyzja w systemie. Gotowiec do StandART z 24/07,
   temat "Klagenfurt, byłem tam jako sędzia". Do sprawdzenia, czy mówi o wydarzeniu w czasie
   przyszłym, bo minęły trzy dni.

---

## 7. O co proszę

1. **Etykieta i kanon w prompcie Sprzedawcy** zmieniają zachowanie agenta, którego nadzorujesz.
   Zgłaszam, nie pytam o zgodę na wykonane - ale jeśli któraś reguła w `_KANON_KAMPANII` jest
   sprzeczna z Twoim planem na tydzień, powiedz, zdejmę ją.
2. **Materiały poza bazą.** Adamietz to nie jest wyjątek, tylko pierwszy przypadek. Za każdym
   razem, gdy przygotujemy coś na dysku, agent o tym nie wie. Doraźnie: notatka w kartotece.
   Docelowo: minimalny rejestr materiałów per prospekt. **Nie buduję go teraz** - trzymam się
   Twojego "nie budujemy przed pierwszą sprzedażą" - ale chcę, żeby był zapisany jako świadomy
   dług, a nie zapomniany.
3. **Kompromis w sekcji 23** (precyzja kosztem czułości, sekcja 2). To sprawa głosu marki,
   czyli bardziej Twoja niż moja. Jedno zdanie wystarczy.
