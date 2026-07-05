# RAPORT do Managera - TASK #71 FAZA E (K8-10) PRZYGOTOWANA

**Od:** BUILD ENGINEER (BE)
**Data:** 05/07/2026 wieczor (tego samego dnia co Faza D - 2 dni przed harmonogramem)
**Zakres:** K8 (raporty subagentow: dzienne/tygodniowe/miesieczny), K9 (decyzje Managera,
validated patterns, approval gate), K10 (roadmap, plan tygodniowy)
**Metoda:** audit-first + docs-first (kazde zrodlo obejrzane przez MCP; daty i metryki z TRESCI stron).

---

## 1. CO WCHODZI - LICZBY

### DDL: `cm-agent/db/013_gate_build_input.sql` (WYMAGANY przed silnikiem E)
AP-304 potwierdzony docs-first: CHECK gate_type w zywej bazie = research/build/acceptance/
model_selection (researcher db/001+005) - 'build_input' NIE przechodzi. DDL 013: poszerza CHECK
(DO-block wzorcem db/005) + dodaje notion_page_id TEXT z unikalnym indeksem czesciowym (kotwica).

### Statyczny SQL: `etl/notion/phaseE_roadmap.sql` (16 INSERT)
roadmap_milestones <- AGS Roadmap (stan 14/05, pelny refresh Managera): 8 critical path
(M0-M6; M2/M3 done, M5 active PRIORYTET 1) + 4 ecosystem_4layer (M3.5-M3.8) + 4 post_m5
(M6.0-M7). M3.7 EU AI Act Kit = brand TNM. Kotwica entry_hash md5('AGS Roadmap|kod').

### Silnik `--phase E` (23 zrodla, 5 NOWYCH handlerow)
| Handler (NOWY?) | Zrodel | Cel |
|---|---|---|
| subagent_daily (NOWY) | 9 | 5x CM RAPORT DNIA (22-30/04), 3x X Comment Specialist (23/04, 27/04, 01/05), 1x LinkedIn SM (27/04); kotwica UNIQUE(brand,channel,data) |
| subagent_weekly (NOWY) | 3 | LinkedIn Weekly #2 (20-26/04, metryki: 673 views/+36 followers/SSI 41), X Weekly #2 (2506 imp/12 follows), CM tygodniowy 17-25/05 |
| monthly_discovery (NOWY) | 2 | Discovery Kwiecien (3 pivoty, 8 rekomendacji) + RAPORT ZAMKNIECIA Kwiecien = JEDEN wiersz 2026-04 (merge - UNIQUE(brand,month); page_id-y w metrics) |
| manager_decisions_split (NOWY) | 6 | strony decyzji 13/04-20/05 (odpowiedzi na raporty CM/LinkedIn SM, TNM Pricing Opcja B, decyzje na raport metryk); split po naglowkach, entry_hash |
| approval_gate (NOWY) | 1 | BE Briefing Pack Brama 2 (23/06) -> gate_type='build_input', agent=Researcher (lookup ILIKE w agent_registry), status='approved' (historycznie zamkniety) |
| sales_playbook | 1 | Validated Patterns v1.0 Top 5 (A1/A2/B/C/D z danymi 14 dni + mapowanie $97/$297/$5-8K) -> section='validated_patterns' |
| content_item | 1 | Plan tygodnia 23-27/06 (PLAN/PLAYBOOK) -> meta_type='weekly_plan' |

## 2. ODSTEPSTWA OD KONTRAKTU (audit-first)
1. **353c...1ba3 to NIE "LinkedIn SM weekly"** - w rzeczywistosci: "Day 12 Analytics Report"
   od X COMMENT SPECIALIST (01/05) -> zaimportowany jako raport DZIENNY kanalu x.
2. **Plan tygodniowy -> status 'archived', NIE 'proposed'**: kontrakt chcial 'proposed'
   ("planer je zobaczy"), ale tydzien 23-27/06 juz MINAL i posty POSZLY - import jako proposed
   karmilby planer CM nieaktualna praca. Intencja kontraktu dotyczy PRZYSZLYCH planow.
3. **Discovery + Zamkniecie miesiaca = 1 wiersz** (merge w handlerze) - UNIQUE(brand_id, month)
   nie pozwala na 2 wiersze za kwiecien; oba teksty pelne, rozdzielone naglowkiem.
4. **LEGACY pominiete zgodnie z kontraktem**: ARCHIWUM Raporty LinkedIn SM (kontener),
   X Content Queue, superseded v1.0-1.2.

## 3. WERYFIKACJA
- py_compile silnika: OK (5 nowych handlerow, rejestr E = 23 zrodla).
- Generator roadmap: assert dollar-quote, 16 INSERT, 7677 zn.
- AP-305 nie grozi: Connection na Nawrocki Business Hub dodany przy Fazie D (BE Briefing Pack
  i strony decyzji leza pod AGS Hub / Hub - pokryte).

## 4. KOMENDY DLA TOMASZA (pelne, kolejnosc WAZNA - DDL przed silnikiem)

PowerShell (push):
```
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d" push origin claude/silly-blackwell-dfc32d
```

SSH - backup przed faza:
```
docker exec pg_n8n pg_dump -U n8n ags_crd | gzip > ~/backups/ags_crd_przed_71E_$(date +%Y%m%d_%H%M).sql.gz && ls -lh ~/backups/ | tail -2
```

SSH - pull + DDL 013 + roadmap:
```
cd ~/ags-agents && git pull --ff-only
docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/013_gate_build_input.sql
docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/etl/notion/phaseE_roadmap.sql
```

SSH - silnik DRY, potem REAL:
```
cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env -v "$PWD/etl":/etl cm-agent:latest python /etl/notion_etl.py --phase E --dry
cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env -v "$PWD/etl":/etl cm-agent:latest python /etl/notion_etl.py --phase E
```

Oczekiwane: DDL 013 -> SELECT pokaze CHECK z 5 wartosciami; roadmap -> 16 x INSERT 0 1 + SELECT
16 wierszy; dry -> 23 x OK; real -> 23 x OK (dzienne/tygodniowe rows=1, decyzje rows=N wpisow,
monthly rows=1+1 merge). Po czystej Fazie E zostaje FAZA F (cutover 08/07: sync worker DB->Notion,
naglowki READ-ONLY MIRROR, drift checksum 03:00).
