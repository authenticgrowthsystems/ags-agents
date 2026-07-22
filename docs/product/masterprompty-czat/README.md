# Masterprompty czatowe (LACZNIK, etap 1)

Pliki do WKLEJENIA przez Tomasza do projektu w aplikacji czatowej na abonamencie
(Claude, ChatGPT - dowolny czat). Wrzucasz RAZ do projektu, potem kazda sesja pracy
zaczyna sie sama: agent czyta stan gry z linku Notion i konczy sesje blokiem
[RAPORT PRACY v1], ktory wklejasz do Telegrama (bot AGS).

## Zasady

- Wersjonowanie jak prompty agentow: pelny nowy plik z podbita wersja, nigdy diffy.
- Kazdy plik jest SAMOWYSTARCZALNY: tozsamosc + glos + kontrakty (RAPORT PRACY /
  stan gry z linku) + regula prawdy.
- Link stanu gry jest juz WPISANY w pliki (strona Notion "Stan gry AGS",
  https://app.notion.com/p/3a5c00c90b938140b271dc5d18a4920a, dostep przez konektor
  Notion czatu - strona NIE jest publikowana do webu; fallback = /kontekst w Telegramie).

## Aktualne wersje (22/07/2026, po wsadzie roboczych promptow Tomasza)

- **`MASTERPROMPT_CZAT_X_v2.md`** - praca reczna na X. Scalone z "X Comment
  Specialist" (szablony A-D, zelazne zasady, prawdziwe historie, listy kont, QT);
  wyciete: stan sesji/statystyki i logowanie Notion (zastapione RAPORTEM PRACY).
  v1 zostaje w repo jako historia.
- **`MASTERPROMPT_CZAT_LINKEDIN_AGS_v1.md`** - praca reczna na LinkedIn. Scalone
  z "LinkedIn SM AGS" (reguly operacyjne, klasyfikacja Buyer/Peer/Partner/
  Competitor-adjacent, frame buyer-lane); wyciety stan pipeline (zyje w stanie gry).

## Decyzje 22/07 (guziki)

- **Lead Tracker Notion = archiwum do odczytu.** Czat NIE pisze do Lead Trackera;
  cala praca wraca RAPORTEM PRACY do bazy ags_crd (SSOT), stan kontaktow czytany
  ze strony Stan gry. Pipeline z Trackera zasiewa jednorazowy raport liniami
  `nowa_osoba` (Tomasz przy pierwszej sesji LinkedIn).
- **Content Manager czatowy: BEZ wersji stalej.** Orkiestracje tresci robi serwerowy
  CM (Telegram); czatowy CM zdublowalby prawde o planie/kolejce. Roboczy prompt CM
  (wsad 15/06) pozostaje zrodlem doktryny contentowej, nie osobnym agentem czatowym.
- Prompty "content X" i "content LinkedIn" - nieuzywane przez Tomasza, nie przerabiamy.

## Format RAPORT PRACY v1 (parser: cm-agent/app/engagement.py)

Typy linii: komentarz, dm_wyslany, dm_odebrany, reakcja, zaproszenie (22/07, wsad
LinkedIn), nowa_osoba, obserwacja. Pelny format i pulapki: docs/komponenty/lacznik.md.
