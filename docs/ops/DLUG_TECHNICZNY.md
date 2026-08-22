# Dlug techniczny AGS (lista zywa)

Rzeczy ZNANE i SWIADOMIE odlozone. Powod istnienia tego pliku (polecenie Managera 26/07):
dlug zapisany z data nie zostaje odkryty powtornie za miesiac jako "nowy blad".

Zasada wpisu: co jest nie tak, gdzie to siedzi (plik:linia), czym grozi, kiedy to bolalo
albo kiedy zabolisz. Wpis znika z listy dopiero razem z poprawka.

---

## REGULA BRANIA DLUGU (ustanowiona 02/08/2026 przez Managera)

**Dlug opisany raz i nieodswiezany starzeje sie tak samo jak kod.**

Biorac pozycje z tej listy: **NAJPIERW sprawdz, czy opis nadal opisuje rzeczywistosc, i dopiero
potem naprawiaj. Jesli opis sie rozjechal - popraw OPIS i zglos, zanim ruszysz kod.**

Trzy dowody z jednego dnia (02/08/2026):

- **D-003** mial notatke "dzis USPIONA, `contact_person` NULL we wszystkich dwunastu wierszach"
  z 26/07. Odczyt 02/08: **33 wiersze z wypelniona osoba na 133**. Objaw byl juz ZYWY od
  tygodnia, a falszywe "brak kontaktu" pokazywalo sie przy prawdziwych prospektach.
- **D-011** w ogole NIE BYL WADA - odczyt obalil przeslanke wpisu (patrz AP-311 na opak).
- **D-005** byl naprawialny, tylko nie WSTECZ, jak zakladal wpis. Wystarczylo przestac wymagac
  naprawy wstecznej i pozwolic karcie rozbroic sie przy pierwszym tapnieciu.

Czyli na dziewiec zamknietych tego dnia **trzy wpisy myllily** o wlasnym przedmiocie. Notatka
w dlugu jest danymi jak kazde inne - i jak kazde inne wymaga sprawdzenia przed uzyciem
(AP-311 w obie strony).

---

## D-001 [ZAMKNIETE 02/08/2026]: Regula weekendowa pilnowana tylko w jednym z czterech miejsc

**NAPRAWIONE.** Powstala JEDNA funkcja `slots.day_ok(channels, day, is_article)` i wolaja ja
teraz wszystkie cztery trasy zapisujace slot:

| trasa | jak bylo | jak jest |
|---|---|---|
| `slots.next_slot` | jedyna, ktora znala regule | bez zmian (`_li_ok`) |
| planer | slot od modelu, walidowany TYLKO jako ISO | odrzuca pozycje z `[dzien]` w powodzie |
| guzik "koniec kolejki" | `MAX(slot)+1 dzien` - z PIATKU robil SOBOTE | przesuwa do najblizszego dozwolonego dnia |
| re-slotter | siatka gniazd bez sprawdzenia dnia | pomija dni zakazane |

**Szczegol, ktory latwo bylo przeoczyc:** trasy trzymaja kanal w ROZNYCH ksztaltach - lista
(planer, karta) albo napis (re-slotter). Gdyby `day_ok` przyjmowalo tylko liste, re-slotter
cicho ominalby guard, mimo ze "wywolanie jest". Funkcja przyjmuje oba ksztalty, a test to pilnuje.

Test: `cm-agent/tests/test_regula_dnia.py` (19 asercji), w tym asercja **AP-309** sprawdzajaca
w ZRODLE, ze kazda z czterech tras faktycznie o regule pyta - zeby nastepna nowa trasa nie
powtorzyla tego dlugu po cichu.

Ponizej oryginalny opis, dla historii.


**Zapisany 26/07/2026** (decyzja Managera: nie naprawiac teraz, zapisac).

Sobota jest twardo wycieta dla LinkedIna w `cm-agent/app/slots.py:109-115` (`_li_ok`), ale
`_li_ok` wolane jest WYLACZNIE z `next_slot`. Trzy pozostale drogi zapisujace slot dnia
tygodnia nie znaja:

- **planer** (`planner.py:312-325`) - slot przychodzi od modelu, walidowany tylko jako ISO,
  chroniony samym promptem,
- **guzik "koniec kolejki"** w kartach (`matreview.py:377-390`, `720-722`) - bierze
  `MAX(slot)+1 dzien`, wiec **z piatku robi sobote jednym tapnieciem**,
- **re-slotter** (`reslot.py:116-131`) - kanal z argv.

Zaden straznik nizej ani Scheduler n8n dnia juz nie sprawdza
(`grep getDay|weekday|dayOfWeek n8n-workflows/` = zero trafien).

Dodatkowo `slots.py:135` robi `continue` na CALY dzien, wiec sobotni zakaz LinkedIna zabiera
slot takze kanalowi X przy materiale wielokanalowym.

**Czym grozi:** post LinkedIn w sobote wbrew kanonowi 19/07, bez zadnego ostrzezenia.
**Docelowo:** jedna funkcja `slots.day_ok(channel, day, is_article)` wolana z czterech miejsc
(wzorzec: straznik meta-naglowka w `channels.py:60-64`).

---

## D-002 [ZAMKNIETE 02/08/2026]: Test kadencji pada po zamknieciu okna publikacji

**NAPRAWIONE.** `slots.py` i `reslot.py` dostaly jedno posrednictwo `_teraz()`, ktore w produkcji
zwraca dokladnie to co wczesniej (`datetime.now(WARSAW)`), a w tescie jest podmieniane na staly
moment (sroda 14:00 dla kadencji, sroda 09:00 dla re-slottera). Oba testy nie odwoluja sie juz
**w ogole** do zegara systemowego - zero wystapien `now()`. Zestaw: **18/18 zielonych**,
po raz pierwszy. Ponizej oryginalny opis, dla historii.



**Zapisany 26/07/2026** (zlapany przy uruchamianiu calego zestawu o 23:20).

`cm-agent/tests/test_kadencja_sufit.py:83` sprawdza "2 z 5 zajete dzis -> slot jeszcze dzis",
liczac `datetime.now()`. Okno kanalu X to 13:00-22:00, wiec **po 22:00 test pada zawsze**,
niezaleznie od kodu. Zweryfikowane: pada identycznie na czystym HEAD.

**Czym grozi:** wieczorna sesja widzi czerwony test i traci czas na szukanie regresji, ktorej
nie ma. Albo, gorzej, przyzwyczaja sie do czerwonego i przeoczy prawdziwa.
**Docelowo:** wstrzykiwac "teraz" do `next_slot` w tescie zamiast polegac na zegarze.

**DRUGI PLIK, ta sama wada (dopisane 27/07):** `cm-agent/tests/test_reslot.py`, przypadek
"#4 w przyszlosci, ludzka minuta, w oknie". Pada okolo poludnia i po poludniu, bo siatka gniazd
liczona z okna 13:00-22:00 czesciowo wypada juz w przeszlosci. Zweryfikowane stashem: pada
identycznie na czystym HEAD. Czyli wada dotyka DWOCH plikow testowych (AP-309) i obie naprawy
sa te sama poprawka: wstrzykniecie zegara zamiast `datetime.now()`.

---

## D-003 [ZAMKNIETE 02/08/2026]: Kolumny kontaktowe lejka bez drogi zapisu przez czlowieka

**NAPRAWIONE, oba objawy.**

1. **Etykieta klamala.** `pipeline_text` POBIERALO `contact_person`, ale go NIE POKAZYWALO,
   wiec prospekt z zapisana osoba dostawal "⚠️ brak kontaktu". Ta sama rodzina co AP-312
   i "BRAK nastepnego kroku" z 27/07: dane byly poprawne, klamal WIDOK. Osoba wyswietla sie
   teraz PIERWSZA - dojscie przez czlowieka jest cenniejsze niz numer ze strony.
2. **Nie bylo recznej drogi zapisu.** `pipeline_add` i `pipeline_move` dostaly pola
   `contact_person` / `contact_email` / `contact_phone`. Opis pola mowi wprost, ze mieszka tam
   takze DOJSCIE ("przez Piotra Hamryszaka") - to byl konkretny przypadek, ktory ten dlug zrodzil.

**Wpis byl PRZETERMINOWANY w czesci "dzis uspiona":** notatka z 26/07 mowila, ze `contact_person`
jest NULL we wszystkich dwunastu wierszach. Odczyt z 02/08 pokazal **33 wiersze z wypelniona
osoba** na 133 - czyli drugi objaw byl juz ZYWY i falszywe "brak kontaktu" zdazylo sie pokazac.

Test: `cm-agent/tests/test_kontakt_lejka.py` (14 asercji). Zestaw 21/21.

Ponizej oryginalny opis, dla historii.


**Zapisany 26/07/2026** (sekcja 4.7 diagnozy; wada realna, dzis USPIONA).

`_zapisz_kontakt` (`sales.py:938-955`) wolany jest wylacznie z automatow, a schematy
`pipeline_add` i `pipeline_move` nie maja pol kontaktowych. Nie da sie recznie dopisac
telefonu, maila ani osoby do wiersza lejka. Do tego `pipeline_text` (`sales.py:142-143`)
nie czyta `contact_person`, wiec "brak kontaktu" zapali sie takze przy wypelnionej osobie.

**Dlaczego dzis nie boli:** sonda 26/07 pokazala `contact_person` NULL we wszystkich
dwunastu wierszach lejka, wiec drugi objaw jeszcze nie wystapil.
**Czym grozi:** adamietz.pl ma ciepla sciezke przez Piotra Hamryszaka i nie ma jej gdzie
zapisac - wiedza o dojsciu zyje poza systemem.

**Aktualizacja 31/07:** teczka prospekta domyka POLOWE tego dlugu - `zapisz_tekst` daje czlowiekowi
droge zapisu tresci wysylki oraz nastepnego kroku z terminem (`sales_pipeline.next_step`, DDL 036).
Pol kontaktowych (osoba, telefon, mail przy wierszu lejka) nadal **nie da sie** wypelnic recznie,
wiec dojscie przez Piotra dalej nie ma swojego miejsca. Dlug zostaje otwarty w tej czesci.

---

## D-004: Materialy przygotowane poza baza sa dla agenta niewidzialne

**Zapisany 27/07/2026** (Manager: zapisac jako swiadomy dlug, nie budowac przed pierwsza sprzedaza).

Agent Sprzedazy zaproponowal Tomaszowi przygotowanie gotowca i researchu pod Adamietza na 28/07,
podczas gdy **material dla Piotra istnieje od 25/07**: notatka dla posrednika plus jednostronicowka
do przekazania decydentowi, oparta na pelnym raporcie wywiadowczym. Agent nie mial jak wiedziec -
plik lezy w `docs/research/prospekci/` POZA gitem (celowo, origin jest publiczny) i poza baza.

**Czym grozi:** agent proponuje robote, ktora jest zrobiona, i to akurat przy najwiekszym dealu
w lejku. Kosztuje zaufanie do agenta bardziej niz przeoczenie, bo wyglada na niekompetencje.

**Doraznie (zrobione):** notatka w `sales_pipeline.notes` prospekta plus regula w prompcie
Sprzedawcy: przeczytaj notatki, ZANIM zaproponujesz przygotowanie czegokolwiek.

**Docelowo:** minimalny rejestr materialow per prospekt (co powstalo, gdzie lezy, jaki status).
Warunek wejscia: po pierwszej platnej sprzedazy, zgodnie z kanonem "nie budujemy systemow przed
pierwsza sprzedaza".

## D-006 [ZAMKNIETE 02/08/2026]: Status `dispatching` ma nazwe, ktora obiecuje co innego niz znaczy

**NAPRAWIONA CZESC WIDOKOWA, bez dotykania kontraktu.** Dwie zmiany w `matreview.py`:

1. Etykieta "W PUBLIKACJI" -> **"ROZESLANY DO KOLEJKI"**. Mowi, CO SIE STALO, a nie co sie
   wlasnie dzieje - czyli nie obiecuje juz sekund przy stanie, ktory trwa dniami.
2. Nowy `_stan_rozsylki()` dokleja do karty **ile wierszy czeka z ilu i na kiedy** (najblizszy
   ORAZ ostatni termin - z ostatniego wiadomo, jak dlugo stan jeszcze potrwa). Jedno zapytanie
   na material, nie N+1.

**Sedno:** zgloszenie brzmialo "nie da sie powiedziec, czy wysyla, czy zawisl". Sama nazwa tego
nie rozstrzygnie i rozstrzygnac NIE MOZE. Rozstrzyga liczba wierszy i ich terminy - i teraz sa
widoczne. Przy okazji powstal jedyny przypadek, ktory naprawde wyglada na zawieszenie i da sie
go odroznic: **zero oczekujacych wierszy przy materiale nadal w tym stanie** - karta ostrzega
wprost. Test: `cm-agent/tests/test_stan_rozsylki.py` (13 asercji).

**NIE ZAMYKALO D-008** (przemianowanie samej WARTOSCI statusu). Zmiana etykiety wyswietlanej
nie dotykala kontraktu miedzy warstwami. **D-008 zostalo zamkniete 03/08/2026** - wartosc
w bazie nazywa sie dzis `handed_off` i mowi to samo, co etykieta z D-006.

Ponizej oryginalny opis, dla historii.


**Zapisany 27/07/2026** (zgloszenie Managera; polecenie: zapisac jako dlug, nie naprawiac dzis).

**Zgloszenie brzmialo:** "status dispatching nie ma limitu czasu, post z 13:30 wisial ponad pol
godziny i ani system, ani CM nie potrafili powiedziec, czy jest w trakcie wysylki, czy zawisl".
Podejrzana przyczyna: tekst ~2000 znakow odrzucony przez API jako za dlugi.

**ODCZYT PRZED NAPRAWA (27/07, cztery zapytania read-only) OBALIL OBIE HIPOTEZY:**

1. **Zaden post nie wisi.** Siedem materialow w `dispatching`, u kazdego liczba wierszy
   "po terminie ponad 2h" wynosi ZERO. Wszystkie oczekujace wiersze maja sloty w przyszlosci
   (od 27/07 21:02 do 04/08 14:15).
2. **Limit czasu ISTNIEJE:** `worker._dispatch_timeout_alert`, prog `config.DISPATCH_TIMEOUT_H = 2`.
   Liczy od SLOTU WIERSZA, nie od dispatchu - swiadomie, bo poprzednia wersja alarmowala o 15:15
   o postach ze slotami na 20:10, a falszywe alarmy ucza ignorowania prawdziwych (komentarz A6,
   21/07). Nie alarmowal, bo nie mial o czym.
3. **Hipoteza o dlugosci bez poparcia.** X opublikowal przez 10 dni 28 postow, najdluzszy
   556 znakow; najdluzszy `scheduled` w kolejce ma 563. LinkedIn publikowal 1549-2016 znakow,
   w kolejce ma 2392-2621 przy limicie platformy 3000. Zaden wiersz nie przekracza limitu swojej
   platformy. Nie ma tez wiersza ze slotem 13:30.

**PRAWDZIWA WADA, ktora zgloszenie odslonilo** (od 29/07 ma wlasny anty-wzorzec: **AP-312**,
a sama nazwa idzie do przemianowania jako **D-008**):

`dispatching` brzmi jak stan PRZELOTNY ("wysylam"), a znaczy "rozeslane do kolejki, czekam az
WSZYSTKIE wiersze serii osiagna stan terminalny" - czyli stan, ktory normalnie trwa DNI. Szesc
materialow siedzi w nim 51 godzin i jest to poprawne: re-slotter rozrzucil serie na dni, wiec
seria konczaca sie 4 sierpnia bedzie w `dispatching` przez dziewiec dni.

Czlowiek czyta nazwe i spodziewa sie sekund. System ma na mysli tydzien. **To jest AP-311 od
strony NAZEWNICTWA:** nie "stan, ktorego nikt nie potrafi zweryfikowac", tylko stan, ktorego
nazwa wprowadza w blad. Manager wyciagnal rozsadny wniosek z mylacej etykiety - dokladnie tak,
jak Agent Sprzedazy przy "BRAK nastepnego kroku".

