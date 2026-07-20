# RAPORT do Managera AGS: integracja wieczorna + tap-testy (20/07/2026, BE-integrator)

## Wdrozone LIVE (serwer 0c773f8, /health ok)

1. **Naprawa incydentu publikacji (P1)**: x -> post_queue (Scheduler, sloty+media),
   linkedin -> draft (gotowce), 10 wierszy PL -> EN, re-sloty, straznik jezyka
   w stage_variant. Kontrola PASS (pl_na_kanalach_en=0). AP-307 w bibliotece.
   Raport: docs/ops/INCYDENT_PUBLIKACJI_20072026.md.
2. **Agent Sprzedazy MVP L1**: DDL 026+027, rebuild z pypdf, patch n8n komend.
   HOTFIX przy tap-testach: prospect research default medium (kanon kosztowy -
   critical przez API zablokowany) + mapowanie model_tier na nazwy modeli
   (GOTCHA: poziomy bylyby ignorowane).
3. **Pakiety aktywowane**: lokalna_automatyzacja PL 1-3 + retention_en EN 1-3
   (6 tierow active) - oferta DFY gotowa do wysylki (docs/product/).
4. Researchowe syntezy sprzedazowe w docs/research/sprzedaz_20072026/ (5.60 PLN).

## Tap-testy DoD Sprzedawcy: 5/5 PASS (dowody w DB, sonda read-only)

- /agents pokazuje Sprzedawce; rozmowa = partner dialogiczny (wlasne zdanie+pytanie).
- /prospect adamietz.pl: job medium 1.51 PLN, synteza sygnalow kupna tickiem,
  wpis w lejku (sales_pipeline stage=prospect, notatki z researchem).
- /pipeline: lejek z higiena (ostrzezenie BRAK next-step).
- /add_sales_material: zapis z embeddingiem (sales_knowledge has_embedding=true).
- Outreach: agent NAJPIERW zakwestionowal ICP (budowlanka B2B != retencja lokalna),
  po kontekscie Tomasza (cieple dojscie przez rodzine) przekwalifikowal na rozmowe
  diagnostyczna pod Blueprint i oddal gotowiec HITL (engagement_log status='proposed',
  zero nazwy narzedzia, mail pod wejscie po znajomosci). PIERWSZY REALNY PROSPEKT
  W LEJKU.

## Obserwacje do backlogu (nie blokuja)

- Telegram nie renderuje ** ** w odpowiedziach Sprzedawcy (formatowanie bota).
- Stopka syntezy ticka radzi "przelacz /agents" nawet gdy Sprzedawca aktywny.
- Sekcja HAK PERSONALIZACJI pusta przy niskim confidence (0.35) - synteza mogla
  jawnie napisac "brak konkretnego haka w evidence".
- sales_knowledge.material_name = poczatek tekstu przy wklejce bez podpowiedzi typu.

## Nastepny ruch (swiat rzeczywisty, nie build)

Telefon rodziny do wlasciciela Adamietz -> Tomasz wysyla gotowiec mailem ->
pipeline_move na 'qualified' po odpowiedzi.
