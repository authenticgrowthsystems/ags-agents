# Maszynka prospektowa

**Stan na 27/07/2026.** Ogniwo 1 z trzech zbudowane. Komponent powstal, gdy kampania wyszla
poza szkoly tanca na cztery rodziny nisz i okazalo sie, ze system umie ZBADAC podmiot,
ktorego nazwe dostanie, ale nie umie sam dojsc do listy podmiotow.

## Po co to jest

Audyt 27/07 (sprawdzony grepem, nie z pamieci): lancuch od niszy do platnego klienta ma osiem
ogniw, mielismy cztery.

| ogniwo | stan |
|---|---|
| wybor niszy i kryterium podzialu | jest (kryterium wynika z OFERTY, nie z branzy) |
| zbieracz podmiotow: nisza + region -> lista firm | **brak** (ogniwo 3) |
| wzbogacanie: firma -> strona, mail, telefon, osoba | polowicznie (Researcher, zrodlo `site`, po jednym podmiocie) |
| kwalifikacja: ktore 40 z 276 zasluguje na dzis | **jest od 27/07** |
| import listy do lejka | **jest od 27/07** |
| tresc per nisza | polowicznie (oferta DFY jedna, uniwersalna) |
| wysylka | **brak** (ogniwo 2) - w calym repo nie ma niczego, co wysyla maila |
| pomiar i follow-up | follow-up jest (straznik terminow 26/07), pomiar odpowiedzi brak |

Kolejnosc budowy wybrana architektonicznie: **import jest pierwszy, bo definiuje kontrakt,
w ktory wpinaja sie dwa pozostale ogniwa.** Zbieracz musi miec gdzie odlozyc wynik, wysylka
musi miec skad wziac adresatow. Zbudowana najpierw wysylka wymusilaby dorazny ksztalt
odbiorcy i przerobke przy zbieraczu.

## Kryterium podzialu nisz (wynika z oferty, nie z branzy)

- **System Retencji (DFY)** trafia w kazdy lokalny biznes z wizytami i klientem powracajacym.
  Mechanika zawsze ta sama: zapytanie czeka dwa dni, puste okna w grafiku, brak opinii,
  klient znika po pierwszej wizycie. Taniec to JEDEN przypadek tej rodziny. Gra na wolumen.
  Rodziny: `sport_dzieci`, `zdrowie_uroda`, `uslugi_grafik`, `taniec`.
- **Diagnoza przeplywu informacji** trafia w firmy po szybkim wzroscie (`wzrost_firmy`).
  Wejscie 15-30 tys., cieple dojscie, cykl tygodniowy. Nigdy nie bedzie wysylka masowa.

## Ogniwo 1: import listy (`app.prospect_import`, DDL 034)

```
docker exec cm-agent python -m app.prospect_import dry   <plik.xlsx> <nisza> [--wszystkie]
docker exec cm-agent python -m app.prospect_import apply <plik.xlsx> <nisza> [--wszystkie]
docker exec cm-agent python -m app.prospect_import wake-dry   <nisza> <ile>
docker exec cm-agent python -m app.prospect_import wake-apply <nisza> <ile>
```

**Zimna lista laduje w etapie `parked`, nie `prospect`.** To jest decyzja, nie szczegol:
wrzucenie 132 zimnych wierszy jako otwartych zrobiloby z lejka liste zyczen, czyli te sama
nieprawde, ktora Manager kazal usunac 26/07, tylko trzynascie razy wieksza. Zimna lista JEST
w bazie i NIE jest w grze. Osobna komenda `wake` budzi N najlepszych z niszy, gdy Tomasz
faktycznie siada do wysylki.

**Obudzony wiersz celowo NIE dostaje `next_followup_at`.** Termin pojawia sie dopiero przy
odhaczeniu wysylki (`sales.mark_outreach_sent`). Inaczej straznik terminow zrobilby tyle
bramek, ilu obudzonych.

**Kwalifikacja (`lead_score` 0-100) odpowiada na JEDNO pytanie: czy da sie do nich napisac
i czy jest do kogo.** Mail 45, telefon 25, www 15, osoba 15; minus 30 za znane "bez MX",
minus 40 za "nieczynne", minus 15 za werdykt PODEJRZANE ze zrodla. To NIE jest ocena wartosci
prospekta - te robi czlowiek i research, nie arytmetyka na kolumnach arkusza.

### Dwie miny zlapane na prawdziwych danych (nie na testach syntetycznych)

1. **Arkusze pomijaja puste komorki**, wiec czytanie po POZYCJI przesuwa kolumny. W bialej
   liscie tanca pod naglowkiem `WWW` siedzial styl tanca. Dlatego kolumny rozpoznajemy po
   ZNORMALIZOWANYM naglowku (male litery, bez ogonkow, aliasy PL i EN), a wartosc, ktora nie
   wyglada jak domena, nie jest adresem.
