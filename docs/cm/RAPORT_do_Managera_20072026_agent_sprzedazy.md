# RAPORT do Managera AGS: Agent Sprzedazy MVP Level 1 ZBUDOWANY (BE-SPRZEDAWCA, 20/07/2026)

Brief: docs/briefs/BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md (zrodlo wymagan: Twoj
BE_BRIEF_AGENT_SPRZEDAZY_MVP_20072026 sekcja 2.2 Level 1). Galaz: build/sprzedawca
(od f2ac056). Status: KOD GOTOWY + skompilowany; czeka paczka integracyjna.

## Co powstalo

1. **Tozsamosc i wiedza** (cm-agent/app/sales.py): prompt systemowy z ZYWYMI danymi z bazy
   (pricing_tiers 10 tierow z oznaczonym TOP OFFERING = Pakiety PL 1-3 DFY, sales_playbook,
   icp_definitions, Voice Bible, lejek, baza wiedzy) + destylat macierzy GOTOWOSC_PRODUKTU
   + twarde zasady: GHL NIE pada w komunikacji (sprzedajemy "system retencji klientow"),
   zero /apply, kanon walutowy, REGULA PRAWDY (Stage 0-1 = zero zmyslonych referencji),
   HITL zawsze, cennik od gory. Frameworki Anthropic sales skills zdestylowane do promptu
   (draft-outreach otwarty Skill toolem: hierarchia hookow, struktura maila, zakazy,
   sekwencja follow-up 3/7/14; account-research: sygnaly kupna; pipeline-review: higiena).
2. **Narzedzia (9, petla agentowa 5 krokow jak CM)**: prospect_research (Researcher
   /request, from='sales-agent', default CRITICAL - pelna kaskada z Manus; wpis w
   agent_registry z 'critical' w DDL 027), prospect_results, draft_outreach (gotowiec
   HITL: naglowek + czysta wklejka osobna wiadomoscia, wzorzec comment-radar; zapis
   engagement_log 'proposed'), offer_for, pipeline_view/add/move (paragony 📊),
   sales_knowledge_search (pgvector + fallback ILIKE), outreach_sent.
3. **Lejek + wiedza (DDL 027)**: sales_pipeline (stage CHECK prospect->won/lost,
   next_followup_at z higiena ⚠️, notes z timestampami) + sales_knowledge (chunki ~2000
   znakow, embedding text-embedding-3-small 1536). Wyniki researchu wracaja ASYNC:
   sales.tick w petli workera -> synteza Sonnetem (KIM SA / SYGNALY KUPNA / PROBLEMY /
   HAK / TIER) -> Telegram + notatka lejka.
4. **Komendy** (deterministycznie PRZED LLM, wzorzec _config_route): /prospect /oferta
   /pipeline /add_sales_material (uzbrojenie 2h: dokument .md/.txt/.pdf albo wklejka
   -> chunk -> embed -> sales_knowledge). Patch przepustki Detect Update Type:
   n8n-workflows/patches/hitl-sales-commands-20072026.cjs (komendy + .pdf<=8MB;
   JEDEN wezel, backup + deactivate/activate; reszta HITL nietknieta).
5. **Wpiecie w /agents BEZ ruszania menu n8n**: menu buduje sie dynamicznie z channels
   - DDL 027 dodaje wiersz (AGS,'sprzedaz','draft',supervised, agent_kind='sales');
   guardy w planner/reports/proactive/_channels_snapshot wykluczaja agent_kind='sales'
   (zero wplywu na plan tygodnia i raporty).

## Poza zakresem L1 (Level 2, wg Twojego briefu)
Gmail/hello@ (MCP Gmail w Cowork = obsluga reczna od zaraz), follow-up automation,
dashboard metryk, mirror sales_knowledge do Notion, semi-auto wysylka (Level 3).

## Wdrozenie (paczka integratora, kolejnosc twarda)
1. merge build/sprzedawca -> sb-work; 2. psql db/027 PRZED rebuildem; 3. rebuild
cm-agent (nowa zaleznosc pypdf w requirements!); 4. node patch hitl-sales-commands;
5. tap-testy DoD: /agents pokazuje "AGS sprzedaz"; /prospect <url> -> paragon zlecenia
-> (po ~10-20 min) synteza na Telegram; rozmowa "napisz outreach do X" -> gotowiec
czysta wklejka; /pipeline -> lejek; /add_sales_material + dokument -> paragon 📚
z liczba kawalkow i embeddingow.

## Ryzyka/decyzje dla Ciebie
- Koszt critical ~15-20 PLN/prospekt (ledger widzi); pierwszy prospekt = takze test
  naprawionego web_search w pelnej kaskadzie.
- Wiersz 'sprzedaz' widac w ⚙️ Cele - NIE aktywowac (opisane w komponencie i pulapkach).
- contacts nie linkuja sie automatycznie do prospektow-firm (CRM osobowy #71);
  swiadome ciecie L1, kolumna contact_id gotowa.
