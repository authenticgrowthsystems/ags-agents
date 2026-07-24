# BE PACZKA #1 od Managera AGS - 24/07/2026 (sprint 20-26/07, 8 zadan)

Przekazana przez Tomasza w oknie BE 24/07 ~18:20. Ten plik = tresc paczki + TRIAGE
inzynierski (co da sie zrobic wprost, co wymaga korekty, co juz jest zrobione).

## Priorytety wg Managera

- BLOCKER (Piotr call-back + Adamietz, do 25/07 rano): **pkt 3**
- BLOCKER (nastepna sesja czatu, dzis wieczor albo jutro rano): **pkt 1 + 2**
- Sprint do 26/07: pkt 4, 5, 6, 7, 8

## Zadania i status inzynierski

### 1. Eksport analityczny do raportu (masterprompty v1.1 / v2.1, tabela channel_kpi_snapshots)
Sekcja "Reakcja na eksport analityczny" w masterpromptach czatowych, parser typ `kpi_snapshot`,
nowa tabela + sync_registry + SCHEMA update. Uwaga: parser raportu pracy jest deterministyczny
(bez LLM) - nowy typ linii trzeba dopisac po stronie serwera, inaczej czat wysle blok, ktorego
nikt nie zrozumie. DDL: nastepny wolny numer to **030**.
**Status: ZROBIONE 24/07 (kod + DDL 030, czeka psql + rebuild).** Sekcja w OBU masterpromptach
(X v3.1, LinkedIn v3.2), parser `_kpi_fields` z testami lokalnymi, tabela channel_kpi_snapshots
z okresem (dzien/7d/28d/90d) i UPSERT-em z COALESCE, wiersz sync_registry (enabled=FALSE),
SCHEMA zaktualizowany. Odczyt wraca do czatu sekcja "METRYKI KANALU" w stanie gry
(reports._kontekst_kpi) - inaczej liczby wpadalyby do bazy i nikt by ich nie ogladal.

### 2. Weryfikacja tozsamosci cross-platform bez web_search
Sekcja w LINKEDIN_AGS v1.1: zrzut profilu X (bio + link w bio) zamiast web_search.
Dowod produkcyjny 24/07 potwierdza teze: web_search zwraca losowe osoby o podobnym nicku.
**Status: ZROBIONE 24/07.** Sekcja w LinkedIn v3.2 ORAZ w X v3.1 (kanon parytetu - luka
u jednego kanalu to obowiazek uzupelnienia). Werdykt trzema stanami (potwierdzona /
z zastrzezeniem / niepotwierdzona) - ta sama skala, co bramka tozsamosci Sprzedawcy,
zeby jedna rzecz nie miala dwoch jezykow. Wynik wraca linia `nowa_osoba` z handlem
drugiego kanalu w bio (mape tozsamosci trzyma serwer, kanon WHO IS WHO).

