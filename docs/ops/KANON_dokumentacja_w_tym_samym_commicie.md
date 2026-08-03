# KANON: dokumentacja idzie w tym samym commicie, w KAŻDYM buildzie

**Ustanowiony 03/08/2026 decyzją Tomasza.** Podniesione z punktu 8
`docs/ops/RUNBOOK_migracje.md`, który obowiązywał wyłącznie migracje danych.
**Od dziś obowiązuje każdy build.**

---

## Reguła

> **Zmiana bez dokumentacji nie jest skończona. Dokumentacja idzie w TYM SAMYM commicie
> co kod, nie w następnym i nie „jak będzie chwila".**

## Dlaczego to powstało

`docs/SYSTEM_DATAFLOW.md` był ostatni raz ruszony **27/07/2026**. Przez następny tydzień,
najbardziej pracowity w historii projektu, mapa systemu nie dostała ani jednej linii.
Nie ma w niej: teczki prospekta, mostu katalogi-baza, etykiety `marka_docelowa`, rejestru
`bulk_operations`, dziesięciu zamkniętych długów, walidacji długości, pola `post_queue.format`,
zniesienia serii X ani przemianowania `dispatching` na `handed_off`.

**Mapa opisywała stan sprzed tygodnia i nikt tego nie zauważył, bo nikt do niej nie zaglądał.**

Przyczyna nie jest lenistwem. Jest nią wzorzec: **dokumentację pisze się wtedy, gdy JEST
produktem zadania** (runbook, anty-wzorzec, dokument komponentu, brief), a nie wtedy, gdy jest
**skutkiem ubocznym** zbudowanej rzeczy. Zadanie „zamknij dług D-006" nie brzmi jak zadanie
dokumentacyjne, więc dokumentacja nie powstaje.

To ta sama rodzina co reguła brania długu (`docs/ops/DLUG_TECHNICZNY.md`) i AP-311:
**zapis przestaje opisywać rzeczywistość, a wygląda tak samo jak zapis aktualny.**

## Co dokładnie trzeba ruszyć

Nie każdy commit rusza wszystko. Przed zamknięciem buildu przejdź trzy pytania:

1. **`docs/SYSTEM_DATAFLOW.md`** - czy zmiana dotyka przepływu danych? Nowa tabela, nowa
   kolumna, nowy pisarz, nowy endpoint, nowy stan w słowniku, zmiana kto-do-kogo-pisze?
   Jeśli tak, mapa MUSI to mieć.
2. **`docs/komponenty/<nazwa>.md`** - czy powstał nowy moduł albo zmienił się KONTRAKT
   istniejącego (sygnatury, wejścia, wyjścia, stany)? Te dokumenty czyta się ZAMIAST kodu,
   więc rozjechany dokument komponentu jest gorszy niż jego brak.
3. **`docs/ops/DLUG_TECHNICZNY.md`** - czy zamykasz dług albo zakładasz nowy? Zamknięcie
   z datą, założenie z plikiem i linią.

## Bramka

**W meldunku kończącym build nazwij, KTÓRY dokument ruszyłeś.** Jeśli żaden - napisz wprost
„dokumentacja bez zmian" i podaj powód. Zdanie musi paść świadomie, bo cisza w tym miejscu
wygląda dokładnie tak samo jak brak potrzeby.

**Build bez tego zdania nie jest zgłoszony jako skończony.**

## Dług, który ta reguła zostawia otwarty

Sama reguła nie nadrabia zaległości. Do zrobienia osobno:

- odświeżenie `docs/SYSTEM_DATAFLOW.md` o tydzień zaległości (27/07 - 03/08);
- `docs/komponenty/operacje.md` - moduł `operacje.py` (rejestr `bulk_operations`) powstał
  02/08 i nie ma własnego dokumentu.

## Powiązania

- `docs/ops/RUNBOOK_migracje.md` punkt 8 - wersja wąska, dla migracji danych.
- `docs/ops/DLUG_TECHNICZNY.md`, nagłówek - reguła brania długu (ta sama choroba, inny zapis).
- `docs/anti-patterns/AP-311...` - obecność zapisu nie jest dowodem, że zapis jest prawdziwy.
