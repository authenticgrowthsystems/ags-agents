# RAPORT do Managera - 11/08/2026 - gotowosc repo dla programisty + D-016, D-017

**Jednym zdaniem:** siedem punktow briefu zamkniete i zweryfikowane na produkcji, ale
**najpowazniejsza przeszkoda dla celu nadrzednego nie byla w briefie** - `main` byl 489 commitow
w tyle, wiec programista sklonowalby kod z polowy czerwca; przy okazji trzy dokumenty
instruktazowe uczyly rzeczy szkodliwych, a skan przed re-eksportem znalazl token bota
wpisany na sztywno w 44 wezlach.

---

## 1. BRIEF: SIEDEM Z SIEDMIU

| # | punkt | stan | dowod |
|---|---|---|---|
| 1 | synchronizacja repo | zamkniete | `main` = galaz pracy, drzewa czyste, 7 galezi skasowanych, tag `archiwum/x-agent-przed-10062026` |
| 2 | `SYSTEM_DATAFLOW` | zamkniete | nadrobiony do 11/08, nowa sekcja "gdzie stoja bramki" (9 pozycji) |
| 3 | `operacje.md` | zamkniete | dopisany, z jawnym "zbudowany, ale NIEPODLACZONY" |
| 4 | indeks AP-306..315 | zamkniete | na gorze biblioteki + wspolny mianownik osmiu z dziesieciu |
| 5 | `DEPLOY_CHECKLIST` | zamkniete | v3 - usunieta instrukcja, ktora kazala odtworzyc AP-307 |
| 6 | D-016 | **wykonane na produkcji** | `nodes` i `activeVersion`: stary napis 0, nowy 1 |
| 7 | `translate_text` | zamkniete | flaga przeznaczenia + kontrola wiernosci, 7/7 odczytow na kontenerze |
| + | AP-307 (poza briefem) | zamkniete | dziesiec z dziesieciu anty-wzorcow ma pelny opis |

**Zestaw urosl z 26 do 32.** Dziewiec nowych dokumentow, piec nowych plikow testowych,
**dwadziescia dwa celowe przywrocenia wady** - kazda bramka zobaczona, jak NIE dziala, zanim
jej zaufalismy.

---

## 2. CZEGO W BRIEFIE NIE BYLO, A BYLO WAZNIEJSZE

### `main` byl 489 commitow w tyle

Zero commitow do przodu, czyste przewiniecie. **Programista klonuje repo, laduje na `main`
i dostaje kod z polowy czerwca** - bez CM w obecnym ksztalcie, bez D-008, bez `handed_off`,
bez trzech warstw AP-315. Mozna bylo wykonac wszystkie siedem punktow co do litery i oddac
mu repozytorium, w ktorym nic z tego nie widac.

### Trzy dokumenty instruowaly do rzeczy szkodliwych albo nieprawdziwych

| dokument | co mowil | stan faktyczny |
|---|---|---|
| `DEPLOY_CHECKLIST` | ustaw `publish_mode='webhook'`; zaaplikuj migracje 001..008 | `webhook` **zabroniony od 22/07** (AP-307: 5 postow w godzine, zgubione media, obcy jezyk); migracji jest **42** |
| `README` | katalogi `skills/`, `mcps/`; X Agent PARKED, LinkedIn BACKLOG | te katalogi nie istnieja, `cm-agent/` (CALY system) nie byl wymieniony; oba kanaly LIVE od miesiecy |
| `SYSTEM_DATAFLOW` | "ostatni DDL 029" | 042 |

**Zaden nie byl oznaczony jako nieaktualny.** Wszystkie wygladaly swiezo - i to jest wlasciwa
tresc problemu, nie same liczby.

### Token bota w definicji n8n (D-017)

Re-eksport workflow do repo mial byc czynnoscia porzadkowa. **Skan przed zapisem pokazal
44 wystapienia tokenu bota Telegrama wklejonego w `parameters.url`** HITL Handlera.
Dokumentacja z 10/08 - moja - podawala na to gotowa komende `curl > plik` razem ze zdaniem,
ze plik jest bezpieczny do commitu. **To zdanie bylo nieprawdziwe.**

**Sprawdzone i wazne: token NIE JEST w historii gita.** Repo bylo i jest czyste.

Kanon "sekrety wylacznie w `app_secrets`, zero literalow w definicjach" okazal sie ZASADA,
nie stanem: Scheduler 0 (de-hardkod 02/07), Lacznik 0, HITL Handler 44.

