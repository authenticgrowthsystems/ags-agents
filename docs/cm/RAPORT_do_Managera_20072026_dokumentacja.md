# RAPORT do Managera - BE-DOKUMENTACJA (20/07/2026, build czysto dokumentacyjny)

Brief: docs/briefs/BRIEF_DOKUMENTACJA_KOMPONENTOWA_20072026.md. Galaz
`build/dokumentacja` (worktree build-dokumentacja, baza 7283354 = lokalny HEAD
sb-work; origin byl 2 commity w tyle, wiec galaz poszla od LOKALNEGO - brief
sam lezal dopiero w 7283354). ZERO kodu, ZERO deployu, ZERO n8n - dotrzymane.

## 1. Co zbudowane (per DoD)

| DoD | Stan | Jak |
|---|---|---|
| 10-11 plikow komponentowych, staly szablon, <=~150 linii, STAN OBECNY | DONE | `docs/komponenty/`: planner, kolejka-publikacja, karty-hitl, decyzje-nauka, metryki, dedup, rozmowa-cm, researcher, grafika, sync-notion, n8n-transport (11 plikow, 74-114 linii kazdy). Szablon: Co robi / Wejscia-wyjscia i tabele / Konfiguracja / Punkty zaczepienia w kodzie / Kanony / Znane pulapki |
| SYSTEM_DATAFLOW = mapa + indeks; sekcje datowane w archiwum | DONE | SYSTEM_DATAFLOW.md przepisany: architektura, glowny przeplyw tresci (pomysl->plan->generacja->decyzja->publikacja->metryki->nauka) z odsylaczami, tabela-indeks 11 komponentow, stan/legacy, TODO diagram. STARA tresc W CALOSCI (skopiowana mechanicznie, zero transkrypcji) w docs/archiwum-dataflow.md z preambula |
| Masterprompt sekcja 1: "docs/komponenty/ - CZYTAJ ZAMIAST kodu" | DONE | pierwszy bullet sekcji 1 RESUME_MASTERPROMPT_19072026.md |
| Test uzytecznosci: 3 pytania WYLACZNIE z nowych dokumentow | PASS 3/3 | sekcja 2 ponizej |

Zrodla kompilacji: SYSTEM_DATAFLOW (sekcje historyczne), SCHEMA_ags_crd,
masterprompt 2b, raporty docs/cm/ (19-20/07, sprint 12/07, STAN_CM 10/07),
briefy 19-20/07, handoff integracji. Kod czytany TYLKO do weryfikacji punktow
zaczepienia (listy `def` per modul - kazda nazwa funkcji w dokumentach
zweryfikowana ze zrodlem) + pamiec trwala dla stanu naprawy Researchera.

## 2. Test uzytecznosci (odpowiedzi bez zagladania w kod)

1. **"Jak zmienic okno publikacji?"** - rozmowa-cm.md: napisac do CM
   "ustaw okno publikacji dla AGS x na 13:00-21:00" - deterministyczny route
   `_config_route` (_USTAW_OKNO_RE) PRZED LLM -> `_target_update` ->
   channels.config.publish_windows + paragon ⚙️. Bez paragonu ⚙️ = niewykonane.
2. **"Co sie dzieje po zatwierdzeniu karty?"** - karty-hitl.md +
   kolejka-publikacja.md: approve (guzik cm:<id>:approve w approval) ->
   content_items 'approved' -> worker claimuje DOPIERO gdy scheduled_for<=NOW()
   -> dispatch per channels.config.publish_mode (webhook subagenta n8n /
   'scheduled' dla Schedulera / 'held' recznie) -> callback: post_queue
   'published' + INSERT published_posts + potwierdzenie na bot #2. Zatwierdzone
   wychodzi ZAWSZE, obecnosc Tomasza nieistotna.
3. **"Gdzie mieszka prog dedupa?"** - dedup.md: brand_config (AGS,
   cm_dup_threshold) = 0.57 (kalibracja 20/07 na zywym korpusie; fallback 0.85
   w kodzie); strojenie SQL-em na brand_config, bo /set nie zna klucza
   (allowlista n8n w backlogu). Porownanie na master_theme, nie canonicalu.

## 3. Decyzje redakcyjne (do wiadomosci, nie do akceptacji)

- Archiwum = PELNY zrzut starego SYSTEM_DATAFLOW (nie tylko G/H): sekcje
  A-F tez byly datowanym dziennikiem ("LIVE 02/07" itd.) i ich tresc zostala
  skompilowana do komponentow; zrzut w calosci = zero ryzyka zgubienia
  szczegolu przy wycinaniu.
- Stan naprawy Researchera (fix 3f97d90 na build/researcher-fix, czeka rebuild)
  opisany w researcher.md jako stan obecny z odsylaczem do briefu naprawczego -
  sesja czytajaca dokumentacje nie moze myslec, ze web_search dziala.
- n8n-transport.md zbiera zasady PUT/backup/reaktywacji w jednym miejscu -
  dotad byly rozsiane po pamieci trwalej i raportach.

## 4. Udzial Tomasza (jedno przejrzenie + push)

1. Przejrzec strukture (wystarczy SYSTEM_DATAFLOW.md + 1-2 pliki komponentowe).
2. Push (PowerShell):
   `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\build-dokumentacja" push origin build/dokumentacja`
3. Merge do sb-work (docs-only, konflikt malo prawdopodobny) - integrator albo
   wprost:
   `git -C "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\sb-work" merge build/dokumentacja`
   (UWAGA: masterprompt i brief sa dotkniete takze przez inne sesje - przy
   konflikcie brac obie zmiany.)

## 5. Otwarte (poza zakresem tego buildu)

- Diagram graficzny calosci (cel sprzedazowy) - TODO w SYSTEM_DATAFLOW pkt 5.
- pg_dump schema-only pozostalych tabel bazowych (TODO w SCHEMA).
- Egzekwowanie kanonu pkt 6a (dokumentacja w TYM SAMYM commicie co zmiana
  zachowania) - od teraz kazdy budowniczy aktualizuje takze wlasciwy plik
  w docs/komponenty/.
