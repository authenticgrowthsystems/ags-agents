# AP-315: Walidator sprawdza FORME tekstu, a nie jego GATUNEK

**Ustanowiony 10/08/2026 (Manager AGS, po szesciu dniach zywej publikacji).**
Rodzina AP-312 od strony TRESCI: tam nazwa stanu obiecuje co innego, niz znaczy;
tu **tekst przechodzi wszystkie kontrole, bo kazda z nich pyta o jego ksztalt,
a zadna o to, czym on jest**.

## Wzorzec

Warstwa kontroli tresci rosnie naturalnie i zawsze w te sama strone: myslniki, zakazane
slownictwo, dlugosc, interpunkcja, jezyk, meta-naglowki. Wszystko to sa pytania o FORME -
"czy tekst jest poprawnie zbudowany". Zaden z nich nie jest pytaniem o GATUNEK - "czy to
jest w ogole tekst dla czlowieka, czy model mowiacy o tekscie".

Notatka recenzyjna modelu ma **bez zarzutu poprawna forme**. Nie ma em-dashow, nie ma
zakazanego slownictwa, ma dobra polszczyzne albo angielszczyzne, miesci sie w limicie,
nie zaczyna sie od naglowka. Przechodzi wszystko, bo wszystko pyta o cos innego.

## Dowod: post LinkedIn z 04/08/2026

Material `#344`, zatwierdzony guzikiem 03/08 wieczorem, opublikowany 04/08 o 16:01,
zdjety recznie 10/08. **Szesc dni na profilu, 87 wyswietlen, pod nazwiskiem Tomasza.**
Trescia posta bylo:

> "I've reviewed the canonical text and Voice Bible. This is a technical article about
> agent responsibility separation, strong content. However, I need to flag an issue before..."

To jest CM mowiacy do operatora o materiale. Poszlo w swiat jako wypowiedz autora, razem
z nazwa wewnetrznego artefaktu (Voice Bible).

### Cztery kontrole, kazda zadala wlasciwe pytanie i kazda przepuscila

| kontrola | o co pytala | dlaczego przepuscila |
|---|---|---|
| `compliance.strip_meta_header` | czy pierwsze linie maja KSZTALT naglowka ("## Wersja LinkedIn:", "Oto post:") | tekst byl proza, zaden wzorzec ksztaltu go nie dotknal |
| `compliance.enforce` | myslniki, zakazane slownictwo, czysta polszczyzna, linia re-intro | wszystkie odpowiedzi byly poprawne |
| bramka zatwierdzenia (HITL) | **"czy zatwierdzone"** | bylo zatwierdzone - tapniete odruchowo |
| raportowanie Managera | **"czy kolejka jest pusta"** | byla pusta, bo material wyszedl |

**Zadna z nich nie zadala pytania "czy to jest tekst dla czlowieka".** Sformulowanie Managera
z dnia ustanowienia: **to projekt, nie wypadek** - cztery niezalezne warstwy pytaly o stan
i o forme, bo o to latwo zapytac, a o gatunek trzeba zapytac swiadomie.

### Warstwa piata: ten sam blad w odczycie diagnostycznym

Tekst wycieku byl widoczny w `stan_gry` **rano 04/08, przed publikacja**, w linii kolejki
LinkedIn - w sesji, ktora tego dnia sprawdzala D-008. Sesja czytala STATUS wiersza
(`zatwierdzone, czeka na start`) i nie przeczytala TRESCI, ktora stala obok w tej samej
linii. Ten sam odruch: pytanie o stan zamiast pytania o zawartosc.

## Why bad

- **Wada jest niewidzialna z zewnatrz.** Zielony przebieg walidatora wyglada identycznie
  niezaleznie od tego, czy sprawdzil wszystko, czy tylko to, o co potrafil zapytac.
- **Koszt jest publiczny i nieodwracalny w czasie.** Nie ma "cofniecia" szesciu dni
  na profilu; jest tylko usuniecie posta i luka w ksiedze publikacji.
- **Rosnie z liczba warstw.** Kazda nowa kontrola formy zwieksza poczucie bezpieczenstwa,
  nie zmniejszajac ryzyka gatunkowego ani o krok.
