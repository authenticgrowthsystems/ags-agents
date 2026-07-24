# RAPORT DO MANAGERA - domkniecie paczki #1 + mini-brief #1.2 (praca 24/07 wieczorem, nazwa wg DoD)

## Jednym zdaniem

Paczka #1 zamknieta w calosci, pieciu odpowiedziom z mini-briefu #1.2 odpowiada kod, a przy
okazji zamknal sie najstarszy dlug techniczny dnia: kaskada Researchera czyta wreszcie strone
badanego podmiotu, a glos marki przestal wychodzic ucięty w dziewieciu miejscach.

## Twoje odpowiedzi -> co z nimi zrobilem

| Punkt | Decyzja | Stan |
|---|---|---|
| P1 tier 'Inne' | dodac, nie scinac, nie migrowac 45 legacy | **LIVE** (DDL 031, CHECK poszerzony; w bazie sa juz pierwsze kontakty z tierem Inne) |
| P2 dm_history | fail-closed na engagement_log per contact_id, bez nowej kolumny | **LIVE** (crm.dm_history + crm.fail_closed_note, indeks w DDL 030) |
| P2 Sekcja 21 | flaga `engagement_log_checked_for_contact_id` | **SQL GOTOWY**, chirurgiczny: docs/ops/voice_bible_sekcja21_24072026.sql |
| P3 cache semantyczny | globalnie OFF | **WDROZONE** (.env + rebuild) + druga warstwa w kodzie |
| P4 auto_image X | wlaczyc dla subagenta X | **WDROZONE** (flaga w channels.config) |
| P5 cichy except | kanon + sprint domykajacy | **ZROBIONE** (AP-306 rozszerzony, 17 miejsc uglosnionych) |
| BONUS voice_bible[:2000] | usunac ciecie, dodac voice_dna_core | **ZROBIONE, ale bylo gorzej niz w zgloszeniu** (nizej) |

## BONUS okazal sie najwiekszym znaleziskiem dnia

Zglosiles jeden slice. Grep pokazal DZIEWIEC: `[:1200]`, `[:1500]`, `[:2500]`, `[:3000]` -
w propozycjach komentarzy, odpowiedziach na DM, komentarzu z wizji, planerze tygodnia, dwoch
sciezkach "inny kat", propozycjach do luk kadencji i w podkladzie niedzielnym. Z 22 168 znakow
Voice Bible model dostawal naglowek pliku i pozycjonowanie, po czym polecenie "pisz tym glosem".
`voice_dna_core` nie wchodzil nigdzie poza sciezka sprzedazowa (naprawiona rano).

To tlumaczy, dlaczego kanon v2.1 obowiazuje od 06/07, a teksty i tak lamaly zasady z sekcji 4.x:
tych zasad w oknie modelu nigdy nie bylo.

Naprawa: jedno zrodlo `brand.voice_block(brand)` = caly rdzen + cala Voice Bible w bloku
oznaczonym do prompt-cache (blok jest bajtowo staly, wiec powtorne wywolania placa 10% za
wejscie). Wybieranie sekcji po slowach kluczowych zostalo sprawdzone i odrzucone juz przy
sprzedazy: z 37 naglowkow zywej Voice Bible dopasowaly sie dwa, a listy zakazanego slownictwa
maja naglowki po angielsku, wiec wypadlyby. Cichy dobor sekcji to ten sam blad co ciecie.

Nowy komponent w dokumentacji: docs/komponenty/glos-marki.md.

## Czego nie bylo w paczce, a wyszlo z zycia tego samego wieczoru

**1. Post na X wyszedl z linia "# X Adaptation".** Tomasz zlapal to na zrzucie z okna edycji.
Model opisywal, CO robi, a opis szedl do kolejki doslownie; ani X, ani LinkedIn nie renderuja
markdown, wiec to nie formatowanie, tylko smiec widoczny dla klienta. Straznik stanal w JEDYNYM
miejscu zapisu do post_queue (channels.stage_variant), wiec kazda przyszla sciezka dostaje go za
darmo. Wiersze sprzed poprawki wyczyszczone SQL-em; jeden post (19:58) zdazyl wyjsc z naglowkiem.

