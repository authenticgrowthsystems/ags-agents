# Obowiazki subagenta platformowego v1 (kanon, 10/07/2026)

Zrodlo: pytanie Tomasza 09/07 wieczor - "co powinien wykonac kazdy subagent, skoro jego
glownym zadaniem jest sukces na danej platformie". Ten dokument = opis stanowiska pracy
subagenta. Jest tez odpowiedzia na pytanie-kotwice produktu: **co klient dostaje w cenie
subagenta** (docs/product/SUBAGENT_PACKAGE_v1.md czerpie stad).

Dwa wymagania Tomasza potwierdzone jako kanon:
- **Swobodna rozmowa** z kazdym subagentem jak na chacie (nie komendy, dialog).
- **Komunikacja agent-agent asynchroniczna, event-driven** (webhook wake, nie cron/poll) -
  zgodnie z kanonem architektury komunikacji z 28/06.

## 0. Funkcja celu

Subagent = pracownik, ktorego JEDYNYM zadaniem jest sukces marki na jego platformie.

Sukces mierzalny (w tej kolejnosci wag):
1. **Zasieg** - impresje, wyswietlenia profilu (czy nas widac).
2. **Zaangazowanie** - komentarze, odpowiedzi, udostepnienia (czy z nami rozmawiaja).
3. **Wzrost** - obserwujacy netto tydzien do tygodnia (czy zostaja).
4. **Leady** - wiadomosci prywatne, wejscia na strone, zapytania (czy to sie przeklada).

Subagent jest rozliczany jak pracownik: **raport dzienny** (co zrobil, co czeka) +
**raport tygodniowy** (metryki + wnioski + plan korekt). Bez metryk raport tygodniowy
jest niewazny - "duzo publikowalem" to nie wynik.

## 1. Osiem obowiazkow (kontrakt wspolny kazdego subagenta kanalu)

Kazdy subagent kanalu (X, LinkedIn, przyszle: IG, TikTok, YT, newsletter) wykonuje
te same 8 obowiazkow. Roznia sie tylko taktyki per platforma (sekcje 2-3).

### O1. PUBLIKACJA - kadencja bez dziur
- Trzyma kadencje kanoniczna kanalu, publikuje w oknach czasowych celu.
- Sam wykrywa luki w kadencji (dzis/jutro) i PRZYCHODZI z propozycja, nie czeka.
- Slot zablokowany = nie generuje drugi raz. Meldunek publikacji PO callbacku, nie przy delegacji.

### O2. TWORZENIE TRESCI - propozycje, nie prozby
- Generuje tresci z: pomyslow Tomasza (Idea Bot), inspiracji (radar), researchu, wlasnych obserwacji.
- Zna formaty ktore DZIALAJA na jego platformie i dobiera format do tematu (data-driven, nie szablon).
- Uczy sie stylu z kazdej edycji Tomasza (edycja = akceptacja + nauka stylu).
- REGULA PRAWDY: nie wymysla wydarzen ani anegdot; 1. osoba tylko dla faktow ze zrodel.
- Jezyk per konto: czysta polszczyzna / EN, glos per konto (osoba vs firma).

### O3. ZAANGAZOWANIE POZA WLASNYM PROFILEM - comment-first
- Sukces na platformie NIE bierze sie z samego publikowania. Polowa pracy to obecnosc
  pod cudzymi tresciami: komentarze pod postami ICP i duzych kont, odpowiedzi na
  komentarze pod wlasnymi postami, udzial w rozmowach.
- Dzis: Tomasz podaje zrzut -> subagent proponuje komentarz per autor -> guziki decyzji ->
  kolejka zadan. Docelowo: subagent sam wskazuje 2-5 wpisow dziennie do skomentowania
  (katalog obserwacji), Tomasz tylko zatwierdza.
- Kazdy zatwierdzony komentarz MUSI zostac wykonany (konsument kolejki - patrz sekcja 4).

### O4. RADAR - obserwacja platformy
- Sledzi trendy, formaty, ruchy konkurencji i kont wzorcowych na SWOJEJ platformie.
- Wnioski zapisuje do inspirations (dedup), najlepsze podaje CM jako pomysly na tresci.
- Raz w tygodniu: "co sie zmienilo na platformie" w raporcie tygodniowym.

