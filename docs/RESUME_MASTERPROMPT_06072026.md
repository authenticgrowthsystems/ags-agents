# MASTER PROMPT - AGS Agent Network, KONTYNUACJA (06/07/2026 wieczor, po maratonie multimediow)

Wklej na starcie nowej sesji. Self-contained. Zastepuje RESUME_MASTERPROMPT_05072026.md.

## 0. KIM JESTES / REGULY TWARDE
Jestes AGS BUILD ENGINEER. Brand voice AGS, BEZ em-dashy, liczby jako kotwice, pelny plik przy
iteracji, JEDEN atomowy krok dla Tomasza, raport po kazdym. Verify PRZED produkcja (py_compile,
node -e syntax check, read-only n8n).
- **DOCS-FIRST ZERO ZGADYWANIA**: diagnoza Z DOWODU (egzekucje n8n, pg_get_constraintdef,
  drift.log), nie proba-blad.
- **Decyzje Tomasza = GUZIKI (AskUserQuestion), rekomendacja pierwsza. Tomasz konczy sesje.**
- **PELNE SCIEZKI + PELNE KOMENDY za kazdym razem** (PowerShell vs SSH oznaczone).
- **AP-301..306** (biblioteka: anti-patterns/library.md + docs/anti-patterns/): 301 typeVersion
  z dzialajacego wezla; 302 slownictwo user-facing; 303 dollar-quote; 304 WSZYSTKIE CHECK-i
  tabeli (wszystkie DDL-e, nie pierwszy grep); **305 Notion 404 = brak Connection integracji**;
  **306 one-shot kontener MUSI sam ladowac sekrety z app_secrets i padac glosno**.
- **REGULA PRAWDY (kanon marki, 06/07)**: generatory NIE wymyslaja wydarzen/anegdot; 1. osoba
  tylko dla faktow ze zrodel; TRUTH_GUARD w kazdym prompcie (generate/planner/proactive/obrazy).
- n8n = TYLKO transport; po KAZDYM PUT deactivate+activate; PUT {name,nodes,connections,settings
  przefiltrowane}. DB zapisy = Tomasz SSH. NIE pushuj Gita (Tomasz). Placeholdery bez <>.
- Sandbox n8n Code: BRAK globalnego URL (parsuj regexem); X-Publisher mial saveDataSuccessExecution
  none (wlaczone 'all' dla diagnostyki - media_errors widoczne).

## 1. GDZIE PRACUJESZ
- **Worktree: `C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d`**
  (galaz claude/silly-blackwell-dfc32d). UWAGA: nowa sesja Cowork tworzy SWIEZY worktree z main -
  pracuj na silly-blackwell przez PELNE sciezki i `git -C`.
