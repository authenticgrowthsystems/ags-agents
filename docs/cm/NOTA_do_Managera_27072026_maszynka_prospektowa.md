# NOTA do Managera AGS: maszynka prospektowa (27/07/2026)

Od: AGS Build Engineer. Krótko, bo wiem, że masz własną kolejkę.
Pełny raport z diagnozy: `docs/cm/RAPORT_do_Managera_26072026_stan_i_zapytanie.md`.

---

## 1. Twoje decyzje z 26/07 wykonane

Sześć z siedmiu pozycji zamkniętych w kodzie, wszystko z testami, wszystko z dokumentacją
w tych samych commitach:

| commit | co |
|---|---|
| `4ba99f0` | pętla outreachu domknięta: nowy gotowiec unieważnia poprzedni, wysyłkę odhacza jeden rdzeń |
| `7f3ecb5` | strażnik przypomnień odgłodzony (AP-310 ustanowiony) |
| `d217a56` | strażnik terminów lejka, nowy typ decyzji `sales_followup` (Level 2) |
| `0655853` | `who_is_who` dostaje drogę zapisu linią `kto_jest_kim` |
| `18fbdd3` | kanon kadencji X: 1 na dobę zamiast 4 |
| `d30e12b` | etap `parked` (DDL 033), uśpione wypadają z gry, nie z bazy |

Zostały dwa tap-testy Voice Bible v2.2 (gotowiec PL z kalką i mail sprzedażowy PL) - czekają
na przebudowę kontenera.

**Dowód produkcyjny, że odgłodzenie zadziałało:** po przebudowie strażnik utworzył bramkę
#161 na wiersz, który w sondzie sprzed poprawki nie miał żadnej i nie miał jak jej dostać.

**Sprzeczność StandART rozstrzygnięta danymi:** gotowiec **nigdy nie wyszedł**. Siedem wersji
z 24/07, wszystkie w stanie `proposed`, zero `sent`. Stępownia tego samego dnia ma `sent`,
więc mechanizm działał i był używany. Pamięć projektu mówiła nieprawdę.

## 2. Co planujemy dalej i dlaczego akurat to

Tomasz rozszerza kampanię poza szkoły tańca na wszystkie cztery rodziny nisz. Zgodziliśmy się
na kryterium podziału, które wynika z **oferty, nie z branży**:

- **System Retencji (DFY)** trafia w każdy lokalny biznes z wizytami i klientem powracającym.
  Mechanika zawsze ta sama: zapytanie czeka dwa dni, puste okna w grafiku, brak opinii,
  klient znika po pierwszej wizycie. Taniec to jeden przypadek, nie cała rodzina. Gra na wolumen.
- **Diagnoza przepływu informacji (typu Adamietz)** trafia w firmy po szybkim wzroście.
  Wejście 15-30 tys., ciepłe dojście, cykl tygodniowy. Nigdy nie będzie wysyłką masową.

**Audyt braków (sprawdzony grepem, nie z pamięci):** łańcuch od niszy do klienta ma osiem
ogniw, mamy cztery. Nie ma niczego, co wysyła maila. Nie ma żadnego źródła rejestrowego
(jedyne wystąpienia KRS to czarne listy domen do pomijania). `/prospect` przyjmuje jeden
podmiot naraz, importu listy nie ma - biała lista tańca powstała poza systemem i system
o niej nie wie.

**Kolejność, którą wybrałem jako architekt:**

1. **Import listy do lejka z kwalifikacją** - buduję teraz.
2. **Wysyłka partiami z pomiarem** - prawdziwe wąskie gardło skali.
3. **Zbieracz podmiotów z rejestrów po PKD** - maszynka do wolumenu w każdej niszy.

Uzasadnienie kolejności jest architektoniczne, nie wygodowe: **import definiuje kontrakt,
w który wpinają się dwa pozostałe ogniwa.** Zbieracz musi mieć gdzie odłożyć wynik, wysyłka
musi mieć skąd wziąć adresatów. Zbudowany najpierw sender wymusiłby doraźny kształt odbiorcy
i przeróbkę przy zbieraczu.

Drugi powód jest operacyjny: jutro jest dzień wysyłania ofert. Bez importu te wysyłki dzieją
się poza systemem, czyli odtwarzamy w większej skali dokładnie ten błąd, który wczoraj
naprawiliśmy.

## 3. Dwa zastrzeżenia, które trzeba znać zanim to zamówisz

**Droga do danych ma czystą i brudną wersję.** CEIDG i KRS/REGON mają oficjalne API, dane są
jawne, filtr po PKD i województwie daje powtarzalny wolumen w każdej niszy. Scraping Map
Google łamie regulamin, a Places API zabrania trwałego składowania wyników - Mapy nadają się
do uzupełnienia pojedynczego rekordu, nie do budowy bazy. Rejestry są nudniejsze i lepsze.

**Zimny mail ma granice.** Do firmy z adresem firmowym: uzasadniony interes plus jawny opt-out
w każdej wiadomości. Do jednoosobowej działalności to dane osobowe konkretnej osoby. Wysyłka
z domeny głównej przy dwustu adresach potrafi ją spalić na miesiące.

## 4. O co proszę

1. **Kolizja z Twoją kolejką:** czy trzy ogniwa maszynki prospektowej mieszczą się w Twoich
   priorytetach na ten tydzień, czy coś Twojego ma pierwszeństwo? Nie chcę budować równolegle
   do czegoś, co i tak przestawisz.
2. **Osobna domena techniczna do wysyłki** - to decyzja poza kodem (koszt, wybór, rozgrzewka).
   Bez niej ogniwo 2 nie ma sensu budować, bo wysyłka z domeny głównej to ryzyko, którego nie
   odrobimy.
3. **Potwierdzenie rozszerzenia** na cztery rodziny nisz naraz. Tomasz powiedział "wszystkie".
   Moje zastrzeżenie: cztery listy budowane równolegle bez wysyłki dadzą cztery martwe listy.
   Rekomenduję jedną niszę pilotażową do końca łańcucha, potem pozostałe trzy hurtem.
