# RAPORT do AGS BUILD ENGINEERA - HANDOFF PO INTEGRACJI (20/07/2026, BE-INTEGRATOR)

Dla kazdej nastepnej sesji budowlanej. Czytaj razem z masterpromptem
(docs/RESUME_MASTERPROMPT_19072026.md - sekcja 4b ma STATUS INTEGRACJI: ZAKONCZONA).

## 1. Stan repo i serwera (koniec sesji 20/07 ~10:30)

- Galaz `claude/silly-blackwell-dfc32d` (worktree sb-work). Sekwencja commitow sesji:
  b2d8dc7 (merge 4 galezi build/* + dokumentacja) -> dd7918c (kalibracja dedup) ->
  ba06906 (⚠️ w approval) -> 471b7da (wyniki tap-testow + brief Researchera) ->
  f3fe7af+ (raporty zamkniecia). Origin zsynchronizowany przez Tomasza.
- Serwer Mikrus: kontener **cm-agent zbudowany z ba06906** (pozniejsze commity = same
  docs, rebuild NIEpotrzebny), /health ok. **DDL 025 zaaplikowany. Next wolny DDL: 026.**
- Galezie buildowe zmergowane i zostaja w historii: build/kolektor-x (5c2175c),
  build/dedup (bcc613a), build/porzadki (01d1a54), build/czyta-swiat (2b123ad).
  Worktree buildowe usuniete. Resztka: pusty katalog `.claude/worktrees/sad-mendel-a94de4`
  (blokada Windows, git go nie widzi - Tomasz moze skasowac recznie, nieszkodliwy).
- Merge czysty (0 konfliktow recznych). Szwy zweryfikowane semantycznie: worker.py =
  _x_collector_tick + sunday_brief.tick + content_memory.dup_check w _draft; matreview.py =
  ⚠️ w _card + UPDATE pq->rejected w akcji 'no'; conversation.py = _USTAW_OKNO_RE/
  _USTAW_KEY_RE przed LLM + narzedzie sunday_world_brief. py_compile 9 modulow OK;
  testy kolektora 16/16 PASS na zmergowanym kodzie.

## 2. Zmiany PONAD merge (fixy z tap-testow, wdrozone i udowodnione)

1. **dd7918c** `cm-agent/app/worker.py` (_draft): `dup_check(item.get("master_theme") or
   canonical, ...)`. POWOD - pomiar na zywym korpusie, nie teoria: embedding PELNEGO
   canonicala NIE separuje (celowy blizniak 0.536 vs zwykle materialy 0.531-0.588; wspolny
   styl domowy dlugich tekstow rozmywa teze). Embedding TEMATU separuje czysto: blizniaki
   0.597-0.627 vs reszta 0.442-0.551. Prog: `brand_config (AGS, cm_dup_threshold)` =
   **0.57** (wiersz v2, czytany przez content_memory._dup_threshold, fallback 0.85 w kodzie).
2. **ba06906** `cm-agent/app/hitl.py`: descriptor `dup_warning` z content_items.media
   renderowany TAKZE w wiadomosci approval (bylo tylko w kartach matreview - a decyzja
   zapada w approval). Lekcja: ostrzezenie musi byc tam, gdzie zapada decyzja.
3. SQL wykonane przez Tomasza (nie wymagaja powtorki): sieroty pq (UPDATE 5, kontrola 0),
   INSERT/UPDATE progu dedup, `channels.config.stats_mode='x_owned_reads'` dla AGS/x
   (wlaczenie kolektora PO sondzie probe i potwierdzeniu klasy Owned Read w konsoli -
   sekwencja DoD dotrzymana; x_user_id zcache'owany w channels.config przez sonde).

## 3. Dowody tap-testow (pelna tabela: RAPORT_do_Managera_19072026_integracja.md sekcja 6a)

- KOLEKTOR: probe HTTP 200, 5/5 postow z non_public_metrics; konsola: kind "Read",
  cykl $0.01; pierwszy zbior **193 snapshoty** za 2026-07-19 (pod progiem alertu 200);
  tick dalej sam raz na dobe UTC (durable guard po MAX(snapshot_date)).
- DEDUP: log `[cm] dup_warning on 1ae52043...: podobienstwo 0.60 do "Single agent hits
  a wall fast..." [x, 11/07]` + linia ⚠️ na karcie (post z incydentu 11/07 - trafienie
  w dziesiatke).
- PORZADKI A: "ustaw okno publikacji dla AGS x na 13:00-22:00" -> natychmiastowy paragon
  ⚙️ bez udzialu LLM. PORZADKI B: ❌ na karcie -> seria pq 263-268 rejected.
- CZYTA SWIAT: reczny tap -> 3 tezy, fallback z jawnym "research nie dojechal", zero
  wpisow do content_items/post_queue. Stan: `brand_config.cm_sunday_brief` = week 2026-30,
  phase=sent. UWAGA: retap w TYM tygodniu wymaga wyzerowania klucza stanu (ksztalt
  sprawdz w sunday_brief._state_set zanim podasz SQL).

## 4. AWARIA RESEARCHERA - dla sesji BE-RESEARCHER-FIX (brief READY)

- Objaw: research_jobs 3 ostatnie joby failed (20/07, 03/07, 28/06) - web_search zepsuty
  od ~28/06, nikt nie zauwazyl (nikt nie wolal). Job 45af415e: complexity=low ->
  kaskada tylko [web_search]; run 7799917d: status=error, **error_message PUSTY**,
  raw_output pusty, ~2 min (podejrzenie timeoutu). Kontener ags-researcher healthy;
  logi miedzy "claimed" a "failed" NIE zawieraja bledu (worker polyka wyjatki - osobny
  punkt DoD naprawy: widocznosc bledow).
- Sciezka techniczna: ags-researcher/app/sources.py -> N8N_BASE_URL +
  /webhook/researcher-web-search -> workflow n8n "Researcher - Web Search"
  (Webhook -> Get Anthropic Key z app_secrets -> httpRequest api.anthropic.com/v1/messages
  -> Normalize -> Guard). Kopia repo: n8n-workflows/researcher/web-search.json
  (ZYWA definicja moze sie roznic - najpierw GET z API n8n!).
- Pierwszy strzal diagnostyczny: executions n8n tego workflowu z 20/07 07:25 UTC
  (pokaze wprost odpowiedz Anthropic API). Hipotezy w kolejnosci + granice sesji +
  DoD: **docs/briefs/BRIEF_NAPRAWA_RESEARCHERA_20072026.md** (sesja rownolegla,
  WYJATKOWE prawa do n8n Researchera, HITL U5pUZjy2yAhR1sWg NIETYKALNY, rebuild tylko
  ags-researcher, cm-agent tylko w pkt 4d briefu za zgoda Tomasza).

## 5. Backlog dopisany w tej sesji

- Patch allowlisty `/set` (wezel Parse And Authorize Set w HITL) o `cm_dup_threshold`
  z walidacja float 0-1. Szkic patchera byl gotowy (wzorzec Temp/ags-media-spike/
  hitl-karty-passthrough.cjs: backup + kotwice + PUT filtrowany + deactivate/activate),
  klasyfikator Cowork zablokowal zapis w sesji integracyjnej. Wykonac w sesji z prawami
  do HITL, za wiedza Tomasza. Do tego czasu strojenie progu = SQL na brand_config.
- Rozwazyc wymuszenie min. medium dla query niedzielnego (auto sklasyfikowal na low ->
  jedno zrodlo -> krucho; BRIEF naprawczy pkt 4d, decyzja guzikami).
- Wzmocnienie paragonow propose_material w prompcie CM (incydent "Zapisane" bez wywolania
  narzedzia; CM sam dodal regule do pipeline Voice Bible - zweryfikowac obecnosc i tresc
  przy bumpie Voice Bible v2.3).

## 6. Lekcje warsztatowe (kandydaci do anti-patterns)

- **SQL**: `SELECT created_at::time ... ORDER BY created_at` sortuje po kolumnie
  WYJSCIOWEJ (sama godzina, bez daty!) - rzutowan nie nazywac jak kolumna sortowania.
  Kosztowalo falszywy trop "znikajacych wierszy".
- **Kalibracja bramek jakosciowych**: prog i jednostke porownania testowac na ZYWYM
  korpusie przed przyjeciem DoD - zalozenie "canonical vs published, prog 0.85" wygladalo
  rozsadnie i bylo bezuzyteczne (0 trafien mozliwych). Dwa pomiary daly poprawna kalibracje.
- **Renderowanie ostrzezen**: alert musi byc w widoku, w ktorym zapada decyzja, nie tylko
  w widoku przegladowym.
- **AP-304 (recydywa)**: research_jobs ma `job_id`, nie `id` - kolumny sprawdzac przed
  SELECT-em, nie zakladac.
