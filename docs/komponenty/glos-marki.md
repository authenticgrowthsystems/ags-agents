# Komponent: GLOS MARKI (voice_dna_core + Voice Bible w promptach)

**STATUS GOTOWOSCI: LIVE, po naprawie ucinania 24/07 (czeka rebuild cm-agent)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Dostarcza modelowi GLOS Tomasza przy KAZDYM pisaniu tekstu: rdzen osobisty
(`voice_dna_core` - destylat 20 wywiadow) plus pelna `voice_bible` (~22 tys. znakow).
Zrodlem prawdy jest `brand_config` (kanon SSOT #71), nie plik w repo.

Jeden brand = jeden glos; nakladki marek (AGS/TNM/RDC) siedza w tresci Voice Bible,
nie w kodzie (kanon: glos RDC = TNM = AGS, bo to ten sam czlowiek).

## BUG NAPRAWIONY 24/07: glos szedl UCIETY (zgloszenie Managera)

Objaw: teksty lamaly zasady, ktore w Voice Bible stoja wprost (m.in. zakazane
slownictwo, rytm zdan), mimo ze kanon v2.1 obowiazuje od 06/07.

Przyczyna z kodu: DZIEWIEC miejsc wysylalo model do pisania z `voice_bible[:1200]`,
`[:1500]`, `[:2500]` albo `[:3000]` z 22 168 znakow. Wycinek to naglowek pliku
i pozycjonowanie - a wiec model dostawal polecenie "pisz tym glosem" BEZ zasad
pisania. Polecenie bez pokrycia. `voice_dna_core` nie wchodzil w ogole poza
sciezka sprzedazowa.

Naprawa: JEDNO wspolne zrodlo bloku glosu.

- `brand.voice_text(brand)` - caly rdzen + cala Voice Bible.
- `brand.voice_block(brand)` - ten sam tekst jako blok `system` oznaczony
  `cache_control: ephemeral` (prompt-cache; blok jest bajtowo staly, wiec
  powtorne wywolania placa 10% za wejscie).
- `brand.system_blocks(brand)` (glowna generacja) korzysta z tego samego bloku.

Wszystkie dziewiec miejsc uzywa teraz `voice_block`. Wyciek sekcji po slowach
kluczowych zostal sprawdzony i ODRZUCONY juz przy sciezce sprzedazowej: z 37
naglowkow zywej Voice Bible dopasowaly sie dwa, a listy zakazanego slownictwa
maja naglowki po angielsku, wiec wypadlyby. Cichy dobor sekcji to ta sama klasa
bledu, co ucinanie.

## Wejscia-wyjscia i tabele

- `brand_config` (per brand): `voice_bible` (wersjonowana bumpem, UNIQUE
  (brand_id, config_key)), `voice_dna_core`, `banned_vocab`, `style_learned`.
- `brand_strategy`: audytorium i filary do bloku roli.
- `content_items.voice_hash` - md5 Voice Bible uzytej przy generacji (audyt
  i odtwarzalnosc: po zmianie glosu wiadomo, ktore teksty powstaly na starym).

## Punkty zaczepienia w kodzie

- `cm-agent/app/brand.py`: `load_brand` (czyta takze `voice_dna_core`),
  `voice_text`, `voice_block`, `system_blocks`.
- Konsumenci bloku glosu: `generate` (canonical, warianty, komentarz z wizji),
  `conversation` (propozycje komentarzy, odpowiedzi na DM), `planner` (plan
  tygodnia, inny kat), `matreview` (inny kat z karty), `proactive` (propozycje
  do luk kadencji), `sunday_brief` (podklad niedzielny).
- Sciezka sprzedazowa ma wlasny sklad glosu (`sales._voice_for_outreach`), bo
  dokłada wzorce z wiadomosci Tomasza (`sales_knowledge.material_type =
  'outreach_example'`) - ta sama zasada calosci, inne zrodla.
- Test: `cm-agent/tests/test_import_smoke.py` sprawdza, ze blok glosu niesie
  CALA Voice Bible i CALY rdzen oraz ma wlaczony prompt-cache.

## Voice Bible v2.2 (24-25/07) - warstwy compliance

Voice Bible v2.2 dodaje sekcje 14-23 (canonical). W KODZIE zyja jako warstwy `compliance.enforce`
(NIE w agent_prompts - ta tabela to rejestr, kod jej nie czyta):
- **Sekcja 14 abstract-tech** (Ottley): hard block slownictwa produktowego w outreach -
  `sales._ZAKAZANE_PRODUKTOWE` + auto-odrzut w gotowcu (od 24/07, pkt 3 paczki).
- **Sekcja 20 interpunkcja PL**: `compliance.pl_comma_flags` (deterministyczna FLAGA w karcie
  TNM/RDC, od 24/07 pkt 8).
- **Sekcja 23 TEST SZATNI** (25/07): `compliance.test_szatni` - HARD (LLM Haiku, przepisanie
  kalki z angielskiego na polski MOWIONY) dla marek PL w `enforce` ORAZ dla kazdego gotowca
  sprzedazowego PL w `sales._draft_outreach`. Wezsza warstwa niz `polish_pl`: lapie zdania
  POPRAWNE, ktore brzmia jak slajd (aforyzm "Kto...ten", rzeczownik odczasownikowy, zaimek bez
  odniesienia, zdanie bez czasownika). Origin: korekta Tomasza na mailu do Dudzika. Test:
  cm-agent/tests/test_voice_v22.py.
- **TAP-TEST SEKCJI 23 NA ZYWO (27/07, polecenie Managera) - PRZESZEDL i znalazl DWIE wady.**
  Dwa przypadki: gotowiec PL napchany kalkami oraz czysty mail sprzedazowy PL (drugi celowo,
  zeby zmierzyc PRECYZJE - falszywa poprawka jest tu rownie kosztowna jak przeoczona kalka).
  - **Kalki: wyciete wszystkie.** "adresujemy wyzwania", "w obszarze", "dedykowane rozwiazanie
    dostarcza wymierne rezultaty w oparciu o najlepsze praktyki", "zaimplementujemy",
    "na poziomie procesu", "synergie", "wartosc dodana dla Panstwa organizacji" - zniknely.
  - **WADA 1: bramka zepsula ODMIANE.** Wynik zaczynal sie od "pomagamy szkoly tanca" zamiast
    "pomagamy szkolom tanca". Bramka pilnujaca polszczyzny sama zrobila blad przypadka.
  - **WADA 2: bramka wygladzila KONKRET.** W czystym mailu "Znam ten moment z wlasnej szkoly"
    zamienila na "Znam to dobrze z wlasnej szkoly" - ogolniej, mniej Tomaszowo. Prompt mowil
    "nie zmieniaj sensu, tonu ani dlugosci", ale nie mowil "nie poprawiaj na sile".
  - **Poprawka (27/07):** dwie reguly dopisane do `TEST_SZATNI_PROMPT` DOSLOWNIE z tych dwoch
    bledow, nie z teorii: (a) odmiana jest wazniejsza niz kalka, bo kalka brzmi korporacyjnie,
    a blad przypadka brzmi jak brak wyksztalcenia; (b) zdanie, ktore juz brzmi jak mowa, wraca
    bajt w bajt.
  - **MINA (AP-306, trzeci raz w repo):** pierwsza proba tap-testu padla na braku klucza, bo
    jednorazowy `docker exec python -` NIE przechodzi przez `worker._load_secrets`. Poprawna
    forma doklada `config.ANTHROPIC_API_KEY = db.get_secret("anthropic_api_key")` na starcie
    (wzorzec z `bulk_polish.py`). Wczesniejsze wystapienia: drift_check 05/07, bulk_polish 06/07.
- Deploy tresci: `cm-agent/db/032_voice_bible_v22_nowa.sql` (bump version+1 od aktualnej,
  guard idempotentny po 'SEKCJA 23', dollar-quote). UWAGA WERSJI: db/022 to STARA v2.2 (12/07,
  inna tresc) - jesli byla wdrozona, baza ma juz v4 i nowa idzie na v5 (sonda rozstrzyga).

## Kanony ktore go dotycza

- Glos = jeden DNA + nakladki marek (12/07).
- SSOT w bazie, nie w pliku (#71); zmiana glosu = UPDATE z bumpem wersji,
  nigdy nowy wiersz.
- Nie tnij glosu, zeby oszczedzic tokeny. Od tego jest prompt-cache. Ciecie
  oszczedza grosze i kosztuje marke.

## Znane pulapki

- Voice Bible w bloku `system` MUSI byc bajtowo stabilna, inaczej prompt-cache
  nie trafia. Doklejanie do niej zmiennych rzeczy (data, stan kolejki) kasuje
  oszczednosc - zmienne ida do wiadomosci uzytkownika, nie do bloku glosu.
- `brand_config` ma UNIQUE (brand_id, config_key): nowa wersja to UPDATE
  + `version+1`, a nie INSERT (AP-304 recydywa z 12/07).
- Marka bez `voice_bible` = generacja bez glosu. `/brand_config <marka>`
  pokazuje to wprost ("BRAK").
