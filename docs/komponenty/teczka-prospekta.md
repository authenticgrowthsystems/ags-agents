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
- **Brak nastepnego kroku jest WYPISANY** ("BRAK ustalonego nastepnego kroku"), nie zostawiony
  jako pusta linia. Pusty wiersz w raporcie lejka byl jedna z przyczyn tego, ze przez tygodnie
  nikt nie zauwazyl prospektow bez terminu (diagnoza 26/07).
- **`_ENG_CHANNEL` w sales.py mapuje `email` na `'Other'`, nie `'Email'`** (stan zastany, poza
  zakresem tej zmiany). Gotowce mailowe Sprzedawcy leza wiec w kanale `Other`, a teksty z teczki
  w `Email`. Rozjazd jest kosmetyczny (teczka laczy po kluczu, nie po kanale), ale przy liczeniu
  wysylki per kanal trzeba o nim pamietac. Dlug: D-009.
