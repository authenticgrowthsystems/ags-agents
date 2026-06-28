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
