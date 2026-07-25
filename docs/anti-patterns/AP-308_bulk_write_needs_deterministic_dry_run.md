# AP-308: Masowa zmiana zywych danych bez DETERMINISTYCZNEGO podgladu

**Anti-pattern (25/07/2026, BE, re-slotter kolejki X):** re-slotter zmienial `scheduled_for`
64 wierszy zywej kolejki publikacji naraz. Pierwsza wersja miala isc od razu do zapisu. Dwa
razy PODGLAD (dry-run) zlapal blad, ktory apply wypuscilby na produkcje, zanim ktokolwiek by
zauwazyl:
1. **v1 rozproszyl serie** - nadmiar kaskadowal po chronologii wiersza, wiec czesci jednej
   serii ladowaly na roznych dniach, hook PO rozwinieciu. Widac to bylo dopiero na liscie
   przeniesien.
2. **siatka dala 3/dzien zamiast 5** - stale gniazda 10:00/12:30/... nie miescily sie w oknie
   publikacji X (13:00-22:00), wiec dwa wypadaly. Rozklad w dry-run pokazal 3/dzien i kolejke
   rozwleczona do 15/08 - artefakt buga, nie zamiar.

Gdyby apply szedl od razu, kolejka publikowalaby sie zle (rozsypane serie / za rzadko) przez
dni, zanim Tomasz by to wychwycil - a publikacja jest wychodzaca i nieodwracalna.

**Dlaczego zle:** masowa zmiana zywych danych jest trudna do cofniecia (zwlaszcza gdy karmi
proces wychodzacy jak Scheduler). Blad w algorytmie przydzialu jest niewidoczny w kodzie i
w testach syntetycznych - ujawnia sie dopiero na PELNYCH prawdziwych danych (tu: prawdziwe
okno kanalu, prawdziwe id serii, prawdziwa skala 64 nie 15).

**Poprawnie:**
1. **Kazda masowa zmiana zywych danych ma tryb DRY-RUN**, ktory drukuje DOKLADNIE to, co
   zrobi apply (rozklad + lista zmian stary->nowy), i nic nie zapisuje. Czlowiek zatwierdza
   podglad, dopiero potem apply. Wzorzec: `python -m app.<tool> dry` / `... apply`
   (jak `x_collector probe`/`collect`).
2. **Wynik MUSI byc deterministyczny** - inaczej apply da co innego niz pokazal dry i podglad
   klamie. Konkretnie: `humanize_slot` losuje minute, wiec re-slotter dostal wlasna
   deterministyczna minute per id (`_human_minute`). Bez tego kazdy przebieg = inne sloty,
   brak idempotencji, dry != apply.
3. **Idempotencja jako test**: drugi przebieg po apply MUSI dac 0 zmian. Jesli daje wiecej,
   operacja nie jest stabilna (cos losowego albo zaleznego od czasu przecieka do wyniku).
4. **Nie hardkoduj tego, co siedzi w configu** (godziny siatki vs `channels.config.
   publish_windows`) - to zrodlo cichych "dziala, ale nie w pelni" bledow (bug 3/dzien).
5. **Nie zakladaj skali** - sonda pokazala 64 wiersze, nie 15 (widok stanu gry ucinal do 10).
   Przed planem na zywych danych pobierz PELNY zbior, nie probka.

**Dowod wartosci reguly:** oba bledy (rozproszenie serii, 3/dzien) zostaly naprawione MIEDZY
dry a apply, kosztem zera na produkcji. Test: `cm-agent/tests/test_reslot.py` (grupowanie
serii, kolejnosc narracyjna, siatka z okna, gestosc sterowana, IDEMPOTENCJA).
