# PRZEKAZANIE: stan na koniec 02/08/2026

**Od:** BE → **Do:** następnej sesji (i Managera AGS).
**Serwer i repo: `0a89a04`. DDL do 039. Testy 21/21.** Kolejka X nadal pusta.

---

## 1. Co się zmieniło w jeden dzień

**Dziewięć długów zamkniętych.** Otwarte zostały pięć, z czego trzy są zablokowane świadomie.

| dług | jak zamknięty |
|---|---|
| D-001 | `slots.day_ok()` - jedna reguła, wołana z czterech tras zapisujących slot |
| D-002 | pośrednictwo `_teraz()`; testy zero odwołań do zegara systemowego |
| D-003 | pola kontaktowe w `pipeline_add`/`pipeline_move`; osoba widoczna **pierwsza** |
| D-005 | **samoleczenie** - martwa karta rozbraja się przy pierwszym tapnięciu |
| D-006 | `_stan_rozsylki()` + etykieta „ROZESLANY DO KOLEJKI" zamiast „W PUBLIKACJI" |
| D-009 | słownik + migracja 9 wierszy w jednym oknie, przy zatrzymanym pisarzu |
| D-010 | `COMMENT ON COLUMN` (DDL 039), świadomie **bez** `DROP` |
| D-011 | **nie było wady** - odczyt obalił przesłankę mojego własnego wpisu |
| D-014 | para `(action_type, channel)` w jednym słowniku `_ENG_KANALY` |

Do tego: **teczka prospekta** (para MCP), **most katalogi-baza**, **etykieta marki TNM**,
**rotacja sekretu Łącznika**, **audyt 124 plików TyNieMusisz** i naprawa grupy A.

## 2. Trzy rzeczy, które zmieniają sposób pracy

**RUNBOOK MIGRACJI** (`docs/ops/RUNBOOK_migracje.md`) - osiem zasad, do czytania **przed** każdą
migracją. Powstał, bo w `docs/ops/` leżało dziesięć plików jednorazowych migracji i zero
runbooków. Dwie zasady zgłosił Manager **po udanym wdrożeniu**, nie po wpadce:
`gunzip -t` zanim zatrzymasz pisarza, oraz świadomość, że łańcuch `&&` chroni dane, ale **nie
chroni dostępności** - a najbardziej prawdopodobnym wyzwalaczem przerwania jest **własna bramka**.

**AP-313** - założenie ASCII przy polskich nazwach własnych. `ILIKE '%Chwalin%'` nie trafia
w „Chwaliński". Groźny, bo pierwszy przebieg działa, a kontrola napisana tym samym wzorcem jest
ślepa tak samo. **Narzędzie do wykrycia błędu miało ten sam błąd.**

**AP-309 rozszerzony o stronę szukania** - grep na jedną frazę zaniża liczbę trafień, gdy dwa
dokumenty mówią to samo innymi słowami. Szukaj **pojęcia, nie frazy**; minimum trzy sformułowania.

## 3. Wzorzec, który powtórzył się sześć razy

**Wzorzec dopasowania to założenie o danych, nie fakt o nich.** Za każdym razem, gdy szukałem
wady jednym wzorcem, znajdowałem mniej wystąpień, niż było: etykieta zamiast treści maila,
parametr `kontakt` zamiast `contact_id`, `%Chwalin%`, cztery sformułowania o analityce, trzeci
„choreograf", kształt kanału (napis kontra lista) w `day_ok`.

**Drugie:** dług opisany raz i nieodświeżany starzeje się tak samo jak kod. D-003 miał notatkę
„dziś uśpiona" z 26/07; 02/08 objaw był już żywy - 33 wiersze z osobą zamiast zera.

**Trzecie:** przy dwóch długach odczyt **obalił przesłankę wpisu**. D-011 nie był wadą (61
„sierot" to zapisy własnej aktywności, których nie czyta żaden licznik), a D-005 był naprawialny
inaczej, niż wpis zakładał. Warto czytać przed naprawą także własne notatki sprzed tygodnia.

## 4. Co zostało otwarte

- **D-007** - operacja hurtowa nie zostawia śladu czytelnego dla drugiego agenta.
  Jedyny realnie wykonalny dług, jaki został.
- **D-008** - przemianowanie **wartości** `dispatching`. 30 miejsc w kodzie (9 plików),
  `CHECK` w trzech plikach DDL, węzły SQL w n8n. Warunek z własnego wpisu: **osobne okno**.
  **Najlepszy kandydat na osobną instancję Claude Code z briefem** - jest samodzielny,
  ma jasne granice i wymaga dyscypliny, nie kreatywności.
- **D-004, D-013** - zablokowane do pierwszej zamkniętej sprzedaży (decyzja Tomasza).
- **D-012** - mapowanie marka → korzeń katalogu, czeka na wielomarkowość.
- **Grupy B i C z audytu TyNieMusisz** - 51 pozycji, decyzja Tomasza: poczekają.

## 5. Jedna rzecz niedomknięta, powiedziana wprost

Naprawa D-005 działa dla kart, które mają zapisany `tg_message_id`. Karta sprzed wprowadzenia
tego zapisu zostanie klikalna, jeśli n8n nie przekaże `message_id` w treści callbacku -
komunikat mówi wtedy „zdjąłem guziki, o ile znam jej numer". Domknięcie jest tanie (dodanie
`message_id` do payloadu w workflow HITL), ale wymaga PUT do n8n, więc nie weszło w to okno.

## 6. Model pracy, ustalony 02/08

Każdy build robi **osobna instancja Claude Code**; ta rola **koordynuje i audytuje**.
D-008 jest pierwszym naturalnym kandydatem do oddania.
