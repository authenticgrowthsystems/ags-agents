# RAPORT do Managera - INTEGRACJA 4 rownoleglych buildow (19/07/2026 noc, BE-INTEGRATOR)

Brief: docs/briefs/BRIEF_INTEGRACJA_19072026.md. Jedyna sesja z prawem do sb-work,
masterpromptu i paczki deploy. Zero nowych feature'ow - wylacznie skladanie.

## 1. Weryfikacja statusow budowniczych (warunek startu)

| Build | Galaz | Status w briefie | Dowody |
|---|---|---|---|
| Kolektor metryk X | build/kolektor-x (5c2175c) | CODE-DONE | testy 16/16 PASS (wektor OAuth1 z docs.x.com), DDL 025 + SCHEMA w tym samym commicie, raport per DoD |
| Bramka duplikacji | build/dedup (bcc613a) | BUILT-LOCAL | py_compile 3/3, test dup_warning_text 4/4, zero DDL, kontrakt 3 plikow dotrzymany |
| Porzadki deterministyczne | build/porzadki (01d1a54) | ZBUDOWANE | test regexow 14/14 (definicje z zywego zrodla), kontrakt 2 plikow dotrzymany |
| CM czyta swiat | build/czyta-swiat (2b123ad) | KOD GOTOWY | py_compile 4 plikow, weryfikacja read-only zywej bazy (rozbieznosc claims text[] vs uuid[] wykryta i obsluzona), zero DDL |

## 2. Merge (worktree sb-work, kolejnosc z briefu)

1. build/kolektor-x - fast-forward (9 plikow).
2. build/dedup - auto-merge worker.py.
3. build/porzadki - auto-merge matreview.py.
4. build/czyta-swiat - auto-merge worker.py + conversation.py.

ZERO konfliktow recznych. Kontrola SEMANTYCZNA szwow (nie tylko git):
- worker.py: import wszystkich nowych modulow + _x_collector_tick (def + wywolanie w petli)
  + sunday_brief.tick() + content_memory.dup_check w _draft - wszystkie 3 kawalki obecne.
- matreview.py: linia ⚠️ DUPLIKACJA w _card (dedup) + UPDATE post_queue->rejected w akcji
  'no' (porzadki) - oba w roznych miejscach, obecne.
- conversation.py: _USTAW_OKNO_RE/_USTAW_KEY_RE przed LLM (porzadki) + narzedzie
  sunday_world_brief z dispatchem (swiat) - obecne.

Weryfikacja: py_compile 9 modulow (worker, matreview, conversation, reports, x_collector,
content_memory, research, sunday_brief, test_x_collector) = OK. Testy kolektora na
zmergowanym kodzie: 16/16 PASS.

## 3. Dokumentacja zamknieta w tej paczce

- SYSTEM_DATAFLOW.md: nowa sekcja H (4 przeplywy integracji, co gdzie zapisane).
- RESUME_MASTERPROMPT_19072026.md: sekcja 4b STATUS INTEGRACJI + next DDL = 026
  (poprawka stanu 023/024 - byly juz wykonane 19/07 wieczorem, sekcja 7 byla stale).
- SCHEMA_ags_crd.md: sekcja x_post_metric_snapshots weszla z galezia kolektora
  (ten sam commit co DDL - regula dotrzymana przez budowniczego).
- Ten raport. Worktree buildowe usuniete (galezie zostaja w historii).

## 4. PACZKA DEPLOY - do wykonania przez Tomasza

KROK 1 - push (PowerShell):
```powershell
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" push origin claude/silly-blackwell-dfc32d
```

KROK 2 - DDL 025 + rebuild (SSH Mikrus, jedna sekwencja):
```bash
cd ~/ags-agents && git pull --ff-only && docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/025_x_post_metric_snapshots.sql && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 15 && curl -fsS http://localhost:8089/health; echo
```

KROK 3 - SQL sprzatajacy sieroty pq (SSH, od porzadkow):
```bash
docker exec -i pg_n8n psql -U n8n -d ags_crd -c "UPDATE post_queue pq SET status='rejected' FROM content_items ci WHERE ci.id=pq.content_item_id AND pq.status='review' AND ci.status IN ('rejected','archived');"
```

DDL 025 jest bezpieczny przed wlaczeniem kolektora: tabela czeka pusta, tick SPI dopoki
stats_mode nie zostanie ustawiony recznie (zero platnych requestow bez decyzji).

## 5. TAP-TESTY po deployu (DoD 4 buildow)

1. **KOLEKTOR - sonda PRZED cronem** (SSH):
   `docker exec cm-agent python -m app.x_collector probe`
   Oczekiwane: HTTP 200, posty z non_public_metrics, [probe] PASS.
   Potem Developer Console: potwierdz klase rozliczenia **Owned Read $0.001** (przy okazji
   odczytaj klase /2/users/me - punkt otwarty). DOPIERO wtedy wlaczenie (SSH):
   `docker exec -i pg_n8n psql -U n8n -d ags_crd -c "UPDATE channels SET config = jsonb_set(config,'{stats_mode}','\"x_owned_reads\"') WHERE brand_id='AGS' AND channel='x';"`
   Nastepnego dnia: sekcja per-post X w raporcie dziennym zasila sie sama.
2. **DEDUP** (Telegram): wygeneruj material o tezie zblizonej do publikacji z ostatnich
   30 dni -> karta z linia ⚠️ DUPLIKACJA (informuje, nie blokuje).
3. **PORZADKI** (Telegram + read-only): "ustaw okno publikacji dla AGS x na 13:00-21:00"
   -> paragon ⚙️ + zmiana w DB; odrzucenie karty (matnav no) -> wiersze pq materialu
   przechodza na 'rejected'; po KROKU 3 sieroty = 0.
4. **CZYTA SWIAT** (Telegram): "podklad na niedziele" -> zapowiedz, po kilku minutach
   3 tezy z faktami i LINKAMI zrodel; content_items i post_queue BEZ nowych wierszy.
   Automat sam rusza w najblizsza sobote 08:00-12:30 (reczny tap nie zajmuje slotu).

## 6. Punkty otwarte (zebrane od budowniczych)

- Klasa rozliczenia /2/users/me - odczyt z konsoli po sondzie (miesci sie w guardrailu).
- Granica 30 dni przy paginacji: mitygacja start_time=29d; gdyby sonda dala 400,
  pierwszy podejrzany = margines (zmniejszyc do 28).
- Kazdy dzien zwloki we wlaczeniu kolektora = bezpowrotnie stracone non_public metryki
  postow starszych niz okno - sonda najlepiej OD RAZU po deployu.
- Pytanie BE-SWIAT do Managera: query researchu szeroki (ICP solo-founderzy) czy wezszy
  (premiery modeli + ceny)? Zostawiony szeroki do pierwszej soboty; korekta = SUNDAY_QUERY.
- Decyzja Voice Bible (zderzenie walutowe) dalej CZEKA na guziki Tomasza (sprzed integracji).
