# D-021: rejestracja narzedzia `nowy_prospekt` w n8n (do procedury okna)

**Stan na 19/08/2026:** kod cm-agenta gotowy (endpoint `POST /lacznik/nowy-prospekt`,
bramka duplikatow, testy). **Narzedzie w n8n NIE jest zarejestrowane** - to jest wlasnie
ten krok, ktory robi sie w oknie z Tomaszem. Do tego czasu Manager nadal nie ma jak zalozyc
prospekta, mimo ze serwer juz to potrafi (AP-307: nowy kontrakt bez przelaczenia konsumenta
to polowa roboty, a wyglada na calosc).

Workflow: **`AGS Lacznik Chat Tools`**, id `yxJUJmZpSUe0tw9K`. Po zmianie ma **piec** narzedzi.

## Co dolozyc

Jeden wezel `n8n-nodes-base.httpRequestTool`, `typeVersion: 4.2`, podlaczony wyjsciem
`ai_tool` do wezla `MCP Lacznik` - dokladnie tak jak cztery istniejace.

| pole wezla | wartosc |
|---|---|
| `name` | `nowy_prospekt` |
| `type` | `n8n-nodes-base.httpRequestTool` |
| `typeVersion` | `4.2` |
| `method` | `POST` |
| `url` | `http://cm-agent:8089/lacznik/nowy-prospekt` |
| `sendHeaders` | `true` |
| `headerParameters` | jedna para: nazwa `X-Lacznik-Secret`, wartosc = ten sam sekret, ktory maja pozostale cztery wezly (`lacznik_e2_secret` z `app_secrets`) |
| `sendBody` | `true`, `specifyBody: 'json'` |
| `options` | `{ response: { response: { neverError: true } } }` |

**`neverError` jest OBOWIAZKOWE.** Odmowa bramki wraca jako HTTP 400 z trescia dla czlowieka:
lista wierszy uznanych za ten sam podmiot plus lista danych, ktore przepadna. Ta tresc jest
tu WARTOSCIA. Bez `neverError` czat zobaczy "tool call failed" i cala robota bramki zniknie.

## Opis narzedzia (`toolDescription`)

```
Zaklada NOWEGO prospekta w lejku sprzedazowym AGS. Wolaj, gdy pojawia sie podmiot albo
osoba, ktorej w lejku jeszcze nie ma - to JEDYNA droga zalozenia wiersza; zapisz_tekst
swiadomie odmawia i tak ma zostac. Bramka duplikatow patrzy na PARE domena plus oddzial,
wiec dwa oddzialy tej samej franczyzy przechodza jako dwa osobne prospekty. Jesli bramka
odmowi, dostaniesz nazwe i identyfikator wiersza, ktory uznala za ten sam, oraz liste
danych, ktore przepadna - NIE porzucaj ich, tylko dopisz je przez pipeline_move do tamtego
wiersza. Jesli to naprawde inny podmiot, zawolaj ponownie i wypelnij pole oddzial. UWAGA:
n8n wymaga wszystkich parametrow, wiec dla tych, ktore nie dotycza, podaj PUSTY CIAG -
system potraktuje je jak brak.
```

## Cialo zadania (`jsonBody`)

**Klucz `$fromAI` JEST nazwa parametru, ktora widzi wolajacy** (pulapka zlapana tap-testem
31/07: wezel mial `contact_id: $fromAI('kontakt', ...)`, wiec Manager wolal nazwa z kontraktu
i dostawal `Received tool input did not match expected schema`). Ponizsze nazwy sa kontraktem
i musza zostac co do znaku.

```
={{ JSON.stringify({ nazwa: $fromAI('nazwa', 'Pelna nazwa podmiotu albo imie i nazwisko osoby, tak jak ma stac w lejku', 'string'), url: $fromAI('url', 'Adres strony prospekta. PUSTY CIAG jesli nie znasz - nie zgaduj domeny', 'string'), oddzial: $fromAI('oddzial', 'Miasto oddzialu albo nazwisko, ktore odroznia ten podmiot od innego o tej samej domenie (franczyza: Egurrola Katowice kontra Egurrola Grodzisk). Zapisze sie jako wartosc ZAOBSERWOWANA, wiec podawaj TYLKO to, co wiesz. PUSTY CIAG jesli nie wiesz', 'string'), osoba: $fromAI('osoba', 'Osoba do kontaktu albo dojscie, np. przez Piotra Hamryszaka. PUSTY CIAG jesli nie dotyczy', 'string'), email: $fromAI('email', 'Adres mailowy prospekta. PUSTY CIAG jesli nie masz', 'string'), telefon: $fromAI('telefon', 'Telefon prospekta. PUSTY CIAG jesli nie masz', 'string'), notatka: $fromAI('notatka', 'Pierwsza linia kartoteki: czym sie zajmuja i skad sie wzieli, np. Szkola tanca, Katowice. Kontakt pierwszego stopnia na LinkedInie. PUSTY CIAG jesli nie dotyczy', 'string'), etap: $fromAI('etap', 'Etap lejka: prospect, qualified, proposal, negotiation, won, lost albo parked. PUSTY CIAG oznacza prospect', 'string') }) }}
```

