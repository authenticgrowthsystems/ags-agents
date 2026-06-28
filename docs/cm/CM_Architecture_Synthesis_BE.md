# CM Architecture - Synteza BE (4 raporty ręczne + nasz stack)

**Data:** 28/06/2026. **Autor:** AGS Build Engineer (Opus 4.8). **Wejście:** 4 raporty ręczne Tomasza (deep-research-report, Projekt Architektury Agenta CM, Manus Implementation Plan, extract-data JSON) + Researcher (medium, automat). **Cel:** osadzić zbieżną rekomendację w NASZEJ realnej infrze i wydobyć decyzje punkt-po-punkcie przed Bramą 2.

## 1. KONSENSUS (wszystkie 4 źródła zgodne - to NIE jest sporne)

**Centralized Content Brain + async delegacja do cienkich adapterów kanałowych.**
- CM = supervisor/orkiestrator (serwis FastAPI), NIE miejsce gdzie miesza się pamięć+kolejka+copywriting+publikacja w jednym kroku. CM trzyma STAN DECYZJI (co planowane / czeka na research / czeka na approval / rozdystrybuowane / opublikowane).
- **Jeden kanoniczny obiekt treści** (Sonnet 4.6 generuje bogaty tekst-matkę) -> adaptery kanałowe (X/LinkedIn/IG) transformują go per platforma (Haiku 4.5, tanio). To chroni RAM (4GB VPS): jedno drogie wywołanie + lekkie adaptacje, NIE 5 równoległych sesji Sonnet.
- Stack = NASZ obecny: Python + n8n + Postgres SSOT. CM = kolejny agent na **kontrakcie async /request** (dokładnie szablon, który zbudowałem dziś dla Researchera - raporty niezależnie go odtworzyły: POST /request -> 202 -> callback).
- **brand_config = jedyne źródło głosu** (live-read + zapis voice_hash/version przy generacji) + **prompt caching** Anthropic na bloku Voice Bible (oszczędność do ~90% input, prefiks musi być bajtowo stały).
- **HITL = 3 bramy** przez Telegram (plan / materiał ryzykowny / publikacja).
- **Multi-tenant brand_id** wszędzie; raporty rekomendują RLS (Row Level Security) do izolacji marek.
- **Notion -> Postgres** jako SSOT: migracja shadow-sync -> parity check -> cutover PER CONSUMER (najpierw CM czyta, potem Idea-bot, na końcu X-agent - on ma największe ryzyko duplikatów).
- n8n = EGZEKUTOR przejść stanu, NIE master danych. Stan biznesowy w Postgresie.

## 2. KOREKTY STACKU (raporty ręczne są architektonicznie dobre, ale stack-naiwne - to naprawiam jako BE)

| Raport mówi | Nasza prawda (poprawka) |
|---|---|
| `claude-3-5-sonnet-20241022` / `claude-3-{tier}` | haiku=`claude-haiku-4-5-20251001`, sonnet=`claude-sonnet-4-6`, opus=`claude-opus-4-8` (zweryfikowane) |
| psycopg2 + SQLAlchemy | psycopg3 + `psycopg_pool` + surowy SQL (jak Researcher) |
| Klucze API w Dockerfile ENV | `app_secrets` single-source; worker .env = tylko POSTGRES_DSN + N8N_BASE_URL |
| `uuid-ossp` | `gen_random_uuid()` (pgcrypto, już jest) |
| port 8000 | własny port (np. 8089), `127.0.0.1`-only, sieć `n8n_network`, webhook guarded `X-Researcher-Secret`-style |
| nowe `inspirations_pool`, `content_drafts` | REUSE istniejących `inspirations`, `hitl_sessions`; nie duplikuj |
| `brand_config` z UUID PK + kolumna voice_bible | nasz `brand_config` = key/value (`brand_id` TEXT='AGS', config_key/config_value; voice_bible to WIERSZ). NIE restrukturyzować |

Korzyść z routingu do BE potwierdzona: premium research dał świetną architekturę, ale wskazywał nieistniejące u nas modele/sterowniki/tabele. Ja to mostkuję do realnego kodu.

## 3. Researcher (medium) vs ręczne premium - kalibracja

Ręczne premium (4 raporty: filozofie + tradeoffy + anti-patterns + DDL + cytowane źródła) były DUŻO bogatsze niż automatyczny Researcher medium (4 opcje, ~0.34 PLN, conf 0.48-0.81). Wniosek: **dla decyzji klasy architektura - ręczne premium albo Researcher na wyższym tierze**. Researcher medium = dobry do faktów/wzbogacania, nie do projektu systemu. (Fast-follow: tier "architektura" -> opus + cięższy Gemini w adapterze, po cost-reconcile.)

## 4. DECYZJE DO PODJĘCIA (punkt po punkcie z Tomaszem, przed Bramą 2)

- **D1. Rdzeń danych:** lean `content_items` (1 nowa tabela-mózg + reuse istniejących, kalendarz = widok/pole) [deep-research] vs pełny zestaw nowych tabel calendar-centric [Manus/Projekt].
- **D2. `brand_strategy`:** osobna tabela (audience/pillars/topics per marka, odrębne od voice_bible) vs fold do brand_config.
- **D3. Multi-tenancy:** RLS + `SET LOCAL app.current_brand_id` teraz vs filtrowanie brand_id w aplikacji teraz (schema RLS-ready, polityki później).
- **D4. Migracja Notion:** w MVP CM vs po (shadow-sync ostrożny; można odłożyć, X-agent zostaje na Notion do czasu).
- **D5. Zakres kanałów MVP:** X (live adapter) + LinkedIn (draft-only) + IG/FB jako cele planu (bez publikacji) na start.

