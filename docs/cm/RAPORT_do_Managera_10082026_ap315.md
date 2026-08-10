# RAPORT do Managera - 10/08/2026 - AP-315, D-008b, D-015

**Jednym zdaniem:** post opublikowany 04/08 przez szesc dni niosl na LinkedInie **wypowiedz
modelu zamiast tresci**, pod nazwiskiem Tomasza; zdjety, przyczyna zrodlowa znaleziona za trzecim
podejsciem, trzy warstwy zabezpieczen na produkcji, przy okazji zamkniete D-008, D-008b
i polowa D-015.

---

## 1. INCYDENT

Material `#344`, zatwierdzony 03/08 wieczorem, opublikowany 04/08 o 16:01. Trescia posta bylo:

> "I've reviewed the canonical text and Voice Bible. This is a technical article about agent
> responsibility separation, strong content. However, I need to flag an issue before..."

To CM mowiacy do operatora o materiale, razem z nazwa wewnetrznego artefaktu. **Szesc dni
na profilu, 87 wyswietlen.** Zdjety recznie 10/08, wycofany z bazy skryptem
`docs/ops/SQL_wycofanie_344_10082026.sql` (ksiega + wiersz kolejki + material), temat wrocil
do produkcji.

**Zaden z pieciu poziomow kontroli go nie zatrzymal**, bo kazdy pytal o co innego:

| kontrola | o co pytala | dlaczego przepuscila |
|---|---|---|
| `strip_meta_header` | czy pierwsze linie maja KSZTALT naglowka | tekst byl proza |
| `compliance.enforce` | myslniki, slownictwo, polszczyzna | wszystkie odpowiedzi poprawne |
| bramka HITL | **czy zatwierdzone** | bylo - tapniete odruchowo |
| raport Managera | **czy kolejka pusta** | byla, bo material wyszedl |
| odczyt `stan_gry` 04/08 rano | **jaki status wiersza** | tresc stala obok, nieprzeczytana |

**Sformulowanie z dnia: to projekt, nie wypadek.** O stan i o forme latwo zapytac, o gatunek
trzeba zapytac swiadomie. Zapisane jako **AP-315**.

---

## 2. PRZYCZYNA ZRODLOWA - znaleziona za TRZECIM podejsciem

Dwie pierwsze diagnozy byly bledne i obie brzmialy pewnie:

1. **"Bezpiecznik gatunku zatrzyma nastepna taka tresc"** - obalone tego samego dnia: druga
   wadliwa karta dostala od niego `([], [])`, zero trafien. Inna awaria tej samej klasy,
   zupelnie inne slownictwo.
2. **"Sprawca jest `compliance._rewrite`"** - obalone odczytem kodu: tekst z 04/08 zaczyna sie
   od "I've reviewed the canonical text and **Voice Bible**", a Voice Bible wchodzi przez
   `system_blocks(brand)`. **`_rewrite` nie przekazuje bloku systemowego w ogole.** Model wolany
   ta droga fizycznie nie widzi Voice Bible.

**Prawdziwa przyczyna:** `brand_config.style_learned` dla AGS zawiera szesc regulek
wydestylowanych z RECZNYCH korekt Tomasza. Wszystkie **po polsku** i wszystkie w ksztalcie
**polecenia**:

> - Zamiast "Trzeba zaprojektowac" pisze "To wymaga konkretnej pracy. Trzeba zaprojektowac"
> - Przed spojnikiem "i" nie stawia sie przecinka.

`generate._learned_style` doklada ten blok do **KAZDEJ** generacji - i wariantu per kanal,
i tekstu-matki. LinkedIn publikuje po angielsku. Model dostaje wiec dwa zadania naraz
i wykonuje to drugie. Obie wadliwe tresci to model **wyliczajacy, co dostal**.

Potwierdzenie: druga karta wprost napisala "you didn't provide me with **the text to translate**.
In the message there is: - Instructions on how **I should translate to English**".

---

## 3. CO WESZLO NA PRODUKCJE

Trzy warstwy, kazda zweryfikowana **zlym wsadem na dzialajacym kontenerze**, nie tylko testem.

