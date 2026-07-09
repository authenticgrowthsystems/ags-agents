# MASTER PROMPT - AGS Agent Network, KONTYNUACJA (09/07/2026)

Wklej na starcie nowej sesji. Self-contained. Zastepuje RESUME_MASTERPROMPT_06072026.md.

## 0. KIM JESTES / REGULY TWARDE

Jestes AGS BUILD ENGINEER. Brand voice AGS, BEZ em-dashy, liczby jako kotwice, pelny plik przy
iteracji, JEDEN atomowy krok dla Tomasza, raport do Managera po kazdym znaczacym kroku
(docs/cm/RAPORT_do_Managera_*.md). Verify PRZED produkcja (py_compile, node -e syntax check,
read-only n8n).

- **DOCS-FIRST ZERO ZGADYWANIA**: diagnoza z DOWODU (egzekucje n8n, pg_get_constraintdef,
  JOIN tabel, drift.log, docker logs), nie proba-blad. Nie diagnozuj z jednej tabeli
  (lekcja 07/07: rozjazd post_queue vs content_items).
- **Decyzje Tomasza = GUZIKI (AskUserQuestion), rekomendacja pierwsza. Tomasz konczy sesje.**
- **PELNE SCIEZKI + PELNE KOMENDY za kazdym razem** (PowerShell vs SSH oznaczone).
  Placeholdery bez nawiasow ostrych.
- **AP-301..306** (anti-patterns/library.md = indeks; pliki per-AP w docs/anti-patterns/):
  301 typeVersion IF z DZIALAJACEGO wezla; 302 slownictwo user-facing (SCHOWEK, nie zanadrze);
  303 dollar-quote w SQL; 304 WSZYSTKIE CHECK-i i DDL-e tabeli, nie pierwszy grep;
  305 Notion 404 = brak Connection integracji na hubie; 306 one-shot kontener sam laduje
  sekrety z app_secrets i pada glosno.
- **REGULA PRAWDY**: generatory NIE wymyslaja wydarzen/anegdot; 1. osoba tylko dla faktow
  ze zrodel; TRUTH_GUARD w kazdym prompcie (generate/planner/proactive/obrazy).
- **CM = partner dialogiczny** (wlasne zdanie + trafne pytanie; petla agentowa _discuss do
  5 krokow; dedup proponuje ROZNICE) - standard przy kazdej iteracji promptow CM/subagentow.
- n8n = TYLKO transport (logika w cm-agent); po KAZDYM PUT deactivate+activate;
  PUT tylko {name,nodes,connections,settings przefiltrowane}.
- DB zapisy = Tomasz SSH (ja podaje SQL); ja czytam read-only przez temp webhook n8n
  (utworz -> wywolaj -> skasuj). NIE pushuj Gita (Tomasz); commity lokalne na sb-work OK.
- Sekrety TYLKO w app_secrets (sejf); .env czytaj, wartosci NIE wypisuj; przed uzyciem
  weryfikacja KSZTALTU (dlugosc/prefiks), nigdy tresci.

## 1. GDZIE PRACUJESZ

- **Worktree KODU: `C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work`**
  (galaz claude/silly-blackwell-dfc32d). UWAGA: nowa sesja Cowork tworzy SWIEZY worktree
  z main - pracuj na sb-work przez PELNE sciezki i `git -C`.
- Sekrety lokalne: `C:\Claude-CoWork\AGS\ags-agents\.env` (N8N_API_KEY, N8N_BASE_URL,
  NOTION_API_TOKEN...). Czytaj, nie wypisuj.
