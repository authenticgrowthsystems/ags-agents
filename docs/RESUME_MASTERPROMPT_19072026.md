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
- DOKUMENTACJA ZYJE (kanon 20/07): kazda zmiana ZACHOWANIA = dokumentacja w TYM SAMYM
  commicie; dokumentacja = STAN OBECNY (historia w raportach/git log); sesja czyta
  DOKUMENTACJE PRZED kodem, a gdy dokumentacji brakuje - dopisuje ja. Pelny zapis:
  docs/briefs/PROTOKOL_SESJI.md pkt 6.

## 1. GDZIE PRACUJESZ

- **Dokumentacja komponentow: `docs/komponenty/` (11 plikow, staly szablon) -
  CZYTAJ ZAMIAST kodu** (kanon DOKUMENTACJA ZYJE). `docs/SYSTEM_DATAFLOW.md` =
  mapa przeplywu + indeks; historia w `docs/archiwum-dataflow.md` i raportach.
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

## 4. KOREKTA KANONU 19/07 (Tomasz; NADPISALA pierwotne priorytety a-e) + PLAN DNIA WYKONANY

KANON (pamiec: project_publikacja_kanon_19072026): (1) ZATWIERDZONE publikuje sie ZAWSZE,
obecnosc Tomasza nieistotna; (2) NIEZATWIERDZONE NIGDY samo - _emergency_promote USUNIETY
Z KODU (nie flaga); luka/cisza = eskalacja z pytaniem; (3) eskalacja subagent->CM->Tomasz
GUZIKAMI, kazda odpowiedz -> agent_learning_log, przejscia supervised->semi_autonomous per
TYP decyzji (nigdy dla zatwierdzania tresci). Blad tygodnia = publikowanie NIEZATWIERDZONEGO,
nie publikowanie w ogole ("tryb nieobecnosci" z (a) NIE powstaje).

PLAN DNIA 19/07 - kod DONE (sesja dnia, commity 30376c3/77b2251/b20a191/576a832):
[1] METRYKI: DDL 023 + import xlsx AggregateAnalytics przez Telegram (n8n galaz document_xlsx
    LIVE) + sekcja PROFIL w raportach + szew x_owned_reads. Brief: BRIEF_METRYKI_19072026.
[2] ESKALACJA+NAUKA: DDL 024 (agent_decisions + decision_modes) + decisions.py + /decnav +
    n8n galaz dec: LIVE + tool escalate_decision. Brief: BRIEF_ESKALACJA_19072026.
[3] KANON: _emergency_promote WYCIETY, _stale_approval_watch (guziki) w petli; komunikaty
    "awaryjna 24h" usuniete. DOWOD held: ZERO approved/dispatching (5 published + 2 rejected
    + 15 sierot bez itemu) -> odmrozenie=no-op, SQL sprzatajacy w BRIEF_KANON_PUBLIKACJI.
[4] BRAMKA TEMATOW: zrodla=FILARY+ICP, meta o wlasnym systemie max 1/tydz (prompt+twardy
    regex, test 6/6 incydentu, 0 FP), limit planu 20 (_enforce_plan_cap), gap-filler na tym
    samym budzecie. Brief: BRIEF_BRAMKA_TEMATOW_19072026.
