# RAPORT do Managera - TASK #71 FAZA D (K6+K7) PRZYGOTOWANA

**Od:** BUILD ENGINEER (BE)
**Data:** 05/07/2026 (2 dni przed harmonogramem 07/07)
**Zakres:** K6 (pricing, sales page, playbooki, sekwencje) + K7 (vendor, funnels, GHL configs)
**Metoda:** audit-first (kontrakt = wskazowka, importujemy RZECZYWISTOSC), docs-first (kazde
zrodlo fetchniete przez MCP i obejrzane PRZED mappingiem), AP-303/AP-304 zachowane.

---

## 1. ROZJAZD CENNIKA AGS PREMIUM - ROZWIAZANY (decyzja Tomasza guzikami)

**Problem z kontraktu:** "$0/$97/$297/$2K+" vs Sales Bible TIERS "Blueprint $2000 / AIOS $5-8K /
Accelerator $15K / Whale $50-75K".

**Ustalenie audit-first:** to NIE sa dwa sprzeczne cenniki. Kanoniczna doktryna
**AGS Multi-Layer Ecosystem Strategy v1.0-1.5 (LOCKED, notion 34fc00c90b93817ca0d4c2269ebe6ca6)**
definiuje 4-warstwowy ekosystem:
- Warstwa 3 (mass market lead magnet): Free Guide $0
- Warstwa 2 (productized mid-tier): Video Walkthrough $97 + DWY Bundle $297
- Warstwa 1 (premium consulting): DOKLADNIE 4 tiery Sales Bible ($2K/$5-8K/$15K/$50-75K)
- Warstwa 4 (affiliate infrastructure): GHL 40% recurring, $39-119/mies per user

Czyli "$2K+" z kontraktu = cala Warstwa 1. Zero konfliktu.

