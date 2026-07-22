# Komponent: LACZNIK SYNCHRONIZACYJNY (praca na abonamencie <-> serwer)

**STATUS GOTOWOSCI: LIVE (wdrozone 22/07: 2 rebuildy + patch n8n + strona Notion 3a5c00c9... + sync_registry stan_gry; tap-testy DoD 4/4 PASS na zywych danych)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Domyka petle miedzy reczna praca Tomasza w czacie na abonamencie (pociag, telefon)
a serwerem AGS. Koncept: docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md
(ZATWIERDZONY guzikami 21/07). SSOT = baza ags_crd; czlowiek jest kablem transmisyjnym.
Cztery klocki etapu 1:

1. **RAPORT PRACY (czat -> serwer):** czatowy agent konczy sesje blokiem
   `[RAPORT PRACY v1]`; Tomasz wkleja go do Telegrama (albo wrzuca .md) -> parser
   BEZ LLM -> engagement_log + contacts + inspirations -> POTWIERDZENIE z licznikami.
   Typy linii: komentarz, dm_wyslany, dm_odebrany, reakcja, zaproszenie (22/07,
   wsad LinkedIn: `- zaproszenie | @slug | wyslane/przyjete | notka`, bez bumpu
   stadium), nowa_osoba, obserwacja.
2. **/kontekst [x|linkedin|sprzedaz|all] (serwer -> czat, FALLBACK):** zwarty stan gry
   BEZ LLM - plan tygodnia, kolejka, publikacje z metrykami, kontakty w grze, otwarte
   decyzje, lejek, radar. Tekst do 4000 znakow albo plik .md.
3. **Strona Notion "Stan gry AGS" (preferencja Tomasza):** ta sama tresc co /kontekst,
   JEDNA strona NADPISYWANA przez tick sync workera (throttle 15 min). Czatowy agent
   czyta stan sam z linku na starcie sesji.
4. **Masterprompty czatowe:** docs/product/masterprompty-czat/ - pliki wklejane RAZ
   do projektu w aplikacji czatowej (tozsamosc + glos + oba kontrakty). Wsad Tomasza
   scalony 22/07: X_v2 (z "X Comment Specialist") + LINKEDIN_AGS_v1 (z "LinkedIn SM");
   decyzja guzikami: Notion Lead Tracker = archiwum do odczytu, praca wraca WYLACZNIE
   raportem; czatowy CM bez wersji stalej (serwerowy CM = orkiestrator).

## Przeplyw

```
PRZED WYJAZDEM: czat czyta <link Notion "Stan gry AGS">  (fallback: /kontekst x -> kopiuj)
PRACA: Tomasz komentuje/DM-uje recznie, czat podpowiada tresci (glos AGS)
KONIEC SESJI: czat drukuje [RAPORT PRACY v1] -> Tomasz wkleja do Telegrama
  -> conversation.handle route '[raport pracy' (PRZED sales.try_command i LLM)
  -> engagement.apply_work_report: parse_work_report (naglowek kanal/data + linie '- typ | ...')
     -> per linia: hash sha256(kanal|znormalizowana linia)[:16]; 'sync:<hash>' juz w
        engagement_log.notes? -> duplikat, pomin
     -> komentarz: engagement_log (x_comment, status='sent') + contacts (clean_author,
        bump 'commented')
     -> dm_wyslany/dm_odebrany: engagement_log ('other', [DM], sent/logged) + bump 'dm'
     -> reakcja: engagement_log ('other', logged) + kontakt bez bumpu
     -> nowa_osoba: contact (stub/istniejacy) + narration + engagement_log (logged)
        + JEDNA karta crm_tier per osoba/24h (dedup po agent_decisions, wzorzec INTAKE-UX)
     -> obserwacja: inspirations (source='raport_pracy') + engagement_log (logged, kopia hasha)
  -> POTWIERDZENIE z licznikami ("zapisane: komentarze: 3, ... pominiete duplikaty: 1"
     + lista niezrozumianych linii - REGULA PRAWDY)
STAN GRY: notion_worker._loop -> stan_gry.tick() (po kazdym drainie, <=60 s):
  brand_config stan_gry_page_id ustawiony? -> throttle 15 min -> _signature() (md5 z max
  timestampow published_posts/sales_pipeline/contacts/engagement_log/agent_decisions/
  content_items) rozny od zapisanego? -> reports.kontekst_text('all') ->
  table_registry._re_render('stan_gry','AGS', page, ...) (soft-clear, mirror_state)
```

## Wejscia-wyjscia i tabele

- `engagement_log`: wpisy z raportu (status wg typu: sent/logged; idempotencja
  'sync:<hash>' w notes). ZERO nowych DDL.
- `contacts`: ensure_contact po clean_author (mechanizm INTAKE-UX); stadium wg akcji
  (komentarz->commented, dm_*->dm, tylko w przod).
