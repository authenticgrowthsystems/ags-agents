# CM UX - feedback Tomasza 05/07/2026 wieczor (po master promptcie #71 i floodzie planera)

> **STATUS 05/07 ~22:00: S1-S4 WDROZONE** (modul cm-agent/app/matreview.py + zmiany conversation/
> hitl/worker + galaz n8n mat* -> POST /matnav, HITL 239 wezlow, aktywowany). Decyzja Tomasza
> guzikami: wszystko jednego wieczora. Szczegoly implementacji ponizej w sekcjach.

Zrodlo: rozmowa 05/07 ~21:00, doslowne wymagania. Status: SPEC do wdrozenia (kolejnosc = decyzja
Tomasza guzikami). Kontekst: plannav (karty planu z ⬅️➡️) juz istnieje dla POZYCJI PLANU;
ponizsze dotyczy (a) intake materialu z rozmowy, (b) przegladu WYGENEROWANYCH materialow,
(c) przypomnien niedzielnych.

## S1. Kosmetyka listy "Podobne publikacje" (dedup z content_memory)
Tytuly podobnych publikacji sa uciete w pol slowa ("I buil"). MA BYC: trojkropek "..." na koncu
kazdej pozycji. Guziki do przegladania NIE sa potrzebne - lista jest czysto informacyjna.

## S2. Decyzja przy zapisie materialu z rozmowy (intake)
Po tym jak CM sprawdzi dedup i chce zapisac material z master promptu / rozmowy, Tomasz MUSI
dostac decyzje guzikami zamiast samego zapisu:
- [Do kolejki] - material laduje w schowku/kolejce, planer go zobaczy;
- [Teraz/dzis] - generacja od razu, publikacja dzis (najblizszy slot);
- [Odrzuc] - material nieistotny, nie zapisujemy.
Czyli: waznosc materialu + timing okresla Tomasz jednym tapnieciem w momencie intake.

## S3. Przeglad wygenerowanych materialow = KARTY z przewijaniem, nie seria wiadomosci
Flood 05/07 20:33 (kilkanascie osobnych wiadomosci "CM: nowy material" z niedzielnego planera)
= NIE TAK. MA BYC: jedna wiadomosc-karta na material + strzalki ⬅️➡️ do przewijania calej paczki
+ na karcie decyzje (Zatwierdz / Odrzuc / inny kat / model). Wzorzec juz istnieje: plannav
(rodzina callbackow, karta w miejscu edytowana) - rozszerzyc na content_items w needs_approval
(paczka = materialy z tego samego planu/dnia).

## S4. Przypomnienia niedzielne + autonomiczny fallback (rozszerzenie kanonu 11c)
- Jesli paczka z niedzielnego planera czeka bez przegladu: przypomnienia "sprawdz i zatwierdz"
  co 15 minut, NAJPOZNIEJ do 23:00 w niedziele (start okna do decyzji: rekomendacja BE = 21:30).
- Jesli do 23:00 Tomasz nie przejrzy: CM SAM wybiera material do wstepnej publikacji
  (np. poniedzialkowy slot), oznacza jako wybor autonomiczny i INFORMUJE na bocie alertowym
  (bot #2). To nie jest stan awaryjny 24h (kanon 11c) - to szybszy, niedzielny wariant dla
  paczki planera; 11c zostaje bez zmian dla zatwierdzonych materialow ze slotem.

## Uwagi wdrozeniowe (BE)
- S1: cm-agent (formatowanie listy podobnych) - zmiana 1-liniowa.
- S2: nowa rodzina callbackow (np. matdec:) w HITL + galaz n8n (AP-301: typeVersion z dzialajacego
  wezla!) + handler w cm-agent (status/scheduled_for).
- S3: reuse plannav: nowa rodzina (np. matnav:) albo rozszerzenie plannav o tryb 'materialy';
  wymaga grupowania paczki (plan_id/dzien) i tlumienia pojedynczych powiadomien per material
  gdy material nalezy do paczki.
- S4: petla w cm-agent (reports/planner cron juz istnieje; dodac harmonogram niedzielny 21:30-23:00
  co 15 min + fallback 23:00) + log AUTONOMOUS_DECISION + alert bot #2.
