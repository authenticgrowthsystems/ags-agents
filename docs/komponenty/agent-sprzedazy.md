# Komponent: AGENT SPRZEDAZY (prospect research, outreach HITL, lejek, baza wiedzy)

**STATUS GOTOWOSCI: W BUDOWIE (kod na build/sprzedawca; czeka psql 027 + rebuild cm-agent + patch n8n + tap-testy DoD)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Nowy agent w istniejacym frameworku subagentow: partner strategiczny Tomasza w sprzedazy
(kogo targetowac, jak, kiedy follow-up, kiedy domykac) + wykonawca operacyjny. Zna macierz
gotowosci produktu (co WOLNO sprzedawac), pelny cennik pricing_tiers (Pakiety PL 1-3 =
TOP OFFERING: DFY "system retencji klientow"), sales_playbook, ICP i Voice Bible. Zleca
research prospektow Researcherowi (tier medium ~1-2 PLN; kanon kosztowy 20/07: critical
NIGDY przez API - glebokie przeswietlenia recznie na abonamentach), pisze outreach
jako GOTOWIEC (HITL - NIC nie wysyla sie samo), prowadzi lejek sales_pipeline i uczy sie
z materialow Tomasza (sales_knowledge z embeddingami). Frameworki Anthropic sales skills
(draft-outreach, account-research, pipeline-review) zdestylowane w promptcie systemowym.

## Route i wejscia

```
/agents -> pozycja "AGS sprzedaz" (menu n8n buduje sie DYNAMICZNIE z channels
  supervised=true AND status IN ('active','draft'); wiersz AGS/sprzedaz z DDL 027,
  config.agent_kind='sales') -> active_agent='subagent:AGS:sprzedaz'
conversation.handle:
  - sales.try_command PRZED LLM (wzorzec _config_route), z KAZDEGO agenta:
    /prospect <nazwa|URL>  -> research medium + wpis w lejku (deterministycznie)
    /pipeline              -> widok lejka (deterministycznie)
    /oferta                -> pelny cennik; /oferta <prospekt> -> rekomendacja tieru (LLM)
    /add_sales_material [hint] -> uzbrojenie na 2h: nastepny dokument .md/.txt/.pdf
      albo wklejka >=200 znakow -> chunk -> embedding -> sales_knowledge
  - active == 'subagent:AGS:sprzedaz' -> sales.handle_chat (petla agentowa 5 krokow,
    Opus przez cm_tier_sales_chat, paragony narzedzi jak u subagentow)
Dokumenty: n8n document_text (po patchu takze .pdf <=8MB) -> /docmsg ->
  handle_document (PDF: ekstrakcja pypdf) -> [DOKUMENT: nazwa] -> aktywny agent /
  uzbrojony ingest materialu.
```

## Narzedzia (9)

prospect_research (Researcher /request, from='sales-agent', default tier medium,
critical zablokowany w kodzie; payload.model_tier = NAZWA MODELU (mapowanie _TIER_MODEL:
medium->sonnet) - poziomy bylyby zignorowane; async, wynik tickiem),
prospect_results (claims z linkami), draft_outreach (email/linkedin_dm/x_dm w Voice
Bible; gotowiec = naglowek + CZYSTA WKLEJKA osobna wiadomoscia, wzorzec comment-radar;
zapis engagement_log status 'proposed' + notatka lejka), offer_for (pakiet danych:
lejek+research+cennik -> model rekomenduje OD GORY), pipeline_view, pipeline_add,
pipeline_move (paragon 📊 przy kazdej zmianie), sales_knowledge_search (pgvector,
fallback ILIKE), outreach_sent (propozycja -> 'sent', follow-up +3 dni).

## Wejscia-wyjscia i tabele (DDL 027)

- `sales_pipeline`: id UUID, contact_id FK contacts, prospect_name/url, stage CHECK
  (prospect/qualified/proposal/negotiation/won/lost), offer_tier, value+currency,
  next_followup_at, research_job_id TEXT, notes (append z timestampem, LEFT 4000), source.
- `sales_knowledge`: material_type CHECK (book/technique/case_study/framework/script/
  recording/other), material_name, chunk_no, content_excerpt, embedding vector(1536)
  (OpenAI text-embedding-3-small, jak published_posts; NULL dozwolony), tags[].
