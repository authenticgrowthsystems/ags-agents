# RAPORT Faza 1 / krok 1f: content_memory cross-channel - od BE do Managera AGS

**Data:** 03/07/2026. **Status: KOD GOTOWY (py_compile PASSED), LIVE po DDL 005 + rebuild cm-agent.**

## Co zbudowane (cm-agent)
- **`app/content_memory.py`** (R5, wzorzec Centralized Content Brain):
  - `get_published(brand, days_ago, channel, limit)` - archiwum published_posts per marka/kanal
  - `top_performing(brand, channel, metric, top_n)` - top wg `engagement_metrics->>metric` (NULLS LAST -> do czasu metryk sortuje po swiezosci; pola metryk doprecyzuje wynik Researchera 728d02ba)
  - `find_similar(text, brand, top_n)` - **pelny pgvector** (cosine `<=>`): embeddingi OpenAI text-embedding-3-small (klucz JUZ w app_secrets - uzywa go adapter OpenAI DR; zero nowych sekretow), backfill leniwy porcjami po 25, degradacja bez crashy gdy klucz/API padnie
  - `suggest_adaptation(published_id, target_channel)` - adaptacja archiwalnego posta na inny kanal (tier 'variant' z routera R4); do kolejki TYLKO przez propose_material + approve
- **Rozmowa CM +3 narzedzia:** `show_archive` ("co najlepiej zagralo?"), `find_similar_published` ("czy juz o tym pisalismy?" - antydubel przed proponowaniem), `adapt_published` ("adaptuj #12 na linkedin").
- **Hook nowego kanalu (open/closed):** petla workera wykrywa kanal active/draft+supervised bez znacznika `welcomed` -> wysyla Tomaszowi propozycje kandydatow do adaptacji z archiwum -> znacznik w channels.config. DDL 005 oznacza ISTNIEJACE kanaly jako welcomed (propozycje tylko dla przyszlych aktywacji, np. Instagram).
- **DDL db/005_embeddings.sql:** `published_posts.embedding vector(1536)` + seed welcomed. (Indeks ivfflat dopiero przy wiekszym archiwum - sekwencyjny cosine przy dzisiejszej skali jest szybszy i prostszy.)

## Acceptance criteria (R5)
| Kryterium | Status |
|---|---|
| (a) get_top_performing zwraca posortowane posty z metrykami | KOD TAK (metryki wchodza z raportami 1g) |
| (b) pytanie w rozmowie CM o najlepsze posty -> dane z archiwum | KOD TAK; E2E po deployu |
| (c) aktywacja testowego kanalu -> propozycja adaptacji | KOD TAK; test = INSERT wiersza channels |
| (d) published_posts ma content_item_id + engagement_metrics | TAK (DDL 004 zaaplikowany przez Tomasza) |
| find_similar pelny pgvector (decyzja Managera #3) | TAK (0.8.2 + text-embedding-3-small) |

## Decyzja BE do odnotowania
Provider embeddingow = OpenAI text-embedding-3-small: klucz juz w app_secrets, koszt $0.02/1M tokenow, 1536 wymiarow. Alternatywa (Voyage) wymagalaby nowego konta/klucza - odrzucona per Pareto.

## Commit
Hash w git log (w wiadomosci do Tomasza).

**Next:** DDL 005 + rebuild (Tomasz) -> 1g raporty (WYMAGA wyniku Researchera 728d02ba - status do sprawdzenia).
