# RAPORT do AGS BUILD ENGINEER - stan po nocy 21/22.07.2026 (~00:40)

Od: BE-integrator (okno napraw publikacji + integracji buildow 20-21/07).
Serwer: claude/silly-blackwell-dfc32d @ 5a812d0, cm-agent przebudowany, /health ok.
CZYTAJ PRZED KODEM: docs/komponenty/ (kanon DOKUMENTACJA ZYJE) + ten raport.

## 1. CO JEST LIVE (dzisiejsze wdrozenia, chronologicznie)

1. **Naprawa incydentu publikacji 20/07** (raport: docs/ops/INCYDENT_PUBLIKACJI_20072026.md):
   AGS/x publish_mode='post_queue' (Scheduler, sloty, ludzkie minuty), AGS/linkedin='draft'
   (gotowce), 10 wierszy PL->EN, straznik jezyka w stage_variant. AP-307 w anti-patterns.
2. **Paczka wieczorna 20/07**: Agent Sprzedazy L1 (DDL 026+027, tap-testy 5/5 PASS,
   pierwszy prospekt Adamietz w lejku, gotowiec mailowy 'proposed'), DFY Retencja
   (6 tierow active PL+EN), syntezy researchu sprzedazowego, engagement-CRM.
   Hotfix sprzedawcy: prospect research tier medium + _TIER_MODEL (model_tier=NAZWY modeli).
3. **Naprawa incydentu 21/07 "nic nie wyszlo"** (posty WYSZLY - klamala ksiega):
   patch n8n scheduler-media-ledger-21072026.cjs na OBA workflow: upload mediow X
   multipart BODY (kontrakt docs.x.com; query-params NIGDY nie dzialaly, INIT 400)
   + Mark Published per-wiersz (published_posts + agent_messages + domkniecie ci).
   W kodzie: _pub_media (propozycje wizualne nie ida do kolejki), gotowiec held z TRESCIA
   do rozmowy + route `wklejone <id>`, ZWIS liczony od slotu. SQL sierot wykonany.
4. **INTAKE-UX** (build/intake-ux, raport docs/cm/RAPORT_do_Managera_21072026_intake_ux.md):
   pamiec watku subagentow (_sub_record), menu intencji po wrzutce (intent_menu),
   dedup osob (clean_author, 1 crm_tier/24h), markdown->HTML; bonus: naprawiony martwy
   guzik "Inny kat" (TRUTH_GUARD import).
5. **Poprawki nocne 22/07** (uwagi Tomasza 00:02-00:05, commity 0614116+5a812d0):
   karta zatwierdzenia = kopia PL (review_pl) + guziki [🎨 Generuj grafike][➕ Dopnij
   zdjecie] (istniejace akcje matnav gen/madd); straznik preambuly wariantu
   (generate._strip_meta_preamble; wiersz 280 wyczyszczony SQL-em na zywo);
   zgloszenia decyzji PO LUDZKU + HTML bold (decisions._TYPE_LABEL, zero [typu]/#id
   w tekscie); NOWY typ 'stale_outreach' = gotowce sprzedawcy POZA maszyneria
   komentarzy (guziki Wyslalem/Czekam/Pokaz tresc/Rezygnuje; "Pokaz tresc" = czysta
   wklejka BEZ intake'u).

## 2. DOWODY, KTORE PRZYJDA SAME (22/07) - PILNUJ

- **16:11** publikacja X wiersza 184 (media z file_id) = PIERWSZY zywy dowod
  multipart-uploadu grafik. Jak brak grafiki -> media_errors w egzekucji Schedulera.
- **~16:00-16:10** gotowiec LinkedIn (wiersz 280, po czyszczeniu zaczyna sie od
  "Imagine your sales agent...") - ma przyjsc do rozmowy z PELNA trescia; domkniecie
  `wklejone 280`.
- Przypomnienie stale_outreach o mailu Adamietz w nowym formacie (po telefonie rodziny).
- Tap-testy DoD INTAKE-UX a-d (brief sekcja 2) - NA SWIEZO z Tomaszem.

## 3. MINY I BACKLOG (nie nadepnac)

- **Callback Subagent X Publisher** oznacza published WSZYSTKIE wiersze materialu
  (WHERE content_item_id bez pq.id) - adapter NIEUZYWANY po zmianie trybow, ale naprawa
  OBOWIAZKOWA przed jakimkolwiek powrotem webhook (masterprompt sekcja 6).
- Token OAuth LinkedIn wygasa ~01/09/2026 - odnowic przed.
- sales.py: markdown ** w odpowiedziach (INTAKE-UX naprawil subagentow, sprzedawca poza
  zakresem briefu - mala poprawka przy nastepnym dotknieciu sales.py).
- Raport kosztow LLM per agent/tydzien z cm_tasks (ledger juz liczy; rachunki 12-15 EUR
  - Tomasz chce widziec na co ida tokeny). Male, wartosciowe.
- /set allowlist: cm_dup_threshold (patch n8n czeka).
- Stare stuby contacts scalic SQL-em przy najblizszym dublu (nota INTAKE-UX).

## 4. KOLEJKA STRATEGICZNA (kolejnosc zatwierdzona)

1. Tap-testy INTAKE-UX + dowody publikacji (sekcja 2).
2. **BE-LACZNIK** (po DONE tap-testow): brief z docs/product/LACZNIK_SYNCHRONIZACYJNY_
   21072026.md - RAPORT PRACY (parser bez LLM) + stan gry przez LINK Notion + przerobka
   masterpromptow czatowych OD TOMASZA (dostarczy przy starcie buildu).
3. Sprzedaz (nie build!): telefon rodziny -> mail Adamietz -> pipeline_move; pierwsza
   wysylka oferty DFY; decyzje D1-D5 z REKOMENDACJE_SPRZEDAZ u Managera (Stripe dzis!).
4. Opisy produktowe subagentow: docs/product/SUBAGENT_X_OPIS_21072026.md + LINKEDIN
   (warstwy, recepta na nowe kanaly) - wsad pod SNAPSHOT i sprzedaz.

## 5. KANONY SWIEZE (nadpisuja starsze nawyki)

- Warstwy (Tomasz 21/07): mozg/serce/kregoslup STALE, interfejs WYMIENNY; n8n = transport
  bez LLM; publikacja NIE zuzywa tokenow.
- Zgloszenia do Tomasza: po ludzku, wytluszczone, zero znacznikow programu; gatunek
  zrodla (research strony / profil / DM / komentarz) determinuje guziki.
- Research: critical NIGDY przez API (~18 PLN) - recznie na abonamentach; API max medium.
- Slowo "paragon" w tekstach bota -> "potwierdzenie" (feedback_potwierdzenie_nie_paragon).

Pelna historia dnia: git log 68d96d2..5a812d0 + docs/cm/RAPORT_do_Managera_20072026_
integracja_wieczorna.md. Pamiec: project_publikacja_kanon_19072026 (incydenty),
project_intake_ux_build, project_lacznik_synchronizacyjny, project_agent_sprzedazy_build.