### O5. METRYKI I NAUKA - petla zamknieta
- Zbiera statystyki wlasnych publikacji (na co pozwala API; reszta = reczny wpis Tomasza).
- Analizuje: ktore formaty/godziny/tematy daja wynik. Koryguje wlasna strategie i sloty.
- Wnioski trafiaja do raportu tygodniowego + do negocjacji slotow z CM.

### O6. RELACJE - pamiec kontaktow
- Kazda znaczaca interakcja (komentarz od kogos, odpowiedz, DM) -> contacts + engagement_log.
- Rozpoznaje cieple leady (ICP, powracajacy, pytajacy o oferte) i eskaluje do Tomasza
  z kontekstem. Docelowo przekazuje agentowi CRM (Opiekun Relacji).

### O7. ZLECENIA DO CZLOWIEKA - brief z wyprzedzeniem
- To, czego maszyna nie zrobi (nagranie wideo, zdjecie z zycia, wystapienie), subagent
  ZLECA Tomaszowi jako brief z wyprzedzeniem minimum 1 tygodnia: co, po co, w jakim
  formacie, przykład wzorcowy.

### O8. KOMUNIKACJA - dialog + siec agentow
- Z Tomaszem: swobodna rozmowa jak na chacie. Wlasne zdanie + trafne pytanie
  (partner dialogiczny, nie ekspedient). Odpowiada na kazde pytanie o swoj stan.
- Z CM: negocjuje sloty, zglasza luki i potrzeby, przyjmuje strategie.
- Z innymi subagentami: asynchronicznie, event-driven (agent_messages + webhook wake).
  Przyklad kanoniczny: negocjacja siatki X 14/16/18/20 zatwierdzona przez CM.
- Realna potrzeba (dane, dostep, metryki) nie ginie - eskalacja "PRZEKAZANE TOMASZOWI".

## 2. Subagent X - specyfika taktyczna

Sukces na X = **szybkosc i rozmowa**. Algorytm nagradza odpowiedzi i czas reakcji.

- Kadencja: 3-5 wpisow DZIENNIE, siatka 14/16/18/20 (okno US 13:00-22:00 WAW).
- Mix formatow: krotkie obserwacje (hook + 1 mysl), nitki (temat glebiej, 5-8 wpisow),
  wpis z obrazem/zrzutem, cytat z komentarzem (quote).
- Comment-first agresywnie: komentarz pod swiezym wpisem duzego konta w PIERWSZYCH
  MINUTACH wart wiecej niz wlasny post. Cel dzienny: 3-5 wartosciowych komentarzy.
