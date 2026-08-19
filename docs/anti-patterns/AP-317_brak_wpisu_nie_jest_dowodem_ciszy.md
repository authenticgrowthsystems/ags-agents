# AP-317: Brak wpisu w bazie nie jest dowodem ciszy, a godzina bez daty nie jest data dzisiejsza

**Ustanowiony 14/08/2026 (Manager AGS, na wlasnym bledzie). Do kanonu 19/08/2026.**
Blizniak AP-311, ale o innej diagnozie i innej naprawie: tam system MIAL JAK pokazac i zawiodl,
tu **system dziala dokladnie tak, jak zostal zaprojektowany, i nadal nie wie**, bo zdarzenie
wydarzylo sie poza jego zasiegiem. Nie ma czego naprawiac.

## Wzorzec

Dwa ruchy, ktore w praktyce chodza para, bo drugi jest lataniem pierwszego:

1. **Baza milczy o kontakcie, wiec kontaktu nie bylo.** Odczyt poprawny, teczka pusta,
   wniosek falszywy. Watek szedl SMS-em, WhatsAppem albo telefonem, czyli kanalem,
   ktorego baza nie widzi i **nie zobaczy, dopoki ktos nie zbuduje warstwy 0**.
2. **Luke lata sie zrzutem ekranu od czlowieka, a zrzut czyta sie bez daty.** Na ekranie
   telefonu stoi sama godzina. Umysl dokleja brakujaca date domyslem "dzis", bo to najtansza
   hipoteza, i robi to **po cichu** - nie ma momentu, w ktorym pada pytanie "skad wiem".

Trzeci ruch jest najdrozszy i to on zamyka petle: **domysl wraca do bazy jako wpis**.
Od tej chwili nikt nie odrozni juz tego, co zostalo ZOBACZONE, od tego, co ZGADNIETE.

## Dowod: watek posrednika, 14/08/2026

Manager przygotowal Tomaszowi SMS do posrednika (Piotr Hamryszak, cieple dojscie do Adamietz)
po sprawdzeniu bazy, w ktorej tego posrednika **nie bylo**. Watek SMS mial wtedy trzy tygodnie
i cztery wiadomosci. Nakladala sie na to druga luka strukturalna: Manager nie ma `pipeline_add`,
wiec dla kontaktu spoza lejka nie da sie zapisac wpisu nawet wtedy, gdy sie o nim wie.

Potem przyszedl zrzut ekranu. Manager odczytal z niego godzine "08:31" jako dzisiejsza, uznal,
ze wiadomosc wlasnie poszla, i **kazal SMS wstrzymac**. Godzina byla sprzed dwoch tygodni.
Bledny odczyt trafil nastepnie do bazy jako fakt.

**Rozstrzygniecie nastepnego dnia** (15/08, Q1 z meldunku): w kanalach niewidocznych dla bazy
poszedl **wylacznie** SMS domykajacy do Hamryszaka, a NIC nie poszlo do szkol ani do Patrycji.
Czyli baza pokazywala cisze wobec jedynej osoby, wobec ktorej ciszy nie bylo. Dokladnie odwrotnie,
niz wynikaloby z jej czytania.

**Ten sam dzien, przypadek domkniety POPRAWNIE.** Konektor Gmail nie zwracal korespondencji
z `grupachwalinski.pl`, wiec wygladalo, ze mail do Miroslawa Damczyka nie poszedl. Manager
zapisal: "Nie zakladam, ze poszla. Czekam na potwierdzenie od Tomasza". Zrzut o 11:09 pokazal,
ze mail poszedl 13/08 i odpowiedz przyszla tego samego dnia. Roznica miedzy tym przypadkiem
a poprzednim nie lezy w narzedziu, tylko w tym, **czy odczyt zostal domkniety pytaniem
do czlowieka, czy domyslem**.

**Ta sama wada na poziomie maszyny (20/07).** `SELECT created_at::time ... ORDER BY created_at`
sortuje po kolumnie WYJSCIOWEJ, czyli po samej godzinie bez daty; kosztowalo falszywy trop
"znikajacych wierszy". Godzina odcieta od daty klamie tak samo, kiedy odcina ja rzutowanie
w SQL, jak wtedy, kiedy odcina ja kadr zrzutu ekranu.

**Przypis, nierozstrzygniete:** spotkanie z Markiem Sroka jest 03.09.2026 o 9:00 (potwierdzone
przez Tomasza 15/08), a w bazie wisi 11:00. Skad wzielo sie 11:00, **w repo nie jest zapisane** -
nie przypisuje tego temu anty-wzorcowi, notuje jako rozjazd do sprawdzenia przy poprawce.

## Why bad

- **Odczyt jest poprawny, a wniosek falszywy, wiec nic nie zapala sie na czerwono.** Przy AP-311
  da sie znalezc winnego: martwa kolumna, filtr, brak drogi zapisu. Tu nie ma wadliwego
  komponentu, wiec nie ma tez momentu, w ktorym ktokolwiek zaczyna szukac.
- **Kazda teczka jest niepelna Z DEFINICJI, nie przez wypadek.** Baza nie zawiera SMS, WhatsAppa,
  rozmow telefonicznych ani wiadomosci z LinkedIn i X i nie bedzie zawierac, dopoki ktos tego
  nie zbuduje. To nie jest stan przejsciowy, do ktorego mozna sie nie przyzwyczajac.