- `agent_registry`: wiersz 'sales-agent' z ARRAY['low','medium','critical'].
- `channels`: wiersz (AGS,'sprzedaz','draft',supervised=true, agent_kind='sales',
  welcomed=true) - TYLKO po to, zeby /agents go pokazal. NIE aktywowac w ⚙️ Cele!
- `engagement_log`: outreach drafty (action_type 'other', agent 'AGS:sprzedaz',
  status proposed->sent).
- `brand_config`: sales_pending_material (stan /add_sales_material, TTL 2h),
  cm_tier_sales_chat / cm_tier_sales_outreach / cm_tier_sales_research_summary
  (nadpisania modelu przez /set).

## Punkty zaczepienia w kodzie

- `cm-agent/app/sales.py`: try_command, handle_chat, _dispatch, _prospect_research,
  _draft_outreach, pipeline_text, ingest_material, pdf_text, tick (RESPONSE Researchera
  -> _summarize_research -> Telegram + notatka lejka).
- `cm-agent/app/conversation.py`: hook w handle() (try_command + galaz AGENT_KEY),
  handle_document (galaz PDF), _channels_snapshot (wyklucza agent_kind='sales').
- `cm-agent/app/worker.py`: sales.tick() w petli.
- Wykluczenia agent_kind='sales' takze w: planner._cadence_text, planner (valid_channels),
  reports.run_all, proactive.check_gaps.
- n8n: patch `n8n-workflows/patches/hitl-sales-commands-20072026.cjs` (przepustka
  /prospect /oferta /pipeline /add_sales_material + .pdf w Detect Update Type).

## Kanony ktore go dotycza

- HITL ZAWSZE: zaden outreach/email nie wychodzi sam - gotowiec, Tomasz wysyla recznie.
- NARZEDZIA NIE UJAWNIAMY (GHL): sprzedajemy REZULTAT ("system retencji klientow").
- REGULA PRAWDY: Stage 0-1 - zero zmyslonych case studies/referencji; fakt bez zrodla
  = "(do weryfikacji)". Zero /apply. Waluta: PL=PLN, zagranica=USD.
- Wartosc przed cena; cennik od gory (premium pierwsze). TWARDA ZASADA WYKONANIA
  (paragon narzedzia albo sie nie stalo).

## Wykluczenie: konflikt interesow RDC (kanon 24/07)

- **Kryterium jest JEDNO (doprecyzowanie Tomasza 24/07): miasto OPOLE.** Sprzedawca nie
  prowadzi szkol, studiow i zespolow tanecznych z Opola. Reszta wojewodztwa opolskiego,
  caly Slask, Dolny Slask i reszta Polski sa w ICP.
- Poprzednia wersja miala DWA kryteria naraz (lista miast + promien 50 km) i zdanie "Slask
  jest OK". Sprzedawca w jednej turze orzekl najpierw, ze Ornontowice sa poza strefa, a
  potem, ze sie lapia - i zablokowal gotowy outreach (dowod: sesja 24/07 13:29). Regula z
  dwoma kryteriami nie jest regula. Nie licz odleglosci.
- Prospekt pod regula: bez researchu i outreachu, stage 'lost' + notatka "konflikt interesow
  RDC", jawny komunikat do Tomasza. Regula wygasa, gdy Tomasz zamknie studio.
- Zapis w prompcie: sales._RULES (pierwsza zasada).

## Podsumowanie klienta / dziennik kapitanski (22/07, kanon Sales Manager P1; v2 po tap-tescie)

- `/dziennik <klient>` (route deterministyczny + przepustka n8n) i narzedzie
  `dziennik_klienta`: WIDOK na kartoteke (sales_pipeline.notes) + interakcje
  (engagement_log, match po nazwie prospekta). Dlugi = plik .md. Zrodla append-only.
- v2 (feedback Tomasza): naglowek "PODSUMOWANIE KLIENTA" (nie "dziennik kapitanski"),
  pelna polszczyzna; sekcja NAJWAZNIEJSZE na gorze (etap, nastepny krok, OBOWIAZUJACA
  STRATEGIA wyciagana z notatek, ostatni ruch); os czasu = krotkie wpisy <=220 znakow
  ze zdjetym markdownem; interakcje <=160/linia; stopka wskazuje pelne tresci.
