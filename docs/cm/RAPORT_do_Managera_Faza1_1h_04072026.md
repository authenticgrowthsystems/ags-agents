# RAPORT Faza 1 / krok 1h: język komunikacji i publikacji (R6) - od BE do Managera AGS

**Data:** 04/07/2026. **Status: KOD GOTOWY (py_compile PASSED), LIVE po DDL 007 + rebuild.**

## Co zbudowane
- **`language_comm`** (rozmowa/menu/raporty): czytane LIVE z brand_config (default 'pl'); wpięte w system prompt rozmowy CM, rozmowy subagentów i rekomendacje raportu tygodniowego. Zmiana: `/set language_comm en` bez deployu.
- **`language_publish` per cel:** generate_variant czyta channels.config.language_publish (default 'en') i wymusza język adaptacji; PL = czysta polszczyzna bez anglicyzmów ("mom test") - reguła w prompcie.
- **DDL db/007_language.sql:** seed language_comm='pl' + language_publish='en' dla istniejących celów (X AGS, LinkedIn profil osobisty); przyszłe cele (LinkedIn strona AGS=en, TNM=pl, RDC=pl) dostają język w config przy INSERT wiersza channels (wzór w komentarzu DDL).
- E2E raportów przed 1h: ręczny strzał /reports/daily -> 2 wiersze subagent_daily_reports (AGS x + AGS linkedin) + push na bota #2; cron ERweY5vHomrpw1SC ACTIVE (08:00 / nd 20:00 Europe/Warsaw).

## Acceptance criteria (R6)
| Kryterium | Status |
|---|---|
| (a) /set language_comm en przełącza język rozmowy bez deployu | KOD TAK (odpowiedzi LLM; stałe komunikaty deterministyczne, np. "Kolejka CM:", zostają PL - pełne i18n stringów przy pierwszej instalacji klienta EN, świadomy Pareto) |
| (b) wariant TNM po polsku / personal po angielsku z tego samego tekstu-matki | KOD TAK (mechanizm per cel; cel TNM dojdzie z App 2) |
| (c) raporty w language_comm | KOD TAK (sekcja rekomendacji; szkielet deterministyczny PL - jw.) |
| (d) seed celów | TAK dla 2 istniejących; 3 przyszłe wzorem w DDL |

## Commit
Hash w git log (w wiadomości do Tomasza).

**FAZA 1 = KOMPLET KODU (rollback R1 + 1b..1h).** Po DDL 007 + rebuild: wniosek o Bramę 3 Fazy 1 (acceptance test całości) -> Faza 2 (proaktywny planer).
