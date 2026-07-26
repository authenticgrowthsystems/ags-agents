# Komponent: ENGAGEMENT-CRM (comment-radar + relacje z ludzmi)

**STATUS GOTOWOSCI: LIVE (wdrozone 20/07: psql 026 + rebuild + patch n8n, tap-testy PASS) + warstwa INTAKE-UX 21/07 (menu intencji, DM, dedup osoby) W GALEZI build/intake-ux - czeka merge + rebuild + tap-testy DoD** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Zamienia komentowanie ze zrzutow w budowanie relacji zapisanych w CRM. Tomasz wysyla
zrzut cudzego posta przy aktywnym subagencie -> wizja Claude proponuje komentarz PER AUTOR
-> kazda propozycja to OSOBNY wiersz engagement_log z contact_id (CRM obowiazkowy) i
WLASNYMI guzikami decyzji. Nieznana osoba dostaje od razu stub w contacts + wymuszony
intake profilu (zrzut profilu -> wizja -> bio/handle + tier zatwierdzany guzikami).
Nic nie ginie: propozycje bez decyzji i zatwierdzone-a-niepotwierdzone wracaja po 24h
guzikami. Album Telegram = JEDEN post (jedna sklejona analiza).

## Przeplyw (szczesliwa sciezka; INTAKE-UX 21/07: najpierw MENU INTENCJI)

```
zrzut/album (subagent aktywny) -> n8n Photo Route -> POST /message 'skomentuj ostatni zrzut'
  -> _sub_comment_vision(menu=True):
     0. uzbrojony intake CRM? -> zrzut = PROFIL (crm.process_profile_photo, nie post)
     1. album (media_group_id)? -> claim grupy + pauza 4 s + JEDEN kontekst
     2. drugi zrzut osobno w <60 s? -> decyzja 'photo_group': jeden post czy rozne?
     3. _intent_menu_open: _screen_shots (wizja-klasyfikacja: osoby/post/DM/profil)
        -> B3: osoba z OTWARTA karta intent_menu <24h? -> doklejka insp_ids, KONIEC
        -> JEDNA karta 'CO WIDZE + PROPONUJE' z guzikami (decisions.ask 'intent_menu'):
           [Skomentuj][Odpowiedz na DM][Poznaj osobe][Wszystko po kolei][Tylko zapisz]
tap dec:<id>:<key> -> apply_intent_menu (wykonanie SEKWENCYJNE, paragon po kazdym watku):
  comment -> _comment_vision_run -> bloki '### Autor / POST: / KOMENTARZ:' -> per autor:
     crm.ensure_contact (match po handle/nazwie OCZYSZCZONEJ clean_author; stub gdy nieznany)
     -> engagement_log (status='proposed', contact_id, author_display)
     -> 3 wiadomosci: naglowek (kontekst relacji + KANAL i JEZYK publikacji) / CZYSTA wklejka /
        [kanal nie-PL: kontrola po polsku translate_text] + guziki cmt:sent|angle|no
     -> nieznany: 4. wiadomosc intake [Dam zrzut profilu][Zostaw stub] (max 1/24h per osoba)
  dm -> _dm_reply_run (wizja czyta konwersacje, 1 odpowiedz w glosie marki) -> TEN SAM tor
     _send_author_proposal(kind='dm') -> engagement_log z markerem [DM] w notes
  intake -> profil widoczny? crm.process_profile_photo od razu : crm.arm_intake (czekamy na zrzut)
  po ostatnim watku: 'co dalej?'; pojedynczy wybor -> karta z POZOSTALYMI intencjami
cmt:sent ([Wkleilem]/[Wyslalem]) -> JEDNO tapniecie domyka cykl (feedback 21/07): engagement
  'sent' + crm.bump_stage(contact, 'dm' gdy DM, inaczej 'commented') + last_interaction -
  bez task_queue i drugiego gotowca (Tomasz kopiuje wklejke od razu z propozycji)
cmt:ok (LEGACY, stare karty sprzed 21/07) -> status='approved' + task_queue 'comment'
  (payload.kind comment|dm) -> gotowiec + [Wkleilem][Pomin]; cmt:done -> task done + 'sent'
  + bump_stage jak wyzej
```

## Wejscia-wyjscia i tabele

