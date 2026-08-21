# ODPOWIEDŹ Managera po przygotowaniu bloków D i E - 19.08.2026

Zapis decyzji, nie parafraza.

## 1. Rotacja tokenu: NIE w oknie, rekomendacja BE przyjęta

> Tokenu w oknie NIE rotujemy, Twój argument przyjęty, rotacja jako osobny krok po 24h
> stabilności z weryfikacją prawdziwą wiadomością.

Argument, który Manager przyjął: po zmianie z D-017 rotacja przestaje wymagać dotykania 44 węzłów
i staje się jednym `UPDATE` w `app_secrets`. Argument z długu („skoro i tak trzeba tam wejść")
przestaje więc obowiązywać. Mieszanie dwóch zmian w jednym oknie na **jedynym interfejsie Tomasza**
kosztuje możliwość odróżnienia, która z nich zawiodła, gdyby bot zamilkł.

**Jedna zmiana, jeden dowód, jedna droga cofnięcia.**

Wykonane po tej decyzji: rozstrzygnięcie wpisane do `docs/ops/OKNO_D017_przygotowane.md`
(bo dokument INSTRUKTAŻOWY jest wykonywany, nie oceniany - AP-316) oraz do wpisu D-017
w `docs/ops/DLUG_TECHNICZNY.md`.

## 2. Luka zmiany terminu: zarejestrowana jako D-025, po oknie

Pełny wpis w `docs/ops/DLUG_TECHNICZNY.md`. Rzecz, która czeka i jest przeterminowana: spotkanie
z Grupą Chwalinski 03.09.2026 jest o **9:00**, a w bazie wisi **11:00**, i nikt tego nie poprawił,
bo nie ma czym.

Sedno luki jednym zdaniem: **żeby poprawić samą liczbę, trzeba dziś skłamać w dzienniku** -
`teczka.zapisz` wymaga niepustej treści i kanału, więc zmiana godziny wymusza wymyślenie
fikcyjnego wpisu do `engagement_log`.

Trzy warunki wykonania zapisane do długu, żeby nie zginęły:
1. **stara wartość musi wrócić w potwierdzeniu** („było 11:00, jest 9:00") - dziś nadpisanie jest
   ciche, a cicha zmiana daty to dokładnie mechanizm, którym 11:00 się tam znalazło;
2. **pochodzenie nowej godziny musi zostać zapisane** (AP-317), bo `next_followup_at` go nie niesie;
3. `_ustaw_krok` używa `COALESCE`, więc **terminu nie da się skasować** - do rozstrzygnięcia,
   czy to wada.

Plus zależność, którą trzeba zamknąć **razem** z D-025: `sales._find_pipeline` nadal nie
normalizuje ogonków, więc `pipeline_move("Chwalinski")` nie trafi w „Grupa Chwaliński" (AP-313).
To jest dokładnie ta nazwa, której dotyczy czekający przypadek.

## 3. Korekta AP-317 przyjęta

> Korekta AP-317 przyjęta, dobra robota z własnym liczeniem 44 węzłów.

Przypis o spotkaniu 03.09 przypisywał je „Markowi Sroce"; źródło mówi Chwaliński, a Sroka
występuje w tym samym dokumencie w innej sprawie i pod inną datą. Poprawione z jawnym śladem,
razem z regułą wyprowadzoną z tego przypadku: **przy nazwisku w dokumencie kanonicznym wracaj
do źródła, nawet gdy zdanie brzmi spójnie**, a przy dwóch sąsiadujących faktach o różnych ludziach
zakładaj, że łatwo je skleić.

---

## STAN PO TEJ ODPOWIEDZI

- **Gotowe do jednego okna n8n:** D (D-017) i E (D-021, rejestracja narzędzia plus tap-test).
  Okno będzie krótkie, bo skrypt i procedura są sprawdzone offline.
- **Po oknie:** wdrożenie bloku G (czeka na rebuild), rotacja tokenu po 24 h stabilności, D-025.
- **Blok H** (D-024, `channels.config.rules`) po D+E, zgodnie z decyzją Z-2.
- **Blok A** robi Tomasz ręcznie.
