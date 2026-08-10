# AGS System - mapa przeplywu danych + indeks komponentow

**Status:** ZYWY dokument = MAPA + INDEKS. Aktualny na **10/08/2026**.
Szczegoly kazdego komponentu mieszkaja w `docs/komponenty/` (staly szablon, stan obecny).
Historia i sekcje datowane: `docs/archiwum-dataflow.md` + raporty `docs/cm/` + git log.

**Zasada nadrzedna:** jedno zrodlo prawdy = PostgreSQL `ags_crd`. Notion = lustro dla czlowieka.
Sekrety TYLKO `app_secrets`. n8n = TYLKO transport - **ale takze teksty, ktore czyta czlowiek**
(patrz D-016), wiec szukajac mylacej wiadomosci w bocie sprawdz n8n, zanim otworzysz kod.

> **Nowy w projekcie?** Czytaj w kolejnosci: ten plik (mapa) → `anti-patterns/library.md`
> (na czym ten projekt sie przejechal - najszybsza droga do zrozumienia, dlaczego kod wyglada
> tak, a nie inaczej) → `docs/komponenty/` (opis modulu zamiast zrodel) →
> `docs/ops/DLUG_TECHNICZNY.md` (co jest swiadomie niedokonczone).

## 1. Architektura (kto gdzie mieszka)

```
Tomasz (Telegram @ags_social_bot + bot #2 logowy)
   |
n8n (Mikrus, transport): HITL U5pUZjy2yAhR1sWg (router komend/callbackow),
   publishery subagentow (X, LinkedIn), Scheduler x1jJEbcWAe3FnpCa (co minute),
   crony raportow 08:00 / nd 20:00 / nd 20:15, drift 03:00, backup 03:30,
   adaptery Researchera, Lacznik yxJUJmZpSUe0tw9K (narzedzia MCP dla czatu)
   |                                   |
cm-agent (kontener Python :8089)    ags-researcher (kontener Python)
   petla workera + FastAPI             petla workera + FastAPI /request
   /message /matnav /plannav /cmt      kaskada 6 zrodel -> synteza
   /decnav /docmsg /metrics/xlsx       claims + options + koszty
   /wake /request /plan /reports
   |                                   |
PostgreSQL ags_crd (pg_n8n) - KREGOSLUP ZAPISU (wszystkie tabele)
Notion - read-only mirror (sync worker w cm-agent; wyjatek: brand_tokens Notion->PG)
```

Komunikacja agent-agent: EVENT-DRIVEN (POST `/wake`, POST `/request`, `X-Researcher-Secret`);
poll 30 s i crony = tylko backstop i rutyny.

**TRZECH PISARZY do `content_items`**, nie jeden - kazda migracja musi uwzglednic wszystkich
(szczegoly: `komponenty/n8n-transport.md`):

| pisarz | co zapisuje |
|---|---|
| kontener `cm-agent` (`worker.py`) | caly cykl zycia materialu |
| n8n `AGS Scheduler v1` | `published` po udanej publikacji |
| n8n `AGS HITL Handler v1.0` | `approved` / `rejected` przy tapnieciu guzika, **z pominieciem cm-agenta** |

Deploy: push (Tomasz) → SSH `git pull` → ew. `psql db/0NN` → `docker build/run` → `/health`.
**Sesje Claude Code NIE MAJA dostepu SSH** - kazde `docker`/`psql` na produkcji wykonuje czlowiek.
Procedura wzorcowa okna migracyjnego: `docs/ops/OKNO_d008_03082026.md`.
Zasady migracji: `docs/ops/RUNBOOK_migracje.md` - **czytac PRZED kazda zmiana w bazie**.

## 2. Glowny przeplyw tresci (od pomyslu do metryki)

```
POMYSL: rozmowa CM / Idea Bot / schowek (inspirations)          [rozmowa-cm]
   v
PLAN TYGODNIA: planner + bramka tematow + cap 20 ->
   content_items 'proposed' -> przeglad guzikami -> approve      [planner]
   v
GENERACJA: canonical (Voice Bible z brand_config w bloku
   systemowym) -> compliance.enforce -> dedup (⚠️ informuje,
   NIE blokuje) -> wariant per kanal (jezyk z channels.config
   .language_publish) -> post_queue 'review'                     [glos-marki, dedup]
   v
DECYZJA TOMASZA: karty matreview + wiadomosc approval
   (edycja = akceptacja + nauka; kazda decyzja -> learning)      [karty-hitl]
   v
'approved' -> BRAMKA SLOTU: petla NIE bierze materialu, dopoki
   nie minie content_items.scheduled_for                         [kolejka-publikacja]
   v
BEZPIECZNIK GATUNKU (AP-315) -> 'handed_off' -> dispatch
   per publish_mode (Scheduler / held / webhook)                 [kolejka-publikacja]
   v
PUBLIKACJA: Scheduler publikuje wiersz 'scheduled' o czasie
   max(slot planu, czas kolejki); reconcile_publications
   domyka material na 'published' PO callbacku                   [kolejka-publikacja]
   v
METRYKI: kolektor X Owned Reads (dobowy snapshot) + import
   LinkedIn xlsx -> channel_metrics_daily -> raporty PROFIL      [metryki]
   v
NAUKA: agent_learning_log + decyzje guzikami + content_memory    [decyzje-nauka]
```