| warstwa | co robi | dowod na produkcji |
|---|---|---|
| **filtr jezykowy regulek** (przyczyna) | do promptu wchodza tylko regulki w jezyku wyjscia; jezyk czytany z samego wpisu, bez DDL | blok EN = `''`, blok PL = komplet szesciu |
| **bramka wyjscia filtra** | odpowiedz `_rewrite` musi byc PRZEROBKA, mierzone pokryciem slow; ponizej 0.35 wraca tekst wejsciowy + wpis do `agent_logs` | rozmowa 0.0, uczciwa korekta 0.923, prog 0.35 |
| **bezpiecznik gatunku** | dwie listy fraz + prog nagromadzenia; blokuje PRZED zapisem `handed_off`, czyli takze materialy zatwierdzone guzikiem w n8n | wyciek `bez_furtki=True` przy `twarde=[]`, dobry post `False` |

**Zestaw: 30/30.** Trzy nowe pliki testowe, kazdy karmiony PRAWDZIWYMI tekstami z produkcji,
nie wymyslonymi. Lacznie **jedenascie celowych przywrocen wady** - kazda bramka zobaczona,
jak nie dziala, zanim jej zaufalismy (AP-314).

### Trzy razy dane obalily to, co przed chwila bylo pewne

- lista twardych fraz miala `voice bible` jako pewniak → **audyt 152 publikacji znalazl ja
  w prawdziwym poscie Tomasza z 11/07** ("clear stages, compliance checks, one voice bible").
  Fraza zeszla do miekkich, a furtki broni teraz LICZNIK: trzy frazy miekkie naraz = brak wyjscia.
  Wyciek ma piec, dobry post ma jedna. Prog sprawdzony na calym korpusie PRZED commitem:
  **`BEZ FURTKI: 0`**.
- filtr jezykowy oparty na `not looks_polish` → **test na prawdziwych regulkach obalil go
  w pierwszym przebiegu**: `Zamiast "poprawiania promptu o jedno zdanie" pisze...` nie ma ani
  jednego ogonka ani slowa funkcyjnego. Bramka padala OTWARTA. Zmienione na POZYTYWNY test
  angielszczyzny, jednokierunkowy.
- `_rewrite` jako przyczyna → obalone przez brak bloku systemowego (wyzej).

---

## 4. ZAMKNIETE PRZY OKAZJI

- **D-008 ZAMKNIETE.** Sciezka `approved -> handed_off -> published` przebiegla SAMA dwa razy:
  `#344` 04/08 16:01, `#358` 05/08 16:01.
- **D-008b ZAMKNIETE.** Slownik `content_items.status` zwezony, `dispatching` zdjete, obraz
  `cm-agent:prev-d008` skasowany. W samym skrypcie znaleziona wada przed uruchomieniem: `DROP`
  i `ADD CONSTRAINT` staly poza transakcja, wiec nieudany `ADD` zostawialby tabele **bez zadnego
  ograniczenia** przy bledzie wygladajacym na "nic sie nie stalo". Dolozone `BEGIN/COMMIT`
  i druga bramka nazywajaca wartosc spoza listy.
- **D-015 CZESCIOWO ZAMKNIETE.** Realny czas publikacji to **`max(slot planu, czas kolejki)`**
  plus tik Schedulera - nie sam czas kolejki, jak twierdzil wpis przez tydzien. Dowod: `#344`
  kolejka 15:49 i `#358` kolejka 15:50 wyszly **oba o 16:01**. Meldunek podaje juz te wartosc;
  dowod w biegu z 18:09 (slot 11/08 **16:00**, pelna godzina - a `humanize_slot` nigdy nie zwraca
  rownej godziny, wiec to nie moze byc czas kolejki).

---

## 5. OTWARTE

| dlug | stan |
|---|---|
| **D-015 reszta** | karta w `/karty` czyta material, wiec przy kolejce pozniejszej niz slot pokazuje do 15 min za wczesnie |
| **D-016 NOWY** | po tapnieciu guzika bot mowi "Publikacja za chwile", a CM sekunde pozniej melduje slot za dobe. Siedzi w n8n, **nie da sie naprawic rebuildem** |
| `translate_text` | kopia PL nie jest tlumaczeniem, tylko osobna wersja (ma zdania, ktorych nie ma w angielskiej). Nikt tego nie sprawdzal |
| **20 decyzji gnijacych** | 14 kart materialow po 12 dni, 3 followupy sprzedazowe, `#179` (21 materialow X) 11 dni |
| zapasc zasiegu LI | 8-13/07: 380-690 wyswietlen dziennie; 27/07-04/08: 39-84 |
| `SYSTEM_DATAFLOW.md` | nietkniety od 27/07, brakuje dwoch tygodni. **Osobna sesja, nie piec minut** |
| brak `docs/komponenty/operacje.md` | modul z 02/08 bez dokumentu |

