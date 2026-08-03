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
  `scheduled_for <= NOW()` -> 'handed_off' -> 'published'.
  **`handed_off` do 03/08/2026 nazywalo sie `dispatching`** (D-008/AP-312: nazwa
  obiecywala stan przelotny, a stan trwa DNI - material czeka, az WSZYSTKIE
  wiersze jego serii przestana sie ruszac). Nazwa zyje w `config.STATUS_HANDED_OFF`.
- `post_queue` (INWENTARZ + HARMONOGRAM): wiersz per wariant kanalowy;
  statusy: review / scheduled / queued / held / dispatching / published /
  failed / rejected. `content_item_id` linkuje do materialu.
  **UWAGA: `dispatching` w TEJ tabeli to INNY slownik i ZOSTAJE** - znaczy
  "jeden wiersz oddany subagentowi", a nie "material czeka na cala serie".
  D-008 go nie dotknelo. Zywy wezel n8n `Mark Published` ma OBIE wartosci
  w jednym zapytaniu, wiec podmiana "po calym tekscie" zrywa kolejke po cichu.
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
- SUFIT KADENCJI (kanon 25/07, zgloszenie Tomasza "po co dzis tyle tweetow"):
  seria rozbijala sie na sloty NIEZALEZNIE od kadencji - gap wymuszal tylko
  ODSTEP miedzy postami, nie ich LICZBE, wiec czesci upychaly sie na dzis, az
  okno sie wypelnilo (7-8 zamiast 3-5). Teraz `slots._daily_cap` daje twardy
  sufit per kanal (X = gorna granica posts_per_day, np. '3-5' -> 5; LinkedIn = 1),
  a `next_slot` pomija dzien, ktory osiagnal limit - nadmiar serii przechodzi na
  kolejny dzien. Sufit jest niezalezny od gap/siatki/jittera (liczy WSZYSTKIE
  sloty dnia z content_items + post_queue). Test: cm-agent/tests/test_kadencja_sufit.py.
- **SLAD AUDYTOWY ZRODLA SLOTU (DDL 035, 29/07).** `post_queue.slot_source` mowi, ktora trasa
  ostatnio ustawila `scheduled_for`: `staging` (channels.stage_variant), `planner`
  (slots.assign_if_needed), `reslot` (app.reslot), `rozmowa` (przesuniecie terminu przez
  czlowieka), `dispatch` (channels, gdy slot byl pusty), `nieznane` (zapis spoza Pythona:
  wezel n8n albo reczny SQL - **nie udajemy, ze wiemy**).
  **Powod:** 28/07 piec wpisow wyszlo w piec minut o 09:00, poza oknem, na koncie ktore trzy
  dni wczesniej dostalo 403 za wykryta automatyzacje. Ustalenie sprawcy zajelo pol godziny
  i udalo sie WYLACZNIE przez eliminacje wszystkich innych tras - w danych nie bylo ani jednego
  sladu. To AP-311 w wersji zapobiegawczej.
  **Uwaga przy dodawaniu nowego zapisu slotu:** etykieta jest obowiazkowa, pilnuje tego
  `cm-agent/tests/test_slot_source.py` (liczy wszystkie zapisy i sprawdza, czy zaden nie zostal
  bez etykiety). `dispatch` etykietuje TYLKO gdy sam nadaje slot - inaczej nadpisalby etykiete
  prawdziwego autora.
- **BRAMKA POTWIERDZENIA TERMINU (29/07, typ decyzji `slot_confirm`).** Przesuniecie materialu
  przez rozmowe NIE zapisuje sie od razu, gdy zachodzi chocby jeden z dwoch NIEZALEZNYCH
  warunkow: termin poza oknem kanalu **albo** polecenie dotyczace wiecej niz jednego wiersza.
  Wtedy leci pytanie z guzikami, a zapis czeka na tapniecie. Zasada "Ty decydujesz o terminie"
  bez zmian - system pyta PRZED skutkiem, zamiast meldowac PO nim.
  Zapis wykonuje `_wykonaj_przesuniecie`, wolane z OBU drog (bezposredniej i z guzika) - jedno
  miejsce, zeby sie nie rozjechaly (AP-309).
- **DWIE TRASY DOTYKAJA WSZYSTKICH WIERSZY MATERIALU NARAZ** (`conversation` przy przesunieciu
  terminu, `slots.assign_if_needed`). Przy materiale wieloczesciowym daja im ten sam czas,
  czyli SALWE. `assign_if_needed` rozrzuca przez `humanize_slot` (+/-15 min), `conversation`
  zapisuje wartosc czlowieka DOSLOWNIE - i to ta druga zbila 28/07 piec wpisow na jedna minute.
  Kontrola okna w `conversation` istnieje i CELOWO nie blokuje ("Ty decydujesz o terminie");
  wada lezy w zalozeniu, ze jeden material to jeden wiersz kolejki.
