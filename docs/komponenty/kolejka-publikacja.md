# Komponent: KOLEJKA I PUBLIKACJA (post_queue, sloty, dispatch, Scheduler)

**STATUS GOTOWOSCI: KOMPLETNY** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Zamienia ZATWIERDZONY material (content_items 'approved') na opublikowane posty:
przydziela sloty, stage'uje warianty kanalowe do post_queue, publikuje przez
adaptery subagentow (n8n) albo Scheduler i domyka ledger publikacji.

KANON 19/07 (project_publikacja_kanon_19072026): zatwierdzone publikuje sie
ZAWSZE (obecnosc Tomasza nieistotna); niezatwierdzone NIGDY samo -
`_emergency_promote` USUNIETY Z KODU. Cisza >24h na approve = eskalacja guzikami
(`_stale_approval_watch`, typ 'stale_approval': Pokaz karte / Odrzuc /
Przypomnij jutro), nigdy auto-decyzja.

## Wejscia-wyjscia i tabele

- `content_items`: state machine tresci; worker claimuje 'approved' DOPIERO gdy
  `scheduled_for <= NOW()` -> 'handed_off' -> 'published'.
  **`handed_off` do 03/08/2026 nazywalo sie `dispatching`** (D-008/AP-312: nazwa
  obiecywala stan przelotny, a stan trwa DNI - material czeka, az WSZYSTKIE
  wiersze jego serii przestana sie ruszac). Nazwa zyje w `config.STATUS_HANDED_OFF`.
- `post_queue` (INWENTARZ + HARMONOGRAM): wiersz per wariant kanalowy;
  statusy: review / scheduled / queued / held / dispatching / published /
  failed / rejected. `content_item_id` linkuje do materialu.
  **UWAGA: `dispatching` w TEJ tabeli to INNY slownik i ZOSTAJE** - znaczy
  "jeden wiersz oddany subagentowi", a nie "material czeka na cala serie".
  D-008 go nie dotknelo. Zywy wezel n8n `Mark Published` ma OBIE wartosci
  w jednym zapytaniu, wiec podmiana "po calym tekscie" zrywa kolejke po cichu.
- `published_posts`: PRAWDA "co opublikowane" (post_id/URL, embedding,
  engagement_metrics) - zasila dedup i content memory.
- `channels.config.publish_mode` decyduje droga: `webhook` (POST adapter
  subagenta n8n -> publikacja NATYCHMIAST -> callback), `post_queue` (status
  'scheduled', bierze Scheduler n8n co minute WG SLOTU wiersza), `draft`
  (status 'held', recznie), `none` (kanal WYLACZONY, nic nie publikuje).
- TRYB WYLACZONY I TRYB NIEZNANY od 19/08 (dlug D-022): `none` ma wlasna,
  jawna galaz w `channels.dispatch_item` - wiersz idzie na `rejected`, powod
  laduje w `agent_logs`, a na kanal logowy leci paragon "KANAL WYLACZONY".
  **Sprostowanie do opisu dlugu, zrobione odczytem:** `none` NIE przechodzilo
  wczesniej bez sladu. Galaz `else` nie jest galezia trybu `draft`, tylko
  lapaczem wszystkiego, wiec wiersz konczyl na `held` - i `worker._send_manual_paste_kits`
  przysylal Tomaszowi pelna tresc z poleceniem "wklej recznie i odpisz
  `wklejone <id>`" dla kanalu, ktory ma nie publikowac. To bylo gorsze niz cisza.
  Wartosc SPOZA listy `config.TRYBY_PUBLIKACJI` (literowka, tryb z przyszlosci)
  to osobny przypadek: wiersz zostaje NIETKNIETY w `review`, wpis w dzienniku ma
  poziom `error`, a meldunek podaje doslownie wartosc, ktorej kod nie zna. Nie
  publikujemy, bo nie wiemy czym; nie poprawiamy po cichu, bo cicha korekta
  wyglada jak sukces. Stan nieterminalny sprawia, ze `_dispatch_timeout_alert`
  odezwie sie ponownie, jesli nikt nie zareaguje.
  Test: `cm-agent/tests/test_tryb_publikacji_wylaczony.py`.