---

## 6. DECYZJE, KTORE ZAPADLY (Manager, 10/08)

1. Post z 04/08 usuniety recznie, `#344` wycofany w bazie, material wraca do produkcji.
2. Bezpiecznik gatunku priorytetem nad wszystkim innym.
3. **Zasada na stale: jesli mozesz to odczytac, nie pytaj.**
4. D-008b wykonane, `prev-d008` skasowany.
5. `d5cd43e` domkniete regula `max()`.
6. AP-315 do kanonu.

Korekty w trakcie, wszystkie trafne:

- **`kolejka` i `meldunek` z twardych do miekkich** - "TNM pisze po polsku do uslug lokalnych,
  gdzie kolejka klientow jest naturalna; twarda blokada na zwyklym slowie odpali raz,
  w najgorszym momencie, i bedzie wygladac jak zepsuty system". Kryterium podzialu list wziete
  z tego zdania i zapisane w AP-315.
- **Odrzucenie mojej propozycji "drugie zatwierdzenie przechodzi" bez podzialu klas** -
  z uzasadnieniem, ktorego nie nazwalem: wpadka 04/08 wziela sie z odruchowego tapniecia, wiec
  furtka bez rozdzialu odtwarzalaby ten sam tryb awarii.
- **"Niezweryfikowanego nie zmiekczamy, tylko usuwamy"** - przy zdaniu "roughly doubles your
  debugging time". Zastapione arytmetyka, ktora czytelnik sprawdzi w glowie.
- **Anegdota otwierajaca zastapiona prawdziwa** - awaria 29/07-03/08, w ktorej dwa agenty czekaly
  na siebie, nikt nie zglosil bledu, a kolejka stala pusta. Z granica: post z 04/08 nie idzie
  do tresci publicznej, bo byl zaprzeczeniem obietnicy produktu; awaria z lipca idzie, bo jest
  lekcja, ktorej post uczy, przezyta na sobie.

---

## 7. WNIOSKI POZA POPRAWKAMI

1. **Petla uczenia sie z korekt czlowieka jest wektorem wstrzykniecia.** Wszystko, co system
   zapamietuje i wklada z powrotem do promptu, moze byc POLECENIEM zamiast preferencja. To nie
   wada jednej funkcji, tylko wlasciwosc kazdej petli "ucz sie z poprawek" - a takich bedzie
   przybywac.
2. **Regulki stylu maja jezyk i to jest ich czesc, nie metadana.** Regula o przecinku przed "i"
   jest bez sensu w angielskim tekscie i model ma racje, pytajac, o co chodzi.
3. **Kazde wywolanie modelu, ktorego wynik wraca do potoku jako DANE, potrzebuje bramki wyjscia** -
   bo "odpowiedz o zadaniu" i "wynik zadania" sa dla kodu nieodroznialne, oba sa napisem.
4. **Zamknieta lista fraz zawsze bedzie o krok za modelem.** Dwie awarie, dwa rozne slowniki.
   Miary relacyjne (pokrycie slow, licznik trafien) sa odporne tam, gdzie listy nie sa.
5. **Odczyt produkcji rozstrzygal za kazdym razem, czytanie kodu nie.** Kod pozwalal na wszystkie
   trzy diagnozy. To juz trzeci raz w tym projekcie, gdy **dane obalily przeslanke wpisu** -
   po D-011 i po migracji D-008.

---

## 8. CZEKA NA TOMASZA

- **11/08 ok. 16:00** - publikacja materialu "Granica miedzy dwoma agentami". Domyka D-015
  end-to-end i jest pierwszym tekstem tego systemu powstalym bez polskiej instrukcji w promptcie.
- **Decyzja o priorytecie na jutro:** 20 gnijacych decyzji, reszta D-015, D-016 (okno n8n),
  `SYSTEM_DATAFLOW`, albo fakty build-in-public do masterpromptu CM.

**Commity:** `8d73b3d`, `2c6d820`, `15a734e`, `6a18d4a`, `513de40`.
**Obraz na produkcji:** `cm-agent:ap315d` (= `latest`). Cofniecie o krok: `cm-agent:d008`.
