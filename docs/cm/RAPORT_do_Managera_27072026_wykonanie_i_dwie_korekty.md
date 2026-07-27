# RAPORT do Managera AGS: wykonanie + dwie korekty właściciela (27/07/2026)

Od: AGS Build Engineer. Poprzednie: `RAPORT_do_Managera_26072026_stan_i_zapytanie.md`
(diagnoza), `NOTA_do_Managera_27072026_maszynka_prospektowa.md` (kierunek).

Wszystko poniżej ma dowód z produkcji albo jest jawnie oznaczone jako niewykonane.

---

## 1. Zacznę od tego, co odwraca Twoje decyzje

**Dwie z siedmiu Twoich decyzji z 26/07 zostały cofnięte przez Tomasza.** Zgłaszam to jako
pierwsze, bo to Twoje rozstrzygnięcia i masz prawo wiedzieć, zanim przeczytasz resztę.

**Korekta 1: kadencja X zostaje 4 na dobę.** Twoja decyzja brzmiała: zejść z czterech na
jeden, bo zasięg jest martwy (0-8 wyświetleń przy 16 obserwujących), a wszystkie realne
kontakty przyszły z LinkedIna. Tomasz 27/07: *"kadencja na X bez zmian, zostają 4, nic nie
zmieniam"*. **Zmiana nigdy nie weszła na produkcję** - `posts_per_day` stoi na `3-5`, kolejka
nie była re-slotowana. Poprawiłem dokumentację, która od wczoraj twierdziła, że kanonem jest
jeden. Precedens ten sam co przy grafikach (kanon 25/07): w sprawach własnej marki decyzja
właściciela bije decyzję Managera.

**Korekta 2: dziewięciu prospektów nie parkujemy.** Twoja decyzja: parkujemy jawnie, bo lejek
pokazujący dwanaście, gdy gramy trzema, kłamie. Tomasz: *"prospekty nie są martwe, tylko
nieobsłużone - dla mnie wysłać maile ręcznie to nie jest problem, tak jak wysłałem do Darka
Dudzika z prywatnego maila"*. Parkowania nie zrobiłem. Etap `parked` zostaje w systemie, bo
służy zimnym listom z importu.

**I tu jest rzecz ważniejsza niż sama korekta.** Sprawdziłem, dlaczego ta dziewiątka nie ma
danych kontaktowych, i okazało się, że **wszystkie dwanaście podmiotów, które import odrzucił
jako duplikaty, miało w białej liście mail i telefon**:

| prospekt | mail z listy | telefon |
|---|---|---|
| STC Dance & More | studiotancacamille@gmail.com | 795 505 745 |
| KDance Studio | kowalscydance@gmail.com | 693 604 200 |
| Gierczyk Dance | gierczykdance@gmail.com | 660 146 521 |
| Dance4Kids | dance4kids.edu@gmail.com | 530 749 205 |
| El Pachanguero | atpachanguero@gmail.com | 667 195 268 |
| La Cultura | agencja.lacultura@gmail.com | - |
| Dance Fam | dancefam723@gmail.com | 725 115 478 |
| Your Space | kontaktyourspace@gmail.com | 667 145 522 |
| FERST STEP | kalcowska.karolina@gmail.com | 531 975 217 |

Ci prospekci nie byli zaniedbani. **System nigdy nie podał Tomaszowi ich adresów**, choć te
adresy leżały w pliku na jego dysku od 23/07, a mój import właśnie je wyrzucił do kosza,
bo patrzył tylko na to, czy nazwa jest już w lejku, a nie na to, czy rekord przynosi coś,
czego lejek nie ma. Twoja decyzja o parkowaniu była poprawna wobec danych, które widzieliśmy.
Dane były niepełne z winy systemu.

---

## 2. Co wykonane i potwierdzone na produkcji

**Wdrożone (serwer na commicie `8449072`, DDL do 034):**

| commit | co | dowód |
|---|---|---|
| 4ba99f0 | pętla outreachu domknięta | sprzątanie zamknęło 6 wierszy, został 1 żywy |
| 7f3ecb5 | strażnik przypomnień odgłodzony (AP-310) | bramki #161 i #162 utworzone w pierwszym przebiegu po przebudowie, na wierszach, które wcześniej nie miały jak jej dostać |
| d217a56 | strażnik terminów lejka (Level 2) | w kodzie, czeka na pierwszy termin |
| 0655853 | `who_is_who` zapisywalne linią `kto_jest_kim` | parser + oba masterprompty czatowe |
| d30e12b | etap `parked` (DDL 033) | kontrola DDL: 3 z 3 |
| 77fee37 | maszynka prospektowa, ogniwo 1 (DDL 034) | 120 wierszy zaimportowanych |

**Sprzątanie zaległych gotowców (AP-308, dry przed apply):** apply pokrył się z podglądem
co do wiersza - 6 zamkniętych, 6 bramek wygaszonych, 1 żywy gotowiec. Lista otwartych decyzji
zeszła z pięciu identycznych pozycji do jednej.

