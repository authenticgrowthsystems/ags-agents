# AGS Agents

**Authentic Growth Systems - Documentation hub + n8n workflow version control + lightweight CLI utilities**

This repo is the source of truth for AGS agent infrastructure. The agents themselves run on Mikrus ivy147 (n8n self-hosted) and Anthropic Console workspaces. This repo holds:

- **Brand canons** (AGS, TNM, RDC, Personal) - the voice + positioning every agent must respect
- **Versioned system prompts** for each agent (audit trail for what changed when)
- **n8n workflow JSON exports** (version control for production workflows)
- **Anti-pattern library** (lessons learned, screened against during agent generation)
- **Build log** (chronological session notes, decisions, problems hit)
- **Lightweight TS utilities** for CLI tasks (brand screening, content drafting, prompt versioning)

What this repo is NOT: a runtime for autonomous agents. The runtime is n8n + AA agent hierarchy.

---

## Agent hierarchy

```
Tomasz Nawrocki (decision maker)
  ↓
MANAGER AGS (Cowork mode - strategist + brand enforcer + brake on heavy decisions)
  ↓
AA - 00 - AGS Core (operational - n8n / GHL / Notion infra builds)
  ↓ ↓
AA X Agent Builder      AA TNM Builder         AA Voice Agent Builder
(X workflows in n8n)    (TNM site + content)   (Pawel RDC voice agent)
```

Each AA agent operates in its own scope. MANAGER AGS coordinates + enforces brand canon. This repo is the shared library they all read from.

---

## Build in public

Every significant build session generates content (X post + LinkedIn post + article excerpt). The infrastructure here IS the product demo for AGS Voice AI Builder + future agent productization. Build in public = sales proof.

Live tracker: [Notion AGS Build in Public Tracker - TBD link]

---

## Stack (production)