**Zasada niezmienna (kanon 19/07):** zatwierdzone publikuje sie ZAWSZE, niezatwierdzone NIGDY samo.

Rownolegle: Researcher na zadanie (`POST /request`) + sobotni podklad "CM czyta swiat"
pod niedzielny artykul [researcher]; sync mirror DB→Notion [sync-notion]; caly transport
i zasady zmian n8n [n8n-transport]; Lacznik - praca reczna Tomasza w czacie na abonamencie
kontra baza [lacznik]; maszynka prospektowa i lejek sprzedazy [maszynka-prospektowa,
agent-sprzedazy, teczka-prospekta].

## 3. GDZIE STOJA BRAMKI (miedzy pomyslem a publiczna publikacja)

Sekcja dolozona 10/08 po incydencie AP-315. **Kazda bramka odpowiada na INNE pytanie** i to jest
cala rzecz: post, ktory szesc dni wisial na LinkedInie z wypowiedzia modelu zamiast tresci,
przeszedl przez cztery kontrole, bo zadna nie pytala o to, czym ten tekst JEST.

| # | bramka | pyta o | blokuje? | gdzie |
|---|---|---|---|---|
| 1 | filtr jezykowy regulek nauczonych | czy regulka stylu jest w jezyku wyjscia | nie wpuszcza do promptu | `generate._learned_style`, `_learning_digest` |
| 2 | bramka wyjscia filtra | czy odpowiedz modelu jest PRZEROBKA tekstu, a nie wypowiedzia o nim | oddaje tekst wejsciowy + wpis w `agent_logs` | `compliance._rewrite` |
| 3 | `strip_meta_header` | czy pierwsze linie maja ksztalt naglowka | scina je | `compliance.strip_meta_header` |
| 4 | `compliance.enforce` | myslniki, zakazane slownictwo, czysta polszczyzna | poprawia (LLM) | `compliance.enforce` |
| 5 | walidacja dlugosci | czy tekst miesci sie w limicie kanalu | **TAK - wariant NIE wchodzi do kolejki**, z jawnym komunikatem | `channels._odrzuc_za_dlugi` |
| 6 | bramka duplikacji | czy temat byl juz publikowany (30 dni, pgvector) | **NIE blokuje, ostrzega** | `content_memory.dup_check` |
| 7 | **czlowiek** (HITL) | czy to ma wyjsc | tak - kanon 19/07 | karty matreview + approval |
| 8 | bramka slotu | czy nadszedl czas | trzyma material | `db.claim_item` |
| 9 | **bezpiecznik gatunku** | czy to tekst dla czlowieka, czy model mowiacy o tekscie | tak, przed `handed_off` | `worker.process_item` |

**Bramka 9 stoi tam, gdzie stoi, celowo:** tedy przechodzi KAZDA publikacja, takze material
zatwierdzony guzikiem w n8n z pominieciem cm-agenta. Sprawdza tresc **wiersza kolejki**,
nie `canonical_body` - publikuje sie wariant.

**Bramka 5 NIGDY nie obcina po cichu** (polecenie Managera 02/08). Urwany w polowie zdania post
jest gorszy niz brak posta, wiec za dlugi wariant jest odrzucany jawnie, z liczba znakow
i roznica do limitu. Ta sama zasada co przy bramce 2: **zatrzymac, nie naprawiac po cichu**.

**Bramki 1, 2 i 9 powstaly 10/08 z jednego incydentu** (AP-315). Warto wiedziec, ktora co lapie:
bramka 9 jest lista fraz i nie zlapala drugiej awarii tego samego dnia; bramka 2 mierzy relacje
wyjscia do wejscia i jest odporna na zmiane slownictwa; bramka 1 usuwa przyczyne. Pelny opis
z liczbami: `docs/anti-patterns/AP-315_walidator_formy_nie_gatunku.md`.

### Godzina publikacji

