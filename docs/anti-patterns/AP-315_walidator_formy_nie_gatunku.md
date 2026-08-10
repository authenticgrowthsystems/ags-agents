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

## Realizacja u nas

- `compliance.bezpiecznik_gatunku` - dwie listy, zwraca `(twarde, miekkie)`
- `channels.sprawdz_gatunek` - czyta wiersze kolejki + odcisk tresci
- `worker.process_item` - bramka przed `handed_off`, znacznik w `media` materialu
- `cm-agent/tests/test_bezpiecznik_gatunku.py` - szesc scenariuszy przez prawdziwa petle,
  karmione tekstem, ktory naprawde wyszedl 04/08

Wyciek z 04/08 lapie sie na frazie **twardej** (`Voice Bible`), wiec zaden podwojny tap
go nie wypusci - i to jest asercja w tescie, nie deklaracja.
