# Subagent kanalu - definicja pakietu (v1, 06/07/2026)

**Pytanie-kotwica (Tomasz 06/07): "Jestes klientem. Kupiles subagenta LinkedIn albo X albo IG.
Co dostajesz w cenie, jakie funkcjonalnosci?"** Ten dokument = odpowiedz i fundament pod cennik
(pricing_tiers), task #70 (pakiet sprzedawalnosci) i backlog produktowy. Warianty wg kanonu
[[project_subagent_object_toggle]]: STANDALONE (wlasny bot Telegram + petla, kupowalny solo)
albo SUPERVISED (pod Content Managerem, ktory nadzoruje wiele kanalow).

## 1. CO JEST W CENIE DZIS (LIVE, zweryfikowane na produkcji)

**Tresc:**
- generacja materialow w glosie marki (Voice Bible klienta + anty-slop + kontrola jezyka
  komunikacji i PUBLIKACJI per cel, np. X=EN, LinkedIn PL);
- kontrola zgodnosci (compliance canon) kazdego tekstu przed publikacja;
- pamiec publikacji cross-channel (pgvector): antydubel przy kazdym nowym temacie + reuse
  archiwum przy podpieciu nowego kanalu.

**Przeplyw i kontrola (czlowiek zawsze w petli):**
- zatwierdzanie 1 tapnieciem na Telegramie: KARTY z przewijaniem ⬅️➡️, decyzje per material
  (Zatwierdz / Na koniec kolejki / Odrzuc / Inny kat) + zbiorczo; zero floodu wiadomosci;
- intake pomyslu z rozmowy: guziki [Do kolejki]/[Dzis]/[Odrzuc];
- **podzial rol: klient zatwierdza TRESC, system proponuje KIEDY** - sloty przydzielane
  automatycznie wg okien publikacji i kadencji (nowosc 06/07);
- okna publikacji per kanal w konfiguracji (zmienialne z czatu), kadencja kanoniczna per kanal;
- stan awaryjny: cisza operatora 24h = publikacja najlepszej opcji w slocie + log + alert
  (wylaczalne per cel); niedzielny wariant: przypomnienia co 15 min + fallback 23:00.

**Planowanie:**
- proaktywny planer tygodnia (kadencja + schowek pomyslow + archiwum + strategia marki),
  plan zatwierdzany kartami albo rozmowa ("wywal 3", "przesun 2 na czwartek 14:00");
- schowek pomyslow (glos/tekst/foto przez bota) zasilajacy planer.

**Publikacja:**
- X: pelny automat (scheduler co minute, OAuth1);
- LinkedIn: publikacja postow przez API (token member) / tryb draft;
- sloty co do minuty, strefa czasowa klienta.

**Rozmowa i raporty:**
- rozmowny subagent na Telegramie (menu /agents): kolejka, co opublikowal, decyzje, metryki;
- rozmowny Content Manager (nadzorca) na najwyzszym modelu: strategia, plan, korekty;
- raporty dzienne 08:00 i tygodniowe (publikacje, metryki, decyzje autonomiczne z uzasadnieniem)
  na osobnym bocie alertowym;
- decyzje autonomiczne ZAWSZE logowane i raportowane.

**Fundament (niewidoczny, ale sprzedajacy):**
- SSOT PostgreSQL (49+ tabel, backup nocny, relacje) + OPCJONALNY mirror Notion one-way
  (flaga per marka; klient bez Notion nie placi kosztu);
- klucze API wylacznie w sejfie DB; wybor modelu AI per zadanie (koszt pod kontrola, guziki 🎚).

## 2. CZEGO JESZCZE NIE MA W CENIE (mapa brakow = backlog produktowy, kolejnosc Tomasza 06/07)
| # | Brak | Stan | Uwagi |
|---|---|---|---|
| 1 | ~~Sloty+okna: CM decyduje KIEDY~~ | **ZBUDOWANE 06/07** (slots.py) | czeka deploy |
| 2 | Multimedia: WLASNE zdjecie z Telegrama w poscie na X i LINKEDIN | **ZBUDOWANE 06/07** (etap 1 X: v2 chunked upload w obu publisherach; etap 1b LinkedIn: assets registerUpload -> post IMAGE; UX: auto-podglad pod karta, ➕/🗑 Media, sugestia wizualu per material) | zostalo: generowane grafiki (etap 2, kontrakt higgsfield, ZDJECIA REFERENCYJNE Tomasza), wideo/animacje (etap 3) |
| 3 | Semi-auto (kanon 10): CM sam zaczepia | **ZBUDOWANE 06/07** (odprawa poranna + luki kadencji z propozycjami; cm_work_mode=semi) | rozbudowa zaczepek iteracyjnie |
| 4 | Artykul-gotowiec LinkedIn: formatowanie + grafiki + checklist | BRAK | FAKT: LinkedIn API nie publikuje artykulow - gotowiec do wklejenia |
| 5 | LinkedIn multi-kanal (strony AGS/TNM/RDC + profil) pod jednym subagentem | ARCHITEKTURA JEST (cele+toggle), tokeny stron po review App 2 + RLS | |
| 6 | Zywe metryki profilu ("co sie dzieje na profilu") | LinkedIn: po review App 2 (kolektor gotowy); X: platny tier -> wpis reczny | |
| 7 | Instalator-kreator u klienta (kanon 11b) | playbook v2 jest; kreator klikany = backlog przed uwolnieniem sprzedazy | |
| 8 | Subagent-pracownik: luka w kadencji -> subagent SAM wola CM o tresc | **ZBUDOWANE 06/07** (agent_messages + propozycje z antydublem + intake guziki); czesc (d) ICP-hunting = BRAK (X read platny tier / LinkedIn po App 2) | Comment Radar SOP = proces reczny do czasu decyzji kosztowej |
| 9 | **Media storage: Google Drive jako zrodlo** (Tomasz 06/07): dzis trzymamy TYLKO file_id (bajty u Telegrama, zero dysku Mikrusa; Telegram getFile limit 20MB - filmy dluzsze wymagaja GDrive); przy publikacji pobranie z GDrive | BRAK - backlog | seam source-descriptor gotowy ({"source":"gdrive","id":...}); wymaga konektora + auth |

## 3. ZASADA PRODUKTOWA
Kazda funkcja z sekcji 1 = pozycja w wartosci pakietu; kazdy punkt sekcji 2 po zbudowaniu
PRZENOSI SIE do sekcji 1 (ten plik = zywy dokument, aktualizowany po kazdym buildzie).
Wycena pakietow: decyzja Manager/Tomasz na bazie tego dokumentu (drabinka ags_premium
w pricing_tiers; subagent standalone vs pakiet z CM = osobne pozycje cennika).
