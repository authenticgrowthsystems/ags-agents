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

## D-015 [CZESCIOWO ZAMKNIETE 10/08/2026]: ktora godzine widzi czlowiek

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

## D-021: Manager nie ma drogi zapisu NOWEGO prospekta - lancuch peka przy nowym czlowieku

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
