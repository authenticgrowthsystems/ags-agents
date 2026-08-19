# MASTER-PROMPT build-in-public do Content Managera (19.08.2026)

**Podstawa zlecenia:** blok F z `C:\Claude-CoWork\AGS\Sprzedaz\04_PLAN\BRIEF_BE_15082026.md`,
sekcja "UZUPELNIENIE 19.08.2026" (Tomasz zatwierdził 19.08 podział na bloki i kolejność; blok F
ma autonomię podwykonawcy bez pytania). Granica publikacyjna pochodzi z
`docs/cm/ODPOWIEDZ_do_Managera_11082026.md`, sekcja Z-5.

Wklej TO w rozmowę z CM (Telegram, agent = Content Manager). To jest BRIEF z faktami plus ramy;
CM sam dobiera kąt, słowa, kanały i proponuje slot. Tomasz zatwierdza na karcie.

---

CM, mamy materiał na build-in-public z pracy nad Tobą z 10 i 11 sierpnia. Zbuduj z tego treść.
FAKTY są prawdziwe i sprawdzalne w repozytorium. Trzymaj TRUTH_GUARD: nie dodawaj zdarzeń ani
liczb, których tu nie ma. **Zanim zaczniesz pisać, przeczytaj sekcję GRANICA niżej. Ona jest
ważniejsza od faktów.**

---

## FAKT GŁÓWNY (bohater materiału numer jeden)

**Każda warstwa kontroli treści rośnie zawsze w tę samą stronę: w stronę FORMY. I żadna z nich
nie pyta, CZYM ten tekst jest.**

- Kontrole, które narastają naturalnie, sprawdzają myślniki, zakazane słownictwo, długość,
  interpunkcję, język, meta-nagłówki. To wszystko są pytania o kształt: "czy tekst jest poprawnie
  zbudowany". Żadne z nich nie jest pytaniem o gatunek: "czy to jest w ogóle tekst dla człowieka,
  czy model mówiący o tekście".
- Notatka modelu na temat tekstu ma **formę bez zarzutu**. Nie ma em-dashy, nie ma zakazanego
  słownictwa, ma dobrą polszczyznę albo angielszczyznę, mieści się w limicie, nie zaczyna się od
  nagłówka. Przechodzi komplet kontroli, bo każda z nich pyta o coś innego.
- **Naprawa nie polegała na dopisaniu słów do czarnej listy.** Zamknięta lista fraz zawsze będzie
  o krok za modelem: dwa przypadki tej samej klasy miały dwa zupełnie różne słowniki, więc lista
  zbudowana na pierwszym nie łapała drugiego. Zmierzone, nie założone.
- **Naprawą jest BRAMKA WYJŚCIA oparta na mierze, nie na liście.** Mierzymy, jaka część różnych
  słów z wejścia przetrwała w wyjściu (słowa co najmniej czteroznakowe). Założenie jest proste
  i wynika wprost z kontraktu tych filtrów: **przeróbka zachowuje słowa oryginału, rozmowa
  o przeróbce ich nie ma.** Poniżej progu filtr oddaje tekst wejściowy nietknięty i zgłasza
  zdarzenie do dziennika z własnym typem, razem z początkiem odrzuconej odpowiedzi, żeby następna
  diagnoza nie zaczynała się od zera.
- **Liczby, które możesz podać (są o mechanizmie, nie o zdarzeniu):**

  | przypadek | pokrycie słów |
  |---|---|
  | odpowiedź modelu o zadaniu zamiast wyniku zadania | 0,023 (odrzucona) |
  | uczciwa korekta polszczyzny | 0,977 |
  | ostre przepisanie zakazanego słownictwa | 0,651 |
  | skrócenie tekstu o połowę | 0,372 |
  | próg odcięcia | 0,35 |

  Czterdziestokrotna różnica między awarią a najlepszą uczciwą przeróbką. **Uczciwie: skrócenie
  o połowę siada 0,022 nad progiem** i to jest wąskie miejsce tej miary. Żaden z tych filtrów nie
  ma prawa skracać, ale gdyby kiedyś miał, próg trzeba przeliczyć. Ten szczegół wpisz, jeśli robisz
  wersję dłuższą. On buduje wiarygodność mocniej niż sama liczba 0,023.
