# PROTOKÓŁ OKNA n8n - 22.08.2026

Plan: `docs/ops/OKNO_n8n_PLAN.md`. **Fazy 1 i 2 wykonane, faza 3 NIE ZACZĘTA** (decyzja Tomasza:
brak czasu, kończymy to, co stoi otworem, reszta czeka).

## FAZA 1: rebuild z blokami G i E - WYKONANA

| krok | wynik |
|---|---|
| 1.1 pull | serwer na `main`, `72c52da`. **Warunek mówił `6aac151` i NIE był spełniony** - brakujący commit to wyłącznie plan okna, jeden plik dokumentacji, zero kodu. Odnotowane, nie przemilczane. |
| 1.2 build | `prev-ge` = `bc` = `33c2ea551ca5`, nowy `cm-agent:ge` = `7c5d0250c019`, build 41 s |
| 1.3 start | kontener wstał, `/health` = `{"status":"ok"}` |
| 1.4 weryfikacja zachowaniem | `/karty` odpowiedziało kartą materiału; odmowa D-019 przyszła po napisaniu „zapamiętaj na zawsze" |

### Znalezisko fazy 1: model OWIJA komunikat D-019 własną narracją

Zaprojektowana treść przyszła **w środku nietknięta**, ale model dopisał przed nią wstęp
(„Nie zapiszę tego jako trwałej reguły, bo nie mam do tego mechanizmu") i akapit na końcu
o sekcji Voice Bible - mimo instrukcji `PRZEKAZ TOMASZOWI DOSLOWNIE, nie streszczaj i nie dopisuj`.

**Kluczowa własność wytrzymała:** nigdzie nie padło, że reguła działa, więc bramka D-019 spełnia
swoje zadanie. Ale instrukcja „dosłownie" **nie jest egzekwowalna** - to prośba do modelu, a nie
bramka. Klasa znana: `_rewrite` też ufał, że model wykona zadanie, dopóki nie doszła bramka
wyjścia (AP-315). Do rozstrzygnięcia, czy komunikaty krytyczne mają iść **poza modelem**,
składane deterministycznie.

## FAZA 2: rejestracja narzędzia `nowy_prospekt` - WYKONANA, tap-test CZEKA

Skrypt: `n8n-workflows/patches/d021-narzedzie-nowy-prospekt-22082026.cjs`.

- `sprawdz`: 6 bramek na zielono, próba w pamięci 6/6, cztery narzędzia przed zmianą
- `zapisz`: kopia zapisana, PUT OK, `deactivate` plus `activate`, **dowód z ponownego odczytu**
  6/6 plus `workflow aktywny: true`. Pięć narzędzi, `typeVersion 4.2`, komplet ośmiu nazw `$fromAI`

**Tap-test na żywym NIE został wykonany**, więc D-021 pozostaje zamknięty częściowo.

### Znalezisko fazy 2, ważniejsze od samej fazy: D-026

Przy czytaniu wzorcowego węzła okazało się, że eksport `n8n-workflows/lacznik-chat-tools.json`
zawiera **żywy sekret `X-Lacznik-Secret` otwartym tekstem, w czterech miejscach, wypchnięty
na origin**. Repozytorium jest prywatne (potwierdzone), więc to nie był pożar, ale sekret należy
uznać za ujawniony. Pełny wpis: D-026.

Druga rzecz z tej samej minuty: `.gitignore` chronił kopie zapasowe **wyłącznie w katalogu
`n8n-workflows/`**, a skrypty zapisują je do katalogu bieżącego, czyli do korzenia repo. Kopia
z żywym sekretem lądowała **poza zasięgiem reguły, która „przecież ją obejmuje"**. Załatane
i sprawdzone plikiem próbnym.

### Fałszywy trop, rozstrzygnięty sondą

Manager AGS zameldował „Łącznik akurat znowu leży" i brak narzędzia. **Odczyt `stan_gry` przez
ten sam konektor zwrócił pełny stan lejka**, czyli Łącznik działał. Prawdziwa przyczyna: rozmowa
Managera trzymała listę narzędzi sprzed zmiany, a lista MCP nie odświeża się sama.

**To jest AP-311 w czystej postaci:** brak narzędzia w widoku miał dwie możliwe przyczyny
i tylko jedna była faktem o świecie. Gdyby nie sonda, cofalibyśmy poprawną zmianę.

## FAZA 3: D-017, token w 44 węzłach - NIE ZACZĘTA

Skrypt i procedura gotowe i sprawdzone offline (`docs/ops/OKNO_D017_przygotowane.md`).
Nic nie zostało dotknięte, więc nie ma czego cofać.

## STAN PO OKNIE

- Na produkcji: **`cm-agent:ge`** (bloki B, C, G, E). Cofnięcie o krok: `cm-agent:prev-ge` (= `bc`).
- n8n `AGS Lacznik Chat Tools`: **pięć narzędzi**, aktywny.
- n8n `HITL Handler`: **nietknięty**.

## DO DOKOŃCZENIA

1. **Tap-test `nowy_prospekt`** - Manager musi przeładować konektor, potem trzy wywołania
   z `docs/ops/D021_NARZEDZIE_N8N_NOWY_PROSPEKT.md`.
2. **Faza 3 (D-017)** - jedno wejście, kilkanaście minut.
3. **D-026** - naprawa bramki eksportera, potem wymiana sekretu.

## ZMIANA STANU FAKTÓW, WYCHWYCONA PRZY OKAZJI

Odczyt `stan_gry` pokazał wpis z 21.08: **Marek Sroka odwołał mailem spotkanie 3.09**
(zebranie wszystkich pracowników), prosi o kontakt po powrocie Mirosława z urlopu 01.09.

Dwie konsekwencje:

1. **Czekający przypadek D-025 przestał istnieć.** Poprawka godziny z 11:00 na 9:00 dotyczy
   spotkania, którego nie będzie. Sama luka (brak drogi zmiany terminu bez wpisu tekstu) zostaje,
   ale straciła swój dowód. W lejku stoi już `Grupa Chwaliński, następny kontakt 01/09 12:00`.
2. **Marek Sroka JEST kontaktem po stronie Chwalińskiego**, co domyka wczorajszą zagadkę
   z nazwiskiem w AP-317. Korekta z 19.08 była słuszna wobec dowodów, jakie wtedy istniały
   (źródło mówiło „Chwaliński" i nic nie łączyło tych dwóch), a dziś wiadomo, że powiązanie
   jest prawdziwe. **Nie zmieniam korekty**: przypis ma mówić to, co potwierdzone, a nie to,
   co się później okazało trafnym domysłem.