**CO ZOSTAJE DO ZROBIENIA (druga polowa zgloszenia, trafna w stu procentach):**

Nigdzie nie widac, OD KIEDY material jest w `dispatching` i NA CO czeka. Poprawka jest tania:
przy kazdej pozycji w tym stanie pokazac liczbe wierszy oczekujacych i najblizszy slot -
"dispatching, czeka 5 wierszy, najblizszy slot 28/07 09:00". Wtedy roznica miedzy "wysylam od
dwoch minut" a "wisi od trzydziestu" jest widoczna bez patrzenia na zegarek.

Rozwazyc takze przemianowanie stanu na cos, co nie klamie ("w kolejce", "rozeslane"), ale to
zmiana kontraktu miedzy tabelami i n8n, wiec osobna decyzja.

**Czym grozi, jesli zostawimy:** przy czterech publikacjach dziennie na dwoch kanalach czlowiek
bedzie regularnie pytal "czy to wisi", a odpowiedz bedzie za kazdym razem wymagala sondy do bazy.
Prawdziwy zwis utonie kiedys w tych falszywych alarmach.

## D-008 [ZAMKNIETE 03/08/2026]: Status `dispatching` przemianowany na `handed_off`

**NAPRAWIONE.** Wartosc `content_items.status` nazywa sie `handed_off`, zyje w jednym miejscu
(`config.STATUS_HANDED_OFF`), a stara nazwa nie ma prawa wrocic ani do kodu, ani do DDL -
pilnuje tego `cm-agent/tests/test_d008_handed_off.py` (24 asercje).

**DLACZEGO `handed_off`, a nie `rozeslane` z tego wpisu ani `awaiting_publication`**
(decyzja Tomasza 03/08, po adwersarzach): stan konczy sie, gdy wiersze kolejki przestaja sie
ruszac - **obojetnie czym**. `worker._DISPATCH_OK` zawiera `held`, czyli gotowiec do RECZNEJ
wklejki: przy LinkedInie material wychodzi ze stanu po kilkudziesieciu sekundach, a publikacja
dopiero czeka na czlowieka. Nazwa obiecujaca publikacje odtworzylaby **AP-312 wewnatrz poprawki
na AP-312**. Osobno: `agent_registry.current_gate` uzywa juz przedrostka `awaiting_*`
w znaczeniu "czekam na bramke zatwierdzenia". `handed_off` to slowo, ktore kodebaza wybrala
sama, zanim ktokolwiek przemianowal wartosc: *"dispatch = HAND-OFF, nie publikacja"* (`worker`)
i *"Every mode here just HANDS OFF"* (`channels`).

**WDROZONE 03/08/2026 wieczorem**, okno 19:28:30-19:42 (13 minut, publikacje staly, kolejka byla
pusta, nic nie przepadlo). Przebieg: `docs/ops/OKNO_d008_03082026.md`, sekcja na koncu.

**CZWARTE USTALENIE, z samego okna: MIGRACJA DANYCH BYLA ZEROWA.** Odczyt przy stojacych
pisarzach pokazal **zero** wierszy w starej wartosci - siedem materialow z 27/07 przez tydzien
dopublikowalo swoje serie i siedzi w `published`. Wpis ponizej opisywal stan sprzed tygodnia
i zestarzal sie tak samo jak D-003 czy D-011. Przemianowanie bylo potrzebne w KODZIE,
w ograniczeniu CHECK i w wezle n8n - w danych nie bylo czego przemianowywac.

**TRZY USTALENIA, KTORE ROZJECHALY SIE Z OPISEM PONIZEJ** (regula brania dlugu zadziala):

1. **Inwentarz "30 miejsc" mieszal DWA ROZLACZNE SLOWNIKI.** Z 32 trafien w `cm-agent/app/`
   do materialu nalezalo **20**, do `post_queue` - **11**, jedno bylo neutralnym komentarzem.
   `post_queue.status` MA WLASNA wartosc `dispatching` i znaczy ona co innego (jeden wiersz
   oddany subagentowi). Podmiana wszystkich 32 zerwalaby dopasowanie w kolejce publikacji.
2. **Zywy workflow n8n ma OBIE wartosci w JEDNYM zapytaniu.** `AGS Scheduler v1`
   (`x1jJEbcWAe3FnpCa`), wezly `Mark Published` i `Mark Published LI`:
   `ci.status='dispatching'` (do zmiany) oraz `q.status IN (...,'dispatching')` (do zostawienia).
   Podmiana "po calym tekscie" nie dawalaby zadnego bledu - SQL nadal bylby poprawny.
3. **Pisarzy do `content_items` jest TRZECH, nie jeden.** Poza `cm-agentem` pisza tam dwa
   workflow n8n: `AGS Scheduler v1` (cron co minute) i `AGS HITL Handler v1.0` (guziki bota,
   wezel `Cm Resolve Gate`, z pominieciem `cm-agenta`). Trzeci umknal wszystkim wczesniejszym
   odczytom, bo **nie zawiera slowa `dispatching`** - trzeba bylo szukac nazwy TABELI, nie
   wartosci. Ostatecznie gaszone byly dwa pierwsze; trzeci ma predykat
   `status='needs_approval'`, wiec nie potrafi ani utworzyc, ani skonsumowac migrowanej wartosci.

**Jak wykonane:** `cm-agent/db/042_status_handed_off.sql` (nowa wartosc OBOK starej),
`docs/ops/SQL_d008_handed_off_03082026.sql` (migracja z bramka na liczbie wierszy, kontrola
INNYM mechanizmem, SQL odwrotny), `n8n-workflows/patches/d008-handed-off-03082026.cjs`
(chirurgiczny PUT, ktory odmawia dzialania, gdy liczby sie nie zgadzaja), procedura okna:
`docs/ops/OKNO_d008_03082026.md`.

**Powiazane:** D-006 (widok, ZAMKNIETE 02/08), **D-008b** (usuniecie starej wartosci
z ograniczenia `CHECK` - swiadomie odlozone, ponizej).

Ponizej oryginalny opis, dla historii.


**Zapisany 29/07/2026** (decyzja Managera: "nie dzis, ale dopisz do listy z data").
Bezposrednia konsekwencja ustanowienia **AP-312**.

`content_items.dispatching` brzmi jak stan PRZELOTNY ("wysylam"), a znaczy "rozeslane do kolejki,
czekam az WSZYSTKIE wiersze serii osiagna stan terminalny" - stan, ktory normalnie trwa DNI.
Manager zglosil 27/07 zawieszony post; odczyt pokazal siedem materialow w tym stanie, wszystkie
zdrowe, najstarszy 51 godzin i poprawnie, bo jego sloty siegaly 4 sierpnia.

Czlowiek czyta nazwe i spodziewa sie sekund. System ma na mysli tydzien.

**Kandydaci na nazwe:** `w_kolejce`, `rozeslane`, `czeka_na_sloty`. Ostatni jest najdluzszy
i najuczciwszy - mowi doslownie, na co stan czeka.

**Dlaczego nie dzis:** to zmiana KONTRAKTU miedzy trzema warstwami naraz. Wartosc wystepuje
w `content_items.status`, w filtrach Pythona (`worker.reconcile_publications` pyta
`WHERE status='dispatching'`, `slots.assign_if_needed` i dwie trasy `conversation` maja ja
w liscie `status IN (...)`) oraz w SQL wezlow n8n. Przemianowanie w polowie zostawi system,
ktory czesciowo szuka starej wartosci, a czesciowo nowej - i to bedzie gorsze niz mylaca nazwa.

**Warunek wykonania:** osobna decyzja, osobne okno, komplet grepem PRZED zmiana (AP-309),
oraz migracja danych i PUT do n8n z rytualem backup / PUT / deactivate+activate.

**Powiazane:** D-006 (widok nie pokazuje, od kiedy material wisi i na co czeka) - te dwie
naprawy warto zrobic razem, bo obie dotykaja tego samego stanu i tej samej niejasnosci.

## D-008b: Stara wartosc `dispatching` w ograniczeniu CHECK - **ZAMKNIETE 10/08/2026**

**Zapisany 03/08/2026, zamkniety 10/08/2026.**

> ### WYKONANE 10/08/2026
>
> Warunek wejscia spelniony z nawiazka: nie jeden, a **dwa** pelne cykle publikacji bez recznej
> pomocy (`#344` 04/08 16:01, `#358` 05/08 16:01). Skrypt przeszedl, ograniczenie zna dzis
> czternascie wartosci i **nie ma wsrod nich `dispatching`**. Rozklad przy operacji: `rejected`
> 139, `published` 87, `archived` 35, `draft` 28, `proposed` 20, `needs_approval` 1, `brief` 1 -
> zero w `approved` i zero w `handed_off`, wiec nic nie wisialo w locie.
>
> Zdjete takze z czterech plikow DDL (`001`, `003`, `010`; `042` zostaje z OBIEMA wartosciami
> celowo - to zapis okna migracyjnego, nie stan docelowy, i ma teraz o tym ramke w naglowku).
> Obraz `cm-agent:prev-d008` mozna skasowac.
>
> **Wada znaleziona w samym skrypcie przy wykonaniu (AP-314 w pliku, ktory go zwalcza):**
> `DROP CONSTRAINT` i `ADD CONSTRAINT` staly poza transakcja. `DROP` udaje sie zawsze, `ADD`
> moze paść na dowolnym wierszu z wartoscia spoza listy - bez transakcji skutek to tabela
> **bez zadnego ograniczenia** przy bledzie wygladajacym na "nic sie nie stalo". Dolozone przed
> uruchomieniem: `BEGIN/COMMIT`, odczyt rozkladu wartosci przed operacja i druga bramka, ktora
> **nazywa** wartosc spoza listy zamiast surowego `violates check constraint` juz po fakcie.

### Zapis pierwotny (03/08) - kontekst decyzji

Ograniczenie `content_items_status_check` zna dzis **obie** wartosci: `handed_off` (uzywana)
i `dispatching` (nieuzywana, zero wierszy). To jest stan **swiadomie przejsciowy**.

**Dlaczego nie od razu.** Dopoki stara wartosc siedzi w ograniczeniu, **droga odwrotu istnieje**:
zamrozony obraz `cm-agent:prev-d008` da sie podniesc, bo baza nadal przyjmie to, co on zapisuje.
Zwezenie slownika odbiera te mozliwosc, a robi to w chwili, gdy nowy kod ma za soba minuty
dzialania, nie doby.

**Czym grozi, jesli zostawimy:** slownik z martwa wartoscia uczy, ze slowniki wolno zasmiecac.
Za pol roku nikt nie bedzie pamietal, ktora z dwoch jest ta zywa - a to jest zarodek nowego
AP-312. Osobno: dopoki wpis jest otwarty, nie wolno skasowac obrazu `cm-agent:prev-d008`.

**Gotowe do uruchomienia:** `docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql` (ma `lock_timeout`
i bramke odmawiajaca dzialania, gdy ktokolwiek siedzi jeszcze w starej wartosci). Po nim trzeba
zdjac stara wartosc takze z czterech plikow DDL - kazdy ma w tym miejscu komentarz wskazujacy
na ten plik.

**Warunek wejscia:** minal co najmniej jeden PELNY cykl publikacji na nowym obrazie
(`approved -> handed_off -> published` bez recznej pomocy) i nikt nie planuje juz cofac obrazu.

## D-015 [ZAMKNIETE 19/08/2026]: ktora godzine widzi czlowiek

**Zapisany 03/08/2026, meldunek zamkniety 10/08, KARTA I RESZTA POWIERZCHNI ZAMKNIETE 19/08.**

**Wszystkie SIEDEM powierzchni pokazujacych godzine publikacji licza ja TYM SAMYM kodem**
`worker._godzina_publikacji`, czyli `max(slot planu, czas kolejki)`.

Rozstrzygniecie 19/08 (koordynator): karta pokazuje DOKLADNIE to, co meldunek. Nie czas kolejki,
nie oba czasy obok siebie, nie slot planu. Powod: dwa organy pokazujace czlowiekowi te sama rzecz
roznymi liczbami to gotowy AP-312, a "oba czasy" przenosi na Tomasza rachunek, ktory ma wykonac
kod. Jedna prawda, jedno zrodlo (AP-309).

Poprawione: karta decyzyjna `/karty` (`matreview._card`), karta podgladu (`_view_card`), paragon
po "Na koniec kolejki", paragon po edycji (`apply_edit`), raport dzienny i `stan_gry`
(`reports._godzina_wiersza`), meldunek dnia subagenta (`proactive.subagent_briefs`). Meldunek bota
byl poprawny od 10/08 i nie zostal tkniety. Widoki PLANU (`planner`) zostaja przy slocie swiadomie
- dotycza materialow `proposed`, ktore nie maja jeszcze wiersza kolejki, wiec slot jest tam jedyna
i poprawna prawda.

**ODCZYT OBALIL POLOWE TABELI Z 03/08.** Wpis mowil, ze raport dzienny i `stan_gry` pokazuja
prawde, bo pokazuja czas z kolejki. Korekta z 10/08 udowodnila, ze sam czas kolejki myli sie
dokladnie tak samo czesto jak sam slot planu, tylko w druga strone. Meldunek poprawiono wtedy,
**a raportu nikt nie przeliczyl, bo tabela nadal mowila o nim "TAK"** - i ta polowa przelezala
jeszcze dziewiec dni. To ta sama lekcja co AP-316, o warstwe wyzej: **tabela stanu starzeje sie
grozniej niz opis problemu, bo wyglada na sprawdzona.**

**CZEGO KARTA NIE ROBI: NIE ZGADUJE (AP-317).** Material bywa ogladany PRZED wysylka i wtedy
wiersza kolejki jeszcze nie ma, czyli dokladnej godziny NIE MA. Karta pisze wtedy slot planu
z dopiskiem, ze dokladnej nie zna, i podaje przedzial, ktory naprawde znamy (bramka `claim_item`
od dolu, `humanize_slot` +15 min od gory). Podstawienie slotu jako pewnika byloby domyslem
zapisanym jak fakt.

Odczyt: `matreview._czas_kolejki`, JEDNO zapytanie na wyrenderowana karte, wzorzec `_stan_rozsylki`
z D-006. Raporty nie placa nic dodatkowego, bo `ci.scheduled_for` przyszlo istniejacym JOIN-em.

Zachowanie: `cm-agent/tests/test_godzina_na_karcie.py` (sciezka alarmu = kolejka POZNIEJ niz slot,
sciezka odwrotna z dowodow #344 i #358, brak kolejki, plus anty-regresja pilnujaca, ze regula nie
zostala przepisana w karcie; przy cofnietej poprawce pada siedem kontroli, sprawdzone przez
koordynatora). Zestaw 37/37. Dokumentacja: `docs/komponenty/karty-hitl.md`,
`docs/komponenty/kolejka-publikacja.md`.

---

## D-015 (tresc oryginalna z 03/08, zostawiona dla kontekstu)

**Zapisany 03/08/2026** (zgloszenie Tomasza: "powinienem tez realna godzine miec w meldunku").
**MELDUNEK ZAMKNIETY 10/08. KARTA w `/karty` zostaje otwarta.**

> ### DOWOD W BIEGU 10/08, 18:09
>
> Material "Granica miedzy dwoma agentami" dostal meldunek **"CM przydzielil slot: Tue 11/08 16:00"**.
> Pelna godzina jest sama w sobie dowodem: `humanize_slot` ma warunek `cand.minute % 15 != 0`,
> wiec **nigdy nie zwraca rownej godziny**. Skoro meldunek podal 16:00, nie podal czasu kolejki -
> podal slot planu, bo kolejka wypadla wczesniej. To jest dokladnie ten przypadek, w ktorym
> poprzednia wersja (`d5cd43e`) obiecywalaby godzine, ktora nie moze nastapic.
> Domkniecie end-to-end: publikacja 11/08 ok. 16:00-16:01.
>
> Co ZOSTAJE otwarte: karta w `/karty` czyta `content_items`, wiec przy kolejce wypadajacej
> POZNIEJ niz slot planu pokazuje do 15 minut za wczesnie. Wymaga dodatkowego odczytu per karta
> (wzorzec `_stan_rozsylki` z D-006) i osobnej decyzji, czy karta ma pokazywac czas kolejki,
> oba czasy, czy zostac przy slocie.