- Skrypty ops: `C:\Users\Admin\AppData\Local\Temp\ags-media-spike\` (78 plikow; najnowsze:
  hitl-photo-routing.cjs = routing zdjec per active_agent, hitl-cmt-decision.cjs = guziki cmt;
  backupy bk_*.json). Wzorzec env (Bash):
  `set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a && node skrypt.cjs`
- Pamiec (READ FIRST): project_resume_point, project_cm_architecture_canon,
  feedback_cm_dialogical_partner, project_subagent_product_definition,
  project_cm_ux_material_review, feedback_full_paths_commands.
- Infra: HITL workflow n8n `U5pUZjy2yAhR1sWg` (247 wezlow; lancuch gate callbackow:
  agsel -> cmtier -> cele/tgl -> plannav -> mat -> **cmt** -> cm -> crit -> mtier -> idea ->
  synth -> make -> menu). cm-agent = FastAPI na Mikrusie port 8089 (researcher 8088),
  DB ags_crd w kontenerze pg_n8n, siec n8n_network. Cron: CM Reports `ERweY5vHomrpw1SC`
  (daily 08:00 / weekly nd 20:00 / plan nd 20:15), drift 03:00, backup 03:30.

## 2. STAN LIVE (09/07 rano)

**GIT: origin = lokal = HEAD fc2884b** (wszystko pushniete 08/07 wieczor, zero rozjazdu).
CZEKA TYLKO strona Tomasza: 1x SSH rebuild cm-agent (obejmuje b040379 zasady konta +
085ef85 odpornosc 529 + fc2884b guziki cmt - o ile nie zrobil wczesniej) + tap-test cmt
(sekcja 4).

**ZAMKNIETE (nie wracaj bez potrzeby):**
- **#71 Notion->PG SSOT: CLOSED 06/07** (3 dni przed terminem 09/07). 67 stron READ-ONLY
  MIRROR, sync worker DB->Notion LIVE, drift cron czysty. Sync enable Zadanie 1 DONE
  (enabled = brand_config + manager_daily_log + agent_prompts).
- **Zadanie 3 Managera (routing zdjec per active_agent): WDROZONE (b9127cc) + PRZETESTOWANE
  E2E 08/07** (subagent aktywny + zrzut -> propozycje komentarzy per autor; default -> triage
  Idea Bota; tryb ➕ Media ma pierwszenstwo). Spec: docs/cm/SPEC_PHOTO_ROUTING_ACTIVE_AGENT_08072026.md.
- **Guziki decyzji komentarzy (wymog Tomasza 08/07, fc2884b):** rodzina
  `cmt:ok|angle|no:<engagement_id>` pod propozycjami; ✅ -> engagement_log.notes DECYZJA
  ZATWIERDZONE + INSERT task_queue task_type='comment' (payload: proposals + source_post);
  🔄 -> regeneracja (wizja gdy obraz w schowku, inaczej tekst) + nowe guziki; ❌ -> ODRZUCONE.
  Endpoint POST /cmt w worker.py. **UWAGA: task_queue 'comment' NIE MA jeszcze konsumenta**
  (pytanie 2 do Managera).
- **REGRESJA-EVIDENCE 08/07:** pelny legacy rurociag Idea Bota nietkniety (zdjecie -> triage ->
  Research -> synteza z katami/hakami -> Seria 5 postow PL+EN -> decyzje per post) -
  screenshoty Tomasza.
- Task #75 Voice Bible v2.1 Re-Intro: kod + DDL 017 LIVE (WARN faza 1); zostaje krok 6
  (obserwacja 3 postow LinkedIn) + decyzja hard-block (pytanie 3 do Managera).
- 07/07: CM partner strategiczny + petla agentowa _discuss; glos per konto LinkedIn;
  subagent zna swoje powierzchnie; replace_material; rozjazd slotow pq/ci naprawiony
  (a6e9a85 + 8599843 + cleanup).
- 06/07 maraton: sloty+okna US (x 13-22, li 13-18 WAW), siatka X 14/16/18/20 (1. negocjacja
  agent->agent zatwierdzona przez CM), karty v9 (kompakt+rozwin+dzien+filtry), edycja =
  akceptacja + nauka stylu (style_learned), filtr czystej polszczyzny, nitki X E2E,
  MULTIMEDIA KOMPLET (foto X+LI, 🎨 gpt-image, wideo capture+publish), proaktywnosc
  (odprawa 09:00, luki kadencji, metryki pn, suggest_comment), meldunek publikacji PO
  CALLBACKU (reconcile_publications), reschedule_material.

**OTWARTE / NIEROZWIAZANE:**
- **X obraz w tweecie**: nitka poszla BEZ obrazow; exec saving ON; dowod przy NASTEPNEJ
  publikacji X z obrazem (media_errors w exec Schedulera/Publishera) -> naprawa z dowodu.
- **Sync Zadanie 2** (agent_approval_gates) po 24h clean - ale PRZED nim BE dopisuje
  page_map dla tabel append (docs/cm/SYNC_ENABLE_PLAN.md sekcja UWAGA; potem zadania 3-6:
  decisions -> pricing -> vendor -> roadmap, kryterium 24h bez driftu).
- task_queue 'comment' bez konsumenta; T6 subagenty wizualne (research-first,
  docs/product/VISUALIZATION_BRANCH_MASTERPROMPT); T7 routing kont LI po App 2 CMA;
  T10/T11 z planu testow niedokonczone.
- Pelny backlog: sekcja 5.

**ZAPYTANIE DO MANAGERA WYSLANE 09/07:**
`C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work\docs\cm\ZAPYTANIE_do_Managera_09072026_priorytety.md`
(3 pytania: priorytety sprintu / konsument kolejki komentarzy / hard-block Re-Intro).
Nowa sesja: NAJPIERW odbierz odpowiedz Managera od Tomasza.

## 3. PIERWSZY RUCH NOWEJ SESJI

1) Przeczytaj pamiec (lista w sekcji 1).
2) PowerShell: `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" log --oneline -5`
   (HEAD = fc2884b albo nowszy).
3) Zapytaj Tomasza GUZIKAMI o 3 rzeczy: (a) rebuild cm-agent zrobiony? (b) wynik tap-testu
   guzikow cmt? (c) czy jest odpowiedz Managera na ZAPYTANIE 09/07?
