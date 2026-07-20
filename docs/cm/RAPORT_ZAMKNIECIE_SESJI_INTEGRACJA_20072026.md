# RAPORT ZAMKNIECIA SESJI: INTEGRACJA 4 BUILDOW (19-20/07/2026, BE-INTEGRATOR)

Sesja: "skladanie dokumentow integracji" (start 19/07 ~23:50, koniec 20/07 ~10:30, z przerwa
noc na sen Tomasza). Zakres wg docs/briefs/BRIEF_INTEGRACJA_19072026.md. Sesja ARCHIWIZOWANA
po tym raporcie - pelny stan przeniesiony do repo + pamieci trwalej.

---

## CZESC I - DLA MANAGERA AGS (stan biznesowo-operacyjny)

### Co system umie od dzis (a wczoraj nie umial)

1. **Widzi wlasne wyniki na X.** Kolektor Owned Reads zbiera raz na dobe prywatne metryki
   (impressions, engagements, profile clicks) wszystkich postow z 29 dni. Koniec recznego
   wpisywania i koniec slepoty metrycznej z tygodnia 13-19/07. Koszt ~$0.15/dzien,
   potwierdzony w konsoli X ($0.01 za caly test), trzy linie obrony kosztow (alert >200,
   twardy stop 500, Spend Cap $20).
2. **Ostrzega przed powtarzaniem tez.** Bramka duplikacji porownuje temat nowego materialu
   z opublikowanymi (30 dni) i pisze na karcie "⚠️ DUPLIKACJA: podobienstwo 0.60 do ...".
   Informuje, nie blokuje - decyzja zawsze u Tomasza. Zlapala na zywo dokladnie ten post,
   ktory 11/07 zdublowal sie mimo instrukcji w prompcie.
3. **Komendy konfiguracyjne sa deterministyczne.** "ustaw okno publikacji dla AGS x na
   13:00-22:00" idzie przez regex prosto do bazy z paragonem ⚙️ - LLM nie ma jak "zalatwic"
   bez wykonania. Odrzucenie karty sprzata cala serie z kolejki (koniec wiecznych sierot).
4. **CM czyta swiat (podklad niedzielny).** W sobote rano sam zleca research tygodnia AI,
   syntetyzuje 3 kandydackie tezy z linkami i wysyla Tomaszowi jako podklad do RECZNEGO
   artykulu. Zero wpisow do kolejki. Fallback uczciwy: gdy research nie dojedzie, mowi to
   wprost i znakuje fakty "(do weryfikacji)" - sprawdzone na zywo.

### Decyzje podjete w sesji (Tomasz guzikami)

- Bramka duplikacji: fix od reki (1 linia) zamiast odkladania - po pomiarze na zywym
  korpusie, ktory obalil zalozenie projektowe (szczegoly w czesci II).
- Awaria Researchera: NIE drazyc w tej sesji - brief naprawczy do rownoleglego okna,
  praca "z boku" (BRIEF_NAPRAWA_RESEARCHERA_20072026, STATUS READY).

### Incydent wart uwagi Managera: test prawdy zadzialal

CM trzykrotnie oglosil "Zapisane" przy trzecim tescie bramki - a material NIE istnial
w bazie (narzedzie sie nie odpalilo). Skonfrontowany pytaniem o paragon: uczciwie przyznal
brak dowodu, nazwal to bledem po swojej stronie, zapisal naprawde i SAM dodal regule
"zadne zapisane bez paragonu z narzedzia" do pipeline Voice Bible. To dziala dokladnie tak,
jak zaprojektowano po incydencie 19/07 ("Zrobione" bez target_update). Wniosek: kultura
paragonow + konfrontacja pytaniem o dowod = skuteczna obrona przed konfabulacja agenta.
Material tez build-in-public (Tomasz moze wrzucic CM-owi do schowka).

### Ryzyka / otwarte

- **PILNE przed sobota:** adapter web_search Researchera pada od ~28/06 (cicho, nikt nie
  wolal). Bez naprawy sobotni podklad znow pojdzie fallbackiem bez linkow. Brief gotowy.
- Pytanie BE-SWIAT czeka na odpowiedz Managera: zakres query niedzielnego - szeroki ICP
  (obecnie) czy wezszy (premiery modeli + ceny)?
- Decyzja Voice Bible (zderzenie walutowe Notion vs kanon) - dalej czeka na guziki Tomasza.
- Klasa rozliczenia /2/users/me w konsoli X - do odczytania przy okazji (niegrozne).

---

## CZESC II - DLA AGS BUILD ENGINEERA (handoff techniczny)

### Stan repo/serwera (na koniec sesji)

- Galaz `claude/silly-blackwell-dfc32d` (worktree sb-work), HEAD **471b7da**, origin = lokal.
  Sekwencja commitow sesji: b2d8dc7 (merge 4 galezi + zamkniecie dokumentacji) -> dd7918c
  (kalibracja dedup) -> ba06906 (⚠️ w approval) -> 471b7da (wyniki tap-testow + brief
  Researchera; same docs, NIE wymaga rebuilda).
- Serwer: kontener cm-agent zbudowany z **ba06906** (3 rebuildy w sesji), health ok.
  DDL 025 zaaplikowany. **Next wolny DDL: 026.**
