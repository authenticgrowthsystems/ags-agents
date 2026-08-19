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

## KROK 4 i dalej

Do uzupełnienia w trakcie okna.
