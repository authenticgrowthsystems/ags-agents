# RAPORT z sesji koordynującej - 19.08.2026

**Tryb:** sesja koordynuje, nie wykonuje (model pracy ustalony 02/08, prośba z
`ODPOWIEDZ_do_Managera_11082026.md`). Praca rozdzielona na dwóch podwykonawców
pracujących równolegle, koordynator trzymał nadzór, weryfikację, dokumentację i commity.

**Zakres:** blok F z planu zatwierdzonego 19.08 plus AP-317 z kolejki briefu.
**Blok A (lejek) NIE był dotykany** - wykonuje go Tomasz ręcznie, zgodnie z decyzją.

## CO ZOSTAŁO ZAMKNIĘTE

| pozycja | commit | plik |
|---|---|---|
| AP-317 do kanonu | `96856c7` | `docs/anti-patterns/AP-317_brak_wpisu_nie_jest_dowodem_ciszy.md` + `anti-patterns/library.md` |
| Blok F, fakty build-in-public do CM | `8331e95` | `docs/cm/BIP_MASTERPROMPT_CM_19082026.md` |

Zestaw testów **33/33 zielony**, mierzony dwa razy: przed pracą na `4e93edb` i po zmianach.
Uruchamiany `python -X utf8`, każdy plik osobno.

## AP-317 - dwie rzeczy, które wyszły inaczej, niż zakładałem

**Pierwsza: dowód na drugą połowę anty-wzorca istnieje, a ja twierdziłem, że go nie ma.**
Szukałem opisem zjawiska (`zrzut`, `screen`, `godzin`) i nie trafiłem. Podwykonawca trafił
od strony etykiety: `grep -rn "AP-317"` po całym katalogu AGS. Pełny przebieg leży w
`C:\Claude-CoWork\AGS\MASTERPROMPT_MANAGER_AGS_v5_fable.md` sekcja 7. Sprawdziłem źródło
osobiście, zanim przyjąłem wpis.

To jest AP-309 od strony szukania w czystej postaci, tylko o jeden poziom wyżej niż zapisany:
biblioteka mówi "szukaj pojęcia, nie frazy, minimum trzy sformułowania". Tu wygrało coś innego -
**szukanie identyfikatora zamiast opisu**. Etykieta `AP-317` jest jedna i nie ma synonimów,
opis zjawiska ma ich dowolnie wiele. Wniosek wart dopisania przy okazji następnej rewizji AP-309:
jeśli rzecz ma nadany numer albo nazwę własną, zacznij od niej, a dopiero potem szukaj opisu.

Wersja z pełnym dowodem jest istotnie mocniejsza od tej, którą zamawiałem. Trzeci stopień
wpadki - **błędny odczyt został zapisany do bazy jako fakt** - jest najważniejszy i nie było go
w moim briefie. Domysł pierze się w źródło prawdy: wiersz w bazie nie niesie informacji o tym,
czy powstał z obserwacji, czy z wnioskowania.

**Druga: podwykonawca musiał podważyć zapis w AP-311, żeby AP-317 miał rację bytu.**
AP-311 broni się przed rozdzieleniem zdaniem "Nie były, albo były poza zasięgiem systemu -
to AP-311". Rozgraniczenie, które się utrzymało, nie idzie po osi wewnątrz/na zewnątrz systemu,
tylko po **naprawialności**:

> Czy istnieje poprawka, po której ta pustka stałaby się wiarygodna?
> Tak - AP-311, szukaj wady. Nie, bo kanał nie ma żadnego połączenia z bazą - AP-317,
> zmieniasz sposób czytania, nie system.

To rozstrzygnięcie stoi w obu plikach. **Wymaga potwierdzenia Managera**, bo zmienia sens zdania
zapisanego wcześniej w AP-311, a nie jestem autorem tamtego wpisu.

AP-317 jest też pierwszym anty-wzorcem tej rodziny, na którym **nie działa recepta reszty**.
W 306, 310 i 314 ciszę produkuje komponent zepsuty, więc da się ją wywołać złym wsadem.
Tu ciszę produkuje komponent sprawny: baza nie widzi SMS, WhatsAppa, telefonów, wiadomości
z LinkedIn i X, więc pusta teczka jest poprawną odpowiedzią na niepełne pytanie. Nie ma czego
nakarmić i nie ma czego naprawić, dopóki nie powstanie warstwa 0. Zamiast bramki w kodzie
wchodzi stały protokół pytania do człowieka - i bramka na tym, co człowiek przyśle.

