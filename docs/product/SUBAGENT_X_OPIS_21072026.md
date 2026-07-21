# SUBAGENT X - pelny opis stanowiska i stanu (21/07/2026 wieczor)

Kanon warstw (Tomasz 21/07): **kregoslup, serce i mozg sa STALE** (warstwa programistyczna
+ baza danych + transport), **warstwa uzytkownika jest WYMIENNA** (dzis Telegram, jutro
Slack/web app - kontrakt /message {chat_id, text} + callbacki tego nie zmienia).
Ten dokument = recepta na kazdego kolejnego subagenta (IG, FB, TikTok, YT).

## 0. Misja i funkcja celu

Subagent X = pracownik, ktorego JEDYNYM zadaniem jest sukces marki na X.
Miary (w kolejnosci wag): zasieg -> zaangazowanie -> wzrost obserwujacych -> leady.
Rozliczany raportem dziennym (08:00) i tygodniowym (nd 20:00). Pelny opis stanowiska
(8 obowiazkow O1-O8): docs/product/SUBAGENT_DUTIES_v1.md.

## 1. Warstwy - co gdzie mieszka

| Warstwa | Co w niej jest | Konkrety |
|---|---|---|
| **MOZG (Python, cm-agent na Mikrus:8089)** | decyzje, tresc, rozmowa, nauka | planner.py (plan tygodnia+bramka tematow), generate.py (tresci+grafiki), channels.py (staging wariantow, serie, straznik jezyka), slots.py (sloty, ludzkie minuty), engagement.py (comment-radar, CRM relacji), matreview.py (karty), decisions.py (eskalacje+nauka), worker.py (petla stanow, ksiega, raporty), conversation.py (rozmowa+deterministyczne komendy) |
| **SERCE (baza ags_crd, pg_n8n)** | CALA pamiec i stan - jedyne zrodlo prawdy | content_items (materialy), post_queue (kolejka+harmonogram), published_posts (ksiega publikacji), x_post_metric_snapshots (metryki), contacts+engagement_log (relacje), task_queue, inspirations, brand_config (konfiguracja+Voice Bible), agent_decisions+agent_learning_log (nauka), cm_tasks (ledger kosztow LLM) |
| **KREGOSLUP (n8n = TYLKO transport, ZERO LLM)** | przepychanie zdarzen i wykonan | HITL U5pUZjy2yAhR1sWg (router wiadomosci/guzikow -> cm-agent), AGS Scheduler x1jJEbcWAe3FnpCa (cron co minute: Fetch Due -> HTTP OAuth1 do X -> ksiega), Subagent X Publisher (adapter webhook, dzis nieuzywany), Reports Cron, Timeout Checker |
| **INTERFEJS (wymienny)** | rozmowa i decyzje Tomasza | Telegram bot glowny (rozmowa, karty, guziki), bot #2 (kanal logowy AGS Alerts); przyszle konektory: Slack / web app (lista wiszacych zadan) - patrz BRIEF_INTAKE_UX pkt 3 |

Zasada tokenowa: **publikacja, harmonogram, metryki, transport i komendy deterministyczne
NIE uzywaja LLM.** LLM placi sie tylko za: tworzenie tresci, rozmowe, vision zrzutow,
syntezy. Szczegoly kosztow: sekcja 4.

## 2. ZROBIONE (stan LIVE 21/07 wieczor)

| Obowiazek | Co dziala | Jak zrealizowane (warstwa) |
|---|---|---|
| O1 Publikacja | plan tygodnia z bramka tematow (meta max 1/tydz, cap 20), zatwierdzanie 1 tapem, sloty w ludzkich minutach (+/-15, nigdy kwadrans), dlugie tresci automatycznie ciete na SERIE osobnych postow po slotach dnia, publikacja co do minuty | Python: planner+channels+slots; DB: content_items->post_queue; n8n: Scheduler co minute (czysty HTTP OAuth1, zero LLM) |
| O1 Ksiega prawdy | po publikacji wpis w published_posts + domkniecie materialu + potwierdzenie na Telegram; ZWIS alarmowany od SLOTU | n8n: Mark Published (SQL per-wiersz, naprawa 21/07); Python: reconcile_publications |
| O1 Grafiki | media jada z wierszem kolejki, upload chunked multipart wg kontraktu docs.x.com (naprawa 21/07 - **dowod live przy publikacji 22/07 16:11**), do kolejki tylko prawdziwe pliki (propozycje wizualne odfiltrowane) | n8n: Scheduler Publish To X (Telegram getFile -> X /2/media/upload); Python: channels._pub_media |
| O2 Tworzenie | generacja w glosie marki (Voice Bible v2.2 z DB), TRUTH_GUARD (zero zmyslen), filtr em-dash, jezyk per kanal ze straznikiem (EN-kanal nie przepusci polskiego), Inny kat, nauka stylu z edycji, Idea Bot (pomysl->research->seria) | Python: generate+compliance; DB: brand_config (voice), agent_learning_log |
| O3 Komentarze | zrzut cudzego posta -> propozycja komentarza PER AUTOR z czysta wklejka + guziki [Zatwierdz/Inny kat/Odrzuc]; odhaczenie = zapis wykonania na kontakcie | Python: engagement (vision) + matreview; DB: engagement_log, task_queue; interfejs: karty Telegram |
| O5 Metryki | kolektor Owned Reads $0.001/odczyt, snapshoty per tweet raz na dobe, raporty czerpia ze snapshotow (ZERO platnych odczytow przy raportach), profil 7d w raporcie dziennym | Python: x_owned_reads tick; DB: x_post_metric_snapshots -> published_posts.engagement_metrics |
| O6 Relacje (CRM) | nowa osoba ze zrzutu -> intake (bio+handle) -> klasyfikacja ICP guzikami (Buyer/Peer/Competitor/Partner) -> wpis contacts; stadium relacji cold->commented->replied->dm->offer->client (+ghosted); kazda interakcja w engagement_log | Python: engagement; DB: contacts (DDL 026), engagement_log; decyzje: agent_decisions |
| O8 Rozmowa | swobodny dialog per konto (partner: wlasne zdanie + pytanie), eskalacje GUZIKAMI z nauka per typ decyzji, raport dzienny 08:00 / tygodniowy nd 20:00, odprawa poranna | Python: conversation+decisions+reports; n8n: crony transportowe |
| Konfiguracja | okna publikacji, tryby, jezyk - komendy deterministyczne ("ustaw okno...") z paragonem ⚙️ bez LLM | Python: _config_route (regex PRZED LLM) |