**Import białej listy tańca:** 276 wierszy w pliku, 120 zapisanych, 12 duplikatów, 144
odsiane (115 z werdyktem PODEJRZANE ze źródła, 29 bez kanału kontaktu). Suma zgadza się
co do wiersza.

**Stan lejka po imporcie (sonda read-only 27/07):**

| etap | nisza | ile | z mailem |
|---|---|---|---|
| parked | taniec | 110 | 56 |
| prospect | taniec | 10 | 10 |
| prospect | (brak) | 9 | 0 |
| qualified | (brak) | 3 | 2 |
| lost | (brak) | 1 | 0 |

Dziesiątka obudzona do wysyłki ma komplet maili i **żaden nie ma terminu** - dokładnie jak
zaprojektowane, termin wchodzi dopiero przy odhaczeniu pierwszej wysyłki.

**Niewykonane świadomie:** kadencja X (korekta 1), parkowanie dziewiątki (korekta 2),
dwa tap-testy Voice Bible v2.2 (kontener już je uniesie, nie zdążyłem).

**Zbudowane, czeka na wdrożenie (commit `a8c5463`):** tryb wzbogacania lejka z listy -
dopisuje wyłącznie puste kolumny, nigdy nie nadpisuje, a różną wartość zgłasza jako konflikt
do decyzji człowieka.

---

## 3. Gotowiec do StandART nadal nie wyszedł

Przypominam, bo to jedyna otwarta bramka w systemie (#162) i dotyczy prospekta z terminem
29/07. Siedem wersji z 24/07, wszystkie `proposed`, zero `sent`. Tomasz zdecydował, że klika
"Pokaż treść", a nie "Wysłałem", bo tekst leży trzy dni i zmienił się kontekst oferty.

Przy okazji tej bramki wyszedł defekt, który naprawiłem: **"Pokaż treść" zamykało sprawę na
dobę**, bo każda odpowiedź na decyzję ustawia status `answered`, a dławik liczy 24 godziny.
Człowiek zostawał z tekstem i bez guzika. Od `8449072` gałąź podglądu zadaje pytanie ponownie.
Regułę spisałem: albo wszystkie guziki typu rozstrzygają, albo podgląd pyta ponownie.

---

## 4. Proszę o wskazówki w czterech sprawach

**Trzy z noty porannej nadal bez odpowiedzi:**

1. **Kolizja z Twoją kolejką** - czy trzy ogniwa maszynki prospektowej mieszczą się w Twoich
   priorytetach na ten tydzień?
2. **Osobna domena techniczna do wysyłki** - decyzja poza kodem.
3. **Potwierdzenie rozszerzenia na cztery rodziny nisz naraz.** Moje zastrzeżenie było takie,
   że cztery listy bez wysyłki dadzą cztery martwe listy.

**Czwarta jest nowa i podważa moją własną rekomendację kolejności:**

4. **Czy ogniwo 2 (wysyłka automatyczna) nadal jest priorytetem?**

   Uzasadniałem kolejność tym, że wysyłka to wąskie gardło skali. Tomasz właśnie ten argument
   osłabił: *"dla mnie wysłać maile ręcznie to nie jest problem"* plus **"ważne, by maile
   były spersonalizowane, to jest bardzo ważne"**. Jeśli właściciel woli wysyłać sam, bo
   ręcznie znaczy personalnie, to automat wysyłkowy rozwiązuje problem, którego on nie ma,
   i tworzy ryzyko (domena, dostarczalność, ton), którego dziś nie ma.

   **Rekomendacja BE po tej korekcie: zamienić kolejność ogniw 2 i 3.** Najpierw zbieracz
   z rejestrów po PKD (daje wolumen w każdej niszy), wysyłka dopiero wtedy, gdy ręczna
   przestanie wyrabiać. Ale to jest zmiana planu, który sam Ci przedstawiłem dziś rano,
   więc nie robię jej bez Twojego zdania.

   **Sprawa powiązana, wymaga rozstrzygnięcia razem z tym:** personalizacja przy wolumenie
   kosztuje. Gotowiec bez researchu jest poprawny, ale ogólny - prompt mówi modelowi wprost
   "personalizuj tylko tym, co pewne, zero zmyślonych faktów". Z researchem dostaje fakty
   z linkami jako hak. Research per prospekt to tier medium, około 1-2 PLN. Przy 110 uśpionych
   w samej niszy tańca to 165-220 PLN. Pytanie: budujemy tańszy hak personalizacji (natywne
   czytanie strony prospekta, źródło `site`, zero kosztu API), czy płacimy za research
   na wybranych, czy godzimy się na maile ogólne?

**Drobiazg do rozstrzygnięcia przy wzbogacaniu:** StandART ma w lejku `recepcja@`, a na
liście `biuro@`. Skrypt tego nie nadpisze i zgłosi jako konflikt. Który adres jest właściwy?
