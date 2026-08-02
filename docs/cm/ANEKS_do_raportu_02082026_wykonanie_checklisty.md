# ANEKS do raportu z 02/08: wykonanie checklisty

**Od:** BE → **Do:** Manager AGS
**Dotyczy:** `RAPORT_do_Managera_02082026_most_katalogi_i_audyt.md`

**Po co ten aneks:** raport powstał **przed** wykonaniem checklisty. Opisuje grupę A jako otwartą
i A3 jako sprawę do sprawdzenia. Od tamtej pory obie są zamknięte. Piszę, żebyś nie planował
pracy, która jest już zrobiona.

Repozytorium `33a21bf`. Serwer zostaje na `951df94` - dzisiejsze zmiany nie ruszają zachowania
produkcji, wgrają się przy najbliższym innym wdrożeniu.

---

## 1. Grupa A zamknięta w całości

Tomasz zatwierdził siedem pozycji i **narzucił kolejność wprost od skutku dla klienta**:
najpierw nieprawdziwe dane o nim samym, potem infrastruktura. Jego uzasadnienie:

> *„Punkty 3, 4 i 7 to nieprawdziwe dane o Tomaszu, które może przeczytać klient. Reszta
> to infrastruktura, która może poczekać godzinę."*

To jest ta sama logika, którą stosował przy wycofaniu serii z X: pierwszeństwo ma to,
co wychodzi na zewnątrz.

## 2. Biografia: TRZY wystąpienia inwersji, nie jedno

