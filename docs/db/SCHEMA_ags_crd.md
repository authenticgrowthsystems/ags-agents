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

## agent_learning_log (petla nauki; DDL w cm-agent/db/020, task #87 12/07/2026)
Kazda decyzja Tomasza o tresci (karta/edycja/podmiana) -> wiersz; generacja czyta ostatnie 20
(generate._learning_digest) przed pisaniem. KOREKTA do briefu: content_item_id = UUID (nie BIGINT).

| kolumna | uwagi |
|---|---|
| id | BIGSERIAL PK |
| subagent_id | VARCHAR(100), 'cm:<brand>' (karty) albo '<brand>:<channel>' (edycje wariantow) |
| brand_id | VARCHAR(50) |
| content_item_id | UUID FK -> content_items(id), nullable |
| proposed_content | TEXT NOT NULL (wersja agenta) |
| final_content | TEXT (wersja po decyzji; NULL przy rejected) |
| diff | TEXT (rezerwa, dzis NULL) |
| correction_type | CHECK: accepted / edited / rejected / replaced |
| notes | TEXT (zrodlo decyzji) |
| created_at | TIMESTAMPTZ default NOW() |

Indeks: idx_learning_log_subagent (subagent_id, created_at DESC).

## channels - kolumna execution_mode (DDL w cm-agent/db/020, task #87)
VARCHAR(30) NOT NULL DEFAULT 'supervised', CHECK: supervised / semi_autonomous / autonomous.
Tryb egzekucji per cel (canonical 12/07 Q2); dzis wszyscy 'supervised' - egzekwowanie trybow
semi/auto = task #86 (menu marek) i dalsze. Przejscia trybow = jawna decyzja Tomasza.

## brands - status (DDL w cm-agent/db/021, task #86 12/07/2026)
CHECK rozszerzony: active / paused / **archived** (soft-delete z /brand_remove - dane
historyczne marki zostaja; /brand_on przywraca). Zarzadzanie: komendy Telegram /brands,
/brand_on|off|add|remove|config|export (cm-agent/app/brands_ui.py, deterministyczne bez LLM).

## channel_metrics_daily (DDL 023, plan dnia 19/07 krok [1] - koniec slepoty metrycznej)
Metryki poziomu KANALU per dzien. Zrodla: import xlsx AggregateAnalytics LinkedIn (Telegram
dokument -> n8n galaz document_xlsx -> POST /metrics/xlsx -> app/metrics_import.py), reczny
wpis X, przyszly kolektor X (szew stats_mode='x_owned_reads' w reports.refresh_metrics).

| kolumna | typ |
|---|---|
| id | BIGSERIAL PK |
| brand_id / channel | VARCHAR(50) / VARCHAR(40) |
| metric_date | DATE; UNIQUE (brand_id, channel, metric_date) |
| impressions / reactions / new_followers / followers_total | INT nullable (COALESCE-merge przy ponownym imporcie) |
| source | CHECK: linkedin_xlsx / x_manual / x_api / linkedin_api |
| raw | JSONB (wartosci dnia z importu) |
| imported_at | TIMESTAMPTZ default NOW() |

Indeks: idx_chan_metrics_lookup (brand_id, channel, metric_date DESC). Raporty subagenta czytaja
przez reports._profile_lines (sekcja PROFIL; >3 dni bez danych = prosba o swiezy eksport).

## channel_audience_snapshots (DDL 023)
Demografia obserwujacych per import: brand_id, channel, captured_date (UNIQUE-triplet),
followers_total INT, demographics JSONB (lista {category, value, pct}), source. Per-post metryki
NIE tu - zostaja w published_posts.engagement_metrics (merge ||, source 'linkedin_xlsx',
match po URN ugcPost-/share-<digits> w post_id).

## agent_decisions (DDL 024, plan dnia 19/07 krok [2] - eskalacja guzikami + nauka)
Ledger ustrukturyzowanych decyzji CM/subagent -> Tomasz (kanon 19/07: eskalacja GUZIKAMI,
kazda odpowiedz uczy). Obsluga: app/decisions.py (ask/handle), callback 'dec:<id>:<key>'
przez n8n galaz dec: -> POST /decnav.

| kolumna | typ |
|---|---|
| id | BIGSERIAL PK |
| subagent_id | VARCHAR(100) ('CM' albo 'AGS:x') |
| brand_id | VARCHAR(50) nullable |
| decision_type | VARCHAR(60) - staly typ (np. 'topic_swap', 'mode_transition') - po nim liczy sie nauka |
| question / options / recommendation / context | TEXT / JSONB [{key,label}] / VARCHAR(40) / JSONB |
| status | CHECK: pending / answered / auto / expired |
| answer / answered_at / tg_message_id | VARCHAR(40) / TIMESTAMPTZ / BIGINT |

Kazda odpowiedz -> agent_learning_log (accepted gdy zgodna z rekomendacja, inaczej replaced).

