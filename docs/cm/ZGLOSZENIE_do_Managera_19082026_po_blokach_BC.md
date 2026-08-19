# ZGŁOSZENIE do Managera - 19.08.2026, po zamknięciu bloków B i C

Bloki B i C zamknięte, zestaw 35/35, commit `1eb298b`. **Rebuild kontenera jeszcze NIE wykonany.**

Trzy znaleziska wyszły przy okazji. Żadne nie jest objęte Twoimi dotychczasowymi decyzjami,
więc żadnego nie ruszam. Pierwsze wymaga decyzji przed rebuildem, dwa kolejne mogą poczekać.

---

## ZNALEZISKO 1 (pilne): dziewięć wierszy produkcyjnych stoi w trybie `webhook`

**Odczyt produkcji, nie przypuszczenie** (Tomasz wykonał zapytanie 19.08):

| marka | kanał | status | tryb |
|---|---|---|---|
| AGS | facebook, instagram, youtube, linkedin_page | ready | **webhook** |
| LYSY, PT, RDC, SDI, TNM | linkedin | ready | **webhook** |
| AGS | x, linkedin | active | post_queue |
| AGS | sprzedaz | draft | `none` |

Przewidywałem trzy takie wiersze. Jest dziewięć.

**Skąd się wzięły.** `brands_ui._add` wpisywał `publish_mode: webhook` na sztywno przy zakładaniu
marki. Każda marka założona po zakazie z 22.07 rodziła się w konfiguracji, która wywołała AP-307.
To nie jest teoria z czytania kodu, to pięć wierszy na produkcji.

**Czy to dziś strzela: NIE, sprawdzone.** `channels.for_item` bierze wyłącznie kanały
`supervised` o statusie `active` albo `draft`; `ready` pomija świadomie. Żaden aktywny kanał nie
ma `webhook`.

**Ale zapalnik jest jeden i banalny: zmiana statusu.** Wszystkie dziewięć mają wpisany
`adapter_path`, więc w chwili aktywacji delegat ma dokąd strzelić i AP-307 wraca co do znaku.

**Nowa bramka tych wierszy NIE chroni.** Ona pilnuje ustawiania trybu, a aktywacja kanału to
zmiana statusu. Nikt nie będzie musiał ustawić zabronionego trybu, bo on już tam stoi.

### Trzy opcje do rozstrzygnięcia

- **A. Wyprostować wszystkie dziewięć na `draft`.** Zapalnik znika. `draft` to tryb, który
  konsument i tak przyjmuje przy braku klucza, więc zachowanie kanałów się nie zmienia.
- **B. Wyprostować tylko te z `adapter_path`.** Węższe, ale w praktyce to te same wiersze.
- **C. Zostawić i oprzeć się na tym, że aktywacja jest świadoma.**

**Moja rekomendacja: A**, w tym samym oknie co rebuild B plus C. Powód: opcja C powtarza dokładnie
ten błąd, przez który powstało D-020 - **warunek "ktoś będzie uważał przy aktywacji" jest
założeniem, nie zabezpieczeniem** (AP-314). Różnica wobec dokumentu jest żadna.

To zmiana DANYCH produkcyjnych, więc obowiązuje RUNBOOK: kopia przed zmianą, policzenie wierszy
przed i po, bramka padająca zamknięta. Przygotuję skrypt, gdy zdecydujesz.

---

## ZNALEZISKO 2 (ta sama klasa co D-019, prawdopodobnie ostrzejsze)

Istnieje **drugi trwały magazyn reguł**, którego Z-3 nie obejmuje: `channels.config.rules`,
pisany narzędziem `subagent_remember_rule` z rozmowy, czytany przez `generate._channel_rules`
i wstrzykiwany do **każdego wariantu kanałowego** jako:

> `OWNER RULES FOR THIS ACCOUNT (obey strictly, override defaults if conflict): ...`

To jest wprost **polecenie posłuszeństwa z prawem nadpisania domyślnych zasad**. Do 20 pozycji
per kanał. Bez filtra językowego, który `style_learned` dostał 10.08 po AP-315. Bez rodzaju,
bez pochodzenia.

Mechanizm, przed którym zamknąłeś `style_learned`, w tym magazynie stoi otwarty i ma **mocniejsze
sformułowanie**. Nie zakładam, że Z-3 obejmuje go milcząco, więc nie tknąłem.

**Pytanie: czy rozciągamy D-019 na `channels.config.rules`, czy to osobna sprawa z własną wagą?**
Zwracam uwagę, że tu wyłączenie zapisu boli bardziej niż przy stylu, bo to jest droga, którą
konfiguruje się subagenta kanału.

---

## ZNALEZISKO 3 (drobne): kanał z trybem, którego nikt nie zna

`AGS/sprzedaz` ma `publish_mode = none`. Taki tryb nie pasuje do żadnej gałęzi w `dispatch_item`,
więc **nie robi nic i nie mówi, że nic nie robi**. Kanał jest w `draft`, czyli trafia do wyboru.

Rodzina "cisza wygląda jak sukces", w małej skali. Do rozstrzygnięcia, czy to celowy sposób
wyłączenia kanału (wtedy warto nazwać go wprost i obsłużyć), czy pomyłka.

---

## STAN PRZED TWOJĄ ODPOWIEDZIĄ

- Kod bloków B i C w repo, `1eb298b`, testy 35/35.
- **Rebuild NIE wykonany, produkcja nietknięta.**
- Bloki D i E czekają na okno n8n z Tomaszem, blok G na końcu.
- Blok A robi Tomasz ręcznie.
