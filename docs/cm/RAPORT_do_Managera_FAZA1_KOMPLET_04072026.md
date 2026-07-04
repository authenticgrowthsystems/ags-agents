# RAPORT KOŃCOWY FAZY 1 MÓZGU CM - od BE do Managera AGS

**Data:** 04/07/2026
**Od:** Build Engineer (Claude Code, Fable 5)
**Do:** Manager AGS Cowork (Opus 4.7)
**Temat:** Faza 1 wg CM_BRAIN_DESIGN_v2 = KOMPLET Z PEŁNYM E2E. Wniosek o review canonical.
**WAŻNE - status Bramy 3:** Tomasz WSTRZYMUJE zatwierdzenie Bramy 3 do czasu **jasnej ścieżki wdrożenia
u osoby trzeciej** (model ma być sprzedawalny). Szczegóły w sekcji 6.

## 1. Wykonanie sekwencji (7 kroków + rollback, raport po każdym - precedens 03/07 dotrzymany)

| Krok | Zakres | Commit | E2E |
|---|---|---|---|
| Rollback R1 | Idea Bot przywrócony jako default | (n8n) | PASSED (triage działa jak przed 03/07) |
| 1b | Router active_agent + menu /agents + agsel: + setMyCommands per czat | 4b34826 | PASSED (menu, przełączanie, routing; po hotfixie AP-301) |
| 1c | Rozmowa CM za menu: Opus 4.8 (live tier), save_to_schowek, kontekst archiwum | 4b34826 | PASSED (schowek, /plan, dyskusja) |
| 1d | Rozmowa subagentów per konto: kolejka #id, remove/reschedule, ad-hoc przez approve, raport na żądanie, historia per agent | 319729b | PASSED (kolejka + raport u AGS x) |
| 1e | cm_tasks + router tierów R4 + guziki 🎚 cmtier: + approval-learning do agent_approval_gates | 318ad35 | LIVE (gałąź zweryfikowana; korekta E2E przy najbliższym materiale) |
| 1f | content_memory: pgvector + embeddingi OpenAI, show_archive/find_similar/adapt, hook nowego kanału | bdf220a | PASSED (show_archive zwrócił archiwum) |
| 1g | Raporty daily/weekly + AUTONOMOUS_DECISION + kolektor metryk (stats_mode) + manual entry X + cron | 837db11 | PASSED (2 raporty dzienne DOTARŁY na bota #2, 04/07 09:31) |
| 1h | R6: language_comm (brand_config) + language_publish per cel + seed | a8899f3 | LIVE (mechanizm; PL cel dojdzie z App 2) |

DDL zaaplikowane przez Tomasza: db/003..007 (user_agent_state, processed_updates, cm_tasks, agent_logs,
kolumny published_posts + embedding, tabele raportów, język). Cron: workflow `CM Reports Cron` ERweY5vHomrpw1SC ACTIVE.
HITL: 224 węzły (rodziny agsel: + cmtier: dopisane, stare gałęzie nietknięte).

## 2. Decyzje Managera z Bramy 2 - wykonanie
1. agent_logs = JEDNA generyczna tabela z agent_id + indeks - WDROŻONE.
2. Metryki docs-first - WYKONANE Z ODCHYLENIEM: job Researchera 728d02ba FAILED (bug syntezy: pole listowe
   jako string). Bug naprawiony TRWALE (coerce validator, cf433dd, test regresji PASSED, wdrożony).
   Fakty wzięte bezpośrednio z oficjalnych docs Microsoft Learn (pełniejsze niż job):
   `docs/research/LINKEDIN_STATISTICS_API_2026.md` + memory reference. Retry joba zaniechany (szkoda 0.6 PLN
   przy faktach już zdobytych). DDL raportów wykonany PO faktach, zgodnie z intencją decyzji.
3. pgvector 0.8.2 - find_similar pełny (embeddingi: OpenAI text-embedding-3-small, klucz JUŻ był w app_secrets).
4. Runtime rozmów subagentów = host w cm-agent - WDROŻONE (kontrakt /message wspólny, wydzielenie przy standalone).
5. Godziny raportów 08:00 / nd 20:00 Europe/Warsaw - WDROŻONE w cronie.
Plus R6 (uzupełnienie Tomasza po E2E): język komunikacji ODDZIELNIE od języka publikacji per cel - WDROŻONE.

## 3. Incydenty i lekcje (wszystkie zdiagnozowane Z DOWODU, nie zgadywaniem)
- **AP-301** (nowy wpis anti-patterns): dwa IF-y postawione z typeVersion 1 + nowym formatem warunków = zawsze TRUE
  (okno awarii guzików bez szkód). Diagnoza z egzekucji 39398 node-by-node; naprawa na 2.2 wzorcem działających bramek.
- **AP-302:** "zanadrze" w komunikacji bota bez potwierdzenia rejestru marki -> globalna zamiana na "schowek".
- **log_bot_token wklejony Z NAWIASAMI OSTRYMI placeholdera** (48 znaków, kształt zły, sendMessage "Not Found") -
  diagnoza read-only po KSZTAŁCIE wartości (bez ujawnienia), fix btrim. Lekcja: placeholdery w DDL bez `<>`.
- **Researcher ResearchOutput:** tool-forced output czasem stringifikuje listy - trwały coerce validator.
- **Luka archiwum:** callbacki subagentów nie pisały published_posts - załatane ZA ZGODĄ Tomasza (klasyfikator
  słusznie wymusił osobną zgodę; zmiana idempotentna z backupami).

## 4. Koszty i kontrola
Ledger `cm_tasks` liczy każdy call LLM (tier, model, tokeny, koszt USD, źródło tieru auto/config/override).
Korekty Tomasza (🎚) trafiają do agent_approval_gates type 'model_selection' - materiał pod przyszłą
auto-automatyzację po ~20-30 korektach (parking zgodnie z Sekcją 4 korekty).

## 5. Otwarte (bez zmian statusu, poza głównym nurtem)
Kosmetyka tekstu HITL po approve; rotacja tokena Telegram (hardkody w starych węzłach); linkedin_client_secret
błędny (token z Token Generatora, wygasa ~01/09/2026); pełne i18n stałych komunikatów; metryki LinkedIn po App 2;
cost-reconcile DR/Manus; głos/foto binaryMode re-test.

## 6. WARUNEK TOMASZA DLA BRAMY 3 (04/07) - do zaplanowania PRZED acceptance
Tomasz: model ma być SPRZEDAWALNY, więc przed zatwierdzeniem potrzebna **jasna ścieżka implementacji u osoby
trzeciej**. Proponowany zakres pakietu (BE przygotuje po review Managera):
1. **Playbook instalacji u klienta** - aktualizacja istniejącego `DEPLOY_CHECKLIST.md` (jest sprzed mózgu CM)
   o: kontener cm-agent, DDL 001-007 jako jeden bootstrap, import workflowów n8n (HITL + 2 publishery + Scheduler
   + Reports Cron) z podmianą credentiali, seed brand_config/channels per klient (język, cele, stats_mode),
   onboarding sekretów (app_secrets - bez ręcznego SQL), rejestracja botów Telegram (główny + logowy).
2. **Diagram graficzny przepływu danych** całego systemu (wymóg documentation requirement; wzór: researcher-dataflow.svg).
3. **SYSTEM_DATAFLOW.md sekcja E** - zaktualizowana do stanu końcowego Fazy 1 (ZROBIONE w tym commicie).
Sekwencyjnie zderzyć z Fazą 2 (planer) - rekomendacja BE: playbook + diagram PRZED Fazą 2, bo Faza 2 doda
kolejne elementy do udokumentowania, a warunek Bramy 3 blokuje formalne domknięcie Fazy 1.

## 7. Linki
Raporty kroków: `docs/cm/RAPORT_do_Managera_Faza1_{rollbackR1,1b,1c,1d,1e,1f,1g,1h}_*.md`
Design: `docs/cm/CM_BRAIN_DESIGN_v2.md` | Przepływ: `docs/SYSTEM_DATAFLOW.md` (sekcja E)
Fakty API: `docs/research/LINKEDIN_STATISTICS_API_2026.md` | Anti-patterns: AP-301, AP-302
Commity: 4b34826, 319729b, e458454, 318ad35, bdf220a, cf433dd, f004bb2, 837db11, a8899f3, ca92b36 (+ ten raport)

**Next:** Manager review -> rekomendacja dla Tomasza co do zakresu pakietu sprzedawalności (sekcja 6) ->
BE buduje playbook + diagram -> Brama 3 -> Faza 2 (planer).

---

## 8. ADDENDUM (Tomasz 04/07, do mapy działań Managera - "niech o tym wszystkim pamięta")

**8.1 BAZA DANYCH = NAJWYŻSZY PRIORYTET ARCHITEKTONICZNY (kanon).** Tomasz: dobrze zbudowane relacje =
zero duplikacji danych + DOWOLNY interfejs (Telegram/web/mobile/Slack) czyta te same, aktualne dane; zmiana
w jednym miejscu widoczna dla wszystkich. BE wykonał pełny audyt stanu faktycznego:
`docs/db/DB_AUDIT_04072026.md` (32 tabele, 18 FK, diagram relacji mermaid, mocne strony + 5 słabości).
Kluczowe znaleziska: (a) rdzeń CM i Researcher w pełni relacyjne; (b) ZERWANA relacja schowek->produkcja
(inspiration_id uuid vs bigint - FK fizycznie niemożliwy); (c) brand/platform jako luzny tekst bez FK
w post_queue/published_posts; (d) contacts ma zdublowane kolumny (ślad sklejenia dwóch projektów 31/05).
Pakiet naprawczy przygotowany: `cm-agent/db/008_relations_fix.sql` (czeka na decyzję Tomasza).

**8.2 CRM / OBSŁUGA OSÓB ("model Marty") - wizja Tomasza POTWIERDZONA W SCHEMACIE.** Warstwa danych JUŻ
istnieje (build 31/05, 0 wierszy): `contacts` (40 pól: narracja, icp_tier, pain_points, next_action+owner,
handles per platforma, intent_signals) + `engagement_log` (contact_id FK: action_type/channel/agent/content/
response/metrics = "Marta zareagowała na post X komentarzem Y") + `task_queue.contact_id` (follow-upy) +
`published_posts.contact_id`. Tomasz: to będzie NASZA SIŁA (do tych ludzi możemy pisać; kanałów będzie dużo).
Właściciele per Blueprint v1.3: **Opiekun Relacji** (Business Manager) + **Sprzedawca**; intake: Sekretarka.
DO MAPY: Brama 1 (research) dla warstwy CRM/Opiekuna Relacji + konsolidacja zdublowanych kolumn contacts
PRZED pierwszym agentem CRM (dziś tanio - 0 wierszy).

**8.3 BACKUP / RETENCJA / ARCHIWIZACJA - dziś BRAK BACKUPU = najwyższe ryzyko operacyjne.** Propozycja BE
w audycie sekcja 4: pg_dump dzienny (cron na Mikrusie, rotacja 7 dni) + kopia tygodniowa POZA serwer;
retencja tylko logów technicznych (agent_messages read >30d, n8n executions max age), tabele biznesowe
nieczyszczone bez decyzji Tomasza. DO MAPY jako P1 (przed sprzedażą obowiązkowe: klient zapyta o backupy).

**8.4 NOTION - masa danych i inspiracji.** Przypomnienie: migracja Notion->Postgres = decyzja D4 z Bramy 2
(PO MVP, shadow-sync -> parity -> cutover per consumer). Nic nie ginie, X-agent czyta Notion jak dotąd.
DO MAPY jako zaplanowany krok, nie zapomniany.

**8.5 OBSIDIAN - dyrektywa Tomasza dla Managera AGS Cowork.** Tomasz chce wgrać do Obsidiana WSZYSTKIE
dotychczasowe konwersacje (ChatGPT + Claude), by nie uciekła żadna myśl. Prośba: Manager prowadzi Tomasza
ZA RĘKĘ (krok po kroku) przez eksport rozmów i przygotowanie przystępnych plików do Obsidiana.
Wpływ na system serwerowy: ZERO zmian w agentach - kanon (decyzja z Bramy 1 CM): Obsidian = mózg STRATEGICZNY
Managera; przepływ JEDNOKIERUNKOWY Obsidian -> Manager destyluje -> brand_config/brand_strategy w Postgres ->
CM czyta projekcję. Agenci serwerowi nigdy nie czytają Obsidiana. Mózg CM jest już na to gotowy
(czyta brand_strategy/brand_config live).

**8.6 TRYBY PRACY SUBAGENTA (wymóg Tomasza, do kontraktu konfiguracji).** Każdy, nawet najmniejszy subagent:
własne ustawienia zmienialne ręcznie + tryb pracy: **autonomiczny / półautonomiczny / automatyczny**
(mechaniczna kolejka wg algorytmu). Stan: fundament jest (channels.config per cel + supervised toggle +
autonomia z logiem), brakuje JAWNEGO pola `work_mode` w kontrakcie config. DO MAPY: dopisać do kontraktu
konfiguracji subagenta (tani krok przy Fazie 2).

**8.7a ZARZĄDZANIE MODUŁAMI Z POZIOMU UŻYTKOWNIKA (Tomasz 04/07, DO MAPY).** Użytkownik musi WIDZIEĆ,
które agenty/cele są włączone, móc je włączać/wyłączać z czatu, a przy włączeniu: nowa konfiguracja ALBO
użycie zapisanej + modyfikacja. Skala: sam Tomasz ma 3 cele na LinkedIn (strona AGS, profil prywatny, RDC);
klient może mieć znacznie więcej. Warstwa danych JUŻ istnieje (channels: status active/paused + supervised +
config per cel) - brakuje UI: lista celów z toggle ON/OFF + kreator konfiguracji w Telegramie.
Rekomendacja BE: wpiąć w zakres Fazy 2 (planer i tak dotyka channels.config) jako krok "zarządzanie celami".

**8.7 DIAGRAMY WIZUALNE.** Tomasz: grafy wizualne (co skąd dokąd przechodzi) są dla niego kluczowe -
świadomie odłożone, ale KANONICZNE (documentation requirement: graficzny diagram przepływu danych jako
element pakietu sprzedawalności, razem z playbookiem z sekcji 6).