**`max(slot planu, czas kolejki)` plus tik Schedulera** - nie sam czas kolejki i nie sam slot.
Pilnuja tego DWIE niezalezne bramki z warunkiem `<= NOW()`: `db.claim_item` na materiale
(bramka 8) i Scheduler na wierszu `scheduled`. `humanize_slot` losuje symetrycznie +/-15 min,
wiec gdy trafi WCZESNIEJ niz slot planu, ta godzina jest martwa. Dowod i historia dwoch
pol-prawd: `docs/ops/DLUG_TECHNICZNY.md` D-015.

### Publikacja spoza systemu

Ksiega `published_posts` zna tylko to, co przez system przeszlo albo zostalo **odnotowane**.
Dwie komendy, dwie rozne sytuacje: `wklejone <id>` domyka gotowca Z KOLEJKI (`manual_paste`),
`wyszlo <kanal> <link>` zapisuje publikacje, ktora system CALKIEM ominela (`manual_external`).
Meldunek dnia rozroznia te trzy stany i nazywa podmiot: "System opublikowal" kontra "System
nie publikowal" kontra "Recznie odnotowane". Powod: `komponenty/kolejka-publikacja.md`.

## 4. Indeks komponentow (CZYTAJ ZAMIAST KODU)

| Komponent | Plik | W srodku |
|---|---|---|
| Planner | [komponenty/planner.md](komponenty/planner.md) | plan tygodnia, bramka tematow, cap 20, gap-filler, plannav |
| Kolejka i publikacja | [komponenty/kolejka-publikacja.md](komponenty/kolejka-publikacja.md) | `post_queue`, sloty, `humanize_slot`, Scheduler, kanon publikacji, sufit kadencji, re-slotter; **regula `max(slot, kolejka)`**; **bezpiecznik gatunku i bramka wyjscia filtra (AP-315)**; publikacja reczna |
| Karty + approval | [komponenty/karty-hitl.md](komponenty/karty-hitl.md) | karty matreview, guziki, media, fulltext, edycja=nauka, approval hitl |
| Decyzje + nauka | [komponenty/decyzje-nauka.md](komponenty/decyzje-nauka.md) | `agent_decisions`, `decision_modes`, `dec:`, progi semi-auto, learning_log. **UWAGA: petla nauki jest wektorem wstrzykniecia - AP-315** |
| Metryki | [komponenty/metryki.md](komponenty/metryki.md) | kolektor X Owned Reads, import xlsx LinkedIn, `channel_metrics_daily`, PROFIL |
| Dedup | [komponenty/dedup.md](komponenty/dedup.md) | `dup_check` na `master_theme`, prog `cm_dup_threshold` 0.57, ⚠️ w kartach i approval |
| Rozmowa CM/subagenci | [komponenty/rozmowa-cm.md](komponenty/rozmowa-cm.md) | route deterministyczne PRZED LLM, narzedzia, pamiec 3 warstwy, subagent = ten sam kod |
| Engagement-CRM | [komponenty/engagement-crm.md](komponenty/engagement-crm.md) | comment-radar per autor, `contacts` + stadium relacji, intake nieznanych, przypomnienia 24 h |
| Researcher | [komponenty/researcher.md](komponenty/researcher.md) | kaskada 6 zrodel, kontrakt `/request`, bramki critical/model, sunday brief |
| Grafika | [komponenty/grafika.md](komponenty/grafika.md) | **AUTO-OBRAZ WYLACZONY** (kanon 25/07: tylko szczegolowe prompty do recznej roboty), guzik 🎨 na zadanie |
| Glos marki | [komponenty/glos-marki.md](komponenty/glos-marki.md) | `voice_dna_core` + PELNA Voice Bible w jednym cache'owanym bloku systemowym |
| Sync Notion | [komponenty/sync-notion.md](komponenty/sync-notion.md) | mirror DB→Notion, `sync_registry`/`page_map`, drift check |
| n8n transport | [komponenty/n8n-transport.md](komponenty/n8n-transport.md) | HITL galezie, publishery, crony, zasady PUT (deactivate+activate), patchery; **teksty widziane przez czlowieka tez sa tutaj** |
| **Operacje hurtowe** | [komponenty/operacje.md](komponenty/operacje.md) | **NOWY 10/08**: `bulk_operations` + `op_id` (D-007). **ZBUDOWANY, NIEPODLACZONY** - zaden kod produkcyjny go nie wola |
| Agent Sprzedazy | [komponenty/agent-sprzedazy.md](komponenty/agent-sprzedazy.md) | `/prospect` research medium, wizytowka, dane kontaktowe w lejku, bramka tozsamosci, gotowiec HITL |
| Maszynka prospektowa | [komponenty/maszynka-prospektowa.md](komponenty/maszynka-prospektowa.md) | lancuch od niszy do klienta: osiem ogniw, mamy piec. Ogniwo 1 (`app.prospect_import`, DDL 034) zbudowane; brak wysylki i zbieracza po PKD |
| Teczka prospekta | [komponenty/teczka-prospekta.md](komponenty/teczka-prospekta.md) | most katalogi-baza (`sales_pipeline.katalog`, DDL 037), para MCP `zapisz_tekst` + `teczka`; nazwa katalogu ustalana RAZ |
| Kanon zimnej wysylki | [komponenty/wysylka-zimna-kanon.md](komponenty/wysylka-zimna-kanon.md) | pozycjonowanie (przedsionek, NIE zamiennik systemu zapisow), trzy argumenty, WhatsApp nie SMS |
| Lacznik | [komponenty/lacznik.md](komponenty/lacznik.md) | RAPORT PRACY (parser bez LLM), `/kontekst`, narzedzia MCP `stan_gry` + `wyslij_raport_pracy` |