- Sekrety lokalne: `C:\Claude-CoWork\AGS\ags-agents\.env` (N8N_API_KEY, N8N_BASE_URL). Czytaj, nie wypisuj.
- Skrypty ops: `C:\Users\Admin\AppData\Local\Temp\ags-media-spike\` - patchery n8n uruchamiasz SAM:
  media-x-publishers.cjs (X media+nitki; sklada publishx_{sched,pub}_new.js + publishx_media_helpers.js),
  li-media.cjs (LinkedIn obraz/wideo; li_publish_new.js), hitl-video.cjs (capture wideo),
  hitl-madd-quiet.cjs (cisza Idea Bota w trybie Media), hitl-matnav.cjs (galaz mat*), backupy bk_*.json.
  Wzorzec env: `set -a && . <(grep -E '^(N8N_BASE_URL|N8N_API_KEY)=' "C:\Claude-CoWork\AGS\ags-agents\.env" | sed 's/\r$//') && set +a && node skrypt.cjs`
- Pamiec (READ FIRST): project_resume_point, project_subagent_product_definition,
  project_cm_ux_material_review, feedback_truth_first_content, project_cm_architecture_canon.

## 2. STAN LIVE (06/07 ~19:00)
**#71 Notion->PG SSOT: fazy A-F + CUTOVER DONE 05/07** (67 stron READ-ONLY MIRROR, sync worker
w cm-agent LIVE, drift cron 03:00 czysty, kolejka sync zdrowa). **ZOSTALO: formalne CLOSED**
(sekcja 4 ponizej) + iteracyjne enable tabel wg docs/cm/SYNC_ENABLE_PLAN.md (Zadanie 1 =
agent_prompts; kryterium 24h clean, dat nie trzymamy sie kurczowo).

**CM/subagenci - zbudowane 06/07 (wszystko LIVE po ostatnim rebuildzie):**
- **Sloty+okna**: Tomasz zatwierdza TRESC, CM przydziela KIEDY (slots.py; publish_windows per cel:
  AGS x 13:00-22:00, li 13:00-18:00 czasu WAW = okno US; TNM/RDC 08-18). **SIATKA slot_grid x =
  14:00/16:00/18:00/20:00 - ZATWIERDZONA PRZEZ CM w pierwszej negocjacji agent->agent 16:32!**
- **Negocjacje agent->agent**: subagent escalate_to_cm -> agent_messages -> CM decyduje (LLM),
  wpisuje config, response + meldunek na bocie #2 + wynik glosem subagenta W CZACIE; antydubel;
  USTALENIA Z CM w kontekscie subagenta. Rejestr: content-manager, subagent-x, subagent-linkedin.
- **Karty (matreview.py)**: kompakt 500 zn.; szeroki ▼Rozwin/▲Zwin (w okienku, limit ~3300);
  4 decyzje + ✏️ Edytuj + ➕Media/🎨Generuj/🗑Media; strzalki zawijaja; multimedia AUTO pod karta
  ('POLECI Z POSTEM', 🎬 dla wideo); 'karty'/'decyzje' przywoluja na dol; show_review_cards z
  theme_fragment/only_with_media (karta KONKRETNEGO materialu).
- **Edycja = AKCEPTACJA** + NAUKA STYLU: VOICE_EDIT (pary przed/po w agent_logs) + destylacja
  regul -> brand_config style_learned -> KAZDY prompt; add_style_rule ('zapamietaj na zawsze');
  wyuczone reguly odsylane Tomaszowi. Inny kat v4: Tomasz podaje kat wiadomoscia (45 min, 'auto').
- **Filtr czystej polszczyzny** w compliance (polish_pl, 'test mamy') + app.bulk_polish (one-shot;
  AP-306!). **Nitki X**: ===TWEET=== 3-6 postow 300-550 zn. (dziala E2E), media na 1. poscie.
- **MULTIMEDIA KOMPLET**: etap 1 foto X+LinkedIn (LI post z obrazem OPUBLIKOWANY E2E 15:37);
  2a GENEROWANIE obrazow (🎨 gpt-image, klucz openai_api_key, podglad=magazyn file_id);
  2c WIDEO wlasne (capture video+video_note w HITL 240 wezlow, galeria/podglad, X chunked 4MB
  +STATUS poll, LI recipe video 1/post, limit 19MB->GDrive backlog). Galeria wyboru ➕ Media
  ([1..6]/Wyslij nowe/Anuluj, timeout 10 min), cisza Idea Bota w trybie Media.
- **Proaktywnosc**: odprawa poranna (semi, 09:00-11:30), luki kadencji dzis/jutro -> propozycje
  z antydublem -> intake guziki, poniedzialkowa prosba o metryki (reczne, subagent_set_metrics),
  suggest_comment (3 komentarze comment-first pod cudzy post, sonnet, jezyk celu).
- **Rozmowa CM widzi**: kolejke 60 + 🖼xN, STAN OPERACYJNY (tryby madd/edit/angle + ostatnie
  przypiecie), CELE I KONFIGURACJE + mechanike slotow, plan, schowek, archiwum. Zakaz zgadywania.
- Sunday guard (przypomnienia 15 min + fallback 23:00 z przyszlym slotem), stan awaryjny 24h.
- Legacy AGS X Agent OFF; TMP webhooki skasowane.
- **NIEROZWIAZANE**: X obraz w tweecie - nitka poszla BEZ obrazow (media_errors polkniete;
  exec saving juz ON) -> nastepna publikacja X z obrazem da dowod; wtedy napraw z dowodu.
  Meldunek 'CM opublikowal' jest optymistyczny (przed callbackiem) - backlog fix.

**Dokumenty**: docs/product/SUBAGENT_PACKAGE_v1.md (zywy cennik-fundament; aktualizuj po buildach),
docs/cm/CM_UX_FEEDBACK_05072026.md, docs/cm/SYNC_ENABLE_PLAN.md, docs/cm/RAPORT_do_Managera_71-*.md,
SYSTEM_DATAFLOW.md sekcja F.

## 3. TESTY W TOKU (Tomasz klika, Ty czytasz dowody)
1. 🎨 Generuj na karcie -> obraz -> zalacznik. 2. Wideo 10s botowi -> galeria -> 🎬 -> Zatwierdz
-> post z wideo (X: obserwuj exec Schedulera/Publishera - media_errors!). 3. "i jak zatwierdzil?"
u subagenta x (USTALENIA). 4. Karty w rytmie Tomasza (32+); stan awaryjny 24h czuwa.

## 4. KLAMRA #71 CLOSED (dzis ~21:20 albo gdy Tomasz wroci)
SSH kontrola: `tail -5 ~/ags-agents/cm-agent/logs/drift.log; docker exec pg_n8n psql -U n8n -d ags_crd -c "SELECT status, COUNT(*) FROM sync_queue GROUP BY status;"`
Czysto (OK + zero failed) => oglos **#71 CLOSED** (meldunek Tomasz -> Manager, 3 dni przed terminem)
i od razu Zadanie 1: `docker exec pg_n8n psql -U n8n -d ags_crd -c "UPDATE sync_registry SET enabled=TRUE WHERE table_name='agent_prompts'; SELECT table_name, enabled FROM sync_registry WHERE enabled;"`
Nastepne tabele wg SYNC_ENABLE_PLAN (24h clean -> nastepna; page_map dla tabel append PRZED
zadaniami 2-3!). Zaktualizuj pamiec + SUBAGENT_PACKAGE.

## 5. BACKLOG (kolejnosc z Tomaszem, guziki)
(a) test/naprawa X obraz (dowod z exec); (b) meldunek publikacji po CALLBACKU nie przy delegacji;
(c) karta-fotka (obraz na gorze, decyzja Tomasza wisi); (d) naglowek dnia na kartach + filtr
'karty jutro'; (e) Idea Bot INTENCJE ('Poprosze o raport' to nie pomysl); (f) GDrive media #9
(wideo >19MB); (g) GENERATOR WIDEO = deep research (Tomasz zbiera rolki IG); (h) zdjecia
referencyjne/higgsfield (2b, twarz w generowanych); (i) ICP-hunting po decyzji o metrykach/API;
(j) task #70 pakiet sprzedawalnosci (playbook+diagram z SSOT+sync_registry); (k) Newsletter #6
anchor 'SSOT w 1 dzien' + zrzut LI z obrazem; (l) RLS przed aktywacja TNM/RDC; (m) konto X dla
TNM (Tomasz zaklada, podpiecie 10 min); (n) i18n; (o) 'zatwierdz w innym terminie' (przesuwanie
slotu approved z karty/rozmowy).

## 6. SZABLONY KOMEND (zawsze podawaj PELNE)
PowerShell push: `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d" push origin claude/silly-blackwell-dfc32d`
SSH pull+rebuild cm-agent: `cd ~/ags-agents && git pull --ff-only && cd cm-agent && docker build -t cm-agent:latest . && docker stop cm-agent && docker rm cm-agent && docker run -d --name cm-agent --restart unless-stopped -m 512m --network n8n_network -p 127.0.0.1:8089:8089 --env-file ./.env -v "$PWD/logs":/app/logs cm-agent:latest && sleep 5 && curl -fsS http://localhost:8089/health; echo`
SSH DDL: `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/0NN_*.sql` (next: 017)
SSH one-shot (AP-306 - moduly laduja sekrety same): `docker run --rm --network n8n_network --env-file cm-agent/.env cm-agent:latest python -m app.<modul>`

## 7. PIERWSZY RUCH NOWEJ SESJI
1) Przeczytaj pamiec (lista w sekcji 1). 2) `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d" log --oneline -5`
(HEAD powinien byc c831610 albo nowszy; jesli Tomasz nie zdazyl push/rebuild - najpierw deploy
zbiorczy sekcja 6). 3) Zapytaj Tomasza o wyniki testow z sekcji 3 i czy klamra #71 (sekcja 4)
juz wykonana; potem backlog sekcja 5 guzikami.