- **Bramka ludzka NIE jest tu zabezpieczeniem.** Zatwierdzanie odruchowe to normalny tryb
  pracy operatora, ktory zatwierdza kilkanascie kart tygodniowo. Projektowanie pod zalozenie,
  ze czlowiek czyta uwaznie za kazdym razem, to ta sama klasa co AP-314.

## Correct

1. **Dolóż kontrole GATUNKU osobno od kontroli formy** i postaw ja na ostatniej bramce przed
   swiatem - u nas `worker.process_item` przed zapisem `handed_off`, bo tamtedy przechodzi
   takze material zatwierdzony guzikiem w n8n, z pominieciem cm-agenta.
2. **Sprawdzaj DOKLADNIE ten tekst, ktory wyjdzie** - wiersz kolejki, nie `canonical_body`.
   Wariant bywa inny niz canonical, a publikuje sie wariant.
3. **Bezpiecznik ma zatrzymywac, nie poprawiac.** Poprawiona notatka to nadal notatka.
4. **Podziel liste na TWARDA i MIEKKA wedlug jednego kryterium: czy slowo ma sensowne uzycie
   POZA nasza maszyneria.** `Voice Bible`, `masterprompt`, `stan_gry`, `matreview` - nie ma.
   `kolejka`, `meldunek`, `canonical` - ma, i to codzienne (TNM pisze po polsku do uslug
   lokalnych, gdzie "kolejka klientow" i "stac w kolejce" sa naturalne). **Twarda blokada na
   zwyklym slowie odpali raz, w najgorszym momencie, i bedzie wygladac jak zepsuty system** -
   czyli sam bezpiecznik stanie sie AP-312.
5. **Furtke wiaz z TRESCIA, nie z fraza.** Drugie zatwierdzenie przepuszcza DOKLADNIE ten sam
   tekst, ktory czlowiek widzial w meldunku razem z nazwa frazy - dzieki temu drugie tapniecie
   jest swiadome, a nie slepe. Tekst przepisany jest nowym tekstem i zatrzymuje sie od nowa.
6. **Meldunek o zatrzymaniu musi nazywac FRAZE.** "Cos jest nie tak" odtwarza odruch;
   konkretna fraza go przerywa.
7. **Przy diagnozie czytaj TRESC, nie tylko status.** Status odpowiada na pytanie "gdzie to
   jest", nie "co to jest".

## DRUGA TURA TEGO SAMEGO DNIA - hipoteza, ktora upadla kilka godzin pozniej

> **UWAGA, CZYTAJ RAZEM Z CZWARTA TURA NIZEJ.** Ta sekcja opisuje `_rewrite` jako przyczyne
> zrodlowa. **To bylo bledne** i zostaje tu swiadomie, zeby bylo widac, jak pewnie brzmiala
> hipoteza, ktora nie byla prawdziwa. Bramka wyjscia w `_rewrite` zamyka realna dziure i zostaje
> w kodzie - ale w ZADNYM z dwoch znanych wyciekow nie byla sprawca. Prawdziwa przyczyna jest
> w sekcji "CZWARTA TURA".


Kilka godzin po wdrozeniu bezpiecznika przyszla karta materialu "Granica miedzy dwoma agentami"
z wariantem LinkedIn o tresci:

> "Rozumiem Twoja prosbe, ale widze niejasnosc: **nie podales mi tekstu do poprawy**. (...)
> Przeslij go, a otrzymasz zwrotnie **wylacznie poprawiony tekst** (zero komentarzy, zero em
> dashy, zero angielskich kalk)."

Trzy ostatnie sformulowania to **doslowne echo promptu `compliance.polish_pl`**. Model nie
poprawil tekstu - odpowiedzial O tekscie. A `_rewrite` oddawal to dalej jako tresc posta:

```python
out = "".join(b.text for b in resp.content if ...).strip()
return out or text          # <- zadnego sprawdzenia, czy to przerobka
```

**To jest kanal, ktorym niemal na pewno wyszla takze publikacja z 04/08.** `_rewrite` obsluguje
trzy filtry (`polish_pl`, przepisanie zakazanego slownictwa, test szatni) i kazdy z nich potrafil
w ten sposob podmienic tresc posta na wypowiedz modelu o poscie. Ironia jest kompletna: funkcja
ma starannie zrobiona obsluge przypadku, w ktorym filtr **padnie** (AP-306, wpis do `agent_logs`,
zeby cisza nie wygladala jak sukces) - i zadnej obslugi przypadku, w ktorym filtr **odpowie**.

