# ZAPYTANIE do Managera - 19.08.2026, blok B (D-019)

**Stan:** blok F i AP-317 zamknięte i wypchnięte (`main` = `origin/main` = `9be1173`).
Blok C (D-020) w robocie. **Blok B WSTRZYMANY na tym pytaniu** - decyzja Tomasza 19.08:
najpierw pytanie do Ciebie, potem praca.

Nie zaczynam, bo odczyt kodu pokazał coś, czego nie ma w treści decyzji Z-3, a co zmienia
zakres roboty i dotyka funkcji, z której Tomasz korzysta osobiście.

---

## USTALENIE, KTÓREGO NIE BYŁO PRZY PODEJMOWANIU DECYZJI Z-3

Do `brand_config.style_learned` piszą **dwa różne organy**, nie jeden:

| organ | plik | kto jest autorem regułki |
|---|---|---|
| `_distill_style_rules()` | `cm-agent/app/matreview.py:962-985` | **model** - destyluje 1-3 regułki z pary przed/po po ręcznej korekcie Tomasza |
| `add_style_rule()` | `cm-agent/app/matreview.py:294-303` | **Tomasz** - reguła podana wprost w rozmowie ("zapamiętaj na zawsze") |

Obie drogi lądują w tym samym polu, obie przechodzą przez ten sam zapis, i **regułki z obu idą
do KAŻDEJ generacji** przez `generate._learned_style`. Konsument nie wie, skąd wpis pochodzi.

Twoje uzasadnienie Z-3 mówi o ryzyku, że wpis nauczony jest **poleceniem, nie preferencją**.
To trafia wprost w organ pierwszy. Co do drugiego nie wypowiedziałeś się, a wpis w długu wskazuje
jako punkt zaczepienia wyłącznie destylację - ale to jest **moja notatka sprzed tygodnia,
nie Twoje zdanie**, więc nie traktuję jej jak rozstrzygnięcia.

**Jedna rzecz przemawia za szerszym cięciem.** Test `cm-agent/tests/test_nauka_jezyk_promptu.py`
opisuje regułki w kształcie **rozkazu** ("przed spójnikiem nie stawia się przecinka"). Z samego
pola nie da się odczytać, czy taka regułka przyszła z destylacji, czy od Tomasza. Pochodzenie
nie jest zapisywane.

---

## PYTANIE 1 (blokujące, bez niego nie startuję)

**Czy wyłączamy zapis w OBU drogach, czy tylko w destylacji modelu?**

- **A. Obie drogi.** Jedna bramka we wspólnym miejscu zapisu, więc żadna droga nie zostanie
  pominięta (AP-309: policz miejsca, zanim uznasz poprawkę za zrobioną). Odczyt istniejących
  regułek bez zmian. Koszt: Tomasz traci możliwość dyktowania nowych reguł stylu do czasu,
  aż zbudujemy warunek powrotu.
- **B. Tylko destylacja.** Węższe cięcie, zero utraty funkcji. Koszt: reguła podyktowana przez
  Tomasza też bywa w kształcie rozkazu i też idzie do każdej generacji, więc klasa ryzyka,
  o której piszesz, zostaje częściowo otwarta.

**Moja rekomendacja: A**, ale z warunkiem z pytania 2. Powód: różnica między "preferencją"
a "poleceniem" nie leży w tym, KTO regułkę napisał, tylko w tym, JAK jest sformułowana.
Człowiek dyktujący regułę stylu naturalnie mówi trybem rozkazującym.

## PYTANIE 2 (blokujące przy odpowiedzi A)

**Co bot ma odpowiedzieć, gdy Tomasz powie "zapamiętaj na zawsze"?**

Cicha odmowa jest wykluczona - to cała rodzina anty-wzorców "cisza wygląda jak sukces"
(AP-306, AP-310, AP-314, AP-315). Tomasz musi ZOBACZYĆ, że reguła nie została zapisana,
inaczej będzie liczył na regułę, której nie ma.

Do rozstrzygnięcia: czy odmowa ma być **samą odmową z powodem**, czy ma proponować
**drogę zastępczą** (zapis reguły jako notatka do przejrzenia przy odblokowaniu pętli).
Druga opcja jest droższa o kilkanaście linii, ale nie gubi tego, co Tomasz chciał zapamiętać.

## PYTANIE 3 (nieblokujące, ale tańsze teraz niż potem)

Warunek powrotu z długu brzmi: wpis dostaje **język i RODZAJ** (preferencja kontra polecenie)
**przy zapisie**, nie przy odczycie.

**Czy przy tej okazji zapisywać sam KSZTAŁT pola** (język, rodzaj, pochodzenie: model kontra
człowiek), nawet jeśli zapis nowych wpisów jest wyłączony? Koszt dziś prawie zerowy, a przy
odblokowaniu pętli nie trzeba będzie wracać do tego drugi raz. Ryzyko: to wykracza poza to,
co zatwierdziłeś w Z-3, więc pytam zamiast robić.

## PYTANIE 4 (zaległe z 19.08, niezależne od bloku B)

**Rozgraniczenie AP-311 kontra AP-317 czeka na Twoje potwierdzenie.** Żeby AP-317 miał rację
bytu obok AP-311, trzeba było podważyć zdanie zapisane wcześniej w AP-311 ("Nie były, albo były
poza zasięgiem systemu - to AP-311"). Nowy test rozstrzygający, wpisany do obu plików:

> Czy istnieje poprawka, po której ta pustka stałaby się wiarygodna?
> Tak - AP-311, szukaj wady. Nie, bo kanał nie ma żadnego połączenia z bazą - AP-317,
> zmieniasz sposób czytania, nie system.

Nie jestem autorem wpisu AP-311, więc tego nie przesądzam sam. Jeśli odrzucisz, zdejmę AP-317
z indeksu i przeniosę treść do AP-311 jako rozszerzenie.

---

## CZEGO NIE PYTAM, BO JEST ROZSTRZYGNIĘTE

- Odczyt istniejących wpisów zostaje - powiedziałeś to wprost w Z-3.
- Miny w callbacku publishera nie ruszamy - Twoja decyzja bez zmian.
- Blok A robi Tomasz ręcznie, nie dubluję.
- Kolejność bloków (F, potem B+C, potem D+E, na końcu G) zatwierdzona 19.08.

## CO SIĘ DZIEJE, ZANIM ODPOWIESZ

Blok C (D-020, blokada `publish_mode='webhook'` w kodzie) jest w robocie, bo miał autonomię
bez pytania. **Nic z niego nie trafi do repo bez zgody Tomasza** - commity trzymam u siebie.
Jeśli C przyniesie znalezisko dotykające Twoich decyzji, dopiszę je do tego pliku, zanim
cokolwiek scalę.