> ### KOREKTA 10/08/2026 - ten wpis byl przez tydzien POL-PRAWDA
>
> Zdanie "post wychodzi o godzinie z KOLEJKI" (takze w tytule dlugu) jest **nieprawdziwe
> w polowie przypadkow**. Realny czas publikacji to **`max(slot planu, czas kolejki)`** plus
> do minuty na tik Schedulera, bo pilnuja go DWIE bramki z warunkiem `<= NOW()`:
> `db.claim_item` nie bierze materialu `approved` przed slotem planu, a Scheduler publikuje
> dopiero wiersz w stanie `scheduled`, ktory powstaje w dispatchu, czyli PO tamtej bramce.
> `humanize_slot` losuje symetrycznie +/-15 min, wiec gdy trafi WCZESNIEJ, ta godzina jest martwa.
>
> **Dowod, dwa na dwa:** `#344` kolejka 15:49, slot 16:00 -> publikacja 04/08 **16:01**;
> `#358` kolejka 15:50, slot 16:00 -> publikacja 05/08 **16:01**. Poszlaka: wszystkie
> zaobserwowane publikacje (13:48, 16:10, 16:31, 16:59, 17:48, 19:12, 20:23, 10:01) wypadaja
> PO najblizszym okraglym slocie, ani jedna przed.
>
> Poprawka `d5cd43e` z 03/08 byla wiec dobra dokladnie tak samo czesto jak kod, ktory poprawiala:
> stara wersja mylila sie, gdy kolejka wypadala pozniej, nowa - gdy wczesniej. Domkniete regula
> w `worker._godzina_publikacji`; `cm-agent/tests/test_godzina_publikacji.py` trzyma obie stare
> wersje jako anty-regresje, zeby nastepna "uproszczajaca" poprawka od razu widziala, ze byly juz
> probowane. **Lekcja: przy dwoch liczbach opisujacych to samo sprawdz, ktora BRAMKA je czyta,
> zanim uznasz jedna za prawdziwa.**
>
> Tabela nizej pochodzi z 03/08 i pokazuje TAMTEN stan wiedzy - zostawiona swiadomie,
> zeby bylo widac, jak wygladala pol-prawda, ktora przez tydzien nikomu nie zgrzytala.

Kanon 19/07 mowi, ze publikacje wychodza o NIEPELNYCH godzinach: `post_queue.scheduled_for`
dostaje czas po humanizacji (do 15 minut obok), a `content_items.scheduled_for` trzyma czysty
slot planu. **Ta roznica jest ZAMIERZONA** - to nie jest rozjazd do naprawienia.

Wada jest w tym, ktory z dwoch czasow widzi czlowiek:

| powierzchnia | pokazuje | czy to prawda o publikacji |
|---|---|---|
| meldunek bota o slocie | **czas z kolejki** (od 03/08) | TAK |
| raport dzienny, `stan_gry` | czas z kolejki | TAK |
| **karta materialu (`/karty`)** | **czysty slot z `content_items`** | **NIE, do 15 minut obok** |

Dowod z 03/08: bot zameldowal `Tue 04/08 16:00`, a w kolejce stalo `04/08 15:49`. Tomasz
zobaczyl obie liczby i zapytal, ktora jest prawdziwa - **i to jest caly problem**. To AP-312
w wydaniu liczbowym: powierzchnia obiecuje godzine, ktora nie nastapi.

**Dlaczego nie naprawione od razu:** karta czyta material, a realny czas siedzi w wierszu
kolejki - potrzebny jest dodatkowy odczyt per karta (wzorzec `_stan_rozsylki` z D-006, jedno
zapytanie, nie N+1). To osobna zmiana w innej warstwie niz meldunek i osobna decyzja, czy karta
ma pokazywac czas kolejki, oba czasy, czy zostac przy slocie planu.

**Czym grozi, jesli zostawimy:** przy czterech publikacjach dziennie czlowiek regularnie widzi
dwie rozne godziny dla tego samego posta i za kazdym razem musi sie zastanowic, ktora obowiazuje.
Dokladnie ten koszt, ktory D-006 i D-008 usuwaly przy nazwie stanu.

## D-007 [ZAMKNIETE 02/08/2026]: Operacja hurtowa nie zostawia sladu czytelnego dla DRUGIEGO agenta

**NAPRAWIONE: rejestr operacji + stempel na wierszach (DDL 040, `app/operacje.py`).**

`bulk_operations` trzyma op_id CZYTELNY DLA CZLOWIEKA (np. `wycofanie-serii-29072026`), date,
autora, opis PO LUDZKU, uzyty warunek i liczbe wierszy. `content_items.op_id` i `post_queue.op_id`
nios� ten identyfikator. Drugi agent wycina dokladny zbior JEDNYM warunkiem i czyta, co to bylo.

**DLACZEGO REJESTR, A NIE `status_source`:** kolumna symetryczna do `slot_source` powiedzialaby,
jakiego RODZAJU pisarz ustawil status. To za malo - dwie operacje tego samego rodzaju znowu
bylyby nieodroznialne, a nikt nie przeczytalby, CO i DLACZEGO sie stalo.

**RETROAKTYWNIE OZNACZONE WYCOFANIE Z 29/07 - i to bylo pilne.** Wpis mowil wprost, ze
`updated_at::date` to proteza dzialajaca "tylko dopoki pamietamy date operacji". DDL 040
utrwala ten zbior, POKI JESZCZE WIEMY. Za miesiac tej wiedzy juz by nie bylo i 21 materialow
zostaloby na zawsze nieodroznialnych od pieciu starych odrzucen.

**Czego NIE zrobiono, powiedziane wprost:** istniejace skrypty hurtowe (`outreach_cleanup`,
`prospect_import`) NIE zostaly przerobione na `operacje.zarejestruj`. Mechanizm jest gotowy
i przetestowany, ale kazdy skrypt trzeba podpiac osobno - to nastepny krok, nie ten.

Test: `cm-agent/tests/test_operacje.py` (18 asercji). Zestaw 22/22.

Ponizej oryginalny opis, dla historii.


**Zapisany 29/07/2026** (zgloszenie Managera, szosta odslona AP-311).

Wycofalem 29/07 dwadziescia jeden materialow X (99 wierszy) ustawiajac im `status='rejected'`.
Content Manager zapytal, **po czym ma je rozpoznac** - i mial racje, bo bez tego zgaduje.

**Problem nie jest w tym, ze danych brakuje. Jest w tym, ze sa nieodroznialne.** Ja wiem, co
wycofalem, bo sam to robilem. CM patrzy na te sama baze i widzi materialy w statusie `rejected`
- **te same, co odrzucone przy przegladzie kart miesiac temu**. Sprawdzone: zapytanie
"platforma X, status rejected, wiecej niz jeden wiersz" zwraca **26** materialow, z czego
dzisiejszych jest **21**. Piec to stare odrzucenia bez zwiazku z operacja.

Doraznie ratuje to `updated_at::date`, ale to jest proteza: dziala tylko dopoki nikt inny nie
dotknie tych wierszy tego samego dnia i tylko dopoki pamietamy date operacji.

**Czym grozi:** kazda operacja hurtowa (sprzatanie gotowcow 27/07, import listy 27/07,
wycofanie serii 29/07) jest dla pozostalych agentow niewidzialna jako operacja. Widza SKUTEK,
nie widza PRZYCZYNY ani ZAKRESU. Przy trzech agentach czytajacych te sama baze to jest
mnozenie sie nieporozumien, a nie brak wygody.

**Docelowo (rozszerzenie sladu audytowego z DDL 035):** slad ma obejmowac nie tylko KTO ustawil
slot, ale takze **kto zmienil status i w ramach jakiej operacji**. Ksztalt do rozstrzygniecia:
kolumna `status_source` symetryczna do `slot_source`, albo etykieta operacji (np.
`op='wycofanie-serii-29072026'`) pozwalajaca wyciac dokladny zbior jednym warunkiem.

Manager 29/07: *"Ty wiesz, co wycofales, bo sam to robiles. CM patrzy na te sama baze i nie
widzi roznicy miedzy materialem wycofanym a odrzuconym przy przegladzie miesiac temu."*

## D-005 [ZAMKNIETE 02/08/2026]: Karty decyzji wygaszone PRZED 27/07 zostaja klikalne

**NAPRAWIONE INACZEJ, NIZ ZAKLADAL TEN WPIS.** Wpis mowil: "poprawka dziala od `f4e88e1` w PRZOD,
karty wygaszone wczesniej zostaja martwe i klikalne" - i uznawal to za nienaprawialne, bo nie
mamy juz ich identyfikatorow.

To bylo prawdziwe tylko przy zalozeniu, ze naprawa musi dzialac WSTECZ. Nie musi.
**Przy pierwszym tapnieciu martwej karty mamy jej numer** - w `tg_message_id` wiersza decyzji
albo w samym callbacku. Galaz "juz rozstrzygnieta" w `decisions.handle` dotad TYLKO odpowiadala
tekstem; teraz **zdejmuje klawiature z tapnietej karty**.

Efekt: kazda martwa karta czysci sie sama przy pierwszym kontakcie z czlowiekiem. Zamiast
naprawy wstecznej - **samoleczenie**. Komunikat mowi wprost, ze guziki zostaly zdjete.

**Ograniczenie, powiedziane wprost:** karty sprzed zapisywania `tg_message_id` maja je puste.
Jesli n8n nie przekaze `message_id` w tresci callbacku, taka karta zostanie klikalna - komunikat
mowi wtedy "o ile znam jej numer". Dodanie `message_id` do payloadu n8n domknelo by to w stu
procentach i jest tanie, ale wymaga PUT do workflow HITL, wiec nie w tym oknie.

Ponizej oryginalny opis, dla historii.


**Zapisany 27/07/2026.**

Do commita `f4e88e1` klawiature z karty zdejmowal wylacznie `decisions.handle` po odpowiedzi
guzikiem. Bramki wygaszone skryptem albo recznym SQL zostawialy w Telegramie karte z zywo
wygladajacymi guzikami. Tomasz tapnal taka 27/07 i dostal "Decyzja #161 juz rozstrzygnieta",
majac w czacie siedem prawie identycznych kart o tym samym prospekcie.

