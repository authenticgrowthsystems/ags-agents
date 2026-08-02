# Komponent: TECZKA PROSPEKTA (para zapisz_tekst + teczka)

**STATUS GOTOWOSCI: ZBUDOWANY 31/07/2026, czeka na wdrozenie (push -> DDL 036 -> rebuild cm-agent -> PUT n8n). Test 36/36 PASS, produkcja jeszcze nie dotknieta** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Teksty sprzedazowe pisane w czacie (Cowork, konektor MCP) laduja w bazie zamiast ginac
w rozmowie. Para narzedzi jednego kontraktu:

- `zapisz_tekst(contact_id, kanal, tresc, status)` - zapis powiazany z kontaktem, z data.
- `teczka(contact_id)` - w JEDNYM wywolaniu: dane kontaktu, cala chronologia, ostatni
  ustalony nastepny krok z data, status.

**Powod powstania:** Manager pisze maile do prospektow w czacie. Dotad zostawaly wylacznie
w oknie rozmowy - zero sladu w bazie, wiec nie dalo sie iterowac, policzyc ani wczytac
w nowej rozmowie. Osobna konwersacja do prospektow nie mialaby z czego powstac.

**Dlaczego JEDEN modul, nie dwa:** zapis i odczyt dziela slownik kanalow, rozstrzyganie
identyfikatora i ksztalt wpisu. Rozdzielone rozjechalyby sie przy pierwszej zmianie kanalu.

## USTALENIE, KTORE UKSZTALTOWALO PROJEKT

Odczyt produkcji 31/07 (sonda jednorazowa, zero zapisow):

| rejestr | wierszy | z mailem | z contact_id |
|---|---|---|---|
| `contacts` | 194 | **0** | - |
| `sales_pipeline` | 133 | - | **0** |

Pokrycie po nazwie: **1 na 133**.

`contacts` to uchwyty z X i LinkedIna zbierane przez radar komentarzy (`mieszkojaroniewski`,
`jasonfeifer`). `sales_pipeline` to prospekty kampanii (szkoly tanca). **To sa dwie rozlaczne
populacje.** Prospekt kampanii NIE MA wiersza w contacts i nie bedzie go mial, bo kanon z 22/07
mowi: zrodlem prawdy o prospekcie jest `sales_pipeline`.

Wniosek dla kontraktu: `contact_id` wskazujacy wylacznie na `contacts` bylby **martwy dokladnie
dla tego, po co narzedzie powstalo**. Dlatego identyfikator rozstrzygamy wobec OBU rejestrow
i zawsze mowimy, w ktorym trafil. Nie dosypujemy contacts pod prospekty - to zrobiloby drugie
zrodlo prawdy o tym samym podmiocie.

## Most do katalogow na dysku (DDL 037, 01/08/2026)

`sales_pipeline.katalog` trzyma sciezke **wzgledna** do folderu klienta, np. `Klienci\Chwalinski`.
Korzen (`C:\Claude-CoWork\TyNieMusisz`) jest cecha maszyny i w wierszu go NIE MA.

**System NIGDY nie tworzy, nie przenosi i nie kasuje katalogow.** Folder powstaje wtedy, kiedy
powstaje pierwszy plik, i robi to czlowiek albo Manager. Baza przechowuje wylacznie NAPIS.

**Nazwa ustalana RAZ przy pierwszym kontakcie i nigdy niezmieniana** (polecenie Tomasza 01/08).
Nie jest to kosmetyka: skoro nic nie przenosi folderow, podmiana napisu zostawilaby wiersz
wskazujacy na nieistniejaca lokalizacje - dokladnie ten rozjazd, ktoremu most zapobiega.
Proba zmiany wraca bledem, ktory tlumaczy kolejnosc: najpierw przenies folder, potem recznym SQL
popraw wiersz. Ta sama regula stoi w SQL (`AND katalog IS NULL`), nie tylko w kodzie.

**DLACZEGO sciezki nie da sie wyliczyc** (odczyt 01/08): `Stepownia_Dudzik` to w bazie
"Wrocławska Stepownia", `La_Cultura_Wrobel` to "Dance Company La Cultura". Katalogi niosa
NAZWISKO WLASCICIELA, ktorego w bazie nie ma w ogole. Zadna transliteracja tego nie odtworzy.

