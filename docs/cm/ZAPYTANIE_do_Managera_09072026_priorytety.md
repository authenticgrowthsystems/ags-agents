# ZAPYTANIE do Managera AGS - priorytety po zamknieciu sprintu (09/07/2026)

Od: BUILD ENGINEER. Cel: ustawic kierunek nastepnych 2-3 sesji. Prosze o decyzje w 3 punktach
(na koncu kazdego punktu format odpowiedzi).

## Meldunek stanu (skrot, pelne raporty w docs/cm/)

1. **Zadanie 3 (routing zdjec per active_agent): WDROZONE + PRZETESTOWANE E2E 08/07.**
   Subagent aktywny + zrzut posta -> propozycje komentarzy per autor (wizja);
   default -> triage Idea Bota; tryb Media ma pierwszenstwo. HITL stabilny.
2. **PONAD ZLECENIE (wymog Tomasza 08/07): warstwa decyzji pod propozycjami komentarzy.**
   Guziki ✅ Zatwierdz / 🔄 Inny kat / ❌ Odrzuc; kazda decyzja trwale w DB
   (engagement_log.notes); zatwierdzone laduja w task_queue jako task_type='comment'
   (kolejka wykonania). Inny kat = regeneracja (wizja lub tekst) z nowymi guzikami.
3. **Regresja: zero szkod.** Pelny legacy rurociag Idea Bota (zdjecie -> triage -> Research ->
   synteza -> Seria 5 postow PL+EN -> decyzje per post) dziala nietkniety - dowod:
   screenshoty Tomasza z 08/07.
4. **#71 pozostaje CLOSED**, sync iteracyjny na Zadaniu 1 (3 tabele enabled), drift czysty.

Wszystko pushniete (HEAD fc2884b). Po stronie Tomasza zostal 1 rebuild kontenera +
1-minutowy tap-test guzikow.

## Pytanie 1: priorytet nastepnych 2-3 sesji

Rekomendacja BE (kolejnosc):
1) **X obraz w tweecie** - jedyny znany otwarty defekt publikacji. Dowod z egzekucji przy
   najblizszej publikacji X z obrazem, naprawa z dowodu (exec saving juz wlaczony).
2) **Sync #71 aftercare**: page_map dla tabel append + Zadanie 2 (agent_approval_gates)
   wg SYNC_ENABLE_PLAN - domyka wartosc migracji.
3) **Task #70 refresh**: playbook + diagram uzupelnione o SSOT/sync_registry
   (pakiet sprzedawalnosci - argument sprzedazowy "SSOT w 1 dzien").

Alternatywy do przetasowania: konsument kolejki komentarzy (pytanie 2), subagenty wizualne
T6 (research-first - najwiekszy brak produktowy wg definicji subagenta), Newsletter #6.

**Odpowiedz: APPROVE kolejnosci 1-2-3 / wlasna kolejnosc.**

## Pytanie 2: konsument kolejki komentarzy

Zatwierdzone komentarze laduja dzis w task_queue i CZEKAJA - nie ma wykonawcy. Opcje:

- **A) Semi-auto (rekomendacja BE):** subagent podaje Tomaszowi gotowy komentarz + odnosnik
  do posta w jednej wiadomosci, Tomasz wkleja recznie (2 klikniecia). Zero ryzyka konta,
  zgodne ze strategia comment-first i limitami platform; do zbudowania w 1 krok.
- **B) Auto przez API:** X write API (ryzyko konta + koszty), LinkedIn komentarze wymagaja
  scope z App 2 CMA (jeszcze w review). Odlozylbym do czasu App 2.
- **C) Nic nie budowac teraz** - kolejka czeka na decyzje przy metrykach/API.

**Odpowiedz: A / B / C.**

## Pytanie 3: Re-Intro hard-block (Voice Bible v2.1, task #75)

Mechanizm WARN dziala (compliance loguje, nie blokuje). Rekomendacja BE: przelaczyc na
hard-block po 3 postach LinkedIn bez falszywych alarmow.

**Odpowiedz: APPROVE / inny prog / zostaje WARN.**
