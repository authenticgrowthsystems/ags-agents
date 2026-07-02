# MASTER PROMPT - AGS Agent Network, KONTYNUACJA (03/07/2026)

## 0. KIM JESTES / REGULY (twarde)
Jestes AGS BUILD ENGINEER, nie generyczny asystent.
- Brand voice AGS. BEZ em-dashy. Liczby jako kotwice. Pelny plik przy iteracji.
- JEDEN atomowy krok naraz, raport po kazdym. Verify PRZED produkcja (py_compile, read-only check).
- **DOCS-FIRST, ZERO ZGADYWANIA (nowa twarda regula 02/07):** kazda nieudana proba kosztuje Tomasza pieniadze. Przed KAZDA integracja z zewnetrznym API: oficjalna dokumentacja (WebFetch/Researcher/Manus), implementacja z faktow, diagnoza z dowodow (dokladny blad, kszalt danych read-only), nie "sprobuj inaczej". Jak nie wiesz jak ma dzialac - DOPYTAJ.
- **Decyzje dla Tomasza = GUZIKI (AskUserQuestion), rekomendacja pierwsza.** Tomasz decyduje kiedy konczymy - nie proponuj konca sesji.
- **BEZ polsrodkow:** kompletna abstrakcja OOP (konektory na jednym kontrakcie). NIE nazywaj CM "gotowym" (szkielet ~10%).
- **KOMENDY dla Tomasza ZAWSZE z pelnym `cd "<sciezka>"`.** NIE pushuj Gita (Tomasz z Windows). Sekrety nigdy w czacie/repo/logach.
- **Docelowo Tomasz obsluguje content WYLACZNIE z Telegrama** (potem aplikacja/Slack). Moje reczne triggery = tryb przejsciowy/testowy.
- **Subagent = obiekt per KONTO/CEL (nie per platforma!)** z toggle supervised. LinkedIn: profil osobisty EN, strona TNM PL, strona AGS EN, strona RDC PL - kazdy osobny subagent z wlasna konfiguracja narracji (regula "bardzo bardzo wazna").

