# RAPORT STANU BUILDU dla Managera AGS (20/07/2026 ~13:25, BE - Instance A audytu)

Zrodla: zywa baza (read-only, inwentarz 13:10), docs/GOTOWOSC_PRODUKTU.md (macierz LIVE),
docs/komponenty/ (11 dokumentow), test landing page (WebFetch 13:15). Format iteracyjny -
sekcje 1.1-1.4 + odpowiedzi na pytania; uzupelnienia dojda po buildach B/C/D.

## 1.1 Inwentarz LIVE

**Agenci:** CM orkiestrator (CZESCIOWY wg kanonu real_scope - planowanie tygodnia, rozmowa-
partner, nadzor, eskalacje z nauka: LIVE), Subagent X (SPRZEDAWALNY MVP: plan->karty->
publikacja slotami->metryki Owned Reads->komentarze; engagement-CRM ZBUDOWANY dzis, czeka
psql 026+rebuild), Subagent LinkedIn (CZESCIOWY: gotowce reczne, metryki xlsx), Idea Bot
(LIVE), Researcher (LIVE po naprawie web_search 20/07; 5 zrodel, cost-cascade; dowod sobotni
26/07), Sunday-brief/CM-czyta-swiat (LIVE, fix split-brain czeka na rebuild), Agent Wizualny
(ZAMROZONY), Agent Sprzedazy (BUILD DZIS - brief gotowy). Szczegoly per komponent:
docs/komponenty/*.md (status w naglowkach).

**Kanaly:** AGS x ACTIVE (publikacja+metryki auto), AGS linkedin ACTIVE (personal, gotowce
reczne; metryki xlsx), ready: AGS linkedin_page/YT/FB/IG + TNM/RDC/LYSY/PT/SDI linkedin
(czekaja aktywacji/tokenow; LinkedIn pages = App 2 CMA poza nasza kontrola). IG/FB/TikTok:
ZERO buildu publikacji.

**Baza (wybrane liczniki):** content_items 229, post_queue 214, published_posts 98,
contacts 45 (tiery Buyer/Peer/Competitor/Partner), engagement_log 15, x_post_metric_snapshots
386 (kolektor dziala!), channel_metrics_daily 30, inspirations 115, research: jobs 22/
evidence 744, cm_tasks 911 (ledger kosztow LLM), pricing_tiers 10, sales_playbook 6,
sales_sequences 1, funnel_configs 1, icp_definitions 1, vendor_registry 8. app_secrets 17.

**n8n ACTIVE (18):** HITL U5pUZjy2yAhR1sWg (rozmowy/decyzje/karty - 252+ wezly), AGS
Scheduler (publikacja per minute), Subagent X/LinkedIn Publisher, CM Reports Cron, HITL
Timeout Checker, LinkedIn OAuth Callback, Researcher x7 (adaptery+statusy), Analytics Daily
Digest, TNM Lead Intake + GHL Waitlist, Apply Lead Intake, Error Handler. Legacy AGS X
Agent OFF (zweryfikowane 20/07).

**Voice/brand:** Voice Bible AGS v2.2 (v=4, md5 dc8b4334) + TNM v2.0 (v=2) + voice_dna_core
v1 (rdzen osobisty, SSOT w DB, Notion=mirror). brand_tokens: AGS 17 + TNM 17. Kanon
walutowy: AGS=USD, TNM/PL=PLN, fakty w walucie zrodla.

## 1.2 Produkty Multi-Layer - gotowosc do sprzedazy

| Tier (pricing_tiers, meta_status) | Ocena | Brakuje konkretnie |
|---|---|---|
| W3 free_guide $0 (active) | ❌ | brak tresci guide'a, brak lead-capture poza aplikacja Blueprint |
| W2 video_walkthrough $97 (active) | ❌ | wideo nie istnieje, brak checkoutu |
| W2 dwy_bundle $297 (active) | ❌ | materialy nie spakowane, brak delivery/checkout |
| W1 blueprint $2K (active) | ⚠️ 80% | LANDING LIVE z aplikacja (dziala!); brakuje: proces platnosci + deliverable template (format raportu 90-min diagnozy) |
| W1 aios_sprint $5-8K (active) | ⚠️ | to w praktyce nasz done-for-you na infrastrukturze AGS (GOTOWOSC sekcja 1) - brak runbooka klienta (BE-SNAPSHOT HOLD) |
| W1 accelerator $15K / whale $50-75K (active) | ❌ | oferta niezdefiniowana operacyjnie |
| W4 affiliate (GHL 40%, seohost) | 🚫 | pipeline nieaktywny, nikt nie sprawdzal linkow |
| **Pakiety PL 1-3 (parking_active): 2000-3000 / 3000-5000 / 5000-8000 PLN + narzedzie $97-297/mc placone przez klienta** | **✅ NAJBLIZEJ SPRZEDAZY** | tylko: aktywacja tierow (SQL+decyzja), oferta-dokument (BUILD C DZIS), sciezka platnosci |

## 1.3 Infrastruktura sales-ready (BE)

- CRM/pipeline: contacts+engagement_log LIVE; sales_pipeline + sales_knowledge = DDL 027
  w buildzie B (dzis). Stadium relacji + intake osob = DDL 026 zbudowane dzis (czeka psql).
- Email: BRAK integracji server-side (Gmail API do zbudowania - Level 2, ~1 dzien docs-first).
  W Cowork jest MCP Gmail (biurordc@gmail.com) - do recznej obslugi od zaraz przeze mnie/Tomasza.
- Payment: NIC zweryfikowanego. Kandydaci: GHL invoicing (Tomasz ma konto GHL - sprawdzenie
  10 min!), Stripe (setup 1-2 dni), P24 dla PLN. Research task 3 (build D) da rekomendacje.
- Landing authenticgrowthsystems.com: **LIVE** - oferta "Revenue Architecture Blueprint",
  aplikacja jako lead-capture, TON selektywny, BEZ checkoutu, BEZ niskich tierow.
  ⚠️ KONFLIKT DOKTRYNY: doktryna zakazuje /apply, a landing stoi na aplikacji - DECYZJA
  Tomasza/Managera (zostawic jako wyjatek dla W1 czy przerobic CTA).
- Assety/case studies: NIE spakowane. Surowce SA: TNM (leady GHL Waitlist LIVE), RDC,
  wlasny system AGS jako zywy case (build-in-public, metryki od dzis). Voice AI demo: brak.

## 1.4 TOP 5 dziur blokujacych PIERWSZY close (w kolejnosci)

1. **SCIEZKA PLATNOSCI** - nie ma jak przyjac pieniedzy (nawet za setup DFY). Najszybciej:
   GHL invoicing (sprawdzenie dzis) albo zwykla FV + przelew na start PL. Bez tego kazda
   rozmowa konczy sie niczym.
2. **OFERTA-DOKUMENT DFY** gotowa do wyslania (BUILD C - dzis; Pakiety PL juz wycenione w DB).
3. **AGENT SPRZEDAZY L1** (BUILD B - dzis): prospect research + outreach drafty + pipeline,
   zeby wysylki ruszyly systematycznie, nie zrywami.
4. **Umowa/warunki DFY** - prosty wzorzec zlecenia (1 strona; kto wystawia FV - dzialalnosc
   Tomasza? DO POTWIERDZENIA przez Tomasza).
5. **Obsluga hello@ / odpowiedzi na leady** - do czasu Level 2: recznie z alertem (leady z
   TNM Waitlist juz wpadaja do GHL - kto je dziS obdzwania?).

## Odpowiedzi na pytania Managera (sekcja 6)

1. **Najblizej first-sale:** NIE W-tiery, tylko **DFY Retencja na Pakietach PL 1-3**
   (parking_active w bazie od migracji #71!) - produkt = praca Tomasza + narzedzie, zaleznosc
   tylko od jego czasu. Drugi: Blueprint $2K (landing LIVE, brakuje platnosci+template).
2. **Anthropic sales skills: TAK, ZAINSTALOWANE** w Cowork: sales:draft-outreach,
   account-research, call-prep, call-summary, pipeline-review, forecast,
   competitive-intelligence, create-an-asset, daily-briefing. Build B destyluje ich
   frameworki do promptu Agenta (server-side nie ma Skill toola - embedded).
3. **Email integration:** Level 2, ~1 dzien z docs-first (Gmail API OAuth + watch). Do tego
   czasu: MCP Gmail w Cowork = obsluga reczna wspierana od zaraz.
4. **Landing:** LIVE (Blueprint, aplikacja). Zeby prospect MOGL WPLACIC dzis: brak checkoutu
   - patrz dziura #1. Uwaga na konflikt doktryny /apply.
5. **Payment:** NIC LIVE zweryfikowanego. Rekomendacja: dzis GHL invoicing/FV+przelew,
   docelowo wg researchu (build D, task 3).

## Status instancji (sekcja 5 briefu Managera)

A (audit) = TEN RAPORT (BE, gotowy). B/C/D = briefy READY w docs/briefs/ (AGENT_SPRZEDAZY_MVP
/ PRODUKT_DFY_RETENCJA / RESEARCH_SPRZEDAZ) - Tomasz odpala 3 okna. E (integracja+deploy
wieczorny: psql 026+027 + rebuild + patch n8n engagement + tap-testy) = BE po DONE B/C.
