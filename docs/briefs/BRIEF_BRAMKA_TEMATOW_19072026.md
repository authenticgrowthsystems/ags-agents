# BRIEF BUILDU: BRAMKA TEMATOW + NOWY PLAN (19072026)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_BRAMKA_TEMATOW_19072026.md zbuduj`
(Build wykonany w sesji dnia 19/07 - plan dnia krok [4].)

## 1. CO budujemy (definition of done)

Koniec petli autoreferencyjnej (incydent 13-19/07): planner i gap-filler przestaja karmic sie
ostatnimi publikacjami i wlasnym systemem. Zrodla tematow = FILARY + ICP (schowek pomocniczo);
meta-tematy o naszym systemie publikacji max 1/tydzien (prompt + TWARDY filtr w kodzie);
limit planu 20 proposed (nadwyzka -> archiwum). Potem: nowy plan z Tomaszem przez CM.

DoD:
- [ ] build_plan: prompt z kolejnoscia zrodel + bramka meta + twardy filtr _meta_like + _enforce_plan_cap
- [ ] _propose_for_gap: te same zrodla + bramka (budzet meta wspoldzielony przez _meta_week_count)
- [ ] Heurystyka _meta_like: 6/6 tematow z incydentu lapana, 0 falszywych trafien na normalnych
- [ ] Po deployu: Tomasz mowi CM "zaplanuj tydzien" -> plan z bramka (max 20, meta <=1)

## 2. KONTRAKT wpiecia w szyne

- planner.py: META_MAX_WEEK=1, PLAN_CAP=20, _meta_like/_meta_week_count/_enforce_plan_cap;
  komunikat planu raportuje odrzucenia bramki i archiwizacje nadwyzki (jawnosc, zero cichych ciec).
- proactive.py (_propose_for_gap): import bramki z plannera (jeden budzet tygodniowy).
- Zero nowych tabel/endpointow/n8n.

## 3. Czego NIE dotykac

Kadencja i sloty (kanon 11d), plan_approve/plan_edit, intake guziki - bez zmian.

## 4. Zaleznosci i stan zastany

Dowod skutecznosci formatow: docs/evidence/screeny_13-19_07/ANALIZA_DOWODOW_19072026.md
(meta 2-44 wysw. vs narracja 2331). brand_strategy (filary/ICP) w brand. Incydent: plan 78 pozycji.

## 5. Udzial Tomasza

Po deployu paczki: napisac do CM "zaplanuj tydzien", przejrzec plan guzikami (max 20 pozycji),
zatwierdzic. To zamyka krok [4].

## 6. Zamkniecie sesji (OBOWIAZKOWE)

STATUS = DONE-CODE (19/07): bramka w plannerze i gap-fillerze, heurystyka przetestowana
(6/6 incydent, 0 false-positive). CZEKA: deploy + "zaplanuj tydzien" z Tomaszem.
Raport: docs/cm/RAPORT_do_Managera_19072026_bramka_tematow.md
