# Komponent: KOLEJKA I PUBLIKACJA (post_queue, sloty, dispatch, Scheduler)

**STATUS GOTOWOSCI: KOMPLETNY** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Zamienia ZATWIERDZONY material (content_items 'approved') na opublikowane posty:
przydziela sloty, stage'uje warianty kanalowe do post_queue, publikuje przez
adaptery subagentow (n8n) albo Scheduler i domyka ledger publikacji.

KANON 19/07 (project_publikacja_kanon_19072026): zatwierdzone publikuje sie
ZAWSZE (obecnosc Tomasza nieistotna); niezatwierdzone NIGDY samo -
`_emergency_promote` USUNIETY Z KODU. Cisza >24h na approve = eskalacja guzikami
(`_stale_approval_watch`, typ 'stale_approval': Pokaz karte / Odrzuc /
Przypomnij jutro), nigdy auto-decyzja.

## Wejscia-wyjscia i tabele

- `content_items`: state machine tresci; worker claimuje 'approved' DOPIERO gdy
  `scheduled_for <= NOW()` -> 'dispatching' -> 'published'.
- `post_queue` (INWENTARZ + HARMONOGRAM): wiersz per wariant kanalowy;
  statusy: review / scheduled / queued / held / dispatching / published /
  failed / rejected. `content_item_id` linkuje do materialu.
- `published_posts`: PRAWDA "co opublikowane" (post_id/URL, embedding,
  engagement_metrics) - zasila dedup i content memory.
- `channels.config.publish_mode` decyduje droga: `webhook` (POST adapter
  subagenta n8n -> publikacja NATYCHMIAST -> callback), `post_queue` (status
  'scheduled', bierze Scheduler n8n co minute WG SLOTU wiersza), `draft`
  (status 'held', recznie).
- STAN 22/07 (decyzja Tomasza "zatwierdzone ma isc samo"): AGS/x ORAZ
  AGS/linkedin = `post_queue` - OBA kanaly publikuje Scheduler per slot wiersza.
  Scheduler ma ROUTER platformy (Route Platform, if 2.2): x -> Publish To X,
  inne -> Publish To LinkedIn (Scheduler) (kod 1:1 z Subagent LinkedIn Publisher
  v2: registerUpload feedshare-image -> PUT -> ugcPosts; obrazy dzialaja) ->
  Mark Published LI (ta sama ksiega per-wiersz) -> LI Confirm. Patch:
  scheduler-linkedin-branch-22072026.cjs. Tryb `draft` (gotowce + 'wklejone <id>')
  zostaje dostepny per kanal; `webhook` NIE respektuje slotow - nie uzywac.