## decision_modes (DDL 024)
Tryb per (subagent_id, decision_type) PK: supervised / semi_autonomous. Przejscie proponuje
system po >=10 odpowiedziach i >=80% zgodnosci w ostatnich 20 (propozycja = decyzja
mode_transition, ten sam mechanizm guzikow); zmiana trybu = zawsze tapniecie Tomasza.
Semi-auto NIE obejmuje zatwierdzania tresci do publikacji (kanon: niezatwierdzone nigdy samo).

## x_post_metric_snapshots (DDL 025, build kolektora metryk X 19/07/2026)
Dzienne snapshoty metryk WLASNYCH postow X z GET /2/users/{id}/tweets (Owned Reads
$0.001/read, OAuth1 user context). Zbiera app/x_collector.py (tick w petli workera,
raz na dobe UTC, guard durable po MAX(snapshot_date)). Prywatne metryki tylko <30 dni -
snapshot utrwala je zanim znikna z API.

| kolumna | typ |
|---|---|
| id | BIGSERIAL PK |
| brand_id / channel | VARCHAR(50) / VARCHAR(40) default 'x' |
| tweet_id | VARCHAR(30); UNIQUE (tweet_id, snapshot_date) - idempotencja doby |
| snapshot_date | DATE default dzien UTC |
| observed_at | TIMESTAMPTZ default NOW() |
| created_at_x | TIMESTAMPTZ (created_at posta z API) |
| public_metrics / non_public_metrics / organic_metrics | JSONB (namespaces API 1:1) |
| raw | JSONB (caly obiekt tweeta z odpowiedzi) |

Indeksy: idx_xpms_tweet (tweet_id, snapshot_date DESC), idx_xpms_brand_date (brand_id,
snapshot_date DESC). Konsument: reports.refresh_metrics (stats_mode 'x_owned_reads') -
czyta NAJNOWSZY snapshot per tweet_id i merguje do published_posts.engagement_metrics
(match post_id=tweet_id, source 'x_api', ZERO odczytow platnych przy raportach).
Followers dziennie: GET /2/users/me -> channel_metrics_daily (source 'x_api').
Wlaczenie celu = UPDATE channels.config.stats_mode (SQL w naglowku 025) PO sondzie.

## contacts + engagement_log - CRM relacji (DDL 026, BE-ENGAGEMENT 20/07/2026)

Baza contacts istnieje od 001 (31/05, 45 osob z migracji #71); DDL 026 dodaje warstwe
relacyjna comment-radaru (komponent: docs/komponenty/engagement-crm.md).

contacts - kolumny dodane/zmienione w 026:

| kolumna | typ | uwagi |
|---|---|---|
| handles | JSONB NOT NULL default '{}' | jedna osoba, wiele kont: {"x": "handle", "linkedin": "slug"}; pas bezpieczenstwa IF NOT EXISTS (audyt 04/07 widzial ta kolumne) |
| relationship_stage | VARCHAR(20) NOT NULL default 'cold' | CHECK (skala zatwierdzona guzikami 20/07): cold/commented/replied/dm/offer/client liniowo (bump TYLKO W PRZOD, crm.bump_stage) + 'ghosted' stan boczny (ozywienie = bump jak z cold) |
| icp_tier | (istniejaca) | CHECK poszerzony: Buyer/Peer/Competitor/Partner (doktryna #71) + legacy Premium/Mid/Free/Watch/N/A (45 zywych wierszy) |

engagement_log - kolumny dodane w 026:

| kolumna | typ | uwagi |
|---|---|---|
| contact_id | UUID FK contacts | istnieje od 001 - 026 to pas bezpieczenstwa; od 20/07 FAKTYCZNIE wypelniane (CRM obowiazkowy) |
| status | VARCHAR(20) NOT NULL default 'logged' | CHECK: logged/proposed/approved/rejected/sent/skipped - cykl zycia propozycji komentarza (koniec decyzji tylko w notes) |
| author_display | VARCHAR(200) | autor ze zrzutu jawnie (dotad ginal w notes 'od: X') |

Indeksy: idx_engagement_contact_id, idx_engagement_status_open (partial: proposed/approved).
UWAGA dlug: contacts ma ZDUBLOWANE kolumny (name/full_name, icp_tier/tier, pain_point/
pain_points...) - konsolidacja PRZED pelnym agentem CRM to osobna decyzja (audyt 04/07 pkt 3),
026 celowo jej NIE dotyka.

## TODO (rozszerzenie dokumentacji schematu)
Pełny `pg_dump --schema-only` do zrzucenia i dopisania tu dla POZOSTAŁYCH tabel bazowych
(post_queue, task_queue, published_posts, contacts, engagement_log, inspirations, channels,
content_items, user_agent_state, app_secrets, agent_messages, agent_logs...). Priorytet: te,
które app zapisuje/czyta bez DDL w repo. Zrzut nie zmieścił się w jednym wklejeniu - do zrobienia
plikowo przy następnej okazji SSH (wariant: pg_dump do pliku w repo na Mikrusie + commit stamtąd).
