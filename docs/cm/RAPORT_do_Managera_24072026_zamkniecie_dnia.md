# RAPORT DO MANAGERA - zamkniecie dnia 24/07/2026 (okno BE)

Raport czastkowy z poludnia: `RAPORT_do_Managera_24072026_awaria_researchera.md` (awaria) oraz
`RAPORT_do_Managera_24072026_sciezka_sprzedazy.md` (przerobka sciezki). Ten dokument domyka dzien
i jest jedynym, ktory trzeba przeczytac, zeby wiedziec, gdzie stoimy.

## 1. Wynik dnia jednym zdaniem

Dzien zaczal sie od niezamknietej awarii Researchera i konczy mailem do prospekta, ktory otwiera
sie zdaniem "trzymam kciuki za Wiktorie, Emilie, Patryka i Piotrka" - po drodze przerobiona
zostala CALA sciezka od surowca do tekstu, 12 wdrozen, 14 commitow, DDL 029.

## 2. Co jest LIVE (kazda pozycja z dowodem, nie z deklaracji)

| Zmiana | Dowod |
|---|---|
| Awaria "joby failed mimo wyniku" zamknieta | przyczyna z kodu i sondy: opcje maja dwa ksztalty (`label` z modelu, `option_label` z bazy); kazdy job 'failed' mial 4 wiersze `options` i czas 0-3 s |
| Cache oddaje FAKTY (claims + confidence), nie same opcje | job 4c391774 wracal 'completed' z zerem claims i karta mowila "job bez claims" |
| Bramka tozsamosci - TRZY stany | wersja z prawem weta modelu zablokowala 2 poprawne prospekty na 2; teraz blokuje wylacznie BRAK DOWODU |
| Sprzedawca sam wchodzi na strone prospekta | sonda jobu 7411d0ba: z domeny klubu weszly SAME TYTULY (22-52 znaki), firecrawl przyniosl 8 linkow z arXiv o prospectingu |
| Agent sam wylawia adres z wlasnego researchu | Stepownia: research podal `stepownia.pl/...` i orzekl "podaj strone"; teraz wchodzi sam - w lejku siedzi tel 501 130 016 i mail, `site_checked_at` 18:43 |
| Dane kontaktowe w KOLUMNACH (DDL 029) | `contact_email`, `contact_phone`, `contact_person`, `site_checked_at`; nadpisywane tylko gdy puste; widoczne w /pipeline |
| Glos w gotowcu: caly rdzen + cala Voice Bible | do promptu szlo `voice_bible[:2000]` z 22 168 znakow (naglowek pliku), `voice_dna_core` nie byl czytany wcale |
| Prog trafnosci bazy wiedzy 0.55 | materialy o Adamietzu wracaly przy 0.40-0.45 na zapytanie o szkole tanca jako "TECHNIKI" |
| Sekcja anty-szablonowa + zakaz prosby o rozmowe w 1. mailu | model przeredagowal zakazane "15 minut" zamiast je porzucic |
| Czysta wklejka (kontrakt `---GOTOWIEC---`) | model poprzedzil mail wlasnym rozumowaniem o konflikcie RDC |
| Naglowek i stopka gotowca | zgloszenie Tomasza: "naglowek z mailem, telefonem i osoba decyzyjna, w stopce status lejka" |
| Czas wydarzenia w haku | gotowiec "trzymam kciuki PRZED Mistrzostwami", ktore juz sie odbyly (Tomasz byl tam jako sedzia); Stepownia po fixie: "kurs 3 czerwca 2026 (JUZ SIE ODBYLO wzgledem 24/07)" |
| Auto-odrzut slownictwa produktowego (paczka pkt 3) | blocker rozmowy z Piotrem; wykrywanie w GOTOWYM tekscie + jedna proba przepisania + ostrzezenie |
| Czysta polszczyzna w tekstach PL | `compliance.polish_pl` istnial od 06/07, sciezka sprzedazowa nigdy przez niego nie szla |
| Jezyk napisow na grafice z JEZYKA CELU | plansza PL pod angielskim postem AGS (lamie separacje marek) |
| Auto-grafika sterowana flaga `auto_image` per kanal | post X bez grafiki przy LinkedIn z automatem = luka parytetu |
| UI jednego bota: badge "kto mowi" + ciche powiadomienia rutynowe | decyzja Tomasza: osobne boty dopiero po dokonczeniu mozgu |
| Otwarte decyzje mowia CZEGO dotycza i OD KIEDY wisza | slowa Tomasza: "mi te numery nic nie mowia"; 4 przeterminowane zamkniete (status `expired`) |

## 3. Dowod skutecznosci na tym samym prospekcie w ciagu jednego dnia

