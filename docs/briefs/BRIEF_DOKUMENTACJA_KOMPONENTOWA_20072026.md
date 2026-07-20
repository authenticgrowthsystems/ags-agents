# BRIEF BUILDU: DOKUMENTACJA KOMPONENTOWA (20072026) - budowniczy: BE-DOKUMENTACJA

Wywolanie sesji (nowe okno; Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_DOKUMENTACJA_KOMPONENTOWA_20072026.md zbuduj`

## 0. Tryb rownolegly

Wlasny worktree+galaz (wzorzec sekcji 0 briefow 19/07): galaz `build/dokumentacja` od
origin/claude/silly-blackwell-dfc32d, worktree `build-dokumentacja`. ZERO deployu/psql/n8n/
zmian kodu - to build CZYSTO dokumentacyjny. Merge przez integratora albo wprost (docs-only,
konflikt malo prawdopodobny - NIE dotykac briefow innych sesji).

## 1. CO budujemy (kanon Tomasza 20/07, utwardzony w PROTOKOL_SESJI pkt 6)

Problem: dokumentacja narasta DATAMI (SYSTEM_DATAFLOW sekcje per dzien, raporty per krok)
- to dziennik zmian, nie podrecznik. Sesja szukajaca "jak dziala planner" czyta historie
albo kod i pali tokeny. Cel: dokumentacja KOMPONENTOWA opisujaca STAN OBECNY.

Deliverable: `docs/komponenty/` - jeden plik na komponent, kazdy w STALYM szablonie
(Co robi / Wejscia-wyjscia i tabele / Konfiguracja (brand_config, channels.config) /
Punkty zaczepienia w kodzie (plik:funkcja) / Kanony ktore go dotycza / Znane pulapki):
1. planner.md (plan tygodnia, bramka tematow, cap, guard crona, sloty)
2. kolejka-publikacja.md (post_queue, slot gate, Scheduler, humanize_slot, serie X, straznik)
3. karty-hitl.md (matreview, karty na dole, Media/Prompt/Generuj, approval hitl, edycja=nauka)
4. decyzje-nauka.md (agent_decisions, decision_modes, dec:, stale_approval, learning_log)
5. metryki.md (kolektor X Owned Reads, import xlsx LinkedIn, channel_metrics_daily, PROFIL)
6. dedup.md (dup_check na master_theme, prog cm_dup_threshold, ⚠️ w kartach i approval)
7. rozmowa-cm.md (conversation: route deterministyczne, narzedzia, pamiec 3 warstwy, subagenci)
8. researcher.md (kaskada zrodel, /request kontrakt, sunday_brief, tabele research_*)
9. grafika.md (gpt-image-2, prompt Sonneta, visual_canon/brand_tokens, kanon mediow)
10. sync-notion.md (mirror, sync_registry/page_map, drift) + n8n-transport.md (HITL galezie,
    zasady PUT, patchery)
Material zrodlowy: SYSTEM_DATAFLOW (sekcje historyczne), SCHEMA, raporty docs/cm/, briefy,
masterprompt 2b - KOMPILUJESZ z istniejacych dokumentow, kod czytasz tylko do weryfikacji
watpliwosci. SYSTEM_DATAFLOW zostaje jako mapa przeplywu + indeks linkujacy do komponentow;
sekcje datowane przenosisz do docs/archiwum-dataflow.md (historia nie ginie, ale nie udaje
dokumentacji).

DoD:
- [ ] 10-11 plikow komponentowych w jednolitym szablonie, kazdy <= ~150 linii, STAN OBECNY
- [ ] SYSTEM_DATAFLOW = mapa + indeks; sekcje datowane w archiwum
- [ ] Masterprompt sekcja 1: "dokumentacja komponentow: docs/komponenty/ - CZYTAJ ZAMIAST kodu"
- [ ] Test uzytecznosci: odpowiedz na 3 pytania kontrolne (np. "jak zmienic okno publikacji",
      "co sie dzieje po zatwierdzeniu karty", "gdzie mieszka prog dedupa") WYLACZNIE z nowych
      dokumentow, bez zagladania w kod

## 5. Udzial Tomasza

Zero SSH/deployu. Jedno przejrzenie struktury + push.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_dokumentacja.md + masterprompt + pamiec + STATUS tu.

STATUS = READY (20/07, kanon DOKUMENTACJA ZYJE wpisany do PROTOKOL_SESJI pkt 6 i masterpromptu)

## 1b. DOPISEK ZAKRESU (Tomasz 20/07, w trakcie buildu - "nie moge sprzedawac czegos co nie jest gotowe")

MACIERZ GOTOWOSCI PRODUKTU: nowy plik `docs/GOTOWOSC_PRODUKTU.md` + STATUS GOTOWOSCI
w naglowku KAZDEGO pliku komponentu. Skala uczciwa, bez marketingu do wewnatrz:
- KOMPLETNY (LIVE, przetestowany tapami, ma dokumentacje) / CZESCIOWY (dziala rdzen,
  brak wymienionych funkcji) / W BUDOWIE / ZAMROZONY / NIEZACZETY.
`GOTOWOSC_PRODUKTU.md` odpowiada wprost na pytanie "JUTRO MAM KLIENTA - CO MOGE SPRZEDAC":
1) definicja MVP per obiekt sprzedazowy (subagent X pod CM, Idea Bot, Researcher, LinkedIn
   tryb reczny...) - co klient dostaje DZIS w cenie, co dojedzie w cenie pozniej (model:
   MVP rozwijany, funkcje doplywaja);
2) czego NIE sprzedajemy (zamrozone/niekompletne) - lista wprost;
3) braki blokujace sprzedaz per obiekt (np. interfejs tylko Telegram, wdrozenie bez
   playbooka do czasu BE-SNAPSHOT).
Kazdy przyszly build MA OBOWIAZEK aktualizowac te macierz (kanon DOKUMENTACJA ZYJE pkt 6a).
