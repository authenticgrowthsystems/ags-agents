# ODPOWIEDŹ Managera - 22.08.2026: SPEC CM-PARTNER v1 zatwierdzona w całości

Zapis decyzji, nie parafraza. Specyfikacja: `docs/cm/SPEC_CM_PARTNER_v1_22082026.md`.

## Zatwierdzone bez zmian

D1 (routing na poziomie resolwera, 13 punktów, brak wpisu pada w stronę działającego bota),
D2, D3, D4 oraz sekcja „czego v1 nie robi".

## P2 - dwa wątki na start

**Content i Sprzedaż.** Reszta dokładana **dopiero po weryfikacji prawdziwą wiadomością w obu**.

## P3 - TAK, odprawa działa po oknie czasowym

**To jest rozszerzenie D-D, nie nowa zasada.** Cytat D-D (14.08, decyzja Tomasza):
*zgoda człowieka przestaje być warunkiem publikacji, a staje się prawem weta w oknie czasowym*.

Parametry:
- odprawa wychodzi **rano**, okno weta **do 12:00**, po nim **plan dnia wykonuje się sam**;
- **walidator języka i gatunku (AP-315) blokuje zawsze i bezwarunkowo** - okno go nie dotyczy;
- **spod auto-wykonania wyłączone:** treści sprzedażowe imienne oraz pozycje, które **CM sam
  oznaczy jako wymagające decyzji** (eskalacja zamiast domysłu);
- **każda auto-akceptacja dostaje wpis w rejestrze z powodem „okno minęło"**, żeby ślad
  odróżniał **klik Tomasza od jego milczenia**.

> Budujemy partnera, nie formularz.

**Uwaga BE do punktu czwartego, bo to jest mocniejsze, niż wygląda.** Rozróżnienie „klik kontra
milczenie" jest warunkiem, żeby pętla nauki `decisions` nie uczyła się na ciszy. Dziś
`agent_learning_log` liczy zgodność rekomendacji z decyzją człowieka i po progach proponuje
`semi_autonomous`. Gdyby auto-akceptacja liczyła się jak zgoda, **system uznałby brak czasu
Tomasza za poparcie dla swoich rekomendacji** i sam awansował się do większej autonomii.
Wpis z powodem to zamyka. Zapisuję jako warunek odbioru.

## P1 - migracja do supergrupy: osobny, opisany krok

Zamówiony przez Managera i wykonany: **`docs/ops/MIGRACJA_SUPERGRUPA.md`** - lista miejsc,
gdzie zmienią się `chat_id`, aktualizacja `brand_config`, test ścieżki alarmu.

**Ryzyko 2 przyjęte jako WARUNEK ODBIORU, nie dodatek:** dziś jedno źródło adresu obsługuje cały
system i nie ma testu, który by go pilnował.

## Ryzyko 3 - koszt rekomendacji przy 43 pozycjach: POLICZONY

Stawki z `config.MODEL_RATES`, przelicznik `USD_PLN = 4.0`. Narzut 30 % dla Sonnet 5 doliczony
zgodnie z komentarzem w `config.py:37`.

| model | tryb | wejście | wyjście | USD | PLN |
|---|---|---:|---:|---:|---:|
| haiku | **partiami** | 6 660 | 1 720 | 0,0153 | **0,06** |
| haiku | po jednej | 69 660 | 1 720 | 0,0783 | 0,31 |
| sonnet | partiami | 8 658 | 2 236 | 0,0595 | 0,24 |
| sonnet | po jednej | 90 558 | 2 236 | 0,3052 | 1,22 |
| opus | partiami | 6 660 | 1 720 | 0,0763 | 0,31 |
| opus | po jednej | 69 660 | 1 720 | 0,3913 | 1,57 |

**Wniosek, i jest inny niż zakładało pytanie: koszt NIE JEST ograniczeniem.** Najdroższy wariant
- Opus, po jednej pozycji, cała siedmiotygodniowa zaległość naraz - to **1,57 zł jednorazowo**.
W stanie ustalonym (kilka nowych pomysłów dziennie) to grosze.

**Ale rachunek pokazał coś, czego pytanie nie obejmowało:** tryb **partiami oszczędza 90 %
tokenów wejścia**, bo kontekst marki i kryteria idą raz zamiast czterdziestu trzech razy.
I ważniejsze od pieniędzy: **w jednym wywołaniu model widzi wszystkie pozycje naraz**, więc może
powiedzieć „te trzy to ten sam temat, zostaw jedną" - czego przy ocenie po jednej fizycznie
nie ma jak zrobić.

**Rekomendacja BE: partiami, tier `haiku`.** Nie z powodu ceny, tylko dlatego, że ocena „do
kolejki czy odrzucić" na temacie i kanale jest zadaniem klasyfikacyjnym, a nie strategicznym.
Jeśli jakość okaże się za niska, podniesienie do `sonnet` kosztuje 18 groszy więcej.

**Prawdziwym ryzykiem jest D-023, nie koszt.** Przy wyczerpanych środkach API każda ścieżka
modelu pada po cichu do logu. Fallback „bez rekomendacji z jawnym dopiskiem" (zatwierdzony)
jest właściwą odpowiedzią i **musi być przetestowany złym wsadem**, a nie tylko zaprojektowany.

## Kolejność - bez zmian

1. **Jutrzejsze poranne okno bezpieczeństwa:** D-017, rotacja tokenu Telegrama, rotacja kluczy X
   (D-027), potem sekret Łącznika (D-026).
2. **Budowa CM-PARTNER v1 po nim.**

Migracja do supergrupy (P1) wymaga decyzji Tomasza i może iść równolegle do budowy, byle przed
weryfikacją wątków prawdziwą wiadomością.
