# RAPORT: teczka prospekta WDROZONA i sprawdzona na zywym systemie (31/07/2026)

**Od:** BE (Budowniczy Systemów) → **Do:** Manager AGS
**Stan: LIVE.** Serwer `0c26350`, repo `67b6190`, DDL do 036. Konektor widzi cztery narzędzia.
Pełny obieg zapis → odczyt udowodniony na produkcji.

---

## 1. Co masz do dyspozycji od teraz

Dwa nowe narzędzia w konektorze `AGS Łącznik`, obok `stan_gry` i `wyslij_raport_pracy`:

- **`teczka(contact_id)`** - w jednym wywołaniu: dane kontaktu, cała chronologia tego, co do
  niego poszło, ostatni ustalony następny krok z datą, status. **Wołaj ZANIM napiszesz cokolwiek
  do prospekta** - bez tego nie wiesz, co już dostał ani co obiecaliśmy.
- **`zapisz_tekst(contact_id, kanal, tresc, status)`** - zapis powiązany z kontaktem, z datą.
  Kanały: `email | sms | whatsapp | dm | telefon`. Status: `draft | sent`.

`contact_id` przyjmuje **nazwę albo UUID**. Nie musisz znać identyfikatorów.

## 2. Ustalenie, które zmieniło Twój kontrakt

Sprawdziłem odczytem, zanim napisałem linijkę kodu, czy `contact_id` ma na co wskazywać.
**Nie miał.**

| rejestr | wierszy | z mailem | z `contact_id` |
|---|---|---|---|
| `contacts` | 194 | **0** | - |
| `sales_pipeline` | 133 | - | **0** |

Pokrycie po nazwie: **1 na 133**. `contacts` to uchwyty z X i LinkedIna z radaru komentarzy.
`sales_pipeline` to prospekty kampanii. **Dwie rozłączne populacje** - szkoła tańca, do której
piszesz mail, nie ma w `contacts` ani jednego wiersza.

Gdybym wziął kontrakt dosłownie, narzędzie byłoby martwe dokładnie dla tego, po co powstało.
Identyfikator jest więc rozstrzygany wobec **obu** rejestrów i teczka zawsze mówi, w którym
trafiła. Nie założyłem 133 kontaktów pod prospekty - to byłoby drugie źródło prawdy o tym samym
podmiocie, wbrew kanonowi z 22/07.

## 3. Cztery decyzje, które podjąłem sam

1. **`status='draft'` to nowa wartość, nie recykling `proposed`.** `proposed` budzi strażnika
   gotowców - każdy Twój mail rodziłby po dobie bramkę „Outreach czeka na wysłanie".
2. **Piąty kanał `whatsapp`**, bo kanon zimnej wysyłki mówi „WhatsApp, nie SMS". Bez tego
   faktyczny kanał kampanii trzeba by zapisać kłamliwie.
3. **`zapisz_tekst` przyjmuje opcjonalny `next_step` z terminem** - bo kroku, którego teczka ma
   zwracać, **nic w systemie nie ustalało**: lejek miał samą datę, a `contacts.next_action`
   istnieje od DDL 001 i nie zapisał go nigdy nikt (0 wierszy).
4. **`dm` celuje w LinkedIn**, bo to kanał DM kampanii.

## 4. Co narzędzie zrobi, a czego nie - sprawdzone na produkcji

| przypadek | wynik |
|---|---|
| nieznana nazwa | błąd + lista podobnych + „NIC nie zapisałem i niczego nie założyłem" |
| fragment „Studio" | **12 kandydatów z UUID-ami, zero zgadywania** |
| WhatsApp + draft | zapisane, widoczne w teczce jako ósmy wpis |

Franczyzy stoją osobno (Egurrola Katowice kontra Egurrola Grodzisk Mazowiecki), więc wada
z dedupu importu tu nie wraca.

## 5. DWIE WADY, KTORE ZNALAZL DOPIERO TAP-TEST

To jest najważniejsza część tego raportu, bo dotyczy sposobu pracy, nie jednej funkcji.

**Komplet zielonych testów jednostkowych (36 asercji) przepuścił obie.**

**Wada pierwsza: teczka pokazywała etykietę zamiast treści maila.** Tap-test na żywym StandART
zwrócił siedem wpisów, w każdym linia `outreach email: Klub Sportowy StandART` i ani słowa
z treści. Przyczyna: wszystkie tory zapisu trzymają konwencję, w której `content` niesie
**wejście albo etykietę**, a `response` niesie **nasz tekst**. Czytałem tylko `content`.
Test tego nie złapał, bo atrapa bazy miała wiersz o kształcie, który **sam wymyśliłem**.

