# RAPORT do Managera: ZAMKNIECIE DNIA 19/07/2026 (sesja dnia po incydencie 13-19/07)

Od: BE. Raporty czastkowe per krok: _metryki, _eskalacja, _kanon_publikacji, _bramka_tematow.
Ten raport = calosc dnia + wieczorne dobudowy z tap-testow Tomasza.

## 1. Incydent tygodnia - zamkniety systemowo

Diagnoza z dowodow (screeny + eksporty LinkedIn, commit 787238f): autopilot publikowal na
X ORAZ LinkedIn; meta-posty o systemie 2-44 wysw. vs 2331 narracja; zasieg LI -90% bez
obecnosci Tomasza; X 613 postow/10 followers = dystrybucja, nie wolumen.

KOREKTA KANONU (Tomasz): bledem bylo publikowanie NIEZATWIERDZONEGO, nie publikowanie
w ogole. Zatwierdzone = ZAWSZE wychodzi; niezatwierdzone = NIGDY samo (_emergency_promote
USUNIETY Z KODU); cisza >24h = pytanie guzikami. Pamiec: project_publikacja_kanon_19072026.

## 2. Plan dnia [1]-[4] - LIVE (3 rebuildy w ciagu dnia, tap-testy Tomasza)

[1] METRYKI: import xlsx AggregateAnalytics przez Telegram E2E PASSED (28 dni, 11 postow
    zmatchowanych, demografia; verify w DB) + sekcja PROFIL w raportach. DDL 023.
[2] ESKALACJA+NAUKA: agent_decisions/decision_modes (DDL 024), guziki dec:, kazda odpowiedz
    -> agent_learning_log, progi 10/80% -> propozycja semi-auto (tap Tomasza). n8n LIVE.
[3] KANON: stan awaryjny wyciety; held sprzatniety wg DOWODU (zero approved w held;
    7 published/rejected + 15 sierot -> rejected, decyzja guzikami).
[4] BRAMKA TEMATOW: filary+ICP, meta max 1/tydz (regex 6/6 incydentu, 0 FP), limit 20.
    NOWY PLAN zbudowany i ZATWIERDZONY przez Tomasza (23 pozycje, tematy pod ICP).

## 3. Bledy wylapane na tap-testach (naprawione tego samego dnia)

- Pusty plan MILCZAL (if chat and n) -> kazde wyjscie planera melduje + lista odrzuconych.
- Cap planu scinal POCZATEK tygodnia (sort po created_at) -> sort po scheduled_for
  (Tomasz wylapal: poniedzialek bez X; 3 posty przywrocone SQL-em).
- CM zameldowal "Zrobione" o zmianie okna BEZ wywolania target_update (DB niezmienione) -
  naprawa SQL; TEST PRAWDY: zmiana configu bez paragonu ⚙️ nie istnieje; backlog:
  deterministyczny route komend konfiguracyjnych.
- Duplikacja tezy (material "Orkiestracja" = post X z 11/07; wykryla zewnetrzna bramka
  przegladarkowego CM, potwierdzone w published_posts) -> reguly stylu #11/#12 zapisane
  TRWALE z paragonami (zweryfikowane w DB), backlog: twarda bramka embedding przy generacji.

## 4. Wieczorne dobudowy (feedback Tomasza przy przegladzie kart)

- Ludzkie minuty publikacji (kanon: +/-15 min, nigdy kwadrans) - slots.humanize_slot.
- Karty po decyzji przychodza NA DOL czatu (koniec przewijania); ➕ Media bez floodu galeria.
- gpt-image-1 -> gpt-image-2 (docs-first) + guzik 📋 Prompt (pelny prompt graficzny do
  wklejenia w zewnetrzny generator; wynik wraca przez ➕ Media).
- Okno LI profilu 16:00-18:00 + plan przesuniety (SQL).

## 5. Taski od poprzedniej sesji (3/3)

(2) Legacy AGS X Agent: OFF, nietkniety od 25/06 - podwojnych publisherow NIE MA (dowod n8n).
(1) Dokumenty Telegram: .md/.txt -> rozmowa aktywnego agenta (galaz document_text + /docmsg).
(3) Voice Bible: zderzenie gotowe - docs/cm/ZDERZENIE_VOICE_BIBLE_19072026.md. SPRZECZNOSC:
    Notion sekcja 9 kaze przeliczac fakty PLN->USD, kanon v2.2 sekcja 15 (nowszy) zakazuje.
    Rekomendacja: brand_config=SSOT + nowy klucz voice_dna_core (sekcje DNA 1-8 z Notion),
    strona Notion -> read-only mirror. CZEKA NA DECYZJE TOMASZA (guziki po przegladzie).

## 6. Nastepne buildy (kolejnosc rekomendowana)

1. Kolektor X Owned Reads (~$4.50/mies; BRIEF READY; kazdy dzien zwloki = strata historii
   prywatnych metryk <30 dni; najpierw Tomasz: Developer Console credits + limit $10).
2. Twarda bramka duplikacji przy generacji (embedding vs published, pgvector).
3. Deterministyczny route komend konfiguracyjnych (incydent "Zrobione" bez narzedzia).
4. Voice Bible SSOT (po decyzji Tomasza). Nastepny wolny DDL: 025.

## 7. Metryki dnia (Tomasz widzi, system tez)

LinkedIn: 488 obserwujacych, tydzien nieobecnosci 281 wysw. (-90%); dane w
channel_metrics_daily + demografia (ICP trafiony: 13% founders, 15% wlasciciele).
Ledger Anthropic: pik $7.50 12/07 (dzien sprintu) - zrzut kosztow poszedl jako wizual
do poniedzialkowego posta (prawdziwe liczby, regula prawdy).