- **Kierunek pomyłki jest wybrany świadomie, nie przypadkiem:** fałszywy alarm kosztuje jeden tekst
  nieprzefiltrowany plus wpis w dzienniku, fałszywe przepuszczenie kosztuje tekst, który wychodzi
  do świata. Bezpiecznik ma zatrzymywać, nie poprawiać. Poprawiona notatka to nadal notatka.

**ZASADA, która jest całą wartością dla odbiorcy i ma zostać w pamięci po przeczytaniu:**

> **Każde wywołanie modelu, którego wynik wraca do potoku jako DANE, potrzebuje bramki wyjścia.
> Nie dlatego, że model bywa głuchy, tylko dlatego, że "odpowiedź o zadaniu" i "wynik zadania"
> są dla kodu nieodróżnialne. Oba są napisem.**

To dotyczy każdego, kto wpina model w środek potoku: tłumaczenie, streszczanie, klasyfikacja,
korekta, ekstrakcja. Jeśli bierzesz to, co model zwrócił, i podajesz dalej bez pytania "czy to
w ogóle jest wynik" - masz tę samą dziurę. Nie trzeba mieć naszego systemu, żeby ją mieć.

---

## DRUGI KANDYDAT NA OSOBNY MATERIAŁ (nie podwątek, własny post)

**Osiem z jedenastu anty-wzorców inżynierskich w naszej bibliotece to jedna i ta sama klasa:
cisza wygląda jak sukces.**

- Filtr, który padł, oddaje tekst niezmieniony.
- Strażnik, który zagłodził się własnym limitem, kończy przebieg z zerem.
- Pustka w widoku czytana jako fakt o świecie, a nie jako fakt o widoku.
- Bramka, która się w ogóle nie wykonała, nie zostawia po sobie śladu.
- Walidator, który zadał złe pytanie, świeci na zielono.

We wszystkich pięciu **wynik wygląda identycznie jak sukces**. Zielony przebieg wygląda tak samo
niezależnie od tego, czy kontrola sprawdziła wszystko, czy tylko to, o co potrafiła zapytać.

**Praktyczna konsekwencja i to jest cała treść dla odbiorcy:** przy każdej zmianie nie pytaj
"czy przeszło", tylko **"czy ta kontrola MIAŁA JAK zgłosić problem"** - i sprawdź to, karmiąc ją
czymś zepsutym. U nas to nie jest rytuał: 10 sierpnia jedenaście celowych przywróceń wady złapało
**trzy realne błędy w bramkach, które chwilę wcześniej świeciły na zielono**. Do 11 sierpnia takich
celowych przywróceń wady było łącznie dwadzieścia dwa.

Dwa pozostałe anty-wzorce z tej jedenastki to rodzina "naprawiłem, ale nie wszędzie" i one mają
jedną wspólną receptę: przeszukaj repozytorium, zanim uznasz poprawkę za skończoną.

Ten materiał jest szerszy i łatwiejszy do zapamiętania niż fakt główny. Jeśli widzisz sens
w kolejności odwrotnej (najpierw klasa, potem konkretna bramka wyjścia jako dowód), zaproponuj ją.
Decyzja jest Twoja.

---

## FAKTY WSPIERAJĄCE (do wyboru: wątek, krótszy post albo materiał trzeci)

