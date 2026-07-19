# BRIEF BUILDU: BRAMKA DUPLIKACJI (19072026) - budowniczy: BE-DEDUP

Wywolanie sesji (Opus 4.8, nowe okno Cowork):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_BRAMKA_DUPLIKACJI_19072026.md zbuduj`

## 1. CO budujemy (definition of done)

Twarda bramka duplikacji TEZY przy generacji materialu: zanim karta pojdzie do Tomasza,
canonical porownywany embeddingiem z OPUBLIKOWANYMI (content_memory, pgvector juz dziala)
- wysokie podobienstwo NIE blokuje, ale karta przychodzi z ostrzezeniem.

DOWOD POTRZEBY (incydent 19/07): material "Orkiestracja agentow" zdublowal slowo w slowo
teze posta X z 11/07 ("Single agent hits a wall fast..."); lista ostatnich publikacji w
prompcie planera NIE wystarczyla (LLM zignorowal); wykryla to dopiero zewnetrzna bramka
(przegladarkowy CM) + potwierdzenie w published_posts.

DoD:
- [ ] Przy worker._draft po wygenerowaniu canonicala: embedding vs published (14-30 dni),
      prog ~0.85 cosine -> flaga w content_items.media (kind='dup_warning', text='podobienstwo
      0.92 do "<head>" z <data>') i OSTRZEZENIE na karcie (matreview._card pokazuje ⚠️ linie).
- [ ] Zero blokowania: decyzja ZAWSZE u Tomasza (kanon 19/07); bramka tylko INFORMUJE.
- [ ] py_compile + tap-test: material o tezie z ostatnich dni -> karta z ⚠️.

## 2. KONTRAKT wpiecia w szyne

- content_memory: uzyj istniejacego wyszukiwania podobienstwa (pgvector, embeddingi OpenAI -
  find_similar_published juz istnieje jako tool rozmowy; wywolaj te sama warstwe z workera).
- Zapis: TYLKO descriptor w content_items.media (zero DDL). Karta: matreview._card.
- Zero n8n, zero nowych endpointow.

## 3. Czego NIE dotykac

Planner/bramka tematow (dziala), decisions.py, Scheduler, publikacja. Zadnego auto-odrzucania.

## 4. Stan zastany

content_memory.get_published + pgvector LIVE; reguly stylu #11/#12 (dedup + twarda liczba)
zapisane w style_learned - bramka jest ich mechanicznym domknieciem.

## 5. Udzial Tomasza

Push + rebuild + jeden tap-test (karta z ⚠️).

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_dedup.md + masterprompt + pamiec + STATUS tu.

STATUS = READY (brief 19/07, tryb awaryjny - handoff na Opus 4.8)