- STAN 22/07 (decyzja Tomasza "zatwierdzone ma isc samo"): AGS/x ORAZ
  AGS/linkedin = `post_queue` - OBA kanaly publikuje Scheduler per slot wiersza.
  Scheduler ma ROUTER platformy (Route Platform, if 2.2): x -> Publish To X,
  inne -> Publish To LinkedIn (Scheduler) (kod 1:1 z Subagent LinkedIn Publisher
  v2: registerUpload feedshare-image -> PUT -> ugcPosts; obrazy dzialaja) ->
  Mark Published LI (ta sama ksiega per-wiersz) -> LI Confirm. Patch:
  scheduler-linkedin-branch-22072026.cjs. Tryb `draft` (gotowce + 'wklejone <id>')
  zostaje dostepny per kanal; `webhook` NIE respektuje slotow - nie uzywac.
- BLOKADA W KODZIE od 19/08 (dlug D-020): `config.sprawdz_tryb_publikacji`
  rzuca `TrybPublikacjiZabroniony` przy probie ustawienia `webhook`, z pelnym
  opisem czterech skutkow z 20/07. Pytaja ja PRZED zapisem dwa punkty wejscia:
  `conversation._target_update` (fraza "ustaw publish_mode dla ..." oraz
  narzedzie target_update z LLM) i `conversation._target_create` (dziedziczenie
  configu przez copy_from_channel). Domyslny tryb NOWEGO celu i nowej marki to
  od 19/08 `draft`, nie `webhook` - do tego dnia kod rodzil kazdy nowy cel
  w trybie zabronionym od 22/07. Zdjecie blokady: zmienna srodowiskowa workera
  `PUBLISH_WEBHOOK_ODBLOKOWANY=AP-307-callback-naprawiony` + restart; wtedy
  paragon dopisuje ostrzezenie, ze sloty i media sa pomijane. Blokada dotyczy
  USTAWIANIA trybu - wierszy `channels` juz stojacych w bazie nie czyta.
  Test: `cm-agent/tests/test_blokada_webhook.py`.
