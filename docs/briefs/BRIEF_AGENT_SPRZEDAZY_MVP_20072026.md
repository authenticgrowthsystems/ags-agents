# BRIEF BUILDU: AGENT SPRZEDAZY MVP Level 1 (20072026) - budowniczy: BE-SPRZEDAWCA

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md zbuduj`
CZYTAJ NAJPIERW: docs/komponenty/rozmowa-cm.md + researcher.md + docs/GOTOWOSC_PRODUKTU.md +
C:\Claude-CoWork\AGS\BE_BRIEF_AGENT_SPRZEDAZY_MVP_20072026.md (brief Managera = zrodlo wymagan).

## 0. Tryb rownolegly + PRIORYTET

KRYZYS FINANSOWY TOMASZA = sprzedaz dzis/jutro rano LIVE. Zero dat, zero faz.
Worktree+galaz `build/sprzedawca` od origin/claude/silly-blackwell-dfc32d (wzorzec sekcji 0
briefow 19/07; NIE sb-work). DDL jako plik db/027 (026 zajete przez engagement-crm!).
WYJATEK n8n (waski): wolno dopisac NOWE komendy do przepustki Detect Update Type
(patcher z backupem + deactivate/activate; HITL poza ta lista NIETYKALNY).
Zakaz deployu - merge+deploy robi BE/integrator (zglos DONE natychmiast, deploy pojdzie
tego samego wieczora).

## 1. CO budujemy (Level 1 wg sekcji 2.2 briefu Managera)

Agent Sprzedazy = NOWY agent w istniejacym frameworku subagentow (agent_registry +
user_agent_state.active_agent; przelacznik /agents juz dziala). Rozmowny partner
strategiczny + operacyjny wykonawca. Konkretnie:

1. **Tozsamosc i wiedza**: nowy agent 'sprzedawca' (brand AGS) z wlasnym promptem:
   zna GOTOWOSC_PRODUKTU.md (co wolno sprzedawac!), pricing_tiers (10 tierow, w tym
   parking_active Pakiety PL 1-3 z abonamentem narzedzia $97-297/mc - TOP OFFERING dla
   malych firm PL), sales_playbook (6 wpisow), icp_definitions, Voice Bible + kanon
   walutowy (AGS=USD, TNM/PL=PLN). ZASADA: narzedzia (GHL) NIE ujawniamy - sprzedajemy
   REZULTAT ("system retencji klientow"). NIE odwoluj sie do /apply (doktryna).
2. **Narzedzia agenta** (petla agentowa jak subagent X):
   - prospect_research(url/nazwa) -> zlecenie Researcherowi (kontrakt /request, tier
     critical dla prospektow - Manus w kaskadzie; wynik: kim sa, sygnaly buyer, problemy
     ktore AGS rozwiazuje) + firecrawl przez Researcher;
   - draft_outreach(prospect, tier) -> personalizowany email/DM w Voice Bible (kanon:
     karta z czysta wklejka jak comment-radar; NIC nie wysyla sie samo - HITL);
   - offer_for(prospect) -> dopasowanie tieru z pricing_tiers + uzasadnienie;
   - pipeline: NOWA tabela sales_pipeline (DDL 027: contact_id FK->contacts, stage CHECK
     prospect/qualified/proposal/negotiation/won/lost, next_followup_at, value, currency,
     notes, updated_at) + narzedzia pipeline_view/pipeline_move (paragony!);
   - sales_knowledge (DDL 027, wg sekcji 2.3 briefu Managera: material_type, content_excerpt,
     source_url, embedding pgvector, tags) + wrzucanie przez ISTNIEJACA galaz document_text
     (tryb /add_sales_material analogiczny do madd: nastepny dokument/tekst -> parse ->
     embed -> INSERT) + semantic search przy outreach.
3. **Komendy** (przepustka n8n): /prospect, /oferta, /pipeline, /add_sales_material -
   route deterministyczny (wzorzec _USTAW_OKNO_RE), reszta = naturalna rozmowa.
4. **Anthropic sales skills**: ZAINSTALOWANE w Cowork (sales:draft-outreach, account-research,
   call-prep, pipeline-review, forecast, competitive-intelligence). Otworz je (Skill tool)
   i DESTYLUJ ich frameworki do promptu systemowego sprzedawcy (embedded, server-side nie
   ma Skill toola). Board of Advisers/NotebookLM = warstwa Tomasza, nie ten build.

DoD (tap-testy z Tomaszem): /agents pokazuje Sprzedawce; /prospect <url> -> research ->
podsumowanie z sygnalami buyer; draft outreach -> karta z czysta wklejka; /pipeline pokazuje
lejek; dokument PDF/tekst -> sales_knowledge z embeddingiem; SCHEMA+komponent
docs/komponenty/agent-sprzedazy.md + macierz gotowosci W TYM SAMYM COMMICIE.

## 3. Czego NIE dotykac
Publikacja/planner/dedup/engagement-crm (rownolegly build na conversation.py - DOTYKAJ
conversation.py TYLKO w sekcjach subagenta/sprzedawcy, dispatch toolow dodawaj na koncu
funkcji; konflikty zlozy integrator). Zadnego auto-wysylania czegokolwiek (HITL zawsze).

## 5. Udzial Tomasza
psql 027 + rebuild (w paczce wieczornej), tap-testy, decyzja guzikami gdy niejasna skala/tier.

## 6. Zamkniecie: raport + komponent + macierz + STATUS tu.

STATUS = ZBUDOWANE (BE-SPRZEDAWCA, 20/07 wieczor) - galaz build/sprzedawca, kod
skompilowany; czeka paczka integratora: merge -> psql 027 PRZED rebuildem -> rebuild
cm-agent (pypdf!) -> patch n8n hitl-sales-commands -> tap-testy DoD. Raport:
docs/cm/RAPORT_do_Managera_20072026_agent_sprzedazy.md; komponent:
docs/komponenty/agent-sprzedazy.md.
