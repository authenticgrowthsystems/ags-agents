# SPEC: CM-PARTNER v1 (22.08.2026) - do zatwierdzenia przez Managera

**Zatwierdzony zakres (Manager, 22.08):** Telegram Topics; kontrakt odprawy jak D-D (CM przychodzi
z gotowym planem, Tomasz ma weto i guziki); osobny widok kolejności na wszystkie kanały; triage
43 pomysłów partiami z rekomendacją CM per pozycja. Priorytet: przed H, D-025 i D-026.

**Kryterium odbioru, słowami Tomasza:** *odprawa, po której on w pięć minut klika albo wetuje,
a reszta dzieje się sama.*

---

## 0. RAMA, KTÓRA POWINNA ZOSTAĆ ZAPISANA

**To jest ta sama reklamacja, którą Tomasz złożył 30 czerwca.** Wtedy: *„Content Manager miał się
kontaktować bezpośrednio ze mną w celu ustalenia postów i planu publikacji... nie mam interfejsu
przez Telegram do CM, nie mam możliwości podglądania postów, które zaplanował. Praca jest wykonana
dopiero w 10 procentach"*. Dziś, 22 sierpnia: *„nie mam guzika zaproponuj kolejność publikacji
na wszystkie kanały, nie mam omówienia strategii"*.

Między jednym a drugim zbudowaliśmy niezawodność egzekucji: bramki, walidatory, blokady,
kilkanaście zamkniętych długów. **Każda z tych rzeczy była uzasadniona** - dwa publiczne wycieki
to nie teoria. Ale skutkiem ubocznym jest to, że przez siedem tygodni wzmacnialiśmy część,
która działała, a rdzeń produktu stoi w miejscu.

**Wniosek dla tej specyfikacji: v1 ma zamknąć pętlę decyzyjną operatora, a nie dołożyć kolejne
zabezpieczenie.** Jeśli coś w zakresie da się odłożyć bez psucia tej pętli, odkładamy.

---

## 1. STAN OBECNY - liczby z odczytu, nie z pamięci

| co | fakt | źródło |
|---|---|---|
| odprawa poranna | **w 100% deterministyczna**, trzy `COUNT`-y, zero wywołań modelu | `proactive.py:204-235` |
| guzik w odprawie | **jeden, i tylko gdy są karty** (`if cards`) | `proactive.py:232-233` |
| 43 „pomysły" | **jedna populacja**: wszystkie AGS, `meta_type` pusty, `op_id` pusty, od **06.07** do 21.08 | odczyt produkcji 22.08 |
| przegląd pomysłów | `/decyzje`, limit **6**, wysyła 6 osobnych wiadomości, `brand_id` na sztywno | `matreview.py:1046-1055` |
| droga do `/decyzje` | **żaden guzik tam nie prowadzi**; komenda nie jest w `setMyCommands` | 55 literałów `callback_data`, węzeł `Parse Agsel Callback` |
| rekomendacja per pozycja | **zero** w intake; ale mechanizm ISTNIEJE i działa gdzie indziej | `decisions.ask(recommendation=)`, `decisions.py:137-181` |
| plan | widok całości **istnieje** (`plan_text`), 20 pozycji = dokładnie `PLAN_CAP` | `planner.py:191-209`, `planner.py:27` |
| widok kolejności na wszystkie kanały | **NIE ISTNIEJE** | sprawdzone dziewięcioma sformułowaniami |
| `message_thread_id` | **nie występuje nigdzie w kodzie** | Python i JSON-y n8n |
| adres wyjścia proaktywnego | **jeden `chat_id` na całą instalację**: `arr[0]` z `admin_chat_ids` | `hitl.py:11-19` |
| limit `callback_data` | **64 bajty, nigdzie nie udokumentowany, brak walidacji**; przy UUID zostaje 12-16 B zapasu | wyliczenie na ośmiu wzorcach |

**Rachunek, który tłumaczy „gubię się":** 43 pozycje przy limicie 6 to **osiem wywołań komendy,
której nie widać w menu**. Najstarsza czeka siedem tygodni. To nie jest kwestia dyscypliny
operatora, tylko interfejsu, który nie ma jak zostać rozładowany.

---

