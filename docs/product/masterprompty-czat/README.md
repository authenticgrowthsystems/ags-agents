# Masterprompty czatowe (ŁĄCZNIK, etap 1)

Pliki do WKLEJENIA przez Tomasza do projektu w aplikacji czatowej na abonamencie
(Claude, ChatGPT - dowolny czat). Wrzucasz RAZ do projektu, potem każda sesja pracy
zaczyna się sama: agent czyta stan gry z linku Notion i kończy sesję blokiem
[RAPORT PRACY v1], który wklejasz do Telegrama (bot AGS).

## Zasady

- Wersjonowanie jak prompty agentów: pełny nowy plik z podbitą wersją, nigdy diffy.
- Każdy plik jest SAMOWYSTARCZALNY: tożsamość + głos + kontrakty (RAPORT PRACY /
  stan gry z linku) + reguła prawdy.
- Pliki pisane pełną polszczyzną (to treść dla agenta i Tomasza, nie kod). Wyjątek:
  nazwy typów w bloku RAPORT PRACY bez polskich znaków - dopasowuje je parser
  (ma też aliasy z polskimi znakami na wszelki wypadek).
- Link stanu gry jest już WPISANY w pliki (strona Notion "Stan gry AGS",
  https://app.notion.com/p/3a5c00c90b938140b271dc5d18a4920a, dostęp przez konektor
  Notion czatu - strona NIE jest publikowana do webu; fallback = /kontekst w Telegramie).

## Aktualne wersje (22/07/2026, po wsadzie roboczych promptów Tomasza)

- **`MASTERPROMPT_CZAT_X_v2.md`** - praca ręczna na X. Scalone z "X Comment
  Specialist" (szablony A-D, żelazne zasady, prawdziwe historie, listy kont, QT);
  wycięte: stan sesji/statystyki i logowanie Notion (zastąpione RAPORTEM PRACY).
  v1 zostaje w repo jako historia.
- **`MASTERPROMPT_CZAT_LINKEDIN_AGS_v1.md`** - praca ręczna na LinkedIn. Scalone
  z "LinkedIn SM AGS" (reguły operacyjne, klasyfikacja Buyer/Peer/Partner/
  Competitor-adjacent, frame buyer-lane); wycięty stan pipeline (żyje w stanie gry).

## Decyzje 22/07 (guziki)

- **Lead Tracker Notion = archiwum do odczytu.** Czat NIE pisze do Lead Trackera;
  cała praca wraca RAPORTEM PRACY do bazy ags_crd (SSOT), stan kontaktów czytany
  ze strony Stan gry. Pipeline z Trackera zasiał jednorazowy raport liniami
  `nowa_osoba` (wykonane 22/07: Crystalee Beck, Chris Del Grande, Jay Greyson).
- **Content Manager czatowy: BEZ wersji stałej.** Orkiestrację treści robi serwerowy
  CM (Telegram); czatowy CM zdublowałby prawdę o planie i kolejce. Roboczy prompt CM
  (wsad 15/06) pozostaje źródłem doktryny contentowej, nie osobnym agentem czatowym.
- Prompty "content X" i "content LinkedIn" - nieużywane przez Tomasza, nie przerabiamy.

## Format RAPORT PRACY v1 (parser: cm-agent/app/engagement.py)

Typy linii: komentarz, dm_wyslany, dm_odebrany, reakcja, zaproszenie (22/07, wsad
LinkedIn), nowa_osoba, obserwacja. Pełny format i pułapki: docs/komponenty/lacznik.md.
