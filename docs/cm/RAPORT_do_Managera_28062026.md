# RAPORT DO MANAGERA AGS (28/06/2026, od BE)

Tomasz wkleja do czatu Manager AGS (Cowork).

## 1. Status budowy (dziś, sesja BE)

- **Kontrakt async LIVE.** Researcher ma webhook `POST /request` (event-driven wake, 202 + callback). To szablon dla CM i Sprzedawcy.
- **Critical-restriction LIVE (Regula 2).** Kaskada critical (DR+Manus, ~18 PLN) tylko `manager-ags` + `tomasz-human`; inny agent z critical -> job parkuje, decyzja wraca do Tomasza przyciskami Telegram (Zatwierdź critical / Daj medium). CM dostanie `allowed_model_tiers=['low','medium']`.
- **Parallel dispatch LIVE** (źródła równolegle), głos/foto zweryfikowane, model_selection learning działa.
- **CM Brama 1 BE Input gotowy + ZATWIERDZONY przez Tomasza** (Charter draft + footprint DB + integration points + acceptance criteria + research query medium). Master prompt dla Ciebie: `docs/cm/MASTER_PROMPT_Manager_CM_Brama1.md`.

## 2. DECYZJA TOMASZA (do odnotowania w Twojej pamięci)

**Wyniki badań ręcznych (Tomasz puszcza deep research przez najwyższe modele premium - np. największy Gemini, do którego ma płatny dostęp) dotyczące ARCHITEKTURY trafiają do BE (Opus 4.8) do technicznej syntezy, NIE przez Managera.**

Uzasadnienie Tomasza: BE = warstwa techniczna + mocniejszy model (4.8 vs Twoje 4.7) + buduje CM, więc dostaje techniczne raporty i pyta Tomasza punkt-po-punkcie przed budową. **To jest decyzja Tomasza.**

Twoja rola bez zmian: orchestrator + właściciel bram (zatwierdzasz Bramy 1/2/3), raportowanie do Tomasza. Techniczną syntezę research-architektury robi BE.

## 3. Jakość research: dwie ścieżki (kalibracja na start)

- **Researcher (automat, /request)** używa Gemini przez API na modelu `gemini-2.5-flash` (lżejszy) - dobry do tieru medium, tani.
- **Tomasz ręcznie** - największy Gemini (płatny) + inne premium modele dla trudnych tematów; wyższa jakość niż nasz flash.
- Na start: **porównujemy** wyniki Researchera vs ręczne premium Tomasza dla tych samych pytań -> kalibracja, czy/kiedy warto podbić adapter Researchera na cięższy model (fast-follow, po cost-reconcile).

## 4. Następny krok = Brama 1 CM

Wyślij zatwierdzony query (medium, BEZ `model_tier` -> auto-tier + guziki korekty na Telegram) do Researchera. Równolegle Tomasz może puścić ten sam temat ręcznie przez największy model. Oba wyniki -> BE synteza -> wejście do Bramy 2. Timeline: Brama 1 dziś, Brama 2 dziś wieczór, build 30/06-01/07, Brama 3 02/07, CM LIVE 02-03/07.

---

*Od: AGS Build Engineer (Opus 4.8). Pełny kontekst: `docs/cm/CM_Brama1_BE_input.md`.*
