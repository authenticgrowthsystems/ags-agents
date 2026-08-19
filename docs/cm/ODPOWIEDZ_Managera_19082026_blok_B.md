# ODPOWIEDŹ Managera na ZAPYTANIE z 19.08.2026 (blok B)

Zapis decyzji, nie parafraza. Pytania w `docs/cm/ZAPYTANIE_do_Managera_19082026_blok_B.md`.
**Wszystkie cztery rozstrzygnięte, blok B odblokowany.**

## P1 - zakres bramki: OPCJA A, obie drogi, jedna bramka we wspólnym miejscu zapisu

Manager przyjął uzasadnienie BE w całości: **różnica między preferencją a poleceniem leży
w sformułowaniu, nie w autorstwie**, a pochodzenie wpisu i tak nie jest dziś zapisywane, więc
węższe cięcie byłoby bramką, której **nie da się wyegzekwować** (AP-309).

> Zero incydentów bije wygodę dyktowania reguł.

## P2 - droga zastępcza, NIE sama odmowa

Gdy Tomasz powie "zapamiętaj na zawsze", bot odpowiada **widocznie**: reguła NIE weszła do stylu
(powód: D-019), została zapisana jako **notatka do przeglądu przy odblokowaniu pętli**.
Nie gubimy tego, co Tomasz chciał zapamiętać, i nie ma żadnej cichej odmowy.

> Te kilkanaście linii jest warte swojej ceny.

## P3 - ZATWIERDZONE rozszerzenie: kształt pola zapisujemy już teraz

Każda notatka niesie **język**, **rodzaj** (preferencja kontra polecenie) i **pochodzenie**
(model kontra człowiek). Notatki z drogi zastępczej z P2 od pierwszego dnia mają pochodzenie
**"człowiek"**. Cel: przy odblokowaniu pętli zostaje tylko **przegląd, bez drugiej migracji**.

Zapis nowych wpisów do samego stylu pozostaje wyłączony.

## P4 - rozgraniczenie AP-311 kontra AP-317 ZATWIERDZONE

Test rozstrzygający uznany za dobry:

> Istnieje poprawka, po której pustka stałaby się wiarygodna - to AP-311 i szukamy wady.
> Kanał nie ma żadnego połączenia z bazą - to AP-317 i zmieniamy sposób czytania, nie system.

**AP-317 zostaje w indeksie jako osobny wzorzec.** Wpis w AP-311 poprawiony zgodnie z opisem BE.
Manager zaznaczył, że jest stroną wpisu z 14.08 i że to rozgraniczenie oddaje jego intencję.

Wykonane 19.08: sekcja "Granica z AP-317" w
`docs/anti-patterns/AP-311_brak_danych_to_nie_fakt.md`, z jawną adnotacją, że człon
"albo były poza zasięgiem systemu" został stamtąd **zdjęty** i przeniesiony do AP-317.

---

## ZAKRES BLOKU B PO TEJ ODPOWIEDZI

1. bramka w miejscu wspólnego zapisu, obejmująca obie drogi,
2. droga zastępcza z widocznym komunikatem,
3. kształt pola przy zapisie notatek,
4. test,
5. rebuild wspólny z blokiem C, zgodnie z planem z 19.08,
6. **dokumentacja w tym samym commicie co kod.**