- Callback publikacji: post_queue 'published' + INSERT published_posts +
  agent_messages RESPONSE + potwierdzenie na kanal logowy (bot #2).

## Sloty (slots.py)

- `next_slot`: najblizszy wolny slot wg okien celu (`publish_windows`,
  np. x 13-22, LI profil 16:00-18:00) i kadencji; `_busy` liczy zajetosc
  z content_items ORAZ post_queue (fix 67f3acf). `_li_ok`: LinkedIn pn-pt post,
  sobota nic, niedziela artykul (reczny).
- `humanize_slot`: ludzkie minuty +/-15 od slotu planu, NIGDY rowny kwadrans -
  stosowany przy KAZDYM wpisie slotu do post_queue. content_items trzyma CZYSTY
  slot planu (roznica ZAMIERZONA).
- `assign_if_needed`: approved bez slotu dostaje go automatycznie.

## Serie X i straznik dlugich (channels.stage_variant)

- Dluga tresc X przy <1000 followers = SERIA samodzielnych postow rozdzielonych
  markerem `===POST===`, po slotach dnia, czesci publikowane SEKWENCYJNIE.
- STRAZNIK: wariant >600 znakow bez `===POST===` = automatyczne ciecie po
  akapitach na serie. Grafika idzie tylko z czescia 1.
- STRAZNIK JEZYKA (20/07): przed zapisem do kolejki wariant sprawdzany z
  `channels.config.language_publish`; gdy kanal 'en' a tekst wyglada po polsku
  (`compliance.looks_polish`) -> `generate.translate_text` na EN. Karta HITL
  pokazuje dokladnie to, co wyjdzie na kanal.
- `[ARTYKUL]` = gotowiec do wklejki recznej (API X/LinkedIn nie publikuje
  artykulow z naszego tieru).

## Konfiguracja

- `channels.config`: publish_windows, publish_mode, posts_per_day,
  follower_count, thread_enabled, language_publish, emergency_publish
  (MARTWY klucz - kod go nie czyta, zostal po incydencie).
- Adaptery n8n: Subagent X Publisher `G3nEIt5lIkiKemiK`, Subagent LinkedIn
  Publisher `Uv9TvUMI8MRSqCLz` (generyczny per cel: secret_prefix), Scheduler
  `x1jJEbcWAe3FnpCa` (co minute, OAuth1). Klucze WYLACZNIE z app_secrets.
- MEDIA X (v3, 22/07, patch scheduler-media-v3-22072026.cjs; wczesniejsze proby:
  query-params = 400 "not one of []", multipart na /2/media/upload = 400 "Missing
  media field" bo to PROSTY upload): chunked idzie POD-SCIEZKAMI -
  INIT POST /2/media/upload/initialize (JSON: media_type,total_bytes,media_category),
  APPEND POST /2/media/upload/{id}/append (multipart: media+segment_index),
  FINALIZE POST /2/media/upload/{id}/finalize (bez body), STATUS = GET z query.
  Zweryfikowane per-endpoint w docs.x.com 22/07. Oba workflow (wspolny kod).
  Do kolejki ida tylko wpisy media z file_id (`channels._pub_media`).
  DOWOD LIVE: oczekiwany przy publikacji 185 (22/07 17:55).
- KSIEGA (naprawa 21/07): Mark Published Schedulera per-wiersz robi UPDATE pq
  + INSERT published_posts + agent_messages RESPONSE + domyka content_items,
  gdy nie ma juz wierszy w locie. Bez tego CM/raporty klamaly "nic nie wyszlo"
  mimo opublikowanych postow (incydent 21/07).
- GOTOWIEC RECZNY (A4, 21/07): wiersz 'held' = worker wysyla do glownej
  rozmowy pelny zestaw (naglowek + czysta wklejka + grafika); domkniecie
  deterministyczna komenda `wklejone <id>` (pq->published + ksiega, source
  manual_paste). ZWIS publikacji liczony OD SLOTU wiersza, nie od dispatchu.

## Punkty zaczepienia w kodzie

- `cm-agent/app/worker.py`: `process_item` (state machine), `_draft` (generacja
  canonical + warianty + dedup), `_stale_approval_watch`, `reconcile_publications`,
  `_publish_report`, `loop`.
- `cm-agent/app/channels.py`: `stage_variant` (staging + serie + straznik),
  `dispatch_item`, `_delegate`, `active_targets`.
- `cm-agent/app/slots.py`: `next_slot`, `humanize_slot`, `assign_if_needed`,
  `_busy`, `_li_ok`.
- Odrzucenie karty sprzata kolejke: `matreview.handle` akcja 'no' ->
  UPDATE post_queue -> 'rejected' (wszystkie wiersze materialu).

## Kanony ktore go dotycza

- Kanon publikacji 19/07 (calosc sekcji "Co robi").
- Ludzkie minuty (kanon 19/07): +/-15 min, nigdy kwadrans.
- Kanon mediow multi-platforma: jedna grafika = reuse na wszystkie kanaly
  materialu (patrz grafika.md).

## Znane pulapki

- INCYDENT 20/07 (AP-307, raport: docs/ops/INCYDENT_PUBLIKACJI_20072026.md):
  przy publish_mode='webhook' delegat publikowal WSZYSTKIE wiersze materialu
  naraz przy dispatchu (burst 4-5 postow/h), gubil media wierszy, a callback
  X Publishera oznaczal 'published' KAZDY wiersz materialu (takze te ze slotami
  w przyszlosci) - baza klamala. Adaptery po zmianie trybow NIEUZYWANE, ale
  callback per-row NIENAPRAWIONY (uzbrojona mina - backlog przed jakimkolwiek
  powrotem do trybu webhook).
- 'held' to zamrazarka: po incydencie 13-19/07 wszystko zamrozone, sprzatniete
  wg dowodu 19-20/07 (sieroty pq bez materialu -> rejected; SQL wykonany,
  kontrola = 0). Nowe sieroty nie powstaja (fix matnav 'no').
- Publishery n8n NIE wolaja jeszcze `/wake` po callbacku - meldunek publikacji
  czeka do 30 s na poll petli (TODO przy najblizszej sesji n8n).
- Legacy AGS X Agent (Notion queue, cron 14/18/22) OFF od 25/06 - podwojnych
  publisherow NIE MA (dowod w n8n 19/07).
- linkedin_access_token z Token Generatora wygasa ~01/09/2026;
  linkedin_client_secret w DB bledny (OAuth callback nieuzywany).