## 3. DO ZROBIENIA (kolejnosc wg wartosci)

| Brak | Co da | Gdzie bedzie | Status |
|---|---|---|---|
| Pamiec watku rozmowy + menu intencji po wrzutce + dedup osob | koniec "topornej obslugi": subagent pamieta o czym mowa, po zrzucie pyta CO zrobic (guziki), domyka watki po kolei | Python: conversation/engagement | **W BUDOWIE (build/intake-ux, 21/07)** |
| Lacznik synchronizacyjny czat<->serwer | praca na abonamencie (pociag) trafia do bazy; czat dostaje stan z bazy | kontrakt RAPORT PRACY + /kontekst - patrz LACZNIK_SYNCHRONIZACYJNY_21072026.md | KONCEPT (decyzja Tomasza) |
| Samodzielne polowanie na posty do komentowania | O3 bez zrzutow od Tomasza (2-5 wpisow dziennie z katalogu obserwacji) | Python: engagement + kolektor | po baseline metryk |
| Petla nauki z metryk | wnioski format/godzina/temat -> automatyczna korekta slotow i strategii | Python: reports->planner | szkielet danych JUZ zbierany |
| Monitoring komentarzy pod WLASNYMI postami | odpowiedzi w oknie algorytmu (1h) | wymaga platnego odczytu X (decyzja kosztowa) | zaparkowane |
| Webhook wake agent-agent | zdarzenia zamiast czekania na tick (kanon 28/06) | n8n + cm-agent /wake | backlog P2 |
| Brief-generator zlecen dla Tomasza (O7) | nagrania/zdjecia zlecane z tygodniowym wyprzedzeniem | Python: proactive | niezaczete |
| X Articles (gotowiec via API draft) | artykuly na X bez recznej wklejki | n8n adapter (endpointy zweryfikowane) | backlog |
| Raport kosztow LLM per agent/tydzien | widzisz na co ida tokeny ZANIM przyjdzie rachunek | Python: reports z cm_tasks (ledger juz jest!) | do dopisania - male |

## 4. Jak subagent PAMIETA i jak oszczedzamy tokeny

**Pamiec = baza, nie kontekst LLM.** Subagent "pamieta", bo kazdy fakt jest wierszem:
co opublikowano (published_posts + embedding do dedupu), z kim rozmawia (contacts+
engagement_log: stadium, historia interakcji), czego sie nauczyl (agent_learning_log,
style_learned, agent_decisions), co ma w planie (content_items/post_queue), konfiguracja
i glos (brand_config). Restart kontenera NIC nie kasuje. (Wada biezaca: okno rozmowy
w Telegramie nie doklada wlasnej historii do kontekstu - to naprawia build INTAKE-UX.)

**Gdzie NIE placimy tokenow:** caly n8n (transport+publikacja+crony), Scheduler,
kolektor metryk (API X placone od odczytu, $0.001, nie tokenami), komendy deterministyczne
(/karty, /plan, ustaw okno, wklejone N, mtier), guziki (callback -> SQL), parsowanie
xlsx metryk.

**Gdzie placimy i jak malo:** tresc (tekst-matka: sonnet domyslnie, guzik haiku/opus per
material), syntezy researchu wg zlozonosci (low->haiku, medium->sonnet), vision tylko
gdy wrzucasz zrzut, rozmowa (najdrozsza pozycja - Opus dla CM; subagenci na tanszych).
Kazde wywolanie LLM laduje w **cm_tasks z kosztem** - ledger juz liczy, brakuje tylko
tygodniowego raportu "na co poszly tokeny" (tabela wyzej). Rachunki 12-15 EUR = glownie
rozmowa + generacja tygodniowego planu + vision; po raporcie kosztow bedzie to widac
czarno na bialym per pozycja.

## 5. Tryb samodzielny (bez CM)

Kanon [[project_subagent_object_toggle]]: subagent = sprzedawalny OBIEKT z przelacznikiem
standalone/supervised. Dzis dziala pod CM (supervised). W trybie samodzielnym te same
eskalacje i pytania, ktore kieruje do CM, kieruje BEZPOSREDNIO do uzytkownika (guziki
decyzji juz sa per subagent - mechanizm decisions.ask nie zalezy od CM). Sam wyciaga
wnioski z metryk (petla nauki - patrz DO ZROBIENIA) i pyta wlasciciela, gdy brak nadzorcy.
