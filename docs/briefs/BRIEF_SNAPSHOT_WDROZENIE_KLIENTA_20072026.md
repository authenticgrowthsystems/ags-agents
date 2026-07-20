# BRIEF BUILDU: SNAPSHOT - wdrozenie u klienta (20072026) - budowniczy: BE-SNAPSHOT

Wywolanie sesji (nowe okno; Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_SNAPSHOT_WDROZENIE_KLIENTA_20072026.md zbuduj`

## 0. Tryb rownolegly

Wlasny worktree+galaz `build/snapshot` od origin/claude/silly-blackwell-dfc32d (wzorzec
sekcji 0 briefow 19/07), worktree `build-snapshot`. Build glownie DOKUMENTACYJNO-SKRYPTOWY:
zero deployu produkcyjnego, zero zmian w dzialajacym cm-agent; wolno pisac NOWE skrypty
seed/eksport (nieaktywne dopoki nie uzyte). Koordynacja z BE-DOKUMENTACJA: komponenty
docs/komponenty/ to material zrodlowy - NIE dubluj ich tresci, LINKUJ.

## 1. PO CO (wymog Tomasza 20/07 - kanon produktu)

"Nie po to buduje dla siebie, zebym potem nie umial tego wdrozyc." Gdy przyjdzie klient
(agent pod konkretna branze / freelancera / osobe), Tomasz ma wiedziec DOKLADNIE jak to
wdrozyc i ustawic. Cel: wdrozenie = minuty, maksymalnie pare godzin przy rozbudowanym.
Sprzedajemy SNAPSHOT: gotowe, dzialajace rozwiazanie, ktorego nie trzeba naprawiac u klienta.

## 2. CO budujemy (trzy warstwy)

**A. PROCES INTAKE KLIENTA (7 krokow fundamentu).** Tomasz na starcie AGS przeszedl
~7-krokowy proces: ICP, messaging house, IKIGAI itd. - to jest PALIWO systemu pod konkretna
osobe/branze. Zadanie: ODNALEZC i SFORMALIZOWAC ten proces (zrodla: brand-canon/, tabele
z migracji #71 w ags_crd: sales_playbook, brand_strategy, doktryny ICP_BOUNDARY/Blueprint;
strony Notion-mirror; jesli czegos brak - USTALIC Z TOMASZEM guzikami, on ten proces
przechodzil recznie). Wynik: docs/product/INTAKE_KLIENTA_7_KROKOW.md - kwestionariusz +
instrukcja prowadzenia (moze prowadzic czlowiek ALBO agent w rozmowie) + MAPOWANIE
odpowiedzi na konfiguracje systemu: brands, channels.config, brand_config (voice_bible
per klient - wzorzec: jeden DNA + nakladka marki, patrz project_voice_dna_architecture),
brand_strategy (filary/ICP karmia planner i bramke tematow), brand_tokens (wizual).

**B. PLAYBOOK WDROZENIA TECHNICZNEGO.** docs/product/PLAYBOOK_WDROZENIA_SNAPSHOT.md -
krok po kroku, wykonywalne przez Tomasza bez zgadywania: (1) infra (VPS, docker, postgres,
n8n - co postawic, w jakiej kolejnosci), (2) DB: db/001..0NN po kolei + seed z intake,
(3) app_secrets - PELNA lista kluczy per komponent (co obowiazkowe, co opcjonalne),
(4) n8n: import workflowow (HITL + publishery + Researcher; eksport zywych definicji
przez API do n8n-workflows/ jako czesc buildu - ZYWE godne zaufania, nie stare kopie),
(5) konty klienta: Telegram bot, X API (developer console + pay-per-use - wzorzec z
BRIEF_KOLEKTOR sekcja 5), LinkedIn OAuth, OpenAI/Anthropic, (6) smoke-testy po wdrozeniu
(lista tapow z oczekiwanymi paragonami), (7) checklista "oddania kluczy" klientowi.
Baza: DEPLOY_CHECKLIST.md v2 (istnieje) - ROZSZERZYC, nie pisac od zera.

**C. SEED/SNAPSHOT TOOLING (minimum, Pareto).** Skrypt(y) w etl/ albo tools/:
(1) eksport zywych workflowow n8n do repo (API GET -> json; kotwica zaufania playbooka),
(2) generator seed-SQL z wypelnionego intake (markdown/yaml odpowiedzi -> INSERTy brands/
channels/brand_config) - zeby "pare minut" bylo doslowne. BEZ przebudowy aplikacji:
multi-brand i /brand_add JUZ istnieja, snapshot na nich jedzie.

DoD:
- [ ] INTAKE_KLIENTA_7_KROKOW.md - komplet krokow potwierdzony z Tomaszem (guziki), mapowanie
      odpowiedz->tabela/klucz dla KAZDEGO pytania
- [ ] PLAYBOOK_WDROZENIA_SNAPSHOT.md - test krzeslem: Tomasz czyta i mowi "umiem to zrobic
      u obcego klienta bez pytania sesji o nic"
- [ ] eksport n8n do repo dziala (skrypt + swieze jsony w n8n-workflows/)
- [ ] generator seed-SQL: przyklad wypelnionego intake (fikcyjny klient "Studio Tanca X")
      -> dzialajacy zestaw INSERTow
- [ ] masterprompt sekcja 1/dokumenty-kotwice: wpis o obu dokumentach

## 3. Czego NIE dotykac

Dzialajacy system Tomasza (zadnych zmian configu AGS/TNM/RDC), HITL, kontenery. Zadnego
"ulepszania" aplikacji przy okazji - snapshot opisuje i pakuje TO CO JEST.

## 4. Stan zastany (nie buduj od nowa)

DEPLOY_CHECKLIST.md v2; docs/komponenty/ (w budowie przez BE-DOKUMENTACJA); SYSTEM_DATAFLOW;
SCHEMA; multi-brand LIVE (brands/channels/brand_config per marka, /brand_add, voice bible
per marka, brand_tokens); migracja #71 (doktryny w PG); n8n-workflows/researcher/ (wzorzec
kopii repo). Memory: project_product_architecture, project_subagent_object_toggle
(subagent = sprzedawalny OBIEKT), project_voice_dna_architecture.

## 5. Udzial Tomasza

Guziki przy formalizacji 7 krokow (on zna proces z autopsji) + test krzeslem playbooka.
Zero SSH poza ewentualnym odpaleniem skryptu eksportu n8n.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_snapshot.md + masterprompt + pamiec + STATUS tu.

STATUS = READY-HOLD (20/07 - patrz sekcja 7; start po macierzy gotowosci)

## 7. KOREKTA TOMASZA 20/07 (przeczytaj przed startem)

- STATUS = READY-HOLD: NIE uruchamiac teraz. Kolejnosc: dokumentacja komponentowa + MACIERZ
  GOTOWOSCI najpierw (agenci nie sa gotowi; "nie moge sprzedawac czegos co nie jest gotowe").
  Sprzedaz KONKRETNEGO agenta klientowi = osobna sesja z Managerem, gdy Manager uruchomiony.
- WYMOG ARCHITEKTONICZNY do warstwy B playbooka: INTERFEJS KLIENTA = WYMIENNY KONEKTOR.
  Telegram to nasz obecny front, ale klient wybiera: Telegram / Slack / aplikacja webowa
  (prawdopodobny glowny kandydat) / aplikacja mobilna (docelowo zastepuje komunikatory).
  Architektura JUZ to umozliwia (n8n=transport, logika w cm-agent /message {chat_id, text}
  - kazdy front to nowy transport do tego samego kontraktu); playbook ma opisac warstwe
  konektorow i miejsce wpiecia nowego frontu, NIE zakladac Telegrama na sztywno.
