# RUNBOOK: migracje danych na produkcji

**Zalozony 02/08/2026 na polecenie Managera, PO udanym wdrozeniu D-009** - zeby zasady nie
czekaly na wpadke. W `docs/ops/` lezy dzis **dziesiec** plikow jednorazowych migracji i zero
runbookow; zasada zapisana w pliku z konkretna data nie doczeka nastepnego razu.

Ten plik czyta sie **przed** kazda migracja dotykajaca danych produkcyjnych.

---

## 1. Zweryfikuj kopie, ZANIM cokolwiek zatrzymasz

```
gunzip -t ~/backups/<plik>.sql.gz && echo "KOPIA OK"
```

**`ls -lh` sprawdza wylacznie to, ze plik ma rozmiar.** Strumien `pg_dump | gzip` potrafi urwac
sie w polowie i zostawic archiwum, ktore wyglada zdrowo, a nie da sie go rozpakowac.

> Kopia, ktora TWIERDZI, ze istnieje, jest gorsza niz jej brak - daje falszywe poczucie odwrotu
> i zmienia decyzje, ktore podejmujesz dalej.

To jest ta sama rodzina co AP-311 (brak danych to nie fakt, dopoki nie sprawdzisz, ze system
moglby je pokazac): **istnienie pliku to nie to samo, co istnienie kopii.**

## 2. Lancuch `&&` chroni DANE, nie chroni DOSTEPNOSCI

Sekwencja `stop -> migracja -> start` spieta operatorem `&&` jest poprawna dla danych: gdy
migracja padnie, nic sie nie zapisze. Ale **kontener zostanie WYLACZONY**, bo `&&` przerywa
reszte lancucha - w tym `docker run`.

Najbardziej prawdopodobny wyzwalacz to **nasza wlasna bramka bezpieczenstwa**: `RAISE EXCEPTION`
konczy `psql` niezerowym kodem. Im lepiej zabezpieczona migracja, tym wieksza szansa, ze
zatrzyma sie w polowie - i zostawi system martwy.

**Przy KAZDYM przerwaniu sekwencji pierwsza czynnoscia jest podniesienie kontenera**, nie
diagnoza. Baza jest wtedy nietknieta (transakcja sie wycofala), wiec stary obraz jest bezpieczny.
Komenda ratunkowa ma byc **przygotowana i wklejalna PRZED startem migracji**, nie szukana
w panice.

## 3. Zatrzymaj PISARZA, zamiast wybierac mniejsze zlo

Gdy migracja zmienia wartosc, ktora jest **kluczem dopasowania** (a nie sama etykieta), kod
i dane rozjechane choc na minute znacza cicha wade.

Nie szukaj "mniej szkodliwej kolejnosci" - **sprawdz, czy da sie usunac okno**. Zwykle da sie:
baza stoi w innym kontenerze (`pg_n8n`) niz pisarz (`cm-agent`), wiec migracja dziala przy
wylaczonym pisarzu.

```
build -> docker stop <pisarz> -> migracja -> docker run <pisarz>
```

Przy zatrzymanym pisarzu pytanie "UPDATE przed czy po rebuildzie" **przestaje istniec**.

## 4. Bramka na liczbie wierszy, wewnatrz transakcji

```sql
BEGIN;
DO $$
DECLARE n integer;
BEGIN
  SELECT COUNT(*) INTO n FROM <tabela> WHERE <ten sam predykat co UPDATE>;
  RAISE NOTICE 'Wierszy do migracji: %', n;
  IF n <> <oczekiwana> THEN
    RAISE EXCEPTION 'STOP: oczekiwano <oczekiwana>, jest %. MIGRACJA WYCOFANA.', n;
  END IF;
END $$;
UPDATE ... RETURNING ...;
COMMIT;
```

Bez tego kontrole wykonuja sie **po** nieodwracalnym zapisie i sluza juz tylko do opisania szkody.

## 5. Kontrola z JAWNYM progiem, nie "czy niezero"

Zapytanie kontrolne musi mowic, ile wierszy jest **poprawne**, i co zrobic przy kazdej innej
liczbie. "Ma nie byc zero" przepusci dwojke jako sukces.

## 6. Kontrola musi uzywac INNEGO mechanizmu niz operacja

Zapytanie sprawdzajace napisane tym samym wzorcem, co migracja, potwierdza wylacznie samo siebie.
Dowod: AP-313 - `ILIKE '%Chwalin%'` nie trafial w "Chwaliński", a kontrola koncowa uzywala tego
samego wzorca i tez nic nie widziala.

## 7. SQL odwrotny w tym samym pliku, zakomentowany

Gotowy do wklejenia, z uwaga, ze cofa TAKZE wiersze zapisane juz przez nowy kod.

## 8. Dokumentacja idzie w tym samym commicie

Szczegolnie zdania typu "rozjazd jest kosmetyczny" - jesli wlasnie naprawiasz cos, co dokumentacja
nazywa nieistotnym, **to zdanie jest zaproszeniem do cofniecia poprawki jednym commitem.**

---

## Precedens: D-009 (02/08/2026)

Wszystkie osiem punktow powyzej pochodzi z jednego wdrozenia. Punkty 3, 4, 5 i 7 znalezli
**adwersarze uruchomieni przeciwko wlasnemu planowi** - moja pierwsza wersja wybierala mniej
szkodliwa kolejnosc zamiast usunac okno, i miala goly UPDATE bez transakcji.
Punkty 1 i 2 dolozyl Manager **po udanym wdrozeniu**, patrzac na to, czego nikt nie sprawdzil.


---

## 9. ZABEZPIECZENIE DANYCH I ZABEZPIECZENIE DOSTEPNOSCI DZIALAJA PRZECIWKO SOBIE

**Wpisane do kanonu 02/08/2026 decyzja Managera, w brzmieniu BE** (uwaga wyszla od Managera,
sformulowanie z raportu uznal za lepsze od swojego).

> **Im lepiej zabezpieczona migracja, tym wieksza szansa, ze zatrzyma sie w polowie -
> bo to WLASNA bramka bezpieczenstwa jest najbardziej prawdopodobnym wyzwalaczem.**

Rozwiniecie: lancuch `&&` w sekwencji `stop -> migracja -> start` jest **poprawny dla danych**.
Gdy migracja padnie, nic sie nie zapisze. Ale **kontener zostanie WYLACZONY**, bo `&&` przerywa
reszte lancucha razem z `docker run`. Dane sa bezpieczne, system martwy, i nikt tego nie zauwazy
do pierwszej wiadomosci do bota.

Najbardziej prawdopodobny wyzwalacz **nie jest awaria z zewnatrz**. Jest nim `RAISE EXCEPTION`
z naszej wlasnej bramki na liczbie wierszy (punkt 4) - czyli **im staranniej zabezpieczylismy
dane, tym latwiej przewrocimy dostepnosc**.

**Praktycznie:**
- komenda ratunkowa (`docker run ...`) ma byc **przygotowana i wklejalna PRZED** startem migracji,
  nie szukana w panice;
- przy KAZDYM przerwaniu sekwencji **pierwsza czynnoscia jest podniesienie kontenera**,
  nie diagnoza - baza jest wtedy nietknieta, wiec stary obraz jest bezpieczny;
- te dwa cele **trzeba wazyc swiadomie**, a nie zakladac, ze jedno zabezpieczenie sluzy obu.