## BLOK F - co poszło do CM i gdzie postawiłem granicę ostrzej niż brief

Bohater materiału: **każda warstwa kontroli treści rośnie w stronę FORMY i żadna nie pyta,
CZYM ten tekst jest**. Naprawą jest bramka wyjścia oparta na mierze pokrycia słów, nie czarna
lista. Puenta działa poza naszym systemem i to ona jest wartością dla odbiorcy: *każde wywołanie
modelu, którego wynik wraca do potoku jako DANE, potrzebuje bramki wyjścia, bo "odpowiedź
o zadaniu" i "wynik zadania" są dla kodu nieodróżnialne, oba są napisem.*

Drugi kandydat, zostawiony CM jako **osobny materiał, nie podwątek**: osiem z jedenastu
anty-wzorców inżynierskich to jedna klasa "cisza wygląda jak sukces". Kolejność między nimi
rozstrzyga CM, bo wybór kąta to jego rola, nie moja.

Granica Z-5 wpisana w plik jako **instrukcja dla CM**, nie jako notatka obok: sześć zakazów
plus test nadrzędny nad ich literą - *czy odbiorca po przeczytaniu tego zdania ma prawo pomyśleć,
że coś nam wyszło publicznie*. Poza Z-5 zakazane tak samo mocno: życie prywatne, stan lejka,
jakakolwiek sugestia płatnych klientów.

**Jedna poprawka koordynatora po audycie.** Podwykonawca zacytował decyzję Z-5 dosłownie,
więc data dzienna incydentu stała w pliku - w sekcji zakazów, obok punktu zabraniającego jej
podawania. Usunąłem ją także z cytatu, z jawnym wyjaśnieniem w pliku. Powód jest ten sam,
o którym jest cały materiał: **brief jest wklejany w kontekst modelu, a zakaz w treści nie
usprawiedliwia wnoszenia danej, której model ma nie użyć.** Do wykonania zlecenia data nie jest
potrzebna ani razu, korzyść zerowa, ryzyko niezerowe. Pełny cytat został w pliku źródłowym,
dostępny dla człowieka. Nie wystarczy zakazać wyniku, trzeba odciąć drogę, którą przychodzi -
to jest AP-315 zastosowany do własnego dokumentu.

## CO ZOSTAJE OTWARTE

1. **Rozgraniczenie AP-311 kontra AP-317 do potwierdzenia przez Managera** (patrz wyżej).
2. **Treść SMS-a domykającego do Piotra Hamryszaka z 14.08 nie została nigdzie zapisana.**
   `PAMIEC_MANAGERA` mówi wprost "Treści SMS nie mam, do uzupełnienia od Tomasza później".
   Bez niej nie wiadomo, czy wstrzymanie wysyłki na dwa dni cokolwiek zmieniło w treści.
   To luka do uzupełnienia przez Tomasza, nie do odtworzenia przez agenta.
3. **Ścieżka w MEMORY.md jest nieaktualna:** wpis podaje `C:\Claude-CoWork\AGS\Sprzedaz_PLAN\`,
   brief leży w `C:\Claude-CoWork\AGS\Sprzedaz\04_PLAN\`. Do poprawy w pamięci trwałej.
4. **Bloki B, C, D, E, G nietknięte.** B i C czekają na wspólny rebuild, D i E na okno n8n
   z Tomaszem przy klawiaturze, G na koniec.
5. **Pozycja 9 z briefu nadal otwarta:** D-018 wygasił martwe karty, ale obsługa grupowanych
   partii dla żywych decyzji wciąż nie istnieje.

## NASTĘPNY KROK DLA TOMASZA

Scal gałąź do `main` i wypchnij. Potem, gdy będzie moment, wklej
`docs/cm/BIP_MASTERPROMPT_CM_19082026.md` w rozmowę z CM i poczekaj na kartę do zatwierdzenia.