**Decyzja Tomasza (guziki 05/07): 7 wierszy, BEZ warstwy affiliate jako tieru cenowego**
(affiliate = infrastruktura, zapisana w vendor_registry przy GoHighLevel).
Drabinka `ags_premium`, wszystkie `meta_status='active'` (decyzja Managera #2).

## 2. CO WCHODZI - LICZBY

### Statyczny SQL: `etl/notion/phaseD_vendor_pricing.sql` (15 INSERT, idempotentny)
| Tabela | Wierszy | Zrodlo |
|---|---|---|
| vendor_registry | 8 (seohost.pl, GoHighLevel, Mailgun, Cloudflare, n8n, Notion, Telegram, Twilio) | Vendor Stack 357c00c9... |
| pricing_tiers | 7 (free_guide 0 / video 97 / dwy 297 / blueprint 2000 / aios 5000-8000 / accelerator 15000 / whale 50000-75000 USD) | doktryna 34fc00c9... |

seohost.pl niesie w config pelna tabele 8 domen (brand, wygasa, email lc.*) + affiliate 25%/15%;
GoHighLevel niesie location_id, limitation sub-account (support Meera A. 15/05), regule AGS
"osobny sub-account przy $20K+ MRR" i affiliate 40% recurring.

### Silnik `etl/notion_etl.py --phase D` (9 zrodel, 2 NOWE handlery)
| Handler | Zrodlo (page_id skrot) | Cel |
|---|---|---|
| funnel_config (NOWY) | 32fc00c9 Blueprint Diagnostic BUILD BRIEF | funnel_configs, meta_status=realized_09_06 |
| content_item | 31bc00c9...0549 AGS Website Copy | content_items meta_type=sales_page, status=archived (strona LIVE z tego promptu) |
| sales_playbook | 34cc00c9...9d8b Growth Playbook | section=growth_playbook |
| sales_playbook | 34cc00c9...57c6 Peer Discovery | section=peer_discovery |
| sales_playbook | 31bc00c9...6a7a Hot Lead Responses (STK+Louise) | section=hot_lead_scripts v1.3 |
| sales_sequence (NOWY) | 31bc00c9...2a75 ABM Follow-up 48h/5d/8d | sales_sequences, steps jsonb 3 kroki z wariantami |
| brand_config_row x3 | 358c...792d, 358c...e9ca, 34ac...ab54 | ghl_config_subaccount_limitation (AGS), ghl_config_dns_pattern (AGS), ghl_config_isolation_pattern (TNM) |

**GHL configs "rozproszone":** notion-search "GHL" dal 10 stron; 3 zakwalifikowane jako CONFIG
(Vendor Patterns cross-brand + TNM isolation z location_id FAxCpFiV8RrnzLTtpAZQ). Pozostale 7 =
knowledge-transfer / build-logi / affiliate spec - NIE sa configiem, pominiete swiadomie
(czesc i tak wejdzie w Fazie E jako raporty).

## 3. ODSTEPSTWA OD KONTRAKTU (do wiadomosci Managera)
1. **pricing 7 wierszy zamiast "4 poziomow"** - pelna rzeczywistosc doktryny, decyzja Tomasza.
2. **Website Copy status=archived, nie draft** - strona AGS jest LIVE zbudowana z tego promptu
   (potwierdzone: "LLM Knowledge Transfer... strona AGS LIVE"); draft byloby falszywym stanem.
3. **Blueprint Diagnostic = funnel ZREALIZOWANY 09/06** (tytul strony: "Triple Proof SHIPPED") -
   wchodzi jako build brief z meta_status=realized_09_06, nie jako aktywny config.
4. **AP-304:** tabele Fazy D nie maja CHECK enumow (db/010: klucze naturalne UNIQUE), CHECK
   content_items.status juz zawiera 'archived' - zweryfikowane w DDL przed generowaniem.

## 4. WERYFIKACJA
- `py_compile` silnika: OK (2 nowe handlery + 9 zrodel D).
- Generator `gen_phased.py` (ags-media-spike): assert na kolizje dollar-quote, 15 INSERT, 9177 zn.
- Wszystkie 9 stron zrodlowych fetchniete i obejrzane przez MCP przed mappingiem (docs-first).

## 5. NASTEPNY KROK
Deploy Fazy D (komendy dla Tomasza w sekcji 6), potem FAZA E (K8-10: raporty subagentow,
manager_decisions, monthly discovery, roadmap_milestones) - zrodla juz zmapowane w masterprompcie.

## 6. KOMENDY DLA TOMASZA (pelne, kolejnosc wazna)

PowerShell (push galezi):
```
git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\silly-blackwell-dfc32d" push origin claude/silly-blackwell-dfc32d
```

SSH Mikrus - pg_dump przed faza (rollback):
```
docker exec pg_n8n pg_dump -U n8n ags_crd | gzip > ~/backups/ags_crd_przed_71D_$(date +%Y%m%d_%H%M).sql.gz
```

SSH Mikrus - pull + statyczny SQL:
```
cd ~/ags-agents && git pull --ff-only
docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/etl/notion/phaseD_vendor_pricing.sql
```

SSH Mikrus - silnik DRY (tylko fetch + liczby, zero INSERT):
```
cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env -v "$PWD/etl":/etl cm-agent:latest python /etl/notion_etl.py --phase D --dry
```

SSH Mikrus - silnik REAL (po czystym dry):
```
cd ~/ags-agents && docker run --rm --network n8n_network --env-file cm-agent/.env -v "$PWD/etl":/etl cm-agent:latest python /etl/notion_etl.py --phase D
```

Oczekiwane wyniki: statyczny SQL - SELECT na koncu pokaze 10 wierszy pricing_tiers (7 ags_premium
+ 3 lokalna_automatyzacja) i 8 vendorow; silnik - 9 x OK z rows=1 (poza brand_config_row, ktory
raportuje 1 przy upsert). Wklej mi output obu krokow.