---

## 3. ZAPYTANIA DO MANAGERA (decyzje, ktorych nie podejmuje sam)

### Z-1. D-017: kiedy odhardkodowujemy token i czy przy okazji rotujemy?

Odhardkodowanie to 44 wezly, czyli skrypt patchujacy na wzor `patches/*.cjs` plus **okno
serwisowe na JEDYNYM interfejsie Tomasza** (po PUT konieczne deactivate+activate).
Repo jest juz zabezpieczone maskujacym eksporterem, wiec **nie pali sie**.

Rotacja nie jest wymuszona - token nie wyciekl poza serwer i maszyne Tomasza. Ale skoro
i tak trzeba dotknac 44 miejsc, zrobienie tego raz z NOWYM tokenem kosztuje tyle samo.

**Rekomendacja: odhardkodowac przy najblizszym oknie n8n, z rotacja w tym samym przebiegu.**

### Z-2. Dwadziescia gnijacych decyzji - co z nimi

Czternascie kart materialow wisi **dwanascie dni**, trzy followupy sprzedazowe dziesiec do
czternastu, plus `#179` (lista 21 materialow X do przerobienia) jedenascie. To nie jest dlug
techniczny - to **stojaca kolejka tresci** przy jednoczesnej zapasci zasiegu.

**USTALENIE Z 16:22, ZMIENIA TO ZAPYTANIE.** Pozycja `#173 stale_approval "Granica miedzy d..."`
wisi 14 dni jako "czeka na Twoja decyzje" - a to jest decyzja dla materialu, ktory WLASNIE
zostal opublikowany. Material przeszedl cala sciezke (zatwierdzony, wycofany, napisany od nowa,
zatwierdzony ponownie, opublikowany), a wpis w rejestrze stoi nietkniety.

**Rejestr decyzji nie zamyka sie, gdy material idzie dalej.** Czyli lista dwudziestu pozycji jest
CZESCIOWO NIEPRAWDZIWA i nie wiadomo, w ktorej czesci. To ta sama rodzina co AP-311: wpis
czytany jako fakt o swiecie, gdy jest tylko faktem o rejestrze. Konsekwencja praktyczna:
przegladanie tej listy "na piechote" oznacza podejmowanie decyzji o rzeczach, ktore juz sie
rozstrzygnely - czyli marnowanie jedynego zasobu, ktorego brakuje.

**Rekomendacja zmieniona: NAJPIERW odczyt, ktory powie, ile z tych dwudziestu jest martwych**
(zestawienie `agent_decisions` z aktualnym `content_items.status` per material), DOPIERO POTEM
przeglad tego, co zostanie. Podejrzewam, ze lista skurczy sie istotnie.

Pierwotna rekomendacja, jesli lista okaze sie zywa: **przejrzec je hurtem w jednym posiedzeniu** (wyciagne pogrupowane, z rekomendacja
per pozycja), zamiast czternastu osobnych kart. Alternatywa uczciwa: wygasic je jawnie
i przyznac, ze plan z 30/07 sie zdezaktualizowal - to tez jest decyzja, byle nie przez milczenie.

### Z-3. Petla nauki jako wektor wstrzykniecia - zostaje w obecnym ksztalcie?

AP-315 pokazal, ze `style_learned` to POLECENIA, nie preferencje, i dwa razy skonczylo sie
publikacja wypowiedzi modelu zamiast tresci. Filtr jezykowy zamyka droge, ktora znamy.
**Nie zamyka klasy**: kazdy przyszly wpis nauczony moze byc poleceniem.

Docelowo wpisy powinny dostawac jezyk i **rodzaj** (preferencja kontra polecenie) PRZY ZAPISIE,
a nie byc zgadywane przy odczycie. To jest zmiana w tym, jak petla sie uczy, wiec nie robie
jej sam. **Pytanie: czy petla nauki ma zostac wlaczona do czasu tej zmiany?**

### Z-4. Uzbrojona mina z AP-307 - naprawiamy czy zostawiamy warunek?

Callback publishera nadal oznacza `published` WSZYSTKIE wiersze materialu (bez `id` wiersza).
Dzis nie boli, bo adaptery po przelaczeniu na `post_queue` sa nieuzywane. **Powrot do trybu
`webhook` bez wczesniejszej naprawy odtworzy falszywy stan bazy co do znaku.**

