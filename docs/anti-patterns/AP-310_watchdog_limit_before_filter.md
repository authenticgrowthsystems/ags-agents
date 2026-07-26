# AP-310: Straznik z LIMIT-em PRZED odsiewem zaglodzi sie na wlasnych zaleglosciach

**Ustanowiony 26/07/2026 (BE, diagnoza lejka).** Rodzina AP-308 od strony ODCZYTU: tam masowy
zapis bez dry-runu, tu masowy odczyt z limitem nalozonym w zlym miejscu.

## Wzorzec

Cykliczny straznik ma pobrac "rzeczy zalegle" i zapytac o nie czlowieka. Zeby nie zalac
Telegrama, dostaje `LIMIT N`. Zeby nie pytac dwa razy o to samo, dostaje odsiew wierszy,
ktore juz maja otwarta bramke. **Jesli odsiew stoi PO limicie (w Pythonie, przez `continue`),
to zablokowane wiersze zjadaja cala pule i straznik przestaje dzialac. Na zawsze.**

Kluczowa wlasnosc, ktora czyni to trwalym: wiersze z otwarta bramka sa zwykle NAJSTARSZE,
a `ORDER BY created_at` bierze wlasnie najstarsze. Blokada nie rozejdzie sie sama.

## Dowod produkcyjny (26/07/2026)

`engagement._watch_proposed` mial:

```sql
SELECT id, agent, author_display FROM engagement_log
WHERE status='proposed' AND created_at < NOW() - interval '24 hours'
ORDER BY created_at LIMIT 5      -- <- limit PRZED odsiewem
```

a odsiew (`SELECT 1 FROM agent_decisions ... -> continue`) dopiero w petli Pythona.

Sonda read-only pokazala: **siedem** wierszy Klubu Sportowego StandART czekalo ponad dobe,
**piec najstarszych** mialo otwarte bramki #152-156. Straznik brał piatke, odsiewal ja w calosci
i konczyl przebieg z zerem przypomnien. Dwa pozostale wiersze nie mialy szans dostac bramki
nigdy. Skutek uboczny byl szerszy niz sprawa StandART: ten sam organ obsluguje propozycje
komentarzy i DM-ow, wiec **caly comment-radar zamilkl od 25/07 rano**, a dokumentacja
komponentu obiecywala w tym czasie "Nic nie ginie".

Wada zyla w dwoch miejscach (`_watch_proposed` i `_watch_in_progress`) - klasyczny AP-309.

## Why bad

- Awaria jest CICHA: nie ma wyjatku, nie ma bledu w logach, licznik przypomnien po prostu
  pokazuje zero, co wyglada jak "nie ma zaleglosci".
- Awaria jest TRWALA: sortowanie od najstarszych gwarantuje, ze zablokowane wiersze zostaja
  w puli w kazdym kolejnym przebiegu.
- Awaria ROZLEWA SIE na sasiadow: jedna nietapnieta sprawa wycisza organ dla wszystkich
  innych rodzajow zaleglosci obslugiwanych tym samym zapytaniem.
- Testy syntetyczne tego nie lapia, bo przy dwoch wierszach i limicie piec problem nie istnieje.
  Ujawnia sie dopiero, gdy zaleglosci przekrocza limit.

## Correct

1. **Odsiew nalezy do zapytania, nie do petli.** `NOT EXISTS` na tabeli decyzji PRZED `LIMIT`,
   zeby limit dotyczyl wierszy, ktore naprawde moga cos wygenerowac.
2. **Limit to dlawik wyjscia, nie wejscia.** Jesli ogranicza rozmiar batcha, ma stac na koncu
   filtrowania, nie na poczatku.
3. **Kazdy straznik z LIMIT-em wymaga pytania "co, jesli wszystkie N sa zablokowane".** Jesli
   odpowiedz brzmi "przebieg konczy sie zerem i nic sie nie zmieni w kolejnym", to jest ta wada.
4. **Wieczne pozycje trzeba domykac u zrodla.** Tu prawdziwym paliwem byla niedomknieta petla
   outreachu (kazdy gotowiec zakladal nowy wiersz `proposed`, nikt starych nie zamykal).
   Kolejnosc naprawy ma znaczenie: najpierw zrodlo, potem straznik - odwrotnie to zamiatanie
   objawu, bo sprzatacz kasuje karty, ktore straznik natychmiast odtwarza.
5. **Obietnica w dokumentacji jest testem.** "Nic nie ginie" w opisie komponentu to zdanie,
   ktore da sie sfalsyfikowac zapytaniem. Warto je odpalic, zanim sie je napisze.