Walidacja przy zapisie: bez polskich znakow (napis ma byc identyczny z dyskiem), bez litery
dysku, bez `..`, tylko litery bez ogonkow, cyfry, `_`, `-`, `.`, spacja i ukosnik. Ukosniki
zwykle sa zamieniane na windowsowe.

Powiazanie czterech istniejacych katalogow: `docs/ops/SQL_katalogi_klientow_01082026.sql`.

## Wejscia-wyjscia i tabele

- `engagement_log` - ksiega wpisow. DDL 036 dodaje:
  - status `'draft'` (szkic) obok istniejacych,
  - kanaly `'SMS'` i `'WhatsApp'`,
  - `pipeline_id UUID REFERENCES sales_pipeline(id)` - **drugi klucz obcy**, obok `contact_id`.
- `sales_pipeline.next_step TEXT` (DDL 036) - tresc nastepnego kroku przy istniejacej dacie
  `next_followup_at`.
- `contacts.next_action` / `next_action_due` - dla kontaktow spolecznosciowych. Kolumny istnialy
  od DDL 001 i przez caly ten czas **nie zapisal ich nikt** (0 wierszy na 31/07); ten komponent
  jest ich pierwszym pisarzem.

## Przeplyw

```
czat (MCP) -> zapisz_tekst -> POST /lacznik/zapisz-tekst (guard lacznik_e2_secret)
  -> teczka.zapisz -> znajdz(ident):
       UUID     -> sales_pipeline.id, potem contacts.id
       fragment -> ILIKE po obu rejestrach
       1 trafienie          -> zapis
       0 trafien            -> Blad + lista podobnych (szukanie po KAZDYM slowie osobno)
       wiele trafien        -> Blad + lista kandydatow; dokladna nazwa rozstrzyga (franczyzy)
  -> INSERT engagement_log (pipeline_id ALBO contact_id, status draft|sent)
  -> opcjonalnie UPDATE next_step + next_followup_at

czat (MCP) -> teczka -> GET /lacznik/teczka?kontakt=... -> teczka.teczka_text:
  naglowek (etap/oferta albo mail/telefon) + NASTEPNY KROK + chronologia rosnaco
```

## Konfiguracja

- Kanaly: slownik `_KANALY` w `teczka.py` - `email | sms | whatsapp | dm | telefon`.
  `dm` celuje w LinkedIn, bo to kanal DM kampanii. DM-y na X = dolozenie klucza, nie zgadywanie
  po tresci.
- Statusy: `_STATUSY` - `draft | sent`.
- Sekret: ten sam `lacznik_e2_secret` w `app_secrets`, co reszta Lacznika.

## Punkty zaczepienia w kodzie

- `cm-agent/app/teczka.py`: `znajdz`, `zapisz`, `_ustaw_krok`, `_wpisy`, `teczka_text`, `_podobne`.
- `cm-agent/app/worker.py`: `POST /lacznik/zapisz-tekst`, `GET /lacznik/teczka`.
- `cm-agent/app/sales.py`: INSERT gotowca ustawia od 31/07 takze `pipeline_id`.
- `cm-agent/db/036_teczka_prospekta.sql`.
- `n8n-workflows/lacznik-chat-tools-create-22072026.cjs`: wezly `zapisz_tekst` i `teczka`.
- Test: `cm-agent/tests/test_teczka.py`.

## Kanony ktore go dotycza

- Zrodlem prawdy o prospekcie jest `sales_pipeline` (22/07, tor gotowcow).
- Kanon zimnej wysylki 27/07: **WhatsApp, nie SMS** - stad kanal `WhatsApp` w DDL, zeby
  wiadomosc faktycznym kanalem kampanii nie musiala byc zapisana klamliwie jako SMS.
- AP-312: nazwa stanu ma znaczyc to, co obiecuje. `draft` znaczy szkic i nic wiecej -
  nie jest gotowcem czekajacym na tapniecie.

## Znane pulapki

- **`draft` to SWIADOMIE nowa wartosc, nie recykling `proposed`.** `proposed` jest konsumowane
  przez `engagement._watch_proposed` (gotowce Sprzedawcy), wiec kazdy mail pisany w Cowork
  zrodzilby po dobie bramke "Outreach czeka na wyslanie". Test pilnuje, ze zaden nowy wpis
  nie ma statusu `proposed`.
