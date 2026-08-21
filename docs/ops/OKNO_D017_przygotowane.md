# OKNO D-017 (PRZYGOTOWANE, NIEWYKONANE) - token bota Telegrama wychodzi z 44 węzłów HITL Handlera

**Stan na 19.08.2026: to jest procedura gotowa do wklejenia, a nie protokół z wykonania.**
Nikt jeszcze nie dotknął produkcji. Skrypt istnieje, przebieg na sucho przeszedł na eksporcie
z repozytorium, bramki zostały odpalone złym wsadem siedem razy i siedem razy padły zamknięte.
Okno otwiera Tomasz, przy klawiaturze, kiedy Manager je zaplanuje.

**Zasada nadrzędna z wpisu D-017: okna NIE otwieramy specjalnie dla tego długu.** Token nie
wyciekł, repozytorium jest czyste. Dług wchodzi przy PIERWSZYM oknie n8n, które i tak się otworzy.

---

## Co dokładnie się zmienia

Dzisiaj 44 węzły `httpRequest` mają token wpisany w ścieżkę adresu:

```
https://api.telegram.org/bot<TOKEN>/sendMessage
```

Po oknie te same 44 węzły czytają token z `app_secrets`, przez nowy węzeł `TG Token`:

```
=https://api.telegram.org/bot{{ $('TG Token').first().json.tg_token }}/sendMessage
```

Łańcuch wykonania zmienia się w jednym miejscu:

```
przed:  Telegram Trigger -> Detect Update Type -> Route By Update Type -> ...
po:     Telegram Trigger -> TG Token -> Detect Update Type -> Route By Update Type -> ...
```

`TG Token` to węzeł Postgres z zapytaniem
`SELECT value AS tg_token FROM app_secrets WHERE key='telegram_bot_token' LIMIT 1;`
na tym samym poświadczeniu, którego używa pozostałych 69 węzłów postgresowych tego workflow.

Ponieważ `TG Token` przestawia wejście `Detect Update Type`, ten węzeł dostaje jednoliniową
poprawkę, żeby czytał dane wprost z wyzwalacza:

```
przed:  const item = items[0].json;
po:     const item = $('Telegram Trigger').first().json;
```

**To jest ta sama dana.** Skrypt liczy tę podmianę osobno i wymaga dokładnie jednej.

### Dlaczego `app_secrets`, a nie poświadczenie n8n ani zmienna środowiskowa

1. **Poświadczenie n8n odpada z powodu technicznego.** Poświadczenia wstrzykują się w nagłówki
   albo w uwierzytelnianie węzła. Telegram trzyma token w ŚCIEŻCE URL. Poświadczenie tego
   miejsca nie obsłuży bez przepisania 44 węzłów na inny typ węzła, a to jest przebudowa,
   nie de-hardkod.
2. **Zmienna środowiskowa (`{{ $env.* }}`) odpada, bo byłaby czwartym mechanizmem.** W całym
   workflow jest zero użyć `$env`. Doszedłby do tego restart kontenera n8n, czyli okno dłuższe
   niż samo `PUT`.
3. **`app_secrets` to kanon tego projektu**, powtórzony w `SYSTEM_DATAFLOW`, `DEPLOY_CHECKLIST`
   i `komponenty/n8n-transport`. Wpis D-017 sam wskazuje ten kierunek słowami "dokładnie tak,
   jak zrobiono w Schedulerze 02/07".
4. **Wiersz JUŻ TAM JEST i JUŻ jest czytany.** Nie zakładamy nowego sekretu. Klucz
   `telegram_bot_token` czyta Scheduler (węzeł `Get Keys`) i czyta go sam HITL Handler
   (węzeł `PostgreSQL Lookup Session`, kolumna `tg_token`). Sześć węzłów tego workflow już
   dziś buduje adres z wyrażenia. Robimy to samo, tylko dla pozostałych 44.

Efekt uboczny, który jest właściwą nagrodą: **rotacja tokenu przestaje być oknem serwisowym.**
Po tej zmianie wymiana tokenu to jeden `UPDATE` w `app_secrets`.

**ROZSTRZYGNIĘTE PRZEZ MANAGERA 19.08: w TYM oknie NIE rotujemy tokenu.** Rotacja wchodzi jako
**osobny krok, po 24 godzinach stabilności**, i też z weryfikacją prawdziwą wiadomością.

