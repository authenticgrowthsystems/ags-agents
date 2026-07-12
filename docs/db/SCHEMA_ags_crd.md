# Schemat bazy ags_crd - tabele bazowe (poza migracjami cm-agent/db)

**Cel:** żywy zapis struktury tabel, które POWSTAŁY POZA repo (build 31/05 X-agent + późniejsze),
żeby programista czytał, a nie odpytywał bazy. **Reguła: każda zmiana DDL = aktualizacja tego pliku.**
Migracje wersjonowane są w `cm-agent/db/0NN_*.sql`; ten plik dokumentuje tabele bazowe i te,
których DDL nie ma w repo.

Weryfikowane z `information_schema.columns` na produkcji 07/07/2026.

## brand_config (single source of truth konfiguracji marki, k/v)
Klucz logiczny: UNIQUE (brand_id, config_key). **Brak kolumny notion_page_id** (mirror do Notion
przez page_map, nie przez wiersz). voice_bible siedzi tu jako wiersz config_key='voice_bible'.

| kolumna | uwagi |
|---|---|
| brand_id | np. 'AGS' (WIELKIE litery - app używa 'AGS') |
| config_key | np. 'voice_bible', 'banned_vocab', 'cm_*' (stany modułów) |
| config_value | TEXT (dla voice_bible = pełny markdown Voice Bible) |
| version | INTEGER, bump przy każdej zmianie (voice_bible: v2.0=2, v2.1=3) |
| updated_by | kto zmienił |
| updated_at | NOW() |

Czytany LIVE przez `brand._config_value` (ORDER BY version DESC LIMIT 1) - **brak cache**, nowa
wersja łapie się przy następnym requeście. `voice_hash` = md5(config_value) liczony w kodzie
(`brand.load_brand`), NIE ma kolumny md5.

## brand_config_history (audit trail zmian brand_config)
| kolumna | nullable | default |
|---|---|---|
| id | NO | nextval (serial) |
| brand_id | YES | |
| field | YES | np. 'voice_bible' |
| old_value | YES | wartość/marker przed |
| new_value | YES | wartość/marker po |
| version_from | YES | |
| version_to | YES | |
| updated_by | YES | |
| updated_at | NO | now() |

## agent_prompts (kanoniczny rejestr promptów; DDL w cm-agent/db/010)
**UWAGA:** app CM NIE czyta tej tabeli - to rejestr kanoniczny + mirror do Notion. Egzekucja
compliance jest w KODZIE (`compliance.py`), nie z agent_prompts.

| kolumna | uwagi |
|---|---|
| id | UUID default gen_random_uuid() |
| agent_name | VARCHAR(80), luźny klucz |
| version | VARCHAR(20) |
| title | TEXT |
| content | TEXT NOT NULL |
| status | 'active' \| 'superseded' (default 'active') |
| notion_page_id | TEXT UNIQUE, nullable |
| created_at | NOW() |

## brand_tokens (tokeny wizualne marek; DDL w cm-agent/db/019, task #84 12/07/2026)
SSOT = baza Notion "Brand Config" (Token_Name / Token_Type / <BRAND>_Value); puller w cm-agent
(app/sync/brand_tokens_pull.py, poll 10 min, konfiguracja: /set brand_tokens_notion_db <id>).
Konsument: generate._visual_canon() - PIERWSZE zrodlo promptow graficznych (przed brand_config
visual_canon i fallbackiem w kodzie).

| kolumna | uwagi |
|---|---|
| brand_id | VARCHAR(50) PK, FK -> brands(brand_id) |
| tokens | JSONB NOT NULL, {token_name: {type: color/font/spacing/motyw/zakaz, value}} |
| updated_at | TIMESTAMPTZ default NOW() |
| source | VARCHAR(50) default 'notion_sync' |

## TODO (rozszerzenie dokumentacji schematu)
Pełny `pg_dump --schema-only` do zrzucenia i dopisania tu dla POZOSTAŁYCH tabel bazowych
(post_queue, task_queue, published_posts, contacts, engagement_log, inspirations, channels,
content_items, user_agent_state, app_secrets, agent_messages, agent_logs...). Priorytet: te,
które app zapisuje/czyta bez DDL w repo. Zrzut nie zmieścił się w jednym wklejeniu - do zrobienia
plikowo przy następnej okazji SSH (wariant: pg_dump do pliku w repo na Mikrusie + commit stamtąd).
