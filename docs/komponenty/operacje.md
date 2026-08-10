# Komponent: REJESTR OPERACJI HURTOWYCH (`bulk_operations`)

**STATUS GOTOWOSCI: ZBUDOWANY, NIEPODLACZONY** - modul, tabela i testy sa; **zaden kod
produkcyjny go nie wola i nikt nie czyta `op_id`**. Dziala wylacznie wtedy, gdy czlowiek
albo agent SWIADOMIE zawola go przy operacji hurtowej. Szczegoly w sekcji "Czego tu nie ma".
(macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Daje operacji hurtowej **nazwe i opis**, ktore drugi agent moze odczytac z bazy.
Kazdy dotkniety wiersz dostaje `op_id`, wiec dokladny zbior wycina sie jednym warunkiem
zamiast zgadywania po dacie i statusie.

```
🧾 wycofanie-serii-29072026 (2026-07-29, BE): Wycofanie 21 materialow X po decyzji
   "jeden wpis na material, koniec serii"
Warunek: brand_id='AGS' AND platform='x' AND czesci > 1
Dotknietych wierszy: 21
```

## Dlaczego powstal (D-007, 02/08/2026)

Zgloszenie Managera z 29/07, **szosta odslona AP-311**. Po wycofaniu 21 materialow Content
Manager zapytal, PO CZYM ma je rozpoznac. Nie brakowalo danych - **dane byly NIEODROZNIALNE**:
`status='rejected'` z operacji hurtowej wyglada identycznie jak `rejected` z przegladu kart
sprzed miesiaca. Zapytanie "X + rejected + wiecej niz jeden wiersz" zwracalo 26 materialow,
z czego z operacji bylo 21.

> "Ty wiesz, co wycofales, bo sam to robiles. CM patrzy na te sama baze i nie widzi roznicy
> miedzy materialem wycofanym a odrzuconym przy przegladzie miesiac temu." - Manager 29/07

## Kontrakt

| funkcja | co robi | uwaga |
|---|---|---|
| `zarejestruj(op_id, kto, opis, warunek=None, brand_id)` | zaklada wpis | **wolaj PRZED zmiana**, nie po |
| `oznacz(op_id, tabela, ids)` | stempluje wiersze, zwraca ile | tabela z bialej listy `TABELE` |
| `opis(op_id)` | jedno-blokowa odpowiedz dla drugiego agenta | |
| `ostatnie(limit=5)` | "co sie tu dzialo hurtem" | |

Tabela `bulk_operations` (DDL 040) + kolumny `op_id` w `content_items` i `post_queue`.

## Decyzje projektowe warte zapamietania

- **`zarejestruj` PRZED zmiana, nie po.** Jesli operacja padnie w polowie, chcesz wiedziec,
  ze w ogole sie zaczela, i na jakim warunku. Wpis po fakcie opisuje tylko udane operacje,
  czyli dokladnie te, ktore najmniej wymagaja wyjasnienia.
- **`op_id` ma byc CZYTELNY i pisany z pamieci** (`wycofanie-serii-29072026`), bo trafia
  do zapytania, ktore ktos wklepie recznie. Stad wzorzec `^[a-z0-9][a-z0-9-]{4,60}$`:
  male litery, cyfry, myslniki. **Bez polskich znakow - AP-313**: nazwa z ogonkiem
  nie trafilaby w dopasowanie pisane z pamieci.
- **Nazwa tabeli przechodzi przez biala liste** (`TABELE`), bo jest jedynym miejscem w module,
  gdzie interpolacja do SQL jest konieczna. Test podaje `"content_items; DROP TABLE contacts"`
  i wymaga odmowy - to jedyna asercja w tym module, ktora pilnuje czegos gorszego niz balagan.
- **Operacja bez opisu jest odrzucana.** Rejestr, ktory przyjmuje puste `opis`, produkuje
  wpisy nieodroznialne od siebie nawzajem - czyli odtwarza problem, ktory mial rozwiazac.
- `oznacz` **nie wywraca operacji** przy bledzie zapisu (zwraca 0 i loguje). Stempel jest
  dodatkiem do zmiany, a nie jej warunkiem - lepiej stracic stempel niz zostawic operacje
  w polowie.

## Czego tu NIE MA (stan na 10/08/2026)

**Zadnego wywolania produkcyjnego.** `grep` po `cm-agent/app/` daje wylacznie sam modul
i jego test; **`op_id` nie jest nigdzie CZYTANE** przez kod. Praktyczne konsekwencje:

1. Rejestr wypelnia sie tylko wtedy, gdy prowadzacy operacje o nim PAMIETA. Rejestr,
   do ktorego nikt nie ma obowiazku pisac, bedzie pusty dokladnie wtedy, gdy bedzie potrzebny -
   to ta sama klasa co AP-314 (zabezpieczenie, ktorego nikt nie widzial przy pracy).
2. Zaden raport ani karta nie pokazuje dzis `op_id`, wiec nawet zapisana operacja nie wyplynie
   sama - trzeba o nia zapytac (`operacje.opis`, `operacje.ostatnie`) albo zajrzec do bazy.
3. Wycofanie 21 materialow z 29/07, ktore ten modul zamowilo, **nie ma wpisu** - modul powstal
   po fakcie.

**Nastepny krok, gdy ktos bedzie to podlaczal:** trasy hurtowe w `reslot`, `outreach_cleanup`
i `bulk_polish` sa naturalnymi pierwszymi konsumentami; kazda z nich dotyka wielu wierszy naraz
i zadna nie zostawia dzis sladu.

## Punkty zaczepienia w kodzie

- `cm-agent/app/operacje.py` - caly modul
- `cm-agent/db/040_operacje_hurtowe.sql` - tabela + kolumny + komentarze
- `cm-agent/tests/test_operacje.py` - kontrakt, w tym odmowa dla nazwy tabeli spoza listy
- `docs/ops/DLUG_TECHNICZNY.md` D-007 - pelny opis dlugu i jak zostal zamkniety