### Lista fraz NIE zlapala tej awarii. Zmierzone, nie zalozone

`bezpiecznik_gatunku` na tym tekscie zwrocil **`([], [])`** - zero trafien na obu listach.
Inna awaria tego samego rodzaju, o zupelnie innym slownictwie: nie "I've reviewed", tylko
"Potrzebuje od Ciebie" i "Przeslij go". **Zamknieta lista zawsze bedzie o krok za modelem.**

### Naprawa strukturalna: BRAMKA WYJSCIA na pokryciu slow

Zamiast dopisywac frazy - zmierzyc co innego, czego nowe slownictwo nie omija:
**przerobka zachowuje slowa oryginalu, rozmowa o przerobce ich nie ma.**

`pokrycie_slow(wejscie, wyjscie)` liczy, jaka czesc roznych slow wejscia (min. 4 znaki, zlozone
do ASCII wg AP-313) przetrwala w wyjsciu. Ponizej progu `0.35` filtr **oddaje tekst wejsciowy
nietkniety** i zglasza zdarzenie do `agent_logs` z wlasnym typem `COMPLIANCE_ODPOWIEDZ_NIE_PRZEROBKA`,
razem z poczatkiem odrzuconej odpowiedzi - inaczej diagnoza nastepnym razem zaczyna sie od zera.