- Galezie build/* (kolektor-x 5c2175c, dedup bcc613a, porzadki 01d1a54, czyta-swiat 2b123ad)
  zmergowane, worktree buildowe usuniete. Pusty katalog
  `.claude/worktrees/sad-mendel-a94de4` trzyma blokada Windows - do recznego skasowania,
  nieszkodliwy (git juz go nie widzi).
- Merge byl czysty (zero konfliktow recznych); szwy zweryfikowane semantycznie:
  worker.py = tick kolektora + tick swiata + dup_check w _draft; matreview.py = ⚠️ w _card
  + czyszczenie pq przy 'no'; conversation.py = route regex + narzedzie sunday_world_brief.
  py_compile 9 modulow OK; testy kolektora 16/16 PASS na zmergowanym kodzie.

### Zmiany wykonane PONAD merge (fixy z tap-testow, wszystkie wdrozone)

1. **dd7918c** `worker._draft`: `dup_check(item.get("master_theme") or canonical, ...)`.
   POWOD (pomiar na zywym korpusie, nie teoria): embedding PELNEGO canonicala nie separuje
   duplikatow - celowy blizniak 0.536, a zwykle materialy 0.531-0.588 (wspolny styl domowy
   dlugich tekstow rozmywa teze). Embedding TEMATU separuje czysto: blizniaki 0.597-0.627,
   reszta 0.442-0.551. Prog w `brand_config (AGS, cm_dup_threshold)` = **0.57** (wiersz v2).
2. **ba06906** `hitl.py`: descriptor `dup_warning` z content_items.media renderowany takze
   w wiadomosci approval (bylo TYLKO w kartach matreview - a decyzja zapada w approval).
3. SQL wykonane u Tomasza: sieroty pq (UPDATE 5, sieroty=0), INSERT+UPDATE progu dedup,
   `channels.config.stats_mode='x_owned_reads'` dla AGS/x (wlaczenie kolektora PO sondzie
   i potwierdzeniu ceny w konsoli - sekwencja DoD dotrzymana).

### Dowody tap-testow (pelna tabela: RAPORT_do_Managera_19072026_integracja.md sekcja 6a)

- Kolektor: probe PASS (5/5 non_public_metrics), konsola "Read"/$0.01, 193 snapshoty
  2026-07-19, x_user_id w channels.config.
- Dedup: log `[cm] dup_warning on 1ae52043...: podobienstwo 0.60 do "Single agent hits
  a wall fast..." [x, 11/07]` + linia na karcie.
- Porzadki: paragon ⚙️ bez LLM; seria 263-268 rejected po ❌.
- Czyta swiat: stan `brand_config.cm_sunday_brief` week 2026-30 phase=sent; job 45af415e
  failed -> fallback z jawnym oznaczeniem. UWAGA: retap w tym samym tygodniu wymaga
  wyzerowania klucza stanu (patrz brief naprawczy pkt 4b).

### Diagnoza awarii Researchera (dla sesji BE-RESEARCHER-FIX)

- research_jobs: 3 ostatnie joby failed (20/07, 03/07, 28/06) - "no sources returned
  evidence"; jedyny run web_search status=error z PUSTYM error_message i pustym raw_output
  (~2 min = podejrzenie timeoutu). Kontener ags-researcher healthy, logi bez linii bledu
  miedzy claimed a failed (worker polyka wyjatki - do naprawy razem z adapterem).
- Sciezka: query complexity=low -> kaskada tylko [web_search] -> n8n workflow "Researcher -
  Web Search" (Webhook -> Get Anthropic Key z app_secrets -> httpRequest
  api.anthropic.com/v1/messages -> Normalize -> Guard). Kopia repo:
  n8n-workflows/researcher/web-search.json (zywa definicja moze sie roznic!).
- Pierwszy strzal diagnostyczny: executions n8n tego workflowu z 20/07 07:25 UTC.
- Wszystko w: docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md (STATUS READY; sesja ma
  WYJATKOWE prawa do n8n Researchera, HITL nietykalny, rebuild tylko ags-researcher).

### Backlog dopisany w tej sesji

- Patch allowlisty n8n Parse And Authorize Set o `cm_dup_threshold` (walidacja float 0-1);
  szkic patchera byl gotowy, klasyfikator Cowork zablokowal zapis z sesji integracyjnej -
  wykonac w sesji z prawami n8n (np. razem z naprawa Researchera, TEN wezel jest w HITL,
  wiec formalnie wymaga zgody na dotkniecie HITL - jedna edycja jsCode, wzorzec
  hitl-karty-passthrough.cjs).
- Rozwazyc wymuszenie min. medium dla query niedzielnego (BRIEF naprawczy pkt 4d, guziki).
- Wzmocnienie paragonow propose_material w prompcie CM (incydent "Zapisane"; CM sam dodal
  regule do Voice Bible pipeline - zweryfikowac przy nastepnym bumpie Voice Bible v2.3).

### Lekcje warsztatowe (anti-patterns kandydaci)

- `SELECT created_at::time ... ORDER BY created_at` sortuje po kolumnie WYJSCIOWEJ (goła
  godzina bez daty) - rzutowan nie nazywac tak samo jak kolumna sortowania (kosztowalo
  falszywy trop "znikajacych" wierszy).
- DoD bramek jakosciowych testowac na ZYWYM korpusie przed przyjeciem progu z briefu -
  zalozenie "canonical vs published, prog 0.85" wygladalo rozsadnie i bylo nieuzyteczne
  w praktyce (2 pomiary = poprawna kalibracja).
- Ostrzezenie musi byc renderowane TAM, gdzie zapada decyzja (dedup mial ⚠️ tylko
  w kartach przegladu, a decyzje ida w approval).

Raport przygotowal BE-INTEGRATOR, 20/07/2026 ~10:30. Sesja gotowa do archiwizacji.