## 2. CZTERY DECYZJE PROJEKTOWE

### D1. Wątki: routing na POZIOMIE RESOLWERA, nie przez ~97 payloadów

Rozpoznanie dało dwie liczby: **~97 payloadów** (jeśli wątek wybiera wołający) albo **13 punktów
decyzyjnych** (jeśli wątek wynika z mapowania „agent → wątek"). **Wybieram drugie** i to jest
najważniejsza decyzja tej specyfikacji.

Uzasadnienie: `conversation._tg` jest ślepy na to, kto woła, **ale wołający zawsze wie, kim jest**.
`matreview` wysyła karty CM, `sales` wysyła sprzedaż, `planner` plan. Nie trzeba przenosić
kontekstu przez `_tg` - wystarczy, żeby **funkcja rozwiązująca adres przyjmowała agenta**.

- `hitl._admin_chat_id()` → `hitl.cel(agent)` zwracające `{"chat_id": ..., "message_thread_id": ...}`.
- Mapowanie `agent → wątek` w `brand_config` pod jednym kluczem, obok istniejącego `admin_chat_ids`.
  **Zero DDL.**
- Wołający dokleja wynik do payloadu jednym `payload.update(cel)`. **11 miejsc**, nie 97.
- **Brak wpisu dla agenta = wysyłka do wątku głównego**, nie błąd. Bramka pada w stronę
  działającego bota (świadome odstępstwo od „pada zamknięta": tu zamknięcie znaczy cisza bota,
  a cisza jest gorsza niż wiadomość w złym wątku).

**Trzy wyjścia omijają `_tg`** (`hitl.py:92`, `logbot.py:33`, multipart w `matreview.py:38,57`),
a `logbot` używa **innego bota**. Każde dostaje ten sam `payload.update(cel)` osobno - są
policzone i jest ich trzy.

**`user_agent_state` NIE zmienia klucza w v1.** Wątek dostaje wiadomości, ale aktywny agent
zostaje per `chat_id`. Powód: zmiana klucza głównego pociąga cztery zapytania w n8n i migrację,
a **prefiks adresujący** (`cm:`, `sp:`, `x:`, `li:`) już dziś rozwiązuje kierowanie pojedynczej
wiadomości i działa. Klucz złożony wchodzi w v2, jeśli okaże się potrzebny.

### D2. Odprawa: CM przychodzi z PLANEM, Tomasz wetuje

Kontrakt zmienia się dokładnie jak D-D: **zgoda przestaje być warunkiem, staje się wetem**.

Odprawa przestaje pytać „co odblokować najpierw?" i zaczyna mówić: **oto plan dnia i kolejność
na wszystkie kanały; masz weto**. Guziki: `Akceptuję wszystko` / `Pokaż kolejność` /
`Przejrzyj pomysły (43)` / `Zmieniam`.

**Odprawa zostaje deterministyczna w warstwie liczb** (trzy `COUNT`-y działają i nie ma powodu
płacić za model). Modelu używamy **wyłącznie** do rekomendacji per pozycja i do jednego zdania
uzasadnienia kolejności. Jeśli model nie odpowie, odprawa idzie bez rekomendacji, z jawnym
dopiskiem - **nigdy nie zastępujemy braku rekomendacji domysłem** (AP-317).

Naprawiamy przy okazji **niespójność złapaną w rozpoznaniu**: licznik kart liczy się per marka,
a guzik `matnav:first:-` otwiera karty **wszystkich marek**. Liczba na guziku i zawartość
przeglądu mogą się rozjechać.

### D3. Widok kolejności: jedna oś czasu, wszystkie kanały

**Nie budujemy od zera.** `reports._queue_upcoming` (`reports.py:176-187`) robi dokładnie to,
czego potrzeba, po zdjęciu jednego warunku `AND pq.platform=%s`. Do tego:

- godzina **musi** iść przez `reports._godzina_wiersza` → `worker._godzina_publikacji`
  = `max(slot planu, czas kolejki)`. To jest D-015 i nie wolno tego liczyć drugi raz;
- etykiety przez `reports._pq_label` (rozróżnia „DO ZATWIERDZENIA" od „zatwierdzone, czeka");
- brak wiersza kolejki = **karta mówi, że nie wie**, tak jak po naprawie z bloku G.

Widok pokazuje **pozycje ponumerowane** i guziki `Przesuń wyżej` / `Przesuń niżej` / `Na inny
dzień` przy pozycji. Logika układania kolejności **już istnieje** w `reslot.py` (serie w blokach,
kolejność narracyjna, siatka dnia, cap kadencji) - dziś tylko dla X i jako skrypt CLI. v1 wystawia
ją na kanały i pod guziki.

### D4. Triage partiami: identyfikator operacji, nie UUID w guziku

**Twarde ograniczenie: w `callback_data` mieści się 64 bajty, a przy UUID zostaje 12-16.
Dwa UUID-y się nie zmieszczą.** To wyklucza „zaznacz kilka i zatwierdź" w naiwnej postaci.

Rozwiązanie wykorzystuje to, co jest: **`operacje.py`** (rejestr operacji hurtowych, D-007)
nadaje `op_id` i stempluje nim wiersze. Partia to **jedna zarejestrowana operacja**:

1. CM proponuje partię (np. 10 pozycji) z rekomendacją per pozycja przez `decisions.ask`;
2. guzik niesie **`op_id` (liczba) plus indeks**, nie UUID-y - mieści się z zapasem;
3. `Zatwierdź całą partię wg rekomendacji` to jeden guzik na dziesięć pozycji;
4. **odstępstwa idą pojedynczo** - Tomasz zmienia tylko te, z którymi się nie zgadza.

To jest ta sama figura co „zatwierdź wszystkie" przy kartach i planie, tylko z rekomendacją
i z rejestrem, który pozwala operację odczytać i cofnąć.

---

## 3. CZEGO v1 NIE ROBI (świadomie)

- **Nie zmienia klucza `user_agent_state`** - patrz D1.
- **Nie rusza `logbot`** poza doklejeniem celu; drugi bot zostaje jako kanał logowy.
- **Nie buduje planera na dwa miesiące** z wizji z 30.06. v1 domyka DZIEŃ, nie kwartał.
- **Nie dotyka D-017, D-026 ani D-027** - to osobne kroki bezpieczeństwa.

---

## 4. RYZYKA

1. **Topics wymagają grupy, nie czatu prywatnego.** Migracja rozmowy do supergrupy z wątkami
   to zmiana po stronie Telegrama, którą wykonuje Tomasz, i **wszystkie `chat_id` się zmienią**.
   To jest jednorazowy koszt, ale musi być zaplanowany, nie odkryty w trakcie.
2. **`admin_chat_ids` ignoruje wszystko poza `arr[0]`** - dziś to jedno źródło adresu dla całego
   systemu. Zmiana dotyka jedenastu wołających i nie ma testu, który by ją pilnował. **Test
   ścieżki alarmu jest warunkiem odbioru**, nie dodatkiem.
3. **Rekomendacja CM per pozycja kosztuje wywołania modelu przy 43 pozycjach.** Trzeba policzyć
   koszt przed wdrożeniem i przewidzieć zachowanie przy wyczerpanych środkach (D-023).

---

## 5. PYTANIA DO MANAGERA

1. **Czy Tomasz jest gotów przenieść rozmowę z botem do supergrupy z wątkami?** Bez tego Topics
   nie istnieją, a wszystkie `chat_id` się zmienią. To jedyna rzecz w tej specyfikacji, która
   wymaga jego działania **przed** budową.
2. **Czy v1 ma objąć wszystkie działy, czy zaczynamy od dwóch wątków** (Content, Sprzedaż)
   i dokładamy resztę po sprawdzeniu? Rekomendacja BE: **dwa wątki**, bo mapowanie agent → wątek
   jest wtedy trywialne do sprawdzenia prawdziwą wiadomością.
3. **Czy odprawa ma prawo publikować bez odpowiedzi Tomasza po oknie czasowym**, tak jak D-D
   ustanowił dla publikacji? Jeśli tak, v1 domyka pętlę naprawdę. Jeśli nie, odprawa nadal czeka
   na człowieka i kryterium odbioru („reszta dzieje się sama") nie zostanie spełnione.

**Pytanie 3 jest najważniejsze i od niego zależy, czy budujemy partnera, czy ładniejszy formularz.**
