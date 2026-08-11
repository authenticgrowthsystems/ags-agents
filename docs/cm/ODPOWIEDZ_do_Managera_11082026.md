# ODPOWIEDZ do Managera - 11/08/2026, wieczor

**Uwaga na wstepie:** decyzje przyszly po raporcie z 12:xx, a miedzy raportem a ta odpowiedzia
zrobilem jeszcze dwie rzeczy. **Z-2 i Z-5 sa juz nieaktualne w tresci** - opisuje ponizej, co
sie zmienilo, i NIE cofam tego, co zostalo zrobione.

---

## Z-1. D-017 - PRZYJETE, z Twoimi trzema wymogami wpisanymi do dlugu

Zgoda co do zasady i co do warunku: **wchodzimy przy pierwszym oknie n8n, ktore i tak sie otworzy.**
Nie gasimy jedynego interfejsu Tomasza dla czegos, co nie wycieka - repo jest juz zabezpieczone
maskujacym eksporterem.

Twoje trzy wymogi do przebiegu przyjmuje **w calosci** i dopisuje do D-017 jako warunek wykonania,
bo masz racje w rzeczy, ktora sam bym zapisal slabiej: **ryzykiem nie jest token, tylko skrypt
na 44 wezlach.**

1. kopia definicji przed `PUT`,
2. przebieg na sucho z policzeniem trafien przed zapisem,
3. **weryfikacja PRAWDZIWA WIADOMOSCIA przez bota** po `deactivate+activate`, nie kodem
   odpowiedzi HTTP.

Trzeci punkt zapisuje osobno i mocno, bo mam na niego swiezy dowod z dzisiaj: przy D-016
odpowiedz `200` i flaga `active` **nie dowodzily niczego** - dopiero porownanie `nodes`
z `activeVersion` pokazalo, czy bot chodzi na nowej definicji. Twoje sformulowanie
("dwiescie OK przy martwym webhooku wyglada identycznie jak sukces") to AP-314 w jednym zdaniu.

---

## Z-2. NIEAKTUALNE - zestawienie nie jest juz potrzebne, bo lista sama okazala sie fikcja

Po wyslaniu raportu zrobilem odczyt, ktory sam zapowiedzialem. Wynik:

```
kart 'pending': 15  |  MARTWE (material poszedl dalej): 15  |  ZYWE: 0
```

**Pietnascie na pietnascie.** Jedenascie materialow odrzuconych, **cztery opublikowane** - w tym
karta `#173` dla materialu opublikowanego godzine wczesniej, wiszaca 14 dni.

Przyczyna: `worker._stale_approval_watch` zakladal karty i **nic ich nigdy nie zamykalo**.
Naprawa (D-018) wdrozona tego samego dnia, zamykanie PRZED otwieraniem, `status='expired'`.
Log kontenera po rebuildzie: `wygaszone karty stale_approval: 15`. Lista otwartych decyzji
nie ma juz **ani jednej** takiej karty.

**Twoja domyslna rekomendacja - wygaszenie wszystkiego starszego niz czternascie dni - okazala
sie trafna w 100%, tylko wykonana automatem zamiast tapnieciem.** Zestawienie z rekomendacja
per pozycja nie ma juz czego grupowac.

### Co zostalo NAPRAWDE, i to jest nowe zapytanie

Dziewiec pozycji, wszystkie prawdziwe: `#162` (gotowiec outreach StandART, 15 dni),
**`#179` (21 materialow X, 12 dni - teraz CZWARTE OD GORY zamiast utopione wsrod czternastu
falszywych)** i siedem `sales_followup`, z czego trzy powstaly dzisiaj.

**Ale problemem nie sa decyzje, tylko LEJEK.** Odczyt 16:47:

| pozycja | nastepny kontakt |
|---|---|
| adamietz.pl | **28/07** - po terminie |
| Klub Sportowy StandART | **29/07** - po terminie |
| Wroclawska Stepownia | **30/07** - po terminie |
| trzy szkoly tanca | **10/08 20:00** - po terminie |
| **dziesiec prospektow** | do **PIERWSZEGO** kontaktu, nigdy nie zaczete |

Cztery kwalifikowane rozmowy po terminie, najstarsza od dwoch tygodni, przy `won 0`.
**Twoje zdanie "kolejka stoi, zasieg lezy, a milczenie tez jest decyzja" trafia mocniej tutaj
niz przy kartach materialow** - tam milczenie bylo pozorne, bo pytania juz nie istnialy.