Powód, przyjęty przez Managera: argument z długu („skoro i tak trzeba dotknąć 44 węzłów")
po tej zmianie przestaje obowiązywać. Mieszanie dwóch zmian w jednym oknie na **jedynym
interfejsie Tomasza** kosztuje możliwość odróżnienia, która z nich zawiodła, gdyby bot zamilkł.
Jedna zmiana, jeden dowód, jedna droga cofnięcia.

---

## KROK 0 (Windows, PowerShell 5.1): wczytaj poświadczenia n8n

`&&` w PowerShellu 5.1 **nie istnieje** i wywala parser. Poniżej wszystko jest w składni PS.

```powershell
cd C:\Claude-CoWork\AGS\ags-agents
```

```powershell
Get-Content .\.env | Where-Object { $_ -match '^(N8N_BASE_URL|N8N_API_KEY)=' } | ForEach-Object { $p = $_ -split '=', 2; Set-Item -Path ("Env:" + $p[0].Trim()) -Value $p[1].Trim() }
```

```powershell
"BASE=$env:N8N_BASE_URL  KEY_DL=$($env:N8N_API_KEY.Length)"
```

Ma się pokazać adres serwera n8n i **niezerowa** długość klucza.
Jeśli `KEY_DL=0` albo `BASE=` jest puste, **zatrzymaj się** - reszta kroków i tak by nie zadziałała.

## KROK 1 (Windows): przebieg na sucho BEZ SIECI, na eksporcie z repozytorium

To jest tania próba generalna. Nie dotyka produkcji w ogóle.

```powershell
node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs sucho-z-pliku n8n-workflows\x-agent\ags-hitl-handler-v1.json
```

Ma się pokazać osiem linii `OK` w sekcji `BRAMKI`, dziesięć linii `OK` w sekcji
`KONTROLA WYNIKU` i na końcu:

```
WYNIK: przemiana przechodzi. Mozna isc do trybu `zapisz` (ten dopiero wysyla PUT).
```

Jakiekolwiek `STOP` w tym kroku znaczy, że popsuł się skrypt albo eksport w repozytorium.
**Zatrzymaj się i wklej wynik do rozmowy.** Do produkcji nie idziemy.

## KROK 2 (Windows): przebieg na sucho na ŻYWEJ definicji, tylko odczyt

```powershell
node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs sucho
```

Ten tryb robi wyłącznie `GET`. Nic nie zapisuje, nic nie wyłącza.

**Warunek przejścia dalej:** te same osiem `OK` w `BRAMKI`, w tym linia

```
OK    liczba wezlow do podmiany: 44, oczekiwana 44
```

**Warunek zatrzymania:** cokolwiek innego niż 44. Liczba 44 pochodzi ze skanu z 11.08 i została
potwierdzona 19.08 na eksporcie w repozytorium. Jeśli żywa definicja pokaże inną, **to jest
ustalenie, nie awaria** - workflow mógł urosnąć (AP-316). Wtedy: **wklej cały wynik do rozmowy
i zatrzymaj się.** Skrypt ma furtkę `--oczekiwane=N`, ale wolno jej użyć dopiero po tym, jak
koordynator potwierdzi na piśmie, że nowa liczba jest prawdziwa. Bramka z fałszywą liczbą jest
gorsza niż brak bramki.

## KROK 3 (Telegram): sprawdź, że nie przerywasz czyjejś decyzji

Przez czas kroku 4 guziki w bocie nie odpowiadają. Okno liczy się w sekundach, ale karta
zatwierdzenia w locie to karta stracona.

Napisz do bota:

```
/karty
```

Jeśli odpowie listą kart czekających na decyzję, **najpierw je zamknij albo odłóż okno.**
Jeśli odpowie, że kart nie ma, idź dalej.

Ta odpowiedź jest jednocześnie **stanem PRZED** - bot działa na starej definicji i odpowiada.
Zapamiętaj, jak wygląda, bo w kroku 5 porównasz.

## KROK 4 (Windows): zapis, z kopią i bramką

```powershell
node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs zapisz
```

Skrypt w tej kolejności: pobiera definicję, przepuszcza ją przez osiem bramek, **zapisuje kopię
i odczytuje ją z powrotem**, przeprowadza przemianę w pamięci, przepuszcza wynik przez dziesięć
kontroli i **dopiero wtedy** wyłącza workflow, robi `PUT`, włącza z powrotem i porównuje
`nodes` z `activeVersion`.

Masz zobaczyć, po kolei:

```
  KOPIA DEFINICJI: ...\n8n-workflows\patches\bk_hitl_d017_<znacznik>.json  (... KB)
  kopia odczytana z powrotem: 254 wezlow. OK.
  deactivate: 200
  PUT: 200
  po PUT (baza): literaly 0 | na "TG Token" 44 | wezlow 255
  activate: 200
  flaga active: true
  nodes         : wyrazenie "TG Token" x44
  activeVersion : wyrazenie x44 | adresow z literalem x0
  ZGODNE: uruchomiona wersja to ta, ktora wlasnie zapisalem.
  ZAPIS: definicja w bazie zgodna z zamiarem.
  STAN: workflow aktywny.
```

**Zapisz sobie ścieżkę pliku `bk_hitl_d017_*.json`. To jest bilet powrotny.**
Ten plik zawiera **żywy token** i dlatego łapie się na regułę `.gitignore`
(`n8n-workflows/**/bk_*.json`). **Nie commituj go i nie wklejaj do rozmowy.**

Warunki zatrzymania w tym kroku:

- `NIEZGODNE: uruchomiona wersja to NIE jest ta, ktora zapisalem.` - idź do RATUNKU.
- `STAN: workflow NIEAKTYWNY` - **to jest pilne**, Tomasz nie ma guzików. Włącz workflow ręcznie
  w panelu n8n albo odpal RATUNEK.
- `activeVersion: BRAK w odpowiedzi API.` - to nie jest sukces ani porażka, tylko brak dowodu.
  Rozstrzyga wyłącznie krok 5.
- Cokolwiek z napisem `STOP` **przed** linią `deactivate` - nic nie zostało wysłane, definicja
  jest nietknięta. Wklej wynik do rozmowy.

## KROK 5: weryfikacja PRAWDZIWĄ WIADOMOŚCIĄ, nie kodem odpowiedzi

**Ten krok jest wymogiem Managera, nie formalnością.** `200` z n8n i flaga `active` nie dowodzą,
że bot działa. Dowód z 19.08: `/health` odpowiadało `ok`, gdy każda ścieżka LLM była martwa przez
wyczerpane środki API. Sformułowanie Managera: **dwieście OK przy martwym webhooku wygląda
identycznie jak sukces.**

Cztery wiadomości, każda dotyka innej grupy z tych 44 węzłów. Rób je po kolei.

**5.1 - podstawowa ścieżka i poprawka w `Detect Update Type`.** Napisz do bota:

```
/menu
```

Ma przyjść **menu z guzikami** (węzeł `Send Menu`, jeden z 44). Jeśli bot MILCZY, poprawka
w `Detect Update Type` zerwała łańcuch. Idź do RATUNKU natychmiast, nie próbuj dalej.

**5.2 - ścieżka guzika i `answerCallbackQuery`.** Tapnij dowolny guzik w tym menu.

Guzik ma **przestać się kręcić od razu** i ma przyjść odpowiedź na wybraną pozycję.
Kręcący się w nieskończoność zegarek na guziku znaczy, że padł węzeł
`Telegram Answer Callback Immediate` - czyli token w adresie nie działa. RATUNEK.

**5.3 - osiem adresów, które dostały prefiks `=` (najbardziej narażona grupa).** Napisz do bota
zwykły tekst, bez ukośnika, np.:

```
proba D-017: notatka na sprawdzenie
```

Ma przyjść **karta podglądu pomysłu z guzikami** (węzeł `Idea Send Preview`). To jest
najważniejszy z czterech testów: tych osiem adresów było zwykłymi napisami, a patch dopisał im
prefiks `=`. Gdyby go zabrakło, n8n wstawiłby klamry dosłownie do adresu, Telegram oddałby 404,
a bot **milczałby bez żadnego błędu widocznego dla Ciebie**. Cisza tutaj = RATUNEK.

**5.4 - odmiana adresu `/file/bot`.** Wyślij botowi dowolne **zdjęcie**.

Ma przyjść normalna reakcja na zdjęcie (węzły `Photo GetFile` i `Photo Download`, jedyne dwa
z adresem w postaci `api.telegram.org/file/bot<TOKEN>/`). Cisza = RATUNEK.

**Wklej do rozmowy, co przyszło na każdą z czterech prób.** Bez tego okno nie jest zamknięte.

## KROK 6 (Windows): przeeksportuj workflow do repozytorium

Po udanym kroku 5 eksport jest sam w sobie dowodem: maska nie ma już czego maskować.

```powershell
node n8n-workflows\eksport-do-repo.cjs sprawdz
```

Przy `AGS HITL Handler v1.0` ma stać:

```
  zamaskowane : nic
  podejrzane  : nic
```

**To jest właściwy dowód zamknięcia D-017.** Do 19.08 stało tam `<TELEGRAM_BOT_TOKEN> x44`.
Jeśli nadal coś maskuje, dług NIE jest zamknięty i trzeba zobaczyć, które węzły zostały.

Dopiero potem zapis:

```powershell
node n8n-workflows\eksport-do-repo.cjs zapisz
```

```powershell
git -C C:\Claude-CoWork\AGS\ags-agents status --short
```

Ma się zmienić `n8n-workflows/x-agent/ags-hitl-handler-v1.json`.
**Nie ma prawa** pojawić się żaden `bk_*.json`. Jeśli się pojawi, `.gitignore` nie zadziałał
i **nie wolno commitować**, dopóki to nie zostanie wyjaśnione.

## KROK 7: sprzątanie i zamknięcie

Kopia `bk_hitl_d017_*.json` zawiera żywy token. Zostaje na dysku, dopóki okno nie jest zamknięte
i potwierdzone. **Kasujemy ją dopiero po kroku 5 zakończonym czterema odpowiedziami bota**, a nie
wcześniej. Do rozmowy wklej: wyniki kroków 2, 4, 5 i 6.

Zamknięcie wpisu D-017 w `docs/ops/DLUG_TECHNICZNY.md` robi koordynator, po oknie.

---

## RATUNEK: powrót do definicji sprzed patcha

Jedna komenda. Ścieżkę kopii wypisał krok 4.

```powershell
node n8n-workflows\patches\d017-token-bez-hardkodu-19082026.cjs cofnij "C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\patches\bk_hitl_d017_<znacznik>.json"
```

Bez podanej ścieżki skrypt weźmie **najnowszą** kopię `bk_hitl_d017_*.json` z katalogu
`patches` i wypisze, którą wziął. Odmówi, jeśli podana kopia jest już **po** patchu.

Cofnięcie robi to samo, co zapis, tylko w drugą stronę: `deactivate`, `PUT` starej definicji,
`activate`, porównanie `nodes` z `activeVersion`. Po nim **powtórz krok 5.1** (`/menu`).
Cofnięcie, które nie zostało sprawdzone wiadomością, nie jest cofnięciem.

**Gdyby skrypt padł w środku i zostawił workflow wyłączony**, a `node` nie odpowiadał: wejdź
w panel n8n, otwórz `AGS HITL Handler v1.0` i przestaw przełącznik `Active` ręcznie. Bot bez
guzików jest gorszy niż bot z hardkodowanym tokenem.

---

## Czego ta procedura NIE robi

- **Nie rotuje tokenu.** Wpis D-017 stawia to pytanie ("skoro i tak trzeba dotknąć 44 węzłów").
  Odpowiedź po tej zmianie brzmi: nie trzeba już dotykać 44 węzłów, żeby rotować. Rotacja staje
  się jednym `UPDATE` w `app_secrets` plus `deactivate`/`activate`. Decyzja Managera, osobno.
- **Nie rusza sześciu węzłów**, które już dziś czytają token z własnego wyrażenia
  (`Agsel Set Commands`, `Agsel Confirm Msg`, `Agents Send Menu`, `Cmtier Confirm`, `Cele Send`,
  `Tgl Send`). Bramka pilnuje, żeby przeszły patch nietknięte.
- **Nie dotyka `AGS Scheduler v1` ani `AGS Lacznik Chat Tools`.** Oba mają zero literałów
  sekretów w parametrach.
