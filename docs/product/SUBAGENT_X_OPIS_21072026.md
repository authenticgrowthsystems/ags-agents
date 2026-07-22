# SUBAGENT X - pelny opis stanowiska i stanu (AKTUALIZACJA 22/07/2026 ~17:45)

Kanon warstw (Tomasz 21/07): **kregoslup, serce i mozg sa STALE** (warstwa programistyczna
+ baza danych + transport), **warstwa uzytkownika jest WYMIENNA** (dzis Telegram, jutro
Slack/web app - kontrakt /message {chat_id, text} + callbacki tego nie zmienia).
Ten dokument = recepta na kazdego kolejnego subagenta (IG, FB, TikTok, YT).
REZIM STABILIZACJI od 22/07 ~17:45: zero nowych funkcji; tylko poprawki z zywych
dowodow i dokumentacja; cel = 48h pracy bez interwencji, wtedy status "GOTOWY CALKIEM".

## 0. Misja i funkcja celu

Subagent X = pracownik, ktorego JEDYNYM zadaniem jest sukces marki na X.
Miary (w kolejnosci wag): zasieg -> zaangazowanie -> wzrost obserwujacych -> leady.
Rozliczany raportem dziennym (08:00) i tygodniowym (nd 20:00). Opis stanowiska
(8 obowiazkow O1-O8): docs/product/SUBAGENT_DUTIES_v1.md.

## 1. Warstwy - co gdzie mieszka

| Warstwa | Co w niej jest | Konkrety |
|---|---|---|
| **MOZG (Python, cm-agent na Mikrus:8089)** | decyzje, tresc, rozmowa, nauka | planner.py (plan tygodnia+bramka tematow), generate.py (tresci+grafiki+straznik preambuly), channels.py (staging, serie, straznik jezyka, filtr mediow), slots.py (sloty, ludzkie minuty), engagement.py (comment-radar, CRM, raport pracy), matreview.py (karty), decisions.py (eskalacje po ludzku+nauka), worker.py (petla stanow, gotowce, raporty), conversation.py (rozmowa, pamiec watku, menu intencji, intencja ze slow) |
| **SERCE (baza ags_crd, pg_n8n)** | CALA pamiec i stan - jedyne zrodlo prawdy | content_items, post_queue, published_posts (ksiega), x_post_metric_snapshots, contacts+engagement_log (CRM relacji), inspirations, brand_config (konfiguracja+Voice Bible), agent_decisions+agent_learning_log, cm_tasks (ledger kosztow LLM) |
| **KREGOSLUP (n8n = TYLKO transport, ZERO LLM)** | przepychanie zdarzen i wykonan | HITL U5pUZjy2yAhR1sWg (router), AGS Scheduler x1jJEbcWAe3FnpCa (cron co minute, ROUTER PLATFORM: x i linkedin; publikacja HTTP + ksiega per-wiersz), Reports Cron, Timeout Checker |
| **INTERFEJSY (wymienne)** | rozmowa i decyzje Tomasza | Telegram bot glowny + bot #2 (kanal logowy); CZAT NA ABONAMENCIE przez Lacznik (RAPORT PRACY + stan gry z Notion); przyszle: Slack / web app |

Zasada tokenowa: publikacja, harmonogram, metryki, transport, komendy deterministyczne,
parser raportu pracy i zapis reakcji NIE uzywaja LLM. Koszt: ~$4.7/tydz. Anthropic
(rozbior 22/07: planner+rozmowy = 60%), Researcher wg zlecen, kolektor $0.001/odczyt.

## 2. ZROBIONE (stan LIVE 22/07 ~17:45)