- `contacts` (45 osob z #71): dopasowanie po `x_handle`, `handles` jsonb ({"x": "...",
  "linkedin": "..."}), `name`/`full_name`. Nowe kolumny (db/026): `handles`,
  `relationship_stage` (skala ZATWIERDZONA guzikami 20/07: cold/commented/replied/dm/offer/
  client liniowo, tylko W PRZOD + 'ghosted' jako stan boczny; kolejny komentarz do ghosted
  ozywia relacje - bump traktuje ghosted jak cold),
  `icp_tier` CHECK poszerzony o doktryne #71 (Buyer/Peer/Competitor/Partner), od 24/07 takze
  **Inne** (db/031, decyzja Tomasza guzikami: dodac piata wartosc, legacy Premium/Mid/Free/
  Watch/N/A zostawic jako historie). Skala zyje w JEDNYM miejscu: `crm.TIERS` / `crm.TIER_OPTIONS`
  (karty, parser raportu, zapis, prompt wizji profilu czerpia stamtad).
  Stub: name, source='Comment', status='Cold', stage='cold'.
  Kolumna `who_is_who` JSONB (db/030, 24/07): kto jest kim PO STRONIE KLIENTA
  ({"role","influence_level","relationship_stage","source_of_data","notes"}). `handles`
  to tozsamosc per KANAL, `who_is_who` to pozycja czlowieka w ORGANIZACJI. Czyta ja
  `crm.relation_context`, wiec rola i wplyw widac w naglowku propozycji i gotowca.
  Pisze ja dzis Sales Manager L1 z czatu (przez SQL Tomasza) - automatyczny zapis
  z raportu pracy to otwarty punkt do decyzji Managera.
- `engagement_log`: propozycja per autor; `contact_id` FK (od 001, teraz FAKTYCZNIE
  wypelniane), `status` cyklu zycia (db/026): proposed -> approved/rejected -> sent/skipped
  (logged = wpisy historyczne), `author_display`. Decyzje NIE zyja juz tylko w notes.
  Od 24/07 log jest TAKZE zrodlem historii DM dla reguly FAIL-CLOSED (indeks
  idx_eng_log_contact_action; marker `[DM]` w notes zostawiaja obie sciezki: propozycja
  subagenta i linia dm_* z RAPORTU PRACY).
- `task_queue` (task_type='comment'): payload + author + contact_id; pending -> gotowiec
  -> in_progress -> done/failed.
- `agent_decisions` (przez decisions.ask): typy `crm_tier` (Buyer/Peer/Competitor/Partner;
  B3 21/07: JEDNA decyzja per osoba w 24h - dubel = nota zamiast drugiego pytania;
  24/07 FAIL-CLOSED: tier WYKLUCZAJACY z lejka (Competitor / out_of_icp) nie dostaje
  rekomendacji, gdy z czlowiekiem byla juz rozmowa - liczone z engagement_log, nie
  z opinii modelu. Skutek uboczny jest celowy: `decisions.ask` bez rekomendacji NIE
  podejmuje decyzji sam nawet w trybie semi_autonomous, wiec wykluczenie zawsze
  przechodzi przez Tomasza. Karta niesie dowod: ile wpisow DM, kiedy ostatni,
  jakie stadium. `context.fail_closed=true` zostaje w wierszu decyzji),
  `stale_comment` ([Wyslalem][Pomin][Pokaz jeszcze raz]), `stale_comment_task`
  ([Tak, odhacz][Nie, pomin]), **`stale_outreach`** ([Wyslalem][Czekam][Pokaz tresc]
  [Rezygnuje] - gotowce Agenta Sprzedazy, obsluga `apply_stale_outreach`; od 26/07 guzik
  "Wyslalem" NIE pisze sam do engagement_log, tylko wola `sales.mark_outreach_sent`, zeby
  obie drogi odhaczenia robily to samo - wczesniej guzik nie ustawial terminu nastepnego
  kontaktu i prospekt zostawal z "BRAK nastepnego kroku"), `photo_group` (jeden post / rozne; context.menu=true gdy
  z trasy wrzutki), **`intent_menu`** (INTAKE-UX 21/07: watek wrzutki jako OBIEKT -
  context: insp_ids/contact_id/screening/done_keys; przyszly konektor UI wyswietli te
  wiersze jako liste wiszacych zadan). Kazda odpowiedz uczy (agent_learning_log); typy
  moga z czasem przejsc na semi-auto (NIE dotyczy tresci).
- `inspirations`: zrzuty ze schowka; po patchu n8n `metadata.media.media_group_id`.
- Stan przejsciowy w brand_config (wzorzec matreview): `crm_intake_pending` (czekamy na
  zrzut profilu, TTL 15 min), `cmt_last_shot` (okno 60 s na pytanie o sklejenie),
  `cmt_group_claim` (album przetworzony raz), `crm_intake_offered` (B3 21/07: karta
  'Nowa osoba' max 1/24h per kontakt).

## Konfiguracja

Brak nowych kluczy configu. Wymaga: psql db/026 PRZED rebuildem cm-agenta (INSERTy pisza
do nowych kolumn), patch n8n `n8n-workflows/patches/hitl-photo-mediagroup-20072026.cjs`
(deactivate+activate w skrypcie). Bez patcha n8n album lapie sie w pytanie <60 s (fallback).

## Punkty zaczepienia w kodzie

