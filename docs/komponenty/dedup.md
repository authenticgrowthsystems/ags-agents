# Komponent: BRAMKA DUPLIKACJI TEZY (embedding vs opublikowane)

**STATUS GOTOWOSCI: KOMPLETNY (strojenie progu przez /set czeka na patch allowlisty; SQL dziala)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Zanim karta materialu trafi do Tomasza, kod porownuje TEMAT materialu
(master_theme) z OPUBLIKOWANYMI trescami ostatnich 30 dni (pgvector cosine).
Trafienie powyzej progu = linia ostrzezenia na karcie i w approval:

```
⚠️ DUPLIKACJA: podobienstwo 0.60 do "Single agent hits a wall fast..." [x, 11/07]
```

Bramka INFORMUJE, nie blokuje (kanon 19/07): zero auto-odrzucania, zero zmian
statusow. Decyzja ZAWSZE u Tomasza. Powod istnienia: incydent 11/07 - material
zdublowal slowo w slowo teze posta X mimo listy publikacji w prompcie planera
(LLM ja zignorowal); wykryla to dopiero zewnetrzna bramka.

## Wejscia-wyjscia i tabele

- Wejscie: `content_items.master_theme` (PO KALIBRACJI 20/07 - patrz pulapki;
  fallback canonical gdy master_theme pusty) po compliance.enforce w _draft.
- Porownanie: `published_posts` z embeddingami (OpenAI text-embedding-3-small,
  ta sama warstwa co find_similar), filtr published_at >= now-30 dni.
- Wyjscie: descriptor `{kind:'dup_warning', text:'podobienstwo X do "<head>"
  [kanal, data]'}` w `content_items.media` (zero DDL - istniejaca kolumna).
- Render: karta matreview (`_card`) ORAZ wiadomosc approval
  (`hitl.send_approval`) - ostrzezenie jest tam, gdzie zapada decyzja.

## Konfiguracja

- Prog: `brand_config (AGS, cm_dup_threshold)` = **0.57** (skalibrowany
  20/07 na zywym korpusie). Fallback w kodzie: 0.85 (gdy brak wiersza).
- Strojenie progu = SQL na brand_config (UPDATE + bump version).
  UWAGA: `/set cm_dup_threshold` NIE dziala - allowlista wezla Parse And
  Authorize Set w n8n nie zna klucza (backlog: patch allowlisty).
- Okno: DUP_WINDOW_DAYS=30 w kodzie (content_memory.py).
- Wymaga `app_secrets.openai_api_key` (embeddingi archiwum juz istnieja).

## Punkty zaczepienia w kodzie

- `cm-agent/app/content_memory.py`: `dup_check` (glowna funkcja),
  `_dup_threshold` (odczyt progu), `dup_warning_text` (render tekstu),
  `embed`, `find_similar` (siostrzana, do rozmowy CM).
- `cm-agent/app/worker.py`: wywolanie w `_draft` -
  `dup_check(item.get("master_theme") or canonical, ...)` (commit dd7918c).
- `cm-agent/app/matreview.py`: linia ⚠️ w `_card`.
- `cm-agent/app/hitl.py`: linia ⚠️ w `send_approval` (commit ba06906).
- Regeneracja ("Inny kat") czysci stare dup_warning - ostrzezenie zawsze
  swieze.

## Kanony ktore go dotycza

- Bramka informuje, nie blokuje; decyzja u Tomasza (kanon 19/07).
- Reguly stylu #11/#12 (zakaz duplikacji tez) - bramka jest ich mechanicznym
  domknieciem.
- Degradacja bez crashy: brak klucza / brak dopasowania -> None, material
  idzie dalej BEZ ostrzezenia (bramka nie moze zablokowac generacji).

## Znane pulapki

- KALIBRACJA 20/07 (lekcja warsztatowa): embedding PELNEGO canonicala NIE
  separuje duplikatow (celowy blizniak 0.536 vs zwykle materialy do 0.588 -
  wspolny styl domowy dlugich tekstow rozmywa teze). Embedding TEMATU
  (master_theme) separuje czysto: blizniaki 0.597-0.627 vs reszta <=0.551.
  Stad porownanie na master_theme i prog 0.57. Progow bramek jakosciowych
  NIE przyjmowac z teorii - mierzyc na zywym korpusie.
- Pierwotne DoD (canonical, prog 0.85) wygladalo rozsadnie i bylo bezuzyteczne
  (0 mozliwych trafien).
- Ostrzezenie tylko na karcie matreview nie wystarczylo - decyzja zapada
  w approval, wiec ⚠️ musi byc i tam (fix ba06906).
