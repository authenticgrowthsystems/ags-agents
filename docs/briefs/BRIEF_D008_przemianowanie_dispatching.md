# BRIEF: D-008, przemianowanie statusu `dispatching`

**Dla:** osobnej instancji Claude Code. **Od:** BE (koordynacja i audyt).
**Data briefu:** 02/08/2026. **Punkt startu: repozytorium na `2f5b5cc`, DDL do 041, testy 23/23.**

> Ten build robi się **w jednym oknie, od początku do końca**. Nie zaczynaj, jeśli nie masz
> na niego całej sesji - zmiana w połowie zostawia system, który częściowo szuka starej
> wartości, a częściowo nowej, i **to jest gorsze niż myląca nazwa, którą naprawiamy**.

---

## 1. Co jest nie tak

`content_items.status = 'dispatching'` brzmi jak stan **przelotny** („wysyłam"), a znaczy
„rozesłane do kolejki, czekam aż WSZYSTKIE wiersze serii osiągną stan terminalny" - czyli stan,
który normalnie trwa **dni**.

27/07 Manager zgłosił zawieszony post. Odczyt pokazał siedem materiałów w tym stanie,
**wszystkie zdrowe**; najstarszy siedział 51 godzin i było to poprawne, bo jego sloty sięgały
4 sierpnia. Manager wyciągnął rozsądny wniosek z mylącej etykiety - dokładnie tak, jak Agent
Sprzedaży przy „BRAK następnego kroku".

To jest **AP-312** (nazwa obiecuje co innego, niż znaczy) w najczystszej postaci.

**Część widokowa jest już naprawiona (D-006, 02/08)** - karta pokazuje, ile wierszy czeka
i na kiedy, a etykieta wyświetlana brzmi „ROZESLANY DO KOLEJKI". **Zostaje sama WARTOŚĆ
w bazie i w kodzie.** To jest zakres tego briefu.

## 2. Kandydaci na nazwę

Z wpisu w długu: `w_kolejce`, `rozeslane`, `czeka_na_sloty`.

**Rekomendacja BE: `rozeslane`.** Powód: mówi, **co się stało**, a nie co się dzieje - a to jest
sedno wady. `czeka_na_sloty` jest najuczciwszy, ale najdłuższy i wprowadza drugie pojęcie
(„slot") do nazwy stanu materiału. `w_kolejce` myli się z `post_queue.status='queued'`.

**Nazwa jest do zatwierdzenia przez Tomasza PRZED startem.** Nie wybieraj sam.

## 3. Inwentarz - policzony 02/08, zweryfikuj przed startem

**Kod: 32 miejsca w 9 plikach** (`grep -rn "dispatching" cm-agent/app/*.py`):

| plik | trafień |
|---|---|
| `worker.py` | 7 |
| `matreview.py` | 7 |
| `conversation.py` | 6 |
| `channels.py` | 4 |
| `slots.py` | 3 |
| `config.py` | 2 |
| `planner.py`, `proactive.py`, `reports.py` | po 1 |

**DDL z ograniczeniem CHECK - trzy pliki:**
`cm-agent/db/001_init.sql:27`, `003_brain_phase1.sql:28`, `010_notion_ssot.sql:232`.

**n8n: NIE ZGADUJ.** Trafienia w repozytorium są wyłącznie w `n8n-workflows/patches/` (kopie
zapasowe) i w skrypcie łatki `scheduler-media-ledger-21072026.cjs`. **Czy ŻYWY workflow zawiera
tę wartość - sprawdź przez API n8n przed startem**, czytając definicję. Wpis w długu twierdzi,
że zawiera; nie potwierdziłem tego odczytem i nie chcę, żebyś działał na moim wspomnieniu.

## 4. To jest KLUCZ DOPASOWANIA, nie etykieta

`worker.reconcile_publications` pyta `WHERE status='dispatching'`, a `slots.assign_if_needed`
i dwie trasy `conversation` mają tę wartość w listach `status IN (...)`.

**Konsekwencja: obowiązuje procedura z `docs/ops/RUNBOOK_migracje.md`, punkt 3 - zatrzymanie
pisarza.** To ta sama klasa co D-009, gdzie kod i dane rozjechane choćby na minutę oznaczały
cichą wadę.

```
build -> docker stop cm-agent -> DDL + UPDATE -> docker run cm-agent
```

Baza stoi w kontenerze `pg_n8n`, pisarzem jest `cm-agent`, więc migracja działa przy wyłączonym
pisarzu. **Nie szukaj „mniej szkodliwej kolejności" - okno da się usunąć całkowicie.**

## 5. Obowiązkowe przed pierwszą linią kodu

1. **Przeczytaj `docs/ops/RUNBOOK_migracje.md` w całości.** Dziewięć zasad, wszystkie mają tu
   zastosowanie. Szczególnie punkt 9: łańcuch `&&` chroni dane, ale nie chroni dostępności,
   a najbardziej prawdopodobnym wyzwalaczem przerwania jest **twoja własna bramka**.
2. **Przeczytaj `docs/ops/DLUG_TECHNICZNY.md`, nagłówek** - regułę brania długu. Sprawdź,
   czy opis D-008 nadal opisuje rzeczywistość. Jeśli się rozjechał - **popraw opis i zgłoś,
   zanim ruszysz kod**. Na dziewięć długów zamkniętych 02/08 trzy wpisy myliły o własnym
   przedmiocie.
3. **Zrób własny grep.** Liczby z sekcji 3 są z 02/08. Nie ufaj im, potwierdź je - AP-309.

## 6. Kolejność wykonania

1. **Odczyt:** własny inwentarz + żywy workflow n8n + rozkład wartości w `content_items.status`.
2. **Nazwa zatwierdzona przez Tomasza.**
3. **Kod:** wszystkie 32 miejsca w jednym commicie. Rozważ stałą (`config.STATUS_ROZESLANE`)
   zamiast literału w 32 miejscach - to usuwa całą klasę przyszłych rozjazdów, dokładnie tak
   jak `_ENG_KANALY` przy D-009/D-014.
4. **DDL:** nowa wartość w `CHECK` **obok starej** (nie zamiast), żeby migracja mogła przebiec.
   Stara wartość znika z ograniczenia **dopiero po** migracji danych, osobnym poleceniem.
5. **Migracja** z bramką na liczbie wierszy w transakcji (runbook punkt 4).
6. **n8n:** PUT z rytuałem kopia → PUT → deactivate + activate. **Sekret:** skrypt tworzący
   przejmuje go z żywego workflow, jeśli nie podasz `LACZNIK_E2_SECRET` - nie nadpisz go
   przypadkiem, bo zerwiesz adres konektora.
7. **Test** pilnujący, że stara wartość nie wróciła do kodu ani do bazy.

## 7. Definicja ukończenia

- [ ] Zero wystąpień starej wartości w `cm-agent/app/` (grep, nie pamięć).
- [ ] `CHECK` w trzech plikach DDL zna wyłącznie nową wartość.
- [ ] Zero wierszy `content_items` ze starą wartością; **kontrola innym mechanizmem** niż
      migracja (runbook punkt 6, AP-313).
- [ ] Żywy workflow n8n sprawdzony i, jeśli trzeba, zaktualizowany; adres konektora **bez zmian**.
- [ ] Test w zestawie, sprawdzony też przez **celowe przywrócenie wady** - musi spaść.
- [ ] Zestaw zielony w całości (dziś 23/23).
- [ ] `docs/ops/DLUG_TECHNICZNY.md`: D-008 zamknięty z datą; **D-006 wspomina o D-008**,
      więc zaktualizuj też tamten wpis.
- [ ] Dokumentacja w **tym samym commicie** co zmiana (runbook punkt 8).

## 8. Czego NIE robić

- **Nie przywracaj serii X.** 02/08 zniesiono ją także w kodzie (`channels.py`). Jeśli natkniesz
  się na kod dzielący wariant na części - to jest wada, nie funkcja.
- **Nie zmieniaj `post_queue.status`.** To osobny słownik i osobna sprawa.
- **Nie ruszaj `post_queue.format`** (DDL 041, dwie wartości: `post`/`article`). Trzecia
  wartość znaczyłaby, że seria wróciła.
- **Nie działaj przy niepustej kolejce bez uprzedzenia Tomasza.** Na 02/08 kolejka X była pusta,
  ale CM dostał nowy masterprompt i **zaczyna produkować** - sprawdź stan, zanim zatrzymasz
  pisarza.

## 9. Kontakt

Wynik zgłoś Tomaszowi jednym meldunkiem. **Ta instancja (BE) koordynuje i audytuje** - jeśli
inwentarz z sekcji 3 nie zgodzi się z twoim odczytem, to jest ustalenie warte zgłoszenia,
a nie drobiazg do cichego poprawienia.
