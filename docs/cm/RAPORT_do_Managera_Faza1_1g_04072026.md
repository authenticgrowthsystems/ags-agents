# RAPORT Faza 1 / krok 1g: autonomia + raporty daily/weekly - od BE do Managera AGS

**Data:** 04/07/2026. **Status: KOD GOTOWY (py_compile PASSED); LIVE po DDL 006 + rebuild + cron (za zgodą).**

## Przygotowanie 1g (wykonane wcześniej, 03/07)
- **Researcher job 728d02ba FAILED** (model zwrócił options jako string) -> trwały fix coerce w ResearchOutput (cf433dd, test regresji PASSED, wdrożony z rebuild). Retry zbędny: fakty wzięte bezpośrednio z oficjalnych docs.
- **Fakty metryk** (f004bb2, `docs/research/LINKEDIN_STATISTICS_API_2026.md`): memberCreatorPostAnalytics (profil osobisty, scope r_member_postAnalytics) + organizationalEntityShareStatistics (strony, rw_organization_admin). Nasz token BEZ scope -> LinkedIn metryki po review App 2 CMA. X = manual entry (decyzja #2).
- **Callbacki subagentów załatane za zgodą:** publikacja INSERTuje published_posts (post_id/URN = klucz do metryk).

## Co zbudowane (cm-agent)
- **`app/reports.py`:** kolektor metryk per cel (`channels.config.stats_mode`: manual default / member_api / org_api - oba tory API zaimplementowane wg docs, degradują się bez scope bez crashy); `set_manual_metrics` (X); **raport dzienny** (deterministyczny: publikacje 24h + metryki + decyzje autonomiczne + kolejka; UPSERT do subagent_daily_reports + push na kanał logowy bot #2); **raport tygodniowy** (agregaty 7 dni + best/worst wg engagement_rate + REKOMENDACJE z LLM tier 'weekly_report' logowane w cm_tasks; UPSERT + push). `run_all(kind)` = per KAŻDY supervised cel (open/closed).
- **Endpoint `POST /reports/daily|weekly`** (guard, 202 + wątek) - cel dla crona.
- **AUTONOMOUS_DECISION wpięte:** usunięcie/przesunięcie pozycji, materiał ad-hoc poza planem -> wpis w agent_logs z rationale i kontekstem; "wyjaśnij decyzję" w rozmowie już to czyta; raporty pokazują.
- **Ręczne metryki w rozmowie subagenta:** narzędzie `subagent_set_metrics` ("wprowadź engagement posta #25: 1200 wyświetleń, 14 reakcji...") -> engagement_metrics source='manual' + auto engagement_rate.
- **DDL db/006_reports.sql:** subagent_daily_reports + subagent_weekly_reports (UNIQUE per cel/okres, UPSERT = raport można odświeżyć).
- **Cron:** nowy workflow n8n "CM Reports Cron" (schedule 08:00 daily + niedziela 20:00, timezone Europe/Warsaw, guard z app_secrets) - skrypt gotowy, CZEKA NA ZGODĘ (produkcyjny create).

## Acceptance criteria (R3)
| Kryterium | Status |
|---|---|
| (a) AUTONOMOUS_DECISION przy odmowie/akcji poza planem + "wyjaśnij decyzję" | KOD TAK; E2E po deployu |
| (b) raport dzienny o stałej godzinie, 4 sekcje | KOD TAK; cron za zgodą; na żądanie działa już teraz ("raport") |
| (c) raport tygodniowy w niedzielę z rekomendacjami | KOD TAK (LLM rekomendacje gdy są publikacje) |
| (d) wiersze w tabelach raportowych per subagent per okres | KOD TAK (UPSERT, UNIQUE) |
| Metryki: LinkedIn po App 2, X manual (decyzja #2) | TAK (stats_mode per cel, oba tory API gotowe na token) |

## Uwaga wykonawcza
Raporty cykliczne pushuję na KANAŁ LOGOWY (bot #2) zgodnie z regułą limitów Telegrama (logi/cykliczne poza czatem rozmowy); interaktywnie "raport" w rozmowie subagenta - na głównym bocie.

**Next:** DDL 006 + rebuild + zgoda na cron -> E2E raportów -> Faza 1 KOMPLET -> 1h język (R6) -> Brama 3 / Faza 2 planer.