- Callback publikacji: post_queue 'published' + INSERT published_posts +
  agent_messages RESPONSE + potwierdzenie na kanal logowy (bot #2).

## Sloty (slots.py)

- `next_slot`: najblizszy wolny slot wg okien celu (`publish_windows`,
  np. x 13-22, LI profil 16:00-18:00) i kadencji; `_busy` liczy zajetosc
  z content_items ORAZ post_queue (fix 67f3acf). `_li_ok`: LinkedIn pn-pt post,
  sobota nic, niedziela artykul (reczny).
- `humanize_slot`: ludzkie minuty +/-15 od slotu planu, NIGDY rowny kwadrans -
  stosowany przy KAZDYM wpisie slotu do post_queue. content_items trzyma CZYSTY
  slot planu (roznica ZAMIERZONA). **LOSUJE przy kazdym wywolaniu** - kto potrzebuje
  tej wartosci poza zapisem, musi dostac JA, a nie zawolac funkcje drugi raz.
- `assign_if_needed`: approved bez slotu dostaje go automatycznie. Zwraca
  `(slot, changed, realny)` - `slot` to czysty plan zapisany do `content_items`,
  `realny` to DOKLADNIE ta wartosc, ktora poszla do `post_queue`.

### DWA CZASY, jeden post - REGULA (D-015 domkniete 10/08/2026)

**Publikacja nastepuje o `max(slot planu, czas kolejki)`, plus do minuty na tik Schedulera.**
Zadna z dwoch liczb nie jest prawda sama w sobie i to jest sedno dlugu, ktory zyl tu tydzien.

Pilnuja tego DWIE niezalezne bramki, obie z warunkiem `<= NOW()`:

1. `db.claim_item` - material `approved` z PRZYSZLYM `content_items.scheduled_for` **nie jest
   w ogole brany przez petle**. Trzyma go do SLOTU PLANU.
2. Scheduler n8n - publikuje `post_queue WHERE status='scheduled' AND scheduled_for <= NOW()`.
   Wiersz wchodzi w stan `scheduled` dopiero w dispatchu, czyli PO otwarciu bramki nr 1.

Wniosek: czas kolejki liczy sie **tylko wtedy, gdy jest pozniejszy** niz slot planu. Gdy
`humanize_slot` wylosuje wczesniej (a losuje symetrycznie +/-15 min, wiec w polowie przebiegow),
ta wczesniejsza godzina jest MARTWA.

**STAN OD 19/08/2026 (D-015 ZAMKNIETY): kazda powierzchnia liczy `max(slot, kolejka)` TYM SAMYM
kodem `worker._godzina_publikacji`.** Zadna nie ma juz wlasnego rachunku (AP-309).

| powierzchnia | pokazuje | prawda o publikacji |
|---|---|---|
| meldunek bota "CM przydzielil slot" | `max(slot, kolejka)` (od 10/08/2026) | TAK |
| karta materialu i podglad (`/karty`) | `max(slot, kolejka)` (od 19/08/2026) | TAK |
| paragony: po edycji, po "na koniec kolejki" | `max(slot, kolejka)` (od 19/08/2026) | TAK |
| raport dzienny, `stan_gry`, meldunek dnia | `max(slot, kolejka)` (od 19/08/2026) | TAK |

Wiersz "raport dzienny, `stan_gry`" mial w tej tabeli **TAK** przy samym czasie kolejki. To bylo
dziedzictwo tabeli z 03/08: korekta z 10/08 udowodnila, ze sam czas kolejki myli sie dokladnie
tak samo czesto jak sam slot planu, tylko w druga strone. Poprawiono wtedy meldunek, a raportu
nikt nie przeliczyl, bo tabela nadal mowila o nim "TAK". Wspolna funkcja: `reports._godzina_wiersza`
(odczyt `_queue_upcoming` dowozi juz `ci.scheduled_for`).

**Czego karta NIE robi: nie zgaduje.** Material widziany PRZED wysylka moze nie miec jeszcze
wiersza w kolejce. Wtedy karta pokazuje slot planu i dopisuje wprost, ze dokladnej godziny nie
zna, razem z przedzialem, ktory zna: realna wypadnie miedzy slotem a 15 minutami po nim.
Podstawienie slotu jako pewnika byloby domyslem zapisanym jak fakt (AP-317). Odczyt kolejki:
`matreview._czas_kolejki`, jedno zapytanie na karte, wzorzec `_stan_rozsylki` z D-006.

**DOWOD, NIE TEORIA (10/08, dwa na dwa):** `#344` kolejka 15:49, slot planu 16:00, opublikowane
04/08 o **16:01**; `#358` kolejka 15:50, slot 16:00, opublikowane 05/08 o **16:01**. Poszlaka
potwierdzajaca: wszystkie zaobserwowane publikacje (13:48, 16:10, 16:31, 16:59, 17:48, 19:12,
20:23, 10:01) wypadaja PO najblizszym okraglym slocie, ani jedna przed - przy losowaniu
symetrycznym polowa powinna wypasc wczesniej.

**Historia tego dlugu jest sama w sobie lekcja.** Do 03/08 meldunek podawal czysty slot planu.
Poprawka `d5cd43e` przestawila go na czas kolejki i wygladala na domkniecie sprawy. Obie wersje
myla sie w polowie przypadkow, kazda w druga strone. Regula i dowod: `worker._godzina_publikacji`,
zachowanie: `cm-agent/tests/test_godzina_publikacji.py` (200 losowan + obie stare wersje jako
anty-regresja, zeby nastepna "uproszczajaca" poprawka od razu widziala, ze byly juz probowane).

Zachowanie kart i paragonow: `cm-agent/tests/test_godzina_na_karcie.py` (sciezka alarmu, czyli
kolejka POZNIEJ niz slot, sciezka odwrotna oraz brak kolejki).

## PRZEKLAD: kiedy publikuje, a kiedy jest tylko kopia (11/08/2026)

`generate.translate_text` ma **cztery wywolania i dwa z nich pisza tekst, ktory WYCHODZI**:

| wywolanie | co robi | `do_publikacji` |
|---|---|---|
| `channels.stage_variant` | straznik jezyka: polski wariant na kanale EN tlumaczony PRZED zapisem do kolejki (incydent 20/07) | **True** |
| `conversation` (wklejka wlasnej tresci) | Tomasz wkleja po polsku, kanal publikuje po angielsku | **True** |
| `worker._draft` | kopia PL do przegladu (`media.kind='review_pl'`) | False |
| `conversation` (komentarze) | kontrola po polsku pod wklejka komentarza | False |

Do 11/08 prompt mowil WSZYSTKIM czterem: *"To kopia do przegladu wlasciciela, nie do publikacji"*.
W dwoch przypadkach **byla to nieprawda o przeznaczeniu wyniku** - i licencja na luz w miejscu,
w ktorym luzu byc nie moze. To AP-312 w wersji dla modelu: etykieta klamie, tylko czytelnikiem
jest maszyna. Od 11/08 prompt mowi prawde zaleznie od flagi i wprost zabrania dodawania zdan.

### Kontrola wiernosci: `generate.sprawdz_przeklad`

Prosba o wiernosc w promptcie nie jest kontrola. Trzy miary, ktore **przezywaja zmiane jezyka**
(`pokrycie_slow` z bramki wyjscia filtra tu NIE dziala - przy poprawnym przekladzie byloby bliskie zeru):

1. **liczba ZDAN** - najostrzejsza, prog 20% przy minimum dwoch zdan roznicy;
2. liczba akapitow;
3. zbior liczb (cyfry sa te same w kazdym jezyku) i proporcja dlugosci.

**Kalibracja na prawdziwej parze, nie z teorii.** Pierwsza wersja miala tylko akapity, liczby
i dlugosc - i **nie zlapala przypadku, dla ktorego powstala**. Kopia PL z karty 10/08 niosla
zdanie, ktorego w zrodle nie bylo ("Albo: Agent A decyduje, czy w ogole odpowiadamy"), ale nie
zmienilo to liczby akapitow, a 90 znakow w 700 miesci sie w pasmie dlugosci. Pomiar: wierny
przeklad EN→PL dal **0%** roznicy w liczbie zdan, rozjazd z 10/08 **29%**.

**Co sie dzieje z zastrzezeniami** - nigdzie nie znikaja po cichu, ale nigdzie tez nie blokuja:

- straznik jezyka: wpis `warn` do `agent_logs` (blokada oznaczalaby polski tekst na kanale EN,
  czyli powrot do incydentu 20/07);
- kopia PL do przegladu: **dopisek NA KARCIE** - "TA KOPIA ROZJECHALA SIE ZE ZRODLEM (...)
  Oceniaj po tekscie, ktory WYCHODZI, nie po tej kopii". Karta jest tym, co czlowiek czyta
  zatwierdzajac, wiec rozjazd musi byc widoczny wlasnie tam, a nie w logu;
- wklejka wlasnej tresci: zastrzezenie w paragonie, bo to tekst Tomasza i tylko on wie,
  czy roznica jest w porzadku.

Zachowanie: `cm-agent/tests/test_przeklad_wiernosc.py`.

## BRAMKA WYJSCIA FILTRA - przyczyna zrodlowa AP-315 (10/08/2026)

`compliance._rewrite` obsluguje TRZY filtry (`polish_pl`, przepisanie zakazanego slownictwa,
test szatni) i do 10/08 oddawal odpowiedz modelu **doslownie** (`return out or text`). Gdy model
zamiast poprawic tekst odpowiadal O tekscie ("nie podales mi tekstu do poprawy (...) otrzymasz
zwrotnie wylacznie poprawiony tekst"), ta odpowiedz stawala sie trescia posta.

Od 10/08 stoi tam bramka na **pokryciu slow**: jaka czesc roznych slow wejscia (min. 4 znaki,
zlozone do ASCII) przetrwala w wyjsciu. Ponizej `PROG_POKRYCIA_FILTRA = 0.35` filtr oddaje tekst
**wejsciowy** nietkniety i pisze do `agent_logs` typ `COMPLIANCE_ODPOWIEDZ_NIE_PRZEROBKA`
z poczatkiem odrzuconej odpowiedzi.

Zmierzone: rozmowa modelu **0.023**, korekta polszczyzny 0.977, ostre przepisanie 0.651,
skrocenie o polowe 0.372. Kierunek pomylki wybrany swiadomie - falszywy alarm kosztuje jeden
tekst nieprzefiltrowany plus wpis w logu, falszywe przepuszczenie kosztuje publiczny post.

**To NIE jest lista fraz i o to chodzi.** Bezpiecznik gatunku (nizej) na tej samej karcie dal
`([], [])`, bo awaria miala inne slownictwo. Pokrycie mierzy relacje wyjscia do wejscia,
wiec nowe slownictwo go nie omija.

## BEZPIECZNIK GATUNKU - ostatnia bramka przed swiatem (AP-315, 10/08/2026)

Przed zapisem `handed_off` (`worker.process_item`) tresc KAZDEGO wiersza kolejki przechodzi
przez `compliance.bezpiecznik_gatunku`. Pyta o jedno: czy to jest tekst dla czlowieka, czy
model mowiacy o tekscie. **To jest inne pytanie niz wszystkie pozostale kontrole tresci** -
one pytaja o forme (myslniki, slownictwo, dlugosc, polszczyzna, meta-naglowki).

Dlaczego akurat tam:

- tamtedy przechodzi **kazda** publikacja, takze material zatwierdzony guzikiem w n8n
  (`AGS HITL Handler`), ktory omija cm-agenta;
- sprawdzana jest tresc **wiersza kolejki**, nie `canonical_body` - publikuje sie wariant,
  a `stage_variant` przepisuje go per kanal.

Dwie klasy fraz, kryterium jedno: **czy slowo ma sensowne uzycie POZA nasza maszyneria.**

| klasa | frazy | zachowanie |
|---|---|---|
| TWARDE | `masterprompt`, `stan_gry`, `matreview`, `Bramka:` | blokada bez furtki |
| MIEKKIE | `voice bible`, `canonical`, `I've reviewed`, `I have reviewed`, `I need to flag`, `strong content`, `zatwierdzam`, `proponuje zmiane`, `kolejka`, `meldunek` | blokada, ale zatwierdzenie TEGO SAMEGO tekstu drugi raz przepuszcza z ostrzezeniem |

**Furtke odbiera takze LICZBA** (`compliance.bez_furtki`, `PROG_MIEKKICH_JAK_TWARDE = 3`):
trzy albo wiecej fraz miekkich w jednym tekscie traktujemy jak twarda. Jedna fraza to wybor
slowa, trzy to gatunek. Dzieki temu wyciek z 04/08 (piec miekkich, ZERO twardych) nadal nie ma
wyjscia, a dobry post z jedna fraza je ma.

`kolejka` i `meldunek` sa MIEKKIE swiadomie (decyzja Managera 10/08): TNM pisze po polsku do
uslug lokalnych, gdzie "kolejka klientow" i "stac w kolejce" sa naturalne. Twarda blokada na
zwyklym rzeczowniku odpalilaby raz, w najgorszym momencie, i wygladalaby jak zepsuty system.

`voice bible` zeszlo do miekkich 10/08 **po audycie 152 publikacji**, ktory znalazl ja
w prawdziwym poscie Tomasza z 11/07 ("clear stages, compliance checks, one voice bible") -
jako pojecie content-ops, nie nazwe naszego pliku. Korpus obalil przeslanke wpisu.
Prog trzech sprawdzony na tym samym korpusie PRZED wdrozeniem: `BEZ FURTKI: 0`.

Mechanika furtki: przy zatrzymaniu material wraca do `needs_approval`, a w jego `media` laduje
znacznik `ap315_blok` z **odciskiem TRESCI** (nie listy trafien). Drugie zatwierdzenie przepuszcza
tylko wtedy, gdy odcisk sie zgadza - tekst przepisany jest nowym tekstem i zatrzymuje sie od nowa.
Znacznik siedzi w `media`, bo musi przezyc powrot do `needs_approval` i tapniecie guzika w n8n.
Przy pisaniu tekstu od nowa `_draft` go zdejmuje razem ze stara trescia.

Odcisk laczony jest SORTOWANY - zapytanie o wiersze nie ma `ORDER BY`, wiec bez sortowania dwa
przebiegi na tych samych danych dalyby dwa rozne odciski i furtka nie otworzylaby sie nigdy,
wygladajac przy tym jak dzialajacy bezpiecznik (AP-314).

Zachowanie: `cm-agent/tests/test_bezpiecznik_gatunku.py` - szesc scenariuszy przez prawdziwa
petle `process_item`, karmione tekstem, ktory naprawde wyszedl na LinkedIna 04/08.

## Serie X i straznik dlugich (channels.stage_variant)

- Dluga tresc X przy <1000 followers = SERIA samodzielnych postow rozdzielonych
  markerem `===POST===`, po slotach dnia, czesci publikowane SEKWENCYJNIE.
- STRAZNIK: wariant >600 znakow bez `===POST===` = automatyczne ciecie po
  akapitach na serie. Grafika idzie tylko z czescia 1.
- SUFIT KADENCJI (kanon 25/07, zgloszenie Tomasza "po co dzis tyle tweetow"):
  seria rozbijala sie na sloty NIEZALEZNIE od kadencji - gap wymuszal tylko
  ODSTEP miedzy postami, nie ich LICZBE, wiec czesci upychaly sie na dzis, az
  okno sie wypelnilo (7-8 zamiast 3-5). Teraz `slots._daily_cap` daje twardy
  sufit per kanal (X = gorna granica posts_per_day, np. '3-5' -> 5; LinkedIn = 1),
  a `next_slot` pomija dzien, ktory osiagnal limit - nadmiar serii przechodzi na
  kolejny dzien. Sufit jest niezalezny od gap/siatki/jittera (liczy WSZYSTKIE
  sloty dnia z content_items + post_queue). Test: cm-agent/tests/test_kadencja_sufit.py.
- **SLAD AUDYTOWY ZRODLA SLOTU (DDL 035, 29/07).** `post_queue.slot_source` mowi, ktora trasa
  ostatnio ustawila `scheduled_for`: `staging` (channels.stage_variant), `planner`
  (slots.assign_if_needed), `reslot` (app.reslot), `rozmowa` (przesuniecie terminu przez
  czlowieka), `dispatch` (channels, gdy slot byl pusty), `nieznane` (zapis spoza Pythona:
  wezel n8n albo reczny SQL - **nie udajemy, ze wiemy**).
  **Powod:** 28/07 piec wpisow wyszlo w piec minut o 09:00, poza oknem, na koncie ktore trzy
  dni wczesniej dostalo 403 za wykryta automatyzacje. Ustalenie sprawcy zajelo pol godziny
  i udalo sie WYLACZNIE przez eliminacje wszystkich innych tras - w danych nie bylo ani jednego
  sladu. To AP-311 w wersji zapobiegawczej.
  **Uwaga przy dodawaniu nowego zapisu slotu:** etykieta jest obowiazkowa, pilnuje tego
  `cm-agent/tests/test_slot_source.py` (liczy wszystkie zapisy i sprawdza, czy zaden nie zostal
  bez etykiety). `dispatch` etykietuje TYLKO gdy sam nadaje slot - inaczej nadpisalby etykiete
  prawdziwego autora.
- **BRAMKA POTWIERDZENIA TERMINU (29/07, typ decyzji `slot_confirm`).** Przesuniecie materialu
  przez rozmowe NIE zapisuje sie od razu, gdy zachodzi chocby jeden z dwoch NIEZALEZNYCH
  warunkow: termin poza oknem kanalu **albo** polecenie dotyczace wiecej niz jednego wiersza.
  Wtedy leci pytanie z guzikami, a zapis czeka na tapniecie. Zasada "Ty decydujesz o terminie"
  bez zmian - system pyta PRZED skutkiem, zamiast meldowac PO nim.
  Zapis wykonuje `_wykonaj_przesuniecie`, wolane z OBU drog (bezposredniej i z guzika) - jedno
  miejsce, zeby sie nie rozjechaly (AP-309).
- **DWIE TRASY DOTYKAJA WSZYSTKICH WIERSZY MATERIALU NARAZ** (`conversation` przy przesunieciu
  terminu, `slots.assign_if_needed`). Przy materiale wieloczesciowym daja im ten sam czas,
  czyli SALWE. `assign_if_needed` rozrzuca przez `humanize_slot` (+/-15 min), `conversation`
  zapisuje wartosc czlowieka DOSLOWNIE - i to ta druga zbila 28/07 piec wpisow na jedna minute.
  Kontrola okna w `conversation` istnieje i CELOWO nie blokuje ("Ty decydujesz o terminie");
  wada lezy w zalozeniu, ze jeden material to jeden wiersz kolejki.
- **KADENCJA X: ZOSTAJE 4/DZIEN (decyzja Tomasza 27/07, NADPISUJE Managera).**
  Manager zdecydowal 26/07 zejscie z czterech na jeden, uzasadniajac to martwym zasiegiem
  (0-8 wyswietlen przy 16 obserwujacych) i tym, ze wszystkie realne kontakty w lejku przyszly
  z LinkedIna. **Tomasz decyzje cofnal tego samego dnia: "kadencja na X bez zmian, zostaja 4,
  nic nie zmieniam".** Zmiana NIGDY nie zostala wykonana na produkcji - `posts_per_day`
  stoi na `3-5` jak stalo, kolejka nie byla re-slotowana. To jest zapis, nie zalegly plan.
  Precedens ten sam co przy grafikach (kanon 25/07): w sprawach wlasnej marki decyzja
  wlasciciela bije decyzje Managera.
  Gdyby kiedys wracac do tematu: `ustaw posts_per_day dla AGS x na 1` (paragon ⚙️), potem
  `app.reslot dry 1` i `apply 1`. Zaden konsument nie wymaga poprawki - sprawdzone 27/07:
  `_daily_cap` bierze gorna granice zakresu, `slots._grid` i `proactive._expected` dolna,
  wiec wartosc jednoliczbowa jest spojna we wszystkich czterech miejscach czytajacych
  `posts_per_day`.
- RE-SLOTTER `app.reslot` (25/07, sprzatanie kolejki sprzed sufitu): kolejka X urosla
  do 64 wierszy z dniami po 7-9 postow (serie rozlewaly sie ZANIM powstal sufit).
  **v2 (decyzja Tomasza "cale serie razem"):** przeplanowuje CALA przyszla kolejke od dzis,
  SERIE w ciaglych blokach, czesci w kolejnosci NARRACYJNEJ (`id` = kolejnosc wstawiania
  przez stage_variant; NIE scheduled_for - ten rozprasza sie przy kolejnych re-slotach).
  Hook idzie przed rozwinieciem, seria nie jest porozrzucana. Sloty: rownomierna siatka
  dnia (10/12:30/15/17:30/20), max cap/dzien, LUDZKA MINUTA DETERMINISTYCZNA per id
  (`_human_minute` - nie losowa, inaczej dry != apply i brak idempotencji). Zmienia
  WYLACZNIE scheduled_for (media/grafiki Tomasza nietkniete). `docker exec cm-agent python
  -m app.reslot dry` = podglad, `... apply` = wykonanie. Idempotentny (drugi przebieg = 0
  zmian). Test: cm-agent/tests/test_reslot.py.
- STRAZNIK JEZYKA (20/07): przed zapisem do kolejki wariant sprawdzany z
  `channels.config.language_publish`; gdy kanal 'en' a tekst wyglada po polsku
  (`compliance.looks_polish`) -> `generate.translate_text` na EN. Karta HITL
  pokazuje dokladnie to, co wyjdzie na kanal.
- STRAZNIK META-NAGLOWKA (24/07, zgloszenie Tomasza ze zrzutu z X): przed zapisem
  do kolejki `compliance.strip_meta_header` zdejmuje z czubka tekstu meta-linie
  modelu - naglowek `# X Adaptation`, etykiete `LinkedIn:`, zapowiedz `Oto wersja:`
  i oplotki ```. Objaw: post #195 wyszedl na X z linia "# X Adaptation"; ani X, ani
  LinkedIn nie renderuja markdown, wiec to nie formatowanie, tylko smiec widoczny
  dla klienta. Ciecie jest zachowawcze (max 3 linie, tylko wzorce meta, hasztag NIE
  jest naglowkiem - po '#' musi stac spacja) i dziala TAKZE na kazdej czesci serii.
  Testy: `cm-agent/tests/test_meta_naglowek.py`. Sprzatanie wierszy sprzed poprawki:
  `docs/ops/meta_naglowki_kolejki_24072026.sql`.
- `[ARTYKUL]` = gotowiec do wklejki recznej (API X/LinkedIn nie publikuje
  artykulow z naszego tieru).

## Konfiguracja

- `channels.config`: publish_windows, publish_mode, posts_per_day,
  follower_count, thread_enabled, language_publish, emergency_publish
  (MARTWY klucz - kod go nie czyta, zostal po incydencie).
- Adaptery n8n: Subagent X Publisher `G3nEIt5lIkiKemiK`, Subagent LinkedIn
  Publisher `Uv9TvUMI8MRSqCLz` (generyczny per cel: secret_prefix), Scheduler
  `x1jJEbcWAe3FnpCa` (co minute, OAuth1). Klucze WYLACZNIE z app_secrets.
- MEDIA X (v3, 22/07, patch scheduler-media-v3-22072026.cjs; wczesniejsze proby:
  query-params = 400 "not one of []", multipart na /2/media/upload = 400 "Missing
  media field" bo to PROSTY upload): chunked idzie POD-SCIEZKAMI -
  INIT POST /2/media/upload/initialize (JSON: media_type,total_bytes,media_category),
  APPEND POST /2/media/upload/{id}/append (multipart: media+segment_index),
  FINALIZE POST /2/media/upload/{id}/finalize (bez body), STATUS = GET z query.
  Zweryfikowane per-endpoint w docs.x.com 22/07. Oba workflow (wspolny kod).
  Do kolejki ida tylko wpisy media z file_id (`channels._pub_media`).
  DOWOD LIVE: oczekiwany przy publikacji 185 (22/07 17:55).
- KSIEGA (naprawa 21/07): Mark Published Schedulera per-wiersz robi UPDATE pq
  + INSERT published_posts + agent_messages RESPONSE + domyka content_items,
  gdy nie ma juz wierszy w locie. Bez tego CM/raporty klamaly "nic nie wyszlo"
  mimo opublikowanych postow (incydent 21/07).
- GOTOWIEC RECZNY (A4, 21/07): wiersz 'held' = worker wysyla do glownej
  rozmowy pelny zestaw (naglowek + czysta wklejka + grafika); domkniecie
  deterministyczna komenda `wklejone <id>` (pq->published + ksiega, source
  manual_paste). ZWIS publikacji liczony OD SLOTU wiersza, nie od dispatchu.

## Publikacja SPOZA systemu (10/08/2026)

**Dwie rozne komendy, bo to dwie rozne sytuacje** - mylenie ich to najprostsza droga
do wpisu w ksiedze, ktory nie odpowiada niczemu:

| komenda | kiedy | co jest w bazie przed |
|---|---|---|
| `wklejone <id>` | gotowiec Z KOLEJKI, wklejony recznie | wiersz `post_queue` w stanie `held`, tresc, material |
| `wyszlo <kanal> <link> [temat]` | publikacja, ktora **calkiem ominela system** | NIC - tylko link do czegos, co juz wisi |

Zrodla w `published_posts.metadata->>'source'`: `manual_paste` i `manual_external`.
Wpis z `wyszlo` ma **pusta tresc swiadomie** - nie zgadujemy jej z linku, a pusty `content`
nie dostaje embeddingu, wiec nie zasmieca bramki duplikacji.

Dwie bramki, obie odmawiaja bez zapisu: **kanal musi istniec** w `channels` (literowka
`linkedln` wpisalaby wiersz, ktorego zaden raport nie pokaze, bo raporty chodza po kanalach
z tej tabeli) oraz **ten sam link nie wchodzi dwa razy** (dublowalby statystyki).

### Dlaczego to powstalo

Zgloszenie Tomasza 10/08: meldunek dnia powiedzial **"Poszlo: nic w ostatnich 24h"** w dniu,
w ktorym wyszly DWA artykuly opublikowane recznie. Zdanie bylo prawdziwe o SYSTEMIE i falszywe
o SWIECIE - AP-312. Od 10/08 meldunek nazywa podmiot: **"System opublikowal: N"** albo
**"System nie publikowal nic w ostatnich 24h"**, publikacje odnotowane recznie ida w osobnej
linii, a przy calkiem pustej ksiedze meldunek **przyznaje sie do slepoty** i podaje gotowa
komende. Zachowanie: `cm-agent/tests/test_publikacja_reczna.py`.

## Punkty zaczepienia w kodzie

- `cm-agent/app/worker.py`: `process_item` (state machine), `_draft` (generacja
  canonical + warianty + dedup), `_stale_approval_watch`, `reconcile_publications`,
  `_publish_report`, `loop`.
- `cm-agent/app/channels.py`: `stage_variant` (staging + serie + straznik),
  `dispatch_item`, `_delegate`, `active_targets`.
- `cm-agent/app/slots.py`: `next_slot`, `humanize_slot`, `assign_if_needed`,
  `_busy`, `_li_ok`.
- Odrzucenie karty sprzata kolejke: `matreview.handle` akcja 'no' ->
  UPDATE post_queue -> 'rejected' (wszystkie wiersze materialu).

## Kanony ktore go dotycza

- Kanon publikacji 19/07 (calosc sekcji "Co robi").
- Ludzkie minuty (kanon 19/07): +/-15 min, nigdy kwadrans.
- Kanon mediow multi-platforma: jedna grafika = reuse na wszystkie kanaly
  materialu (patrz grafika.md).

## Znane pulapki

- INCYDENT 20/07 (AP-307, raport: docs/ops/INCYDENT_PUBLIKACJI_20072026.md):
  przy publish_mode='webhook' delegat publikowal WSZYSTKIE wiersze materialu
  naraz przy dispatchu (burst 4-5 postow/h), gubil media wierszy, a callback
  X Publishera oznaczal 'published' KAZDY wiersz materialu (takze te ze slotami
  w przyszlosci) - baza klamala. Adaptery po zmianie trybow NIEUZYWANE, ale
  callback per-row NIENAPRAWIONY (uzbrojona mina - backlog przed jakimkolwiek
  powrotem do trybu webhook).
- ETYKIETY KOLEJKI PO LUDZKU (23/07, konfuzja "[review] = niezatwierdzone"):
  raporty i kontekst pokazuja wiersz 'review' materialu ZATWIERDZONEGO jako
  "zatwierdzone, czeka na start" (reports._pq_label; JOIN na content_items.status).
  "DO ZATWIERDZENIA" widac tylko, gdy material realnie czeka na approve.
  Zatwierdzanie dzieje sie NA MATERIALE, nie na wierszach kolejki.
- 'held' to zamrazarka: po incydencie 13-19/07 wszystko zamrozone, sprzatniete
  wg dowodu 19-20/07 (sieroty pq bez materialu -> rejected; SQL wykonany,
  kontrola = 0). Nowe sieroty nie powstaja (fix matnav 'no').
- Publishery n8n NIE wolaja jeszcze `/wake` po callbacku - meldunek publikacji
  czeka do 30 s na poll petli (TODO przy najblizszej sesji n8n).
- Legacy AGS X Agent (Notion queue, cron 14/18/22) OFF od 25/06 - podwojnych
  publisherow NIE MA (dowod w n8n 19/07).
- linkedin_access_token z Token Generatora wygasa ~01/09/2026;
  linkedin_client_secret w DB bledny (OAuth callback nieuzywany).
