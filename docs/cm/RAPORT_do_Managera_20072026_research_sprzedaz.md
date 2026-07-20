# RAPORT do Managera AGS: BE-RESEARCH-SPRZEDAZ zamkniety (20/07/2026)

Brief: BRIEF_RESEARCH_SPRZEDAZ_20072026 (SEKCJA 4 briefu Agent Sprzedazy MVP).
Galaz: build/research-sprzedaz (od origin/claude/silly-blackwell-dfc32d). Zero zmian kodu/n8n
(tylko temp webhooki read-only + dispatch, posprzatane po sobie).

## Wykonanie

4 joby zlecone Researcherowi przez kontrakt POST /request (event-driven, sekret z app_secrets
doklejany przez node PG - nie opuscil serwera). Wszystkie COMPLETED, kaskada medium
(web_search + Firecrawl + Gemini DR):

| Job | Poziom | Koszt | Claims/Evidence |
|---|---|---|---|
| konkurencja_ghl f66640c0 | medium (bramka critical zadziala, Tomasz guzikiem dal medium - level_override) | 1.66 PLN | 11/77 |
| ai_sales_tools 551dc3e6 | medium | 1.57 PLN | 15/84 |
| payment_processing 175abc14 | medium | 1.10 PLN | 14/75 |
| kanaly_pl 6a7216d2 | medium | 1.28 PLN | 13/72 |

**Koszt lacznie: 5.60 PLN** (ledger cost_events). Bramka critical_escalation = dziala zgodnie
z kanonem manager-decisions (nieznany agent -> park -> guziki -> level_override).

## Wyniki (docs/research/sprzedaz_20072026/)

01 KONKURENCJA: luka potwierdzona - rynek US tool-first ($300-5000 setup, delivery 1-4 tyg.),
nikt nie sprzedaje "systemu retencji" koncowym malym firmom bez ujawniania stacku; model
"setup + klient placi narzedzie sam" rzadki; rynek PL pusty w indeksie.
02 TOOLS: zaden (Clay/Instantly/HeyReach/Attio/Apollo) nie ma natywnego HITL - nie kupujemy,
budujemy swoje (Researcher ~1.3-1.7 PLN/job bije Clay $149+/mies.).
03 PAYMENT: Stripe = jedyna opcja na DZIS (PLN+USD jedno konto, Payment Links, P24 jako
metoda wewnatrz); GHL Invoicing to nakladka na Stripe, nie procesor.
04 KANALY PL: grupy FB (WoM > reklama), BNI druga fala, Fixly/Oferteo odradzam; rekomendacja
BE: ciepla siec Tomasza + case RDC najpierw.

REKOMENDACJE_SPRZEDAZ_20072026.md = 5 decyzji (D1 cena premium 6-9 tys. PLN / $2-2.5 tys.,
D2 Stripe dzis, D3 nie kupujemy tooli, D4 ciepla siec + FB, D5 bez doplaty za Manusa teraz).
Nastepny krok Tomasza: konto Stripe (15 min).

## Uwagi procesowe

- Confidence jobow 0.42-0.6: evidence dla nisz PL plytkie; luki oznaczone JAWNIE w dokumentach
  (REGULA PRAWDY). D5 proponuje 2 reczne 15-min weryfikacje zamiast platnego critical.
- Czesc linkow evidence to przekierowania vertexaisearch (Gemini grounding) + znany artefakt
  arxiv.org/abs/web: - opisane w dokumentach.
- Payload model_tier='critical'/'medium' NIE wplynal na kaskade (TIER_MODELS przyjmuje nazwy
  modeli, nie poziomy; poziom i tak wyznacza router + bramka). Obserwacja do ew. doprecyzowania
  w docs/komponenty/researcher.md przez sesje integracyjna.