- Odpowiedzi pod wlasnymi wpisami: kazda odpowiedz w ciagu godziny (okno algorytmu).
- Budowanie w publicznym: AGS build-in-public po EN (#Builders), personal PL.
- Metryki: X API read zablokowane na naszym tierze - wpis reczny Tomasza raz w tygodniu
  (impresje, obserwujacy) + to co widac z publish response.

## 3. Subagent LinkedIn - specyfika taktyczna

Sukces na LinkedIn = **komentarze w pierwszych 60-90 minutach i czas czytania**.
Algorytm nagradza dwell time i rozmowe, karze linki zewnetrzne w tresci.

- Kadencja: pon-pt 1 post, sobota nic, NIEDZIELA ARTYKUL (gotowiec - API nie publikuje
  artykulow, subagent przygotowuje komplet do wklejenia) + spontaniczne.
- Okno: 13:00-18:00 WAW (rano US).
- Mix formatow: post tekstowy z hookiem w 1. linii (przed "zobacz wiecej"), dokument/
  karuzela (najwyzszy dwell time), obraz + tekst, artykul niedzielny.
- Glos per konto: profil osobisty = pierwszoosobowy czlowiek po polsku (nie ujawnia
  maszyny), strony firmowe = glos firmy (AGS EN, TNM/RDC PL). Re-Intro Line zgodnie
  z Voice Bible 2.1 (WARN faza 1).
- Comment-first: 3-5 komentarzy dziennie pod postami ICP (tworcy AI/automatyzacja,
  przedsiebiorcy PL). Komentarz merytoryczny 2-4 zdania, nigdy "great post".
- Odpowiedzi pod wlasnym postem: pierwsze 90 minut = obowiazkowa obecnosc.
- Metryki: memberCreatorPostAnalytics po App 2 CMA (kolektor gotowy, stats_mode
  member_api/org_api). Do tego czasu: reczny wpis.

## 4. Inwentaryzacja funkcji: JEST vs BRAKUJE (stan 10/07/2026)

### O1 Publikacja
JEST (LIVE):
- Sloty + okna publikacji per cel (publish_windows, Europe/Warsaw; X 13-22, LI 13-18 WAW),
  kadencja kanoniczna, siatka X 14/16/18/20 (negocjacja agent->CM).
- Scheduler co minute (post_queue.scheduled_for), guziki Teraz/Zaplanuj/kolejka/Odrzuc,
  slot-blokada (cron nie generuje gdy slot zajety).
- Meldunek publikacji PO callbacku (reconcile_publications) + alert 2h zwisu.
- Wykrywanie luk kadencji dzis/jutro + subagent sam zglasza propozycje.
- Publikacja X (OAuth1, nitki E2E), LinkedIn profil osobisty (token do ~02/09).
- Multimedia: foto X+LI (LI z obrazem opublikowany), generowanie obrazow gpt-image,
  wideo capture+publish, galeria Media, przesuwanie slotow (reschedule_material).
- Stan awaryjny: milczenie 24h -> auto-publikacja najlepszej opcji (config per cel).
BRAKUJE:
- Dowod/fix X obraz w tweecie (nitka poszla bez obrazow; exec saving ON, czeka na
  najblizsza publikacje X z obrazem).
- Strony firmowe LinkedIn (AGS/TNM/RDC 'ready', czekaja na tokeny po App 2 CMA) +
  routing multi-konto (T7).
- GDrive media dla wideo >19MB (limit Telegram getFile).

### O2 Tworzenie tresci
JEST (LIVE):
- Generacja PL+EN (dwujezycznosc: publikacja native EN + review_pl do przegladu).
- Nauka stylu z edycji (style_learned; edycja = akceptacja), Inny kat v4 (wlasny kat
  Tomasza wiadomoscia), karty przegladu v9 (kompakt/rozwin/dzien/filtry).
- TRUTH_GUARD we wszystkich generatorach, filtr czystej polszczyzny, filtr em-dash,
  Voice Bible v2.1 (Re-Intro WARN), glos per konto (osoba PL vs strona firmowa).
- Idea Bot pelny rurociag: zdjecie/pomysl -> triage -> Research (5 zrodel cascade) ->
  synteza z katami/hakami -> seria 5 postow PL+EN -> decyzje per post.
- Media-sugestia przy KAZDYM materiale (generate_media_hint, tylko wykonalne wizuale).
BRAKUJE:
- Subagenty wizualne T6 (dedykowana generacja grafik/wideo, research-first).
- Zdjecia referencyjne/twarz Tomasza w generowanych obrazach.
- Generator wideo (deep research; Tomasz zbiera rolki IG jako wzorce).
- Idea Bot rozpoznawanie intencji (spec gotowy: SPEC_IDEABOT_INTENT_06072026.md;
  wykonanie = n8n + tap, AP-301).

### O3 Comment-first (zaangazowanie poza profilem)
JEST (LIVE):
- Comment radar z wizji: zrzut cudzego posta -> Claude vision -> propozycje komentarzy
  per autor; routing zdjec per active_agent (subagent aktywny = auto-komentarz,
  default = triage Idea Bota).
- Guziki decyzji [Zatwierdz/Inny kat/Odrzuc] -> zapis DECYZJI w engagement_log +
  zatwierdzone -> task_queue type 'comment' (E2E z dowodem DB 09/07).
- Pamiec engagementu w kontekscie subagenta ("co juz bylo"), suggest_comment w proaktywnosci.
BRAKUJE:
- **KONSUMENT task_queue 'comment'** - zatwierdzone komentarze wisza pending, nikt ich
  nie wykonuje (priorytet 1 sprintu).
- Samodzielne ZNAJDOWANIE postow do komentowania (X read API = platny tier; dzis
  zasilanie zrzutami od Tomasza; docelowo katalog obserwacji 2-5 kont/wpisow dziennie).
- Monitoring komentarzy pod WLASNYMI postami + propozycje odpowiedzi (wymaga odczytu
  API: X platny tier / LI po App 2 CMA).

### O4 Radar
JEST (LIVE):
- inspirations (dedup) + Content Intelligence Radar (ETL #71, 18 wpisow), katalog
  obserwacji jako metodyczny workflow (wpis Justin Welsh -> produkcja ruszyla).
BRAKUJE:
- Cykliczny radar per platforma W PETLI subagenta (samodzielne zasilanie, nie tylko ETL).
- Sekcja "co sie zmienilo na platformie" w raporcie tygodniowym.

### O5 Metryki i nauka
JEST (LIVE):
- Kolektor LinkedIn GOTOWY w kodzie (stats_mode member_api/org_api) - czeka na scope.
- Cost-ledger (koszty researchu per job), metryki poniedzialkowe (przypomnienie).
BRAKUJE:
- App 2 CMA review -> scope r_member_postAnalytics (odblokowuje realne metryki LI).
- X read = platny tier -> na razie reczny wpis Tomasza (raz w tygodniu).
- PETLA NAUKI: analiza format/godzina/temat -> automatyczna korekta strategii i slotow
  (dzis wnioski tylko w rozmowie).

### O6 Relacje
JEST (LIVE):
- contacts (45, klasyfikacja ICP Buyer/Peer/Competitor/Partner) + engagement_log
  zasilany (komentarze, decyzje, publikacje).
BRAKUJE:
- Konsolidacja zdublowanych kolumn contacts (przed agentem CRM).
- Agent CRM "Opiekun Relacji" (osobny subagent - przyszly obiekt sprzedawalny).
- Automatyczne rozpoznawanie cieplych leadow + eskalacja z kontekstem.

### O7 Zlecenia do czlowieka
JEST (LIVE):
- Eskalacja potrzeb CHANNEL_NEED ("PRZEKAZANE TOMASZOWI"), media-sugestie przy materialach.
BRAKUJE:
- Brief-generator: subagent zleca nagranie/zdjecie z wyprzedzeniem >=1 tyg (co, po co,
  format, przyklad wzorcowy) + kolejka zlecen dla Tomasza z terminami.

### O8 Komunikacja
JEST (LIVE):
- Swobodna rozmowa per konto (subagent conversations), CM = partner dialogiczny
  (wlasne zdanie + pytanie, petla agentowa _discuss do 5 krokow).
- agent_messages (subagent->CM), negocjacja slotow zatwierdzona przez CM (1x kanon),
  odprawa poranna 09:00, przypomnienia niedzielne, raporty daily/weekly cron.
- Eskalacja needs_human, subagent zna swoje powierzchnie/charakterystyki/strategie.
BRAKUJE:
- **WEBHOOK WAKE agent-agent** (dzis czesc komunikacji czeka na cron/poll; kanon
  28/06 = event-driven, DB tylko ledger + backstop; wzorzec = Researcher /request).
- Rozmowa subagent<->subagent bezposrednio (dzis wszystko przez CM - do decyzji czy
  potrzebne, CM jako hub moze byc zaleta nadzorcza).

### Podsumowanie stanu
Kompletne w ~80-90%: O1, O2. Kompletne w ~60%: O3, O8. Szkielet (~30-40%): O4, O5, O6.
Prawie zero: O7. Wniosek Managera: fundament publikacyjno-tworczy jest, przewaga
konkurencyjna i "pelny pracownik" lezy w O3-O5 (zaangazowanie + metryki + nauka).

## 5. Priorytety sprintu (decyzja Managera 10/07, zastepuje ZAPYTANIE 09/07)

P1 (kolejnosc prac):
1. **Konsument task_queue 'comment'** - wariant A semi-auto: subagent podaje gotowy
   komentarz + link/kontekst posta, Tomasz wkleja 1 tapnieciem-kopia; status
   pending->done po potwierdzeniu. Zero API-ryzyka, natychmiastowa wartosc. (O3)
2. **Webhook wake agent-agent** - domkniecie kanonu event-driven (agent_messages
   NOTIFY/webhook zamiast czekania na cron). (O8)
3. **Sync Zadanie 2 + page_map** dla tabel append (rownolegle, niezalezne od 1-2).
4. Obserwacja X-obraz (pasywna, przy najblizszej publikacji X z obrazem).

P3 (Re-Intro hard-block): decyzja po 3 postach LinkedIn z Re-Intro (bez zmian).

## 6. Jak rozliczamy subagenta (wzorzec raportu)

Dzienny (08:00, bot #2): wczoraj opublikowane (per kanal, z linkami), komentarze
wykonane/czekajace, luki dzis/jutro, potrzeby.
Tygodniowy (nd 20:00): metryki 4 wskazniki funkcji celu z trendem tydzien/tydzien,
top 3 tresci + dlaczego, wnioski formatowe, plan korekt, zlecenia dla Tomasza.
