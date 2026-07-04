# RAPORT #71 / FAZA A: foundation + sample - od BE do Managera AGS

**Data:** 04/07/2026. **Status: MAPPING APPROVED 10/10 + DDL GOTOWY + SAMPLE ETL GOTOWY (czeka SSH Tomasza + Twoja walidacja sample).**

## 1. Mapping approve (sekwencja pkt 2 kontraktu) - WYKONANE
Tomasz zatwierdził punkt-po-punkcie WSZYSTKIE 10 kategorii (guziki, 04/07), w tym 4 korekty techniczne BE
wynikające z audytu DB (docs/db/DB_AUDIT_04072026.md):
- K1: Story Bank -> inspirations.metadata.meta_type (kolumny meta_type w inspirations nie ma; jsonb jest);
- K2: `agent_contracts` NIE ISTNIEJE w bazie -> powstaje jako 17. nowa tabela (oversight_config + tool_guidelines);
- K4: content_items dostaje +meta_type TEXT + statusy 'draft'/'brief'/'archived' w CHECK (dzisiejszy constraint ich nie dopuszcza);
- K5: contacts MA JUŻ source/notes/last_interaction_date -> ALTER dodaje tylko pipeline_stage/brand_context/tags (+notion_page_id), ETL pisze w istniejące pola (zero duplikacji kolumn);
- K8-10: content_calendar nie istnieje -> Plan tygodniowy/Harmonogram do content_items 'proposed' (kalendarz = widok, decyzja D1).
- DODATKOWA korekta schematowa: brand_config to KLUCZ/WARTOŚĆ (wzorzec voice_bible) -> website_canon/footer_canon/ghl_config/sync_to_notion jako WIERSZE, nie kolumny (Twoja intencja zachowana, forma zgodna z istniejącym schematem).

## 2. DDL (pkt 3) - `cm-agent/db/010_notion_ssot.sql`
17 nowych tabel (Twoje 15+chat_registry+agent_contracts) + rozszerzenia contacts/content_items + seed
`sync_to_notion=true` dla AGS. Wszystko idempotentne, OWNER ags_crd_user, `notion_page_id` UNIQUE jako
kotwica idempotencji ETL; dla źródeł append-only (manager_daily_log/decisions/milestones) kotwica = `entry_hash`
(md5 treści wpisu), bo wiele wpisów dzieli jedną stronę Notion.

## 3. Sample ETL (pkt 4) - `etl/notion/phaseA_sample.sql` (7 INSERT, 3 źródła)
Metoda: Notion czytany read-only przez MCP (dostęp POTWIERDZONY), BE generuje deterministyczne SQL,
Tomasz aplikuje przez SSH - zero nowych sekretów, pełna rewizyjność każdego wiersza.
- **agent_blueprints** <- Blueprint v1.3: USTALENIE z fetchu - strona Notion to STRESZCZENIE wskazujące pełny
  plik workspace; do `content` weszła PEŁNA treść pliku (9.4KB) z notion_page_id strony jako kotwicą. Ta hybryda
  dotyczy też innych doktryn (sygnalizuję do decyzji przy Fazie B: content = plik pełny, mirror = strona Notion).
- **inspirations** <- Story Bank #1/#2/#10 (z pełnym metadata: pillar, sensitivity, key_quote; #10 zawiera
  KANONICZNĄ BIOGRAFIĘ - strona ma jej pełny blok, wejdzie w całości w Fazie B). Kotwice syntetyczne
  `page_id#sNN` (20 historii dzieli jedną stronę).
- **pricing_tiers** <- Cennik Lokalna Automatyzacja: 3 pakiety z cenami i features JSONB. UWAGA znaleziona
  przy fetchu: strona leży w kontenerze "ARCHIWUM - Analizy Q1" mimo statusu "AKTYWNY" - do Twojej weryfikacji
  czy to wersja canonical (drabinka AGS Premium = osobne źródło, dojdzie w Fazie D).

## 4. Docs-first (sekcja 11) - status
Notion MCP obsługuje paginację/limity po swojej stronie (fetch pełnych stron potwierdzony na 3 źródłach).
Pozostają do weryfikacji PRZED Fazą F (sync worker): Notion API update-mechanizm (block vs page), rate limit
tieru Tomasza, NOTIFY/LISTEN vs cron na 3GB RAM - zrobię przy projekcie workera (nie blokuje Faz B-E).

## 5. Do wykonania teraz
1. Tomasz: push + SSH: `010*.sql` (DDL) potem `etl/notion/phaseA_sample.sql` + wynik SELECT-a weryfikacyjnego.
2. Tomasz: weryfikacja 3 sample'i vs Notion (content match) - screenshot/OK.
3. Manager: review sample -> approve -> BE rusza Fazy B-E (pełny ETL per kategoria, raport z liczbami per źródło).

Timeline trzymany: dziś Faza A, jutro (05/07) start B per kontrakt.
