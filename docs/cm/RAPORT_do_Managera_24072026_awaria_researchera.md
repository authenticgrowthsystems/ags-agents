# RAPORT DO MANAGERA - domkniecie awarii Researchera (24/07/2026)

## Jednym zdaniem

Awaria "joby prospektowe padaja" byla w rzeczywistosci trzema oddzielnymi wadami na sciezce
research prospekta, wszystkie namierzone z dowodow (baza + kod + zrzuty Telegrama), naprawione
i wdrozone; lejek sprzedazowy ma teraz bramke tozsamosci, bo research potrafil opisac inna firme.

## Co bylo zepsute (dowody, nie hipotezy)

1. **Joby 'failed' mimo policzonego wyniku.** Opcje maja dwa ksztalty: swieze z modelu klucz
   `label`, wczytane z cache klucz `option_label` (nazwa kolumny). Meldunek czytal tylko `label`,
   dostawal None i `join` wywracal sie PO `set_status(completed)`; petla nadpisywala status na
   'failed'. Sygnatura w bazie: kazdy job 'failed' mial 4 wiersze w `options` i czas 0-3 s,
   kazdy 'completed' 86-121 s.
2. **Cache oddawal opcje bez faktow.** Konsumenci (karta prospekta Sprzedawcy, podklad CM)
   czytaja CLAIMS z linkami zrodel. Job z cache konczyl sie 'completed' z zerem claims, wiec
   Sprzedawca meldowal "Researcher odpowiedzial, ale bez claims" (dowod: job 4c391774, StandART).
3. **Research trafial w inny podmiot.** Powtorne `/prospect <nazwa>` szlo bez adresu strony,
   bo kod nie bral `prospect_url` z lejka. Dowod: job 0602c6a7 - "Dance Company La Cultura"
   (Sosnowiec, lacultura.pl) opisany jako Cultura Dance Arts w Pawtucket, Rhode Island.
   Karta i tak konczyla sie zacheta "napisz outreach do Dance Company La Cultura".
4. **Kontaminacja semantyczna (zamkniete rano, tu dla skali).** 6 jobow dostalo wynik CUDZEJ
   firmy: 23/07 trzy joby dostaly opcje Scorpion Dance Team, 24/07 trzy dostaly opcje StandART.
   Claims sie nie kopiowaly, wiec do outreachu nic skazonego nie weszlo - skazone sa wylacznie
   wiersze `options` tych jobow.

## Co naprawione (commity df7c60b + 7c31cd5, LIVE po rebuildzie obu kontenerow)

- Cache kopiuje claims (z linkami do evidence joba zrodlowego) i confidence; meldunek czyta
  `label` LUB `option_label`; payload cache niesie koszt i confidence (koniec "koszt ? PLN").
- Zapytanie badawcze bierze adres z lejka i wymaga POTWIERDZENIA TOZSAMOSCI (domena, miasto,
  kraj) albo jawnego "nie mam pewnosci".
- Prospekt bez domeny (9 z 12 w lejku ma tylko gmail) dostaje do zapytania pierwsza linie
  kartoteki (miasto + kontakt) jako dyskryminator.
- `/prospect <nazwa> <domena>` - ostatni token wygladajacy na adres to strona, nie czesc nazwy.
- BRAMKA TOZSAMOSCI: podsumowanie zaczyna sie od `TOZSAMOSC: potwierdzona|niepewna` (kontrakt
  dla kodu). Przy "niepewna" karta nie proponuje outreachu tylko ponowne zlecenie ze strona,
  a gotowiec outreachu jedzie z ostrzezeniem nad trescia.
- Meldunek surowy Researchera milknie dla `sales-agent` (Sprzedawca wysyla wlasna karte);
  RESPONSE do agent_messages leci zawsze.

## Co zostaje na stole

- **Decyzja Tomasza:** cache semantyczny globalnie OFF czy plaster na fraze 'prospect research'.
  Dzisiejsze zabezpieczenie omija kazdy nowy szablon zapytania o podmiot (AP-307).
- **Sprzatanie:** 6 jobow ze skazonymi wierszami `options` do skasowania (SQL gotowy).
- Kampania na 12 szkol tanca rusza dopiero po zielonym tap-tescie trojki.

## Wniosek dla systemu

Cache semantyczny ma sens dla pytan TEMATYCZNYCH, nie dla zapytan o KONKRETNY PODMIOT.
Przy kazdej nowej klasie zapytan trzeba sprawdzic, czy podobienstwo TEKSTU oznacza
podobienstwo TRESCI. Drugi wniosek: nazwa firmy bez adresu nie jest identyfikatorem -
kazde zapytanie o podmiot musi niesc dyskryminator (domena albo miasto i kontakt).