**Wada druga: narzędzie wystawiało parametr `kontakt` zamiast `contact_id` z kontraktu.**
Wołanie nazwą z uzgodnionego kontraktu kończyło się `Received tool input did not match expected
schema`. To **AP-312 w warstwie integracji**: etykieta obiecywała co innego, niż znaczyła.
Przy okazji wyszło, że n8n oznacza **każdy** parametr `$fromAI` jako wymagany i nie ma sposobu
na opcjonalny - `defaultValue` tego nie zdejmuje, `isOptional` to otwarty wniosek o funkcję.
Opcjonalność realizujemy pustym ciągiem.

**Wniosek, który proponuję przyjąć jako regułę:** tap-test po wdrożeniu jest **obowiązkowy,
nie opcjonalny**. Test jednostkowy sprawdza kod wobec mojego wyobrażenia o danych. Tap-test
sprawdza go wobec danych.

## 6. Znalezione przy okazji, wymaga Twojej uwagi

1. **StandART (etap `qualified`) ma następny krok z terminem 29/07 08:00** - dwa dni po terminie
   i **bez opisu**, sama data. To jeden z trzech najdalej posuniętych prospektów w lejku.
2. **DWA z SIEDMIU gotowców StandART mają w treści ROZUMOWANIE agenta zamiast samego maila.**
   Po pełnym odczycie teczki policzyłem to dokładnie - **29 procent, czyli wzorzec, nie incydent**
   (AP-309: sprawdź, ile miejsc dzieli tę wadę):
   - wpis 2: „Zanim napiszę tekst, jedna uwaga: ... Hak, który wybrałem: ..."
   - wpis 4: „Ornontowice to nie Opole, więc konflikt interesów RDC tu nie zachodzi, mogę pisać
     normalnie. Hak sezonowy jest solidny: ..."

   Oba niosą wewnętrzną analizę odległości od Royal Dance Center i wybraną strategię zaczepienia.
   Gdyby ktoś skopiował taki gotowiec bez czytania, poszłoby to do klienta razem z uzasadnieniem,
   dlaczego wolno go zaczepiać.

   **Nie naprawiałem** - to zachowanie agenta, nie kod, więc decyzja jest Twoja. Zwracam uwagę,
   że pole `response` było dotąd praktycznie nieoglądane: teczka jest pierwszym narzędziem, które
   te treści w ogóle pokazuje. Wada mogła siedzieć tam od początku i nikt nie miał jak jej zobaczyć.
3. **Skrypt tworzący workflow Łącznika losował nowy sekret przy każdym uruchomieniu**, a sekret
   siedzi w ścieżce triggera - dołożenie jednego narzędzia zerwałoby adres konektora. Naprawione.
   **Sekret Łącznika został tego dnia wymieniony** (trafił na zrzut ekranu). Rotacja domknięta
   w trzech miejscach: definicja n8n, `app_secrets`, konektor claude.ai. Stary adres zwraca 404 -
   sprawdzone. Narzędzia zweryfikowane wywołaniem przez konektor, czyli tą samą drogą, którą
   pójdziesz Ty.
4. **Dług D-009:** gotowiec mailowy Sprzedawcy ląduje w kanale `Other`, tekst z teczki w `Email`.
   Nie poprawiłem od ręki, bo ta wartość jest kluczem dopasowania przy unieważnianiu gotowców -
   podmiana bez migracji odtworzyłaby wadę StandART z 24/07. Liczenie wysyłki per kanał kłamie.
5. **Dług D-003 zamknięty w połowie:** jest ludzka droga zapisu treści i następnego kroku.
   Pól kontaktowych przy wierszu lejka nadal nie da się wypełnić ręcznie.

## 7. Stan i co czeka

**Kolejka X nadal pusta** - nie ruszałem, zgodnie z poleceniem.

Otwarte po stronie Tomasza: uprawnienia narzędzi stoją na `Needs approval`, więc przy każdym
wywołaniu dostanie pytanie (dla `teczka`, czystego odczytu, warto rozważyć `Always allow`).

**Czekam na następne zadanie.** Walidacja długości i pole formatu stoją nietknięte.
