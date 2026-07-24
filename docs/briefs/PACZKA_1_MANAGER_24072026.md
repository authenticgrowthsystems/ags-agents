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
nowa tabela + sync_registry + SCHEMA update. **Status: DO ZROBIENIA.** Uwaga: parser raportu
pracy jest deterministyczny (bez LLM) - nowy typ linii trzeba dopisac po stronie serwera,
inaczej czat wysle blok, ktorego nikt nie zrozumie. DDL: nastepny wolny numer to **030**.

### 2. Weryfikacja tozsamosci cross-platform bez web_search
Sekcja w LINKEDIN_AGS v1.1: zrzut profilu X (bio + link w bio) zamiast web_search.
**Status: DO ZROBIENIA, najtansze z calej paczki** (edycja jednego pliku masterpromptu).
Dowod produkcyjny 24/07 potwierdza teze: web_search zwraca losowe osoby o podobnym nicku.

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
**Status: SPRAWDZONE - kolumny NIE MA** (`information_schema` = 0 trafien). Trzeba ALTER TABLE
(DDL 030 razem z pkt 1 albo osobno) + aktualizacja workflow Sales Manager L1:
role / influence_level / relationship_stage / source_of_data / notes.

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
`relationship_stage != 'cold'`. **Status: DO ZROBIENIA.** Uwaga: `contacts` nie ma kolumny
`dm_history` - historia DM zyje w `engagement_log` (action_type dm_*, contact_id).
Regule trzeba oprzec na engagement_log albo dopisac kolumne w DDL 030.

### 8. Heurystyka interpunkcji PL (flag, nie hard-block)
Przecinek przed: ze, zeby, ktory/ktora/ktore, gdy, jesli, bo. Dla brand_id IN ('tnm','rdc'),
w matreview jako ostrzezenie. **Status: DO ZROBIENIA.** Naturalne miejsce: `compliance.py`
obok `polish_pl` (filtr czystej polszczyzny juz tam mieszka).

## Uwagi calosciowe

- **Pkt 4 nie wchodzi bez decyzji** (patrz wyzej): zakres z paczki lamie zywe dane.
- Pkt 1, 5, 7 dotykaja DDL - jesli robimy razem, to JEDEN plik `030_*.sql`, psql PRZED rebuildem.
- Pkt 2 i 3 to edycje promptow: najszybszy zysk, zero ryzyka schematu, i pkt 3 jest blockerem
  rozmowy z Piotrem - stad kolejnosc realizacji: **3, 2, 8, potem 1+5+7 (jeden DDL), pkt 4 po decyzji**.
- Raport zwrotny wg DoD: `docs/cm/RAPORT_do_Managera_25072026_paczka1.md`.