| | rano | wieczorem |
|---|---|---|
| tozsamosc | niepewna / niepotwierdzona | **potwierdzona** (domena w dowodach) |
| dane kontaktowe | "brak w evidence" | telefon i mail w kolumnach lejka |
| sygnaly kupna | "brak bezposrednich" | aktywna zbiorka, obozy, breaking jako dyscyplina olimpijska |
| hak | "zapytaj o proces zapisow" | kampania na Mistrzostwa Europy, z imionami zawodnikow |
| otwarcie maila | "widze, ze StandART prowadzi..." | "trzymam kciuki za Wiktorie, Emilie, Patryka i Piotrka" |
| prosba o rozmowe | "masz 15 minut w tym tygodniu?" | pytanie o obsluge zapisow po sezonie obozowym |

## 4. Cztery moje wlasne regresje, zlapane i naprawione tego samego dnia

Podaje je, bo KLASA bledu jest wazniejsza niz sam blad i wszystkie cztery daja ten sam objaw:
system twierdzi, ze dziala, a czlowiek patrzy w cisze.

1. **`Decimal` w payloadzie meldunku** - dolozylem `overall_confidence` czytane z NUMERIC; JSON
   tego nie serializuje, INSERT lecial wyjatkiem, wyjatek byl POLYKANY. Joby konczyly sie
   'completed' i nikt sie o tym nie dowiadywal. Fix: sanityzacja calego payloadu + ESKALACJA
   zamiast ciszy. Lekcja: cichy `except` na sciezce powiadamiania zamienia awarie w niewidzialna cisze.
2. **Nowy `material_type` bez DDL** (AP-304 recydywa) - CHECK nie znal wartosci, INSERT padl.
3. **Tap-test na wartosci, ktorej NIE MA w bazie** - wizytowke testowalem adresem z `www`,
   a w lejku jest gola domena bez wpisu DNS. Test przechodzil, kod nie dzialal, Tomasz przez
   pol godziny patrzyl w cisze. Lekcja: testuj wartoscia, ktora system faktycznie posiada.
4. **`contacts.contact_id` zamiast `contacts.id`** - zapytanie o osobe decyzyjna lecialo
   wyjatkiem, wiec naglowek gotowca ZAWSZE pokazywal "nieustalona". Znowu AP-304.

Wniosek systemowy do rozwazenia przez Managera: **kazdy cichy `except` na sciezce, ktora ma
kogos powiadomic, jest bledem projektowym.** Proponuje traktowac to jako kanon, nie jako
lekcje jednorazowa.

## 5. Paczka #1 Managera - status

Pelny triage per punkt: `docs/briefs/PACZKA_1_MANAGER_24072026.md`.

- **pkt 3 (BLOCKER Piotr/Adamietz) ZROBIONY** - auto-odrzut slownictwa produktowego, dwuwarstwowy.
- **pkt 6 ZROBIONY** - piapiasilva to **Pia Silva**, boutique branding, autorka "Badass Your
  Brand"; `contacts.id` 896d2232-0aa9-4ae7-914f-2e79fbf2fc2b, tier Buyer, etap commented,
  ostatnia interakcja 22/07, handles `{"linkedin":"piapiasilva"}`. **Klucz do odnalezienia lezy
  w engagement_log, nie w handle** - szukac po nazwisku i firmie.
- **pkt 5 SPRAWDZONY** - kolumny `contacts.who_is_who` NIE MA, trzeba ALTER TABLE.
- **pkt 2, 8 DO ZROBIENIA** - najtansze z calej paczki (edycja masterpromptu + heurystyka
  w compliance.py).
- **pkt 1, 5, 7 -> JEDEN DDL 030.** UWAGA dla pkt 7: `contacts` NIE MA kolumny `dm_history`;
  historia DM zyje w `engagement_log` per `contact_id`. Regula fail-closed musi opierac sie na
  engagement_log albo dopisujemy kolumne w tym samym DDL - **prosze o decyzje.**
- **pkt 4 WYMAGA KOREKTY ZAKRESU (blokujaca).** Sciecie `icp_tier` do 5 wartosci wywali 45
  zywych wierszy: Watch 37, Premium 7, Mid 1 (sonda z 177 kontaktow). Rekomendacja: DODAC 'Inne'
  do istniejacej listy, a migracje legacy potraktowac jako osobna decyzje. **Nie ruszam bez zgody.**

## 6. Decyzje Tomasza podjete dzisiaj (wiazace, zapisane w kanonach)

1. **Konflikt interesow RDC ma JEDNO kryterium: miasto Opole.** Poprzednia wersja miala dwa
   kryteria naraz (lista miast + promien 50 km) i Sprzedawca w jednej turze orzekl dwie
   sprzeczne rzeczy, blokujac gotowy outreach. Regula z dwoma kryteriami nie jest regula.
