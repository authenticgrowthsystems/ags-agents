# RAPORT: most katalogi-baza, AP-313 i audyt TyNieMusisz

**Od:** BE (Budowniczy Systemów) → **Do:** Manager AGS
**Prace z 01/08/2026, raport pisany po północy.**
**Stan: WDROŻONE i sprawdzone na produkcji.** Serwer `951df94`, DDL do 038.

---

## 1. Most katalogi-baza (DDL 037 + 038)

Struktura katalogów klientów (`Klienci\<Nazwa>\` z podfolderami) i wiersze w lejku były
dwoma niezależnymi światami. Teraz są związane przez `sales_pipeline.katalog`.

**Ustalenie, które wymusiło kształt: ścieżki NIE DA SIĘ wyliczyć z bazy.**

| katalog na dysku | wiersz w lejku |
|---|---|
| `Stepownia_Dudzik` | **Wrocławska Stepownia** |
| `La_Cultura_Wrobel` | **Dance Company La Cultura** |
| `Chwalinski` | (nie istniał) |

Katalogi niosą **nazwisko właściciela** - Dudzik, Wróbel - którego w bazie nie ma w ogóle.
Żadna transliteracja tego nie odtworzy, więc ścieżka jest **przechowywana**, nie liczona.

Kolumna wisi na `id`, nie na nazwie: `prospect_name` **nie ma ograniczenia UNIQUE**, więc
wiązanie po nazwie pękłoby przy pierwszej franczyzie (Egurrola ma w lejku trzy wiersze).
Nazwa katalogu ustalana **raz i nigdy niezmieniana** - reguła stoi w kodzie **i** w SQL.
Powód nie jest kosmetyczny: system nigdy nie tworzy ani nie przenosi katalogów, więc podmiana
napisu zostawiłaby wiersz wskazujący na nieistniejącą lokalizację.

Cztery katalogi powiązane, Grupa Chwaliński założona (qualified, Jan Szuta, dane kontaktowe).

## 2. Decyzja Tomasza o markach - warta odnotowania jako wzorzec

Polecenie brzmiało: dodać markę TNM i przepiąć na nią cały polski lejek (24 wiersze).

**Odczyt przed wykonaniem: 107 miejsc w `cm-agent/app/` filtruje `brand_id='AGS'`,
w tym 13 w samym `sales.py`.** Przepięcie wypchnęłoby te 24 wiersze z widoku lejka,
ze strażnika terminów i z generowania gotowców - **po cichu**, bo zapytanie bez wyników
nie jest błędem.

Tomasz, po przedstawieniu rachunku, cofnął własne polecenie:

> *„Wypchnięcie 24 wierszy poza widok lejka, w tygodniu, w którym mam trzy otwarte rozmowy
> i wysłany materiał do dealera, to jest kupowanie porządku za sprzedaż. Wielomarkowość nie
> przybliża do pierwszej faktury, a przepięcie danych bez gotowego kodu ją oddala."*

**Rozwiązanie: `sales_pipeline.marka_docelowa` jako ETYKIETA, nie filtr.** Żaden kod jej nie
czyta. Ustawiona na TNM dla 24 aktywnych wierszy. Kiedy kod będzie wielomarkowy, przepięcie
będzie jednym UPDATE-em zamiast ponownego rozstrzygania 24 przypadków z pamięci.

**Reguła obowiązująca od 01/08:** polski rynek i polski język to TNM, anglojęzyczne kontakty
z X i LinkedIna to AGS. Wielomarkowość kodu wchodzi do kolejki **po pierwszej zamkniętej
sprzedaży** (dług D-013).

Kontrola po operacji potwierdziła: `brand_id | AGS | 134` - filtr nietknięty.

## 3. AP-313 USTANOWIONY: założenie ASCII przy polskich nazwach własnych

**Złapany na własnym kodzie, kilka godzin po tym, jak ten kod przeszedł komplet testów
i wdrożenie.**

Zabezpieczenie przed duplikatem brzmiało `ILIKE '%Chwalin%'` dla nazwy **Chwaliński**.
Nie trafia **nigdy**: C-h-w-a-l-i-**ń**-s-k-i - w tym słowie nie ma zwykłego `n`.

**Dlaczego groźniejszy niż literówka:** pierwszy przebieg działa poprawnie, wiersz się zakłada,
test przechodzi. Defekt wychodzi dopiero przy **drugim** uruchomieniu, jako duplikat.
A zapytanie kontrolne na końcu tego samego pliku używało **tego samego wzorca**, więc było
ślepe dokładnie tak samo.

**To odróżnia AP-313 od zwykłej pomyłki: narzędzie do wykrycia błędu miało ten sam błąd.**
Stąd czwarta zasada wpisu: kontrola musi używać innego mechanizmu niż to, co kontroluje.

**Rachunek AP-309:** 27 dopasowań `ILIKE`/`LIKE` w `cm-agent/app/`, z czego **siedem** dotyczy
nazw własnych (`sales.py` 225/1178/1730, `teczka.py` 69/76/106/109). Reszta to nasze znaczniki
ASCII w `notes` - tam ogonka nie ma czego rozbić. Naprawa: normalizacja **obu stron** przez
`translate()` (bez `unaccent`, które wymagałoby rozszerzenia bazy).

**Konkretny skutek, gdyby przeszło niezauważone:** katalog na dysku nazywa się `Chwalinski`,
wiersz w bazie `Grupa Chwaliński`. Wpisanie nazwy katalogu do `teczka` zwracało
**„nie znajduję"** - komunikat brzmiący jak BRAK KLIENTA, nie jak usterka wyszukiwania.
Most pękłby przy pierwszym prawdziwym użyciu. Sprawdzone po naprawie na produkcji: znajduje.

## 4. Biografia - naprawiona, bo była aktywnym źródłem kłamstwa

`TyNieMusisz\STORY_BANK.md` i `CONTEXT_OS_AGS.md` były **starszymi kopiami** dokumentów żyjących
w katalogu AGS. Niosły biografię naprawioną w AGS 14/05:

- `CONTEXT_OS_AGS.md:75` → **„Self-taught dancer, now mentor"**
- brak sprostowania o faksach (szły do **przedszkoli w Opolu**, nie do szkół tańca)

Zsynchronizowane z kanonem. Zweryfikowałem przed nadpisaniem, że wersje AGS są **nadzbiorem** -
wszystkie historie obecne, o jeden nagłówek więcej. Stare kopie w `_ARCHIWUM`, nic nie skasowane.

Kanon: **inżynier był pierwszy, taniec był planem B, który wyszedł jako plan A na dwadzieścia
lat.**

## 5. Audyt 124 plików TyNieMusisz

Ośmiu audytorów, wyłącznie odczyt. **56 kandydatów** z uzasadnieniem: `LISTA_do_przejrzenia_01082026.md`.
Segregacja wg reguł Tomasza (A do naprawy w treści, B do archiwum, C zostaw) - dostarczona
**grupa A**, pięć pozycji: `GRUPA_A_do_naprawy_01082026.md`.

**Najpilniejsza (A1):** `PRODUKT_GLOWNY_Google_Ads_bez_przepalania.md` wiersz 20 mówi
*„Nie jestem specjalistą od reklamy. **Jestem choreografem.**"* - dokładnie ta inwersja, którą
kanon nazywa błędem, na stronie **produktu głównego**, czyli w tekście czytanym przed zakupem.

**KOREKTA WŁASNEGO ZGŁOSZENIA (A3).** Zgłosiłem, że polityka prywatności jest „jedyną pozycją
z konsekwencją prawną", sugerując śledzenie bez zgody. **Sprawdziłem to na żywej stronie
i myliłem się co do wagi.** Wdrożenie GA4 jest poprawne: Consent Mode v2, wszystko `denied`
domyślnie z `region: ['PL','EU','EEA']`, zgoda wyłącznie po kliknięciu, baner ma oba wyjścia
(„Akceptuję wszystkie" i „Tylko niezbędne"). **Nie ma śledzenia bez zgody.** Nieprawdziwy jest
sam **opis**: polityka mówi „nie używamy cookies analitycznych" i „baner pojawi się
w przyszłości", a GA4 `G-Y5P5B8RSHF` działa od 30/05. To naruszenie obowiązku informacyjnego,
nie zasady zgody. Wpis poprawiony, żeby lista nie straszyła bardziej, niż powinna.

**Audyt ujawnił też mój błąd:** w briefie dla ośmiu agentów napisałem „GreenHostingLab (GHL)".
Zmyśliłem to. **GHL to GoHighLevel** - 252 wystąpienia w plikach, zero dla mojej wersji.
Zgłaszam, bo „nazwy narzędzi" to jedna z kategorii grupy A.

## 6. Wzorzec dnia, wart uwagi przy planowaniu

**Trzy razy pod rząd wada wyszła dopiero przy uderzeniu w żywe dane, nie w testach:**

1. teczka pokazywała etykietę zamiast treści maila (atrapa bazy miała kształt, który sam
   wymyśliłem: treść w `content`, a prawdziwy gotowiec trzyma ją w `response`),
2. narzędzie MCP wystawiało parametr `kontakt` zamiast `contact_id` z kontraktu,
3. `%Chwalin%`, które nie trafia nigdy.

Test jednostkowy sprawdza kod wobec **wyobrażenia autora o danych**. Tap-test sprawdza go
wobec danych. Proponuję przyjąć jako regułę: **tap-test po wdrożeniu jest obowiązkowy.**

## 7. Dług zapisany

**D-010** (trzy kolumny na stan w `contacts`, w tym `pipeline_stage` bez ograniczenia,
45 wierszy), **D-011** (61 sierot w `engagement_log` - ani kontakt, ani lejek),
**D-012** (nic nie mapuje marki na korzeń katalogu), **D-013** (kod jednomarkowy,
wielomarkowość po pierwszej sprzedaży).

## 8. Otwarte

- **Narzędzie MCP `zapisz_tekst` nie zna jeszcze parametru `katalog`** - kod i baza go obsługują,
  ale PUT do n8n nie poszedł. Do czasu wgrania katalog ustawia się wyłącznie SQL-em.
- **Grupa A czeka na rękę Tomasza** (A1 pilna, A5 wymaga decyzji handlowej o cenie).
- **Kolejka Managera bez zmian:** walidacja długości + pole formatu, potem rozsuwanie części.
  **Kolejka X nadal pusta** - nie ruszałem.