- Higiena zapisu: `_append_notes` przycina pojedynczy wpis do 600 znakow - bloby
  (caly research) wypychaly historie z limitu 4000 (ucieta strategia "Sekwen").
- Kanon i decyzje Managera (progi 5/20, kolejnosc P1):
  docs/product/SALES_MANAGER_ARCHITEKTURA_22072026.md.

## Tozsamosc prospekta w zapytaniu badawczym (fix 24/07)

- `_prospect_research` bierze URL z LEJKA, gdy wiadomosc go nie niesie (`url or
  row['prospect_url']`), i dopisuje nowy adres do wiersza, jesli go tam brakowalo.
  Bez tego powtorne `/prospect <nazwa>` szlo bez `strona:` i Researcher badal inny
  podmiot o podobnej nazwie. Dowod: job 0602c6a7 - "Dance Company La Cultura"
  (Sosnowiec, lacultura.pl) wrocil jako Cultura Dance Arts w Pawtucket RI.
- `_research_query` zada POTWIERDZENIA TOZSAMOSCI (domena, miasto, kraj) i jawnego
  "nie mam pewnosci" w pierwszym claimie zamiast zgadywania. Skutek uboczny: tekst
  zapytania sie zmienil, wiec exact cache wczesniejszych jobow nie trafia (kazdy
  prospekt liczy sie od nowa, ~1-2 PLN).
