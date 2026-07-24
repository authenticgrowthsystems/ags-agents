# RAPORT DO MANAGERA - sciezka sprzedazy od surowca do maila (24/07/2026)

## Jednym zdaniem

Dzien zaczal sie od niezamknietej awarii Researchera, a skonczyl mailem, ktory cytuje imiona
zawodnikow z aktywnej zbiorki klubu - po drodze zlapalismy szesc wad, z czego trzy byly moje
wlasne regresje z tego samego dnia.

## Co zmienilo sie w produkcie (kolejnosc = kolejnosc odkrywania)

1. **Awaria "joby failed mimo wyniku" ZAMKNIETA.** Przyczyna: opcje maja dwa ksztalty (`label`
   z modelu, `option_label` z bazy); meldunek czytal jeden i wywracal sie PO zapisaniu wyniku.
2. **Cache oddaje fakty, nie same opcje.** Job z cache konczyl sie "gotowy" z zerem claims,
   a karta prospekta mowila "job bez claims".
3. **Bramka tozsamosci, trzystanowa.** Wersja z prawem weta modelu zablokowala 2 poprawne
   prospekty na 2. Dowod liczy sie z DANYCH (domena w evidence, miasto w claims), deklaracja
   modelu tylko obniza stan do ostrzezenia. Blokuje wylacznie BRAK dowodu.
4. **Glos w outreachu.** Model dostawal 9% Voice Bible (2000 z 22 168 znakow - naglowek pliku),
   zero osobistego rdzenia i cudzy case jako "techniki" (materialy o Adamietzu przy 0.40-0.45
   podobienstwa do zapytania o szkole tanca). Teraz: caly rdzen + cala Voice Bible, prog
   trafnosci 0.55, sekcja anty-szablonowa i wzorce z wiadomosci, ktore Tomasz naprawde wyslal.
5. **Sprzedawca sam wchodzi na strone prospekta.** Sonda pokazala, ze kaskada Researchera
   przyniosla z domeny klubu SAME TYTULY (22-52 znaki), a adapter firecrawl osiem linkow
   z arXiv o prospectingu AI. Wizytowka: strona glowna + do 3 podstron, regexem mail i telefon.
6. **Dane ida do KOLUMN (DDL 029).** contact_email, contact_phone, contact_person,
   site_checked_at; nadpisywane tylko gdy puste. Widoczne w /pipeline.
7. **Gotowiec ma naglowek i stopke.** Do kogo leci (osoba, mail, telefon, strona, ostrzezenie
   o tozsamosci), czysta wklejka, stan lejka i ktory to kontakt.
8. **UI jednego bota** (decyzja Tomasza: osobne boty dopiero po dokonczeniu mozgu): badge
   "kto mowi" w kazdej odpowiedzi, log-bot i powtorki przypomnien wyciszone.

## Trzy regresje wprowadzone i naprawione TEGO SAMEGO DNIA (uczciwie)

- **Decimal w payloadzie meldunku.** Dolozylem `overall_confidence` czytane z NUMERIC; Decimal
  nie serializuje sie do JSON, INSERT lecial wyjatkiem, wyjatek byl polykany. Joby konczyly sie
  `completed` i nikt sie o tym nie dowiadywal. Fix: sanityzacja calego payloadu + eskalacja
  zamiast ciszy. **Lekcja: cichy `except` na sciezce powiadamiania zamienia awarie w cisze.**
- **Typ materialu bez DDL.** Kod dopisal `outreach_example`, CHECK go nie znal (AP-304 recydywa).
- **Test na wartosci, ktorej nie ma w bazie.** Wizytowke testowalem adresem z `www`, a w lejku
  jest gola domena bez wpisu DNS. Test przechodzil, kod nie dzialal, Tomasz patrzyl w cisze.
  Fix: cztery warianty adresu + paragon mowi wprost, gdy strony nie udalo sie otworzyc.

## Dowod koncowy (ten sam prospekt, ten sam dzien)

| | rano | po poludniu |
|---|---|---|
| tozsamosc | niepewna | **potwierdzona** (domena w dowodach) |
| dane kontaktowe | "brak w evidence" | **510-555-099 + recepcja@**, w kolumnach lejka |
| sygnaly kupna | "brak bezposrednich" | aktywna zbiorka, obozy, breaking jako dyscyplina olimpijska |
| hak | "zapytaj o proces zapisow" | **kampania na Mistrzostwa Europy w Klagenfurcie, z imionami** |
| otwarcie maila | "widze, ze StandART prowadzi..." | "trzymam kciuki za Wiktorie, Emilie, Patryka i Piotrka" |
| CTA | "masz 15 minut w tym tygodniu?" | pytanie o obsluge zapisow po sezonie obozowym |

## Zostaje otwarte

- **Kaskada Researchera nie czyta strony badanego podmiotu** - obejscie dziala tylko w sprzedazy,
  kazdy inny konsument dostaje dalej tytuly zamiast tresci (docs/komponenty/researcher.md).
- **Cache semantyczny**: globalnie OFF czy plaster na fraze 'prospect research' - decyzja Tomasza.
- **Osoba decyzyjna**: mamy pobrana podstrone z instruktorami, mozna z niej wyciagnac nazwiska
  (instruktor to nie zawsze decydent - potrzebna reguła).
- **Poczta i CRM (GoHighLevel)**: brief gotowy, docs/briefs/BRIEF_POCZTA_I_CRM_GHL_24072026.md.
