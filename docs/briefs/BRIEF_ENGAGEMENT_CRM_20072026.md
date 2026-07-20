# BRIEF BUILDU: ENGAGEMENT-CRM subagenta (20072026) - budowniczy: BE-ENGAGEMENT

Wywolanie sesji (nowe okno; Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_ENGAGEMENT_CRM_20072026.md zbuduj`
CZYTAJ NAJPIERW: docs/komponenty/rozmowa-cm.md + karty-hitl.md + docs/GOTOWOSC_PRODUKTU.md
(kanon: dokumentacja zamiast archeologii kodu).

## 0. Tryb rownolegly

Wlasny worktree+galaz `build/engagement-crm` od origin/claude/silly-blackwell-dfc32d
(wzorzec sekcji 0 briefow 19/07). Zakaz deployu/psql/n8n; DDL jako plik db/026 w commicie.
Po DONE: merge + deploy przez BE/integratora.

## 1. PO CO (feedback Tomasza 20/07 z pierwszej realnej sesji komentowania na telefonie)

Comment-radar dziala E2E, ale: (a) UX telefonu bolal (NAPRAWIONE 20/07 inline: kazda
propozycja = osobna czysta wiadomosc; ten build NIE dubluje tego), (b) osoby, ktore
komentujemy, NIE trafiaja do CRM, (c) subagent gubi watek propozycji, (d) dwa zrzuty
jednego posta = dwie "osoby". Kanon od poczatku projektu: "zapisywac w jakie relacje
wchodze z jakimi ludzmi" - baza contacts ISTNIEJE (45 osob, icp_tier Buyer/Peer/
Competitor/Partner z migracji #71) i lezy odlogiem.

## 2. CO budujemy

**A. KAZDA PROPOZYCJA = OSOBNY REKORD Z GUZIKAMI (koniec batchy).**
Dzis: jeden wpis engagement_log na caly zrzut, guziki batchowe, decyzje tekstem gina.
Cel: propozycja per AUTOR = wlasny wiersz engagement_log + wlasne guziki cmt:ok|angle|no
POD TA KONKRETNA wiadomoscia (naglowek-autor / czysta wklejka / guziki - trzecia wiadomosc
w moim fixie 20/07 to wlasnie guziki per autor). ZERO decyzji rozpoznawanych tylko z prozy.

**B. CRM: OSOBA OBOWIAZKOWA.**
Przy kazdej propozycji: dopasuj autora do `contacts` (po handle/nazwie; kolumny sprawdz
w SCHEMA - AP-304!). NIEZNANY = subagent WYMUSZA intake ZANIM zamknie temat:
"Nowa osoba: <handle>. Nie znam jej. Wejdz na profil i daj zrzut - zaloze wpis" ->
zrzut profilu -> wizja -> INSERT contacts (imie, handle per platforma, bio-skrot,
icp_tier PROPONOWANY przez model + zatwierdzany guzikiem [Buyer/Peer/Competitor/Partner]).
MULTI-PLATFORMA: jedna osoba, wiele kont - kolumna/jsonb `handles` {x:..., linkedin:...}
(DDL 026 jesli trzeba ALTER; sprawdz najpierw istniejace kolumny contacts!).
Kazda interakcja (komentarz/DM/oferta) LINKUJE do contact_id w engagement_log
(ALTER engagement_log + contact_id FK, DDL 026) + pole stadium relacji na kontakcie
(np. cold/commented/replied/dm/offer/client - CHECK; Tomasz zatwierdzi skale guzikami).

**C. PAMIEC WATKU + DOMYKANIE PETLI.**
Propozycja NIEZDECYDOWANA (Tomasz przeskoczyl autora) NIE ginie: status 'proposed'
w engagement_log; subagent na pytanie "co wisi?" listuje; po 24h sam przypomina
(wzorzec stale_approval z decisions.py - guziki [Wyslalem][Pomin][Pokaz jeszcze raz]).
Zatwierdzone-a-niepotwierdzone (task_queue comment in_progress > 24h) - to samo:
"wyslales komentarz do X? [Tak, odhacz][Nie, pomin]". Zadnego zgadywania.

**D. MULTI-ZRZUT = JEDEN POST.**
Telegram album ma media_group_id - zrzuty z jednej grupy traktuj jako JEDEN post
(sklejona analiza wizji). Zrzuty wyslane osobno w <60 s: dopytaj JEDNYM pytaniem
("to czesci jednego posta czy rozne posty?") zamiast produkowac duchy autorow.
(Dowod incydentu: 2 zrzuty dlugiego posta -> "Dhairya" i "Vladimir" jako 2 osoby.)

**E. DOKUMENTACJA (kanon pkt 6):** nowy komponent docs/komponenty/engagement-crm.md
(szablon jak pozostale) + aktualizacja GOTOWOSC_PRODUKTU (obiekt "Subagent X" dostaje
w MVP: CRM relacji) + STATUS w rozmowa-cm.md. Klient kupujacy subagenta X ma z dokumentu
wiedziec jak to dziala i czego wymaga na starcie.

DoD (tap-testy):
- [ ] zrzut nieznanej osoby -> propozycja + wymuszony intake -> wpis w contacts z tierem
- [ ] zrzut znanej osoby -> propozycja pokazuje kontekst relacji ("komentowales 3x, stadium: commented")
- [ ] przeskoczenie autora -> po 24h przypomnienie guzikami; "co wisi?" listuje
- [ ] album 2 zrzutow -> JEDNA analiza, jeden autor
- [ ] engagement_log.contact_id wypelnione dla nowych interakcji

## 3. Czego NIE dotykac

Fix czystej wklejki 20/07 (dziala), publikacja, planner, dedup. Notion contacts NIE ruszac
(DB=SSOT, mirror osobno). Konsolidacja WSZYSTKICH kolumn contacts = poza zakresem
(znany dlug "konsolidacja przed agentem CRM") - dodajesz tylko co niezbedne.

## 4. Stan zastany

contacts 45 wpisow (icp_tier z Notion #71; Founders List = instrukcja), engagement_log
(notes z DECYZJA, kind comment), task_queue 'comment' + consumer_tick z Done/Skip,
rodzina cmt: w HITL routuje do /cmt, decisions.py (wzorzec przypomnien), media_group_id
w surowym update Telegrama (sprawdz co przekazuje n8n - moze wymagac dopisania pola
w Detect Update Type: WOLNO, wzorzec patcherow z backupem).

## 5. Udzial Tomasza

psql 026 + rebuild po merge; skala stadiow relacji + tiery guzikami; 4-5 tap-testow.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_engagement_crm.md + komponent + macierz +
masterprompt + pamiec + STATUS tu.

STATUS = ZBUDOWANE (20/07, BE-ENGAGEMENT, galaz build/engagement-crm) - kod + DDL 026 +
patch n8n (plik) + dokumentacja w commicie; czeka: merge przez integratora, psql 026 PRZED
rebuildem, rebuild cm-agent, uruchomienie patcha n8n, decyzja Tomasza o skali stadiow
(CHECK dopuszcza cala proponowana skale cold/commented/replied/dm/offer/client), 5 tap-testow
DoD. Raport: docs/cm/RAPORT_do_Managera_20072026_engagement_crm.md
