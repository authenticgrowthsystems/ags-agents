# PROTOKÓŁ OKNA SERWEROWEGO 19.08.2026

Wykonanie wg `docs/ops/OKNO_19082026_BC_i_webhook.md`. Odczyty wklejane przez Tomasza z Mikrusa,
zapisywane tutaj na bieżąco. Decyzja Managera: `SELECT` przed, kopia do `docs`, `UPDATE`,
`SELECT` po, rebuild, weryfikacja prawdziwą wiadomością.

## KROK 1 - kod na serwerze: ZNALEZIONA WADA, naprawiona

Pierwsze `git pull` **nie przyniosło dzisiejszego kodu**. Repozytorium na Mikrusie stało na gałęzi
`claude/silly-blackwell-dfc32d`, nie na `main`, i pociągnęło `4e93edb` (stan z 11.08) zamiast
`54fe646`. Lokalnej gałęzi `main` na serwerze **w ogóle nie było**.

To jest pułapka warta zapamiętania: **`git pull` na serwerze wyglądał na sukces** - fast-forward,
pięć plików, 359 linii - i nic w jego wyniku nie mówiło, że to nie ta gałąź. Krok 1 miał warunek
"na górze musi stać `1eb298b`" i tylko dlatego wyszło na jaw.

Naprawa: `git checkout -b main origin/main`. Plik nieśledzony
`cm-agent/danceit_BIALA_LISTA_23072026.xlsx` przetrwał przełączenie.

Po naprawie: `HEAD -> main`, `54fe646`, równo z `origin/main`.

## KROK 2 - kopia tabeli `channels`, ZWERYFIKOWANA

`~/kopia_channels_19082026.sql`, 16K. Pierwsza kontrola (`grep -c` po `COPY`) dała `1` i **nie była
dowodem** - to liczba bloków, nie wierszy. Druga kontrola, innym mechanizmem, policzyła wiersze
wewnątrz bloku: **12**, zgodnie ze stanem tabeli.

## KROK 3 - stan PRZED

```
 brand_id |    channel    | status |    tryb
----------+---------------+--------+------------
 AGS      | facebook      | ready  | webhook
 AGS      | instagram     | ready  | webhook
 AGS      | linkedin      | active | post_queue
 AGS      | linkedin_page | ready  | webhook
 AGS      | sprzedaz      | draft  | none
 AGS      | x             | active | post_queue
 AGS      | youtube       | ready  | webhook
 LYSY     | linkedin      | ready  | webhook
 PT       | linkedin      | ready  | webhook
 RDC      | linkedin      | ready  | webhook
 SDI      | linkedin      | ready  | webhook
 TNM      | linkedin      | ready  | webhook
(12 rows)
```

**Dziewięć wierszy `webhook`, wszystkie w statusie `ready`. Zero aktywnych z `webhook`.**
Dokładnie to, czego oczekuje bramka w `SQL_webhook_na_draft_19082026.sql`: przebieg ma się
zatrzymać, gdyby którykolwiek `webhook` siedział na kanale `active`.

Stan zgodny z odczytem sprzed okna, więc między jednym a drugim nic się nie zmieniło.

## KROK 4 - obraz zbudowany bez przestoju

`prev-bc` = `latest` = `d018` = `8fd96be70f13` (identyfikatory zgodne, warunek kroku spełniony).
Nowy `cm-agent:bc` = `33c2ea551ca5`, build 106 s.

## KROK 5 - pisarz zatrzymany

`docker stop cm-agent`. Przestój trwał od tego momentu do kroku 7.

## KROK 6 - UPDATE w transakcji, bramka przepuściła

```
NOTICE:  BRAMKA OK: 9 wierszy do poprawienia, zero aktywnych.
UPDATE 9
NOTICE:  KONTROLA OK: zero wierszy z trybem webhook.
COMMIT
```

Stan PO: dziewięć wierszy `ready` stoi na `draft`. `AGS/x` i `AGS/linkedin` nietknięte
(`active`, `post_queue`). `AGS/sprzedaz` został z `none` zgodnie z decyzją Managera (D-022).

## KROK 7 - nowy obraz podniesiony

`cm-agent:bc` wstał, `/health` zwrócił `{"status":"ok"}`.

## KROK 8 - weryfikacja prawdziwą wiadomością: ZROBIŁA SWOJE

**`/health` mówiło `ok`, a system był częściowo niesprawny.** Pierwsza próba:

- `/karty` odpowiedziało normalnie (`Brak materialow do przegladu`),
- `zapamiętaj na zawsze: nie używaj słowa ekosystem` zwróciło
  **`Blad przetwarzania wiadomosci`**.

Log kontenera pokazał przyczynę i **nie był to nasz kod**:

```
anthropic.BadRequestError: Error code: 400 - 'Your credit balance is too low
to access the Anthropic API.'
```

Skończyły się środki na API. `/karty` przeszło, bo jest deterministyczne; padła każda ścieżka
wołająca model, w tym `proactive.tick` (powtarzalnie, w pętli). Rebuild był zdrowy przez cały
ten czas i cofanie nie było potrzebne.

**To jest dowód wart zapamiętania osobno: gdyby weryfikacja skończyła się na kodzie 200,
zamknęlibyśmy okno jako udane, mając niesprawny system.** Wymóg 3 z Z-1 zarobił na siebie
w pierwszym oknie, w którym go zastosowaliśmy - i zadziałał na awarii, której nikt nie planował
tym testem złapać.

Po doładowaniu kredytów przez Tomasza druga próba dała **dokładnie zaprojektowany komunikat**:

> Odkładam tę regułę.
> Muszę Ci to przekazać wprost, bez upiększania:
> Nie zapisałem tej reguły do stylu i nie chcę, żebyś na nią liczył.
> Uczenie stylu mam wyłączone (dług D-019). Powód: taka reguła szła potem do KAŻDEGO pisanego
> tekstu, a dwa razy skończyło się to publicznym postem, który był wypowiedzią modelu zamiast treści.
> Twoja reguła nie przepadła. Odłożyłem ją na bok razem z językiem i datą, żebyś miał ją przed
> oczami w dniu, w którym uczenie odblokujemy.
> Jeśli ma działać już teraz, powiedz mi to przy konkretnym tekście. W tym jednym zastosuję ją od ręki.

Model przekazał go dosłownie, bez własnej narracji i bez twierdzenia, że reguła działa - czyli
instrukcja `PRZEKAZ TOMASZOWI DOSLOWNIE` zadziałała. Po powrocie API subagenci wznowili pracę
i zaczęły przychodzić karty materiałów.

## WYNIK OKNA

**Zamknięte, oba cele osiągnięte.** Kod bloków B i C na produkcji (`cm-agent:bc`), dziewięć
wierszy wyprostowanych na `draft`, weryfikacja przeprowadzona zachowaniem, nie kodem odpowiedzi.

Cofnięcie o krok: `cm-agent:prev-bc` (= `d018`). Kopia tabeli: `~/kopia_channels_19082026.sql`,
12 wierszy, zweryfikowana dwoma mechanizmami.

## DO ODNOTOWANIA POZA ZAKRESEM OKNA

Awaria kredytów API trwała **jakiś czas przed oknem** - log pokazuje powtarzalne padanie
`proactive.tick` w pętli, nie pojedynczy przypadek. Nikt się o tym nie dowiedział, dopóki
człowiek nie napisał do bota. **System nie ma alarmu na wyczerpanie środków API**, a każda
ścieżka LLM pada wtedy po cichu do logu. To rodzina "cisza wygląda jak sukces" i zasługuje
na osobne zgłoszenie do Managera.