Poprawka dziala od `f4e88e1` w PRZOD. **Karty wygaszone wczesniej (m.in. #152-156, #161) zostaja
martwe i klikalne** - nie mamy juz ich identyfikatorow w reku w momencie wygaszania.

**Czym grozi:** kolejne tapniecie w stara karte i komunikat "juz rozstrzygnieta". Nieszkodliwe,
mylace. Znikna z pola widzenia same, gdy czat sie przewinie.

---

## D-009 [ZAMKNIETE 02/08/2026]: Gotowiec mailowy w kanale `Other`, tekst z teczki w `Email`

**NAPRAWIONE, commit ea13447 + migracja przy zatrzymanym cm-agencie.** Slownik `email -> Email`
i dziewiec istniejacych wierszy w JEDNYM oknie wdrozeniowym. Okno usuniete przez zatrzymanie
kontenera (baza stoi w innym kontenerze niz pisarz), nie przez wybor mniejszego zla.
Wyszlo przy okazji: `channel` outreachu nie byl walidowany - dolozona bramka. Ponizej oryginal.


**Zapisany 31/07/2026** (stan zastany, zauwazony przy budowie teczki prospekta).

`sales.py:802` mapuje kanaly gotowcow tak: `_ENG_CHANNEL = {"email": "Other", "linkedin_dm":
"LinkedIn", "x_dm": "X"}`. Wartosc `'Email'` istnieje w ograniczeniu `engagement_log` od DDL 001,
ale tor gotowcow z niej nie korzysta. `teczka.zapisz` zapisuje maile poprawnie jako `'Email'`,
wiec od 31/07 ten sam kanal ma w ksiedze **dwie rozne etykiety** zaleznie od tego, kto pisal.

**Dlaczego nie poprawilem od reki:** `_ENG_CHANNEL` jest KLUCZEM w `_open_outreach_rows`, ktore
domyka poprzednie gotowce w tym samym kanale. Podmiana wartosci rozjechalaby dopasowanie
z wierszami juz lezacymi w bazie i zywe gotowce przestalyby sie unieważniac - to ta sama wada,
ktora 24/07 zrobila StandART siedem wierszy i piec bramek. Poprawka wymaga migracji istniejacych
wierszy razem ze zmiana slownika, w jednym kroku.

**Czym grozi:** nie rozbija niczego dzisiaj (teczka laczy wpisy po `pipeline_id`, nie po kanale),
ale **kazde liczenie wysylki per kanal bedzie klamac** - maile rozpadna sie na dwie kupki.

---

## D-010 [ZAMKNIETE 02/08/2026]: `contacts` ma TRZY kolumny na stan tej samej osoby

**ZAMKNIETE KOMENTARZEM W SCHEMACIE (DDL 039), swiadomie BEZ usuwania kolumny.**

Odczyt 02/08 rozstrzygnal, ktora z trzech jest problemem: **`pipeline_stage` nie czyta NIKT** -
grep po calym `cm-agent/app/` daje zero trafien poza schematem. `relationship_stage` (stadium
relacji) i `status` (temperatura) to dwie ROZNE osie i ich wspolistnienie da sie obronic.

**Dlaczego komentarz, a nie DROP:** usuniecie jest nieodwracalne i zabiera 45 wartosci
o nieznanym dzis pochodzeniu. Kolumna nie szkodzi, dopoki nikt jej nie czyta - zaszkodzi
w chwili, gdy KTOS ja przeczyta, biorac za zrodlo prawdy o etapie. Nazwa `pipeline_stage`
brzmi dokladnie jak etap w lejku i wlasnie to czyni ja grozna: to zaproszenie do pomylki,
nie zwykly balast.

**Lekarstwo podane tam, gdzie nastepny agent NAPRAWDE zajrzy** - w `COMMENT ON COLUMN`,
nie w pliku dokumentacji, ktorego moze nie otworzyc. Wszystkie trzy kolumny dostaly opis
mowiacy, ktora jest zrodlem prawdy i po co sa pozostale. To jest AP-312 rozwiazany na poziomie
schematu.

Ponizej oryginalny opis, dla historii.


**Zapisany 01/08/2026** (polecenie Tomasza: nie ruszac, zgłosic po moscie).

- `relationship_stage` varchar(20) NOT NULL, CHECK na 7 wartosci - zywa, wypelniona zawsze
  (cold 121, commented 69, dm 4).
- `status` varchar(50) NOT NULL, CHECK na 7 INNYCH wartosci (Cold/Warm/Hot/Customer/...).
- `pipeline_stage` **text, BEZ ograniczenia, wypelniony w 45 wierszach** - pozostalosc,
  ktorej nikt nie pilnuje i nic nie waliduje.

**Czym grozi:** dwa pierwsze da sie obronic (relacja kontra temperatura), trzeci jest czystym
dlugiem - tekst bez slownika, ktory przy pierwszym odczycie przez agenta zostanie wzięty za
zrodlo prawdy o etapie. To AP-312 czekajace na wywolanie.

---

## D-011 [ZAMKNIETE 02/08/2026 - NIE BYLO WADY]: "61 sierot" w `engagement_log`

**Zapisany 01/08/2026 przeze mnie. Zamkniety 02/08 po odczycie, ktory obalil wlasna przeslanke.
Zero zmian w kodzie i w bazie - i to jest wlasciwy wynik tego zadania.**

### Co pokazal odczyt

1. **Wszystkie 61 wierszy ma PUSTE `author_display`.** Nie ma czego dopinac. Zero pasuje
   do `contacts`, zero do `sales_pipeline` - nie dlatego, ze nazwy sie roznia, tylko dlatego,
   ze nazwy NIE MA. Normalizacja ogonkow (AP-313), ktora zapisalem jako narzedzie naprawy,
   nie ma tu czego normalizowac.
2. **To nie sa osierocone interakcje, tylko zapisy WLASNEJ aktywnosci.** Probka tresci:
   `"test draft"`, `"Raw insights queue for X Agent v1.0"`, `"Opis: Obrazek przedstawia posty
   na LinkedIn"`, `"My AI agent said 'published.'"`. Opublikowane posty, analizy zrzutow ekranu,
   wewnetrzne znaczniki kolejki. Wszystkie 61 maja `status='logged'`, czyli "zapisuje fakt".
   **One nie maja drugiej strony - i nie powinny miec.**
3. **Zaden licznik ich nie widzi.** Oba zapytania zliczajace (`crm.py:137` i `crm.py:178,181`)
   sa zawezone `WHERE contact_id=...`, wiec wiersz bez kontaktu jest z nich wykluczony.
   W `n8n` tej tabeli nie czyta nic. Nie istnieje zadne globalne `COUNT(*)` bez zawezenia.

### Dlaczego to trafilo na liste dlugu

Zdanie "zajmuja miejsce w licznikach (348 wpisow)" bylo **moje** i bylo nieprawdziwe: 348 to
liczba z MOJEJ sondy, nie z zadnego widoku systemu. Zapisalem brak powiazania jako wade,
nie sprawdzajac, czy cokolwiek tego powiazania POTRZEBUJE.

**To jest AP-311 zastosowane na opak.** Anty-wzorzec mowi: brak danych nie jest faktem, dopoki
nie sprawdzisz, ze system moglby je pokazac. Symetrycznie: **obecnosc danych nie jest problemem,
dopoki nie sprawdzisz, ze cokolwiek je czyta.**

### Co z tego zostaje naprawde (drobne, nie dlug operacyjny)

Wiersze `x_post` i `linkedin_post` w `engagement_log` dubluja to, co ma wlasna tabele
`published_posts`. To zapach modelowania, nie usterka: nic sie przez to nie psuje, zaden odczyt
nie klamie. Odnotowane, zeby nie odkrywac tego trzeci raz.

---

## D-012: Nic nie mapuje marki na korzen katalogu

**Zapisany 01/08/2026** (wyszlo przy budowie mostu katalogi-baza).

`sales_pipeline.katalog` trzyma sciezke WZGLEDNA (`Klienci\Chwalinski`) i to jest poprawne -
korzen jest cecha maszyny, nie prospekta. Ale **korzen nie jest nigdzie zapisany**. Ustalenie
Tomasza brzmi "korzen wynika z brand_id", tyle ze:

- wszystkie 134 wiersze maja dzis `brand_id='AGS'`,
- katalogi tych czterech leza pod `C:\Claude-CoWork\TyNieMusisz`,
- czyli mapowanie marka -> korzen dalo by dzis ZLY wynik, gdyby ktos je napisal doslownie.

**Czym grozi:** dopoki sciezke sklada czlowiek, nic sie nie dzieje. Pierwsze narzedzie, ktore
zechce OTWORZYC plik z teczki, bedzie musialo ten korzen skads wziac - i zgadnie.
**Docelowo:** `brands.katalog_korzen` albo wpis w `brand_config`, wypelniony razem
z przejsciem kodu na wielomarkowosc (patrz D-013).

---

## D-013: Kod jest jednomarkowy - wielomarkowosc czeka na pierwsza sprzedaz

**Zapisany 01/08/2026 (decyzja Tomasza, wariant drugi).**

**107 miejsc w `cm-agent/app/` filtruje `brand_id='AGS'`, w tym 13 w samym `sales.py`.**
Przepiecie 24 polskich wierszy na marke TNM wypchneloby je z widoku lejka, ze straznika
terminow i z generowania gotowcow - po cichu, bo zapytanie bez wynikow nie jest bledem.

**Decyzja:** dane NIE sa przepinane. Powstaje ETYKIETA `sales_pipeline.marka_docelowa`
(DDL 038), ktorej **zaden kod nie czyta**, zeby przyszle przepiecie bylo jednym UPDATE-em,
a nie ponownym rozstrzyganiem 24 przypadkow z pamieci.

**Warunek wejscia buildu wielomarkowego:** PO pierwszej zamknietej sprzedazy, nie wczesniej.
Uzasadnienie Tomasza: *"Wielomarkowosc nie przybliza do pierwszej faktury, a przepiecie danych
bez gotowego kodu ja oddala"*.

---

## D-014 [ZAMKNIETE 02/08/2026]: `action_type` mowi co innego niz `channel` dla tego samego maila

**NAPRAWIONE. Przyczyna byla WSPOLNA z D-009:** para (action_type, channel) miala DWA zrodla -
kanal ze slownika, typ literalem w INSERT - wiec miala jak sie rozjechac i rozjechala sie
dwukrotnie. Od 02/08 para siedzi w jednym slowniku `_ENG_KANALY`, w tym samym ksztalcie co
`teczka._KANALY`. Migracja: `docs/ops/SQL_d014_action_type_02082026.sql`.

**Odczyt pokazal, ze to ETYKIETA, nie klucz** (inaczej niz przy D-009): jedyne zapytanie
filtrujace po `action_type` (crm.py:180) jest zawezone do `contact_id`, a wszystkie dziewiec
gotowcow ma je puste; w calej bazie zero wierszy pasuje do `action_type ILIKE %dm%`. Dlatego
zatrzymywanie kontenera NIE bylo tu potrzebne - powiedziane wprost, zamiast powtarzania
ciezszej procedury dla powagi. Ponizej oryginal.


**Zapisany 02/08/2026** (znaleziony przez adwersarzy przy naprawie D-009).

`sales.py` wstawia gotowca z literalem `action_type='other'` **dla kazdego kanalu**, podczas gdy
`teczka.py` mapuje maila na `action_type='email'`. Obie kolumny lezą w tej samej tabeli i sa
pokazywane na tej samej osi czasu w teczce prospekta.

**Dlaczego NIE naprawilem tego razem z D-009:** to druga kolumna, wiec druga migracja. Wciagniecie
jej do tego samego okna podwoiloby zakres zmiany, ktora dotyka klucza dopasowania gotowcow -
a wlasnie ten klucz jest miejscem, gdzie blad kosztuje najwiecej. Regula "slownik i migracja
w jednym kroku" nie znaczy "wszystkie slowniki naraz".

**Czym grozi:** dzis niczym operacyjnie - `action_type` nie filtruje zadnego zapytania w torze
outreachu. Ale kazdy przyszly raport typu "ile maili wyszlo" da inny wynik zaleznie od tego,
czy policzy po `channel` czy po `action_type`.

**Docelowo:** `action_type` z tego samego slownika co `channel` + migracja istniejacych wierszy,
w jednym kroku. Rozroznik ten sam, trzypasowy, co przy D-009.

## D-016 [ZAMKNIETE 11/08/2026]: potwierdzenie obiecywalo "za chwile", gdy material nie mial jeszcze slotu

**Zapisany 10/08/2026, zamkniety 11/08/2026.**

> ### WYKONANE 11/08 - i diagnoza z 10/08 wymagala SPROSTOWANIA
>
> Wpis z 10/08 mowil, ze wezel odpowiada "stalym napisem". **Odczyt zywej definicji to obalil.**
> `Telegram Cm Confirm` (`parameters.jsonBody`) juz czytal slot i byl warunkowy:
>
> ```js
> 'Zatwierdzono. Publikacja ' + ($json.scheduled_for
>      ? ('w slocie: ' + <data pl-PL, Europe/Warsaw>)
>      : 'za chwile') + '. Potwierdzenie przyjdzie na kanale logowym.'
> ```
>
> Przy materiale ZE SLOTEM zdanie bylo prawdziwe i uzyteczne. Falszywa byla **wylacznie galaz
> zapasowa**. Tomasz trafil w nia dlatego, ze material mial `scheduled_for = NULL` - wyzerowany
> tego samego dnia rano przez `SQL_wycofanie_344_10082026.sql`. Dlug byl wiec WEZSZY, niz go
> opisalem: nie "napis klamie zawsze", tylko "klamie dokladnie wtedy, gdy slot dopiero powstanie".
>
> **Zmiana:** `: 'za chwile')` → `: 'w slocie, ktory CM zaraz przydzieli')`. Jedno slowo, nie cale
> zdanie. Swiadomie NIE obiecujemy meldunku o godzinie, choc w tej galezi zwykle przychodzi: gdy
> `next_slot` nie znajdzie wolnego gniazda, `changed` zostaje False i meldunek nie idzie. Obietnica
> meldunku bylaby tym samym bledem przesunietym o jedno zdanie.
>
> **Dowod:** `nodes` **i** `activeVersion` pokazuja stary napis **0**, nowy **1**. Sprawdzenie
> `activeVersion` jest tu mocniejsze niz odpowiedz 200 i flaga `active` - to ta migawka decyduje,
> na czym bot naprawde chodzi ([[project_n8n_reactivate_after_put]]).
>
> Patch: `n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs`
> (`sprawdz` / `patch` / `cofnij`). Kopia sprzed zmiany lezy obok jako `bk_hitl_d016_*.json`.
>
> **Dwie rzeczy ustalone przy okazji, obie warte wiecej niz sama poprawka:**
> 1. **Patche n8n uruchamia sie Z MASZYNY TOMASZA, nie z serwera.** Serwer nie ma ani `node`,
>    ani pliku `.env`; n8n wystawia API po HTTPS. Instrukcja w naglowku patcha z 03/08 wskazywala
>    sciezke windowsowa i byla poprawna - probowalem odpalic to na serwerze i dopiero
>    `command not found` mi to uswiadomil.
> 2. **Zywy workflow ma 254 wezly, eksport w repo 143** - patrz sekcja nizej.

### Zapis pierwotny (10/08) - kontekst zgloszenia

Po tapnieciu guzika zatwierdzenia bot odpowiada:

> ✅ Zatwierdzono. **Publikacja za chwile.** Potwierdzenie przyjdzie na kanale logowym.

Sekunde pozniej, w tym samym czacie:

> 🗓 CM przydzielil slot: **Tue 11/08 16:00**

"Za chwile" i "za dwadziescia dwie godziny" w jednym oddechu. **To jest AP-312 w wydaniu
czasowym**: etykieta obiecuje co innego, niz sie stanie - dokladnie ta sama klasa, ktora
przerabialismy tego dnia przy D-006, D-008 i D-015.

**Gdzie siedzi:** w wezle n8n `AGS HITL Handler v1.0`, nie w cm-agencie. Guzik zatwierdzenia
**omija kontener** (patrz `docs/komponenty/n8n-transport.md` - trzeci pisarz do `content_items`),
wiec tekst potwierdzenia jest stalym napisem w definicji workflow. cm-agent nie ma jak go
poprawic i nie da sie tego naprawic rebuildem.

**Dlaczego to nie jest kosmetyka:** przy kadencji czterech publikacji dziennie czlowiek dostaje
te pare wiadomosci kilka razy dziennie. Zdanie, ktore systematycznie klamie, uczy ignorowac
CALY kanal logowy - a to jest ten sam kanal, ktorym ida alarmy zwisu i meldunki bezpiecznika
gatunku. Koszt nie jest w tej jednej wiadomosci, tylko w zaufaniu do reszty.

**PATCH GOTOWY 11/08, CZEKA NA URUCHOMIENIE:**
`n8n-workflows/patches/d016-potwierdzenie-bez-obietnicy-11082026.cjs` (tryby `sprawdz`/`patch`/`cofnij`).

Nowe zdanie: **"Materiał czeka na swój slot - publikacja nie idzie od razu."**
Odrzucony wariant "CM przydzieli slot i zamelduje": **to bylby ten sam blad przesuniety o jedno
zdanie.** CM melduje slot TYLKO wtedy, gdy go wlasnie przydzielil - `slots.assign_if_needed`
zwraca `changed=False`, gdy material slot juz mial, i wtedy zaden meldunek nie idzie. Obietnica
meldunku bylaby falszywa w dokladnie tych przypadkach, w ktorych czlowiek na nia czeka.

**Dwie roznice wobec patcha D-008, obie wymuszone przez to, CO jest gaszone:**

1. Tam gaszony byl Scheduler (cron). Tu gaszony jest HITL Handler, czyli **jedyny interfejs
   Tomasza** - przez okno patcha guziki w bocie nie odpowiadaja. Dlatego skrypt gasi dopiero
   PO przygotowaniu definicji w pamieci i **sam wraca do gry** na koncu, zamiast zostawiac
   workflow wylaczony.
2. Skrypt **NIE szuka wezla po nazwie**, tylko przeszukuje cala definicje rekurencyjnie po tresci.
   Powod nizej.

### Ustalenie uboczne: eksport n8n w repo jest o DWA MIESIACE do tylu

`n8n-workflows/x-agent/ags-hitl-handler-v1.json` ma `updatedAt` **2026-06-11**, 143 wezly
i **nie zawiera wezla `Cm Resolve Gate` w ogole**. Napisu "Publikacja za chwile" nie ma nigdzie
w repozytorium - zyje wylacznie w definicji na serwerze.

**Konsekwencja dla kogos, kto czyta repo:** pliki w `n8n-workflows/` opisuja warstwe transportowa,
ktorej juz nie ma. Nie da sie z nich wywnioskowac, jak system dzis odpowiada. Kazdy patch musi
czytac definicje ZYWA (tak robia wszystkie skrypty w `patches/`), a nie eksport.

**Do nadrobienia osobno:** re-eksport zywych workflow do repo. Bez tego kolejny czytajacy powtorzy
ta sama pomylke - ja zrobilem ja dwa razy w ciagu jednej sesji, najpierw zakladajac, ze napis jest
w n8n (trafnie), potem ze jednak w Pythonie (blednie, bo `grep` po "za chwil" trafil w cztery INNE
zdania w `cm-agent/app/`). Odczyt precyzyjny rozstrzygnal; odczyt zgrubny wprowadzil w blad.

## D-017: Token bota Telegrama wpisany NA SZTYWNO w 44 wezlach HITL Handlera

### Przygotowane 19/08/2026 (WYKONANIE CZEKA NA OKNO - dlug NIE jest zamkniety)

Skrypt `n8n-workflows/patches/d017-token-bez-hardkodu-19082026.cjs` (piec trybow: `sprawdz`,
`sucho`, `sucho-z-pliku`, `zapisz`, `cofnij`) plus procedura `docs/ops/OKNO_D017_przygotowane.md`
z komendami w skladni PowerShella 5.1.

**Liczba 44 potwierdzona dwoma niezaleznymi przeliczeniami** (podwykonawca i koordynator, osobnymi
skryptami) na eksporcie z 11/08: 44 wezly `httpRequest` z twardym tokenem, JEDEN literal,
36 adresow wyrazeniowych i 8 zwyklych. Dlug sie NIE zestarzal.

**Trzy pulapki, ktorych NIE BYLO w tym wpisie, a kazda po cichu rozwalilaby naiwny patch:**
1. **osiem z 44 adresow to zwykle napisy, nie wyrazenia** - bez dopisania prefiksu `=` n8n
   wstawi klamry DOSLOWNIE do URL, Telegram odda 404, a bot **zamilknie bez zadnego bledu**;
2. **dwa adresy maja odmiane `/file/bot<TOKEN>/`** (pobieranie plikow) - podmiana po
   `https://api.telegram.org/bot` ominelaby je;
3. **galaz rownolegla dla wezla z tokenem dalaby blad LOSOWY**, bo przy `executionOrder: v1`
   kolejnosc galezi zalezy od polozenia wezlow na plotnie. Stad lancuch
   `Telegram Trigger -> TG Token -> Detect Update Type`, a nie galaz.

**Poswiadczenie n8n ODPADA, wbrew pierwotnemu zapisowi tego dlugu.** Poswiadczenia wstrzykuja sie
w NAGLOWKI, a Telegram trzyma token w SCIEZCE URL. Zostaje `app_secrets`, klucz
`telegram_bot_token` - wiersz JUZ tam jest i JUZ jest czytany (Scheduler, `PostgreSQL Lookup
Session`). Zadnego czwartego mechanizmu.

**Wpis nie odnotowal, ze robota jest w polowie zrobiona:** szesc wezlow tego samego workflow
czyta token z wyrazenia od dawna. To zmienia charakter zadania z "wymysl mechanizm" na
"dokoncz zaczete", a bramka pilnuje, zeby te szesc przeszlo NIETKNIETYCH.

**Bramka zlapala blad swojego autora.** Pierwsza wersja wzorca URL wykluczala klamry i po
przemianie widziala zero podmienionych wezlow. Kontrola wyniku zatrzymala przebieg na sucho,
offline, zanim cokolwiek dotknelo produkcji.

**Sprawdzone przez koordynatora, nie przyjete z raportu:** przebieg offline daje 8 bramek
i 10 kontroli wyniku na zielono (exit 0, zero sieci); przy wsadzie z 43 wezlami zamiast 44
bramka **pada ZAMKNIETA** (`STOP liczba wezlow do podmiany: 43, oczekiwana 44`,
`KONIEC: bramka zamknieta, przemiany nawet nie probuje`, exit 1).

**Rekomendacja co do rotacji tokenu przy tej okazji: NIE w tym oknie.** Argument "skoro i tak
trzeba dotknac 44 wezlow" po tej zmianie przestaje obowiazywac - rotacja staje sie jednym
`UPDATE` w `app_secrets`. Mieszanie dwoch zmian w jednym oknie na JEDYNYM interfejsie Tomasza
kosztuje mozliwosc odroznienia, ktora z nich zawiodla, gdy bot zamilknie. Decyzja Managera.

**ROZSTRZYGNIETE PRZEZ MANAGERA 19/08: rekomendacja PRZYJETA, tokenu w oknie NIE rotujemy.**
Rotacja wchodzi jako **osobny krok, po 24 godzinach stabilnosci**, rowniez z weryfikacja
prawdziwa wiadomoscia. Jedna zmiana, jeden dowod, jedna droga cofniecia.

**Zapisany 11/08/2026** (skan przed pierwszym re-eksportem workflow do repo).

Kanon tego projektu, powtorzony w trzech miejscach (`SYSTEM_DATAFLOW`, `DEPLOY_CHECKLIST`,
`komponenty/n8n-transport`), brzmi: **sekrety wylacznie w `app_secrets`, zero literalow
w definicjach n8n**. Odczyt zywej definicji pokazal, ze dla HITL Handlera to jest ZASADA,
a nie stan faktyczny:

| workflow | literaly sekretow w `parameters` |
|---|---|
| `AGS Scheduler v1` | **0** (de-hardkod 02/07, zrobiony i utrzymany) |
| `AGS Lacznik Chat Tools` | **0** |
| **`AGS HITL Handler v1.0`** | **44** - token w `parameters.url`, adres `api.telegram.org/bot<TOKEN>/...` |

**Poswiadczenia n8n nie sa problemem** - `node.credentials` to referencje `{id, name}`.
Problem jest w PARAMETRZE: adres HTTP z tokenem w sciezce.

### Czym to grozi

1. **Kazdy eksport workflow do repo publikuje dzialajacy token.** Dokumentacja z 10/08 podawala
   na to gotowa komende (`curl > plik`) razem ze zdaniem, ze plik jest bezpieczny do commitu.
   Gdyby ktos ja wykonal, token trafilby na publiczny GitHub. **Sprawdzone: token NIE JEST
   w historii gita** - ani w zacommitowanych eksportach, ani w zadnym wczesniejszym commicie.
2. **Rotacja tokenu wymaga edycji 44 wezlow**, a nie jednego wiersza w `app_secrets`.
   To zamienia piecio-minutowa czynnosc w okno serwisowe na jedynym interfejsie Tomasza.
3. Kopie robocze patchow (`bk_*.json`) sa surowymi zrzutami, wiec **zawieraja token bez maski**.
   Regula `.gitignore` na `n8n-workflows/**/bk_*.json` robi od 11/08 takze robote bezpieczenstwa,
   nie tylko porzadkowa - i jest tam o tym komentarz.

### Co zrobiono 11/08 (obejscie, NIE naprawa)

`n8n-workflows/eksport-do-repo.cjs`: eksport maskuje znane wzorce sekretow i **odmawia zapisu**,
gdy po maskowaniu zostanie cokolwiek podejrzanego (bramka pada zamknieta, AP-314). Trzy zywe
workflow sa dzieki temu w repo aktualne i czyste: HITL 254 wezly z 44 placeholderami
`<TELEGRAM_BOT_TOKEN>`, Scheduler 10, Lacznik 11.

**To chroni REPOZYTORIUM, nie produkcje.** Token nadal siedzi w definicji.

### Docelowo

Token wychodzi z `parameters.url` do poswiadczenia n8n albo do odczytu z `app_secrets`
w locie - dokladnie tak, jak zrobiono w Schedulerze 02/07. 44 wezly, wiec skrypt patchujacy
na wzor `patches/*.cjs`, z bramka na liczbe podmian i kopia sprzed zmiany.
**Osobne okno**: HITL Handler to jedyny interfejs Tomasza, a po PUT trzeba deactivate+activate.

**Decyzja do podjecia przy okazji:** czy rotowac token. Nie wyciekl poza serwer i maszyne
Tomasza, wiec rotacja nie jest wymuszona - ale skoro i tak trzeba dotknac 44 wezlow,
zrobienie tego raz z nowym tokenem kosztuje tyle samo, co ze starym.

## D-018 [ZAMKNIETE 11/08/2026]: rejestr decyzji tylko rosl - karty nie wygasaly, gdy material szedl dalej

**Znaleziony i zamkniety 11/08/2026**, godzine po publikacji materialu "Granica miedzy dwoma agentami".

Lista OTWARTYCH DECYZJI w `stan_gry` pokazywala od dwoch tygodni czternascie kart
"Material czeka na Twoja decyzje ponad 24h". Odczyt zestawiajacy je z aktualnym stanem
materialu (`context->>'content_item_id'`, klucz, ktorego straznik uzywa do throttlingu):

```
kart 'pending': 15  |  MARTWE (material poszedl dalej): 15  |  ZYWE: 0
```

**Piętnascie na pietnascie martwych. Jedenascie materialow odrzuconych, CZTERY OPUBLIKOWANE** -
w tym karta `#173` dla materialu opublikowanego **godzine wczesniej**, wiszaca 14 dni.

### Przyczyna

`worker._stale_approval_watch` zakladal karty przy materiale czekajacym >24 h i **nic ich nigdy
nie zamykalo**. Material szedl dalej swoja sciezka (approve, reject, publikacja), wpis w rejestrze
stal nietkniety. Nie bylo zadnego konsumenta zamykajacego - tak samo jak przy `next_followup_at`
w diagnozie lejka 26/07.

To **AP-311 od strony ZAPISU**: wpis czytany jako fakt o swiecie, gdy jest tylko faktem
o rejestrze. Rejestr, ktory tylko rosnie, po miesiacu przestaje byc lista zadan i staje sie
szumem - a wtedy przestaje sie go czytac razem z tym, co w nim wazne. Przy czternastu falszywych
pozycjach `#179` (prawdziwe pytanie o 21 materialow X) jest nie do zauwazenia.

### Naprawa

Zamykanie **PRZED** otwieraniem, w tej samej funkcji, ktora karty zaklada. Karta `pending`,
ktorej material nie jest juz `needs_approval`, dostaje `status='expired'`.

- **`expired`, nie `answered`** - Tomasz nie odpowiedzial. Nie `auto` - system nie zdecydowal.
  Pytanie przestalo byc pytaniem. Wartosc jest w slowniku od DDL 024, tylko nikt jej nie uzywal.
- **Bez powiadomienia.** To sprzatanie po sobie, a nie zdarzenie warte przerywania komus dnia;
  slad idzie do logu kontenera.
- **Bramka na ksztalt uuid** przy rzutowaniu `context->>'content_item_id'` - jeden zly wpis
  bez niej wywraca CALEGO straznika, czyli takze eskalacje niezatwierdzonych materialow.

Piętnascie istniejacych kart **zamknie sie samo przy pierwszym przebiegu petli po rebuildzie** -
nie ma osobnego SQL-a do wykonania.

Zachowanie: `cm-agent/tests/test_wygasanie_decyzji.py`.

### Lekcja z pisania testu do tej poprawki

Asercja o kolejnosci przeszla na ZEPSUTYM kodzie (blok wygaszania wewnatrz petli daje te sama
sekwencje zdarzen). Druga wersja, liczaca `for ` miedzy blokiem a petla, padla na ZDROWYM kodzie,
bo w bloku stoi wyrazenie listowe `[r["id"] for r in wygasle]`. Trzecia mierzy WCIECIE i dopiero
ona mierzy to, o co chodzilo: poziom zagniezdzenia.

**Dwie zle asercje pod rzad przy jednej poprawce.** Obie wygladaly rozsadnie i obie sprawdzaly
cos podobnego do tego, co mialy sprawdzac. To jest dokladnie ta sama klasa co AP-315 na poziomie
testu: kontrola pyta o cos innego, niz mysli jej autor - i tylko celowe przywrocenie wady
to pokazuje.

## D-019 [ZAMKNIETE 19/08/2026]: Petla nauki dopisuje nowe wpisy bez jezyka i rodzaju

**Zamkniete 19/08/2026** wedlug decyzji Managera Z-3 (11/08) i rozstrzygniecia zakresu z 19/08
(`docs/cm/ODPOWIEDZ_Managera_19082026_blok_B.md`).

**Odczyt kodu obalil zdanie z tego wpisu, ze producent jest jeden.** Pisarzy bylo DWOCH:
`matreview.add_style_rule` (regula dyktowana przez Tomasza) i `matreview._distill_style_rules`
(destylacja modelu z korekty VOICE_EDIT). Manager rozstrzygnal: bramka obejmuje OBIE drogi
w JEDNYM wspolnym miejscu, bo roznica miedzy preferencja a poleceniem lezy w SFORMULOWANIU,
nie w autorstwie. Bramka stoi w `matreview._state_set` na kluczu `style_learned`, wiec nie ominie
jej takze trzeci pisarz, gdyby powstal (AP-309); flaga `ZAPIS_STYLU_WYLACZONY` jest W KODZIE,
nie w ustawieniu (AP-314). Odczyt `generate._learned_style` NIETKNIETY.

Zamiast cichej odmowy jest droga zastepcza: regula podyktowana przez Tomasza laduje jako notatka
w `brand_config.style_rules_parked` (jezyk, rodzaj, pochodzenie plus pole `ustalenie`, ktore
rozroznia ZAOBSERWOWANE od WYWNIOSKOWANEGO per wlasnosc - AP-317). `rodzaj` zapisuje sie jako
jawnie nieustalony, bo preferencji od polecenia nie odroznia dzis nic mierzalnego, a zgadniety
rodzaj czytaloby sie przy odblokowaniu petli jako fakt. Bot mowi Tomaszowi wprost, ze regula
do stylu nie weszla, i proponuje zastosowanie jej do jednego konkretnego tekstu. Zero DDL,
zadnego okna migracyjnego.

Domkniete przez koordynatora w tym samym commicie: `conversation._run_tool` skladal
`"Regula stylu zapisana na stale"`, czyli po wylaczeniu zapisu **falszywe potwierdzenie - gorsze
niz cicha odmowa**; opis `TOOL_STYLE_RULE` obiecywal modelowi zapis na stale. Oba poprawione.

**Warunek powrotu bez zmian:** wpis dostaje jezyk i RODZAJ PRZY ZAPISIE. Samo zdjecie flagi tego
warunku NIE spelnia.

Zachowanie: `cm-agent/tests/test_bramka_nauki_stylu.py` (63 kontrole; przy celowo przywroconej
wadzie pada piec, sprawdzone przez koordynatora). Opis: `docs/komponenty/glos-marki.md`.

**ZNALEZISKO POZA ZAKRESEM, ta sama klasa, prawdopodobnie ostrzejsze - CZEKA NA MANAGERA:**
istnieje DRUGI trwaly magazyn regul, `channels.config.rules`, pisany narzedziem
`subagent_remember_rule` z rozmowy i wstrzykiwany przez `generate._channel_rules` do KAZDEGO
wariantu kanalowego jako `OWNER RULES FOR THIS ACCOUNT (obey strictly, override defaults if
conflict)`. To jest wprost polecenie posluszenstwa z prawem nadpisania domyslnych zasad, bez
filtra jezykowego, bez rodzaju, bez pochodzenia, do 20 pozycji per kanal. Mechanizm, przed ktorym
Z-3 zamknal `style_learned`, w tym magazynie stoi otwarty. NIE TKNIETY - poza zakresem D-019.

---

## D-019 (tresc oryginalna z 11/08, zostawiona dla kontekstu)

**Zapisany 11/08/2026 (decyzja Managera Z-3, NIE wykonana - blok dla nastepnej sesji).**

**Polecenie: wylaczyc ZAPIS nowych wpisow do `brand_config.style_learned`. Odczyt istniejacych,
juz przefiltrowanych, ZOSTAJE.**

Uzasadnienie Managera, mocniejsze od pytania, ktore zadalem: filtr jezykowy z AP-315 zamyka
**droge**, ktora znamy, ale **klasa zostaje otwarta** - kazdy przyszly wpis nauczony moze byc
POLECENIEM, nie preferencja. Koszt powtorki to publiczny post pod nazwiskiem Tomasza; mielismy
dwa. **"Przy zerowym przychodzie nie potrzebujemy, zeby system uczyl sie szybciej. Potrzebujemy
zera incydentow."** Wylaczenie kosztuje dzis prawie nic.

**Warunek wlaczenia z powrotem:** wpis dostaje **jezyk i RODZAJ** (preferencja kontra polecenie)
**PRZY ZAPISIE**, a nie jest zgadywany przy odczycie.

Punkt zaczepienia: producent wpisow do `style_learned` (destylacja z korekt VOICE_EDIT);
konsument `generate._learned_style` zostaje bez zmian.

## D-020 [ZAMKNIETE 19/08/2026]: Blokada `publish_mode='webhook'` ma byc W KODZIE, nie w dokumencie

**Zapisany 11/08/2026 (decyzja Managera Z-4). Wykonany 19/08/2026.**
**Manager ODRZUCIL moja rekomendacje "zostawic jako warunek twardy w dokumencie".**

Powod jest w moim wlasnym raporcie z tego samego dnia: `DEPLOY_CHECKLIST` przez trzy tygodnie
po incydencie AP-307 nadal instruowal, zeby ustawic `publish_mode='webhook'`. Nikt go nie oznaczyl
jako nieaktualnego, bo wygladal swiezo. **Warunek zapisany w dokumencie jest zalozeniem,
nie zabezpieczeniem - to jest AP-314 co do litery** (i AP-316, ktory z tego powstal).

**Do zrobienia:** ustawienie `publish_mode='webhook'` ma **padac glosno w kodzie**, z komunikatem
wskazujacym AP-307 i wymogiem swiadomego zdjecia blokady. Kilkanascie linii plus test.

**Czego NIE ruszamy:** samej miny w callbacku publishera (oznacza `published` wszystkie wiersze
materialu). Na to okna nie wydajemy - decyzja Managera bez zmian.

### Co dokladnie blokuje kod (19/08/2026)

**Bramka: `config.sprawdz_tryb_publikacji(tryb, gdzie)`** w `cm-agent/app/config.py`, tuz pod
stalymi trybow. Jedna funkcja, jedna decyzja; wolajace pliki tylko ja pytaja. Przy `webhook`
rzuca `config.TrybPublikacjiZabroniony` z komunikatem, ktory **nazywa AP-307 i cztery skutki
z 20/07** (4-5 postow X w godzine, wiersze wyslane bez mediow, polski post na anglojezycznym
profilu, baza oznaczajaca `published` wszystkie wiersze materialu). Nigdy nie poprawia wartosci
po cichu - cicha korekta wygladalaby jak sukces (AP-306).

**Dwa punkty wejscia, oba w drodze do zapisu, nie po nim:**

1. `conversation._target_update` - **jedyna droga, ktora czlowiek SWIADOMIE ustawia tryb**:
   fraza `ustaw publish_mode dla <marka> <cel> na ...` (regex przed LLM) oraz narzedzie
   `target_update` wolane przez model. Odmowa wraca jako tekst z `⛔`, zapisu nie ma.
2. `conversation._target_create` - bo `copy_from_channel` potrafi wciagnac `webhook`
   z configu innego celu, **bez niczyjej decyzji**.

**Osobne, powazniejsze znalezisko przy okazji: `webhook` byl WARTOSCIA DOMYSLNA w dwoch
miejscach zakladajacych cele.** `conversation._target_create` (`base.setdefault`) i
`brands_ui._add` (`/brand_add`, konfiguracja celu linkedin wpisana na sztywno). Zakaz obowiazywal
od 22/07, a kod **przez cztery tygodnie rodzil kazdy nowy cel i kazda nowa marke wprost w tej
konfiguracji, ktora wywolala incydent** - u nowego klienta tez. Oba miejsca stoja teraz na
`config.PUBLISH_DRAFT`, czyli na tej samej wartosci, ktora konsument (`channels.dispatch_item`)
i tak przyjmuje przy braku klucza. Nowy cel czeka na reczna wklejke, dopoki Tomasz swiadomie
nie przelaczy go na `post_queue`.

**To samo znalezisko w migracjach, czyli u KAZDEGO nowego klienta.** `002_seed_ags.sql` zakladal
cele `youtube`, `facebook`, `instagram` wprost z `"publish_mode":"webhook"`, a `007_language.sql`
podawal w komentarzu **wzor konfiguracji nowego celu z tym samym trybem**. `DEPLOY_CHECKLIST`
w kroku 6 pisze "DO NOT set webhook", a w kroku 3 kazal zaaplikowac plik, ktory ustawial go za
instalatora - dokladnie AP-316. Oba pliki poprawione na `draft`. **Produkcji to nie rusza**: seed
ma `ON CONFLICT DO NOTHING`, wiec wiersze zasiane wczesniej zostaja takie, jakie sa.

**Swiadome zdjecie blokady:** zmienna srodowiskowa workera
`PUBLISH_WEBHOOK_ODBLOKOWANY=AP-307-callback-naprawiony` plus restart kontenera. Trzy powody
tego ksztaltu: (1) zyje **poza repozytorium**, wiec zaden dokument, commit ani rozmowa z botem
jej nie przestawi - trzeba dostac sie do serwera; (2) **nie jest logiczna** - `true`, `1`, `TAK`
nie dzialaja, wiec nie da sie jej odbebnic odruchem; (3) **haslo nazywa warunek** z AP-307
(callback per wiersz), wiec zeby je wpisac, trzeba wiedziec, czego dotyczy. Zdjecie blokady tez
nie jest ciche: paragon dopisuje ostrzezenie, ze sloty i media sa pomijane.

**Test:** `cm-agent/tests/test_blokada_webhook.py`. Pilnuje SCIEZKI ALARMU (zly wsad -> odmowa
**i zero zapisow do bazy**), obejsc (`WEBHOOK`, spacje, `true` w zmiennej), drogi zdjecia blokady
oraz tego, ze `/brand_add` i `target_create` dalej dzialaja - bezpiecznik, ktory zabija dzialajaca
sciezke, sam bylby awaria (AP-312). Sprawdzony przez celowe wylaczenie bramki: 25 kontroli
na czerwono, w tym obie kontrole "do bazy nic nie poszlo".

**Czego kod NIE wie i musi sprawdzic czlowiek:** jaka wartosc `publish_mode` maja WIERSZE
NA PRODUKCJI. Blokada dotyczy **ustawiania** trybu, nie czyta istniejacych wierszy `channels`.
Kanal, ktory dzis siedzi w bazie z `webhook`, dalej pojdzie sciezka delegata i **zaden test tego
nie zobaczy**. Do sprawdzenia recznie (AP-307 punkt 3 - pytaj o konfiguracje, nie tylko o kod):

```sql
SELECT brand_id, channel, status, config->>'publish_mode' AS tryb FROM channels ORDER BY 1,2;
```

## D-021 [ZAMKNIETE 22/08/2026]: Manager nie ma drogi zapisu NOWEGO prospekta

**TAP-TEST NA ZYWYM WYKONANY 22/08. DLUG ZAMKNIETY W CALOSCI.**

**Zdarzenie zrodlowe tego dlugu wreszcie wyladowalo w bazie.** Rafal Petrykowski - czlowiek,
na ktorym luka wyszla pierwszy raz 11/08 i ktorego wpis lezal od tego czasu w pliku na dysku -
stoi w lejku jako `668d6152-b422-4b80-bac9-7ff3b8161112`, **z `source='lacznik'`**, czyli
zalozony przez nowy endpoint. Zrobil to Manager, gdy tylko narzedzie pojawilo sie w jego liscie.

**Obie sciezki sprawdzone na produkcji, przez dwa rozne organy:**
- **zapis** - Manager, wiersz istnieje z wlasciwym zrodlem;
- **odmowa** - koordynator, proba zalozenia tego samego podmiotu drugi raz.

**Odmowa udowodnila na ZYWYCH DANYCH cos, czego test automatyczny udowodnic nie mogl (AP-313).**
Podalem nazwe **bez ogonka** (`Rafal Petrykowski`), a w bazie stoi **z ogonkiem**
(`Rafał Petrykowski`). Bramka trafila. Powod, ktory sama podala: *"ta sama nazwa po odjeciu
ogonkow i slow rodzajowych"*. To jest dokladnie ten przypadek, dla ktorego powstal AP-313
(`ILIKE '%Chwalin%'` NIE trafia w "Chwaliński") - tylko tym razem **normalizacja zadzialala
po OBU stronach porownania, na prawdziwym wierszu, w produkcji.**

Odmowa spelnila tez komplet wymogow z AP-311: podala **nazwe i identyfikator** wiersza uznanego
za ten sam, **powod**, **co przepadnie** przy porzuceniu wpisu (osoba i notatka 65 znakow),
**dwie drogi dalej** (dopisanie przez `pipeline_move` albo pole `oddzial`), i zakonczyla zdaniem
`NIC nie zapisalem i niczego nie zalozylem`.

**PRZYPADEK TESTOWY Z FRANCZYZA POPRAWIONY, bo instrukcja zestarzala sie przez zmiane DANYCH.**
Procedura z 19/08 kazala zalozyc "Katowice Egurrola Dance Studio" i oczekiwac PRZEJSCIA.
Odczyt lejka z 22/08 pokazuje, ze **Katowice juz tam stoja** (Martyna Jalocha), wiec dzis to samo
wolanie ma dac ODMOWE. **Ktos wykonujacy test wedle pierwotnego brzmienia uznalby DZIALAJACA
bramke za zepsuta.** To AP-316 w odmianie, ktorej wpis nie przewidywal: instrukcja starzeje sie
takze wtedy, gdy kod sie nie zmienil, a zmienily sie DANE - i wyglada przy tym tak samo swiezo.
Franczyze pokrywa test automatyczny; na zywym lejku nie zakladamy fikcyjnych prospektow, bo lejek
jest zrodlem prawdy dla sprzedazy, nie poligonem.

---

## D-021 (zapis czesciowego zamkniecia z 19/08, zostawiony dla kontekstu)

**KOD GOTOWY 19/08. Narzedzie w n8n NIE jest zarejestrowane** - do czasu okna Manager nadal nie ma
jak zalozyc prospekta, mimo ze serwer juz to potrafi. **To jest AP-307 co do litery: nowy kontrakt
zbudowany bez przelaczenia zywego konsumenta.** Opis rejestracji:
`docs/ops/D021_NARZEDZIE_N8N_NOWY_PROSPEKT.md`.

**SPROSTOWANIE DO WLASNEGO OPISU.** Wpis nizej wskazuje `sales.py:626` jako "zdolnosc, ktora
istnieje w kodzie". Ta funkcja (`_ensure_pipeline`) wstawia PIEC kolumn i **nie ma pol
kontaktowych**, wiec zdarzenia zrodlowego tego dlugu - Petrykowskiego z dojsciem - **nie dalaby
rady zapisac**. Prawdziwym pisarzem byl `_pipeline_add:1545` (dziesiec kolumn, z wlasna slaba
bramka). INSERT-ow do `sales_pipeline` byly wiec DWA, nie jeden.

Co zrobione:

1. `sales._wstaw_prospekta` - **jedyny** pisarz nowego wiersza w module. Wolaja go trzy drogi:
   research, narzedzie rozmowy i Lacznik. Trzeci INSERT bylby trzecia okazja do rozjazdu (AP-309).
2. `sales.sprawdz_duplikaty` - **jedna** bramka dla narzedzia `pipeline_add` i dla Lacznika.
   Porownuje **pare (domena, oddzial)**, nigdy sama domene: dedup po domenie zabija franczyzy
   (Grodzisk i Katowice Egurrola, jedna domena, dwa prawdziwe prospekty). **Trzy stany, nie dwa:**
   ten sam / inny / **niepewne**. Ogonki normalizowane po OBU stronach istniejacym mechanizmem
   (`teczka._bez_ogonkow` plus `teczka._jak_nazwa`), bo `ILIKE '%Chwalin%'` NIE trafia
   w "Chwaliński" (AP-313). **Pada ZAMKNIETA** (AP-314): przy niepewnosci nie zaklada. Droga
   wyjscia jedna i jawna, pole `oddzial` - i nie jest wytrychem, bo oddzial stojacy w nazwie
   wiersza z lejka to nadal duplikat.
3. Odrzucenie mowi **KTORY** wiersz uznano za ten sam (nazwa plus identyfikator), **DLACZEGO**,
   i **CO PRZEPADNIE** przy porzuceniu wpisu. To jest AP-311: import z 23/07 wyrzucil dwanascie
   rekordow pytajac tylko "czy nazwa jest w lejku", a nie "czy wnosi cos, czego lejek nie ma" -
   mail i telefon dziewieciu prospektow lezaly na dysku, gdy lejek pokazywal "brak kontaktu".
4. Zapis rozroznia **ZOBACZONE od WYWNIOSKOWANEGO** (AP-317). Oddzial podany wprost dostaje
   etykiete `miasto:`, ktora automat importu czyta jako FAKT; oddzial wywnioskowany z nazwy tej
   etykiety **nie dostaje** i jest nazwany wprost jako domysl.
5. `worker.lacznik_nowy_prospekt` (`POST /lacznik/nowy-prospekt`) za tym samym guardem co reszta
   Lacznika, blad 400 z trescia dla czlowieka.

**ZERO migracji bazy** - `sales_pipeline` ma wszystkie potrzebne kolumny (sprawdzone).

Zachowanie: `cm-agent/tests/test_nowy_prospekt.py`. Przypadek franczyzy przechodzi OBA oddzialy
(sprawdzone: Katowice i Warszawa przy tej samej domenie co Grodzisk). Przy wylaczonej bramce pada
**28 kontroli**, a kontrole franczyzy zostaja zielone - test odroznia wade bramki od sciezki,
ktora ma przechodzic (sprawdzone przez koordynatora). Zestaw 38/38.
Dokumentacja: `docs/komponenty/lacznik.md`, `docs/komponenty/agent-sprzedazy.md`.

**CO ZOSTAJE OTWARTE:**
- rejestracja narzedzia w n8n plus tap-test na zywym (okno z Tomaszem);
- **luka `next_step_date`** - brak drogi zmiany samego terminu bez wpisu tekstu. NIE zalatana
  tym endpointem i **nie nalezy**: danie drzwiom zakladajacym semantyki "a jak juz jest, to popraw"
  przywraca find-or-create, czyli dokladnie to, przed czym stoi bramka. Osobne pytanie do Managera;
- **zywa dziura AP-313 poza zakresem D-021:** `sales._find_pipeline` (po nim chodza `pipeline_move`,
  `outreach_sent`, `offer_for`, `draft_outreach`) **nadal nie normalizuje ogonkow**, wiec
  `pipeline_move("Chwalinski")` nie trafi w "Grupa Chwaliński". Ma znaczenie dokladnie przy
  poprawce terminu z punktu wyzej.

---

## D-021 (tresc oryginalna z 11/08, zostawiona dla kontekstu - `sales.py:626` wskazane BLEDNIE, patrz sprostowanie)

**Zapisany 11/08/2026 (zgloszenie Managera Z-6; odczyt wykonany, budowa NIE).**

**Zdarzenie:** Tomasz odwrocil rozmowe sprzedazowa z Rafalem Petrykowskim (kontakt pierwszego
stopnia na LinkedInie). Wiadomosc poszla. **Manager nie mial jak tego zapisac** - wpis lezy
w pliku na dysku.

**Co Manager MA przez Lacznik:** `GET /lacznik/stan`, `GET /lacznik/teczka` (odczyt),
`POST /lacznik/raport`, `POST /lacznik/zapisz-tekst` (zapis).

**Dlaczego odmowilo:** `teczka.zapisz` ma w kontrakcie *"Nieznany identyfikator = blad z lista
podobnych, NIGDY ciche zalozenie nowego wiersza"*. **To NIE jest wada, tylko swiadoma bramka** -
ciche zakladanie wierszy zamienialoby kazda literowke w nazwisku w nowego prospekta.
**Rozluznienie jej byloby bledem.**

**Czego NIE MA:** endpointu zakladajacego prospekta. Zdolnosc **istnieje w kodzie**
(`sales.py:626`, `INSERT INTO sales_pipeline`), ale nie jest wystawiona do Lacznika.

**Prawdziwa trudnosc - bramka duplikatow:** dedup po samej domenie **zabija franczyzy**.
W lejku stoja dzis `Grodzisk Mazowiecki Egurrola Dance Studio` i `Katowice Egurrola Dance Studio` -
ta sama domena `egurrola.com`, dwa rozne prospekty, dwa rozne kontakty. Bramka musi patrzec
na **pare (domena, oddzial/osoba)**, nie na sama domene.

**Waga (sformulowanie Managera):** to nie jest wygoda. Baza ma byc zrodlem wiedzy, a lancuch peka
dokladnie w chwili, w ktorej pojawia sie NOWY czlowiek - czyli w jedynym momencie, ktory buduje lejek.

## D-022 [ZAMKNIETE 19/08/2026]: Kanal z trybem publikacji, ktorego nie zna zaden konsument

**NAPRAWIONE W KODZIE 19/08. Danych produkcyjnych nie ruszano** - `AGS/sprzedaz` zostaje z `none`,
zgodnie z decyzja Managera Z-3.

**SPROSTOWANIE DO WLASNEGO OPISU, ZROBIONE ODCZYTEM.** Wpis nizej mowi, ze `none` "przechodzi
przez cala funkcje i nie dzieje sie nic, bez wyjatku, bez wpisu w dzienniku, bez sladu".
**To nieprawda i mylilo w bezpieczna strone.** Galaz `else` w `dispatch_item` nie byla galezia
trybu `draft`, tylko **lapaczem wszystkiego**, wiec wiersz konczyl na `status='held'`. A `held`
uruchamia `worker._send_manual_paste_kits`, ktory przysyla Tomaszowi PELNA TRESC z poleceniem
"wklej recznie i odpisz `wklejone <id>`".

**Skutek byl wiec GORSZY niz cisza: ustawienie mowilo "nie publikuj", a system prosil czlowieka
o reczna publikacje na tym kanale.** Sprawdzone przez koordynatora w trzech ogniwach: stara galaz
`else` (`git show`), selekcja `held` w `_send_manual_paste_kits:665`, i test cofniety do stanu
sprzed poprawki. Drugie sprostowanie: `channels.for_item` nie istnieje, selektorem kanalow jest
`channels.active_targets`.

Co zrobione:

1. `config.PUBLISH_NONE` obok pozostalych `PUBLISH_*`, krotka `TRYBY_PUBLIKACJI` i bramka
   `config.tryb_publikacji_znany` w konwencji `sprawdz_tryb_publikacji` z D-020.
2. `channels.dispatch_item`: **dwie jawne galezie PRZED lapaczem.**
   - **WYLACZONY** (`none`): wiersz na `rejected` (wartosc JUZ ISTNIEJACA w slowniku kolejki,
     zero migracji), powod do `agent_logs` poziom `warn`, paragon mowiacy wprost, ze kanal jest
     wylaczony, ze to NIE awaria i czym to odkrecic. Stan terminalny, wiec nie ma juz gotowca
     do wklejania ani alarmu o zwisie.
   - **NIEZNANY** (literowka, tryb z przyszlosci): wiersz **zostaje NIETKNIETY w `review`**,
     dziennik poziom `error`, meldunek podaje DOSLOWNIE wartosc, ktorej kod nie zna. Nie
     publikujemy, bo nie wiemy czym (bramka pada zamknieta, AP-314); nie poprawiamy po cichu,
     bo cicha korekta wyglada jak sukces (AP-306); nie kasujemy wiersza, bo po poprawieniu
     ustawienia material ma pojsc bez regeneracji. Stan nieterminalny sprawia, ze
     `_dispatch_timeout_alert` odezwie sie ponownie, jesli nikt nie zareagowal.
3. `worker._dispatch_ack`: osobne linie dla obu trybow zamiast wspolnego "gotowiec czeka na Twoje
   reczne wklejenie".

**DLACZEGO WYLACZONY I NIEZNANY TO DWA PRZYPADKI, A NIE JEDEN:** do 19/08 kazda nieznana wartosc
zachowywala sie jak wylaczenie, czyli **blad konfiguracji byl nieodroznialny od swiadomego
ustawienia**, a system sam wybieral za czlowieka, co ta wartosc "pewnie znaczy". Domysl
podstawiony za decyzje to AP-317 w warstwie konfiguracji.

**CZEGO NIE ZROBIONO, POWIEDZIANE WPROST:** `channels.active_targets` nadal WYBIERA kanal z trybem
`none` jako cel, wiec wariant dla wylaczonego kanalu jest generowany i stagowany, a dopiero
dispatch go zamyka. Czystsza naprawa jest o warstwe wyzej (nie stagowac wcale), ale zmienia,
ktore kanaly dostaja warianty, i nalezy do osobnej decyzji. Osobno: gdy material celuje WYLACZNIE
w kanal wylaczony, `reconcile_publications` awansuje go potem na `published`, bo wszystkie wiersze
sa terminalne. To istniejaca slabosc reconcile przy wierszach nieudanych, nie nowa - ale D-022
dokłada jej nowe wystapienie i warto to nazwac.

Zachowanie: `cm-agent/tests/test_tryb_publikacji_wylaczony.py` (tryb wylaczony, tryb nieznany
oraz REGRESJA trybow zwyklych: `post_queue`, `draft`, brak klucza, `webhook` z adapterem i bez;
przy obu galeziach wylaczonych pada pietnascie kontroli, sprawdzone przez koordynatora).
Zestaw 37/37. Dokumentacja: `docs/komponenty/kolejka-publikacja.md`.

---

## D-022 (tresc oryginalna z 19/08, zostawiona dla kontekstu - w czesci NIEPRAWDZIWA, patrz sprostowanie wyzej)

**Zapisany 19/08/2026 (znalezisko przy blokach B i C, decyzja Managera: do kolejki, nie ruszac teraz).**

`AGS/sprzedaz` ma na produkcji `config->>'publish_mode' = 'none'`. Taka wartosc nie pasuje do
zadnej galezi w `channels.dispatch_item`: nie jest `webhook`, nie jest `post_queue`, a domyslka
`config.PUBLISH_DRAFT` dziala tylko przy BRAKU klucza, nie przy kluczu z nieznana wartoscia.
Kanal ma status `draft`, wiec `channels.for_item` go WYBIERA - i wtedy nie dzieje sie nic.

**Why bad:** to rodzina "cisza wyglada jak sukces" (AP-306, AP-310, AP-314). Material trafia do
kanalu, kanal go przyjmuje, nie leci wyjatek, nie ma wpisu w dzienniku, a publikacja nie nastepuje.
Z zewnatrz nieodroznialne od kanalu, ktory nie mial czego opublikowac. Jesli `none` jest CELOWYM
sposobem wylaczenia kanalu, to jest tez AP-312: nazwa nie mowi, ze to wylacznik, a zachowanie nie
mowi, ze cos zostalo pominiete.

**Do zrobienia:** nieznany tryb ma **padac glosno albo meldowac pominiecie**, nigdy milczec.
Jesli `none` ma zostac jako wylacznik, nazwac go wprost i obsluzyc jawna galezia z paragonem.
Do rozstrzygniecia przy okazji, ktora i tak otwiera `channels.py` - **osobnego okna na to nie
wydajemy** (decyzja Managera 19/08).

**Punkt zaczepienia:** `cm-agent/app/channels.py`, `dispatch_item` (~linia 294) i `for_item` (~19).

## D-023: Wyczerpanie srodkow API nie ma alarmu - kazda sciezka LLM pada po cichu do logu

**Zapisany 19/08/2026 (znalezisko z okna serwerowego B+C).**

**Dowod produkcyjny.** Podczas weryfikacji okna 19/08 bot odpowiedzial `Blad przetwarzania
wiadomosci`. W logu:
`anthropic.BadRequestError: 400 - 'Your credit balance is too low to access the Anthropic API.'`

Log pokazywal **powtarzalne** padanie `proactive.tick` w petli, nie pojedynczy przypadek - czyli
awaria trwala JAKIS CZAS PRZED oknem. Nikt sie o niej nie dowiedzial, dopoki czlowiek nie napisal
do bota. `/health` zwracalo `{"status":"ok"}` przez caly ten czas, bo nie dotyka modelu.

**Why bad:** to rodzina "cisza wyglada jak sukces" (AP-306, AP-310, AP-314, AP-315), ale grozniejsza
od typowego przypadku, bo **jedna przyczyna wycina naraz WSZYSTKIE organy oparte na modelu**:
generacje, subagentow, rozmowe, planer, filtry tresci. Deterministyczne sciezki (`/karty`, kolejka,
Scheduler) chodza dalej i system wyglada na zywy. Sonda zdrowia jest slepa z definicji, bo pyta
o proces, nie o zdolnosc do pracy. Do tego przyczyna jest ZEWNETRZNA i odnawialna: wroci przy
kazdym wyczerpaniu srodkow, niezaleznie od jakosci kodu.

**Malo prawdopodobne, ale warte nazwania:** awaria byla widoczna dla Tomasza dopiero jako
"blad przetwarzania", czyli komunikat, ktory nie mowi, co sie stalo ani co zrobic.

**Do zrobienia (do rozstrzygniecia przez Managera):**
1. rozpoznawac `credit balance is too low` osobno od innych bledow modelu i meldowac Tomaszowi
   WPROST, z nazwa przyczyny i linkiem do doladowania, zamiast generycznego "blad przetwarzania";
2. alarm po stronie systemu przy pierwszym takim bledzie, nie po N-tym, i BEZ powtarzania
   przy kazdym tiku (inaczej zaleje kanal);
3. rozwazyc, czy `/health` ma odrozniac "proces chodzi" od "system jest zdolny do pracy" - to
   ta sama roznica, ktora AP-315 nazwal miedzy forma a gatunkiem.

**Punkt zaczepienia:** `cm-agent/app/proactive.py` (`tick`, `_propose_for_gap`),
`cm-agent/app/conversation.py` (`_discuss`), wspolny klient modelu w `generate.client`.

## D-024: Drugi magazyn regul (`channels.config.rules`) bez filtra, rodzaju i pochodzenia - BLOK H

**Zapisany 19/08/2026 (znalezisko z bloku B; decyzja Managera Z-2 z 19/08).**

Rownolegly do `style_learned` magazyn regul: `channels.config.rules`, pisany narzedziem
`subagent_remember_rule` z rozmowy, czytany przez `generate._channel_rules` (`generate.py:208`)
i wstrzykiwany do **KAZDEGO wariantu kanalowego** jako:

`OWNER RULES FOR THIS ACCOUNT (obey strictly, override defaults if conflict): ...`

Do 20 pozycji per kanal. **Bez filtra jezykowego**, ktory `style_learned` dostal 10/08 po AP-315,
**bez rodzaju** (preferencja kontra polecenie) i **bez pochodzenia**. Sformulowanie jest mocniejsze
niz wszystko, co stalo kiedykolwiek w `style_learned`: to wprost polecenie posluszenstwa z prawem
nadpisania domyslnych zasad.

**Decyzja Managera Z-2 (19/08): to OSOBNA sprawa, D-019 NIE rozciaga sie na nia wprost.**
Uzasadnienie: tu pisze **czlowiek przez narzedzie**, nie model z destylacji, a to jest **legalna
droga konfiguracji subagenta**. Wylaczenie zapisu boli tu bardziej niz przy stylu, bo odbiera
jedyna droge konfigurowania kanalu. **Zapis zostaje WLACZONY do czasu bloku H.**

**Zakres bloku H (po D+E), cztery pozycje:**
1. ten sam **filtr jezykowy**, ktory `style_learned` dostal po AP-315;
2. **ksztalt wpisu** (jezyk, rodzaj, pochodzenie) PRZY ZAPISIE, nie zgadywany przy odczycie;
3. **zmiana prefiksu** tak, zeby zaden zbior regul kanalowych nie mial prawa nadpisac walidatora
   jezyka i gatunku - dzisiejszy prefiks daje mu to prawo wprost;
4. **wykaz WSZYSTKICH obecnych wpisow** `config.rules` do przegladu Managera.

**Punkty zaczepienia:** `cm-agent/app/generate.py:208` (`_channel_rules`),
`cm-agent/app/conversation.py` (narzedzie `subagent_remember_rule`, zapis do `channels.config`
przez `jsonb_set` na kluczu `rules`, ~linia 2717).

## D-025: Brak drogi zmiany SAMEGO terminu spotkania, bez wpisu tekstu

**Zapisany 19/08/2026 (znalezisko z bloku E; decyzja Managera 19/08: rejestrujemy, wykonanie PO OKNIE n8n).**

**Czekajacy przypadek, prawdziwy i przeterminowany:** spotkanie z **Grupa Chwalinski** jest
03.09.2026 o **9:00**, ul. Wroclawska (potwierdzone przez Tomasza 15/08), a **w bazie wisi 11:00**.
Nikt tego nie poprawil, bo nie ma czym.

**AKTUALIZACJA 22/08: czekajacy przypadek PRZESTAL ISTNIEC.** Odczyt `stan_gry` pokazal wpis
z 21/08: **Marek Sroka odwolal mailem spotkanie 3.09** (zebranie wszystkich pracownikow), prosi
o kontakt po powrocie Miroslawa z urlopu 01/09. W lejku stoi juz `Grupa Chwalinski, nastepny
kontakt 01/09 12:00`. **Sama luka zostaje** - drogi zmiany terminu bez wpisu tekstu nadal nie ma -
ale straciła swoj dowod, wiec przy ustalaniu priorytetu nie wolno juz powolywac sie na "wisi
przeterminowana poprawka". Przy okazji: Marek Sroka JEST kontaktem po stronie Chwalinskiego,
co domyka zagadke nazwiska z AP-317 (korekta z 19/08 zostaje bez zmian - przypis ma mowic to,
co bylo potwierdzone, a nie to, co pozniej okazalo sie trafnym domyslem).

**Stan faktyczny (odczyt z 19/08):**
- `/lacznik/zapisz-tekst` **umie** ustawic `next_step_date`, ale `teczka.zapisz` wymaga niepustej
  `tresc` i kanalu ze slownika. **Zmiana samej godziny wymusza wiec wymyslenie fikcyjnego wpisu**
  do `engagement_log`. To jest cala luka: zeby poprawic liczbe, trzeba sklamac w dzienniku.
- `sales._pipeline_move` umie ustawic `next_followup_at` osobno, ale jest osiagalny WYLACZNIE
  jako narzedzie LLM w rozmowie Sprzedawcy. Lacznik go nie ma.
- `teczka._ustaw_krok` juz istnieje i obsluguje OBA rejestry (lejek `next_followup_at`,
  kontakt `next_action_due`).

**Dlaczego NIE zalatano tego endpointem z D-021** (swiadoma decyzja, nie przeoczenie):
`/lacznik/nowy-prospekt` to **drzwi zakladajace**. Danie im semantyki "a jak juz jest, to popraw"
przywraca find-or-create, czyli dokladnie to, przed czym stoi bramka D-021. Literowka w nazwie
albo zalozylaby ducha, albo **po cichu przesunela termin komus innemu**.

**Koszt osobnej drogi:** maly. `POST /lacznik/termin` (~15 linii w `worker.py`) plus publiczne
`teczka.ustaw_krok` (~20 linii): `znajdz` (odporne na ogonki, odmawia przy wieloznacznosci, nigdy
nie zaklada) plus `_ustaw_krok` plus jeden wezel w n8n.

**Trzy rzeczy, ktorych przy tym NIE WOLNO pominac:**
1. **Stara wartosc MUSI wrocic w potwierdzeniu** ("bylo 11:00, jest 9:00"). Dzis `_ustaw_krok`
   nadpisuje po cichu, a **cicha zmiana daty to dokladnie mechanizm, ktorym 11:00 sie tam znalazlo**.
2. **Skad wziela sie nowa godzina, musi zostac zapisane** (AP-317). `next_followup_at` nie niesie
   pochodzenia. Minimum: dopisek "termin poprawiony 11:00 -> 9:00, zrodlo: potwierdzenie Tomasza 15/08".
3. `_ustaw_krok` uzywa `COALESCE`, wiec **terminu NIE DA SIE skasowac** (NULL znaczy "bez zmian").
   Kasuje tylko galaz `park` w `apply_followup`, z guzika. Do rozstrzygniecia, czy to wada.

**ZALEZNOSC, ktora trzeba zamknac RAZEM z tym dlugiem:** `sales._find_pipeline` (po nim chodza
`pipeline_move`, `outreach_sent`, `offer_for`, `draft_outreach`) **nadal nie normalizuje ogonkow**,
wiec `pipeline_move("Chwalinski")` NIE trafi w "Grupa Chwaliński" (AP-313). To jest ta sama nazwa,
ktorej dotyczy czekajacy przypadek - poprawka terminu bez tej naprawy nie zadziala.

**Punkty zaczepienia:** `cm-agent/app/worker.py` (endpointy Lacznika), `cm-agent/app/teczka.py`
(`_ustaw_krok`, `znajdz`), `cm-agent/app/sales.py` (`_find_pipeline`).

## D-026: Sekret Lacznika lezy otwartym tekstem w eksporcie w repo, a bramka eksportera patrzy obok

**AKTUALIZACJA 22/08: krok 1 z czterech ZROBIONY - bramka naprawiona.**

`n8n-workflows/eksport-do-repo.cjs` pyta teraz o WARTOSC, nie o nazwe pola. Chodzi po **DRZEWIE
JSON**, nie po tekscie, i mierzy **lite bloki**: nieprzerwane ciagi `[A-Za-z0-9]` od 32 znakow
(od 24, gdy blok jest czysto szesnastkowy). **Separatory blok przerywaja i to samo z siebie
rozwiazuje problem falszywych alarmow:** UUID (8-4-4-4-12) rozpada sie na czlony po najwyzej
12 znakow, wiec `id` wezla, `versionId`, `activeVersionId` i `webhookId` NIE MAJA JAK trafic
w prog. Nie trzeba bylo wpisywac ich na zadna liste.

Doszla regula, ktorej brakowalo wprost: **para nazwa/wartosc** - obiekt ma `name` brzmiace jak
sekret i osobne `value`. Dokladnie ksztalt, o ktory ten dlug sie potknal.

Biale listy sa dwie i obie jawne. Na KLUCZACH zwalniaja PARE (klucz, ksztalt), nie sam klucz:
sekret 48-hex podlozony pod `id` nadal wpada. Progi zmierzone na dziewieciu prawdziwych
eksportach: 32 daje 13 trafien i zero smiecia, 24 zaczyna lapac wlasne slownictwo n8n,
20 lapie kilkanascie wyrazow. **Bramka, ktora krzyczy przy kazdym eksporcie, zostanie wylaczona
i nie chroni niczego** - to bylo kryterium projektowe, nie estetyka.

Komunikat odmowy jest DZIALALNY: podaje sciezke w JSON razem z NAZWA WEZLA, dlugosc wartosci
i jej dwanascie pierwszych znakow, nigdy calosc, plus cztery kroki, co z tym zrobic. Nowy tryb
`skan <plik.json>` przepuszcza pliki z dysku tym samym torem, bez sieci i bez zapisu.

**PROBA ZLYM WSADEM WYLAPALA DWA BLEDY W SAMEJ BRAMCE (AP-314 punkt 1 zadzialal).**
`meta.instanceId` (64 hex, odcisk instancji n8n) wpadal w regule base64 ZANIM biala lista miala
szanse sie odezwac - bramka odmawialaby przy KAZDYM zywym eksporcie. **Ten sam blad mial
oryginal.** Drugi: plik z samymi zaslepkami `__X_CONSUMER_SECRET__` byl odrzucany, choc nie ma
w nim zadnego sekretu.

**AP-309, przeliczone: sekret Lacznika NIE JEST jedynym miejscem.** Bramka zatrzymuje **dwa
z dziewieciu** eksportow. Drugi to komplet poswiadczen OAuth1 do konta X - patrz **D-027**,
wpis powazniejszy niz ten.

**Sprostowanie liczby w tym wpisie:** sekret Lacznika stoi w PIECIU miejscach, nie czterech -
cztery naglowki `X-Lacznik-Secret` plus **sciezka triggera MCP** (`nodes[0] "MCP Lacznik"
.parameters.path`, ksztalt `lacznik-<48 hex>`).

**Zostaje: kroki 2, 3 i 4** - wymiana sekretow i sprzatanie repo, wymagaja czlowieka i zgody
Managera. Bramka naprawiona PRZED sprzataniem celowo.

**Zapisany 22/08/2026 (znalezisko z okna n8n, faza 2).**

`n8n-workflows/lacznik-chat-tools.json` zawiera **zywy sekret `X-Lacznik-Secret` w czterech
miejscach**, otwartym tekstem. Plik jest **sledzony przez gita i wypchniety na origin**.
Repozytorium jest **prywatne** (potwierdzone przez Tomasza 22/08), wiec ekspozycja ogranicza sie
do osob z dostepem - ale sekret nalezy uznac za ujawniony i wymienic.

**Dlaczego bramka eksportera go nie zlapala - i to jest wlasciwa lekcja.**
`n8n-workflows/eksport-do-repo.cjs` ma liste wzorcow ZABRONIONYCH, ktorych trafienie ma odmowic
zapisu. Jeden z nich to `(?:secret|password|passwd|apikey|api_key|token)\s*[:=]\s*["'][^"']{16,}["']`.
Wyglada na komplet, a **nie ma szansy trafic w ksztalt, ktorego uzywa n8n**:

```
"name": "X-Lacznik-Secret",
"value": "<48 znakow hex>"
```

Slowo `secret` stoi po stronie **nazwy naglowka**, a wartosc siedzi pod kluczem `value`.
Bramka pytala o KSZTALT PRZYPISANIA, a nie o to, CZY TO JEST SEKRET - **AP-315 co do litery,
tylko o warstwe nizej**: tam walidator sprawdzal forme tekstu zamiast gatunku, tu maskownik
sprawdza forme przypisania zamiast tego, czym jest wartosc.

**Druga polowa: opis commita klamal i nikt tego nie zauwazyl.** Commit `67b6190` nazywa sie
"Kopia definicji Lacznika po dolozeniu pary teczki (**bez sekretu, sanityzowana**)". Pozniejszy
`c1dc6a1` wpisal sekret z powrotem, a **tytul tamtego commita zostal w historii jako swiadectwo,
ktore juz nie obowiazuje**. To AP-316 przeniesione na komunikaty commitow: opis stanu starzeje
sie tak samo jak instrukcja, tylko nikt go nie odswieza, bo commit jest niezmienny.

**Do zrobienia (kolejnosc ma znaczenie):**
1. **Najpierw naprawic bramke**, potem czyscic. Odwrotnie to zamiatanie objawu: nastepny eksport
   wpisze sekret ponownie. Bramka ma pytac o WARTOSC, nie o nazwe pola - kandydat: kazdy ciag
   hex dlugosci >= 32 poza znanymi identyfikatorami, plus jawna biala lista.
2. Wymienic sekret `lacznik_e2_secret` w `app_secrets` i w definicji workflow. **UWAGA: sekret
   siedzi w sciezce triggera MCP**, wiec zmiana przestawia adres konektora w claude.ai - trzeba
   go zaktualizowac po stronie Tomasza, inaczej Manager traci wszystkie cztery narzedzia.
3. Rozstrzygnac, czy czyscic HISTORIE gita (przepisanie historii repo wspoldzielonego z serwerem
   i galeziami), czy uznac wymiane sekretu za wystarczajaca. **Rekomendacja: wymiana wystarczy**,
   bo po niej stary ciag jest bezwartosciowy, a przepisanie historii ma wlasne ryzyko i dotyka
   klonu na Mikrusie.
4. Sprawdzic POZOSTALE eksporty w `n8n-workflows/` tym samym pytaniem - nie zakladac, ze to
   jedyny plik (AP-309: policz miejsca, zanim uznasz poprawke za zrobiona).

**Punkty zaczepienia:** `n8n-workflows/eksport-do-repo.cjs` (tablica wzorcow zabronionych),
`n8n-workflows/lacznik-chat-tools.json`, `app_secrets` klucz `lacznik_e2_secret`.

## D-027: Komplet poswiadczen OAuth1 do konta X wpisany na sztywno w eksporcie w repo

**Zapisany 22/08/2026 (znalezisko przy naprawie bramki z D-026). POWAZNIEJSZY NIZ D-026.**

`n8n-workflows/x-agent/ags-hitl-handler-v1.json` zawiera **cztery poswiadczenia OAuth1 do konta X**
wpisane na sztywno w `parameters.jsCode` dwoch wezlow: `Post Edited To X` (nodes[16])
i `Post To X Approve` (nodes[26]). Sa to: klucz aplikacji, sekret aplikacji, token dostepu
i sekret tokenu - czyli **komplet wystarczajacy do publikowania na koncie Tomasza**.

**Zasieg (sprawdzony):** plik jest sledzony przez gita, **jest na origin**, a w historii dotykalo
go **jedenascie commitow**. Repozytorium jest PRYWATNE, wiec krag jest ograniczony - ale
poswiadczenia nalezy uznac za ujawnione.

**Pierwszy commit, ktory wprowadzil ten plik, nazywa sie `Sync production workflows +
SECURITY SANITIZATION + cleanup`** (`3340d7c`). To drugi raz tego samego dnia, gdy opis commita
swiadczy o czyms, czego w tresci nie ma - przy D-026 bylo "bez sekretu, sanityzowana".
**Komunikat commita jest deklaracja autora, nie wlasnoscia tresci**, a wyglada jak swiadectwo.

**Dlaczego stara bramka eksportera tego nie widziala, mimo ze miala regule na `token = "..."`.**
Bo dzialala na TEKSCIE pliku, a w JSON-ie kod wezla ma cudzyslowy uciekane:
`consumerSecret = \"...\"`. Wzorzec `[:=]\s*["']` trafial na ukosnik odwrotny i nie dopasowywal sie.
**To trzecie wcielenie tej samej choroby** - po AP-315 i po samym D-026: sprawdzanie FORMY ZAPISU
zamiast tego, czym jest wartosc. Nowa bramka (D-026 krok 1) chodzi po sparsowanym drzewie,
gdzie znakow ucieczki juz nie ma, i widzi to od razu.

**Waga wyzsza niz D-026, z dwoch powodow:**
1. to nie sekret wewnetrznego lacznika, tylko **poswiadczenia konta w serwisie zewnetrznym**;
2. **konto X bylo juz raz zablokowane 25/07** (403, przejsciowa blokada) - drugie zdarzenie
   na tym koncie ma inna wage niz pierwsze.

**Za to TANSZE w naprawie niz D-026:** rotacja kluczy X idzie po stronie `developer.x.com`
i **NIE przestawia adresu konektora MCP**, wiec nie zrywa Managerowi narzedzi. Wymaga natomiast
podmiany wartosci w dwoch wezlach n8n - czyli **okna**, i najlepiej tego samego, w ktorym
wykonamy D-017.

**Do zrobienia:**
1. rotacja kompletu kluczy X po stronie `developer.x.com`;
2. wyjecie ich z `jsCode` do `app_secrets` albo poswiadczenia n8n - **wzorzec jest juz w repo**,
   bo `Post To X Approve` czyta token Telegrama przez `$('PostgreSQL Lookup Session')...tg_token`,
   czyli ten wezel UMIE juz siegac do bazy;
3. ponowny eksport przez naprawiona bramke - ma przejsc bez znalezisk;
4. decyzja o historii gita (jedenascie commitow) wspolnie z ta sama decyzja dla D-026.

**NIEUSTALONE, wymaga okna:** kopia w repo ma 143 wezly, a zywa definicja 254, wiec **nie wiadomo,
czy produkcja nadal ma te klucze w `jsCode`**. Niezaleznie od odpowiedzi rotacja jest potrzebna,
bo klucze leza w repo i na origin.

**Punkty zaczepienia:** `n8n-workflows/x-agent/ags-hitl-handler-v1.json` wezly `Post Edited To X`
i `Post To X Approve`; wzorzec odczytu z bazy w tym samym pliku (`PostgreSQL Lookup Session`).

## D-028 [ZAMKNIETY PO STRONIE cm-agenta 22/08]: Sufiks `@nazwabota` w grupie rozbraja komendy

**Zapisany 22/08/2026 (znalezisko z przygotowania migracji do supergrupy).**

**Mechanizm.** W grupie klient Telegrama doklada do komendy nazwe bota: tap w menu wysyla
`/karty@AGSbot`, a przy wielu botach sufiks jest WYMAGANY. Wzorce komend byly zakotwiczone
na `$`, wiec z sufiksem przestawaly pasowac.

**Why bad:** to rodzina "cisza wyglada jak sukces" (AP-306, AP-310, AP-315), ale z GADATLIWYM
objawem, czyli grozniejsza w odbiorze. Wiadomosc nie ginie: `Detect Update Type` przepuszcza ja
jako `plain_text` (uzywa `startsWith`, wiec sufiks jej nie rusza), Python nie rozpoznaje komendy,
a tekst trafia do LLM, ktory go grzecznie kwituje. **Czlowiek widzi ODPOWIEDZ, wiec nie ma powodu
podejrzewac awarii** - dopiero brak skutku zdradza problem, i to po czasie.

**Zamkniete 22/08 po stronie cm-agenta, SIEDEM miejsc:** `conversation._PREVIEW_RE`,
`_SCHOWEK_RE`, `_KARTY_RE`, `_DECYZJE_RE`, `_CANCEL_RE`, `brands_ui._CMD_RE` oraz
`sales.try_command` (bylo porownanie do krotki literalow, nie regex). Notacja `(?:@\w+)?` -
ta sama, ktora od dawna mialy `_KONTEKST_RE` i piec wzorcow w `sales.py`.

**To jest AP-309 w czystej postaci.** Ktos juz kiedys sie na tym przejechal i naprawil DWA
miejsca punktowo. Wada zyla dalej w siedmiu pozostalych przez caly ten czas, **niewidoczna,
bo w czacie prywatnym sufiksu nie ma**. Dlatego bramka nie jest lista przypadkow, tylko
**SKANEM ZRODEL**: `cm-agent/tests/test_sufiks_bota_w_grupie.py` czyta wzorce z `app/*.py`
i zada sufiksu po kazdej nazwie komendy. Osma komenda dopisana bez sufiksu zapali sie sama.

**Najgrozniejszy pojedynczy przypadek (zamkniety):** `sales.try_command` wychodzil z uzbrojonego
trybu `/add_sales_material` przez `low in ("/cancel","/anuluj","anuluj")`. `/anuluj@AGSbot` nie
pasowal do krotki, a linijke nizej wypadal z galezi przez `not text.startswith("/")` - czyli
**przelatywal BEZ SLADU, tryb zostawal uzbrojony na dwie godziny, a nastepna wklejka >= 200
znakow wchodzila do bazy wiedzy jako material sprzedazowy.**

**Bramka zaplacila za siebie natychmiast:** pierwsza wersja skanera przechodzila na zielono,
BEDAC SLEPA na forme `/(alternatywa|...)` uzywana przez `brands_ui._CMD_RE`. Zlapala to asercja
"skan faktycznie cos przejrzal". Sprawdzone niezaleznie przez koordynatora na innym wzorcu
(`_DECYZJE_RE`): po cofnieciu poprawki test pada z DWOCH stron - przypadkiem funkcjonalnym
i przegladem statycznym.

**OTWARTE - jedno miejsce w n8n, do najblizszego okna (NIE otwieramy dla niego okna):**
wezel `Parse And Authorize Set`: `reqText.trim().match(/^\/set\s+(\S+)\s+([\s\S]+)$/)`.
Poprawka: `/^\/set(?:@\w+)?\s+.../`. Objaw do czasu patcha: `/set@AGSbot klucz wartosc` dostaje
odpowiedz "Format: /set <klucz> <wartosc>" na POPRAWNA komende. Reszta n8n jest odporna:
routing przez `startsWith` (23 dopasowania), `Parse Get Key` bierze `parts[1]`, osiem
`Parse *Callback` czyta `callback_query.data`, do ktorej Telegram sufiksu nie doklada.

**Punkty zaczepienia:** `cm-agent/app/conversation.py:30-45`, `cm-agent/app/brands_ui.py:22-27`,
`cm-agent/app/sales.py:2187-2198`, `cm-agent/tests/test_sufiks_bota_w_grupie.py`.

## D-029: `/anuluj` jest MARTWY od dawna i nie ma to zwiazku z grupa

**Zapisany 22/08/2026 (znalezisko uboczne przy D-028).**

Lista przepustowa w wezle `Detect Update Type` wymienia: `/plan /cancel /kolejka /raport /karty
/schowek /decyzje /brand /prospect /oferta /pipeline /add_sales_material /dziennik /kontekst`.
**`/anuluj` jej NIE MA** (sprawdzone: w calym pliku workflow wystepuje `/cancel`, nie `/anuluj`),
a ostatnia regula to `if (txt && !txt.startsWith('/'))`. Czyli `/anuluj` dostaje `type: 'other'`
i **jest wyrzucany w n8n - nigdy nie dociera do Pythona.**

**TRZY miejsca w Pythonie obsluguja `/anuluj` i wszystkie sa MARTWYM KODEM.** Dziala wylacznie
`anuluj` bez ukosnika (przechodzi torem `plain_text`) oraz `/cancel`.

**Why bad:** to nie jest wada dzialania, tylko wada ZAUFANIA DO KODU. Trzy miejsca w repo
twierdza, ze komenda jest obslugiwana; ktos czytajacy kod wyciaga wniosek racjonalny i falszywy
(AP-312 na poziomie martwej sciezki). Do tego objaw dla czlowieka jest niemy: `/anuluj` nie robi
nic i nic nie mowi.

**Do zrobienia (jedna linia, przy najblizszym oknie n8n):** dopisac `/anuluj` do listy
przepustowej w `Detect Update Type`. **Albo** decyzja odwrotna: usunac obsluge `/anuluj`
z Pythona i zostawic sam `/cancel` - wtedy kod przestaje klamac. **Rekomendacja BE: dopisac
do n8n**, bo `anuluj` bez ukosnika juz dziala i uzytkownik ma prawo oczekiwac, ze wersja
z ukosnikiem tez.

**Punkt zaczepienia:** `n8n-workflows/x-agent/ags-hitl-handler-v1.json`, wezel `Detect Update Type`.
