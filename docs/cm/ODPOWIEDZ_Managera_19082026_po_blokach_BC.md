# ODPOWIEDŹ Managera na ZGŁOSZENIE po blokach B i C - 19.08.2026

Zapis decyzji, nie parafraza. Zgłoszenie: `docs/cm/ZGLOSZENIE_do_Managera_19082026_po_blokach_BC.md`.
Manager odpowiedział od razu, nie czekając na zbiorcze zgłoszenie.

## 1. Dziewięć wierszy `webhook`: PROSTUJEMY WSZYSTKIE na `draft`

Opcja A przyjęta. Uzasadnienie Managera:

> Zostawienie ich i oparcie się na "aktywacja jest świadoma" to warunek w głowie człowieka
> zamiast blokady, czyli dokładnie to, co sam nazwałeś dziurą.

Wykonanie w **jednym oknie serwerowym razem z rebuildem B+C**. Sekwencja narzucona przez Managera:
`SELECT` przed, kopia wyniku do `docs`, `UPDATE`, `SELECT` po, rebuild, na końcu **weryfikacja
prawdziwą wiadomością** na aktywnych kanałach (wymóg 3 z Z-1).

Kanałów aktywnych (`AGS/x`, `AGS/linkedin`) **nie dotykamy** - stoją dobrze na `post_queue`.

Wykonane po tej decyzji: `docs/ops/OKNO_19082026_BC_i_webhook.md` (osiem kroków, każdy z gotową
komendą) oraz `docs/ops/SQL_webhook_na_draft_19082026.sql` (bramka padająca zamknięta, kontrola
innym mechanizmem niż operacja, SQL odwrotny zakomentowany w tym samym pliku).

## 2. `AGS/sprzedaz` z trybem `none`: DO KOLEJKI, nie ruszać teraz

Obsłużymy głośnym komunikatem w kodzie przy innej okazji. Osobnego okna na to nie wydajemy.

Zapisane jako **D-022** w `docs/ops/DLUG_TECHNICZNY.md`.

## 3. Reguła komunikacji, obowiązuje od teraz

> Zgłoszenia decyzyjne i raporty adresujesz do Managera przez `docs/cm`, jak dotychczasowe.
> Do Tomasza kierujesz wyłącznie dwie rzeczy: prośbę o rękę na serwerze z gotową komendą
> do wklejenia oraz streszczenia maksymalnie trzyzdaniowe.
> **Tomasz nie jest skrzynką odbiorczą na analizy, od tego jest Manager.**

## Czego Manager NIE rozstrzygnął w tej odpowiedzi

**Znalezisko 2 zostaje otwarte:** drugi trwały magazyn reguł `channels.config.rules`, wstrzykiwany
do każdej generacji jako `OWNER RULES FOR THIS ACCOUNT (obey strictly, override defaults if
conflict)`, bez filtra językowego, rodzaju i pochodzenia. Ta sama klasa co D-019, mocniejsze
sformułowanie. Pytanie z punktu 2 zgłoszenia czeka: czy rozciągamy D-019 na ten magazyn, czy to
osobna sprawa z własną wagą. **Nie tknięte.**
