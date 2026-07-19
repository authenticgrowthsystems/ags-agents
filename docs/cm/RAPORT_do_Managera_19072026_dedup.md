# RAPORT do Managera - BE-DEDUP (19/07/2026)

Budowniczy: BE-DEDUP (Fable 5 start, Opus 4.8 finish). Galaz: `build/dedup`. Tryb rownolegly -
zero deployu (push/rebuild/psql/n8n nalezy do INTEGRATORA).

## Co zbudowane: TWARDA BRAMKA DUPLIKACJI TEZY

Domkniecie regul stylu #11/#12 mechanizmem. Incydent 19/07: material "Orkiestracja agentow"
zdublowal slowo w slowo teze posta X z 11/07 ("Single agent hits a wall fast...") - lista
ostatnich publikacji w prompcie planera NIE wystarczyla (LLM zignorowal). Teraz kod porownuje
embedding zanim karta pojdzie do Tomasza.

## Mechanizm (zgodny z kanonem 19/07: bramka INFORMUJE, nie blokuje)

1. Po wygenerowaniu i skompilowaniu canonicala (worker `_draft`, za compliance.enforce):
   `content_memory.dup_check(canonical, brand_id)` liczy embedding i szuka najbardziej podobnego
   OPUBLIKOWANEGO z ostatnich 30 dni (pgvector cosine, ta sama warstwa co find_similar, ale
   z filtrem po published_at).
2. Trafienie >= 0.85 -> descriptor w content_items.media: `{kind:'dup_warning', text:'podobienstwo
   0.92 do "<head>" [x, 11/07]'}`. Zero DDL - istniejaca kolumna media.
3. Karta materialu (matreview `_card`) pokazuje linie `⚠️ DUPLIKACJA: ...`. Tomasz widzi ryzyko
   i decyduje - zatwierdza, odrzuca albo "Inny kat".

Decyzja ZAWSZE u Tomasza. Zero auto-odrzucania, zero zmian statusow, zero blokowania.

## Twarde zasady dotrzymane

- Dotkniete TYLKO 3 pliki z KONTRAKTU: content_memory.py, worker.py, matreview.py.
- Nietkniete: planner/bramka tematow, decisions.py, Scheduler, publikacja, n8n, endpointy.
- Degradacja bez crashy: brak openai_api_key / brak dopasowania -> None, material idzie dalej
  bez ostrzezenia (bramka nie moze zablokowac generacji). try/except wokol wywolania.
- Regeneracja ("Inny kat") czysci stare 'dup_warning' - ostrzezenie zawsze swieze.
- Strojenie progu na zywo bez rebuilda: `/set cm_dup_threshold 0.9` (brand_config override).

## Testy

- py_compile: 3/3 OK.
- Test lokalny czystej funkcji dup_warning_text: 4/4 PASSED (None-hit, pelne trafienie z data,
  brak daty, newline w head sklejony do spacji; head przyciety do 80 znakow).

## Do wykonania przez INTEGRATORA (nie przeze mnie)

- Merge build/dedup do paczki deploy. Brak DDL (nie zajmuje slotu 025).
- Po rebuildzie tap-test wg DoD: material o tezie z ostatnich <=30 dni -> karta z ⚠️ DUPLIKACJA.
- Wymaga app_secrets.openai_api_key (juz LIVE - archiwum ma embeddingi).

## Udzial Tomasza (po integracji)

Push + rebuild (robi INTEGRATOR) + jeden tap-test: wygeneruj material zblizony do czegos z
ostatnich 30 dni i potwierdz linie ⚠️ na karcie.