2. **Jeden bot, lepszy interfejs.** Osobne boty telegramowe dla wszystkich agentow budujemy
   docelowo, gdy mozg bedzie gotowy (kanon WARSTWY: interfejs jest wymienny).
3. **Poczta dla agenta ODLOZONA** - "na razie wysylam recznie, ale zapytaj mnie o to pozniej".
   Trzy warianty i dwa ograniczenia (zgoda na informacje handlowa wg art. 10 uslug droga
   elektroniczna; rozgrzewka domeny z SPF, DKIM, DMARC) w briefie.
4. **Przeterminowane decyzje zamykamy statusem `expired`, nie DELETE** - `agent_decisions`
   karmi petle nauki, wiec usuniecie wierszy zafalszowalo by statystyki zgodnosci.

## 7. Co czeka na Managera (pytania, nie prosby o akceptacje)

1. Punkt 4 paczki: dodajemy 'Inne' do istniejacej listy czy migrujemy 45 legacy kontaktow?
2. Punkt 7: regula fail-closed na `engagement_log` czy dokladamy `contacts.dm_history`?
3. Cache semantyczny Researchera: globalnie OFF czy plaster na fraze 'prospect research'?
   Bilans plastra: 0 korzysci, 6 jobow z cudza firma.
4. Grafiki na X: wlaczyc `auto_image`? 31 postow tygodniowo, 17 juz ma grafike z materialu,
   automat dotknalby czternastu (koszt promptu ~$0,017 + generacja obrazu poza ledgerem).
5. Czy podnosimy "cichy except = blad projektowy" do rangi kanonu?

## 8. Dlug techniczny przekazany dalej (z dowodami, nie z przeczuc)

- **Kaskada Researchera nie czyta strony badanego podmiotu.** Obejscie dziala TYLKO w sprzedazy;
  kazdy inny konsument dostaje tytuly zamiast tresci. To najwazniejsza otwarta wada systemu.
- Osoba decyzyjna: mamy pobrana podstrone instruktorow, mozna z niej wyciagnac nazwisko
  (instruktor to nie zawsze decydent - potrzebna regula).
- `prospect_url` wybiera podstrone zamiast domeny glownej (Stepownia: `/author/dudzikdariusz`).
- Anglicyzmy w promptach wewnetrznych: kilkadziesiat miejsc, czesc to tokeny parsera - przeglad
  recznie, nie hurtem.
- Sprzedawca nie widzi zrzutow ekranu (wrzutka trafia w routing zdjec, nie do `sales.handle_chat`).

## 9. Dokumentacja zaktualizowana w tym samym dniu (kanon DOKUMENTACJA ZYJE)

- `docs/komponenty/agent-sprzedazy.md` - wizytowka, kolumny kontaktowe, bramka trzystanowa,
  naglowek i stopka, czas wydarzenia, czysta polszczyzna, tozsamosc prospekta w zapytaniu.
- `docs/komponenty/researcher.md` - incydent 24/07 z przyczyna zrodlowa, skala kontaminacji,
  regresja `Decimal`, OTWARTE: kaskada nie czyta stron podmiotu.
- `docs/komponenty/grafika.md` - jezyk napisow z jezyka celu.
- `docs/komponenty/rozmowa-cm.md` - badge "kto mowi", ciche powiadomienia.
- `docs/db/SCHEMA_ags_crd.md` - DDL 028 (`outreach_example`) i 029 (kolumny kontaktowe).
- `docs/SYSTEM_DATAFLOW.md` - wpis Agenta Sprzedazy przepisany (byl nieaktualny: mowil
  "research critical", co kanon kosztowy zabrania od 20/07), sekcja stanu i legacy odswiezona.
- `docs/RESUME_MASTERPROMPT_24072026.md` - stan na 20:00 + pelna lista zaleglosci w czterech
  blokach (paczka, decyzje, dlug, kampania).
- Briefy: `PACZKA_1_MANAGER_24072026.md`, `BRIEF_POCZTA_I_CRM_GHL_24072026.md`.

## 10. Kampania - stan faktyczny

- **StandART**: gotowiec WYSLANY recznie przez Tomasza (wersja ciepla, hak sedziowski
  z Klagenfurtu - Tomasz sedziowal na tych mistrzostwach). Czeka oznaczenie "wyslalem".
- **Stepownia**: research potwierdzony (tel 501 130 016, Dariusz Dudzik jako decydent),
  gotowiec do napisania.
- **La Cultura, STC**: research gotowy, gotowce do napisania.
- **Adamietz**: follow-up telefoniczny do Piotra - najwiekszy deal w lejku, blocker sprzedazowy.
