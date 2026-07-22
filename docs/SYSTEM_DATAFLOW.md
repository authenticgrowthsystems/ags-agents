# AGS System - mapa przeplywu danych + indeks komponentow

**Status:** ZYWY dokument = MAPA + INDEKS (reforma 20/07/2026, kanon DOKUMENTACJA
ZYJE - PROTOKOL_SESJI pkt 6). Szczegoly kazdego komponentu mieszkaja w
`docs/komponenty/` (staly szablon, stan obecny). Historia i sekcje datowane:
`docs/archiwum-dataflow.md` + raporty `docs/cm/` + git log.
**Zasada nadrzedna:** jedno zrodlo prawdy = PostgreSQL `ags_crd`. Notion =
lustro dla czlowieka. Sekrety TYLKO `app_secrets`. n8n = TYLKO transport.

## 1. Architektura (kto gdzie mieszka)

```
Tomasz (Telegram @ags_social_bot + bot #2 logowy)
   |
n8n (Mikrus, transport): HITL U5pUZjy2yAhR1sWg (router komend/callbackow),
   publishery subagentow (X, LinkedIn), Scheduler (co min), crony raportow
   08:00/nd 20:00/nd 20:15, drift 03:00, backup 03:30, adaptery Researchera
   |                                   |
cm-agent (kontener Python :8089)    ags-researcher (kontener Python)
   petla workera + FastAPI             petla workera + FastAPI /request
   /message /matnav /plannav /cmt      kaskada 5 zrodel -> synteza
   /decnav /docmsg /metrics/xlsx       claims + options + koszty
   /wake /request /plan /reports
   |                                   |
PostgreSQL ags_crd (pg_n8n) - KREGOSLUP ZAPISU (wszystkie tabele)
Notion - read-only mirror (sync worker w cm-agent; wyjatek: brand_tokens
   Notion->PG)
```

Komunikacja agent<->agent: EVENT-DRIVEN (POST /wake, POST /request,
X-Researcher-Secret); poll 30s i crony = tylko backstop/rutyny.
Deploy: push (Tomasz) -> SSH pull -> ew. psql db/0NN -> docker build/run ->
/health. Szablony komend: masterprompt sekcja 8.

## 2. Glowny przeplyw tresci (od pomyslu do metryki)

```
POMYSL: rozmowa CM / Idea Bot / schowek (inspirations)      [rozmowa-cm]
   v
PLAN TYGODNIA: planner + bramka tematow + cap 20 ->
   content_items 'proposed' -> przeglad guzikami -> approve  [planner]
   v
GENERACJA: canonical (voice z brand_config) -> compliance ->
   dedup embedding (⚠️ informuje) -> warianty per kanal ->
   auto-grafika -> post_queue 'review'                       [dedup, grafika]
   v
DECYZJA TOMASZA: karty matreview + wiadomosc approval
   (edycja = akceptacja + nauka; kazda decyzja -> learning)  [karty-hitl]
   v
PUBLIKACJA: approved + slot (humanize +/-15 min) -> dispatch
   per publish_mode (webhook subagent / Scheduler / held) ->
   published_posts; ZATWIERDZONE ZAWSZE, NIEZATWIERDZONE
   NIGDY SAMO                                                [kolejka-publikacja]
   v
METRYKI: kolektor X Owned Reads (dobowy snapshot) + import
   LinkedIn xlsx -> channel_metrics_daily -> raporty PROFIL  [metryki]
   v
NAUKA: agent_learning_log + decyzje guzikami (semi-auto
   zarabiane odpowiedziami) + content_memory (pgvector)      [decyzje-nauka]
```

Rownolegle: Researcher na zadanie (POST /request) + sobotni podklad
"CM czyta swiat" pod reczny niedzielny artykul [researcher]; sync mirror
DB->Notion [sync-notion]; caly transport i zasady zmian n8n [n8n-transport];
Lacznik = praca reczna Tomasza w czacie na abonamencie <-> baza (RAPORT PRACY,
stan gry; Etap 2 = narzedzia MCP w n8n, czat czyta i raportuje SAM) [lacznik].

## 3. Indeks komponentow (CZYTAJ ZAMIAST KODU)

