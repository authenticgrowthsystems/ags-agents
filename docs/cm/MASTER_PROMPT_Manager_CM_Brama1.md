# MASTER PROMPT -> MANAGER AGS: Brama 1 CM (29/06/2026)

Tomasz wkleja ten plik do czatu **Manager AGS** (Cowork). To brief Bramy 1 dla Content Managera, przygotowany przez BE.

---

## 1. Kontekst (co BE dowiózł 28/06 - fundament Fazy 1)

- **KONTRAKT ASYNC LIVE.** Researcher ma webhook `POST /request` (event-driven: budzi workera natychmiast, zwraca `202 {job_id}`, wynik leci callbackiem - Telegram + `agent_messages` RESPONSE). To jest **szablon dla CM i Sprzedawcy** (każdy nowy agent: FastAPI + /request + wake + callback).
- **CRITICAL-RESTRICTION LIVE (Regula 2).** Kaskada `critical` (OpenAI DR + Manus, ~18 PLN/query) zarezerwowana dla `manager-ags` + `tomasz-human`. Każdy inny agent z zapytaniem critical -> job parkuje i decyzja wraca do Tomasza przyciskami Telegram (Zatwierdź critical / Daj medium). **CM dostanie `allowed_model_tiers=['low','medium']`** -> może wołać Researchera DO medium, NIE critical.
- **Parallel dispatch LIVE** (źródła lecą równolegle), głos/foto zweryfikowane, model_selection learning loop działa.
- **Sekwencja (Blueprint v1.3):** kontrakt [DONE] -> **CM** -> Manager AGS migracja -> Sprzedawca.

## 2. Twoje zadanie teraz = BRAMA 1 CM (research gate)

Zleć Researcherowi research **architektury agenta Content Manager** (model_tier=medium). BE przygotował pełny kontekst kierunkowy (Charter draft, footprint DB reuse-vs-nowe, integration points z X-agent/HITL/Scheduler/Researcher, acceptance criteria Brama 1-3) w repo: `docs/cm/CM_Brama1_BE_input.md`.

## 3. Gotowy research query (medium) - to wyślij

> Architektura agenta Content Manager dla wielomarkowego (multi-tenant brand_id) systemu publikacji w stacku Postgres + n8n + Python worker. Jak zaprojektować brand-aware "kręgosłup" treści, który: (1) trzyma JEDEN plan treści zasilający wiele kanałów, (2) czyta strategię/głos z brand_config + pamięć z published_posts + pomysły z inspirations, (3) zleca research agentowi Researcher asynchronicznie przez webhook /request (max poziom medium) i deleguje publikację do modułów per-platforma (X teraz, LinkedIn/IG później), (4) integruje się z istniejącym pipeline n8n (HITL handler, X-agent cron, per-minutowy scheduler) przenosząc źródło treści z Notion do Postgres jako single source of truth. Jakie wzorce orkiestracji agent-to-agent, podział tabel (reuse istniejących 9 vs nowe), i kontrakt komunikacyjny są najlepsze, z naciskiem na Pareto dla solo-operatora 2-4h/dzień?

## 4. Jak to odpalić (wykonuje TOMASZ na Mikrusie)

Manager nie ma bezpośredniego dostępu do serwera. Po tym jak zatwierdzisz/dopracujesz query, Tomasz odpala go event-driven (`from=manager-ags`, więc bez restrykcji critical, ale query i tak jest medium):

```bash
SECRET=$(docker exec pg_n8n psql -U n8n -d ags_crd -tAc "SELECT value FROM app_secrets WHERE key='researcher_webhook_secret'" | tr -d '[:space:]') && \
curl -sS -X POST http://localhost:8088/request \
  -H "X-Researcher-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"query":"<WKLEJ QUERY Z SEKCJI 3>","from":"manager-ags"}'; echo
```

UWAGA: NIE podajemy `model_tier` -> tier jest AUTO (medium query -> sonnet), więc na wyniku Telegram dostaniesz guziki korekty **[haiku / sonnet / opus]** ("Zły tier? Popraw"). Jednym tapem możesz podbić syntezę na **opus** (cięższy model) dla ważnej decyzji architektury, a Manager się na tym uczy. (Gdybyś chciał wymusić tier z góry, dodaj `"model_tier":"opus"` - wtedy guzików NIE będzie, bo narzucony tier nie jest decyzją do nauki.)

Researcher zwróci **4 opcje architektury CM** (Najszybsza / Najtańsza / Najwyższe upside / Najwyższa pewność) z dowodami, na Telegram + `agent_messages` RESPONSE = materiał wejściowy do Bramy 2.

## 5. Po Bramie 1

- Przejrzyj 4 opcje, wybierz kierunek -> **Brama 2** (plan budowy: tabele/migracje, workflowy n8n, serwis Python, endpointy komunikacji, plan testów).
- **Timeline CM:** Brama 1 dziś, Brama 2 dziś wieczór, build 30/06-01/07, Brama 3 02/07, **CM LIVE 02-03/07**.
- Diagram CAŁOŚCI (sprzedażowy) produkuje CM po LIVE (Zasada #5 Cross-Platform Doctrine), nie BE.

---

*Przygotował: AGS Build Engineer, 28/06/2026. Pełny kontekst techniczny: `docs/cm/CM_Brama1_BE_input.md`.*