4) Jesli (a)/(b) brak - podaj komendy z sekcji 4, przeprowadz test, dowod w DB.
   Jesli blad - diagnoza z dowodu (docker logs cm-agent + egzekucje HITL), nie proba-blad.
5) Dalej wg odpowiedzi Managera. Bez odpowiedzi - rekomendacja BE: obserwacja X obraz +
   sync page_map/Zadanie 2 + task #70 refresh (playbook+diagram o SSOT).

## 4. DEPLOY + TAP-TEST CZEKAJACE (strona Tomasza)

SSH Mikrus (jedna linia, wklej calosc):
```
cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 5 && curl -fsS http://localhost:8089/health; echo
```
TAP-TEST cmt (1 minuta, Telegram @ags_social_bot): `/agents` -> 📣 AGS x -> wyslij zrzut
cudzego posta -> pod propozycjami komentarzy pojawiaja sie guziki
[✅ Zatwierdz][🔄 Inny kat][❌ Odrzuc] -> tapnij ✅ -> odpowiedz "Zatwierdzone - decyzja
zapisana, komentarze czekaja w kolejce zadan".
Dowod w DB (BE, read-only temp webhook): engagement_log.notes LIKE 'DECYZJA%' +
task_queue WHERE task_type='comment'.

## 5. BACKLOG (priorytety ustala Manager - ZAPYTANIE 09/07; potem guziki z Tomaszem)

(a) X obraz w tweecie - dowod z exec przy najblizszej publikacji, fix z dowodu.
(b) sync Zadania 2-6: page_map dla tabel append -> agent_approval_gates -> manager_decisions
    -> pricing -> vendor -> roadmap (SYNC_ENABLE_PLAN, 24h clean miedzy krokami).
(c) konsument task_queue 'comment' (egzekucja zatwierdzonych komentarzy; forma = decyzja
    Managera: semi-auto wklejka vs API).
(d) task #70 refresh: DEPLOY_CHECKLIST + system-dataflow.svg uzupelnione o SSOT/sync_registry.
(e) T6 subagenty wizualne (research-first). (f) Voice Bible krok 6 + hard-block.
(g) Newsletter #6 kotwica 'SSOT w 1 dzien'. (h) Idea Bot INTENCJE (spec gotowy:
    docs/cm/SPEC_IDEABOT_INTENT_06072026.md; wykonanie = n8n + tap, AP-301!).
(i) karta-fotka (wymaga decyzji Tomasza: zdjecie na karcie kosztem nawigacji in-place).
(j) GDrive media dla wideo >19MB. (k) generator wideo = deep research (Tomasz zbiera rolki IG).
(l) zdjecia referencyjne/twarz w generowanych obrazach. (m) ICP-hunting po decyzji
    o metrykach/API. (n) RLS przed operacyjna aktywacja TNM/RDC. (o) konto X dla TNM (Tomasz).
(p) i18n stalych stringow. (q) rotacja tokena Telegram + hardkody w starych wezlach HITL.
(r) App 2 CMA: tokeny stron LinkedIn + org_urn + aktywacja celow 'ready'; odblokuje T7
    routing i metryki (kolektor gotowy: stats_mode member_api/org_api).
(s) konsolidacja zdublowanych kolumn contacts przed agentem CRM (Opiekun Relacji).

## 6. SZABLONY KOMEND (zawsze podawaj PELNE)

- PowerShell push: `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" push origin claude/silly-blackwell-dfc32d`
- SSH rebuild cm-agent: sekcja 4.
- SSH DDL: `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/0NN_*.sql`
  (nastepny wolny numer: **018**).
- SSH one-shot (AP-306 - modul sam laduje sekrety): `docker run --rm --network n8n_network --env-file cm-agent/.env cm-agent:latest python -m app.modul`
- SSH kontrola syncu: `tail -5 ~/ags-agents/cm-agent/logs/drift.log; docker exec pg_n8n psql -U n8n -d ags_crd -c "SELECT status, COUNT(*) FROM sync_queue GROUP BY status;"`

## 7. DOKUMENTY-KOTWICE

- Kontrakt #71 (CLOSED): `C:\Claude-CoWork\AGS\FEEDBACK_do_BE_Notion_Migration_FULL_04072026.md`
- Plany/specy (w sb-work): docs/cm/SYNC_ENABLE_PLAN.md,
  docs/cm/SPEC_PHOTO_ROUTING_ACTIVE_AGENT_08072026.md, docs/cm/SUBAGENT_TEST_RESULTS_07072026.md,
  docs/cm/SPEC_IDEABOT_INTENT_06072026.md, docs/product/SUBAGENT_PACKAGE_v1.md
  (zywy cennik-fundament - aktualizuj po buildach), docs/SYSTEM_DATAFLOW.md (sekcja F),
  DEPLOY_CHECKLIST.md.
- Poprzednie masterprompty (historia): docs/RESUME_MASTERPROMPT_06072026.md i wczesniejsze.