WIECZOR 19/07 - WSZYSTKO POWYZSZE LIVE (3 rebuildy, tap-testy PASSED): import xlsx E2E
(28 dni w channel_metrics_daily, PROFIL w raportach), held sprzatniety (SQL wg dowodu),
NOWY PLAN zatwierdzony (23 pozycje pod ICP, bramka dziala). Fixy z tapow: pusty plan melduje
(REGULA PRAWDY w planerze), cap wypycha KONIEC tygodnia (nie poniedzialek), okno LI 16:00-18:00
+ przesuniete sloty, humanize_slot (ludzkie minuty +/-15, nigdy kwadrans), karty po decyzji
NA DOL czatu, Media bez floodu (galeria na zadanie mgal), gpt-image-2 (docs-first) + guzik
📋 Prompt (media[].image_prompt), dokumenty .md/.txt -> rozmowa agenta (document_text + /docmsg).
TASKI POPRZEDNIEJ SESJI 3/3: legacy X OFF od 25/06 (dowod - zero podwojnych publisherow);
dokumenty obsluzone; Voice Bible zderzenie GOTOWE (docs/cm/ZDERZENIE_VOICE_BIBLE_19072026.md:
sprzecznosc walutowa Notion s.9 vs kanon s.15; rekomendacja brand_config=SSOT + voice_dna_core
+ mirror) - CZEKA NA DECYZJE TOMASZA guzikami. INCYDENTY dnia z lekcjami: CM "Zrobione" bez
target_update (test prawdy: config bez paragonu ⚙️ = niewykonane), duplikacja tezy 11/07
(reguly stylu #11/#12 zapisane trwale z paragonami). Raport dnia:
docs/cm/RAPORT_do_Managera_19072026_zamkniecie_dnia.md.
RESEARCH X SKONSUMOWANY: 3 raporty zbiezne -> Owned Reads $0.001, GET /2/users/{id}/tweets,
OAuth1 user context dziala, ~$4.50/mies; brief buildu: BRIEF_KOLEKTOR_METRYK_X_19072026 (READY).

## 4b. KOLEJKA BUDOWNICZYCH (tryb awaryjny 19/07 ~22:00 - handoff Fable 5 -> Opus 4.8)

DECYZJE PLANU (BE w roli Managera, 22:30 - Manager Opus 4.7 milczal, Tomasz zarzadzil
decyzje; pelne uzasadnienie: docs/cm/DECYZJA_BE_19072026_plan_kolejki.md): P1 kolejnosc
1-4 POTWIERDZONA; P2 piaty build = SOP Faza 3 LinkedIn buyer-lane (szosty = adapter X
Articles); P3 X: kadencja zostaje, ZERO budow pod wzrost X do 2 tyg. baseline z kolektora,
tania dzwignia = comment-radar na postach ICP (zbudowany); P4 Stage 0-1 potwierdzone.

TRYB ROWNOLEGLY (Tomasz 22:45, nadpisal sekwencyjnosc): 4 okna JEDNOCZESNIE, kazde na
WLASNYM worktree+galezi build/* (komenda w sekcji 0 kazdego briefu; NIKT nie pracuje na
sb-work!). Kazde okno: startuje Fable 5 (max 2 prompty), potem Tomasz przelacza model na
Opus 4.8, ktory konczy w tym samym oknie. ZAKAZ deployu/psql/n8n u budowniczych - calosc
sklada BE-INTEGRATOR (docs/briefs/BRIEF_INTEGRACJA_19072026.md): merge 4 galezi -> jedna
paczka deploy -> tap-testy -> zamkniecie za wszystkich. Kolejnosc priorytetow (gdyby
trzeba bylo wybierac): jak nizej.

1. **BE-KOLEKTOR** (najpilniejsze - prywatne metryki X tylko <30 dni wstecz):
   `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_KOLEKTOR_METRYK_X_19072026.md zbuduj`
   STATUS=READY-BILLING (saldo $6.96, cap $20, Auto Recharge ON). Start od sondy. DDL 025.
2. **BE-DEDUP**:
   `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_BRAMKA_DUPLIKACJI_19072026.md zbuduj`
3. **BE-PORZADKI**:
   `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_PORZADKI_DETERMINISTYCZNE_19072026.md zbuduj`
4. **BE-SWIAT** (przed najblizsza sobota - podklad niedzielnego artykulu):
   `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_CM_CZYTA_SWIAT_19072026.md zbuduj`

**STATUS INTEGRACJI (BE-INTEGRATOR, 20/07 rano): ZAKONCZONA - DEPLOY + TAP-TESTY DONE.**
4 galezie zmergowane, wdrozone (psql 025 + 3 rebuildy) i przetestowane z Tomaszem:
KOLEKTOR LIVE (sonda PASS, Owned Read potwierdzony w konsoli, stats_mode ON, 193 snapshoty
19/07); PORZADKI A+B PASS; DEDUP PASS po kalibracji z zywego korpusu (dup_check na
master_theme zamiast canonicala dd7918c, prog 0.57 w brand_config, ⚠️ takze w approval
ba06906 - dowod: 0.60 vs post z incydentu 11/07); CZYTA SWIAT mechanizm+fallback PASS,
ale noga researchowa FAILED - adapter web_search Researchera PADA OD ~28/06 (3 joby failed,
cichy error) -> **BRIEF_NAPRAWA_RESEARCHERA_20072026.md READY (sesja rownolegla, wyjatkowe
prawa do n8n Researchera, HITL nietykalny)**. Wyniki + incydenty (CM "Zapisane" bez
paragonu - test prawdy zadzialal; /set bez klucza cm_dup_threshold - obejscie SQL):
docs/cm/RAPORT_do_Managera_19072026_integracja.md sekcja 6a.

Dalszy backlog (bez briefow, pisze je sesja planujaca gdy przyjdzie kolej): adapter X Articles
n8n (sonda tieru), guziki /brands + wizard FSM + egzekwowanie execution_mode, SOP Faza 3,
publishery wolaja /wake, intencja zdjecia w routingu, Voice Bible v2.3 (seria X), RDC voice,
Agent Wizualny (ZAMROZONY, spec gotowy), App 2 CMA, brand_assets, tryb jezyka canonicala,
3b automation model_selection. Zamrozone NIE odmrazac bez decyzji Tomasza.

**BE-ENGAGEMENT (20/07 popoludnie): ZBUDOWANE, czeka integracja.** Galaz build/engagement-crm:
comment-radar dostaje CRM relacji (brief BRIEF_ENGAGEMENT_CRM_20072026, komponent
docs/komponenty/engagement-crm.md - CZYTAJ ZAMIAST kodu): propozycja per AUTOR = wlasny wiersz
engagement_log (status proposed/approved/sent/... + contact_id + author_display) z wlasnymi
guzikami cmt:; contacts z #71 dopasowywane po handle/nazwie, NIEZNANY = stub + wymuszony intake
profilu (zrzut -> wizja -> tier Buyer/Peer/Competitor/Partner guzikami przez decisions 'crm_tier');
przypomnienia 24h (typy stale_comment / stale_comment_task); album media_group_id = JEDEN post
(patch n8n: n8n-workflows/patches/hitl-photo-mediagroup-20072026.cjs; bez patcha fallback =
pytanie 'jeden post czy rozne?' przy zrzutach <60 s). DDL 026 (contacts.handles +
relationship_stage + icp_tier CHECK poszerzony; engagement_log.status + author_display).
WDROZENIE: merge -> psql 026 PRZED rebuildem -> rebuild cm-agent -> patch n8n -> 5 tap-testow
DoD z briefu. Nastepny wolny DDL po tym buildzie: **027**.

**BE-SPRZEDAWCA (20/07 popoludnie): ZBUDOWANY, czeka integracja.** Galaz build/sprzedawca:
Agent Sprzedazy L1 (brief BRIEF_AGENT_SPRZEDAZY_MVP_20072026, komponent
docs/komponenty/agent-sprzedazy.md - CZYTAJ ZAMIAST kodu): nowy agent w menu /agents przez
wiersz channels (AGS,'sprzedaz',config.agent_kind='sales' - menu n8n buduje sie dynamicznie
z channels, ZERO zmian wezlow menu; guardy w planner/reports/proactive/snapshot wykluczaja
agent_kind='sales'); komendy /prospect /oferta /pipeline /add_sales_material deterministycznie
PRZED LLM; patch przepustki: n8n-workflows/patches/hitl-sales-commands-20072026.cjs (komendy
+ .pdf<=8MB do document_text; pypdf dodany do requirements = rebuild obowiazkowy); research
prospektow tier critical (agent_registry 'sales-agent' z 'critical'; async - wynik tickiem
sales.tick -> synteza sygnalow buyer + notatka lejka); outreach = GOTOWIEC HITL (czysta
wklejka osobna wiadomoscia, engagement_log 'proposed', NIC nie wysyla sie samo); DDL 027
(sales_pipeline + sales_knowledge pgvector 1536). WDROZENIE: merge -> psql 027 PRZED
rebuildem -> rebuild cm-agent -> patch n8n -> tap-testy DoD z briefu. Nastepny wolny DDL
po tym buildzie: **028**.

RESEARCHER NAPRAWIONY 20/07 (merge 3fd3560): web_search padal od 28/06 przez domyslne
dynamic filtering Anthropic w web_search_20260209 (15s->110s) - fix allowed_callers:['direct']
+ koniec polykania bledow (sources/worker/Normalize) + cost_usd z usage; zywy n8n oxwcD1i...
ZAPATCHOWANY (kopia repo == zywa), kontener ags-researcher LIVE z fixem; 4d: sunday_brief
wymusza minimum medium (wchodzi po rebuildzie cm-agent). Pamiec:
project_researcher_awaria_websearch_20072026. UWAGA SERWER: klon ~/ags-agents stal na galezi
naprawczej - po pullu przestawic na claude/silly-blackwell-dfc32d.

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

NOWE 20/07 (INCYDENT PUBLIKACJI, AP-307, raport docs/ops/INCYDENT_PUBLIKACJI_20072026.md):
tryby publikacji PO NAPRAWIE: AGS/x='post_queue' (Scheduler, sloty+media),
AGS/linkedin='draft' (gotowce reczne). MINA UZBROJONA: callback Subagent X Publisher
oznacza 'published' WSZYSTKIE wiersze materialu (WHERE content_item_id bez id wiersza) -
naprawic PRZED jakimkolwiek powrotem do trybu webhook. Straznik jezyka w stage_variant
(en-kanal + polski tekst -> translate_text) wchodzi z wieczornym rebuildem.

NOWE 19/07 wieczor: (0) TWARDA BRAMKA DUPLIKACJI przy generacji: embedding canonicala vs content_memory OPUBLIKOWANYCH (pgvector juz jest) -> karta z ostrzezeniem podobienstwa; incydent: material 'Orkiestracja agentow' zdublowal teze posta X z 11/07 mimo listy ostatnich publikacji w prompcie planera (LLM zignorowal; wykryla to dopiero zewnetrzna bramka jakosci przegladarkowego CM). (i) deterministyczna sciezka komend konfiguracyjnych (regex route przed
LLM) - INCYDENT: CM odpowiedzial "Zrobione" o zmianie okna BEZ wywolania target_update (DB
niezmienione, brak paragonu ⚙️; naprawa recznym SQL-em). Test prawdy: zmiana configu bez
paragonu ⚙️ = niewykonana. (ii) kanon niepelnych godzin WDROZONY (slots.humanize_slot:
+/-15 min od slotu planu, nigdy kwadrans; pq = czas ludzki, ci = czysty slot planu).
(iiib) LUKA: odrzucenie karty (matnav no) NIE kasuje wierszy post_queue materialu - zostaja
'review' na zawsze (nie publikuja sie, ale smieca; dowod: wiersz 245 artykulu odrzuconego
19/07). Fix na 1 linie w matnav 'no': UPDATE pq SET status='rejected' WHERE content_item_id.
Sprzatanie biezacych 5 sierot: UPDATE post_queue pq SET status='rejected' FROM content_items ci
WHERE ci.id=pq.content_item_id AND pq.status='review' AND ci.status IN ('rejected','archived');
(iii) KANON MEDIOW MULTI-PLATFORMA (Tomasz 19/07): jedna grafika/zdjecie = reuse na
wszystkie kanaly materialu (dziala automatem); platforma wymagajaca INNEGO medium (np.
Instagram = wideo) dostaje JAWNE zadanie w karcie: "wygeneruj albo nagraj" - zero wracania
do tematu po fakcie. Warianty formatu per platforma (LI 4:5, X 16:9) = Agent Wizualny.
(iv) Straznik dlugich X WDROZONY (stage_variant: >600 zn. bez ===POST=== = automatyczne
ciecie po akapitach na serie; grafika tylko czesc 1).
**Kolektor metryk X Owned Reads** = nastepny build (BRIEF_KOLEKTOR_METRYK_X_19072026 READY;
DDL 025; Tomasz najpierw: Developer Console pay-per-use credits + limit $10). Konsumpcja
docs/inbox/cm_przegladarka_19072026/ (artykuly/SOP od przegladarkowego CM - na razie samo
README). Metryki poniedzialkowe: eksport AggregateAnalytics -> Telegram (juz automat).
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
Nastepny wolny DDL: **026** (025 x_post_metric_snapshots zmergowany, czeka na psql w paczce
deploy integracji; 023 metryki + 024 decyzje juz wykonane u Tomasza 19/07).

## 8. SZABLONY KOMEND

- Push (PowerShell): `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" push origin claude/silly-blackwell-dfc32d`
- Rebuild (SSH): `cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 5 && curl -fsS http://localhost:8089/health; echo`
- DDL (SSH): `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/0NN_*.sql`
- Logi (SSH): `docker logs --since 30m cm-agent 2>&1 | tail -60`
