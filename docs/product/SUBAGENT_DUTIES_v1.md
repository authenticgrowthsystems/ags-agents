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

## 4. Stan wdrozenia: zbudowane vs brakuje (mapa na backlog)

| Obowiazek | Zbudowane | Brakuje |
|---|---|---|
| O1 Publikacja | sloty+okna, luki kadencji, slot-blokada, meldunek po callbacku | dowod X-obraz (obserwacja) |
| O2 Tresci | generacja PL/EN, nauka stylu, TRUTH_GUARD, filtr polszczyzny, multimedia foto/obraz/wideo | subagenty wizualne T6 (research-first) |
| O3 Comment-first | wizja zrzutu -> propozycje per autor -> guziki decyzji -> task_queue (E2E 09/07) | **konsument task_queue 'comment'** (P2); docelowo katalog obserwacji bez zrzutow |
| O4 Radar | inspirations + Content Intelligence Radar (ETL #71) | cykliczny radar per platforma w petli subagenta |
| O5 Metryki | kolektor LI gotowy; cost-ledger | App 2 CMA (LI), reczny wpis X, petla wnioski->strategia |
| O6 Relacje | contacts+engagement_log zasilane, logowanie komentarzy | konsolidacja kolumn contacts, agent CRM |
| O7 Zlecenia | - (wzorzec opisany w wizji CC) | brief-generator + kolejka zlecen dla Tomasza |
| O8 Komunikacja | rozmowy per konto, agent_messages, negocjacja slotow (1x kanon), eskalacja needs_human | **webhook wake agent-agent** (dzis czesciowo poll), swobodny dialog = ciagle iterowac |

Wniosek Managera: fundament (O1-O2) jest kompletny, przewaga konkurencyjna lezy w O3-O5
(zaangazowanie + metryki + nauka). To tam idzie nastepny sprint.

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
