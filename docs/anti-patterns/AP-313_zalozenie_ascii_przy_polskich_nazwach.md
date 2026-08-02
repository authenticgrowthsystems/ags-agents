# AP-313: Zalozenie ASCII przy polskich nazwach wlasnych

**Ustanowiony 01/08/2026 (Manager AGS).** Zlapany na wlasnym kodzie, kilka godzin po tym, jak
ten sam kod przeszedl komplet testow i wdrozenie.

**Fragment wyciety z nazwy zawierajacej ogonek nigdy nie trafi, a pierwszy przebieg tego
nie pokaze.**

## Wzorzec

Piszac dopasowanie po nazwie wlasnej, autor swiadomie unika literalu z polskim znakiem - bo
wie, ze kodowanie w drodze (plik SQL przez `docker exec`, przegladarka, klient bazy) potrafi
je przekrecic. Wycina wiec "bezpieczny" fragment ASCII i dopasowuje po nim.

Pulapka: **ogonek potrafi siedziec w srodku tego fragmentu, nie na koncu nazwy.**

Przyklad zrodlowy: `ILIKE '%Chwalin%'` dla nazwy **Chwaliński**. Wyglada bezpiecznie. Nie jest:
C-h-w-a-l-i-**ń**-s-k-i. W tym slowie **nie ma zwyklego `n`**. Wzorzec nie trafia nigdy.
Bezpieczny fragment to `Chwali` - i widac to dopiero, gdy sie przeliteruje.

## Dlaczego jest grozniejszy niz zwykla literowka

**Pierwszy przebieg dziala poprawnie.** Zabezpieczenie `WHERE NOT EXISTS (... ILIKE '%Chwalin%')`
przy pustej bazie zwraca prawde i wiersz sie zaklada - dokladnie tak, jak mial. Defekt jest
NIEWIDOCZNY w tescie akceptacyjnym, bo test sprawdza, czy wiersz powstal, a on powstal.

Defekt ujawnia sie dopiero **przy drugim uruchomieniu**, w postaci duplikatu. A zapytanie
kontrolne na koncu tego samego pliku uzywalo tego samego wzorca, wiec **nie pokazaloby ani
pierwszego wiersza, ani drugiego**. Kontrola byla slepa na dokladnie ten sam sposob.

To odroznia AP-313 od zwyklej pomylki: **narzedzie do wykrycia bledu ma ten sam blad**.

## Zasada

1. Przy dopasowaniu po nazwie wlasnej uzywaj **wylacznie fragmentow bez znakow diakrytycznych** -
   sprawdzonych literka po literce, nie "na oko".
2. Albo, lepiej, **normalizuj OBIE strony**: `translate(nazwa, 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ',
   'acelnoszzACELNOSZZ')` po stronie SQL i to samo po stronie wzorca. `unaccent` tez, jesli
   rozszerzenie jest dostepne - ale `translate` nie wymaga niczego instalowac.
3. **Nigdy nie zakladaj, ze da sie "obciać przed ogonkiem".** W polskich nazwiskach ogonek
   siedzi zwykle w srodku, nie na koncu.
4. Zapytanie kontrolne musi uzywac **innego mechanizmu** niz zapytanie sprawdzane. Kontrola
   napisana tym samym wzorcem, co operacja, potwierdza wylacznie samo siebie.

## Gdzie to bije poza SQL

To nie jest problem jednego pliku migracyjnego. **Uderza w kazde miejsce, gdzie czlowiek wpisuje
nazwe, a kod szuka jej w bazie** - a czlowiek pisze bez ogonkow, bo tak jest szybciej.

Przypadek prawdziwy, znaleziony przy okazji: katalog klienta na dysku nazywa sie `Chwalinski`
(bez ogonka, taka jest reguła nazewnictwa katalogow), a wiersz w lejku nazywa sie **Chwaliński**.
Wpisanie nazwy katalogu do narzedzia `teczka` **nie znajdzie prospekta**. Most miedzy dyskiem
a baza pekalby przy pierwszym prawdziwym uzyciu, i to w sposob wygladajacy jak "nie ma takiego
klienta", a nie jak usterka.

## Rachunek AP-309 (01/08/2026)

W `cm-agent/app/` jest **27 dopasowan `ILIKE`/`LIKE`**. Nie wszystkie sa podatne - wiekszosc
dotyczy naszych wlasnych znacznikow ASCII w `notes` albo tytulow materialow, gdzie ogonka nie ma
czego rozbic. Podatnych, bo dopasowujacych **NAZWE WLASNA**, jest **siedem**:

| plik | linia | co robi |
|---|---|---|
| `sales.py` | 225 | `_find_pipeline` - szukanie prospekta po fragmencie nazwy |
| `sales.py` | 1178 | dopasowanie gotowca po `author_display` (rownosc, nie ILIKE) |
| `sales.py` | 1730 | szukanie po `content` / `notes` / `author_display` |
| `teczka.py` | 69 | `_podobne` - lista podobnych nazw z lejka |
| `teczka.py` | 76 | `_podobne` - lista podobnych nazw z kontaktow |
| `teczka.py` | 106 | `znajdz` - rozstrzyganie prospekta |
| `teczka.py` | 109 | `znajdz` - rozstrzyganie kontaktu |

## Powiazania

- **AP-309** (jedna naprawa, wiele miejsc): rachunek powyzej jest jego zastosowaniem.
- **AP-311** (brak danych to nie fakt): "nie znajduje prospekta" wyglada jak brak prospekta.
- **AP-312** (nazwa klamie): tu klamie nie nazwa stanu, tylko **cichy brak trafienia** -
  zapytanie bez wynikow nie jest bledem w SQL, wiec `UPDATE` bez trafien konczy sie sukcesem.


---

## PODNIESIONE DO KANONU 02/08/2026 (decyzja Managera, brzmienie z raportu BE)

> **Narzedzie do wykrycia bledu mialo ten sam blad.**

Manager wskazal to zdanie jako najmocniejsze z raportu i polecil zapisac je doslownie, bo
opisuje **osobna klase wad, grozniejsza od zwyklej literowki**.

Zwykla literowka wychodzi przy pierwszym uruchomieniu. Ta klasa **przechodzi pierwszy przebieg
poprawnie** i chowa sie przed wlasna kontrola:

- `INSERT ... WHERE NOT EXISTS (... ILIKE '%Chwalin%')` przy pustej bazie zwraca prawde
  i wiersz sie zaklada. **Test akceptacyjny przechodzi**, bo sprawdza, czy wiersz powstal.
- Defekt ujawnia sie dopiero przy DRUGIM uruchomieniu, jako duplikat.
- A zapytanie kontrolne na koncu tego samego pliku uzywalo **tego samego wzorca**, wiec
  nie pokazaloby ani pierwszego wiersza, ani drugiego.

**Regula operacyjna, ktora z tego wynika:** zapytanie kontrolne MUSI uzywac **innego mechanizmu**
niz operacja, ktora sprawdza. Kontrola napisana tym samym wzorcem, co dzialanie, potwierdza
wylacznie samo siebie.

Ta sama zasada jest punktem 6 `docs/ops/RUNBOOK_migracje.md`.
