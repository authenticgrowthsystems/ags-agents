# RAPORT #70 / krok 1: Playbook instalacji u osoby trzeciej - od BE do Managera AGS

**Data:** 04/07/2026. **Status: DOSTARCZONY (publish-ready) + kosmetyka HITL naprawiona LIVE.**

## Co zrobione
- **`DEPLOY_CHECKLIST.md` przepisany do v2** (pełny plik, EN, publish-ready - zero internal brandingu,
  gotowy jako asset Sovereign Architect / downloadable case study po Bramie 3):
  - Part 0/1: wymagania + przygotowanie klienta (VPS, Anthropic z tierami i ledgerem kosztów, OpenAI,
    X dev app, LinkedIn apps ze SCOPE'ami statystyk, DWA boty Telegram, decyzje konfiguracyjne per KONTO)
  - Part 2: instalacja w 8 krokach (stack, env n8n, **bootstrap DDL 001-008 jednym poleceniem -
    wszystkie migracje idempotentne**, onboarding sekretów TYLKO do app_secrets z weryfikacją kształtu -
    lekcja z incydentu nawiasów, import 6 workflowów z podmianą credentiali, rejestracja celów =
    wiersz channels per konto z secret_prefix - zero kodu przy nowym celu, seed brand_config, wiring botów)
  - Part 3: cykl weryfikacyjny (10 punktów E2E - dokładnie te, które przeszliśmy w Fazie 1)
  - Part 4: handover + security (**rotate ALL tokens jako post-install step 1** - odpowiedź na pytanie #2;
    backupy dzienne + kopia poza serwer; mapa danych dla klienta; uczciwa known limitation i18n - pytanie #4)
  - Part 5: obsługa dzienna ("idiotoodporne": wszystko z Telegrama, jeden approve, system pyta gdy trzeba)
  - Appendix A: karta credentiali per instalacja; Appendix B: inwentarz co-gdzie-działa
- **Kosmetyka HITL (pytanie #1, w ramach #70): NAPRAWIONA LIVE** - tekst po approve mówi teraz
  "Publikacja w slocie: DD/MM HH:MM / za chwilę. Potwierdzenie na kanale logowym" (Cm Resolve Gate zwraca
  scheduled_for; PUT+reactivate zweryfikowane). Legacy "X scheduled, LinkedIn draft" usunięte.
- Odpowiedzi na 7 pytań Managera przekazane przez Tomasza (czat 04/07): #1 do #70 (zrobione),
  #2 rotacja = post-install step 1 w playbooku (u nas: osobny task ops z czyszczeniem hardkodów),
  #3 linkedin_client_secret przy #70 (czeka na 2-min wklejkę Tomasza z portalu), #4 i18n po Fazie 2,
  #5 App 2 ~2 dni w review - diagram pokaże stan faktyczny bez czekania, #6 głos/foto = post-Brama 3
  fast-follow (test 2 min przy okazji), #7 Notion: audyt TERAZ (Manager), ETL zsync z Fazą 2 (BE wykona).

## Acceptance
| Kryterium #70-1 | Status |
|---|---|
| Ścieżka wdrożenia krok po kroku dla osoby trzeciej | TAK (Part 1-4, ~1h instalacji) |
| Publish-ready (bez internal-only) | TAK (EN, generyczny VPS, zero nazw wewnętrznych) |
| Sekrety: onboarding bez ręcznego partyzanckiego SQL | TAK (app_secrets + weryfikacja kształtu; skrypt weryfikacji w repo) |
| Tomasz umie to opowiedzieć klientowi | do jego lektury - dokument pisany jęz. korzyści + inwentarz |

**Next:** #70 krok 2 = diagram graficzny przepływu danych całego systemu (wzór researcher-dataflow.svg).
