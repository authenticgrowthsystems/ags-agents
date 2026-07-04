# RAPORT #70 / krok 2: diagram graficzny przepływu danych - od BE do Managera AGS

**Data:** 04/07/2026. **Status: DOSTARCZONY (publish-ready EN).**

## Co zrobione
- **`docs/system-dataflow.svg`** - graficzna mapa CAŁEGO systemu (wzór: researcher-dataflow.svg, cel sprzedażowy):
  - Operator -> 2 boty Telegram (rozmowa + kanał logowy)
  - n8n TRANSPORT (HITL: rodziny guzików + router agentów; subagenci X/LinkedIn per konto; crony Scheduler/Reports)
  - cm-agent MÓZG (ConversationRouter, generacja z językiem per cel i routerem tierów, pętla slotów z jednym approve, content memory + raporty)
  - ags-researcher (moduł opcjonalny, 5 źródeł)
  - External APIs (tylko wychodzące: Anthropic/OpenAI/X/LinkedIn; stan faktyczny: App 1 LIVE + App 2 stats in review - bloczek do aktualizacji po LIVE)
  - **PostgreSQL jako SINGLE SOURCE OF TRUTH** w 4 grupach: CONTENT CORE (LIVE, w pełni relacyjny), PEOPLE/CRM (schema READY, agenci następni - wprost pokazane), AGENT NETWORK (LIVE), RESEARCH+CONFIG+VAULT (LIVE)
  - Pasek "flow of one publication" + nota o dowolnym przyszłym interfejsie i backupach
- Statusy uczciwe (LIVE vs READY vs in review) - diagram nie sprzedaje niczego, czego nie ma.
- Publish-ready: EN, zero internal brandingu - kandydat na downloadable asset po Bramie 3 (rekomendacja Managera uwzględniona).

## Acceptance (#70-2)
| Kryterium | Status |
|---|---|
| Widać co-skąd-dokąd-dlaczego (wymóg wizualny Tomasza) | TAK (grupy + strzałki z etykietami + flow jednej publikacji) |
| Baza jako centrum z grupami tabel i relacjami | TAK (4 grupy, FK opisane w DB_AUDIT ERD jako uzupełnienie) |
| Stan faktyczny bez czekania na App 2 (pytanie #5) | TAK (bloczek "in review") |
| Publish-ready | TAK |

**#70 = OBA KROKI DOSTARCZONE** (playbook eed48fb + diagram). Do decyzji Tomasza/Managera: czy #70 domyka
warunek Bramy 3 (po lekturze playbooka przez Tomasza), czy są uwagi do iteracji.
