# Content Manager (CM) - BE Input dla Bramy 1 (research gate)

**Data:** 28/06/2026. **Autor:** AGS Build Engineer. **Cel:** kierunkowy kontekst techniczny, żeby Brama-1 research REQUEST Managera AGS do Researchera (model_tier=medium) był dobrze sprecyzowany.
**Sekwencja (Blueprint v1.3):** kontrakt async [DONE 28/06] -> **CM** -> Manager AGS migracja -> Sprzedawca.
**Zasada nadrzędna:** jedno źródło prawdy = Postgres `ags_crd`. Bot = cienkie UI. Serce = n8n + LLM + DB.

---

## 1. Czym JEST CM (Charter draft)

- **Rola:** brand-aware mózg treści = **kręgosłup** produktu na sprzedaż. Sprzedawany standalone (klient bez modułów publikujących i tak używa CM + kopiuje wyniki). Publishery (X / LinkedIn / IG) = wpinalne PŁATNE moduły.
- **Multi-tenant** po `brand_id` (AGS, TNM, ... ). Każdy obiekt = moduł (OOP), osobny kontekst agenta gdy trzeba.
- **Odpowiedzialności rdzeniowe:**
  1. Trzyma **JEDEN plan treści per marka** zasilający WIELE kanałów (zabija dryf "bot ma własne życie").
  2. Czyta strategię/głos z `brand_config`; WIDZI pamięć publikacji (`published_posts`) + kolejkę (`post_queue`) + bazę pomysłów (`inspirations`). Nie jest ślepy (vs dzisiejszy CM-czat, który żebrze o zrzuty).
  3. Kuruje drafty przez pipeline treści (HITL handler), taguje taksonomię (build-report / news / edu), egzekwuje brand canon (BEZ em-dashy, `voice_bible`).
  4. **Zleca research Researcherowi** asynchronicznie (webhook `/request`, max medium) gdy pomysł/post potrzebuje dowodów.
  5. Proponuje zmiany głosu/configu Tomaszowi (approval-learning), raportuje do Managera AGS.
  6. Routuje zatwierdzoną treść do modułów publikujących (X live; LinkedIn/IG później) + do schedulera.

## 2. Gdzie CM siedzi w sieci agentów

- CM = **agent serwerowy** (serwis FastAPI), zarejestrowany w `agent_registry` (`agent_name='content-manager'`, `allowed_model_tiers` default `['low','medium']` z db/007 -> może wołać Researchera DO medium, NIE critical; critical tylko manager-ags).
- **Komunikacja = kontrakt async zbudowany dziś:** CM wystawia `POST /request` (wake), pisze/czyta `agent_messages` (księga), oddaje callbacki. Wzorzec = `ags-researcher/app/worker.py` (POST /request + wake event + 202 + callback). Rozmawia z: Manager AGS (orkiestracja), Researcher (dowody via /request), Tomasz (Telegram), moduły publikujące.

## 3. Kandydaci na footprint DB (kierunkowo - research ma to zwalidować)

**Reuse-first (istniejący kręgosłup 9 tabel treści + sieć agentów):**
| Tabela | Rola dla CM |
|---|---|
| `brand_config` [R] | voice_bible, banned_vocab, publish_windows, taksonomia, strategia per marka |
| `inspirations` [R/W] | inbox pomysłów |
| `post_queue` [R/W] | inwentarz treści + scheduling (status, scheduled_for, brand, platform, topic) |
| `hitl_sessions` [R/W] | sesje zatwierdzania |
| `published_posts` [R] | pamięć/archiwum publikacji |
| `conversation_state`, `voice_notes/samples` | capture + pamięć głosu |
| `agent_registry/messages/approval_gates`, `research_jobs` | sieć + research |

**Potencjalnie NOWE (research ma rozstrzygnąć reuse vs nowe):**
- `content_plan` - obiekt "jeden plan zasilający wiele kanałów" (planowane itemy: kanał, slot, taksonomia, status) ALBO rozszerzenie `post_queue`.
- metryki wydajności per-platforma (przyrost followersów / engagement) - jedyna genuinely-nowa zależność dla autonomii (z [[project_product_architecture]]).
- rejestr modułów/kanałów aktywnych per marka - pod model płatnych add-onów.

## 4. Punkty integracji (research ma je zmapować)