| Obowiazek | Co dziala | Jak zrealizowane |
|---|---|---|
| O1 Publikacja | plan tygodnia z bramka tematow, zatwierdzanie 1 tapem (karta z kopia PL + guziki grafiki), sloty w ludzkich minutach, serie zamiast klocow, publikacja co do minuty przez Scheduler | Python: planner+channels+slots+hitl; n8n: Scheduler (HTTP, zero LLM) |
| O1 Ksiega prawdy | published_posts + domkniecie materialu per-wiersz + potwierdzenie na Telegram; ZWIS liczony od SLOTU; gotowce reczne domykane komenda `wklejone <id>` | n8n: Mark Published; Python: reconcile |
| O1 Grafiki | media z file_id jada z wierszem; upload chunked v3 (initialize/append/finalize wg docs.x.com per-endpoint); propozycje wizualne odfiltrowane ze sciezki publikacji | n8n: Scheduler Publish To X; Python: _pub_media. UWAGA: pierwszy zywy dowod v3 = publikacja 22/07 17:55 |
| O2 Tworzenie | Voice Bible z DB, TRUTH_GUARD, straznik jezyka (EN-kanal nie przepusci polskiego), straznik preambuly (meta-komentarz modelu ucinany), Inny kat, nauka stylu z edycji, Idea Bot | Python: generate+compliance |
| O3 Komentarze | zrzut -> propozycja per autor z czysta wklejka; [Wkleilem/Wyslalem] = 1 tap domyka cykl + stadium CRM; jezyk odpowiedzi DM = jezyk rozmowcy | Python: engagement+conversation (INTAKE-UX) |
| O5 Metryki | kolektor Owned Reads (snapshoty per tweet 1x/doba, prog alertu 300), raporty ze snapshotow bez platnych odczytow, profil 7d | Python: x_collector; DB: x_post_metric_snapshots |
| O6 Relacje (CRM) | intake osob ze zrzutow (1 karta/24h, dedup wariantow nazwy), stadium cold->...->client, OBOWIAZEK KLASYFIKACJI z raportow pracy (tier tylko ze zweryfikowanego profilu), zapis reakcji (follow/like) bez LLM | Python: crm+engagement (INTAKE-UX+Lacznik) |
| O8 Rozmowa | pamiec watku (takze trasy deterministyczne), menu intencji po wrzutce (JEDNA karta, wykonanie po kolei), INTENCJA ZE SLOW wykonywana bez pytania ("zaktualizuj w bazie", "skomentuj"...), zgloszenia po ludzku i wytluszczone (bez #id/[typow]), HTML bez surowych gwiazdek | Python: conversation+decisions |
| Lacznik | praca na abonamencie wraca PLIKIEM RAPORT PRACY (parser bez LLM, idempotencja), /kontekst + strona Notion "Stan gry" dla czatu; masterprompt czatowy X_v2 | Python: engagement+reports+sync; docs/product/masterprompty-czat/ |

## 3. DO ZROBIENIA (backlog - NIC z tego nie wchodzi w rezimie stabilizacji)

| Brak | Co da | Status |
|---|---|---|
| Dowod 48h bez interwencji | status GOTOWY CALKIEM w macierzy | OBSERWACJA od 22/07 wieczor |
| Anty-powtorka otwarc | generator nie wpada w rytm ("Saturday morning" x3) | backlog (incydent 22/07) |
| Grupowanie przypomnien per autor | 3 warianty odpowiedzi = 1 przypomnienie, nie 3 | backlog (kosmetyka) |
| Raport kosztow LLM tygodniowy | "na co poszly tokeny" bez pytania BE | backlog (cm_tasks juz liczy) |
| Poprawki raportu dziennego | stopka metryk, wyswietlenia profilu ze snapshotow, flaga przeterminowanych slotow | backlog (audyt 22/07) |
| Samodzielne polowanie na posty do komentowania | O3 bez zrzutow | po baseline metryk |
| Petla nauki z metryk -> sloty/formaty | O5 pelny | po baseline |
| Webhook wake agent-agent | zdarzenia zamiast ticku | backlog P2 |
| Callback X Publishera per-row | OBOWIAZKOWE przed jakimkolwiek powrotem trybu webhook | mina opisana w kolejka-publikacja.md |
| X Articles, brief-generator O7 | jak wczesniej | backlog |

## 4. Pamiec i tryb samodzielny

Bez zmian od v1 opisu: pamiec = baza (restart nic nie kasuje); tryb standalone =
te same eskalacje kierowane do wlasciciela zamiast CM (decisions.ask nie zalezy od CM).
Historia watku rozmowy dziala od INTAKE-UX (B1).