- **Nieznany identyfikator NIGDY nie zaklada nowego wiersza.** Ciche tworzenie kontaktu
  produkuje duchy, ktorych pozniej nikt nie odrozni od prawdziwych. Blad wraca z lista
  podobnych i jawnym zdaniem "NIC nie zapisalem".
- **Wieloznacznosc tez nic nie zapisuje.** Fragment "Egurrola" trafia w trzy franczyzy;
  rozstrzyga dopiero pelna nazwa albo UUID. To ta sama rodzina wad, co dedup po samej domenie
  z importu prospektow.
- **Historia sprzed DDL 036 wisi na nazwie, nie na kluczu.** `_wpisy` dla prospekta bierze
  `pipeline_id` ORAZ dokladna nazwe z `author_display`, inaczej teczka pokazalaby tylko
  te czesc historii, ktora powstala po migracji. Backfill w DDL 036 dopina, co da sie dopiac
  dokladnym dopasowaniem; reszta zostaje z NULL, bo lepiej puste niz podpiete blednie.
- **`content` to WEJSCIE albo etykieta, `response` to NASZ tekst.** Konwencja jest wspolna dla
  wszystkich torow zapisu: przy komentarzu `content` niesie cudzy komentarz, a `response` nasza
  odpowiedz; przy gotowcu Sprzedawcy `content` to sam napis "outreach email: <nazwa>", a caly mail
  siedzi w `response`. Pierwsza wersja `_wpisy` czytala wylacznie `content` - **tap-test na zywych
  danych StandART 31/07 pokazal siedem wpisow, w kazdym sama etykieta i ani slowa z tresci maili.**
  Odtad `_tresc_wpisu` pokazuje oba: wejscie cytatem, nasz tekst normalnie. Test tego pilnuje.
- **Walidacja katalogu stoi PRZED zapisem tekstu, nie po.** Pierwsza wersja sprawdzala sciezke
  dopiero po wstawieniu wiersza do `engagement_log`, wiec bledna sciezka zostawiala zapisany
  tekst I blad naraz - czlowiek widzial blad, ponawial i robil duplikat. Zlapane wlasnym testem
  01/08. Kolejnosc sprawdzen w `_sprawdz_katalog` tez ma znaczenie: litera dysku sprawdzana
  jest PRZED filtrem znakow, inaczej `C:\...` odbijalo sie komunikatem o "niedozwolonych
  znakach" zamiast o sciezce bezwzglednej (AP-312 w komunikacie bledu).
- **Brak nastepnego kroku jest WYPISANY** ("BRAK ustalonego nastepnego kroku"), nie zostawiony
  jako pusta linia. Pusty wiersz w raporcie lejka byl jedna z przyczyn tego, ze przez tygodnie
  nikt nie zauwazyl prospektow bez terminu (diagnoza 26/07).
- **`_ENG_CHANNEL` w sales.py NIE JEST slownikiem etykiet - to KLUCZ DOPASOWANIA.** Wartosc stad
  trafia do `_open_outreach_rows`, ktora po niej znajduje poprzednie ZYWE gotowce prospekta,
  zeby je uniewaznic. **Zmiana wartosci bez migracji istniejacych wierszy odcina stare gotowce
  od wyszukiwania i odtwarza wade StandART z 24/07** (siedem otwartych gotowcow, piec bramek,
  cztery godziny).
  **D-009 zamkniete 02/08/2026:** `email` mapuje sie na `'Email'`, dziewiec istniejacych wierszy
  zmigrowane w tym samym oknie wdrozeniowym, przy ZATRZYMANYM cm-agencie (zatrzymanie usuwa okno
  zamiast wybierac mniejsze zlo - baza stoi w innym kontenerze niz pisarz).
  Wczesniejsza wersja tego wpisu nazywala rozjazd "kosmetycznym". **Byla w bledzie** i mogla
  zachecic do cofniecia slownika jednym commitem, bez migracji. Test w `test_outreach_petla.py`
  pilnuje teraz niezmiennika: kanal zapisu i kanal wyszukiwania to ta sama wartosc.