- **X Agent** `TbHt6ZwfqmMarx18` (cron 14/18/22) - dziś ciągnie z Notion "## QUEUE"; CM przenosi ŹRÓDŁO do DB (single source) -> Notion staje się lustrem. CM trzyma plan; X-agent staje się modułem publikującym konsumującym `post_queue`.
- **HITL handler / Idea-bot** `U5pUZjy2yAhR1sWg` (202 węzły) - capture/triage/research/brama-treści/publish. CM orkiestruje NAD nim.
- **Scheduler** `x1jJEbcWAe3FnpCa` (co minutę) - publikuje `post_queue` o `scheduled_for`. CM go zasila.
- **Researcher** (5 źródeł, `/request`) - CM zleca dowody (medium).
- **brand_config** - single source głosu; CM proponuje zmiany, Tomasz zatwierdza.

## 5. Wzorce n8n / build do reuse

- async `/request` webhook + wake + 202 + callback (dzisiejszy szablon).
- adapter + guard (`X-Researcher-Secret`) dla każdego zewnętrznego calla.
- gałąź callbacku HITL (`Is X?` -> Parse -> Postgres -> Telegram confirm) dla interakcji Telegram CM.
- Postgres `FOR UPDATE SKIP LOCKED` jako kolejka; `brand_config` key/value; `app_secrets` jako single-source sekretów.
- Python orchestrator (worker) na pętlę; n8n na adaptery/ingress.

## 6. Znane luki, które CM ma domknąć (z flag samego CM)

- Jeden plan treści zasilający wiele kanałów (koniec dryfu).
- Głos single-source w `brand_config` (zrobione dla Researcher voice_bible v2 - wzorzec gotowy).
- Filtr em-dash/hyphen we WSZYSTKICH punktach publikacji.
- Dedup kolejki; CTA/link w reply pod tweetem; Szprycha-via-bot; ciągłość X Article.
- Pola taksonomii (build-report/news/edu) + pinned legenda.
- Migracja źródła Notion -> DB.

## 7. Acceptance criteria (draft, Brama 1 -> 3)

- **Brama 1 (research) PASS** = output pokrywa: architekturę agenta CM (serwis serwerowy + komunikacja przez kontrakt async), decyzję o footprincie DB (reuse vs nowe tabele), kontrakt integracji z X-agent/HITL/Scheduler/Researcher, ścieżkę migracji single-source (Notion->DB), model modułowych publisherów - dostarczone w formacie 4 opcji decyzyjnych.
- **Brama 2 (build plan) PASS** = konkretny plan budowy (tabele/migracje, workflowy n8n, serwis Python, endpointy komunikacji, plan testów) spełniający zakres kierunkowy.
- **Brama 3 (acceptance) PASS** = CM LIVE: zarejestrowany agent, osiągalny przez `/request`, produkuje brand-aware plan treści z `brand_config`+`published_posts`+`inspirations`, zleca research (medium), routuje zatwierdzoną treść do publishera X + schedulera, raportuje do Managera, wszystko na DB single-source. Cel 02-03/07.

## 8. Proponowany research query Bramy 1 (Manager wysyła, medium)

> "Architektura agenta Content Manager dla wielomarkowego (multi-tenant brand_id) systemu publikacji w stacku Postgres + n8n + Python worker. Jak zaprojektować brand-aware 'kręgosłup' treści, który: (1) trzyma JEDEN plan treści zasilający wiele kanałów, (2) czyta strategię/głos z brand_config + pamięć z published_posts + pomysły z inspirations, (3) zleca research agentowi Researcher asynchronicznie przez webhook /request (max poziom medium) i deleguje publikację do modułów per-platforma (X teraz, LinkedIn/IG później), (4) integruje się z istniejącym pipeline n8n (HITL handler, X-agent cron, per-minutowy scheduler) przenosząc źródło treści z Notion do Postgres jako single source of truth. Jakie wzorce orkiestracji agent-to-agent, podział tabel (reuse istniejących 9 vs nowe), i kontrakt komunikacyjny są najlepsze, z naciskiem na Pareto dla solo-operatora 2-4h/dzień?"

---

**Co dalej:** Tomasz zatwierdza ten BE Input -> jutro rano Manager wysyła powyższy query do Researchera = Brama 1 odpala. Researcher zwróci 4 opcje architektury -> Brama 2 (plan budowy) -> build 30/06-01/07 -> Brama 3 02/07 -> CM LIVE.
