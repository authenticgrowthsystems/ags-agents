# Masterprompty czatowe (ŁĄCZNIK, etap 1 + 2)

Pliki do WKLEJENIA przez Tomasza do projektu w aplikacji czatowej na abonamencie
(Claude, ChatGPT - dowolny czat). Wrzucasz RAZ do projektu, potem każda sesja pracy
zaczyna się sama: agent czyta stan gry (narzędziem Łącznika albo z lustra Notion)
i kończy sesję blokiem [RAPORT PRACY v1] wysyłanym narzędziem (fallback: plik .md
do Telegrama).

## Zasady

- Wersjonowanie jak prompty agentów: pełny nowy plik z podbitą wersją, nigdy diffy.
- Każdy plik jest SAMOWYSTARCZALNY: tożsamość + głos + kontrakty (RAPORT PRACY /
  stan gry) + reguła prawdy.
- Pliki pisane pełną polszczyzną (to treść dla agenta i Tomasza, nie kod). Wyjątek:
  nazwy typów w bloku RAPORT PRACY bez polskich znaków - dopasowuje je parser
  (ma też aliasy z polskimi znakami na wszelki wypadek).
- Link stanu gry (lustro Notion, fallback) jest już WPISANY w pliki (strona
  "Stan gry AGS", https://app.notion.com/p/3a5c00c90b938140b271dc5d18a4920a,
  dostęp przez konektor Notion czatu - strona NIE jest publikowana do webu;
  ostatni fallback = /kontekst w Telegramie).

## Aktualne wersje (22/07/2026, Etap 2 - narzędzia Łącznika)

- **`MASTERPROMPT_CZAT_X_v3.md`** - praca ręczna na X. v3 = v2 + rytuały przez
  narzędzia konektora "AGS Łącznik" (`stan_gry` na starcie, `wyslij_raport_pracy`
  na końcu), fallback = stary rytuał (Notion + plik). v2/v1 zostają w repo jako
  historia.
- **`MASTERPROMPT_CZAT_LINKEDIN_AGS_v3.md`** - praca ręczna na LinkedIn. v3 = v1 +
  te same rytuały narzędziowe (numer wyrównany z X; v2 dla LinkedIn nie istniała).

## PODPIĘCIE KONEKTORA "AGS Łącznik" w claude.ai (instrukcja dla Tomasza)

Wykonujesz RAZ (na koncie, nie per projekt). Wymagania wcześniejsze: (1) rebuild
cm-agenta z endpointami /lacznik/* (paczka tego builda), (2) sekret w app_secrets
(SQL z wyjścia skryptu tworzącego workflow - patrz raport builda).

1. Wejdź na claude.ai i zaloguj się.
2. Kliknij swoje inicjały / awatar w lewym dolnym rogu.
3. Wybierz **Settings** (Ustawienia).
4. W menu ustawień wybierz zakładkę **Connectors** (Konektory).
5. Kliknij **Add custom connector** (Dodaj własny konektor).
6. W polu **Name** wpisz: `AGS Łącznik`.
7. W polu **Remote MCP server URL** wklej URL z raportu builda (kształt:
   `https://ivy147-20147.mikrus.cloud/mcp/lacznik-<SEKRET>`). Advanced settings
   (OAuth) zostaw PUSTE - autoryzacją jest sekret w ścieżce URL.
8. Kliknij **Add** (Dodaj).
9. W NOWEJ rozmowie kliknij ikonę narzędzi (suwaki) przy polu wiadomości i sprawdź,
   że konektor "AGS Łącznik" jest WŁĄCZONY, a na liście widać narzędzia
   `stan_gry` i `wyslij_raport_pracy`.
10. Test: napisz "pokaż stan gry x" - agent ma zawołać narzędzie `stan_gry`
    i streścić stan zgodny z bazą. To jest tap-test a) z briefu.

Konektor działa też w aplikacjach Claude na telefonie i desktopie (to ustawienie
konta). W projekcie czatowym (X / LinkedIn) trzymaj masterprompt v3 - on każe
agentowi używać narzędzi.

## WARIANT B (fallback bez MCP: ChatGPT Custom GPT / dowolny klient HTTP)

Gdy MCP niedostępne (np. praca w ChatGPT), te same operacje przez webhooki n8n
(sekret podaje wołający, walidacja w cm-agent):

- `POST https://ivy147-20147.mikrus.cloud/webhook/chat-raport`
  body JSON: `{"secret":"<SEKRET>","kanal":"x","raport":"[RAPORT PRACY v1] ..."}`
- `GET https://ivy147-20147.mikrus.cloud/webhook/stan-gry?secret=<SEKRET>&scope=x`

Dla Custom GPT: schemat Action w `OPENAPI_LACZNIK_WARIANT_B.yaml` (importujesz
w konfiguracji GPT -> Actions -> paste schema; sekret wpisujesz w Instructions
GPT-a, bo Action nie przekazuje kluczy w query/body sama z siebie).

## Decyzje 22/07 (guziki)

- **Lead Tracker Notion = archiwum do odczytu.** Czat NIE pisze do Lead Trackera;
  cała praca wraca RAPORTEM PRACY do bazy ags_crd (SSOT), stan kontaktów czytany
  ze stanu gry. Pipeline z Trackera zasiał jednorazowy raport liniami
  `nowa_osoba` (wykonane 22/07: Crystalee Beck, Chris Del Grande, Jay Greyson).
- **Content Manager czatowy: BEZ wersji stałej.** Orkiestrację treści robi serwerowy
  CM (Telegram); czatowy CM zdublowałby prawdę o planie i kolejce. Roboczy prompt CM
  (wsad 15/06) pozostaje źródłem doktryny contentowej, nie osobnym agentem czatowym.
- Prompty "content X" i "content LinkedIn" - nieużywane przez Tomasza, nie przerabiamy.

## Format RAPORT PRACY v1 (parser: cm-agent/app/engagement.py)

Typy linii: komentarz, dm_wyslany, dm_odebrany, reakcja, zaproszenie (22/07, wsad
LinkedIn), nowa_osoba, obserwacja. Format BEZ zmian w Etapie 2 - ten sam parser.
Pełny format i pułapki: docs/komponenty/lacznik.md.