Każdą rozstrzygamy osobno, z rekomendacją BE, zanim ruszy build.

## 5. DECYZJE ROZSTRZYGNIĘTE (log, Tomasz 28/06)

- **OBSIDIAN = mózg STRATEGICZNY Managera (NIE CM).** Dwuwarstwowy, jednokierunkowy przepływ: Obsidian (strategia/why/relacje, warstwa Manager+Tomasz, Cowork) -> Manager (najcięższy model) destyluje -> Postgres `brand_config`+`brand_strategy` (SSOT operacyjny) -> CM czyta projekcję. Obsidian projektujemy przy MIGRACJI MANAGERA (krok po CM). Agenci serwerowi nie czytają Obsidiana; `voice_bible` zostaje kanoniczny w Postgresie. Reguła anty-dryf: strategia płynie Obsidian->Postgres, nigdy odwrotnie.
- **D1 ROZSTRZYGNIĘTE = Lean.** CM rdzeń operacyjny = Postgres: 1 nowa tabela `content_items` (mózg: brand_id, temat/master_theme, canonical_body, kanały docelowe, status, scheduled_for, link do research_jobs/inspiracji) + REUSE: `post_queue` jako per-kanałowy outbox/warianty, `published_posts` (pamięć), `inspirations` (pomysły), `brand_config` (głos). Kalendarz = pole/widok na content_items, nie osobny master. Obsidian NIE zastępuje tego rdzenia, tylko zasila go przez Manager->brand_strategy.
- **D2 ROZSTRZYGNIĘTE = osobna lean `brand_strategy`** (brand_id, target_audience, content_pillars[], core_topics[], opcj. competitor_urls). voice_bible zostaje w brand_config. To 2. i OSTATNIA nowa tabela obok content_items.
- **D3 ROZSTRZYGNIĘTE = app-level brand_id teraz + schema RLS-READY** (brand_id NOT NULL + indeks wszędzie); RLS policies włączamy jako osobny krok PRZED wciągnięciem 2. marki do CM. **KOREKTA Tomasza: multi-tenant LIVE TERAZ** - marki już działające: AGS, TNM (tyniemusisz.pl, PL, LinkedIn firmowy przynosi efekty), Royal Dance (ciągle), SdI/Impress (do ruszenia). CM MVP startuje od AGS i onboarduje marki kolejno -> RLS-enablement = bliski P1 (nie odległa przyszłość), tani retrofit bo brand_id już wszędzie.
- **D4 ROZSTRZYGNIĘTE = migracja Notion PO MVP** (osobny ostrożny krok shadow-sync -> parity -> cutover per consumer). CM MVP dowodzi rdzenia na NOWEJ treści; żywy X-agent czytający Notion zostaje nietknięty podczas budowy.
- **D5 REFRAME (Tomasz: BEZ półśrodków) = pełna obiektowa abstrakcja kanałów.** WSZYSTKIE kanały (X, LinkedIn, YouTube, Facebook, Instagram) = pierwszoklasowe MODUŁY na jednym kontrakcie przyłącza (generate-variant, validate, publish-or-draft, status) + **rejestr kanałów** (3. nowa tabela `channels`: brand_id, channel, status active/ready, creds_ref, config). AKTYWNE od startu: X (auto-publish), LinkedIn (generacja wariantu; auto-publish gdy API wpięte). GOTOWE-do-wpięcia (stub do tego samego kontraktu, nieaktywne): YouTube, Facebook, Instagram - implementacja per-moduł przy aktywacji (creds+API). Zasada: kompletna abstrakcja OOP, nie hardkodowany minimalny MVP. [[feedback_no_halfmeasures_modular]]. **3 nowe tabele łącznie: content_items, brand_strategy, channels.**
- **D5 FINAL (Tomasz: zero poślizgu + dowolny przyszły subagent) = GENERYCZNY framework subagentów (open/closed).** CM = generyczny GOSPODARZ subagentów, gotowy przyjąć DOWOLNY nowy kanał/subagenta (X, LinkedIn, YT, FB, IG, TikTok, Pinterest, + nieznane przyszłe) BEZ przebudowy rdzenia. Rejestr `channels` generyczny (channel = dowolny string, NIE sztywny enum). **Jeden kontrakt dla WSZYSTKICH subagentów** (publishery + Researcher + przyszli) = ten sam async `/request` webhook + callback + rejestr, który zbudowano 28/06. Dodanie subagenta = wpis w rejestrze + implementacja modułu do kontraktu, ZERO zmian w CM core. Nie budujemy każdego API teraz (to byłby poślizg) - budujemy GENERYCZNY framework, który czyni każde wpięcie trywialnym. Researcher = referencyjny subagent (już na kontrakcie).

## 6. ARCHITEKTURA ZABLOKOWANA (wynik Bramy 1 = wejście do Bramy 2)

Centralized Content Brain na FastAPI+n8n+Postgres SSOT. CM = generyczny supervisor/host subagentów na jednym async kontrakcie (/request+callback+rejestr). Rdzeń: `content_items` (mózg) + `brand_strategy` + `channels` (generyczny rejestr) + REUSE (post_queue outbox, published_posts pamięć, inspirations, brand_config głos). Voice live-read + hash + prompt caching. HITL 3 bramy Telegram. Multi-tenant app-level + RLS-ready (RLS przed 2. marką w CM). Notion migracja PO MVP. Kanały aktywne: X (auto) + LinkedIn (draft); reszta ready-to-plug. Obsidian = mózg strategiczny Managera (warstwa wyżej, przy migracji Managera).
