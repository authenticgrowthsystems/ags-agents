# Komponent: PLANNER (plan tygodnia + bramka tematow + gap-filler)

## Co robi

Buduje proaktywny plan tygodnia dla marki: lista materialow (content_items status
'proposed') z tematem, celem i slotem. Tomasz przeglada plan guzikami i zatwierdza
JEDNA decyzja (model jednego zatwierdzenia); zatwierdzone pozycje ida do generacji.
Gap-filler wykrywa luki kadencji dzis/jutro i proponuje wypelnienie na tych samych
zasadach co planner (te same zrodla, ta sama bramka, ten sam budzet meta).

Uruchamianie: cron n8n niedziela 20:15 (POST /plan) + na zadanie narzedziem
`plan_build` w rozmowie CM ("zaplanuj tydzien").

## Wejscia-wyjscia i tabele

- Wejscia: `brand_strategy` (filary, ICP - PIERWSZE zrodlo tematow), `inspirations`
  (schowek - pomocniczo), `content_items` (antydubel + budzet meta z 7 dni),
  `channels` (kadencja, okna, statusy celow).
- Wyjscia: `content_items` status 'proposed' (`scheduled_for` = CZYSTY slot planu,
  bez humanizacji), wiadomosc planu na Telegram z guzikami przegladu (plannav),
  po zatwierdzeniu status przechodzi dalej w pipeline (patrz kolejka-publikacja.md).
- Zarys miesiaca: `_month_outline` / `_save_month_outline` (brand_config).

## Bramka tematow (kanon 19/07)

1. PROMPT: zrodla w obowiazkowej kolejnosci (1. filary marki, 2. problemy ICP,
   3. schowek pomocniczo); ostatnie publikacje ZDEGRADOWANE do roli antydubla
   (nie inspiracji - to byla petla autoreferencyjna z incydentu 13-19/07);
   licznik "zostalo X meta na ten tydzien".
2. TWARDY FILTR za promptem (LLM bywa gluchy na limity): `_meta_like` - regex PL+EN
   (kadencja/sloty/kolejka/luki/cadence/queue/autopilot/subagent + para
   "moj|nasz|my|our" x "system|agent|bot|pipeline"). Budzet META_MAX_WEEK=1
   liczony z content_items (7 dni, bez rejected/archived), WSPOLNY dla plannera
   i gap-fillera.
3. LIMIT PLANU: `_enforce_plan_cap` - max 20 proposed; nadwyzka wypychana od KONCA
   tygodnia (sort po scheduled_for, NIE created_at) -> archived.
4. JAWNOSC (REGULA PRAWDY): kazde wyjscie planera melduje; odrzucone tematy
   raportowane z powodem ([meta]/[cel]/[slot]); pusty plan NIGDY nie milczy.

Niedziela LinkedIn: artykul niedzielny = RECZNY Tomasza (podklad dostarcza
CM czyta swiat - patrz researcher.md); harmonogram LI pilnowany w slots (pn-pt post,
sobota nic, niedziela artykul reczny).

## Konfiguracja

- `brand_strategy` per brand: target_audience, content_pillars, core_topics.
- `channels.config`: posts_per_day (kadencja), publish_windows (okna),
  follower_count (dobor formatu).
- Stale w kodzie: PLAN_CAP=20, META_MAX_WEEK=1 (planner.py).
- `brand_config`: admin_chat_ids (dokad idzie plan).

## Punkty zaczepienia w kodzie

- `cm-agent/app/planner.py`: `build_plan` (glowna budowa), `_meta_like` (twardy
  filtr), `_meta_week_count`, `_enforce_plan_cap`, `plan_text`/`plan_items`
  (podglad), `handle_nav` (guziki plannav), `approve_plan`, `edit_plan_item`,
  `_reangle_theme` (Inny kat pozycji planu).
- `cm-agent/app/proactive.py`: `check_gaps`, `_propose_for_gap` (gap-filler),
  `morning_nudge` (odprawa 09:00), `handle_agent_requests` (wnioski subagentow),
  `tick` (wpiecie w petle workera).
- `cm-agent/app/worker.py`: endpointy `POST /plan`, `POST /plannav`.
- Rozmowa CM: narzedzia `plan_build`, `plan_approve`, `plan_edit`
  (conversation.py `_plan_build_async`, `_plan_approve`, `_plan_edit`).

## Kanony ktore go dotycza

- Kanon publikacji 19/07: plan proponuje, NIGDY sam nie zatwierdza; zatwierdzenie
  = wylacznie tap Tomasza (przeglad plannav albo plan_approve z wyjatkami).
- Meta-posty o wlasnym systemie: max 1/tydzien (dowod z metryk: meta 2-44 wysw.
  vs narracja 2331).
- REGULA PRAWDY: zero cichych ciec i cichych pustek.
- Decyzje Tomasza = guziki.

## Znane pulapki

- Cap ciecia sortowal kiedys po created_at i scinal POCZATEK tygodnia (incydent:
  poniedzialek bez X) - poprawne ciecie od NAJDALSZYCH slotow.
- Lista ostatnich publikacji w prompcie NIE wystarcza jako antydubel - LLM ja
  ignoruje; twarda bramka embedding jest OSOBNYM komponentem (dedup.md).
- Plan przed bramka potrafil spuchnac do 78 pozycji (incydent 13-19/07) -
  cap 20 jest twardy.
- `scheduled_for` w content_items to czysty slot planu; ludzkie minuty dostaje
  dopiero post_queue (roznica ZAMIERZONA - patrz kolejka-publikacja.md).
