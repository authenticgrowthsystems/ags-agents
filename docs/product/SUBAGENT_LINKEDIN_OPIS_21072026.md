# SUBAGENT LINKEDIN - pelny opis stanowiska i stanu (21/07/2026 wieczor)

Blizniak Subagenta X (te same warstwy, ta sama baza, ten sam kontrakt 8 obowiazkow -
czytaj SUBAGENT_X_OPIS_21072026.md sekcje 0-1; tu tylko ROZNICE). To wlasnie jest
dowod recepty: nowy kanal = te same organy, inna taktyka i inny adapter publikacji.

## 0. Specyfika platformy

Sukces LinkedIn = komentarze w pierwszych 60-90 min + czas czytania. Kadencja: pon-pt
1 post (okno profilu prywatnego ok. 16:00-18:00), sobota nic, NIEDZIELA ARTYKUL -
robi go TOMASZ RECZNIE (kanon 19/07: planner nie planuje niedzieli, dopoki CM nie umie
czytac swiata). Profil prywatny Tomasza publikuje WYLACZNIE PO ANGIELSKU (straznik
jezyka w stagingu od 21/07). Strony firmowe (AGS/TNM/RDC) = osobne cele, czekaja na
tokeny po App 2 CMA.

## 1. ZROBIONE (stan LIVE 21/07 wieczor)

| Obowiazek | Co dziala | Jak zrealizowane (warstwa) |
|---|---|---|
| O1 Publikacja | tryb GOTOWCA (publish_mode='draft', decyzja po incydencie 20/07): materialy planuja sie normalnie (sloty, karty, zatwierdzanie), a w slocie dostajesz do rozmowy PELNY zestaw: naglowek + czysta wklejka + grafika; wklejasz recznie, domykasz komenda `wklejone <id>` (wpis do ksiegi published_posts) | Python: worker._send_manual_paste_kits + route _wklejone_route (naprawa 21/07, czeka na rebuild); DB: post_queue status 'held' |
| O1 Publikacja API (uspiona) | adapter Subagent LinkedIn Publisher istnieje i dziala (post 20/07 opublikowany przez API) - WYLACZONY, bo ignorowal sloty; wraca po naprawie trybu | n8n: Uv9TvUMI8MRSqCLz (OAuth token profilu, wygasa ~01/09/2026) |
| O2 Tworzenie | identycznie jak X (Voice Bible, TRUTH_GUARD, straznik jezyka EN, dedup embedingowy) + rownolegly ODPOWIEDNIK PL do przegladu (Tomasz czyta po polsku, publikuje sie EN) | Python: generate/channels - wspolne organy |
| O3 Komentarze | comment-radar ze zrzutow dziala TAK SAMO jak na X (per autor, czysta wklejka, guziki); rozpoznaje DM vs post z feedu i proponuje wlasciwy gatunek odpowiedzi | Python: engagement (wspolny organ, routing per active_agent) |
| O5 Metryki | import xlsx z eksportu LinkedIn (AggregateAnalytics przez Telegram -> DB), sekcja PROFIL w raportach (wyswietlenia/reakcje/obserwujacy 7d); kolektor API GOTOWY w kodzie (stats_mode member_api/org_api) - czeka WYLACZNIE na scope po review App 2 CMA (poza nasza kontrola) | Python: metrics_import + reports; n8n: galaz document_xlsx; DB: channel_metrics_daily + engagement_metrics |
| O6 Relacje | wspolny CRM z X (contacts + stadium + engagement_log) - dzis dziala na zrzutach LinkedIn (intake Djordje/Dana 21/07 = zywy dowod) | wspolne organy, DDL 026 |
| O8 Rozmowa | swobodny dialog per konto, raport dzienny/tygodniowy, zgloszenia luk kadencji | wspolne organy |

## 2. DO ZROBIENIA

| Brak | Co da | Gdzie bedzie | Status |
|---|---|---|---|
| Pamiec watku + menu intencji + dedup osob | jak X - wspolna naprawa | build/intake-ux | **W BUDOWIE** |
| Scope metryk API (memberCreatorPostAnalytics) | metryki bez xlsx | App 2 CMA review | POZA NASZA KONTROLA - czekamy |
| Powrot publikacji API z poszanowaniem slotow | zero recznego wklejania post. pon-pt | wymaga: Scheduler umie LinkedIn ALBO adapter czyta scheduled_for; decyzja architektoniczna przy najblizszym buildzie publikacji | zaparkowane (gotowiec dziala) |
| Strony firmowe AGS/TNM/RDC | multi-konto LinkedIn | tokeny po App 2 CMA + routing multi-cel (T7) | czeka na CMA |
| Karuzele/dokumenty PDF | najwyzszy dwell time na LI | generacja PDF (organ grafiki) + gotowiec | niezaczete |
| Artykul niedzielny - podklad "CM czyta swiat" | Tomasz pisze artykul na gotowym podkladzie z tezami i linkami | sunday_brief (mechanizm LIVE, noga researchowa naprawiona 20/07; dowod sobota 26/07) | W TESCIE |
| Token OAuth profilu | wygasa ~01/09/2026 - odnowic PRZED | Token Generator (procedura znana) | pilnowac terminu |

## 3. Pamiec, tokeny, tryb samodzielny

Identycznie jak Subagent X (sekcje 4-5 tamtego dokumentu) - wspolna baza, wspolny
ledger kosztow, wspolne mechanizmy nauki. Roznica kosztowa: LinkedIn NIE ma platnych
odczytow API (xlsx darmowy, scope po CMA tez), wiec caly koszt kanalu = generacja
tresci + rozmowa.

## 4. Recepta na kolejne kanaly (IG, FB, TikTok, YT)

Nowy subagent kanalu = 4 kroki, zadnego nowego frameworku:
1. **Wiersz w channels** (brand, kanal, okna, jezyk, publish_mode, voice_note) -
   menu /agents buduje sie samo z bazy.
2. **Adapter publikacji w n8n** (webhook wg kontraktu Publishera: content+media in,
   callback z ksiega out) ALBO tryb gotowca od dnia 1 (dziala bez zadnego API!).
3. **Taktyka platformy** w prompcie subagenta (kadencja, formaty, algorytm) - sekcja
   w brand_config, nie kod.
4. **Metryki**: kolektor per API kanalu albo import pliku (wzorzec xlsx juz jest).
Wszystko inne (plan, karty, CRM, decyzje, nauka, raporty, rozmowa) to WSPOLNE ORGANY -
dostaje je kazdy nowy kanal za darmo. Instagram/Facebook wymagaja dodatkowo organu
multimediow (wideo/karuzele) - patrz SPEC_VISUAL_AGENT (zamrozony do decyzji).