- `inspirations`: obserwacje radaru (source='raport_pracy', metadata.channel/date).
- `agent_decisions`: karty crm_tier dla nowych osob (dedup 24h per contact_id).
- `brand_config` (AGS): `stan_gry_page_id` (id strony Notion - zaklada Tomasz),
  `stan_gry_state` ({"sig","ts"} - stan throttla, pisze tick).
- `sync_mirror_state`: wiersz ('stan_gry','AGS') - block_ids + checksum renderu strony.
- `sync_registry`: wiersz ('stan_gry', enabled, re_render) - TYLKO po to, zeby nocny
  drift check (03:00) obejmowal strone (iteruje po registry); trigger enqueue dla
  nieistniejacej tabeli nigdy nie strzeli, dispatch tej nazwy nie zobaczy.
  Higiena strony: soft-clear (jeden aktualny render, stare bloki archiwizowane),
  zapis tylko przy zmianie odcisku stanu, throttle 15 min, sufit 280 blokow
  z jawnym uciecien, edycje reczne gina przy nastepnym renderze (alarm driftu).

## Konfiguracja

- Strona Notion: Tomasz zaklada strone "Stan gry AGS" (Connection integracji na stronie -
  AP-305!), potem SQL (SSH):
  `docker exec -i pg_n8n psql -U n8n -d ags_crd -c "INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by) VALUES ('AGS','stan_gry_page_id','<ID_STRONY>',1,'tomasz') ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value, version=brand_config.version+1;"`
- Przepustka n8n: `n8n-workflows/patches/hitl-kontekst-command-22072026.cjs`
  (deactivate+activate w skrypcie). Bez patcha /kontekst wpada do 'other' i ginie;
  wklejka RAPORTU dziala bez patcha (zwykly tekst).
- Masterprompty czatowe: `docs/product/masterprompty-czat/` (aktualne: X_v2 +
  LINKEDIN_AGS_v1; link i ID strony juz wpisane, rytual startu = KONEKTOR Notion).

## Punkty zaczepienia w kodzie

- `cm-agent/app/engagement.py`: `parse_work_report`, `apply_work_report`, `_line_hash`,
  `_hash_seen`, `_report_insert`, `_report_tier_card`.
- `cm-agent/app/conversation.py`: route `'[raport pracy' in text.lower()` + `_KONTEKST_RE`
  w `handle()` (PRZED sales.try_command i LLM).
- `cm-agent/app/reports.py`: `kontekst_text(scope)`, `send_kontekst(chat_id, scope)`.
- `cm-agent/app/sync/stan_gry.py`: `tick()`, `_signature()`; wpiecie w
  `cm-agent/app/sync/notion_worker.py` (`_loop`, po `_drain`).

## Kanony ktore go dotycza

- SSOT = PostgreSQL; Notion = lustro DO CZYTANIA, nigdy druga prawda (doktryna #71).
- Zero LLM w parserze i /kontekst (deterministyczne, tanie, przewidywalne).
- REGULA PRAWDY: niezrozumiane linie raportu wracaja jawnie w potwierdzeniu; brak
  swiezego stanu gry = czat prosi o /kontekst zamiast zgadywac.
- Slownictwo: w tekstach do Tomasza "potwierdzenie", nie "paragon" (feedback 22/07).
- Decyzje guzikami: tier nowej osoby przez decisions.ask, 1 karta/24h.

## Znane pulapki

- Notion API timeoutuje na duzych stronach (#71) - stan gry to JEDNA nadpisywana strona,
  throttle 15 min, a porazka zapisu TEZ zuzywa okno throttla (nie mlocimy API); fallback
  zawsze /kontekst.
- AP-305: strona bez Connection integracji = API jej nie widzi ("pusto mimo id").
- Hash idempotencji liczy sie z kanalu + znormalizowanej linii (male litery, sklejone
  spacje) - zmiana JEDNEGO znaku tresci = nowa linia, zapisze sie drugi raz.
- Wklejka >=200 znakow przy UZBROJONYM /add_sales_material bylaby zjedzona przez
  ingest materialu - dlatego route raportu stoi PRZED sales.try_command.
- Raport >4096 znakow: Telegram TNIE wklejke na kilka wiadomosci, a czesc bez
  naglowka [RAPORT PRACY nie trafia do parsera (idzie do aktywnego agenta jak
  zwykly tekst). KONTRAKT PODSTAWOWY (decyzja Tomasza 22/07 po tap-tescie d):
  raport = PLIK .md o nazwie RAPORT_PRACY_<kanal>_RRRR-MM-DD_HHMM.md wyslany do
  Telegrama jako dokument (handle_document -> ten sam parser, zero ciecia, slad
  audytowy w nazwie). Fallback: krotka wklejka tekstem; dluga = CZESCI po ~20
  linii, kazda z wlasnym naglowkiem i [KONIEC RAPORTU]. Parser toleruje linie
  bez '- ' (decyduje pierwszy token przed '|').
- reports.kontekst_text importuje planner/sales/decisions LENIWIE (cykl importow:
  conversation -> reports).
- `/set` NIE zna klucza stan_gry_page_id (allowlista n8n) - konfiguracja SQL-em.
