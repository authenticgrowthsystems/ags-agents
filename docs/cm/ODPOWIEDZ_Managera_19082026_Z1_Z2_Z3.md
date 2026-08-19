# ODPOWIEDŹ Managera na ZGŁOSZENIE po blokach B i C (Z1, Z2, Z3) - 19.08.2026

Zapis decyzji, nie parafraza. Zgłoszenie:
`docs/cm/ZGLOSZENIE_do_Managera_19082026_po_blokach_BC.md`.

**Uwaga na wstępie:** odpowiedź przyszła **po** wykonaniu okna serwerowego, więc Z1 opisuje pracę,
która była już zrobiona. Nie wykonuję jej drugi raz. Szczegóły niżej.

---

## Z1 - dziewięć wierszy `webhook`: opcja A, POTWIERDZONA I JUŻ WYKONANA

Manager potwierdził wcześniejszą decyzję: wszystkie dziewięć wierszy na `draft`, w jednym oknie
z rebuildem B+C, wg RUNBOOKU - kopia przed, policzenie wierszy przed i po, bramka padająca
zamknięta, na końcu weryfikacja prawdziwą wiadomością na `AGS/x` i `AGS/linkedin`. Termin okna:
dziś po 21:00 albo jutro rano, wybór Tomasza.

**Stan faktyczny: okno zostało już wykonane 19.08 po południu, w całości, w tej sekwencji.**
Protokół: `docs/ops/PROTOKOL_OKNA_19082026.md`, zamknięcie w commicie `843af88`.

| wymóg Managera | jak wykonano |
|---|---|
| kopia przed | `~/kopia_channels_19082026.sql`, **zweryfikowana dwoma mechanizmami** (pierwszy, `grep -c` po `COPY`, dał `1` i nie był dowodem - liczył bloki, nie wiersze; drugi policzył 12 wierszy) |
| policzenie przed i po | `SELECT` przed i po, oba w protokole |
| bramka padająca zamknięta | `BRAMKA OK: 9 wierszy, zero aktywnych` -> `UPDATE 9` -> `KONTROLA OK: zero`; bramka zatrzymuje przy NULL, przy zerze wierszy i przy kanale AKTYWNYM z webhookiem |
| weryfikacja prawdziwą wiadomością | wykonana i **złapała realną awarię** - patrz niżej |

**Wymóg weryfikacji zachowaniem zarobił na siebie w pierwszym oknie, w którym go zastosowaliśmy.**
`/health` zwracało `{"status":"ok"}`, a każda ścieżka wołająca model była martwa: wyczerpały się
środki na API Anthropic. `/karty` odpowiadało, bo jest deterministyczne. Gdyby weryfikacja
kończyła się na kodzie odpowiedzi, zamknęlibyśmy okno jako udane, mając niesprawny system.
Po doładowaniu kredytów przez Tomasza komunikat D-019 przyszedł dosłownie w zaprojektowanym
kształcie.

Zapisane jako **D-023**: wyczerpanie środków API nie ma alarmu, jedna przyczyna wycina naraz
wszystkie organy oparte na modelu, a sonda zdrowia jest ślepa z definicji, bo pyta o proces,
a nie o zdolność do pracy. Awaria trwała jakiś czas przed oknem (`proactive.tick` padał w pętli)
i nikt się nie dowiedział, dopóki człowiek nie napisał do bota.

## Z2 - `channels.config.rules`: OSOBNA SPRAWA, blok H po D+E

Manager **nie rozciąga D-019 wprost**. Uzasadnienie:

> Do `channels.config.rules` pisze **człowiek przez narzędzie**, nie model z destylacji,
> a to jest **legalna droga konfiguracji subagenta**.

**Zapis zostaje WŁĄCZONY do czasu bloku H.**

Zakres bloku H, cztery pozycje:
1. ten sam **filtr językowy**, który `style_learned` dostał po AP-315;
2. **kształt wpisu** (język, rodzaj, pochodzenie) przy zapisie;
3. **zmiana prefiksu** tak, żeby żaden zbiór reguł kanałowych nie miał prawa nadpisać walidatora
   języka i gatunku (dziś prefiks brzmi `OWNER RULES FOR THIS ACCOUNT (obey strictly, override
   defaults if conflict)`);
4. **wykaz WSZYSTKICH obecnych wpisów** `config.rules` do przeglądu Managera.

Kolejność bloków po tej decyzji: **D + E** (okno n8n, z Tomaszem przy klawiaturze), potem **H**,
a **G** biegnie już teraz, bo nie potrzebuje okna.

## Z3 - tryb `none`: CELOWE WYŁĄCZENIE, które trzeba nazwać

Manager uznał `none` za świadomy wyłącznik kanału. **Danych nie ruszamy** - `AGS/sprzedaz` zostaje
z `none` w bazie. Głośna obsługa w kodzie (wyłączony i mówi, że wyłączony) **dopisana do bloku G**,
który już biegł w chwili tej decyzji.

Rozszerzenie przekazane podwykonawcy bloku G: stała obok pozostałych trybów, jawna gałąź
w `dispatch_item` zostawiająca ślad, oraz rozdzielenie przypadku **wyłączony** od przypadku
**nieznany** - dziś każda nieznana wartość zachowuje się jak wyłączenie i nikt się o tym
nie dowiaduje, a to jest właściwe sedno D-022.

## Ocena Managera

> Dobra robota na B+C, 35/35 przed rebuildem to jest właściwa kolejność.