**2. Kaskada Researchera nie czytala strony badanego podmiotu.** Twardy dowod: adapter
"firecrawl" wola `api.firecrawl.dev/v2/search/research/papers` - to wyszukiwarka PRAC NAUKOWYCH,
nie crawler. Stad osiem linkow z arXiv w researchu o szkole tanca. Kaskada dostala natywne
zrodlo `site` (Python, bez n8n, bez klucza, bez kosztu): warianty adresu, strona glowna + do 3
podstron, dowod nr 1 = krotki wyciag kontaktowy, ktory ZAWSZE miesci sie w limicie syntezy.
Rusza tylko wtedy, gdy zapytanie niesie adres. Obejscie w sprzedazy zostaje, bo pelni inna
funkcje (wypelnia kolumny lejka), ale przestalo byc jedyna sciezka.

**3. Trzy pozycje dlugu z listy wieczornej:** adres prospekta wskazywal archiwum autora zamiast
domeny (Stepownia), osoba decyzyjna nie byla odrozniana od instruktora, Sprzedawca nie widzial
zrzutow ekranu. Wszystkie zamkniete, kazda z testem.

## Regula, ktora proponuje podniesc do kanonu

Trzy z dzisiejszych bledow to JEDNA klasa: **poprawka zrobiona w jednym miejscu, gdy ta sama
wada zyla w wielu**. Glos ucinany w 9 miejscach, tier przepisany w 4, cichy except w 19.
AP-307 mowi o konsumentach kontraktu; to jest jego blizniak: **zanim uznasz poprawke za
zrobiona, policz, ILE MIEJSC ma te sama wade** (`grep`, nie pamiec). Dopisalem to do przegladu
AP-306; jesli uznasz, ze zasluguje na wlasny numer, nadaj go.

## Dowody

Cztery zestawy testow lokalnych, wszystkie PASS, bez bazy, bez sieci, bez LLM:
- `ags-researcher/tests/test_site.py` - 26 (adres z zapytania, warianty www/http, dowody, brzegi),
- `cm-agent/tests/test_paczka1.py` - 45 (interpunkcja, parser KPI, fail-closed, skala tierow),
- `cm-agent/tests/test_meta_naglowek.py` - 29 (w tym 5 przypadkow "NIE ruszaj tresci"),
- `cm-agent/tests/test_sales_prospekt.py` - 13 (adres prospekta, decydent vs instruktor),
- `cm-agent/tests/test_import_smoke.py` - 21 (import wszystkich modulow + kontrola pelnego glosu).

Dowody produkcyjne: kolejka X bez meta-naglowkow po sprzataniu, pierwsze kontakty z tierem
'Inne' w bazie, `/health` obu kontenerow ok po rebuildzie.

## DoD paczki #1 - stan pozycja po pozycji

- masterprompty czatowe: **ZROBIONE** (LinkedIn v3.2, X v3.1; Tomasz musi wkleic je do projektu
  czatowego ponownie, inaczej czat pracuje na starej wersji),
- tabela channel_kpi_snapshots: **LIVE** (DDL 030; pierwsza linia `kpi_snapshot` czeka na
  pierwszy eksport analityczny),
- contacts.icp_tier + 'Inne' bez migracji: **LIVE**,
- contacts.who_is_who JSONB: **LIVE** (odczyt w naglowku propozycji i gotowca),
- sales_agent auto-odrzut slownictwa: **LIVE** (commit babfe03, rano),
- AP-306.md canonical: **ZROBIONE**,
- cache prospect research OFF: **WDROZONE**,
- auto_image X ON: **WDROZONE**,
- Voice Bible v2.2 z fix truncation: **fix truncation ZROBIONY W KODZIE** (to byl bug loadera,
  nie tresci Biblii); wsad v2.2 i Sekcja 21 po Twojej stronie - SQL na flage czeka gotowy.

## Otwarte (potrzebuje Twojej decyzji)

1. **Kto zapisuje `who_is_who`.** Kolumna i odczyt sa, drogi zapisu nie ma. Propozycja: linia
   `kto_jest_kim | osoba | rola=... | wplyw=... | zrodlo=...` w RAPORCIE PRACY, tym samym
   deterministycznym parserem co `kpi_snapshot`. Jeden dzien pracy.
2. **Migracja legacy tierow** (Watch/Premium/Mid -> Inne): zgodnie z Twoja decyzja NIE ruszam,
   ale zostaje jako osobny sprint post-Adamietz.
3. **Anglicyzmy w promptach wewnetrznych:** poprawione teksty widoczne dla Tomasza i polskie
   instrukcje dla modelu (follow-up -> nastepny kontakt, deal -> sprawa, lead -> zapytanie,
   insight -> wniosek). NIE ruszalem nazw narzedzi, kolumn i tokenow parsera - tam angielski
   jest czescia kontraktu, nie stylem.