- **KADENCJA X: ZOSTAJE 4/DZIEN (decyzja Tomasza 27/07, NADPISUJE Managera).**
  Manager zdecydowal 26/07 zejscie z czterech na jeden, uzasadniajac to martwym zasiegiem
  (0-8 wyswietlen przy 16 obserwujacych) i tym, ze wszystkie realne kontakty w lejku przyszly
  z LinkedIna. **Tomasz decyzje cofnal tego samego dnia: "kadencja na X bez zmian, zostaja 4,
  nic nie zmieniam".** Zmiana NIGDY nie zostala wykonana na produkcji - `posts_per_day`
  stoi na `3-5` jak stalo, kolejka nie byla re-slotowana. To jest zapis, nie zalegly plan.
  Precedens ten sam co przy grafikach (kanon 25/07): w sprawach wlasnej marki decyzja
  wlasciciela bije decyzje Managera.
  Gdyby kiedys wracac do tematu: `ustaw posts_per_day dla AGS x na 1` (paragon ⚙️), potem
  `app.reslot dry 1` i `apply 1`. Zaden konsument nie wymaga poprawki - sprawdzone 27/07:
  `_daily_cap` bierze gorna granice zakresu, `slots._grid` i `proactive._expected` dolna,
  wiec wartosc jednoliczbowa jest spojna we wszystkich czterech miejscach czytajacych
  `posts_per_day`.
- RE-SLOTTER `app.reslot` (25/07, sprzatanie kolejki sprzed sufitu): kolejka X urosla
  do 64 wierszy z dniami po 7-9 postow (serie rozlewaly sie ZANIM powstal sufit).
  **v2 (decyzja Tomasza "cale serie razem"):** przeplanowuje CALA przyszla kolejke od dzis,
  SERIE w ciaglych blokach, czesci w kolejnosci NARRACYJNEJ (`id` = kolejnosc wstawiania
  przez stage_variant; NIE scheduled_for - ten rozprasza sie przy kolejnych re-slotach).
  Hook idzie przed rozwinieciem, seria nie jest porozrzucana. Sloty: rownomierna siatka
  dnia (10/12:30/15/17:30/20), max cap/dzien, LUDZKA MINUTA DETERMINISTYCZNA per id
  (`_human_minute` - nie losowa, inaczej dry != apply i brak idempotencji). Zmienia
  WYLACZNIE scheduled_for (media/grafiki Tomasza nietkniete). `docker exec cm-agent python
  -m app.reslot dry` = podglad, `... apply` = wykonanie. Idempotentny (drugi przebieg = 0
  zmian). Test: cm-agent/tests/test_reslot.py.
- STRAZNIK JEZYKA (20/07): przed zapisem do kolejki wariant sprawdzany z
  `channels.config.language_publish`; gdy kanal 'en' a tekst wyglada po polsku
  (`compliance.looks_polish`) -> `generate.translate_text` na EN. Karta HITL
  pokazuje dokladnie to, co wyjdzie na kanal.
- STRAZNIK META-NAGLOWKA (24/07, zgloszenie Tomasza ze zrzutu z X): przed zapisem
  do kolejki `compliance.strip_meta_header` zdejmuje z czubka tekstu meta-linie
  modelu - naglowek `# X Adaptation`, etykiete `LinkedIn:`, zapowiedz `Oto wersja:`
  i oplotki ```. Objaw: post #195 wyszedl na X z linia "# X Adaptation"; ani X, ani
  LinkedIn nie renderuja markdown, wiec to nie formatowanie, tylko smiec widoczny
  dla klienta. Ciecie jest zachowawcze (max 3 linie, tylko wzorce meta, hasztag NIE
  jest naglowkiem - po '#' musi stac spacja) i dziala TAKZE na kazdej czesci serii.
  Testy: `cm-agent/tests/test_meta_naglowek.py`. Sprzatanie wierszy sprzed poprawki:
  `docs/ops/meta_naglowki_kolejki_24072026.sql`.
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
- ETYKIETY KOLEJKI PO LUDZKU (23/07, konfuzja "[review] = niezatwierdzone"):
  raporty i kontekst pokazuja wiersz 'review' materialu ZATWIERDZONEGO jako
  "zatwierdzone, czeka na start" (reports._pq_label; JOIN na content_items.status).
  "DO ZATWIERDZENIA" widac tylko, gdy material realnie czeka na approve.
  Zatwierdzanie dzieje sie NA MATERIALE, nie na wierszach kolejki.
- 'held' to zamrazarka: po incydencie 13-19/07 wszystko zamrozone, sprzatniete
  wg dowodu 19-20/07 (sieroty pq bez materialu -> rejected; SQL wykonany,
  kontrola = 0). Nowe sieroty nie powstaja (fix matnav 'no').
- Publishery n8n NIE wolaja jeszcze `/wake` po callbacku - meldunek publikacji
  czeka do 30 s na poll petli (TODO przy najblizszej sesji n8n).
- Legacy AGS X Agent (Notion queue, cron 14/18/22) OFF od 25/06 - podwojnych
  publisherow NIE MA (dowod w n8n 19/07).
- linkedin_access_token z Token Generatora wygasa ~01/09/2026;
  linkedin_client_secret w DB bledny (OAuth callback nieuzywany).
