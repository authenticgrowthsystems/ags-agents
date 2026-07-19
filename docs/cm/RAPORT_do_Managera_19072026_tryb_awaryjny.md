# RAPORT do Managera: TRYB AWARYJNY - handoff Fable 5 -> Opus 4.8 (19/07/2026 ~22:00)

Od: BE (sesja dnia 19/07). Kontekst: Tomasz zarzadzil tryb awaryjny - pelen handoff tak,
by budowniczowie na Opusie 4.8 konczyli robote po maksymalnie 2 promptach na build.

## 1. Co jest ZBUDOWANE i LIVE (zweryfikowane tapami + read-only, dzis)

Pelna lista: RAPORT_do_Managera_19072026_zamkniecie_dnia.md. Skrot: kanon publikacji w kodzie
(zatwierdzone zawsze / niezatwierdzone nigdy; _emergency_promote usuniety), metryki LinkedIn
(import xlsx E2E + PROFIL w raportach), decyzje guzikami + petla nauki (DDL 024, semi-auto
za tapem), bramka tematow + plan tygodnia ZATWIERDZONY (jutro od 13:50 wychodzi 8 publikacji),
ludzkie minuty, karty na dole, dokumenty/xlsx przez Telegram, gpt-image-2 + guzik 📋 Prompt,
straznik dlugich X, guard crona planera, kanon niedzielny, Voice Bible SSOT (voice_dna_core
v1 + mirror + instrukcja dla przegladarkowego CM), billing kolektora X (saldo $6.96, cap $20).

## 2. Kolejka budowniczych (masterprompt sekcja 4b - kazdy = nowe okno Opus 4.8, 2 prompty)

1. BE-KOLEKTOR - kolektor metryk X Owned Reads (READY-BILLING; najpilniejsze: okno 30 dni
   prywatnych metryk ucieka codziennie). DDL 025.
2. BE-DEDUP - twarda bramka duplikacji tezy przy generacji (embedding vs published; incydent
   "Orkiestracja" = dubel tezy z 11/07).
3. BE-PORZADKI - deterministyczny route komend konfiguracyjnych (incydent "Zrobione" bez
   narzedzia) + kasowanie wierszy pq przy odrzuceniu karty + SQL sierot.
4. BE-SWIAT - sobotni podklad niedzielnego artykulu (Researcher digest tygodnia AI; artykul
   dalej pisze Tomasz recznie - kanon).

Kazdy brief: self-contained, z dowodami incydentow, kontraktem wpiecia, guardrailami,
udzialem Tomasza i obowiazkowym zamknieciem sesji. Slowniczek tabel i verify-SQL w
masterprompcie (sekcja 2b) - nastepca NIE zgaduje kolumn.

## 3. Ryzyka handoffu i mitygacje

- Dwie sesje na sb-work JEDNOCZESNIE = konflikt (protokol: sekwencyjnie; kolejnosc w 4b).
- Opus 4.8 MUSI czytac oba pliki wywolania PRZED dotknieciem czegokolwiek (protokol pkt 3).
- Wszystko na dzis jest LIVE po 4 rebuildach - budowniczowie zaczynaja od czystego stanu;
  jedyne czekajace u Tomasza: zaden SQL, zaden rebuild (stan czysty, branch = origin).
- Publikacje tygodnia ida SAME (zatwierdzone, slot gate, Scheduler) - zadna sesja nie jest
  potrzebna do jutrzejszych postow.

## 4. Prosba do Managera

Priorytety kolejki 4b potwierdzic lub przestawic; po kazdym buildzie budowniczy melduje
raportem per krok (protokol). Rytm zostaje: brief -> build -> dowod -> raport.