**Rekomendacja: zostawic jako warunek twardy** (jest zapisany w AP-307 i w komponencie),
nie wydawac na to okna, dopoki nikt nie planuje wracac do `webhook`.

### Z-5. Material build-in-public z ostatnich dwoch dni

Historia jest mocna i prawdziwa: agent opublikowal wlasna notatke recenzyjna pod nazwiskiem
wlasciciela, zyla szesc dni, a naprawa nie byla czarna lista slow, tylko bramka wyjscia
i pytanie o GATUNEK tekstu. Zgodnie z kanonem nie pisze tresci sam.

Publikacja o 16:01 dolozyla do tej historii ostatni element i **jest nim dowod, nie deklaracja**:
czysty prompt dal czysta tresc za pierwszym razem, a post o granicy miedzy agentami opisuje
awarie 29/07-03/08, w ktorej dwa agenty czekaly na siebie cztery dni. System opublikowal lekcje,
ktora sam przerobil na sobie.

**Pytanie: przygotowac fakty do masterpromptu CM?** Jesli tak, potrzebuje jednej decyzji
brzegowej: **czy wpadka z 04/08 wchodzi do materialu publicznego.** Moja rekomendacja -
NIE w tresci publicznej (zgodnie z Twoim rozstrzygnieciem z 10/08: tamto bylo zaprzeczeniem
obietnicy produktu), ale TAK jako powod, dla ktorego bramki powstaly, opisany bez podawania
tresci tamtego posta.

---

## 4. WNIOSKI METODOLOGICZNE

1. **Cztery razy w ciagu dwoch dni odczyt obalil moja wlasna teze** - przy bezpieczniku
   gatunku, przy `_rewrite`, przy `voice bible` i przy D-016. Raz obalil **moj wlasny test**,
   ktory swiecil na zielono przy zepsutym kodzie, bo asercja trafiala w komentarz.
   Za kazdym razem roznice robilo karmienie kontroli **prawdziwymi danymi z produkcji**.
2. **Odczyt zgrubny wprowadza w blad tak samo skutecznie jak brak odczytu.** `grep` po
   "za chwil" trafil w cztery inne zdania i na pol godziny zmienil diagnoze D-016 na bledna.
   Odczytac trzeba to, o co sie pyta, a nie cos podobnego.
3. **Zapisany anty-wzorzec nie jest wdrozonym anty-wzorcem.** Po zapisaniu sprawdz, czy
   jakikolwiek dokument INSTRUKTAZOWY nadal uczy starego zachowania.
4. **Kalibruj progi na prawdziwej parze, nie z teorii.** Kontrola wiernosci przekladu
   w pierwszej wersji NIE lapala przypadku, dla ktorego powstala. Miara zdan doszla dopiero
   po pomiarze: wierny przeklad 0% roznicy, rozjazd 29%.

---

## 5. CO CZEKA

- **DOPISANE 11/08 16:22: publikacja BYLA, o 16:01.** `urn:li:share:7492943159539298304`.
  **D-015 ZAMKNIETE END-TO-END, trzy razy ten sam ksztalt:** `#344` 04/08 16:01, `#358` 05/08 16:01,
  "Granica miedzy dwoma agentami" 11/08 16:01 - za kazdym razem slot planu 16:00, czas kolejki
  wczesniejszy, publikacja o slocie planu plus tik Schedulera. Regula `max(slot, kolejka)`
  potwierdzona na trzech niezaleznych materialach.
  To takze **pierwszy tekst tego systemu powstaly bez polskiej instrukcji w promptcie** - czysty
  prompt dal czysta tresc za pierwszym razem, co potwierdza diagnoze AP-315 empirycznie.
- Potwierdzenie zachowaniem dla D-016: przy najblizszym zatwierdzeniu materialu BEZ slotu guzik
  ma odpowiedziec "Publikacja w slocie, ktory CM zaraz przydzieli".

**Commity:** `8d73b3d`, `2c6d820`, `15a734e`, `6a18d4a`, `513de40`, `d3022c7`, `1c43471`,
`76ea8d3`, `aa5a203`, `584271c`, `b05a7fe`, `f601b3b`, `f989dd9`, `0539833`, `7830989`,
`05955c0`, `899aa60`.
**Produkcja:** `cm-agent:d016` (= `latest`). Cofniecie o krok: `cm-agent:ap315d`.
**Repo:** `main` = `claude/silly-blackwell-dfc32d` = `899aa60`, dwie galezie zamiast dziewieciu.