- `cm-agent/app/crm.py`: `find_contact`/`ensure_contact` (stub; match takze po nazwie
  oczyszczonej `clean_author` - B3), `relation_context` (od 24/07 pokazuje role i wplyw
  z `who_is_who`), `dm_history`/`fail_closed_note` (24/07, pkt 7 paczki #1),
  `bump_stage` (tylko w przod),
  `arm_intake`/`get_intake`/`clear_intake`, `intake_recently_offered`/`mark_intake_offered`
  (strażnik karty 24h), `process_profile_photo` (z dedupem decyzji crm_tier 24h),
  `apply_tier`, `pending_text` ("co wisi?").
- `cm-agent/app/conversation.py`: `_sub_comment_vision` (intake/album/okno 60 s; menu=True
  z trasy wrzutki), `_screen_shots`/`_intent_menu_open`/`apply_intent_menu`/`_intake_run`
  (INTAKE-UX 21/07), `_dm_reply_run`/`_sub_reply_dm` (odpowiedzi DM), `_comment_vision_run`,
  `_send_author_proposal` (3 wiadomosci + guziki per autor; kind comment|dm),
  `_parse_comment_blocks`, `handle_cmt` (sent = jeden tap 21/07; legacy ok/done/skip +
  no/angle per autor + intake/stub; kind z markera [DM] w notes), `apply_photo_group`,
  trasa "co wisi?" w `_subagent_handle`.
- `cm-agent/app/engagement.py`: `consumer_tick` (gotowiec z autorem + kontekstem CRM),
  `stale_watch` (przypomnienia 24h), `apply_stale_comment`, `apply_stale_task`.
- `cm-agent/app/generate.py`: `comment_from_image` (lista obrazow, format POST:/KOMENTARZ:),
  `profile_from_image` (JSON: name/handle/bio/proposed_tier/why).
- `cm-agent/app/decisions.py`: `_apply_action` rejestr typow crm_tier / stale_comment /
  stale_comment_task / photo_group.
- `cm-agent/app/worker.py`: `engagement.stale_watch()` w petli.

## Warstwa LACZNIK (22/07): praca reczna z czatu na abonamencie

Interakcje wykonane RECZNIE poza Telegramem (czat na abonamencie w podrozy) wchodza do
TEGO SAMEGO CRM przez parser RAPORT PRACY (bez LLM): blok `[RAPORT PRACY v1]` wklejony
do rozmowy -> `engagement.apply_work_report` -> engagement_log (komentarz='sent',
dm_wyslany='sent', dm_odebrany/reakcja/obserwacja='logged') + contacts (clean_author,
stadium: komentarz->commented, dm_*->dm) + inspirations (obserwacje) + karta crm_tier
dla nowych osob (1/24h). Idempotencja: 'sync:<hash>' w notes. Szczegoly, format i
pulapki: [lacznik.md](lacznik.md).

## Kanony ktore go dotycza

- "Zapisywac w jakie relacje wchodze z jakimi ludzmi" (kanon od poczatku projektu) -
  contacts przestaje lezec odlogiem, kazda interakcja ma contact_id.
- Decyzje Tomasza = GUZIKI, ZERO decyzji rozpoznawanych z prozy (05/07 + brief 20/07).
- Kanon 19/07: zero zgadywania - po 24h ciszy PYTANIE guzikami, nigdy auto-domkniecie.
- Paragon kazdej decyzji; REGULA PRAWDY (brak researchu/wizji = jawny komunikat).
- Publikacja komentarzy przez API celowo NIE (ryzyko tieru X; wklejka reczna).

## Znane pulapki

- Kolejnosc wdrozenia: psql 026 PRZED rebuildem - kod INSERTuje do contact_id/status/
  author_display; bez DDL insert pada (try/except -> propozycja idzie, ale BEZ guzikow).
- contacts ma ZDUBLOWANE kolumny (name/full_name, icp_tier/tier...) - konsolidacja to
  osobny, znany dlug (audyt 04/07 pkt 3). Ten komponent pisze: name, x_handle, handles,
  icp_tier, relationship_stage, narration, last_interaction_date/type.
- icp_tier CHECK dopuszcza dwie skale (legacy + doktryna #71) - stare 45 wierszy ma
  Premium/Mid/Watch; nowe wpisy dostaja Buyer/Peer/Competitor/Partner z guzikow.
- Claim albumu (cmt_group_claim) to read-check-write bez blokady - przy rownoczesnych
  POSTach z n8n teoretyczny wyscig; pauza 4 s + pojedynczy operator = ryzyko pomijalne.
- Wizja nie zawsze widzi handle (czesto tylko display name) - dopasowanie po nazwie
  case-insensitive; multi-platformowa tozsamosc scala dopiero intake (handles jsonb).
  B3 (21/07): warianty wyswietlania ('X • 2nd', emoji, zaimki) czysci clean_author PRZED
  dopasowaniem i zapisem stuba - wczesniej kazdy wariant = nowy stub i nowa karta.
- Istniejace stuby sprzed 21/07 z brudna nazwa (np. 'Djordje Klikovac • 2nd') NIE scala
  sie automatem z czysta - jesli po wdrozeniu pojawi sie dubel, scalic recznie SQL-em.
- 'Pokaz jeszcze raz' przy przypomnieniu tworzy NOWY wiersz proposed (stary -> rejected
  z nota) - guziki zawsze wskazuja zywy wiersz, licznik interakcji nie liczy odrzuconych.