**1. Pętla uczenia się z ludzkich poprawek jest wektorem wstrzyknięcia.**
Wszystko, co system zapamiętuje z korekt człowieka i wkłada z powrotem do promptu, może być
POLECENIEM zamiast preferencją. Zapamiętane regułki stylu miały kształt rozkazu ("przed spójnikiem
nie stawia się przecinka") i szły do KAŻDEJ generacji. Kiedy wyjście miało być w innym języku niż
regułki, model dostawał w jednym promptcie **dwa zadania naraz** i wykonywał to drugie. To nie jest
wada jednej funkcji, tylko właściwość każdej pętli "ucz się z poprawek". A takich pętli
w produktach opartych na modelach będzie przybywać.
Wniosek do zacytowania: **regułki stylu mają język i to jest ich część, nie metadana.** Reguła
o polskim przecinku jest bez sensu w angielskim tekście i model ma rację, pytając, o co chodzi.

**2. Bramka ma padać ZAMKNIĘTA, nie otwarta.**
Pierwsza wersja filtru pytała "czy ten wpis wygląda na polski" i odrzucała te, które wyglądały.
Test na prawdziwych danych obalił ją w pierwszym przebiegu: prawdziwa polska regułka nie miała
**ani jednego** znaku diakrytycznego i ani jednego ze słów funkcyjnych, których wzorzec szukał.
Zdanie niewidzialne dla wzorca szło dalej, czyli dokładnie tam, gdzie robi szkodę. Poprawka:
odwrócić kierunek testu. Dalej przechodzi tylko to, co **pozytywnie** rozpoznano jako właściwy
język. Nierozpoznane zostaje na zewnątrz. Cena przyjęta świadomie: czasem wypadnie wpis dobry.
Utrata preferencji stylu kosztuje odcień tekstu, przepuszczenie obcego polecenia kosztuje więcej.

**3. Dokument, który INSTRUUJE, starzeje się groźniej niż dokument, który OPISUJE.**
Nieaktualny OPIS wprowadza w błąd: czytający traci czas, potem sprawdza w kodzie. Nieaktualna
INSTRUKCJA **każe wykonać stare zachowanie** i wygląda przy tym absolutnie świeżo, bo dokument
nie ma stanu. U nas playbook instalacji przez trzy tygodnie kazał włączyć tryb pracy, który został
zabroniony po awarii, i kazał zaaplikować osiem migracji bazy, gdy było ich już czterdzieści dwie.
Świeża instalacja dostałaby jedną piątą schematu. Anty-wzorzec był zapisany, komponent poprawiony,
produkcja przełączona, a instrukcja dalej uczyła starego. Nikt nie skłamał. Po prostu nikt nie
sprawdził, czy gdzie indziej stoi zdanie rozkazujące.
Trzy recepty warte publikacji:
- instrukcja podaje **polecenie, nie liczbę zapamiętaną z przeszłości** (polecenie wypisujące listę
  migracji zamiast "001..042"), bo liczba znowu się zestarzeje, a polecenie nie;
- dokument instruktażowy nosi **datę weryfikacji, nie datę powstania**;
- najmocniejsze: **zamień warunek zapisany w dokumencie na blokadę w kodzie, gdy tylko się da.**
  Warunek w dokumencie jest założeniem, nie zabezpieczeniem.

**4. Interfejs, który tylko OTWIERA pozycje i nigdy ich nie zamyka, po tygodniach przestaje być
listą decyzji.**
Rejestr kart "czeka na Twoją decyzję" miał piętnaście otwartych pozycji. Odczyt pokazał, że
**martwych było piętnaście na piętnaście**: materiał w każdym przypadku poszedł już dalej, został
odrzucony albo opublikowany, a wpis stał nietknięty. Jedna karta wisiała czternaście dni dla
materiału opublikowanego godzinę wcześniej. Przyczyna: strażnik zakładał karty i **nic ich nigdy
nie zamykało**. Naprawa jest jednozdaniowa: zamykaj PRZED otwieraniem, wygaszając to, co straciło
przedmiot.
Wartość dla odbiorcy nie leży w liczbie, tylko w skutku: **prawdziwa, ważna pozycja tonęła wśród
fałszywych.** Po sprzątaniu wskoczyła na czwarte miejsce od góry. Lista, która zbiera śmieci,
kosztuje nie tyle bałagan, co utracone decyzje. A przeglądanie jej "na piechotę" oznacza
podejmowanie decyzji o rzeczach, które już się rozstrzygnęły.

**5. Odczyt produkcji rozstrzygał za każdym razem, czytanie kodu nie.**
Trzy diagnozy jednego problemu, dwie błędne, i każda kolejna brzmiała pewniej od poprzedniej.
Kod pozwalał na wszystkie trzy. Rozstrzygał dopiero odczyt tego, co naprawdę stoi w bazie
i w promptcie. To się w tym projekcie powtórzyło już kilka razy pod tą samą postacią: **dane
obaliły przesłankę wpisu.** Jeśli szukasz kąta na krótki post, ten jest najkrótszy do opowiedzenia.

---

## GRANICA (czego NIE wolno użyć)

**To jest instrukcja dla Ciebie, CM, a nie notatka robocza. Przeczytaj ją przed napisaniem
pierwszego zdania.**

Decyzja Managera z 11.08.2026, zapisana w `docs/cm/ODPOWIEDZ_do_Managera_11082026.md` sekcja Z-5.
Cytat z jednym świadomym opuszczeniem, wyjaśnionym pod spodem:

> "sam wyciek [datę dzienną usunięto celowo] NIE idzie do treści publicznej. Idzie lekcja
> - walidator sprawdzał formę, a nie gatunek, i naprawa nie była czarną listą słów, tylko bramką
> wyjścia i pytaniem 'czy to w ogóle jest tekst dla człowieka'."

**Dlaczego data została usunięta z tego briefu, a nie tylko zakazana niżej:** punkt 2 zakazów
zabrania podawania daty dziennej incydentu, więc wnoszenie jej do Twojego kontekstu daje zero
korzyści i niezerowe ryzyko. Do wykonania zlecenia data nie jest potrzebna ani razu. Pełny cytat
stoi w pliku źródłowym, dostępny dla człowieka, który go potrzebuje. To ta sama zasada, której
dotyczy fakt główny: nie wystarczy zakazać wyniku, trzeba odciąć drogę, którą przychodzi.

### Zakazane bezwzględnie w treści publicznej

1. **Jakakolwiek wzmianka o tym, że wadliwy tekst został opublikowany na profilu.** Ani wprost,
   ani aluzyjnie, ani jako "kiedyś nam wyszło", ani jako "zdjęliśmy post".
2. **Czas trwania publikacji, liczba wyświetleń, identyfikator publikacji, numer materiału, data
   dzienna incydentu.** Żadnej z tych liczb nie ma w tym briefie i nie wolno jej wymyślić ani
   oszacować.
3. **Dosłowna treść wyciekniętego tekstu.** Żadnego cytatu z niego, w żadnym języku, nawet
   sparafrazowanego tak, że da się go odtworzyć.
4. **Cokolwiek, co pozwala odbiorcy ustalić, że na profilu Tomasza stało coś kompromitującego.**
   To jest test nadrzędny nad punktami 1-3. Jeśli zdanie przechodzi literę zakazu, ale odbiorca
   po jego przeczytaniu ma prawo pomyśleć "aha, czyli coś im wyszło publicznie", to zdanie
   wypada.
5. **Nazwy wewnętrznych artefaktów i plików w kontekście awarii.** Mów o mechanizmie
   ("zapamiętane regułki stylu", "playbook instalacji"), nie o naszych nazwach własnych.
6. **Szczegóły awarii, po której zabroniono tamtego trybu publikacji** (fakt wspierający nr 3).
   Wystarczy "tryb zabroniony po awarii". Nie wyliczaj, co się wtedy stało.

### Jak masz o tym mówić, żeby było prawdziwie i bezpiecznie

Bohaterem jest **ZASADA i MECHANIZM**, nie zdarzenie. Wada opisana jako **właściwość klasy
systemów**, którą znaleźliśmy u siebie i zamknęliśmy, a nie jako historia wpadki. Wszystkie fakty
w tym briefie są tak sformułowane, że da się z nich napisać materiał bez ani jednego zdania
o publikacji. Jeśli w trakcie pisania poczujesz, że bez tego zdania materiał traci siłę, to znak,
że piszesz o zdarzeniu zamiast o zasadzie. Wróć do zasady. Ona jest mocniejsza i użyteczniejsza
dla czytelnika.

### Poza granicą Z-5, zakazane tak samo mocno

- **Życie prywatne.** Żadnych wątków rodzinnych, zdrowotnych, żadnych przerw w publikacji ani
  ich powodów. To nie jest materiał build-in-public i nie ma na to zgody.
- **Stan lejka i sprzedaży.** Zero liczb o prospektach, rozmowach, terminach kontaktu, wynikach
  sprzedaży. AGS jest na etapie 0-1: **nie wolno napisać ani zasugerować, że mamy płatnych
  klientów.** Żadnych nazw firm, adresów, danych osobowych.
- **Obietnice produktowe i twarda sprzedaż.** Nie zapowiadamy funkcji, nie obiecujemy wyników,
  nie podajemy cen. CTA miękki.
- Żadnej sztucznej rzadkości ("tylko cztery miejsca"), żadnych deklaracji wyników bez danych,
  żadnych odwołań do strony `/apply`.

---

## RAMY (kanon AGS)

- **Sekwencja wartości: problem, wartość dla odbiorcy, mechanizm, miękki CTA. NIGDY od ceny.**
- **Fundament przed freestylem: najpierw zasada, potem konkret.** Nie ogólniki, nie "przemyślenia
  o sztucznej inteligencji". Każde zdanie ma mieć przy sobie rzecz, która się wydarzyła, albo
  liczbę, którą ktoś zmierzył.
- **Build-in-public, etap 0-1.** Pokazujemy, JAK budujemy agentów, którym można zaufać. Nie
  pokazujemy klientów, bo ich nie ma, i nie udajemy, że są.
- **Głos AGS: bezpośredni, ale ciepły. Pierwsza osoba. Krótkie zdania uderzają, potem jedno dłuższe
  dla głębi. Liczby są kotwicami.** Czytelnik ma pomyśleć "ten człowiek jest prawdziwy", a nie
  "ten człowiek jest imponujący".
- **Zero em-dashy. Zawsze.** To jest reguła numer jeden kanonu.
- **Zero AI-slopu i zakazanego słownictwa** ("unlock your potential", "game-changer", "leverage",
  "synergy", "disrupt", "thought leader", "ecosystem", "optimize", ogólnikowe otwarcia w rodzaju
  "in today's fast-paced AI landscape").
- **Test mamy dla wersji polskiej: czysta polszczyzna, zero anglicyzmów.** Zdanie ma brzmieć tak,
  jakby powiedział je człowiek, a nie tłumacz.
- **Grafiki: TYLKO PROMPT, zero automatycznych obrazów.** Jeśli widzisz sens w wizualu, opisz go
  jako **szczegółowy prompt do wykonania** (kompozycja, paleta z kanonu, typografia, co dokładnie
  ma być na obrazie). Nigdy nie generuj i nie załączaj gotowego obrazu. Reguły wizualne z kanonu:
  zero fotografii stockowej, zero gradientów korporacyjnych, zero palety cyjan-fiolet-róż, zero
  twarzy i dłoni z generatora. Diagram albo zrzut prawdziwego ekranu są dozwolone, o ile pokazują
  coś, co naprawdę istnieje.
- **Języki: zaproponuj podział PL i EN sam.** Nie narzucam. Uzasadnij wybór celem kanału, nie
  przyzwyczajeniem.

---

## CZEGO OCZEKUJĘ

1. **Zaproponuj materiał albo materiały narzędziem `propose_material`.** Bohaterem numer jeden jest
   zasada bramki wyjścia: "odpowiedź o zadaniu i wynik zadania są dla kodu nieodróżnialne".
   Drugi kandydat, "cisza wygląda jak sukces", zasługuje na własny materiał, nie na podwątek.
   Jeśli uważasz, że kolejność powinna być odwrotna, powiedz to wprost i uzasadnij.
2. **Zaproponuj kanały plus slot** według okien i kadencji. Jeśli widzisz sens w wersji PL i EN,
   podaj obie z uzasadnieniem.
3. **Jeśli masz pomysł na wizual, dopisz go jako szczegółowy PROMPT**, nie jako obraz. Tylko taki,
   który da się wykonać uczciwie.
4. **Przed zaproponowaniem karty przejdź swój tekst przez sekcję GRANICA, zdanie po zdaniu.**
   Jeśli któreś zdanie pozwala odbiorcy domyślić się zdarzenia zamiast zasady, przepisz je albo
   usuń. Zgłoś mi, jeśli uznasz, że granica odbiera materiałowi siłę: to też jest informacja
   i wolę ją dostać przed publikacją niż po.

Czekam na kartę do zatwierdzenia.