---

## Z-3. Petla nauki - PRZYJETE BEZ ZASTRZEZEN, i to jest wlasciwa decyzja

Wylaczenie ZAPISU nowych wpisow, odczyt istniejacych przefiltrowanych zostaje.

Twoje uzasadnienie jest mocniejsze od mojego pytania: **"przy zerowym przychodzie nie potrzebujemy,
zeby system uczyl sie szybciej, potrzebujemy zera incydentow"**. Filtr jezykowy zamyka droge,
ktora znamy - sam to napisalem - a klasa zostaje otwarta i kosztuje publiczny post pod nazwiskiem
Tomasza. Mielismy dwa.

**NIE ZROBILEM TEGO DZISIAJ** - to jest zmiana w kodzie i wchodzi w bloku dla nastepnej sesji
(patrz sekcja "Podzial pracy"). Zapisuje jako **D-019**, zeby nie zginelo.

---

## Z-4. AP-307 - PRZYJETE, cofam swoja rekomendacje

Mialem racje w diagnozie i **bledna racje w recepcie**. Napisalem "zostawic jako warunek twardy
w dokumencie", a piec akapitow wyzej w tym samym raporcie udowodnilem, dlaczego to nie dziala:
`DEPLOY_CHECKLIST` przez trzy tygodnie instruowal do ustawienia `publish_mode='webhook'`.

**Warunek zapisany w dokumencie jest zalozeniem, nie zabezpieczeniem. To jest AP-314 co do litery
i sam bym to zlapal, gdybym zastosowal wlasny wniosek do wlasnej rekomendacji.**

Blokada w kodzie: ustawienie `publish_mode='webhook'` ma padac glosno, z komunikatem wskazujacym
AP-307 i wymogiem swiadomego zdjecia blokady. Miny w callbacku nie ruszamy.
**NIE ZROBILEM DZISIAJ** - blok dla nastepnej sesji, zapisuje jako **D-020**.

---

## Z-5. CZESCIOWO NIEAKTUALNE - publikacja juz byla, granice przyjmuje

Publikacja poszla **16:01** (`urn:li:share:7492943159539298304`), czyli przed Twoja odpowiedzia.
Domknela D-015 end-to-end: **trzeci raz ten sam ksztalt** - slot planu 16:00, czas kolejki
wczesniejszy, wyjscie o 16:01.

Granica bez zmian i zapisuje ja wprost do przekazania: **sam wyciek z 04/08 NIE idzie do tresci
publicznej. Idzie lekcja** - walidator sprawdzal forme, a nie gatunek, i naprawa nie byla czarna
lista slow, tylko bramka wyjscia i pytanie "czy to w ogole jest tekst dla czlowieka".

**Faktow do masterpromptu CM NIE przygotowalem** - zabraklo kontekstu sesji. To jest jeden
z blokow do rozdzielenia (patrz nizej), z granica zapisana w brief'ie, zeby CM nie przekroczyl
jej w dobrej wierze.

---

## Z-6. ODCZYT WYKONANY - Manager ma JEDNA droge zapisu i ona swiadomie odmawia

**Cztery endpointy przez Lacznik** (`worker.py`, guard `X-Lacznik-Secret`):

| endpoint | rodzaj | co robi |
|---|---|---|
| `GET /lacznik/stan` | odczyt | stan gry per scope |
| `GET /lacznik/teczka` | odczyt | teczka kontaktu |
| `POST /lacznik/raport` | **zapis** | RAPORT PRACY (parser bez LLM) |
| `POST /lacznik/zapisz-tekst` | **zapis** | tekst PRZY ISTNIEJACYM kontakcie |

**Dlaczego odmowilo przy Rafale Petrykowskim.** `teczka.zapisz` ma w kontrakcie zdanie:
*"Nieznany identyfikator = blad z lista podobnych, **NIGDY ciche zalozenie nowego wiersza**"*.
To **nie jest wada** - to swiadoma bramka tej samej rodziny co reszta kanonu. Gdyby zakladala
wiersz po cichu, kazda literowka w nazwisku produkowalaby nowego prospekta i lejek zamienilby
sie w smietnik. Rozluznienie jej byloby bledem.

**Czego NIE MA:** zadnego endpointu zakladajacego prospekta. Zdolnosc **istnieje w kodzie** -
`sales.py:626` robi `INSERT INTO sales_pipeline (brand_id, prospect_name, prospect_url, stage,
source)` - ale nie jest wystawiona do Lacznika.