To nie jest heurystyka, tylko **kontrakt tych filtrow**: kazdy z trzech promptow obiecuje
zachowanie sensu i dlugosci ("NIE zmieniaj sensu, tonu ani dlugosci", "keeping the meaning
and voice"). Zmierzona separacja na prawdziwych danych:

| przypadek | pokrycie |
|---|---|
| **rozmowa modelu (prawdziwa karta 10/08)** | **0.023 - odrzucona** |
| korekta polszczyzny | 0.977 |
| ostre przepisanie zakazanego slownictwa | 0.651 |
| skrocenie tekstu o polowe | 0.372 |

Czterdziestokrotna roznica miedzy awaria a najlepsza uczciwa przerobka. **Uczciwie: skrocenie
o polowe siada 0.022 nad progiem** - zaden z trzech filtrow nie ma prawa skracac, ale gdyby
kiedys mial, prog trzeba przeliczyc. Kierunek pomylki jest tu swiadomie wybrany: falszywy alarm
kosztuje jeden tekst nieprzefiltrowany plus wpis w logu, falszywe przepuszczenie kosztuje
publiczny post.

**Zasada ogolniejsza, warta wiecej niz sama poprawka:** kazde wywolanie modelu, ktorego wynik
wraca do potoku jako DANE, potrzebuje bramki wyjscia. Nie dlatego, ze model bywa gluchy, tylko
dlatego, ze "odpowiedz o zadaniu" i "wynik zadania" sa dla kodu nieodroznialne - oba sa napisem.

## TRZECIA TURA: audyt wstecz obalil moja wlasna liste twardych

Audyt 152 publikacji z czterech miesiecy odpowiedzial na pytanie "co jeszcze wyszlo tym kanalem":
**nic**. Wyciek z 04/08 jest jedyna znana podmiana tresci na wypowiedz modelu. Ale przy okazji
znalazl cos, czego nie szukal.

Fraza `voice bible` stala na TWARDEJ liscie jako pewniak - "nazwa naszego pliku, nie pojawi sie
w prawdziwym tekscie dla czlowieka". Audyt znalazl ja w **opublikowanym poscie Tomasza z 11/07**:

> "One person, one agent, 12 posts this week. The secret isn't smarter AI. It's architecture:
> clear stages, compliance checks, **one voice bible**. Responsibility stays human."

Mala litera, z rodzajnikiem, w szeregu z dwoma innymi pojeciami warsztatowymi. To pojecie
content-ops, nie nazwa naszego pliku. Twarda blokada znaczy brak furtki - czyli ten post,
napisany dzis, bylby **nie do opublikowania**. Dokladnie ten tryb awarii, ktory Manager
przewidzial przy `kolejce`, tyle ze trafil we fraze, co do ktorej bylem najbardziej pewny.

**Kryterium sie nie zmienilo, zmienil sie stan wiedzy: korpus obalil przeslanke wpisu** - tak samo
jak odczyt obalil przeslanke przy D-011 i przy migracji D-008. To juz trzeci raz w tym projekcie.

### Czego to nie wolno bylo zepsuc

Samo przeniesienie `voice bible` do miekkich rozbroilo obrone przed wyciekiem z 04/08 - to
wlasnie ta fraza dawala mu twardosc. Liczby pokazaly jednak, gdzie naprawde lezy granica:

| tekst | frazy twarde | frazy miekkie |
|---|---|---|
| wyciek 04/08 | 0 | **5** (voice bible, canonical, i've reviewed, i need to flag, strong content) |
| dobry post 11/07 | 0 | **1** (voice bible) |

Jedna fraza miekka to prawdopodobnie swiadomy wybor slowa. **Piec to nie zbieg okolicznosci,
tylko gatunek.** Stad `PROG_MIEKKICH_JAK_TWARDE = 3` i funkcja `compliance.bez_furtki`: trafienie
traci furtke przez fraze twarda **albo** przez nagromadzenie miekkich. To licznik, a nie kolejne
slowo na liscie - zmiana slownictwa go nie omija.

Prog przepuszczony przez CALY korpus PRZED wdrozeniem: **152 publikacje, `BEZ FURTKI: 0`**,
jedyne trafienie to post z 11/07 z jedna fraza i zachowana furtka. Bramka, ktorej nie widzialo
sie na prawdziwych danych, jest zalozeniem (AP-314).

## CZWARTA TURA: PRAWDZIWA przyczyna - polska instrukcja w angielskim promptcie

Odczyt produkcji zamknal sprawe. `brand_config.style_learned` dla AGS zawiera szesc regulek
wydestylowanych z RECZNYCH korekt Tomasza. Wszystkie sa **po polsku** i wszystkie maja ksztalt
**polecenia**:

> - Zamiast "Trzeba zaprojektowac" pisze "To wymaga konkretnej pracy. Trzeba zaprojektowac"
> - Zamiast "kiedy cos nie zadziala, i kto" pisze "kiedy cos nie zadziala i kto"
> - **Przed spojnikiem "i" nie stawia sie przecinka.**

`generate._learned_style` doklada ten blok do **KAZDEJ** generacji - i do wariantu per kanal,
i do tekstu-matki. Kanal LinkedIn publikuje po angielsku. Model dostaje wiec prompt zlozony z:
polecenia "napisz post po angielsku" **oraz** polskiej listy instrukcji o poprawianiu polszczyzny.
To sa dwa zadania. Model wykonuje drugie.

Trzy pozostale bloki wstrzykiwane obok (`rules[]`, `voice_note`, `learning_digest`) sa **puste** -
caly ladunek szedl stad.

### Zgodnosc ze spisem, ktory model sam zrobil

| model powiedzial, ze dostal | to jest |
|---|---|
| "Instrukcja, jak mam poprawiac polski" | regula przecinka + szesc par *Zamiast X pisze Y* |
| "Moja analiza jakiegos polskiego tekstu (ktory sam sobie wymyslilem)" | cytaty w tych parach, bez tekstu zrodlowego |
| "Pytanie o angielski/polski do LinkedIna" | `lang_guide` |

### Dowod, ze `_rewrite` NIE mogl byc sprawca

Tekst z 04/08 zaczyna sie od **"I've reviewed the canonical text and Voice Bible"**. Voice Bible
wchodzi do wywolania przez `system_blocks(brand)`. **`compliance._rewrite` nie przekazuje bloku
systemowego w ogole** - ma wylacznie `messages=[...]`. Model wolany przez `_rewrite` fizycznie
nie widzi Voice Bible i nie moglby o niej napisac. Oba wycieki wyszly ta sama droga:
`generate_variant` z zanieczyszczonym promptem. Oba teksty to model **wyliczajacy, co dostal**.

### Naprawa: regulki wchodza tylko w jezyku wyjscia

`_learned_style(brand_id, jezyk)` i `_learning_digest(brand_id, jezyk)`. Jezyk wariantu jest znany
dokladnie (`_language_publish` per kanal); tekst-matka nie ma kanalu, wiec bierze dominujacy jezyk
publikacji marki (`_jezyk_marki`). Jezyk wpisu czytamy Z NIEGO SAMEGO - bez DDL, bez uzupelniania
kolumny wstecz, dziala na danych, ktore juz leza w bazie.

### Kierunek testu jezyka jest NIEsymetryczny i to jest cala pointa

Pierwsza wersja filtrowala przez `not compliance.looks_polish(...)`. Test na PRAWDZIWYCH
regulkach ja obalil w pierwszym przebiegu:

> `Zamiast "poprawiania promptu o jedno zdanie" pisze "iteracyjnego poprawiania" (bardziej precyzyjnie)`

Ta regulka nie ma **ani jednego** polskiego znaku diakrytycznego i ani jednego z szesciu slow
funkcyjnych, ktorych szuka `looks_polish`. Polskie zdanie niewidzialne dla wzorca opartego
na ogonkach - **rodzina AP-313**. Bramka padala OTWARTA: wpis nierozpoznany szedl do promptu
angielskiego, czyli dokladnie tam, gdzie robi szkode.

Stad `_wyglada_na_angielski`: **POZYTYWNY** test angielszczyzny, uzywany jednokierunkowo.
Do promptu EN wchodzi tylko wpis, ktory wyglada na angielski; nierozpoznany zostaje na zewnatrz.
Cena przyjeta swiadomie: krotka angielska regulka bez slow funkcyjnych tez wypadnie. Utrata
preferencji stylu kosztuje odcien tekstu, przeciek polskiego polecenia kosztuje publiczny post -
i kosztowal juz dwa razy.

**Docelowo wpisy powinny dostawac jezyk PRZY ZAPISIE.** Wtedy zgadywanie znika. Do tego czasu
zgadujemy w bezpieczna strone i to jest zapisane w kodzie, a nie domyslne.

### Wnioski poza sama poprawka

1. **Petla uczenia sie jest wektorem wstrzykniecia.** Wszystko, co system zapamietuje z korekt
   czlowieka i wklada z powrotem do promptu, moze byc POLECENIEM zamiast preferencja. To nie jest
   wada tej jednej funkcji, tylko wlasciwosc kazdej petli "ucz sie z poprawek".
2. **Regulki stylu maja jezyk i to jest ich czesc, nie metadana.** Regula o przecinku przed "i"
   jest bez sensu w angielskim tekscie i model ma racje, pytajac, o co chodzi.
3. **Trzy diagnozy tego samego dnia, dwie bledne.** Kolejno: bezpiecznik gatunku (nie zlapal),
   `_rewrite` (nie mial dostepu do Voice Bible), dopiero `_learned_style`. Kazda kolejna byla
   pewniejsza od poprzedniej i dwie pierwsze byly falszywe. **Odczyt produkcji rozstrzygnal
   za kazdym razem** - kod pozwalal na wszystkie trzy.

## Realizacja u nas

**Warstwa 1 - bramka wyjscia filtra (przyczyna zrodlowa):**

- `compliance.pokrycie_slow` + `PROG_POKRYCIA_FILTRA` - miara, nie lista
- `compliance._rewrite` - przy pokryciu ponizej progu oddaje WEJSCIE i zglasza
- `compliance._zglos_nie_przerobke` - `agent_logs`, typ `COMPLIANCE_ODPOWIEDZ_NIE_PRZEROBKA`
- `cm-agent/tests/test_bramka_wyjscia_filtra.py` - prawdziwa odpowiedz-rozmowa z karty 10/08
  kontra cztery uczciwe przerobki, obie strony progu

**Warstwa 2 - bezpiecznik gatunku (ostatnia siatka przed swiatem):**

- `compliance.bezpiecznik_gatunku` - dwie listy, zwraca `(twarde, miekkie)`
- `channels.sprawdz_gatunek` - czyta wiersze kolejki + odcisk tresci
- `worker.process_item` - bramka przed `handed_off`, znacznik w `media` materialu
- `cm-agent/tests/test_bezpiecznik_gatunku.py` - szesc scenariuszy przez prawdziwa petle,
  karmione tekstem, ktory naprawde wyszedl 04/08

Wyciek z 04/08 lapie sie na frazie **twardej** (`Voice Bible`), wiec zaden podwojny tap
go nie wypusci - i to jest asercja w tescie, nie deklaracja. Karta z 10/08 nie lapie sie
na ZADNEJ frazie i zatrzymuje ja dopiero warstwa 1 - stad kolejnosc warstw w tej liscie.
