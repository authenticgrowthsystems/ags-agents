# MASTER PROMPT - AGS Agent Network, KONTYNUACJA (19/07/2026)

Wklej na starcie nowej sesji. Self-contained. Zastepuje RESUME_MASTERPROMPT_09072026.md.

## 0. KIM JESTES / REGULY TWARDE (bez zmian, skrot)

AGS BUILD ENGINEER (Manager AGS = Claude w czacie Cowork, NIE agent na serwerze). Brand voice
AGS, zero em-dash, pelne pliki przy iteracji, JEDEN atomowy krok dla Tomasza, raport do Managera
po znaczacym kroku (docs/cm/RAPORT_do_Managera_*.md). py_compile przed commitem.
- DOCS-FIRST, diagnoza z DOWODU (2+ zrodla), nie hipotezy. AP-301..306 (docs/anti-patterns/).
- Decyzje Tomasza = GUZIKI (AskUserQuestion), rekomendacja pierwsza. Tomasz konczy sesje.
- PELNE SCIEZKI + PELNE KOMENDY zawsze (PowerShell vs SSH oznaczone) - "nie na skroty".
- REGULA PRAWDY wszedzie; CM = partner (patrzy zanim pyta, wykonuje STOP przed doprecyzowaniem,
  paragon KAZDEJ decyzji nowa wiadomoscia).
- n8n = TYLKO transport; po KAZDYM PUT deactivate+activate; PUT {name,nodes,connections,settings}.
- DB zapisy = Tomasz SSH (ja podaje SQL); ja czytam read-only przez temp webhook (wzorzec:
  Temp/ags-media-spike/verify-*.cjs). Git push = Tomasz. Sekrety TYLKO app_secrets.
- KAZDA zmiana DDL = docs/db/SCHEMA_ags_crd.md w TYM SAMYM commicie.

## 1. GDZIE PRACUJESZ

- Worktree KODU: `C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work` (galaz
  claude/silly-blackwell-dfc32d; nowa sesja Cowork tworzy swiezy worktree z main - pracuj
  na sb-work przez `git -C`).
- Sekrety lokalne: `C:\Claude-CoWork\AGS\ags-agents\.env` (N8N_API_KEY itd. - czytaj ksztalt).
  Wzorzec env (Bash): `set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' ".../.env" | sed 's/\r$//') && set +a && node skrypt.cjs`
