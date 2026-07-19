# ZDERZENIE VOICE BIBLE: Notion (przegladarkowy CM) vs brand_config (serwer) - 19/07/2026

Task (3) od poprzedniej sesji. Dowody: Notion 331c00c90b9381afa511fa8c9ae3658c (fetch 19/07)
vs brand_config AGS voice_bible v=4 md5 dc8b4334 (22168 zn., read-only 19/07).

## 1. Co trzyma kto

| | Notion "VOICE BIBLE - Tomasz Nawrocki (CANONICAL)" | brand_config AGS "Voice Bible v2.2" |
|---|---|---|
| Charakter | OSOBISTE DNA glosu (20 wywiadow, 26/03): ton, motywy, wartosci, wzorce decyzji, metafory, one-liner, 10 regul tworzenia | OPERACYJNA biblia MARKI: pozycjonowanie, banned vocab, zero em-dash, formaty, compliance, Re-Intro, X Article, barwy, waluta |
| Sekcje | 1-8 DNA + 9 "Waluta i jezyk per marka" (dopisane 28/06) | 1-15 (waluta = 15, canonical 12/07) |
| Wersjonowanie | brak (LOCKED, edycje reczne) | version=4, md5, historia w brand_config_history |
| Kto czyta | przegladarkowy CM (Opus w czacie) | caly serwer (generacje, compliance, subagenci) |

## 2. SPRZECZNOSC MERYTORYCZNA (nie kosmetyka)

**Notion sekcja 9 (28/06):** "Kwoty z briefow podawane w PLN przeliczac na USD przed publikacja."

**brand_config sekcja 15 (canonical 12/07, NOWSZE):** "Dane zrodlowe przytaczamy w ICH walucie
jako FAKT (rachunek byl w PLN = piszemy PLN, nawet w tresci AGS EN) - zero mechanicznego
przeliczania faktow. Ceny i oferty marki ZAWSZE w walucie marki. Benchmark cross-market
z przelicznikiem, zawsze z jawnym oznaczeniem (~)."

Skutek rozjazdu: przegladarkowy CM PRZELICZA fakty PLN->USD (wbrew regule prawdy o danych
zrodlowych), serwer zostawia fakty w walucie zrodla. Ten sam artykul dual-brand wyjdzie
z innymi liczbami zaleznie od tego, ktory agent go pisal.

Drugi rozjazd (mniejszy): Notion sekcja 9 nie zna niuansow sekcji 15 (benchmarki z ~,
zakaz golych liczb przy kwotach) ani sekcji 14 (barwy per marka).

## 3. Czego brakuje po stronie serwera

Sekcje 1-8 Notion (DNA: "Direct but Warm", motywy, wartosci, "Jakos to bedzie", metafory
taniec=architektura, 10 regul) NIE ISTNIEJA w brand_config - naglowki v2.2 ich nie zawieraja.
To jest dokladnie "wspolny rdzen" z kanonu glosu 12/07 (jeden DNA + nakladki marek), ktory
dzis zyje TYLKO w Notion, poza wersjonowaniem i poza zasiegiem serwera.

## 4. REKOMENDACJA (zgodna z architektura po cutoverze #71: DB=SSOT, Notion=mirror)

1. **brand_config = SSOT** dla WSZYSTKIEGO co glosowe:
   a) zasady operacyjne marek - juz sa (AGS v2.2, TNM v2.0);
   b) rdzen DNA (sekcje 1-8 z Notion) -> NOWY klucz brand_config `voice_dna_core`
      (brand AGS, wspolny rdzen czytany przy generacjach wszystkich marek) - INSERT
      przez Tomasza SSH, tresc 1:1 z Notion (jest dobra, niczego nie przepisujemy).
2. **Notion = READ-ONLY MIRROR**: strona 331c... wchodzi do sync_registry/page_map jak
   67 stron po cutoverze; sekcja 9 ZNIKA z Notion (zastapiona mirrorem sekcji 15+14
   z brand_config) - jedna wersja prawdy, koniec dopisywania zasad w dwoch miejscach.
3. **Przegladarkowy CM dostaje instrukcje** (przez inbox/sync): czyta mirror, NIE edytuje;
   nowe reguly zglasza Tomaszowi -> BE -> bump w brand_config (wersja+md5+historia).
4. Do czasu wykonania 1-3: przy artykulach dual-brand od przegladarkowego CM sprawdzac
   waluty faktow recznie (Tomasz juz raz to wylapal przy liczbach 800ms/$0,02).

## 5. Nastepny krok

Decyzja Tomasza guzikami (BE przygotuje SQL na `voice_dna_core` + wpis page_map po tapnieciu).