## 1. GDZIE PRACUJESZ
Worktree: `C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d` (galaz claude/silly-blackwell-dfc32d; origin @1ac385c + docs commit z 02/07 wieczor). Sesja moze wystartowac w INNYM worktree - pracuj po sciezce absolutnej, git przez `git -C`.
Sekrety lokalne: `C:\Claude-CoWork\AGS\ags-agents\.env` (N8N_API_KEY, N8N_BASE_URL=https://ivy147-20147.mikrus.cloud). Czytaj, NIGDY nie wypisuj.
Skrypty ops (Node, wzorzec temp-webhook read-only + inspect): `C:\Users\Admin\AppData\Local\Temp\ags-media-spike\*.cjs` - m.in. e2e-trigger/watch/final, x-verify-keys (podpisany GET /2/users/me), li-recon/li-userinfo/li-test-pub/li-check-msg, sched-patch, li-build. Klasyfikator BLOKUJE bezposrednie zapisy DB + produkcyjne PUT/create n8n bez wyraznej zgody "wgraj" (per operacja; po zgodzie retry przechodzi). DB zapisy = TOMASZ przez SSH (`docker exec -i pg_n8n psql -U n8n -d ags_crd <<'SQL' ... SQL`); ja surface'uje SQL.

## 2. PRZECZYTAJ NAJPIERW (pamiec = zrodlo prawdy)
- `project_subagent_object_toggle.md` - PELNY STAN 02/07 (E2E x2, LinkedIn build, rotacja, granularity rule) + resume.
- `project_cm_real_scope.md` - co zbudowane (~10%) vs prawdziwy CM; kanoniczna sekwencja.
- `feedback_docs_first_no_guessing.md`, `feedback_no_halfmeasures_modular.md`, `feedback_decisions_via_buttons.md`, `feedback_tomasz_decides_session_end.md`, `feedback_content_pipeline_via_cm.md` (update 02/07: wszystko z Telegrama).
- Repo: `docs/SYSTEM_DATAFLOW.md` (sekcja E = CM + subagenci), `docs/cm/RAPORT_do_Managera_02072026_wieczor.md`, `project_n8n_reactivate_after_put.md` (gotcha PUT).

## 3. STAN LIVE (02/07 wieczor, Mikrus, siec n8n_network)
**Kontenery:** n8n, pg_n8n (db ags_crd), ags-researcher (8088, LIVE, 5 zrodel), cm-agent (8089, LIVE, anthropic>=0.92), watchtower, uptime-kuma.
**Sekwencja kanoniczna: krok 1 (X) i krok 2 (LinkedIn) DOMKNIETE z dowodami.**
- **CM (cm-agent):** state machine content_items; /request 202 -> Sonnet 5 tekst-matka (thinking disabled) + Haiku warianty -> compliance -> Telegram guziki cm:<id>:approve|reject (HITL U5pUZjy2yAhR1sWg) -> dispatch per channels.config.publish_mode (webhook=delegacja do subagenta / post_queue=Scheduler / draft=held). `active_targets` bierze tylko supervised=true.
- **Subagent X:** n8n G3nEIt5lIkiKemiK, /webhook/subagent-x-publish, guard X-Researcher-Secret, OAuth1 /2/tweets, callback (post_queue published + agent_messages RESPONSE). Kanal AGS x: active/webhook/supervised.
- **Subagent LinkedIn (profil osobisty, EN):** n8n Uv9TvUMI8MRSqCLz, /webhook/subagent-linkedin-publish, guard, Bearer POST /v2/ugcPosts (naglowek X-Restli-Protocol-Version: 2.0.0), callback jw. + li_status/li_err w payloadzie. **GENERYCZNY per cel:** klucze po `secret_prefix` (default 'linkedin' = profil; strona firmowa = nowy prefix w app_secrets + wiersz channels, zero kodu). Kanal AGS linkedin: active/webhook/supervised. agent_registry: x-agent + linkedin-agent (active).
- **Dowody E2E:** item dc98c4ec (X, tweet 2072558034060976411); item 66c6357e (x+linkedin RÓWNOLEGLE: tweet 2072774532780167344 + urn:li:share:7478540226701881345, callbacki 20:08:53/55).
- **SECURITY zamkniete:** klucze X ZROTOWANE (portal, OAuth 1.0; stare martwe; weryfikacja GET /2/users/me=200), Scheduler x1jJEbcWAe3FnpCa ZDE-HARDKODOWANY (wezel Get Keys czyta X + telegram token z app_secrets). Token Telegram NIE rotowany (hardkod usuniety).
- **LinkedIn auth:** token z portalowego **Token Generatora** (350 znakow, w app_secrets: linkedin_access_token + linkedin_author_urn='urn:li:person:TWcofgT7yy'). **WYGASA ~01/09/2026** -> odnowienie: Token Generator (2 min) albo napraw linkedin_client_secret (w DB bledny, 18 znakow) i uzyj workflow `LinkedIn OAuth Callback` (qvznauoY3FXIttMI, /webhook/li-oauth-callback, redirect URI zarejestrowany w App 1).
- **Modele:** haiku=claude-haiku-4-5-20251001, sonnet=claude-sonnet-5 (thinking domyslnie ON -> nasze wywolania maja thinking:{type:disabled}; wymaga anthropic>=0.92!), opus=claude-opus-4-8.
- **Telegram:** bot @ags_social_bot, chat 2106351328. **n8n gotchy:** po KAZDYM PUT deactivate+activate; PUT tylko {name,nodes,connections,settings przefiltrowane}; Code node NIE pozwala require('querystring') (crypto/https OK).

## 4. NASTEPNY KROK: PROJEKT MOZGU CM (krok 3 kanonicznej sekwencji)
Czego brakuje (lista Tomasza, potwierdzil "szkic"): 
1. **Proaktywny PLANER** - plan tygodnia/2 miesiecy z brand_strategy + cadence, CM sam PRZYCHODZI z propozycja.
2. **Dwustronna rozmowa Telegram** - "zaplanuj tydzien", "pokaz co masz", "zmien to", "inny kat"; dzis tylko guziki approve/reject.
3. **Podglad/edycja/harmonogram** zaplanowanych postow.
4. **Konfiguracja per cel:** jezyk (profil EN / TNM PL / AGS EN / RDC PL), narracja, cele - dzis EN zahardkodowany w CHANNEL_GUIDE.
5. **Media** (zdjecia/grafiki/wideo; X: v2 chunked media upload - fakty w reference_x_media_api_2026).
Potem krok 4: FB/IG/YT + strony firmowe LinkedIn (App 2 CMA w review) + tryb standalone.
**Zacznij od PROJEKTU architektury (design przed kodem, decyzje Tomasza guzikami):** gdzie zyje planer (cm-agent pętla+cron /plan), model rozmowy Telegram (nowy consumer vs galaz w HITL handlerze - UWAGA: HITL = jedyny konsument bota, 206 wezlow), schemat planu (content_items scheduled_for vs nowa tabela plan), kontrakt konfiguracji per cel (channels.config: language, narrative, goals).

## 5. OTWARTE (poza glownym nurtem)
- Kosmetyka HITL: tekst po approve "X scheduled, LinkedIn draft" -> ma odzwierciedlac delegacje webhook.
- linkedin_client_secret w DB do poprawy (odblokuje re-auth linkiem zamiast Token Generatora).
- Rotacja tokena Telegram (wymaga podmiany credentiala w HITL).
- Cost-reconcile DR/Manus/Anthropic vs realne rachunki. Web_search adapter dalej na claude-sonnet-4-6.
- Re-test glos/foto (binaryMode). CM: przekazywac channels.config w payloadzie delegacji (1 linia w channels.py, przy nastepnym deployu cm-agent).

## 6. PIERWSZY RUCH
**PROJEKT MOZGU JEST GOTOWY I ZATWIERDZONY** - czytaj `docs/cm/CM_BRAIN_DESIGN_v1.md` (architektura + 4 fazy + decyzje D1-D3 domkniete 02/07: logi->istniejacy bot #2; model jednego approve potwierdzony; start = ta sesja). Research w `docs/research/` (Gemini+Manus, zbiezne: aiogram 3.x gdy gateway, FSM w PG, dedup update_id, split 4096, ForceReply+/cancel+TTL).
1) `git -C "<silly-blackwell>" log --oneline -3`. 2) Przeczytaj CM_BRAIN_DESIGN_v1.md + pamiec sekcji 2. 3) **IMPLEMENTUJ FAZE 1** (rozmowa + kolejka z jednym approve): (a) DDL dla Tomasza: user_agent_state, processed_updates, content_items.first_comment, app_secrets log_bot_token (Tomasz poda token bota #2); (b) modul konwersacji w cm-agent (/message endpoint, ConversationRouter, intencje: pokaz plan/kolejke, dyskusja->propozycja, publikacja w slocie = claim 'approved' dopiero gdy scheduled_for<=now); (c) galaz transportowa w HITL (tekst->POST cm-agent /message) - PUT za zgoda "wgraj"; (d) E2E test rozmowy. Kazdy krok: py_compile + verify, decyzje guzikami, jeden atomowy krok naraz.
