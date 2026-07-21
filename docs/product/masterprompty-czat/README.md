# Masterprompty czatowe (LACZNIK, etap 1)

Pliki do WKLEJENIA przez Tomasza do projektu w aplikacji czatowej na abonamencie
(Claude, ChatGPT - dowolny czat). Wrzucasz RAZ do projektu, potem kazda sesja pracy
zaczyna sie sama: agent czyta stan gry z linku Notion i konczy sesje blokiem
[RAPORT PRACY v1], ktory wklejasz do Telegrama (bot AGS).

## Zasady

- Wersjonowanie jak prompty agentow: pelny nowy plik z podbita wersja, nigdy diffy.
- Kazdy plik jest SAMOWYSTARCZALNY: tozsamosc + glos + kontrakty (RAPORT PRACY /
  stan gry z linku) + regula prawdy.
- `<LINK_STAN_GRY>` w pliku podmienia Tomasz na publiczny link strony Notion
  "Stan gry AGS" (zaklada ja przy wdrozeniu Lacznika; fallback = /kontekst w Telegramie).
- Masterprompty ROBOCZE Tomasza (te, ktorymi juz uruchamial agentow w czacie) sa
  WSADEM: przy ich dostarczeniu BE scala je z wersja stala i podbija wersje pliku
  (decyzja Tomasza 21/07, koncept LACZNIK_SYNCHRONIZACYJNY_21072026.md).

## Pliki

- `MASTERPROMPT_CZAT_X_v1.md` - praca reczna na X (komentarze, DM, poznawanie ludzi).
- LinkedIn / sprzedaz: powstana przy dostarczeniu wsadu Tomasza (ten sam szkielet).