### 3. Auto-reject vocab w Sprzedawcy + Voice Bible +8 banned (BLOCKER)
Zakaz slow: automatyzacje, workflows, systemy AI, integracje, AI systems, AI workflows,
agents platform, custom AI. Retrieval o vocab shift per ICP ("utrzymuje Ci klientow, ktorzy
odchodza" > "buduje Ci system AI"). **Status: DO ZROBIENIA - to jest blocker rozmowy z Piotrem,
wiec idzie pierwsze.** Czesciowo pokryte kanonem "NARZEDZIA NIE UJAWNIAMY" (nazwa platformy),
ale lista slow jest szersza i dotyczy SPOSOBU mowienia o produkcie, nie tylko nazwy narzedzia.

### 4. contacts.icp_tier - piaty tier "Inne"
**Status: WYMAGA KOREKTY ZAKRESU.** Sonda 24/07 (177 kontaktow):
- dzisiejszy CHECK dopuszcza 9 wartosci: Buyer, Peer, Competitor, Partner + legacy
  Premium, Mid, Free, Watch, N/A,
- w bazie zyja: Peer 44, **Watch 37**, Buyer 18, **Premium 7**, Competitor 6, Partner 5,
  **Mid 1**, puste 59.
Twarde sciecie do 5 wartosci (Buyer/Peer/Partner/Competitor/Inne) **wywalilo by 45 wierszy**
na CHECK. Rekomendacja: DODAC 'Inne' do istniejacej listy i osobno zdecydowac, czy legacy
(Watch/Premium/Mid/Free/N/A) migrujemy na nowa skale, czy zostawiamy jako historie.
Decyzja nalezy do Tomasza/Managera - nie ruszam bez niej.

### 5. contacts.who_is_who JSONB
**Status: KOLUMNA ZROBIONA 24/07 (DDL 030), ZAPIS DO DECYZJI MANAGERA.** ALTER TABLE
+ komentarz kolumny + odczyt w `crm.relation_context` (rola i wplyw widac w naglowku
propozycji i gotowca, czyli tam, gdzie sie pisze do czlowieka). Kontrakt pola:
role / influence_level (decydent|wplywowy|uzytkownik|nieznany) / relationship_stage /
source_of_data / notes.
OTWARTE: kto ZAPISUJE. Dzis: Sales Manager L1 z czatu przez SQL Tomasza. Propozycja BE:
nowa linia raportu `kto_jest_kim | osoba | rola=... | wplyw=... | zrodlo=...` (ten sam
deterministyczny parser co `kpi_snapshot`, jeden dzien pracy). Kolumna bez drogi zapisu
zostanie pusta, a pusta kolumna klamie tak samo jak brak kolumny.

### 6. SELECT piapiasilva
**Status: WYKONANE 24/07 (read-only sonda).** Wynik:
- `contacts.id` = 896d2232-0aa9-4ae7-914f-2e79fbf2fc2b, `name` = piapiasilva,
  `handles` = {"linkedin": "piapiasilva"}, `icp_tier` = Buyer,
  `relationship_stage` = commented, `last_interaction_date` = 22/07/2026, notatki puste.
- **KLUCZ DO ODNALEZIENIA (wazniejszy niz handle):** engagement_log 22/07 21:20 niesie wpis
  "Pia Silva, boutique branding, Bad Ass Your Brand". Prawdziwe nazwisko to **Pia Silva**,
  autorka ksiazki "Badass Your Brand", branding butikowy. Szukac po nazwisku i firmie,
  nie po handle - handle mogl sie zmienic.
- 22/07 22:19 poszedl do niej komentarz (status sent), ten sam, ktorego uzywamy dzis jako
  wzorca glosu w outreachu.
- UWAGA: kolumna klucza w `contacts` to **`id`**, nie `contact_id` (AP-304 - ten sam blad
  zlapal mnie 24/07 w naglowku gotowca).

### 7. Sales Manager L1: sprawdz historie DM PRZED tier='out_of_icp'
Fail-closed, gdy `dm_history` niesprawdzone; dotyczy kontaktow 1. stopnia z
`relationship_stage != 'cold'`. Uwaga: `contacts` nie ma kolumny `dm_history` - historia DM
zyje w `engagement_log` (marker [DM] w notes, contact_id).
**Status: ZROBIONE 24/07 na engagement_log** (kolumny `dm_history` NIE dopisujemy: duplikat
historii natychmiast rozjechalby sie z logiem). `crm.dm_history` + `crm.fail_closed_note`
wpiete w OBA miejsca, ktore proponuja tier (karta z raportu pracy i karta ze zrzutu profilu -
AP-307: kazdy zywy konsument w tym samym buildzie). Mechanizm: tier wykluczajacy z lejka
(Competitor / out_of_icp) przy istniejacej historii rozmow traci REKOMENDACJE, a karta
niesie dowod (ile wpisow DM, kiedy ostatni, jakie stadium). Skutek uboczny jest celowy
i wazniejszy niz sama karta: `decisions.ask` bez rekomendacji NIE decyduje sam nawet
w trybie semi_autonomous (crm_tier jest na semi od 22/07, decyzja #90) - wiec wykluczenie
z lejka zawsze przechodzi przez Tomasza. Po stronie czatu ta sama regula w obu
masterpromptach. Indeks idx_eng_log_contact_action w DDL 030.

### 8. Heurystyka interpunkcji PL (flag, nie hard-block)
Przecinek przed: ze, zeby, ktory/ktora/ktore, gdy, jesli, bo. Dla brand_id IN ('tnm','rdc'),
w matreview jako ostrzezenie. Naturalne miejsce: `compliance.py` obok `polish_pl`.
**Status: ZROBIONE 24/07.** `compliance.pl_comma_flags` (deterministycznie, zero LLM, zero
kosztu) + linia ⚠️ INTERPUNKCJA w karcie materialu dla TNM/RDC, max 3 fragmenty, liczone
z PELNEJ tresci (nie z przycietego podgladu). Heurystyka celowo ostrozna: poczatek zdania,
istniejacy przecinek i zbitki "mimo ze" / "nawet jesli" / "w ktorym" nie sa zglaszane -
falszywy alarm w kazdej karcie skonczylby sie ignorowaniem flagi. 19 przypadkow testowych
(6 pozytywnych, 10 negatywnych, 3 brzegowe) w cm-agent/tests/test_paczka1.py.

## Uwagi calosciowe

- **Pkt 4 nie wchodzi bez decyzji** (patrz wyzej): zakres z paczki lamie zywe dane.
- Pkt 1, 5, 7 dotykaja DDL - jesli robimy razem, to JEDEN plik `030_*.sql`, psql PRZED rebuildem.
- Pkt 2 i 3 to edycje promptow: najszybszy zysk, zero ryzyka schematu, i pkt 3 jest blockerem
  rozmowy z Piotrem - stad kolejnosc realizacji: **3, 2, 8, potem 1+5+7 (jeden DDL), pkt 4 po decyzji**.
- Raport zwrotny wg DoD: `docs/cm/RAPORT_do_Managera_25072026_paczka1.md`.

## STAN NA 24/07 WIECZOR (po wykonaniu)

7 z 8 punktow zamknietych: 3 (babfe03), 6 (sonda), 2, 8, 1, 5 (kolumna), 7.
Zostaje **pkt 4** - czeka na decyzje Tomasza, bo twarde sciecie tierow wywala 45 zywych
wierszy. Pkt 5 ma kolumne i odczyt, ale otwarta droge ZAPISU (propozycja: linia
`kto_jest_kim` w raporcie pracy).
NIE WDROZONE JESZCZE NA SERWER: DDL 030 + rebuild (paczka lezy w repo, kolejnosc:
push -> psql 030 -> rebuild -> tap-testy). Do czasu psql sekcja METRYKI KANALU
w stanie gry jest cicha (brak tabeli = pusta lista, nie awaria) - to celowe.
