# AP-314: Bramka bezpieczenstwa, ktorej nikt nie widzial przy pracy, jest zalozeniem

**Ustanowiony 03/08/2026 (BE, w trakcie okna migracyjnego D-008).**
Rodzina AP-311, ale skierowana do wewnatrz: tam brak danych brany za fakt o swiecie,
tu **cisza wlasnego zabezpieczenia brana za dowod, ze nie bylo czego zglaszac**.

## Wzorzec

Przy ryzykownej operacji dokladasz zabezpieczenie: bramke na liczbie wierszy, straznika,
walidator, asercje. Zabezpieczenie nigdy nie zostaje zobaczone przy pracy - bo przeciez
"wszystko przechodzi". Tymczasem sciezka bledu takiego zabezpieczenia to **kod nieuruchomiony
ani razu, siedzacy w najbardziej krytycznym miejscu calej operacji**.

Cisza zabezpieczenia ma dwie mozliwe przyczyny i tylko jedna jest dobra:

1. **Nie bylo czego zglaszac** (dobra),
2. **Zabezpieczenie nie ma jak zglosic** - nie doszlo do wykonania, porownuje z pustka,
   albo pyta o cos innego, niz mysli autor.

Rozroznic ich **nie da sie z zewnatrz**. Wyglada tak samo: brak alarmu.

## Dowod: okno D-008 (03/08/2026)

Migracja miala bramke wg RUNBOOK punkt 4 - liczba wierszy porownywana z oczekiwana, `RAISE
EXCEPTION` przy niezgodnosci, wszystko w transakcji. Pierwsze uruchomienie na produkcji:

```
ERROR:  syntax error at or near ":"
LINE 6:   IF n <> :oczekiwana THEN
```

**`psql` nie podstawia zmiennych `:nazwa` wewnatrz bloku cytowanego dolarami** (`DO $$ ... $$`) -
dla niego tresc miedzy `$$` to zwykly tekst. Bramka nie zadzialala **zle**; ona w ogole
**nie doszla do wykonania**.

Tym razem bylo glosno: `ON_ERROR_STOP`, transakcja sie wycofala, zero szkody. Ale ten sam blad
o wlos obok jest **calkowicie cichy**, i mial go moja wlasna poprawka, dopoki go nie domknelem:

```sql
SELECT oczekiwana INTO oczek FROM _bramka;   -- gdy tabela pusta, oczek = NULL
IF n <> oczek THEN RAISE EXCEPTION ...;      -- n <> NULL daje NULL, czyli NIE-prawde
```

`IF` sie nie wykonuje, wyjatku nie ma, migracja **przechodzi bez kontroli** - a w logu stoi
linia sugerujaca, ze bramka byla. Porownanie z pustka jest grozniejsze niz brak porownania.

## Why bad

- **Zabezpieczenie zmienia decyzje.** Uruchamiasz ryzykowna operacje smielej, bo "jest bramka".
  Falszywe zabezpieczenie jest wiec gorsze niz jego brak - dokladnie jak kopia zapasowa, ktora
  twierdzi, ze istnieje (RUNBOOK punkt 1).
- **Sciezka bledu to kod nietestowany z definicji.** Sciezka sukcesu wykonuje sie zawsze,
  sciezka alarmu - nigdy, az do dnia, w ktorym wszystko od niej zalezy.
- **Cisza jest nieodrozninalna od poprawnosci.** Straznik, ktory nic nie zwraca, wyglada jak
  straznik, ktory nie mial czego zwrocic (to samo co AP-310 i AP-306).
- **Im lepiej zabezpieczona operacja, tym wiecej takiego kodu.** RUNBOOK punkt 9 mowi to samo
  od strony dostepnosci; tu jest ta sama mysl od strony zaufania.

## Correct

1. **Odpal zabezpieczenie ze ZLYM wsadem i zobacz, jak zatrzymuje - ZANIM zaufasz mu przy dobrym.**
   Przy D-008 kosztowalo to jedno dodatkowe uruchomienie i trzy minuty przestoju:

   ```
   NOTICE:  Wierszy do migracji: 0 (oczekiwano: 99)
   ERROR:   STOP: oczekiwano 99 wierszy, jest 0. MIGRACJA WYCOFANA, nic nie zapisano.
   ```

   Dopiero po zobaczeniu tego wolno uruchomic wersje prawdziwa.
2. **Bramka ma padac ZAMKNIETA.** Jawnie sprawdz, czy w ogole dostala czym porownywac
   (`IF oczek IS NULL THEN RAISE EXCEPTION`). Domyslne zachowanie SQL przy `NULL` to
   przepuszczenie, czyli najgorsze mozliwe.
3. **Nie ufaj podstawianiu tam, gdzie go nie widzisz.** W `psql` zmienne `:nazwa` dzialaja
   w zwykych zapytaniach, a **nie** wewnatrz `$$...$$` ani w innych literalach - wartosc trzeba
   wpuscic osobnym zapytaniem (tabela tymczasowa, `SET`) i przeczytac ja w bloku.
4. **Test jednostkowy sciezki alarmu jest wart wiecej niz test sciezki sukcesu.** Przy D-008
   test kontraktu nazwy sprawdzono **pieciema celowymi przywroceniami wady**, w tym takim,
   ktorego nikt by nie przewidzial (migracja slownika `post_queue`, ktorej robic NIE WOLNO).
   To ta sama zasada, tylko w kodzie zamiast w SQL.

## Granica z sasiadami

- **AP-311** - brak DANYCH brany za fakt. Tu: brak ALARMU brany za fakt. Ten sam blad
  wnioskowania, tylko przedmiotem jest wlasne narzedzie.
- **AP-306** - cichy `except` polykajacy wyjatek. Tam zabezpieczenie zjada blad; tu
  zabezpieczenie samo jest bledem, ktorego nikt nie zjadl, bo nikt go nie wywolal.
- **AP-310** - straznik gasnacy na wlasnych zaleglosciach. Tam straznik dziala i zwraca zero;
  tu nie dziala i tez zwraca zero.

**Index:** anti-patterns/library.md | **Powiazane:** docs/ops/RUNBOOK_migracje.md punkty 1, 4, 9, 10.
