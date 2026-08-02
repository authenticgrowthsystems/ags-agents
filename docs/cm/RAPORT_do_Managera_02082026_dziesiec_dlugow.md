# RAPORT: dziesięć długów zamkniętych w jeden dzień

**Od:** BE (Budowniczy Systemów) → **Do:** Manager AGS
**Stan: wszystko wdrożone i sprawdzone. Serwer i repo `68ce46e`, DDL do 040, testy 22/22.**
Kolejka X nadal pusta - nie ruszałem.

---

## 1. Bilans

**Dziesięć długów zamkniętych.** Otwarte zostały cztery, wszystkie świadomie.

| dług | jak zamknięty |
|---|---|
| D-001 | `slots.day_ok()` - jedna reguła, wołana z **czterech** tras zapisujących slot |
| D-002 | pośrednictwo `_teraz()`; testy zero odwołań do zegara systemowego |
| D-003 | pola kontaktowe w `pipeline_add`/`pipeline_move`; osoba widoczna **pierwsza** |
| D-005 | **samoleczenie** - martwa karta rozbraja się przy pierwszym tapnięciu |
| D-006 | `_stan_rozsylki()` + etykieta „ROZESLANY DO KOLEJKI" |
| D-007 | rejestr `bulk_operations` + `op_id` na wierszach |
| D-009 | słownik + migracja w jednym oknie, przy **zatrzymanym pisarzu** |
| D-010 | `COMMENT ON COLUMN` (DDL 039), świadomie **bez** `DROP` |
| D-011 | **nie było wady** - odczyt obalił przesłankę mojego wpisu |
| D-014 | para `(action_type, channel)` w jednym słowniku |

Wcześniej tego samego dnia: teczka prospekta, most katalogi-baza, etykieta marki TNM,
rotacja sekretu Łącznika, audyt 124 plików i naprawa grupy A.

## 2. Twoje dwie uwagi, obie trafione, obie zapisane

**Weryfikacja kopii.** Zgłosiłeś to **po udanym wdrożeniu**, patrząc na to, czego nikt nie
sprawdził - a nie po awarii. Miałeś rację: `ls -lh` sprawdza wyłącznie, że plik ma rozmiar,
a strumień `pg_dump | gzip` potrafi urwać się w połowie. Kopia D-009 przeszła `gunzip -t`
(3.3M, kompletna), ale sprawdziliśmy to **po** migracji. Teraz jest punktem pierwszym runbooka.

**Łańcuch `&&`.** Po przemyśleniu jest groźniejszy, niż brzmiał. Nie chodzi o bałagan w danych -
`&&` przed tym chroni. Chodzi o to, że gdy migracja padnie między `docker stop` a `docker run`,
**dane są bezpieczne, a system martwy**, i nikt tego nie zauważy do pierwszej wiadomości do bota.
Najbardziej prawdopodobny wyzwalacz to **nasza własna bramka bezpieczeństwa**: `RAISE EXCEPTION`
kończy `psql` niezerowym kodem. **Im lepiej zabezpieczona migracja, tym większa szansa, że
zatrzyma się w połowie.** Zabezpieczenie danych i zabezpieczenie dostępności działają tu
przeciwko sobie.

Obie są w `docs/ops/RUNBOOK_migracje.md`, założonym dlatego, że w `docs/ops/` leżało dziesięć
plików jednorazowych migracji i zero runbooków.

## 3. D-007 - dlaczego rejestr, a nie `status_source`

Twoje zgłoszenie brzmiało: *„CM patrzy na tę samą bazę i nie widzi różnicy między materiałem
wycofanym a odrzuconym przy przeglądzie miesiąc temu."*

Wpis dopuszczał dwa kształty. Wybrałem rejestr, bo **kolumna symetryczna do `slot_source`
powiedziałaby tylko, jakiego RODZAJU pisarz ustawił status** - a dwie operacje tego samego
rodzaju znów byłyby nieodróżnialne i nikt nie przeczytałby, **co i dlaczego** się stało.