| Komponent | Plik | W srodku |
|---|---|---|
| Planner | [komponenty/planner.md](komponenty/planner.md) | plan tygodnia, bramka tematow, cap 20, gap-filler, plannav |
| Kolejka i publikacja | [komponenty/kolejka-publikacja.md](komponenty/kolejka-publikacja.md) | post_queue, sloty, humanize_slot, serie X, Scheduler, kanon publikacji, stale_approval |
| Karty + approval | [komponenty/karty-hitl.md](komponenty/karty-hitl.md) | karty matreview, guziki, media, fulltext, edycja=nauka, approval hitl |
| Decyzje + nauka | [komponenty/decyzje-nauka.md](komponenty/decyzje-nauka.md) | agent_decisions, decision_modes, dec:, progi semi-auto, learning_log |
| Metryki | [komponenty/metryki.md](komponenty/metryki.md) | kolektor X Owned Reads, import xlsx LinkedIn, channel_metrics_daily, PROFIL |
| Dedup | [komponenty/dedup.md](komponenty/dedup.md) | dup_check na master_theme, prog cm_dup_threshold 0.57, ⚠️ w kartach i approval |
| Rozmowa CM/subagenci | [komponenty/rozmowa-cm.md](komponenty/rozmowa-cm.md) | route deterministyczne, narzedzia, pamiec 3 warstwy, subagent=ten sam kod |
| Engagement-CRM | [komponenty/engagement-crm.md](komponenty/engagement-crm.md) | comment-radar per autor, contacts+stadium relacji, intake nieznanych, przypomnienia 24h, album=1 post |
| Researcher | [komponenty/researcher.md](komponenty/researcher.md) | kaskada 5 zrodel, kontrakt /request, bramki critical/model, sunday brief |
| Grafika | [komponenty/grafika.md](komponenty/grafika.md) | gpt-image-2, prompt Sonneta, brand_tokens/visual_canon, kanon mediow |
| Sync Notion | [komponenty/sync-notion.md](komponenty/sync-notion.md) | mirror DB->Notion, sync_registry/page_map, drift check |
| n8n transport | [komponenty/n8n-transport.md](komponenty/n8n-transport.md) | HITL galezie, publishery, crony, zasady PUT, patchery |
| Agent Sprzedazy | [komponenty/agent-sprzedazy.md](komponenty/agent-sprzedazy.md) | /prospect research critical, outreach gotowce HITL, lejek sales_pipeline, sales_knowledge z embeddingami |
| Lacznik | [komponenty/lacznik.md](komponenty/lacznik.md) | RAPORT PRACY (parser bez LLM), /kontekst, strona Notion Stan gry, masterprompty czatowe; Etap 2: narzedzia MCP stan_gry + wyslij_raport_pracy (workflow yxJUJmZpSUe0tw9K, endpointy /lacznik/*) |

Schemat tabel: `docs/db/SCHEMA_ags_crd.md` (tabele bazowe + kazda zmiana DDL)
+ masterprompt sekcja 2b (slowniczek najwazniejszych tabel). Migracje:
`cm-agent/db/0NN_*.sql`. Diagram Researchera: `docs/researcher-dataflow.svg`.

## 4. Stan i legacy (skrot)

- LIVE: caly przeplyw z sekcji 2 (multi-brand AGS/TNM/RDC active), kolektor X
  (od 20/07), dedup (skalibrowany), sync mirror v1 (brand_config +
  manager_daily_log).
- AWARIA w naprawie: adapter web_search Researchera (fix na
  build/researcher-fix, czeka rebuild - szczegoly researcher.md).
- LEGACY OFF: stary AGS X Agent (kolejka Notion, cron 14/18/22) wylaczony
  od 25/06 - opis w archiwum-dataflow.md sekcje B.
- ZAMROZONE (nie odmrazac bez decyzji Tomasza): Agent Wizualny, App 2 CMA,
  strony firmowe LinkedIn, standalone subagenci.

## 5. Do udokumentowania dalej

- [ ] Diagram graficzny CALOSCI (pipeline + Researcher + siec agentow) -
      czesc pakietu sprzedazowego, renderowany gdy build skonczony.
- [ ] pg_dump schema-only pozostalych tabel bazowych do SCHEMA_ags_crd.md
      (TODO z SCHEMA).