2. **Dedup po samej domenie wyrzucil trzy REALNE prospekty.** Siec Egurrola ma jedna domene
   i osobny oddzial w Katowicach, Krakowie, Warszawie i Grodzisku, kazdy z wlasnym mailem.
   Franczyza to nie duplikat - to tylu klientow, ile oddzialow. Klucz domeny zawiera teraz
   miasto. Dwa razy ten sam oddzial dalej jest duplikatem.

### Wzbogacanie: duplikat nie jest smieciem (dodane 27/07 po uwadze Tomasza)

```
docker exec cm-agent python -m app.prospect_import wzbogac-dry   <plik.xlsx>
docker exec cm-agent python -m app.prospect_import wzbogac-apply <plik.xlsx>
```

Tomasz, 27/07: **"prospekty nie sa martwe, tylko nieobsluzone"**. Mial racje podwojnie.
Pierwotny import traktowal trafienie w istniejacy wiersz jako duplikat i wyrzucal rekord,
patrzac wylacznie na to, czy nazwa jest juz w lejku - a nie na to, czy przynosi cos, czego
lejek NIE MA.

**Dowod:** wszystkie dwanascie "duplikatow" z bialej listy tanca mialo mail i telefon,
podczas gdy dziewiec odpowiadajacych im wierszy lejka swiecilo "⚠️ brak kontaktu". Ci
prospekci nie byli zaniedbani - system nigdy nie podal Tomaszowi ich adresow, choc adresy
lezaly w pliku na jego dysku.

Zasady trybu:
- **Dopisuje WYLACZNIE puste kolumny.** Nigdy nie nadpisuje tego, co juz jest.
- **Rozna wartosc = KONFLIKT do decyzji czlowieka**, nie ciche nadpisanie. Przyklad z zycia:
  StandART ma w lejku `recepcja@...`, a na liscie `biuro@...` - to moze byc lepszy adres
  albo gorszy, i rozstrzyga to czlowiek, nie skrypt.
- **Nie dotyka etapu** i nie dodaje nowych wierszy - podmiot spoza lejka jest pomijany.
- Slad w notatce: `27/07 uzupelnione z listy <plik>: contact_email, contact_phone`.

### Dowod z pierwszego przebiegu (biala lista tanca, 27/07)

276 wierszy w pliku, **132 do zapisu, 0 duplikatow, 144 odsiane** (115 z werdyktem
PODEJRZANE ze zrodla, 29 bez jakiegokolwiek kanalu kontaktu). Rozklad kwalifikacji:
39 w przedziale 80-100, 39 w 60-79, 8 w 40-59, 46 w 20-39. Z flaga `--wszystkie`:
245 do zapisu, 29 odsianych.

## Czego tu jeszcze NIE MA

- **Ogniwo 2, wysylka partiami z pomiarem.** To jest prawdziwe waskie gardlo skali. Wymaga
  decyzji poza kodem: osobna domena techniczna, skrzynka nadawcza, rozgrzewka. Wysylka
  z domeny glownej przy dwustu adresach potrafi ja spalic na miesiace.
- **Ogniwo 3, zbieracz podmiotow z rejestrow po PKD.** CEIDG i KRS/REGON maja oficjalne API
  i jawne dane - to jest czysta droga do wolumenu w kazdej niszy. Scraping Map Google lamie
  regulamin, a Places zabrania trwalego skladowania wynikow, wiec Mapy nadaja sie do
  uzupelnienia pojedynczego rekordu, nie do budowy bazy.
- **Warstwa niszowa w tresci** (nisza -> bol -> dowod -> jezyk). Oferta DFY jest dzis jedna
  i uniwersalna.

## Granice, o ktorych trzeba pamietac przy wysylce

Zimny mail do firmy z adresem firmowym: uzasadniony interes plus jawny opt-out w kazdej
wiadomosci. Do jednoosobowej dzialalnosci to dane osobowe konkretnej osoby. Partiami,
nie jednym strzalem.

## Wejscia-wyjscia

- **Wejscie:** arkusz .xlsx z dowolnymi naglowkami z listy aliasow (nazwa, miasto,
  wojewodztwo, adres, telefon, e-mail, www, reprezentant, werdykt, problemy).
- **Wyjscie:** wiersze `sales_pipeline` (stage `parked`, `niche`, `lead_score`,
  `contact_email`, `contact_phone`, `contact_person`, `prospect_url`, `source='lista'`,
  `notes` z pochodzeniem).
- **DDL 034:** `sales_pipeline.niche`, `sales_pipeline.lead_score`, indeks
  `idx_sales_pipeline_niche (brand_id, niche, stage, lead_score DESC)`.

Test: `python cm-agent/tests/test_prospect_import.py` (35 przypadkow, bez bazy i bez sieci).
