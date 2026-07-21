# LACZNIK SYNCHRONIZACYJNY: praca na abonamencie <-> serwer (KONCEPT 21/07/2026)

Problem (Tomasz 21/07): "Jade pociagiem, pracuje z agentem w czacie na abonamencie
(stala oplata, taniej niz tokeny API). Odpowiadam na komentarze, wysylam DM-y, daje
reakcje, poznaje nowych ludzi. Agent na serwerze NIE MOZE o tym nie wiedziec - i w
druga strone: czatowy agent ma znac stan z bazy i pracowac dalej."

Zasada nadrzedna (kanon warstw): **SSOT = baza ags_crd.** Notion = lustro bazy
(sync_registry, do CZYTANIA gdy baza niedostepna), nigdy druga prawda. Czat na
abonamencie = kolejny WYMIENNY INTERFEJS do tych samych organow - dokladnie jak
Telegram, tylko ze czlowiek jest kablem transmisyjnym.

## Rozwiazanie docelowe: dwa kontrakty + jedna zasada

### Kontrakt 1: RAPORT PRACY (kierunek czat -> serwer)

Staly, wersjonowany format blokowy, ktory czatowy agent MA OBOWIAZEK wygenerowac
na koniec kazdej sesji pracy (wpisany do masterpromptu czatowego projektu):

```
[RAPORT PRACY v1] kanal: X | data: 2026-07-21
- komentarz | @handle | link-do-posta | tresc komentarza
- dm_wyslany | @handle | tresc
- dm_odebrany | @handle | streszczenie
- reakcja | @handle | like | link
- nowa_osoba | @handle | bio/notka | proponowany tier
- obserwacja | notka do radaru
[KONIEC RAPORTU]
```

Dostarczenie (oba kanaly od dnia 1):
- **wklejka do Telegrama** (subagent kanalu aktywny): deterministyczny route
  `[RAPORT PRACY` -> parser BEZ LLM -> INSERT engagement_log + contacts (stadium wg
  typu akcji: komentarz->commented, dm->dm itd.) + intake nowych osob (karta tieru
  guzikami tylko dla nieznanych) -> PARAGON z licznikami ("zapisane: 3 komentarze,
  1 DM, 2 nowe osoby").
- **plik .md** wrzucony do rozmowy (handle_document juz przyjmuje .md - zero nowego kodu).

Idempotencja: hash linii raportu jako external_ref w engagement_log - ten sam raport
wkleisz dwa razy i NIC sie nie zdubluje.

### Kontrakt 2: PAKIET KONTEKSTU (kierunek serwer -> czat)

Komenda `/kontekst [kanal]` w Telegramie -> serwer sklada zwarty zrzut stanu jako
tekst/plik .md do skopiowania w czat:
plan tygodnia (sloty+statusy), ostatnie publikacje z metrykami, kontakty w grze
(stadium != cold, z ostatnia interakcja), otwarte watki/decyzje, lejek sprzedazy,
notatki radaru. Zero LLM - czysty odczyt z bazy, format staly.

Rytual podrozny = 30 sekund: przed wyjazdem `/kontekst x` -> kopiuj w czat ->
pracujesz na abonamencie -> na koniec czat drukuje RAPORT PRACY -> wklejasz do
Telegrama -> paragon. Baza spójna, zero tokenow API za prace wykonana recznie.

### Zasada: Notion = lustro, nie kanal zapisu

Raporty pracy NIE ida przez Notion (API Notion na AGS Hub ma timeouts - dowod z #71;
wklejka do Telegrama jest szybsza i ma paragon). Notion pozostaje lustrem DO CZYTANIA:
gdy czat nie moze dostac pakietu kontekstu, czyta lustro. Sync DB->Notion robi
istniejacy organ sync-notion (page_map).

## Etap 2 (pozniej, nie warunkuje etapu 1)

Czatowy agent claude.ai z bezposrednim dostepem read-only do stanu (konektor MCP /
endpoint HTTP z sekretem) - wtedy pakiet kontekstu pobiera sie sam, a raport pracy
mozna wysylac przyciskiem. Etap 1 nie wymaga ZADNEJ nowej infrastruktury i dziala
w kazdym czacie (Claude, ChatGPT, cokolwiek) - dlatego wchodzi pierwszy.

## Co trzeba zbudowac (etap 1 = maly build)

1. Parser RAPORT PRACY + route + paragon (Python: engagement/conversation; bez LLM).
2. Komenda /kontekst (Python: reports; przepustka komendy w n8n - patcher).
3. MASTERPROMPT CZATOWY per subagent (docs/product/: tozsamosc, glos, kontrakty
   raportu i kontekstu) - plik, ktory Tomasz wkleja do projektu w aplikacji czatowej.
4. Idempotencja: kolumna external_ref w engagement_log (maly DDL) albo hash w notes.

## DECYZJA TOMASZA (21/07 wieczor, guziki)

**TAK - budujemy PO zakonczeniu buildu INTAKE-UX** (zero ryzyka konfliktow w
conversation.py). Dwa doprecyzowania od Tomasza, ktore wchodza do zakresu:

1. **Masterprompty czatowe od Tomasza jako wsad.** Tomasz dostarczy masterprompty,
   ktorymi JUZ uruchamia agentow w czacie. BE modyfikuje je wg naszych wytycznych
   (glos, kontrakty RAPORT PRACY / PAKIET KONTEKSTU, regula prawdy) do wersji STALEJ,
   wielokrotnego uzytku - wrzucasz raz i kontynuujesz prace w kazdej sesji.
2. **Stan gry przez LINK, nie wklejke (preferencja):** masterprompt czatowy zawiera
   staly LINK do strony Notion (lustra), na ktorej serwer AKTUALIZUJE stan gry
   (pakiet kontekstu). Czatowy agent na starcie sesji CZYTA stan sam z linku -
   zero recznego wklejania. `/kontekst` w Telegramie zostaje jako fallback, a organ
   sync-notion dostaje zadanie: strona "Stan gry <kanal>" odswiezana po kazdej
   istotnej zmianie (publikacja, zmiana lejka, nowy kontakt). UWAGA projektowa:
   zapis do Notion bywa wolny (timeouts #71) - stan gry to JEDNA strona nadpisywana,
   nie append; przy niedostepnosci Notion czat prosi Tomasza o /kontekst.

STATUS: ZATWIERDZONY, START PO DONE INTAKE-UX. Brief BE-LACZNIK powstanie wtedy
(wsad: masterprompty od Tomasza + ten dokument).