- **Runtime:** n8n self-hosted on Mikrus ivy147 (https://ivy147-20147.mikrus.cloud)
- **Database:** PostgreSQL (containerized alongside n8n)
- **Auto-update:** Watchtower (Docker)
- **Monitoring:** Uptime Kuma (http://ivy147.mikrus.xyz:30147) + Telegram alerts
- **LLM:** Anthropic Claude (Haiku 4.5 default, Sonnet for complex tasks) - workspace "AGS", auto-reload $10/$2/$30 cap
- **Telegram bot:** @ags_alerts_bot (Chat ID 2106351328) for alerts + HITL approvals
- **Backups:** Backblaze B2 cloud (rclone v1.74.1) - currently BLOCKED on SSL cert ticket
- **CRM:** GHL (shared sub-account AGS + RDC)
- **Payments:** GHL Payments → Stripe (under Royal Dance Company, temporary until US AGS entity)

## Stack (this repo)

- **Language:** TypeScript 5.x (for utilities only)
- **Runtime:** Node.js 22 LTS
- **Package manager:** pnpm (monorepo workspaces)
- **Used for:** CLI tools, parsers, screening utilities - NOT full agent runtimes

---

## Repo structure

```
ags-agents/
├── cm-agent/              # THE SYSTEM. Content Manager: FastAPI + state-machine loop.
│   ├── app/               #   worker.py (petla), generate.py, compliance.py, channels.py, slots.py
│   ├── db/                #   DDL numerowane 001..042 - uruchamiane po kolei
│   └── tests/             #   38 plikow, stdlib only. Uruchamiaj `python -X utf8 <plik>`:
│                          #   bez tego padajacy test wywala UnicodeEncodeError na emoji
│                          #   w konsoli Windows i NIE POKAZUJE, co sie zepsulo
├── ags-researcher/        # Researcher: 6 zrodel, cost-cascade, wolany przez cm-agent
├── docs/                  # ZACZNIJ TUTAJ (patrz "Od czego zaczac" nizej)
│   ├── komponenty/        #   opis kazdego modulu - CZYTAJ ZAMIAST kodu
│   ├── ops/               #   RUNBOOK migracji, DLUG_TECHNICZNY, okna wdrozeniowe
│   ├── anti-patterns/     #   AP-306..AP-315, pelne opisy
│   ├── db/                #   SCHEMA_ags_crd.md
│   └── cm/                #   raporty do Managera, chronologicznie
├── anti-patterns/         # library.md - indeks anty-wzorcow, jedno zdanie na kazdy
├── brand-canon/           # Zrodlo prawdy glosu: AGS, TNM, RDC, Personal
├── n8n-workflows/         # Eksporty JSON zywych workflow + `patches/` (skrypty .cjs)
├── memory/                # build-log.md + stan per agent
├── prompts/               # Wersjonowane prompty systemowe per agent
├── packages/              # Narzedzia CLI (manager, shared)
├── scripts/               # Jednorazowki: eksport workflow, migracje
├── etl/                   # Import danych
└── CLAUDE.md              # Kontekst trybu Cowork dla tego repo
```

### Od czego zaczac (nowa osoba, dwie godziny)

1. `docs/GOTOWOSC_PRODUKTU.md` - co dziala, co czesciowo, czego nie ma
2. `anti-patterns/library.md` - na czym ten projekt sie juz przejechal. **To jest najszybsza
   droga do zrozumienia, dlaczego kod wyglada tak, a nie inaczej**
3. `docs/komponenty/` - opis modulu zamiast czytania zrodel
4. `docs/ops/DLUG_TECHNICZNY.md` - co jest swiadomie niedokonczone i dlaczego
5. `docs/ops/RUNBOOK_migracje.md` - **przed kazda zmiana w bazie, bez wyjatkow**

### Archiwum

Galezie `build/*` i wczesne `claude/*` zostaly skasowane 10/08/2026 jako wchloniete w calosci.
Jedna nie byla: architektura X Agenta sprzed 10/06/2026 (wlasny serwer kolejki, inne workflow
`n8n-workflows/x-agent/`) zyje pod tagiem **`archiwum/x-agent-przed-10062026`** - zastapil ja
model fire-and-forget z osobnym publisherem HITL. Szukasz starego rozwiazania kolejki:
`git show archiwum/x-agent-przed-10062026`.

---

## Status (10/08/2026)

Poprzednia wersja tej tabeli byla z **19/05** i mowila, ze X Agent jest zaparkowany,
a LinkedIn w backlogu - oba sa od miesiecy jedynymi zywymi kanalami. Szczegoly i to,
czego tu NIE MA, sa w `docs/GOTOWOSC_PRODUKTU.md`; ta tabela jest tylko zgruba.

| Komponent | Status |
|---|---|
| **cm-agent** (Content Manager) | **LIVE** na produkcji, kontener `cm-agent` na Mikrusie |
| LinkedIn (AGS) | **LIVE**, publikacja automatyczna przez Scheduler n8n |
| X (AGS) | **LIVE**, publikacja automatyczna; kolejka pusta od 29/07 (decyzja, nie awaria) |
| Researcher | **LIVE**, 6 zrodel, kaskada kosztowa |
| Lacznik (MCP: `stan_gry`, `wyslij_raport_pracy`) | **LIVE** |
| Bramka HITL (Telegram) | **LIVE** - czlowiek zatwierdza KAZDA tresc, kanon 19/07 |
| Bezpieczniki tresci (AP-315) | **LIVE** od 10/08: bramka wyjscia filtra, bezpiecznik gatunku, filtr jezykowy regulek |
| Metryki | X automatycznie; LinkedIn recznie (wniosek o API zlozony 22/07) |
| Agent Sprzedazy | L1, dziala; pierwsza sprzedaz jeszcze nie zamknieta |
| Wielomarkowosc (TNM, RDC) | kod jednomarkowy - D-013, czeka na pierwsza sprzedaz |

---

## Active priorities

> **Ta lista jest z 19/05/2026 i NIE jest aktualna.** Zostaje nietknieta swiadomie: priorytety
> ustala wlasciciel, nie sesja porzadkowa, wiec zgadywanie ich byloby gorsze niz jawna data.
> Stan faktyczny prac czytaj z `docs/ops/DLUG_TECHNICZNY.md` (co otwarte i dlaczego)
> oraz z najnowszego raportu w `docs/cm/` - to one sa zywe.

1. **P0 Wave 0.5 GHL Pipeline Rebuild** - 4-tier funnel (Free Guide / $97 / $297 / $2K+). Direct revenue path.
2. **P1 AGS Agent Factory (this repo + AA X Agent Builder reactivation)** - parallel system-as-content track
3. **P2 Free Guide + $97 product content** (PL for TNM, EN for AGS) - feeds Wave 0.5
4. **P3 Backup strategy** - BLOCKED on Backblaze SSL ticket

---

## License

UNLICENSED (private until stable, then likely MIT or Apache 2.0).
