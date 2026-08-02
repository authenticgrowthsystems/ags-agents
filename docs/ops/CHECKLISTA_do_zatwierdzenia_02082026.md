# Checklista: co chcę poprawić. Decyzja przy każdej pozycji Twoja

**02/08/2026, BE dla Tomasza.** Nic z tej listy nie jest zaczęte.
Odhacz to, co ma iść; przekreśl resztę. Kolejność jest moją rekomendacją, nie wymogiem.

Legenda kosztu: **S** = do 30 minut, **M** = pół sesji, **L** = osobny build.

---

## I. DOMKNIĘCIE DZISIEJSZEJ ROBOTY (bez tego most jest w połowie)

- [ ] **1. PUT do n8n: parametr `katalog` w narzędziu `zapisz_tekst`.** `S`
  Kod i baza już go obsługują, ale narzędzie MCP go **nie wystawia** - sprawdziłem.
  Do czasu wgrania Manager nie ustawi katalogu przez rozmowę, tylko Ty SQL-em.
  *Jedna komenda w PowerShell, adres konektora bez zmian.*

- [ ] **2. Tap-test zapisu katalogu przez konektor.** `S`
  Po punkcie 1: zapis tekstu z katalogiem dla prospekta, który go nie ma, i sprawdzenie,
  że próba zmiany istniejącego wraca błędem. Dziś przetestowane tylko jednostkowo.

---

## II. GRUPA A - nieprawdziwe dane, które ktoś czyta

- [ ] **3. A1: „Jestem choreografem" na stronie produktu głównego.** `S` **NAJPILNIEJSZE**
  `PRODUKT_GLOWNY_Google_Ads_bez_przepalania.md` wiersz 20.
  Przepisać otwarcie tak, żeby inżynier był pierwszy. Liczba dwudziestu lat zostaje - błędem
  jest kolejność i to, czym się przedstawiasz. **Tekst napiszę, Ty zatwierdzasz przed zapisem.**

- [ ] **4. A2: „10 lat" kontra „dwadzieścia lat".** `S`
  `TNM_o-mnie_copy_v3.5.md` wiersz 31. Ujednolicić do dwudziestu, zgodnie z kanonem.

- [ ] **5. A3: polityka prywatności opisuje stan, który minął.** `S`
  Dwa pliki: `TNM_Polityka_Prywatnosci_v1.md` i `GHL_Build_v3\pages\polityka-prywatnosci.md`.
  Przepisać punkt o cookies: GA4 z Consent Mode jako stan **obecny**, nie przyszły; podać
  identyfikator i okres. Przy okazji **zdjąć baner „v1.0 do weryfikacji w 14 dni"** - backlog
  zamknął tę weryfikację 29/05.
  *Przypominam: samo wdrożenie jest poprawne, nie ma śledzenia bez zgody. To poprawka tekstu.*

- [ ] **6. A5: trzy różne ceny wejścia w plikach uznanych za aktualne.** `S` **DECYZJA TWOJA**
  2 000 zł (spec v3, Home copy) kontra 497 zł (blok ankiety) kontra drabina 497-697-997-1297.
  **Nie podejmę tej decyzji za Ciebie.** Powiedz, która cena obowiązuje - dopiszę ją w nagłówku
  każdego z tych plików jako jedyne źródło.

- [ ] **7. A4: stary PDF z wymyśloną liczbą klientów.** `S`
  `google_ads_kompendium_2026.pdf` ma zdanie „z doświadczeń z setkami lokalnych firm
  usługowych". PDF-a nie da się poprawić, więc jedyna naprawa to **nie wysyłać go** -
  nowszy `google_ads_bez_przepalania.pdf` tego zdania nie ma. Formalnie pozycja grupy B.

---

## III. DŁUG, KTÓRY BOLI NAJSZYBCIEJ

- [ ] **8. D-002: dwa testy zależne od zegara.** `S`
  `test_kadencja_sufit.py` i `test_reslot.py` padają zależnie od pory dnia, na czystym HEAD.
  **Dlaczego chcę to zrobić:** czerwony test, który zawsze jest czerwony, uczy ignorowania
  czerwonych testów. Naprawa jest ta sama w obu: wstrzyknąć zegar zamiast `datetime.now()`.

- [ ] **9. D-011: 61 sierot w `engagement_log`.** `M`
  Wpisy bez `contact_id` i bez `pipeline_id` - teczka ich nie pokaże przy nikim.
  Chcę spróbować dopiąć je po `author_display` z normalizacją ogonków (AP-313), a resztę
  **oznaczyć jawnie jako historyczne, nie kasować**. Najpierw podgląd, ile się dopnie.

- [x] **10. D-009 ZROBIONE 02/08. Mail Sprzedawcy lądował w kanale `Other`, tekst z teczki w `Email`.** `M`
  Ten sam kanał ma w księdze dwie etykiety. Nie ruszałem, bo ta wartość jest kluczem
  dopasowania przy unieważnianiu gotowców - podmiana bez migracji istniejących wierszy
  odtworzyłaby wadę StandART z 24/07. Wymaga jednego kroku: słownik + migracja razem.

---

## IV. KOLEJKA MANAGERA (czeka na jego sygnał, nie na Twój)

- [ ] **11. Walidacja długości postów + pole formatu.** `M`
  Manager wstrzymał do czasu, aż CM zacznie produkować jednoczęściowo. Kolejka X nadal pusta.

- [ ] **12. Rozsuwanie części przy przesunięciu terminu.** `M`
  Ostatnia pozycja z jego kolejki po salwie slotów z 28/07.

---

## V. CZEGO NIE PROPONUJĘ ROBIĆ TERAZ, ŻEBYŚ WIEDZIAŁ, ŻE PAMIĘTAM

- **Wielomarkowość kodu (D-013).** 107 miejsc filtruje `brand_id`. Warunek wejścia ustaliłeś
  sam: **po pierwszej zamkniętej sprzedaży.**
- **D-010** (trzy kolumny na stan w `contacts`), **D-012** (mapowanie marka → korzeń katalogu),
  **D-001** (reguła weekendowa w jednym z czterech miejsc), **D-006/D-008** (`dispatching`
  do przemianowania), **D-003** (pola kontaktowe lejka bez ręcznego zapisu),
  **D-004** (rejestr materiałów per prospekt), **D-005** (stare karty klikalne),
  **D-007** (operacja hurtowa bez śladu).
- **Grupy B i C z audytu** - 51 pozostałych pozycji. Sam powiedziałeś: reszta poczeka.

---

## Moja rekomendacja, gdybyś chciał jedno zdanie

Zrób **1, 3 i 5**. Punkt 1 domyka most, który dziś jest w połowie. Punkt 3 kosztuje pół godziny,
a naprawia tekst, który czyta klient przed zakupem. Punkt 5 to jedyna pozycja z jakąkolwiek
konsekwencją formalną. Reszta może czekać bez szkody.