- **Prospekt bez domeny** (9 z 12 w lejku ma tylko gmail): `_identity_hint` bierze
  pierwsza linie notatek (miasto + kontakt, np. "Szkola tanca, Dobrzykowice. Kontakt:
  ...@gmail.com") i wkleja ja do zapytania jako "dane z kartoteki". Sama nazwa szkoly
  tanca nie identyfikuje podmiotu w skali swiata.
- `/prospect <nazwa> <domena>`: ostatni token wygladajacy na adres jest traktowany jako
  STRONA, nie czesc nazwy (wczesniej doprecyzowanie wchodzilo do nazwy firmy).
- **Bramka tozsamosci - TRZY stany, bo to dwa rozne pytania.**
  1. Czy research dotyczy TEJ firmy - liczone z DOWODOW przez `_identity_verdict`: domena
     prospekta musi wystapic w `evidence_items.source_url` albo w tresci claims; prospekt
     bez domeny - miasto z kartoteki musi wystapic w claims. Model tutaj nie glosuje.
  2. Czy cos budzi watpliwosc - deklaracja modelu (`TOZSAMOSC: niepewna - <powod>` w
     pierwszej linii podsumowania; prompt precyzuje, ze chodzi o PODMIOT, nie o kanal kontaktu).

  Stany: `potwierdzona` (dowod + brak zastrzezen) -> karta proponuje outreach;
  `z zastrzezeniem` (dowod jest, model marudzi) -> outreach dozwolony z prosba o weryfikacje
  punktu, gotowiec z ⚠️; `niepotwierdzona` (BRAK dowodu) -> outreach zablokowany, karta zada
  ponownego zlecenia ze strona, gotowiec z ⛔.
  Marker `[WERDYKT TOZSAMOSCI: <stan>]` zyje w notatkach lejka; `_draft_outreach` czyta OSTATNI.
  Nazwa markera MUSI byc inna niz "TOZSAMOSC:", bo tak zaczyna sie pierwsza linia podsumowania
  pisana przez model - skan po samym slowie trafial w tekst modelu zamiast w werdykt kodu
  (dowod 24/07 11:18: notatka La Cultury miala ciag "niepotwierdzona -> niepewna ->
  z zastrzezeniem -> niepewna", gdzie co druga pozycja pochodzila od modelu).
  **Dlaczego trzy, nie dwa:** wersja z prawem weta modelu zablokowala 2 poprawne prospekty
  na 2 (La Cultura i STC - dowody potwierdzaly podmiot, model marudzil o kanal kontaktu).
  Bramka blokujaca poprawne przypadki zostaje zignorowana i przestaje chronic przed
  prawdziwym bledem tozsamosci.

## Glos w tekstach do klienta (fix 24/07, po zywym gotowcu)

Objaw: gotowiec dla StandART brzmial jak folder reklamowy - otwarcie "widze, ze...",
zwrot "pomagamy klubom i szkolom tanecznym", CTA "masz 15 minut w tym tygodniu".
Trzy przyczyny, wszystkie z sondy, nie z wrazenia:

1. **Voice Bible obcieta do 9%.** Do promptu szlo `voice_bible[:2000]` z 22 168 znakow,
   czyli naglowek pliku i pozycjonowanie. Zasad pisania (sekcje 3-6: przymiotniki glosu,
   banned vocab 4.1-4.5, em-dash, format) model nie widzial NIGDY.
   Teraz `_voice_for_outreach` podaje CALY rdzen + CALA Voice Bible (cap `_VOICE_MAX`
   30 tys. znakow). Prob wybierania sekcji po slowach kluczowych ODRZUCONY sonda:
   z 37 naglowkow zywej Voice Bible dopasowaly sie dwa, a listy zakazanego slownictwa
   i regula em-dash maja naglowki po angielsku - wypadlyby. To ta sama klasa bledu.
2. **voice_dna_core nie byl czytany wcale.** 4471 znakow destylatu z 20 wywiadow
   osobistych lezalo w brand_config, a sciezka sprzedazowa brala tylko voice_bible.
   `_voice_dna_core()` wchodzi teraz i do gotowca, i do promptu rozmowy (w calosci).
3. **Baza wiedzy podsuwala cudzy case.** Sa 3 materialy (same Adamietz) i najblizszy
   sasiad zawsze cos zwracal - do maila o szkole tanca wchodzily raporty o holdingu
   budowlanym z podobienstwem 0.40-0.45 jako "techniki". `_KNOWLEDGE_MIN_SIM` = 0.55
   i brak fallbacku ILIKE dla tekstow do klienta: lepiej jawna luka niz falszywy kontekst.

Dodatkowo `_ANTY_SZABLON` w prompcie systemowym gotowca. Powstal, bo zakazy w
`_FRAMEWORKS` nie wystarczyly: model otworzyl mail fraza wprost zakazana i przepisal CTA
doslownie z PRZYKLADU w tych frameworkach. Sekcja nazywa oba mechanizmy (recytowanie
ilustracji, pozorowana personalizacja) i konczy sie testem podmiany nazwy firmy.

**Wzorce wlasne:** `material_type='outreach_example'` w sales_knowledge (wrzutka przez
`/add_sales_material` z podpowiedzia "wzorzec"). `_outreach_examples()` wkleja do 3
ostatnich DOSLOWNIE do promptu - model pisze od zdan Tomasza, nie od teorii.

## Wizytowka: agent sam wchodzi na strone prospekta (24/07, zgloszenie Tomasza)

Zgloszenie: "wszedlem na strone i od razu widze kontakt telefoniczny i wiem kto tam uczy -
tak nie mozemy pracowac". Research kosztowal 1,24 PLN i orzekl "brak danych kontaktowych".

**Sonda jobu 7411d0ba (dowod, nie hipoteza):**
- `web_search` zwrocil z domeny klubu PIEC wynikow, ale same TYTULY po 22-52 znaki
  ("Klub Sportowy StandART - Instruktorzy"). Zero tresci strony.
- `firecrawl` (adapter od pobierania stron) nie tknal domeny klubu ANI RAZU - osiem wynikow
  z arXiv i blogow o "prospectingu AI", z artefaktem prefiksu `arxiv.org/abs/`.
- Najdluzszy dowod w calym jobie: praca naukowa, 1073 znaki.
- Regex telefonu po CALEJ tresci dowodow: 0 trafien.

Synteza byla wiec uczciwa (napisala, czego nie ma w dowodach) - pobieranie bylo puste.

**Fix (deterministyczny, bez modelu):** `wizytowka(url)` w sales.py pobiera strone glowna
prospekta i do 3 podstron pasujacych do `kontakt|contact|cennik|zapisy|grafik|instruktor|
o-nas|about`, zdejmuje znaczniki i wyciaga mail plus telefon. Wywolywana w dwoch miejscach:
- `_prospect_research` PRZED zleceniem researchu: fakty ida do zapytania jako PEWNE
  ("nie podwazaj i nie pisz, ze ich brak") i do notatek lejka,
- `_draft_outreach`: tekst strony ladzie w promptcie jako pierwsze zrodlo haka, a mail
  i telefon maja PIERWSZENSTWO w naglowku gotowca.

Tap-test na zywej stronie 24/07: 4 pobrane strony, telefon 510-555-099, mail
recepcja@..., 28 358 znakow tekstu. Cztery zapytania HTTP, zero kosztu modelu.

**Dane ida do KOLUMN, nie do prozy (DDL 029, zgloszenie Tomasza "research ma tez
automatycznie uzupelniac baze danych bo od tego jest"):** `sales_pipeline.contact_email`,
`contact_phone`, `contact_person`, `site_checked_at`. Wypelniaja je dwa deterministyczne
zrodla: `wizytowka()` (przy zleceniu researchu i przy pisaniu gotowca) oraz `tick()` po
zakonczonym researchu (regex po claims i podsumowaniu). `_zapisz_kontakt` nadpisuje
WYLACZNIE puste pola - to, co Tomasz wpisal recznie, jest nietykalne. Kontakt widac teraz
w `/pipeline` przy kazdym prospekcie, a jego brak jest oznaczony ⚠️ na etapach
prospect/qualified.

**Zostaje otwarte (osobny build):** dlaczego adapter firecrawl na zapytanie o konkretny
podmiot zwraca arXiv. To wada kaskady zrodel Researchera, nie sprzedazy - patrz
docs/komponenty/researcher.md.

## Naglowek i stopka gotowca (24/07, feedback Tomasza)

Gotowiec idzie TRZEMA wiadomosciami, zeby dalo sie go zrewidowac bez otwierania bazy:

1. **Naglowek** (`_outreach_naglowek`): kanal, nazwa prospekta, osoba decyzyjna, mail, telefon,
   strona, ewentualne ostrzezenie o tozsamosci. Dane leca z kartoteki CRM (contacts po
   `contact_id`), notatek lejka i claims researchu - regexem, bez LLM. Czego nie ma, jest
   napisane wprost ("(nieustalona - research jej nie znalazl)"), bo pusty naglowek klamie
   mniej niz zgadniety. Regex telefonu odrzuca NIP i REGON (zweryfikowane na probkach).
2. **Czysta wklejka** - sam tekst, do skopiowania. Instrukcja "zwroc wylacznie tresc" NIE
   wystarczyla: model poprzedzil mail wlasnym rozumowaniem o konflikcie RDC i o wyborze haka
   (dowod 24/07 14:03). Dlatego kontrakt formatu (`---GOTOWIEC---` w pierwszej linii) plus
   deterministyczne ciecie `_tylko_gotowiec`: po znaczniku, awaryjnie dla maila od linii
   `TEMAT:`, a gdy nie ma ani jednego - caly tekst (lepiej za duzo niz pusto).
3. **Stopka** (`_outreach_stopka`): etap lejka, ktory to kontakt (pierwszy czy kolejny - liczone
   z engagement_log, nie z pamieci modelu), termin follow-upu i instrukcja "napisz wyslalem".

Docelowo dane kontaktowe maja przyjsc z CRM zamiast z regexa - brief:
`docs/briefs/BRIEF_POCZTA_I_CRM_GHL_24072026.md`.

## Znane pulapki

- Wiersz channels 'sprzedaz' pojawia sie w menu ⚙️ Cele (n8n) - NIE wlaczac go jako celu
  publikacji; guardy w kodzie (planner/reports/proactive/snapshot) i tak go ignoruja.
- Research medium trwa kilka minut (~1-2 PLN/job); critical przez API zablokowany
  (kanon kosztowy 20/07) - kod cicho obniza 'critical' do medium
  - /prospect zwraca paragon od razu, wynik przychodzi tickiem; nie czekac w rozmowie.
- PDF ze skanow (obrazy) nie da tekstu - pypdf zwraca pusto, bot melduje jawnie.
- Embeddingi wymagaja openai_api_key w app_secrets - bez niego sales_knowledge dziala
  na fallbacku ILIKE (jawnie oznaczone w paragonie zapisu).
- Level 2 (poza zakresem L1): obsluga hello@ (Gmail API), follow-up automation,
  dashboard metryk konwersji, mirror sales_knowledge do Notion.
