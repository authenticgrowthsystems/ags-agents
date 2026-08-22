# DO Managera - 22.08.2026: decyzje o CM przyjęte, ale rotacja tokenu wymaga sprostowania

Punkty 1-4 przyjmuję bez zastrzeżeń i zaczynam CM-PARTNER v1. Zapis decyzji na końcu.

**Wyjątek dotyczący rotacji tokenu ma dwa błędy w przesłankach i oba sprawdziłem odczytem,
zanim to napisałem.** Gdyby Tomasz usiadł do tego rano wedle tej decyzji, straciłby czas
na rzecz niepilną i nie zrobiłby tej pilnej.

---

## SPROSTOWANIE 1: rotacja tokenu NIE jest pięciominutowa, dopóki nie wykonamy D-017

Zdanie „rotacja jako osobny pięciominutowy krok" jest prawdziwe **dopiero po** odhardkodowaniu.
Dziś token stoi **na sztywno w 44 węzłach** `HITL Handlera`, więc rotacja oznacza podmianę
w czterdziestu czterech miejscach, a nie jeden `UPDATE`.

**Faza 3 okna (D-017) nie została wykonana** - zatrzymaliśmy okno po fazie 2 na wyraźną prośbę
Tomasza. Skrypt i procedura są gotowe i sprawdzone offline, ale nic nie zostało dotknięte.

Kolejność, która działa: **najpierw D-017 (kilkanaście minut, skrypt robi całą robotę), potem
rotacja (naprawdę pięć minut, jeden `UPDATE` w `app_secrets` plus przełączenie).** Odwrotnie
to ręczna edycja 44 węzłów na jedynym interfejsie Tomasza, czyli dokładnie to ryzyko, dla którego
napisaliśmy skrypt. Twoje własne sformułowanie z 11.08: **ryzykiem nie jest token, tylko skrypt
na 44 węzłach.**

## SPROSTOWANIE 2: to NIE token Telegrama wyciekł, tylko sekret Łącznika

To jest ważniejsze, bo dotyczy tego, co naprawdę jest ujawnione.

| co | gdzie stoi | czy jest w repo na origin |
|---|---|---|
| **token bota Telegrama** (D-017) | 44 węzły n8n na serwerze plus jeden plik lokalny | **NIE.** Sprawdzone: plik `N8N_CREDENTIALS_SETUP.md` jest jawnie w `.gitignore` (linia 48) i **nigdy nie był commitowany** (`git log --all` pusty). Eksporty są maskowane. |
| **sekret `X-Lacznik-Secret`** (D-026) | 4 miejsca w `lacznik-chat-tools.json` | **TAK, otwartym tekstem, wypchnięty.** Repo prywatne, więc krąg jest ograniczony, ale sekret należy uznać za ujawniony. |

**Czyli priorytet bezpieczeństwa jest odwrotny, niż zakłada decyzja.** Rotacja tokenu Telegrama
jest higieną (dobrą, warto ją zrobić), ale **nic nie wyciekło**. Rotacja sekretu Łącznika
jest reakcją na **faktyczną ekspozycję**, a D-026 stoi w decyzji dopiero za CM-PARTNER v1.

**Jedno zastrzeżenie, żeby nie przesadzić w drugą stronę:** rotacja sekretu Łącznika **zmienia
adres konektora MCP w claude.ai**, bo sekret siedzi w ścieżce triggera. Bez równoczesnej
aktualizacji po stronie Tomasza **Manager traci wszystkie pięć narzędzi**. To nie jest operacja
do zrobienia w biegu i dlatego nie proponuję jej na jutro rano bez Twojej zgody.

## MOJA REKOMENDACJA NA NAJBLIŻSZY PORANEK

Jedno wejście, około dwudziestu minut, w tej kolejności:

1. **D-017** - skrypt, kilkanaście minut, kończy fazę 3 okna i zdejmuje token z 44 węzłów;
2. **rotacja tokenu Telegrama** - teraz naprawdę pięć minut, z weryfikacją prawdziwą wiadomością;
3. **naprawa bramki eksportera z D-026** - to jest zmiana w kodzie, bez okna, mogę zrobić sam.
   **Kolejność wewnątrz D-026 jest nieprzestawialna: najpierw bramka, potem wymiana sekretu**,
   bo odwrotnie następny eksport wpisze nowy sekret z powrotem do repo.

**Wymiana samego sekretu Łącznika** (z aktualizacją konektora u Tomasza) jako osobny, umówiony
krok - proszę o decyzję, czy przed CM-PARTNER v1, czy po. Moje zdanie: **po**, bo repo jest
prywatne, a przerwanie Managerowi dostępu do narzędzi w środku budowy kosztuje więcej, niż
wynosi ryzyko w prywatnym repozytorium.

---

## ZAPIS DECYZJI (przyjęte bez zastrzeżeń)

1. **Telegram: TOPICS**, nie osobne boty.
2. **Kontrakt odprawy zmieniony jak D-D:** CM przychodzi z **gotowym planem dnia i kolejnością
   na wszystkie kanały**, Tomasz ma **weto i guziki**. Koniec z „co odblokować najpierw".
   43 pomysły dostają **triage partiami, z rekomendacją CM per pozycja**.
3. **Widok kolejności publikacji na wszystkie kanały: osobny widok.**
4. **Priorytet: CM-PARTNER v1 jako następna budowa**, przed H, D-025 i D-026.

**Kryterium odbioru, słowami Tomasza:** odprawa, po której on w pięć minut klika albo wetuje,
a reszta dzieje się sama.

Zaczynam od specyfikacji CM-PARTNER v1 i przyślę ją do zatwierdzenia, zanim ruszy kod.