## Polaczenie

W sekcji `connections` doloz wpis blizniaczy do istniejacych:

```
'nowy_prospekt': { ai_tool: [[{ node: 'MCP Lacznik', type: 'ai_tool', index: 0 }]] }
```

## Trzy rzeczy, o ktore latwo sie potknac w oknie

1. **Sekret ma zostac TEN SAM.** Siedzi w sciezce triggera MCP, wiec wygenerowanie nowego
   zmienia adres konektora w claude.ai i rozjezdza go z `app_secrets`. Skrypt tworzacy
   przejmuje sekret z zywego workflow, o ile nie poda mu sie `LACZNIK_E2_SECRET` - i wlasnie
   dlatego nie nalezy go podawac.
2. **Po KAZDYM PUT: deactivate + activate.** PUT zapisuje do bazy, ale aktywny snapshot
   workflow trzyma stara definicje. Bez przelaczenia narzedzie bedzie w bazie i nie bedzie
   go w rozmowie.
3. **Sonda przed uznaniem za zrobione.** `initialize` plus `tools/list` na adresie konektora
   MCP; na liscie ma stanac **piec** narzedzi, w tym `nowy_prospekt` z osmioma parametrami.
   Lista z czterema narzedziami znaczy, ze aktywny snapshot jest stary (punkt 2).

## Tap-test na zywym, ZANIM uznamy dlug za zamkniety

Bramce, ktorej nikt nie widzial przy pracy, nie ufamy (AP-314). Trzy wolania z rozmowy
Managera, w tej kolejnosci:

1. **Zalozenie:** `nazwa` = "Rafal Petrykowski", `osoba` = "Rafal Petrykowski",
   `notatka` = "Kontakt pierwszego stopnia na LinkedInie, rozmowe odwrocil Tomasz",
   reszta pusta. Oczekiwane: potwierdzenie z identyfikatorem nowego wiersza. To jest
   zdarzenie zrodlowe dlugu i ma wreszcie wyladowac w bazie.
2. **Duplikat:** to samo wolanie drugi raz. Oczekiwane: odmowa, ktora podaje nazwe
   i identyfikator wiersza z punktu 1. Jesli wiersz doszedl drugi raz, bramka nie dziala
   i nie ma o czym rozmawiac.
3. **Franczyza:** ~~`nazwa` = "Katowice Egurrola Dance Studio"~~ **PRZYPADEK NIEAKTUALNY,
   POPRAWIONY 22/08.**

   > **UWAGA, gdyby ktos wykonal ten test wedle pierwotnego brzmienia, uznalby DZIALAJACA bramke
   > za zepsuta.** Odczyt lejka z 22/08 pokazuje, ze **Katowice Egurrola juz w nim stoja**
   > (Martyna Jalocha, `katowice@egurrola.com`). Wiec dzis to wolanie ma dac **ODMOWE**, nie
   > przejscie - i odmowa bedzie dowodem, ze bramka dziala, a nie ze jest zepsuta.
   >
   > To jest AP-316 w miniaturze: **instrukcja napisana 19/08 zestarzala sie przez zmiane
   > DANYCH, nie kodu**, i wygladala przy tym tak samo swiezo.

   **Franczyze pokrywa juz test automatyczny** (`cm-agent/tests/test_nowy_prospekt.py`), gdzie
   dwa oddzialy tej samej domeny przechodza OBA. Powtarzanie tego na zywym lejku zalozyloby
   **fikcyjnego prospekta**, ktorego trzeba by potem sprzatac - a lejek jest zrodlem prawdy
   dla sprzedazy, nie poligonem. **Na zywym robimy wylacznie punkty 1 i 2.**

Punkt 3 nie zaklada juz zadnego wiersza, wiec nie ma czego sprzatac.