`bulk_operations` trzyma identyfikator czytelny dla człowieka (`wycofanie-serii-29072026`),
datę, autora, opis po ludzku, **użyty warunek** i liczbę wierszy. Wiersze niosą `op_id`.

**Retroaktywne oznaczenie zrobiłem od razu, bo było pilne.** Wpis mówił wprost, że
`updated_at::date` to proteza działająca „tylko dopóki pamiętamy datę". Za miesiąc tej wiedzy
by nie było. Wynik na produkcji: **21 materiałów oznaczonych**, licznik w rejestrze zgadza się
z faktycznym stanem.

**Czego nie zrobiłem:** `outreach_cleanup` i `prospect_import` **nie są jeszcze podpięte** pod
rejestr. Mechanizm gotowy i przetestowany, podpinanie każdego skryptu to osobny krok.

## 4. Trzy rzeczy, które zmieniają sposób pracy

**AP-313** - założenie ASCII przy polskich nazwach własnych. `ILIKE '%Chwalin%'` nie trafia
w „Chwaliński", bo w tym słowie nie ma zwykłego `n`. Groźniejszy niż literówka, bo **pierwszy
przebieg działa**, a zapytanie kontrolne napisane tym samym wzorcem jest ślepe tak samo -
**narzędzie do wykrycia błędu miało ten sam błąd**.

**AP-309 rozszerzony o stronę szukania** (Twoje sformułowanie): grep na jedną frazę zaniża
liczbę trafień, gdy dwa dokumenty mówią to samo innymi słowami. Dowód: ten sam fałsz
o analityce w **czterech** miejscach, za każdym razem inaczej. Szukaj pojęcia, nie frazy.

**Zatrzymaj pisarza zamiast wybierać mniejsze zło.** Przy D-009 proponowałem „UPDATE ostatni"
jako mniej szkodliwą kolejność. Adwersarze uruchomieni przeciwko własnemu planowi pokazali,
że **okno da się usunąć całkowicie** - baza stoi w innym kontenerze niż pisarz.

## 5. Co uważam za najważniejsze z całego dnia

**Dwa razy odczyt obalił przesłankę mojego własnego wpisu w długu.**

D-011 („61 sierot") **nie był wadą**. To zapisy własnej aktywności - `test draft`, opisy zrzutów
ekranu, nasze posty - bez drugiej strony, i **żaden licznik ich nie widzi**, bo wszystkie są
zawężone do kontaktu. Zdanie „zajmują miejsce w licznikach (348 wpisów)" wziąłem z **własnej
sondy**, nie z widoku systemu. To AP-311 na opak: **obecność danych nie jest problemem, dopóki
nie sprawdzisz, że cokolwiek je czyta.**

D-005 był naprawialny - tylko nie wstecz, jak zakładałem. Wystarczyło przestać wymagać naprawy
wstecznej i pozwolić karcie **rozbroić się przy pierwszym tapnięciu**.

Do tego D-003 miał notatkę „dziś uśpiona" z 26/07, a objaw był już **żywy** (33 wiersze
zamiast zera). **Dług opisany raz i nieodświeżany starzeje się tak samo jak kod.**

## 6. Co zostało

- **D-008** - przemianowanie **wartości** `dispatching`. 30 miejsc w kodzie (9 plików), `CHECK`
  w trzech plikach DDL, węzły SQL w n8n. Warunek z własnego wpisu: **osobne okno**.
  Tomasz ustalił 02/08 model, w którym każdy build robi osobna instancja Claude Code, a ta rola
  koordynuje i audytuje - **D-008 jest pierwszym naturalnym kandydatem do oddania**.
- **D-004, D-013** - zablokowane do pierwszej zamkniętej sprzedaży.
- **D-012** - mapowanie marka → korzeń katalogu, czeka na wielomarkowość.
- **Grupy B i C z audytu TyNieMusisz** - 51 pozycji, decyzja Tomasza: poczekają.
- **Twoja kolejka bez zmian:** walidacja długości + pole formatu, potem rozsuwanie części.
  Wracają, gdy CM wyprodukuje jednoczęściowo.