Schemat tabel: `docs/db/SCHEMA_ags_crd.md`. Migracje: `cm-agent/db/0NN_*.sql`.
Anty-wzorce: `anti-patterns/library.md` (indeks) + `docs/anti-patterns/AP-*.md` (pelne opisy).

## 5. Stan i legacy

- **LIVE:** caly przeplyw z sekcji 2. Kanaly: AGS/linkedin i AGS/x publikuja automatycznie
  przez Scheduler. Kolejka X pusta od 29/07 - **decyzja** ("jeden wpis na material, koniec serii"),
  nie awaria.
- **DDL: ostatni zaaplikowany 042** (`status_handed_off`). Nastepny wolny: **043**.
  Slownik `content_items.status` zwezony 10/08 (D-008b): `dispatching` **usuniete**.
  **UWAGA: `post_queue.status` ma WLASNA wartosc `dispatching` i tam ZOSTAJE** - inny slownik,
  inne znaczenie (jeden wiersz oddany subagentowi). Nie rob podmiany "po calej bazie".
- **Zmiany 27/07 - 10/08, ktorych nie bylo w poprzedniej wersji tej mapy:**
  DDL 035 `slot_source` (kto ostatnio ustawil slot), 036 teczka prospekta, 037 most katalogi-baza,
  038 `marka_docelowa` (ETYKIETA, nie filtr), 039 `contacts.pipeline_stage` oznaczona jako MARTWA,
  040 rejestr operacji hurtowych, 041 `post_queue.format` + walidacja dlugosci,
  042 `handed_off`; zniesienie serii X; trzy warstwy AP-315; regula godziny publikacji.
- **ZAMKNIETE dlugi:** D-001, D-002, D-003, D-005, D-006, D-007, D-008, D-008b, D-009, D-010,
  D-011 (nie bylo wady), D-014, D-015 czesciowo.
- **OTWARTE:** D-004, D-012, D-013 (wielomarkowosc - czeka na pierwsza sprzedaz),
  D-015 reszta (karta w `/karty`), **D-016** (bot mowi "Publikacja za chwile" przy slocie za dobe -
  siedzi w n8n, nie da sie naprawic rebuildem). Pelne opisy: `docs/ops/DLUG_TECHNICZNY.md`.
- **LEGACY OFF:** stary AGS X Agent (kolejka Notion, cron 14/18/22) wylaczony od 25/06 -
  opis w `archiwum-dataflow.md` sekcja B. Architektura sprzed 10/06 zachowana pod tagiem
  `archiwum/x-agent-przed-10062026`.
- **ZAMROZONE** (nie odmrazac bez decyzji Tomasza): Agent Wizualny, App 2 CMA, strony firmowe
  LinkedIn, standalone subagenci.

## 6. Do udokumentowania dalej

- [ ] Diagram graficzny CALOSCI (pipeline + Researcher + siec agentow) - czesc pakietu
      sprzedazowego, renderowany gdy build skonczony.
- [ ] `pg_dump` schema-only pozostalych tabel bazowych do `SCHEMA_ags_crd.md`.
- [ ] `translate_text`: kopia PL nie jest tlumaczeniem, tylko osobna wersja (ma zdania,
      ktorych nie ma w angielskiej). Nikt tego nie sprawdzal - patrz raport 10/08.
- [ ] Podlaczenie rejestru operacji hurtowych do tras `reslot`, `outreach_cleanup`, `bulk_polish`.
