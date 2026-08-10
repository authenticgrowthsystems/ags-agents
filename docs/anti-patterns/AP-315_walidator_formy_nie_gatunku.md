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

## DRUGA TURA TEGO SAMEGO DNIA - przyczyna zrodlowa znaleziona

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
