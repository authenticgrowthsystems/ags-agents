# Komponent: ENGAGEMENT-CRM (comment-radar + relacje z ludzmi)

**STATUS GOTOWOSCI: W BUDOWIE (kod + DDL 026 w galezi build/engagement-crm; czeka merge + psql + rebuild + patch n8n + tap-testy)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Zamienia komentowanie ze zrzutow w budowanie relacji zapisanych w CRM. Tomasz wysyla
zrzut cudzego posta przy aktywnym subagencie -> wizja Claude proponuje komentarz PER AUTOR
-> kazda propozycja to OSOBNY wiersz engagement_log z contact_id (CRM obowiazkowy) i
WLASNYMI guzikami decyzji. Nieznana osoba dostaje od razu stub w contacts + wymuszony
intake profilu (zrzut profilu -> wizja -> bio/handle + tier zatwierdzany guzikami).
Nic nie ginie: propozycje bez decyzji i zatwierdzone-a-niepotwierdzone wracaja po 24h
guzikami. Album Telegram = JEDEN post (jedna sklejona analiza).

## Przeplyw (szczesliwa sciezka)

```
zrzut posta (subagent aktywny) -> n8n Photo Route -> POST /message 'skomentuj ostatni zrzut'
  -> _sub_comment_vision:
     0. uzbrojony intake CRM? -> zrzut = PROFIL (crm.process_profile_photo, nie post)
     1. album (media_group_id)? -> claim grupy + pauza 4 s + JEDNA analiza calosci
     2. drugi zrzut osobno w <60 s? -> decyzja 'photo_group': jeden post czy rozne?
     3. comment_from_image (1+ obrazow) -> bloki '### Autor / POST: / KOMENTARZ:'
  -> per autor: crm.ensure_contact (dopasowanie po handle/nazwie, INSERT stub gdy nieznany)
     -> engagement_log (status='proposed', contact_id, author_display)
     -> 3 wiadomosci: naglowek z kontekstem relacji / CZYSTA wklejka / guziki cmt:ok|angle|no
     -> nieznany: 4. wiadomosc intake [Dam zrzut profilu][Zostaw stub]
cmt:ok -> status='approved' + task_queue 'comment' -> gotowiec z kontekstem CRM + [Wkleilem][Pomin]
cmt:done -> task done + engagement 'sent' + crm.bump_stage(contact,'commented') + last_interaction
```

## Wejscia-wyjscia i tabele

- `contacts` (45 osob z #71): dopasowanie po `x_handle`, `handles` jsonb ({"x": "...",
  "linkedin": "..."}), `name`/`full_name`. Nowe kolumny (db/026): `handles`,
  `relationship_stage` (cold/commented/replied/dm/offer/client, CHECK, tylko W PRZOD),
  `icp_tier` CHECK poszerzony o doktryne #71 (Buyer/Peer/Competitor/Partner) obok legacy
  (Premium/Mid/Free/Watch/N/A). Stub: name, source='Comment', status='Cold', stage='cold'.
- `engagement_log`: propozycja per autor; `contact_id` FK (od 001, teraz FAKTYCZNIE
  wypelniane), `status` cyklu zycia (db/026): proposed -> approved/rejected -> sent/skipped
  (logged = wpisy historyczne), `author_display`. Decyzje NIE zyja juz tylko w notes.
- `task_queue` (task_type='comment'): payload + author + contact_id; pending -> gotowiec
  -> in_progress -> done/failed.
- `agent_decisions` (przez decisions.ask): typy `crm_tier` (Buyer/Peer/Competitor/Partner),
  `stale_comment` ([Wyslalem][Pomin][Pokaz jeszcze raz]), `stale_comment_task`
  ([Tak, odhacz][Nie, pomin]), `photo_group` (jeden post / rozne). Kazda odpowiedz uczy
  (agent_learning_log); typy moga z czasem przejsc na semi-auto (NIE dotyczy tresci).
- `inspirations`: zrzuty ze schowka; po patchu n8n `metadata.media.media_group_id`.
- Stan przejsciowy w brand_config (wzorzec matreview): `crm_intake_pending` (czekamy na
  zrzut profilu, TTL 15 min), `cmt_last_shot` (okno 60 s na pytanie o sklejenie),
  `cmt_group_claim` (album przetworzony raz).

## Konfiguracja

Brak nowych kluczy configu. Wymaga: psql db/026 PRZED rebuildem cm-agenta (INSERTy pisza
do nowych kolumn), patch n8n `n8n-workflows/patches/hitl-photo-mediagroup-20072026.cjs`
(deactivate+activate w skrypcie). Bez patcha n8n album lapie sie w pytanie <60 s (fallback).

## Punkty zaczepienia w kodzie

- `cm-agent/app/crm.py` (NOWY): `find_contact`, `ensure_contact` (stub), `relation_context`,
  `bump_stage` (tylko w przod), `arm_intake`/`get_intake`/`clear_intake`,
  `process_profile_photo`, `apply_tier`, `pending_text` ("co wisi?").
- `cm-agent/app/conversation.py`: `_sub_comment_vision` (intake/album/okno 60 s),
  `_comment_vision_run`, `_send_author_proposal` (3 wiadomosci + guziki per autor),
  `_parse_comment_blocks`, `handle_cmt` (ok/no/angle per autor + done/skip + intake/stub),
  `apply_photo_group`, trasa "co wisi?" w `_subagent_handle`.
- `cm-agent/app/engagement.py`: `consumer_tick` (gotowiec z autorem + kontekstem CRM),
  `stale_watch` (przypomnienia 24h), `apply_stale_comment`, `apply_stale_task`.
- `cm-agent/app/generate.py`: `comment_from_image` (lista obrazow, format POST:/KOMENTARZ:),
  `profile_from_image` (JSON: name/handle/bio/proposed_tier/why).
- `cm-agent/app/decisions.py`: `_apply_action` rejestr typow crm_tier / stale_comment /
  stale_comment_task / photo_group.
- `cm-agent/app/worker.py`: `engagement.stale_watch()` w petli.

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
- 'Pokaz jeszcze raz' przy przypomnieniu tworzy NOWY wiersz proposed (stary -> rejected
  z nota) - guziki zawsze wskazuja zywy wiersz, licznik interakcji nie liczy odrzuconych.