Raport zgłaszał jedno (`PRODUKT_GLOWNY`, „Jestem choreografem"). Przy pracy wyszło drugie
(`TNM_o-mnie_copy_v3.5`: *„myślenie systemami nie zaczęło się od kodu. Zaczęło się od scen"* -
inwersja napisana ładniej, ale ta sama), a **trzecie znalazłem przypadkiem**, przy nakładaniu
naklejek: `TNM_Google_Ads_Ekosystem_Produktowy.md` miał w podpisie autora *„choreograf
i właściciel studia tańca z 20-letnim doświadczeniem"*.

**Nie znalazłem go wcześniej, bo szukałem frazy, nie pojęcia.** To ten sam błąd, który
opisuję w punkcie 5 poniżej - popełniony przeze mnie w trakcie naprawiania go u innych.

Wszystkie trzy poprawione. **Teksty do dwóch pierwszych napisał Tomasz**, ja naniosłem wyłącznie
poprawki gramatyczne. Uzupełnił kanon o szczegół, którego nie znałem: **praca magisterska nie była
teoretyczna** - napisał oprogramowanie klienta i serwera, czyli realny kod i wdrożenie.

Kanon w obowiązującym brzmieniu: inżynier był pierwszy (elektronika i telekomunikacja, profil
komunikacja cyfrowa, praca magisterska o budynku inteligentnym w architekturze klient-serwer
z napisanym kodem, odrzucona propozycja doktoratu), taniec był planem B, który wyszedł jako plan A
na ponad dwadzieścia lat. **Nigdy „choreograf, który nauczył się systemów".**

## 3. A3 naprawione. Podtrzymuję korektę wagi z raportu

Oba pliki polityki prywatności przepisane na stan faktyczny: GA4 z Consent Mode, baner z dwoma
wyjściami, brak pikseli reklamowych. Zastrzeżenia „v1.0 do weryfikacji w 14 dni" zdjęte -
sprawdziłem w backlogu, że weryfikacja prawna faktycznie została zamknięta 29/05, a backlog
wymieniał zdjęcie tego banera jako **jedyną** pozostałą czynność.

**Bez dopisku, że polityka została zweryfikowana prawnie.** To decyzja Tomasza: takie twierdzenie
ma wyjść od niego, nie ode mnie.

## 4. Punkt o cenach przerobiony przez Tomasza - i jego wersja jest lepsza

Proponowałem jedną naklejkę „ZAPARKOWANY" i zwróciłem uwagę, że nałożenie jej na
`PRODUKT_GLOWNY` godzinę po poprawieniu tam biografii wygląda niespójnie. Tomasz **zmienił
instrukcję na dwie różne etykiety** i uzasadnił to tak:

> *„Poprawiliśmy w tym pliku biografię, bo biografia jest prawdą o człowieku niezależnie
> od tego, czy produkt się sprzedaje. Cena to co innego. Dwie różne rzeczy, dwie różne naklejki."*

- cztery pliki cenowe → `STATUS: CENY NIEOBOWIĄZUJĄCE 02/08/2026`
- dwa pliki produktu → `STATUS: PRODUKT NIEAKTYWNY OD 05/2026. Treść merytoryczna aktualna.`

**Ceny nie zostały ustalone i nie miały być.** Trzy sprzeczne widełki były problemem wyłącznie
dlatego, że pliki udawały aktualne.

## 5. AP-309 rozszerzony o stronę SZUKANIA (sformułowanie Tomasza)

**Grep na jedną frazę zaniża liczbę trafień, kiedy dwa dokumenty mówią to samo innymi słowami.**

Dowód: ten sam fałsz o analityce siedział w dwóch plikach w **czterech** miejscach, za każdym
razem inaczej: „nie używa cookies analitycznych" / „Google Analytics (w przyszłości)" / „brak
Google Analytics, Facebook Pixel w Wave 0" / „GA4, gdy wdrożone Wave 1+". Grep pierwszej frazy
zwrócił **jedno** trafienie z czterech.

Zasada: **szukaj pojęcia, nie frazy. Minimum trzy różne sformułowania, zanim uznasz plik
za czysty.**

**To był wzorzec całej sesji, cztery razy pod rząd:** etykieta zamiast treści maila, parametr
`kontakt` zamiast `contact_id`, `%Chwalin%`, cztery sformułowania o analityce - a na koniec
trzeci „choreograf". Wspólny mianownik: **wzorzec dopasowania to założenie o danych, nie fakt
o nich.**

## 6. Most domknięty i sprawdzony na produkcji

Narzędzie `zapisz_tekst` zna już parametr `katalog`. **Gałąź zapisu przetestowana na żywej
bazie** w sekwencji narzuconej przez Tomasza: wyczyszczone SQL-em → ustawione narzędziem →
druga próba zmiany odbita błędem. Test na Wrocławskiej Stepowni, **świadomie nie na Chwalińskim** -
jego wiersz miał zostać nietknięty, bo to jedyny prospekt, do którego idzie dziś materiał.

Zgłosiłem wcześniej, że ta gałąź jest pokryta wyłącznie testem jednostkowym. Tomasz kazał
sprawdzić na produkcji, powołując się na moje własne słowa o tym, że to nie to samo.

## 7. D-002 zamknięty. Zestaw 18/18 zielonych, pierwszy raz

`slots.py` i `reslot.py` mają jedno pośrednictwo `_teraz()`: produkcja bez zmiany zachowania,
test podmienia na stały moment. Oba testy nie odwołują się już **w ogóle** do zegara systemowego.

Powód, dla którego to nie jest kosmetyka: czerwony test, który bywa czerwony niezależnie od kodu,
uczy ignorowania czerwonych testów.

## 8. Ustalenia, które zamykają otwarte pytania z audytu

**tyniemusisz.pl NIE jest zawieszone ani zamknięte.** Audytor zapisał to jako pytanie ważące
na połowie listy. Odpowiedź Tomasza: **TNM to marka, pod którą idzie cały polski lejek
sprzedażowy** - 19 szkół tańca, StandART, Wrocławska Stepownia, Dance Company La Cultura,
adamietz.pl i Grupa Chwaliński. Audytor nie mógł tego wiedzieć z plików, bo w bazie wszystkie
wiersze mają jeszcze `brand_id='AGS'`. Dopisane do notatki z audytu, żeby nie wracało.

**Reguła marek obowiązująca:** polski rynek i polski język to TNM, anglojęzyczne kontakty
z X i LinkedIna to AGS. **Wielomarkowość kodu wchodzi po pierwszej zamkniętej sprzedaży**
(D-013), a nie wcześniej.

**Nowa reguła doktrynalna, ustanowiona przy okazji D-009:** słownik i migracja istniejących
wierszy idą w jednym kroku albo nie idą wcale. Tomasz zapisał to jako regułę po moim uzasadnieniu,
dlaczego nie ruszam kanałów w `_ENG_CHANNEL` - to ta sama lekcja co StandART 24/07.

## 9. Co zostaje otwarte

- **Grupy B i C z audytu, 51 pozycji.** Decyzja Tomasza: poczekają.
- **Twoja kolejka bez zmian:** walidacja długości + pole formatu, potem rozsuwanie części.
  Wracają, kiedy CM wyprodukuje jednoczęściowo. **Kolejka X nadal pusta.**
- **Dług:** D-001, D-003 do D-013 (bez zamkniętego D-002). Najbliżej bólu **D-009** - mail
  Sprzedawcy ląduje w kanale `Other`, tekst z teczki w `Email`, więc liczenie wysyłki per kanał
  kłamie. Naprawa wymaga słownika i migracji w jednym kroku.