- **Domysl jest tanszy niz pytanie, wiec wygrywa domyslnie.** "Dzis" nie kosztuje nic i nie
  zostawia sladu; pytanie kosztuje wiadomosc i opoznia odpowiedz o godziny.
- **Blad zapisany do bazy zmienia status z pomylki na dane.** Wiersz nie niesie informacji o tym,
  czy powstal z obserwacji, czy z wnioskowania. To AP-312 od strony pochodzenia: nie klamie
  nazwa, klamie ZRODLO.
- **Szkoda jest zewnetrzna i relacyjna.** Wstrzymany SMS to nie linijka w logu, tylko cisza wobec
  czlowieka, ktorego poproszono o przysluge, w relacji prywatnej o juz naruszonym saldzie
  (D-F, 14/08).

## Correct

1. **Zanim podasz gotowy tekst do kogokolwiek, zapytaj czlowieka o kanaly, ktorych baza nie widzi.**
   Jedno zdanie: "co ostatnio poszlo do tej osoby i kiedy". Bez odpowiedzi nie piszesz nic.
   Regula przyjeta przez Managera 14/08; w Sales Managerze v1 zaszyta jako rutyna R-2, czyli
   warstwa 0 zrobiona czlowiekiem zamiast integracja - tania i do zbudowania w jednej sesji.
2. **Pusta teczka raportuje "nie wiem", nie "nic nie bylo".** Widok ma nazywac swoj horyzont;
   cisza w widoku o zawezonym zasiegu nie jest cisza w swiecie.
3. **Godzina bez daty zatrzymuje, nie domysla sie.** Przy zrzucie bez naglowka dnia pytasz o date
   albo prosisz o szerszy kadr. Ten sam mechanizm co AP-314 punkt 2: brakujaca wartosc ma padac
   ZAMKNIETA. Domyslne "dzis" to odpowiednik porownania z NULL, ktore przepuszcza po cichu.
4. **Wpis do bazy rozroznia ZOBACZONE od WYWNIOSKOWANEGO.** Data z domyslu albo nie wchodzi,
   albo wchodzi z jawna adnotacja. Bez tego rozroznienia wpis jest nieodwracalny - za tydzien
   nikt nie odtworzy, skad sie wzial.
5. **Decyzja o WSTRZYMANIU wymaga tego samego dowodu co decyzja o WYSLANIU.** Ten blad kosztowal
   wlasnie przez asymetrie: wstrzymanie wyglada na ostrozne, wiec przeszlo bez sprawdzenia.
   Niewyslana wiadomosc jest dzialaniem, nie jego brakiem.
6. **Luke strukturalna zglaszaj jako luke, nie obchodz jej po cichu.** Brak `pipeline_add`
   sprawia, ze kontakt spoza lejka nie ma gdzie wyladowac i dziennik idzie na dysk. To zachowanie
   jest poprawne dokladnie tak dlugo, jak dlugo jest widoczne.

## Granica z AP-311

Oba wpisy zaczynaja sie od pustki w widoku i oba koncza sie wnioskiem "nic sie nie dzialo".
Rozne sa DIAGNOZA i NAPRAWA.

| | AP-311 | AP-317 |
|---|---|---|
| stan systemu | wadliwy: brak drogi zapisu, filtr, brak odczytu | sprawny, dziala zgodnie z projektem |
| pytanie | czy system MIAL JAK to pokazac? | nie mial i nie bedzie mial, wiec co z tym robisz? |
| naprawa | poprawka; po niej pustka zaczyna cos znaczyc | staly protokol: pytanie do czlowieka plus bramka na jego odpowiedzi |
| domkniecie | jednorazowe | zadne, dopoki nie powstanie warstwa 0 |

Test rozstrzygajacy: **czy istnieje poprawka, po ktorej ta pustka stalaby sie wiarygodna?**
Jesli tak - AP-311, szukaj wady. Jesli nie, bo kanal nie ma zadnego polaczenia z baza -
AP-317, zmieniasz sposob czytania, nie system.

Drugiej polowy tego wpisu AP-311 nie obejmuje wcale: nie ma tam nic o tym, ze **kanal
kompensacyjny tez potrzebuje bramki**. Zrzut ekranu jest lekarstwem na AP-311 (sonda bije
pamiec) i jednoczesnie nosnikiem nowego bledu, bo przychodzi bez kontekstu, ktory baza
niosla za darmo.

## Punkty zaczepienia

- `C:\Claude-CoWork\AGS\MASTERPROMPT_MANAGER_AGS_v5_fable.md` sekcja 7 (pelny przebieg trzech
  stopni, sformulowanie Managera) i sekcja 12 punkty 1-3 (przyczyna zrodlowa, brak `pipeline_add`)
- `C:\Claude-CoWork\AGS\PAMIEC_MANAGERA_dlug_i_decyzje.md` sekcja 1 (lista kanalow niewidocznych,
  regula Managera) oraz wpisy z 15.08 (rozstrzygniecie Q1, rozjazd godziny u Chwalinskiego)
- `C:\Claude-CoWork\AGS\DZIENNIK_14082026.md` - ten sam dzien, przypadek domkniety poprawnie
- `docs/cm/RAPORT_do_BE_20072026_handoff_integracja.md` sekcja 6 - `created_at::time`
  i falszywy trop znikajacych wierszy
- `docs/anti-patterns/AP-311_brak_danych_to_nie_fakt.md`, `AP-314_bramka_ktorej_nikt_nie_widzial.md`
  punkt 2, `AP-312_nazwa_stanu_klamie.md`
