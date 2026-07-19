# BRIEF BUILDU: CM CZYTA SWIAT - niedzielny artykul (19072026) - budowniczy: BE-SWIAT

Wywolanie sesji (Opus 4.8, nowe okno Cowork):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_CM_CZYTA_SWIAT_19072026.md zbuduj`

## 1. CO budujemy (definition of done)

KANON 19/07 (Tomasz): niedzielny artykul LinkedIn = insight tygodnia ze swiata AI; robi go
Tomasz RECZNIE, a planer ma zakaz planowania niedzieli - DOPOKI CM nie umie sam czytac swiata.
Ten build = zdolnosc czytania swiata: cotygodniowy digest tego, co sie dzialo w AI, jako
PODKLAD pod artykul (draft do recznej obrobki Tomasza w sobote, NIE auto-publikacja).

Mechanizm (Pareto, na istniejacych organach):
- SOBOTA rano (tick w petli workera, wzorzec weekly_metrics_reminder): CM zleca Researcherowi
  (POST /request na ags-researcher:8088, kontrakt juz istnieje - CM commissions research)
  badanie "najwazniejsze wydarzenia/dyskusje AI ostatnich 7 dni dla ICP solo-founderow"
  (tier medium - CM ma cap <=medium).
- Wynik + schowek tygodnia (inspirations, w tym zlapane posty innych z Idea Bota) + top
  publikacje tygodnia -> synteza (Sonnet): 3 kandydackie tezy artykulu z twardymi liczbami
  i zrodlami.
- SOBOTA ~12:00: wiadomosc do Tomasza: "Podklad pod niedzielny artykul" (tezy + fakty +
  linki zrodel) + przypomnienie o materialach wlasnych. ZERO wpisu do planu/kolejki.

DoD:
- [ ] Sobotni tick wysyla podklad (tap-test: wywolanie reczne "podklad na niedziele")
- [ ] Draft NIE wchodzi do content_items ani post_queue (kanon: niedziela = recznie)
- [ ] Zrodla w podkladzie linkowane (regula prawdy - zero niepodpartych faktow)

## 2. KONTRAKT

- Researcher /request (RESEARCHER_URL w config; wzorzec: research.py w cm-agent),
  inspirations (odczyt), published_posts (top tygodnia), sendMessage (conversation._tg).
- Zero DDL (wyniki Researchera ladowane jego wlasnym obiegiem), zero n8n.
- Stan anty-dublowy w brand_config (wzorzec _state_get/_state_set, klucz cm_sunday_brief).

## 3. Czego NIE dotykac

Planner (zakaz niedzieli ZOSTAJE), gap-filler, bramka tematow, publikacja.

## 4. Stan zastany

Researcher LIVE (5 zrodel, cost-cascade, cap medium dla CM); Idea Bot lapie cudze posty
do inspirations; kanon niedzielny w planner._cadence_text + proactive._expected (19/07).

## 5. Udzial Tomasza

Push + rebuild + tap-test podkladu; w sobote: obrobka podkladu w artykul (jego czesc kanonu).

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_czyta_swiat.md + masterprompt + pamiec + STATUS tu.

STATUS = READY (brief 19/07, tryb awaryjny - handoff na Opus 4.8)
