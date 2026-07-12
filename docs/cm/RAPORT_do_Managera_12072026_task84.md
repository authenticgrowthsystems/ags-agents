# RAPORT do Managera - 12/07/2026: Task #84 Visual Canon -> brand_tokens (Opcja C)

Od: BUILD ENGINEER | Status: strona PG + puller + konsument GOTOWE (kod); czeka DDL 019 +
rebuild + czesc Tomasza (baza Notion + wypelnienie + /set). Zbudowane w dniu briefu.

## Wykonane (zero zgadywania, jeden commit z DDL + SCHEMA per regula 08/07)

1. **db/019_brand_tokens.sql**: tabela per brief (brand_id PK FK->brands, tokens JSONB,
   updated_at, source) + wpis w docs/db/SCHEMA_ags_crd.md w tym samym commicie.
2. **Puller Notion->PG**: app/sync/brand_tokens_pull.py w ISTNIEJACYM workerze cm-agent
   (poll 10 min; parsowanie generyczne: KAZDA kolumna <BRAND>_Value -> marka, wiec RDC/LYSY
   dojda bez zmiany kodu; paginacja; nieznana marka = log i pomin). Konfiguracja bez deployu:
   `/set brand_tokens_notion_db <database_id>`.
3. **Konsument**: generate._visual_canon() - kolejnosc zrodel: brand_tokens (JSON W3C DTCG
   wklejany do promptu, "hexy litera w litere") -> brand_config visual_canon -> fallback
   w kodzie (AGS destylat; NOWY fallback TNM: ciepla zielen + terakota + krem wg SOP).
   Obejmuje WSZYSTKICH konsumentow grafiki (🎨 Generuj, auto-grafika, generate_material_image),
   bo wszyscy ida przez generate_image_prompt.

## ODSTEPSTWO od briefu (decyzja BE, do akceptacji Managera)

Brief zakladal workflow n8n (Notion Watch trigger). Wybralem puller w cm-agent, bo:
(a) notion_api_key JUZ jest w app_secrets (sync worker #71) - n8n wymagalby NOWEGO credentiala
Notion i drugiej Connection (AP-305 x2); (b) 'Watch' w n8n to i tak poll; (c) tokeny marki
zmieniaja sie rzadko - 10 min wystarcza; (d) mniej ruchomych czesci = mniej driftu.
Kierunek Opcji C (Notion SSOT -> PG -> agenci) bez zmian.

## Czesc Tomasza (odblokowuje LIVE)

1. SSH: DDL 019 + rebuild (komendy w czacie).
2. Notion: utworzyc baze "Brand Config" (kolumny: Token_Name [Title], Token_Type [Select:
   color/font/spacing/motyw/zakaz], AGS_Value [Text], TNM_Value [Text]) + **Connection
   integracji na bazie (AP-305!)** + wypelnic z Claude Design (hexy, fonty, motywy, zakazy).
3. Telegram: `/set brand_tokens_notion_db <database_id>` (id z URL bazy).
4. Tap: po <=10 min od wypelnienia 🎨 Generuj na dowolnym materiale AGS -> grafika z tokenow
   (dowod: docker logs '[brand_tokens] sync z Notion' + hexy w obrazie).

## Bonus w tej samej paczce

cf43715: paragon decyzji na kartach + BUG-FIX matnav ok/no/okq (rozpakowanie _card() do 2
wartosci wybuchalo PO zapisie statusu - stad 'kliknalem odrzuc i nic sie nie stalo').