- Skrypty ops: `C:\Users\Admin\AppData\Local\Temp\ags-media-spike\` (patchery n8n hitl-*.cjs
  z backupami bk_*.json; weryfikatory verify-*.cjs).
- Pamiec (READ FIRST): project_resume_point, project_cm_architecture_canon,
  feedback_cm_dialogical_partner (+rozszerzenie 12/07), project_voice_dna_architecture,
  feedback_full_paths_commands, project_subagent_product_definition.
- Infra: HITL n8n `U5pUZjy2yAhR1sWg` (247 wezlow; Detect Update Type = router komend z
  przepustka /karty /schowek /decyzje /brand*; Parse And Authorize Set = allowlista /set
  z freetext keys). cm-agent FastAPI Mikrus:8089 (endpointy: /message /matnav /plannav /cmt
  /wake /request /plan /reports). DB ags_crd w pg_n8n. Crony: CM Reports 08:00/nd 20:00/nd
  20:15 plan, drift 03:00, backup 03:30. Deploy: push (Tomasz) -> SSH pull + ew. psql db/0NN
  -> docker build/run -> /health.

## 2. INCYDENT TYGODNIA 13-19/07 (Tomasz nieobecny - polkolonie) - DIAGNOZA

Screeny: docs/evidence/screeny_13-19_07/. Cztery mechanizmy:
1. **Stan awaryjny 24h (kanon 11c) dzialal jako autopilot** - publikowal bez Tomasza
   (18/07 seria 4 postow X jednego wieczora). Kanon byl na "zapomnial", nie "tydzien nieobecny".
2. **Petla autoreferencyjna tresci**: wypelniacz luk + schowek pelen build-in-public o systemie
   -> posty o wlasnych lukach kadencji/slotach/obserwowalnosci w kolko na X.
3. **Plan spuchl do 78 pozycji** (planner nd + gap-filler, akceptacja tylko reczna).
4. **Slepota metryczna**: X = wpis reczny (nie bylo komu), LinkedIn = czeka App 2 CMA.

**SPRZATANIE 19/07 (SQL podany Tomaszowi; ZWERYFIKUJ w nowej sesji read-only):**
emergency_publish=false na WSZYSTKICH celach (do odwolania!), post_queue review/scheduled/queued
-> held (wszystko zamrozone), proposed (78) -> rejected. Intake drafts zostaly (nieszkodliwe).
Nic nie publikuje sie bez tapniecia Tomasza.

## 2b. SLOWNICZEK TABEL (dopisane 19/07 po bledzie nastepcy: platform/is_active NIE istnieja w channels)

- **brands**: brand_id PK, brand_name, status (active|paused|archived)
- **channels** (CELE): id, brand_id, **channel**, **status** (active|draft|ready|paused),
  supervised bool, adapter_path, execution_mode, config jsonb (language_publish, secret_prefix,
  publish_windows, publish_mode, follower_count, thread_enabled, rules[], voice_note,
  emergency_publish)
- **content_items**: id **UUID**, brand_id, master_theme, status (planned|needs_research|
  researching|drafting|needs_approval|approved|dispatching|published|rejected|failed|proposed|
  draft|brief|archived), canonical_body, target_channels[], scheduled_for, media jsonb
- **post_queue** (KOLEJKA): id serial, **brand**, **platform** (x|linkedin...), content, topic,
  status (review|scheduled|queued|held|dispatching|published|failed|rejected), content_item_id,
  scheduled_for, media jsonb
- **brand_config**: brand_id, config_key, config_value, version - **UNIQUE (brand_id,
  config_key)**, wersjonowanie przez UPDATE+bump, NIE nowe wiersze!
- **task_queue**: id UUID, agent_id, task_type (publish|comment|...), platform, payload jsonb,
  status (pending|in_progress|done|failed|blocked|...)
- **engagement_log**: id UUID, action_type (x_post|x_comment|linkedin_post|...), channel
  (X|LinkedIn|... - z wielkiej!), agent ('AGS:x'), content, response, notes
- **agent_logs**: agent_id, log_type (AUTONOMOUS_DECISION|CONVERSATION_SUMMARY|CHANNEL_NEED|
  VOICE_EDIT|RE_INTRO_MISSING - bez CHECK), rationale, context jsonb
- **agent_learning_log**: subagent_id, brand_id, content_item_id UUID, proposed/final_content,
  correction_type (accepted|edited|rejected|replaced)
- **brand_tokens**: brand_id PK, tokens jsonb, updated_at, source
Pelniej: docs/db/SCHEMA_ags_crd.md + docs/SYSTEM_DATAFLOW.md.

## 3. PIERWSZY RUCH NOWEJ SESJI

1) Pamiec + ten plik. 2) `git -C ...sb-work log --oneline -5` (HEAD >= 67f3acf; sprawdz czy
Tomasz pushnal - moze byc ahead). 3) Zweryfikuj sprzatanie GOTOWYM SQL-em (read-only temp
webhook, wzorzec Temp/ags-media-spike/verify-close.cjs):
```sql
SELECT 'emergency_off' AS co, COUNT(*)::text AS n FROM channels WHERE supervised=true AND (config->>'emergency_publish')='false'
UNION ALL SELECT 'held', COUNT(*)::text FROM post_queue WHERE status='held'
UNION ALL SELECT 'proposed', COUNT(*)::text FROM content_items WHERE status='proposed';
```
(oczekiwane: emergency_off=11, held>0, proposed=0). 4) Screeny Tomasza w docs/evidence -
przeanalizuj i uzupelnij diagnoze. 5) PRIORYTETY NAPRAWCZE (sekcja 4) - guziki z Tomaszem.

## 4. PRIORYTETY NAPRAWCZE (wnioski z incydentu - USTAL Z TOMASZEM KOLEJNOSC)

(a) **TRYB NIEOBECNOSCI** (`/urlop start|stop` albo /brands-style): zamraza publikacje +
    emergency + gap-filler + planner; odprawa raz dziennie "spie, kolejka zamrozona".
    Auto-detekcja: brak JAKIEJKOLWIEK aktywnosci Tomasza >48h = auto-tryb + alert.
(b) **BRAMKA ROZNORODNOSCI TEMATOW**: gap-filler i planner NIE moga proponowac tematow
    o samym systemie czesciej niz X/tydzien; dedup tematyczny na poziomie planu (motywy,
    nie tylko embedding); zrodla tematow: filary + ICP, nie ostatnie publikacje.
(c) **METRYKI = przestaje byc slepy**: X wpis reczny co poniedzialek (dziala), App 2 CMA
    review (Tomasz/zewnetrzne), rozwazyc scraping wlasnego profilu przez sonde.
(d) Stan awaryjny: NIE wlaczac ponownie bez trybu nieobecnosci; prog moze byc per cel.
(e) Limit planu (np. max 20 proposed; nowe wypychaja najstarsze do archiwum).

## 5. STAN LIVE (wszystko z 10-13/07, zweryfikowane tapami przed nieobecnoscia)

- **Sprint briefu #83-#90 + #84 + v2.2 wykonany 12/07 w jeden dzien** (raporty per task
  w docs/cm/RAPORT_do_Managera_12072026_*.md + zamkniecie_sprintu).
- CM: partner (view_last_screenshot patrzy przed pytaniem; hold_todays_queue = STOP przed
  doprecyzowaniem; paragony decyzji nowa wiadomoscia; przeglad planu plannav vs karty matnav
  rozrozniane). max_tokens 4000/2000. Pamiec dlugoterminowa rozmow (CONVERSATION_SUMMARY).
  Petla agentowa subagentow (5 krokow) + paragony wykonania.
- Multi-brand: brands AGS/TNM/RDC active + LYSY/PT/SDI paused; /brands on/off/add/remove/
  config/export (tekstowe); propose_material z brand_id; kolejka/karty wszystkie marki 🏷.
- TNM: Voice Bible PL v2.0 ADOPTOWANA (brand_config v2, poprawki: 4.11 Regula Prawdy +
  Aneks A filary; plik zrodlowy C:\Claude-CoWork\TyNieMusisz\TNM_Voice_Bible_PL_v2.0.md);
  cel TNM/linkedin = STRONA ready (czeka App 2); konto osobiste Tomasza = WYLACZNIE EN.
- AGS Voice Bible v2.2 LIVE (brand_config v4, md5 dc8b4334; db/022): X post/Article/thread
  per follower_count, 13.8 Re-Intro X Article, 14 barwy per marka, 15 waluta per marka.
  KOREKTA PO BUMPIE (do v2.3): dluga tresc X <1000 foll. = SERIA samodzielnych postow
  ===POST=== po slotach dnia (stage_variant rozdziela; slots._busy liczy tez post_queue;
  czesci sekwencyjnie - fix 67f3acf), [ARTYKUL] = kloc reczny. Dowod: seria 155-158.
- brand_tokens (#84): Notion "Brand Config" (id c15f07cc-4db7-497d-a48e-a13d56d36cba,
  Manager utworzyl) -> puller w sync workerze co 10 min -> PG (AGS=17, TNM=17 tokenow)
  -> generate._visual_canon (1. zrodlo promptow graficznych). /set ma freetext allowliste.
- #87: execution_mode (11 celow supervised) + agent_learning_log (log wszystkich decyzji
  kart/edycji/podmian + _learning_digest w kazdej generacji). UWAGA: tabela byla pusta
  19/07 rano (Tomasz nieobecny - zadnych decyzji).
- #88 zdjecie przy CM -> rozmowa CM; #89 karta approved 🔒 + 📄 fulltext kawalki+plik .md,
  hitl dlugie warianty jako .md, tryb reczny w approval pokazuje tekst-matke.
- Grafika: prompt Sonneta (kanon/tokeny) + gpt-image high + generate_material_image +
  auto-grafika przed karta (cm_auto_image) + describe_material_image (agent WIDZI grafike).
- Intake publikacji zewnetrznej ([ZEWN]) + wake webhook (POST /wake) + konsument komentarzy
  (gotowiec + cmt:done|skip).
- Obserwacja: canonical AGS potrafi wyjsc PO POLSKU (wariant X i tak EN; ew. doprecyzowac).

## 6. BACKLOG (poza priorytetami naprawczymi)

Adapter X Articles n8n (endpointy zweryfikowane: POST /2/articles/draft {title, content_state
DraftJS} -> /publish; OAuth1 OK; sonda tieru na zywo z Tomaszem). Guziki /brands + wizard FSM
+ egzekwowanie execution_mode. Priorytet 4 SOP Faza 3 (2 warianty feedu przy artykule,
pierwszy komentarz autora <=30 min, strona repost, buyer-lane pomiar). n8n publishery wolaja
/wake po callbacku. Intencja zdjecia w routingu (pytanie-o-material vs cudzy-post). Voice
Bible v2.3 (seria X). RDC voice (rdzen DNA + nakladka). Agent Wizualny ZAMROZONY (spec
docs/product/SPEC_VISUAL_AGENT_10072026.md + synteza researchu docs/research/). App 2 CMA.
brand_assets (zdjecia/loga). Tryb jezyka canonicala.

## 7. DOKUMENTY-KOTWICE

docs/cm/RAPORT_STAN_CM_I_SUBAGENTOW_10072026.md (architektura CM+subagenci, pamiec 3 warstwy),
docs/product/SUBAGENT_DUTIES_v1.md (8 obowiazkow O1-O8), docs/db/SCHEMA_ags_crd.md,
docs/SYSTEM_DATAFLOW.md, BE_BRIEF_HOT_FIXES_12072026.md (C:\Claude-CoWork\AGS\),
docs/cm/INSTRUKCJA_dla_Managera_Notion_BrandConfig_12072026.md, DEPLOY_CHECKLIST.md.
Nastepny wolny DDL: **023**.

## 8. SZABLONY KOMEND

- Push (PowerShell): `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" push origin claude/silly-blackwell-dfc32d`
- Rebuild (SSH): `cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 5 && curl -fsS http://localhost:8089/health; echo`
- DDL (SSH): `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/0NN_*.sql`
- Logi (SSH): `docker logs --since 30m cm-agent 2>&1 | tail -60`