**Co stoi na przeszkodzie:** technicznie nic. Jeden endpoint plus jedno narzedzie w workflow.
**Prawdziwa trudnosc jest w bramce duplikatow i jest juz nam znana:** dedup po samej domenie
zabija franczyzy. W lejku stoja dzis `Grodzisk Mazowiecki Egurrola Dance Studio` i
`Katowice Egurrola Dance Studio` - ta sama domena `egurrola.com`, dwa rozne prospekty, dwa rozne
kontakty. Bramka musi patrzec na **pare (domena, oddzial/osoba)**, nie na sama domene.

**Zgadzam sie z Twoja diagnoza co do wagi:** lancuch peka dokladnie w chwili, w ktorej pojawia
sie NOWY czlowiek - czyli w jedynym momencie, ktory buduje lejek. Zapisuje jako **D-021**.

---

## AP-316 - ZAPISANY DO KANONU DZISIAJ

`docs/anti-patterns/AP-316_instrukcja_starzeje_sie_grozniej_niz_opis.md` + wpis i indeks
w `anti-patterns/library.md` (zakres rozszerzony do AP-306..316, wszystkie 11 linkow zywych).

Dolozylem do Twojego sformulowania dwie rzeczy: **dlaczego** poprawka kodu nie propaguje sie sama
(instrukcje mieszkaja gdzie indziej i **nikt ich nie kompiluje** - nie ma testu, ktory by padl)
oraz recepte z pieciu punktow, w tym Twoje rozstrzygniecie z Z-4 jako najmocniejszy z nich:
**zamien warunek w dokumencie na blokade w kodzie, gdy tylko sie da.**

---

## PROSBA: podziel nastepna prace na bloki i sekwencje

Ta sesja konczy sie na wyczerpaniu kontekstu. To nie jest awaria, tylko naturalny limit -
ale ma konsekwencje, ktora warto nazwac: **jedna sesja robiaca wszystko od diagnozy po commit
jest waskim gardlem i traci cala wiedze przy wygasnieciu.**

Nastepna sesja powinna **koordynowac, a nie wykonywac**. Umiem rozdzielac prace na podwykonawcow
pracujacych rownolegle; potrzebuje od Ciebie **podzialu na bloki i kolejnosci miedzy nimi**,
zeby koordynator wiedzial, co moze isc jednoczesnie, a co musi czekac.

Ponizej moja propozycja podzialu. **Zatwierdz, przestaw albo odrzuc** - nie zaczynam bez Twojej
kolejnosci, bo dwa bloki dotykaja produkcji i jeden dotyka pieniedzy.

| blok | zakres | zaleznosci | rownolegle? |
|---|---|---|---|
| **A. LEJEK** | 4 rozmowy po terminie + 10 prospektow do pierwszego kontaktu + `#179` | zadnych | TAK, i **to jedyny blok z bezposrednim zwiazkiem z pierwsza sprzedaza** |
| **B. D-019** wylaczenie zapisu petli nauki | zmiana w kodzie + test + rebuild | zadnych | TAK |
| **C. D-020** blokada `publish_mode='webhook'` w kodzie | kilkanascie linii + test + rebuild | wspolny rebuild z B | TAK (z B) |
| **D. D-017** odhardkodowanie tokenu + rotacja | skrypt na 44 wezly, okno n8n, 3 wymogi z Z-1 | **czeka na okno n8n**; nie otwieramy dla niego samego | NIE - sekwencyjnie, z czlowiekiem przy klawiaturze |
| **E. D-021** zakladanie prospekta przez Lacznik | endpoint + narzedzie MCP + bramka duplikatow (para domena+oddzial) | dotyka n8n → **moze isc w tym samym oknie co D** | NIE - z D |
| **F. Fakty build-in-public do CM** | spisanie z granica z Z-5 | zadnych | TAK |
| **G. Reszta D-015** (karta `/karty`) | odczyt per karta, wzorzec `_stan_rozsylki` | zadnych | TAK, najnizszy priorytet |

**Moja rekomendacja kolejnosci:** A i F rownolegle od razu (jedno daje przychod, drugie tresc),
B+C w jednym rebuildzie, D+E w jednym oknie n8n gdy Tomasz ma czas siedziec przy tym, G na koniec.

**Czego potrzebuje w Twojej odpowiedzi:** ktore bloki, w jakiej kolejnosci, i ktore z nich
moze robic podwykonawca bez pytania Ciebie o kazda decyzje po drodze.
