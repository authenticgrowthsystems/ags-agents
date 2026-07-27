# Komponent: DECYZJE USTRUKTURYZOWANE + PETLA NAUKI (eskalacja guzikami)

**STATUS GOTOWOSCI: CZESCIOWY (mechanizm LIVE; nauka mloda - progi semi-auto nieosiagniete)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Kazda decyzja operacyjna CM/subagenta, ktorej agent nie moze podjac sam, idzie
do Tomasza jako WIADOMOSC Z GUZIKAMI (rekomendacja ⭐ pierwsza). Kazda odpowiedz
uczy system; po wystarczajacej zgodnosci system SAM proponuje przejscie danego
TYPU decyzji na semi-auto - ale zmiana trybu to tez decyzja z guzikami.

GRANICA (kanon 19/07): semi-auto obejmuje TYLKO decyzje operacyjne (sloty,
podmiany, priorytety). Zatwierdzanie TRESCI do publikacji NIGDY nie przechodzi
przez ten mechanizm.

## Wejscia-wyjscia i tabele

- `agent_decisions` (DDL 024): ledger decyzji - subagent_id ('CM'/'AGS:x'),
  decision_type (STALY typ, np. 'topic_swap', 'stale_approval',
  'mode_transition' - po nim liczy sie nauka), question, options jsonb
  [{key,label}], recommendation, status (pending/answered/auto/expired),
  answer, tg_message_id.
- `decision_modes` (DDL 024): tryb per (subagent_id, decision_type):
  supervised / semi_autonomous.
- `agent_learning_log`: KAZDA odpowiedz -> wpis (accepted gdy zgodna
  z rekomendacja, inaczej replaced).

## Przeplyw

```
agent -> decisions.ask(subagent_id, brand, decision_type, question, options,
         recommendation) -> Telegram wiadomosc z guzikami dec:<id>:<key>
Tomasz tap -> n8n HITL galaz dec: -> POST /decnav -> decisions.handle:
  zapis odpowiedzi + wpis learning_log + zdjecie guzikow z oryginalu +
  paragon NOWA wiadomoscia + ewentualne akcje (decisions._apply_action)
NAUKA: >=10 odpowiedzi typu i >=80% zgodnosci w ostatnich 20 ->
  _maybe_propose_transition -> decyzja 'mode_transition' (guziki, tap Tomasza)
SEMI-AUTO: ask() sam wybiera rekomendacje, loguje do learning_log i wysyla
  paragon INFORMACYJNY - pelna widocznosc, zero cichych decyzji
```

Watcher ciszy: `worker._stale_approval_watch` (petla) - material >24h bez
approve = decyzja 'stale_approval' (⭐ Pokaz karte / Odrzuc material /
Przypomnij jutro); throttle w DB = jedna otwarta/swieza decyzja per item.

## Konfiguracja

- Progi nauki w kodzie (decisions.py): 10 odpowiedzi / 80% zgodnosci
  w ostatnich 20.
- `brand_config.admin_chat_ids` - dokad ida decyzje.
- Tryb per typ: wiersz w `decision_modes` (zmiana WYLACZNIE tapnieciem
  mode_transition).

## Punkty zaczepienia w kodzie

- `cm-agent/app/decisions.py`: `ask`, `handle`, `_apply_action`,
  `_apply_mode_transition`, `_maybe_propose_transition`, `mode_for`, `_learn`,
  `pending_text` (dla /decyzje).
- `cm-agent/app/worker.py`: `POST /decnav`, `_stale_approval_watch`.
- `cm-agent/app/conversation.py`: narzedzie `escalate_decision` (opis uczy CM
  kiedy eskalowac i ze zatwierdzanie tresci to NIE to); komenda /decyzje
  pokazuje tez czekajace decyzje ustrukturyzowane.
- n8n HITL: galaz dec: (Is Dec Callback? -> Dec Secret -> Dec Fire).

## Kanony ktore go dotycza

- Kanon publikacji 19/07 pkt 3: eskalacja subagent->CM->Tomasz GUZIKAMI,
  kazda odpowiedz -> agent_learning_log, przejscia supervised->semi_autonomous
  per TYP decyzji, nigdy dla zatwierdzania tresci.
- Paragon kazdej decyzji nowa wiadomoscia (kanon 05/07).
- Manager decisions approval-learning: autonomia jest ZARABIANA odpowiedziami.

## Zmiany 22/07 (uwagi Tomasza 00:05)

- Zgloszenia PO LUDZKU i WYTLUSZCZONE (HTML): naglowek = przyjazna nazwa typu
  (_TYPE_LABEL w decisions.py, np. "Outreach czeka na wyslanie (AGS:sprzedaz)"),
  zero [decision_type]/#id w tekscie widocznym (id zyje tylko w callbackach).
  Potwierdzenie: "<b>wybor</b> - typ: poczatek pytania".
- NOWY typ 'stale_outreach': gotowce SPRZEDAWCY (agent *:sprzedaz) wypadly z maszynerii
  komentarzy - wlasne guziki [Wyslalem/Czekam/Pokaz tresc/Rezygnuje]; 'Pokaz tresc' =
  czysta wklejka BEZ intake'u ("Dam zrzut profilu" przy prospekcie z researchem strony
  to byl incydent decyzji #14). Zrodlo prawdy o prospekcie = sales_pipeline.
- NOWY typ 'sales_followup' (26/07, Level 2 zatwierdzony przez Managera): termin kontaktu
  w lejku minal -> pytanie guzikami [Skontaktowalem sie / Przypomnij za 3 dni / Odpuszczam
  na teraz]. Powstal, bo `next_followup_at` mialo WYLACZNIE konsumentow pull: czternascie
  tickow workera, zaden nie czytal pola, w n8n zero trafien. Karta niesie dowod (etap, ile
  po terminie, kanaly kontaktu albo jawne "BRAK", ostatnia notatka), zeby guzik nie byl
  zgadywanka. Trzy guziki, kazdy ROZSTRZYGAJACY - swiadomie bez "pokaz", bo kazda odpowiedz
  zamyka decyzje i "pokaz" wyciszyloby przypomnienie na dobe. Obsluga: `sales.apply_followup`.
  ETAPU nie rusza zaden guzik (qualified znaczy zakwalifikowany, nie skontaktowany).

## Znane pulapki

- decision_type musi byc STALY (nie freetext) - po nim grupuje sie nauka;
  nowy typ = swiadoma decyzja projektowa.
- Throttle stale_approval: jedna otwarta decyzja per item - flood niemozliwy,
  ale tez nie czekaj na drugie przypomnienie tego samego dnia.
- **KAZDA odpowiedz zamyka decyzje** (`decisions.answer` ustawia `answered` bezwarunkowo).
  Guzik, ktory brzmi jak podglad ("Pokaz tresc"), tez ja zamyka - a poniewaz throttle liczy
  `answered_at > NOW() - 24h`, sprawa milknie na dobe. Dlatego: **albo wszystkie guziki typu
  sa ROZSTRZYGAJACE** (tak zaprojektowany jest `sales_followup`, swiadomie bez "pokaz"),
  **albo galaz podgladu musi zadac pytanie ponownie** (tak robi od 27/07 `apply_stale_outreach`
  po pokazaniu tresci, wzorem toru komentarzy). Zgloszone przez Tomasza przy bramce #162:
  "klikam Pokaz tresc, nie Wyslalem" - i zostalby z tekstem bez guzika.
- **Throttle jest PER PRZEDMIOT, nie per przebieg** (doprecyzowanie 26/07): zdanie "flood
  niemozliwy" bylo za mocne. Dodatkowo kazdy straznik, ktory laczy throttle z `LIMIT`, musi
  miec odsiew W ZAPYTANIU przed limitem - inaczej zablokowane pozycje zjadaja cala pule
  i organ zamiera po cichu (AP-310, dowod produkcyjny 25-26/07).
- **Status 'expired' nie jest ustawiany przez zaden cykliczny sprzatacz** (stan na 26/07).
  Pisza go dzis: recznny SQL Tomasza oraz - od 26/07 - zamykanie nadmiarowych gotowcow
  w `sales._close_outreach_rows` i skrypt `app.outreach_cleanup`. Bramka bez wlasciciela
  zostaje 'pending' na zawsze i wycisza czujke swojego przedmiotu.
- Status 'auto' = decyzja podjeta w semi-auto; przy audycie odrozniac od
  'answered' (czlowiek).
- Pokrewna, STARSZA warstwa bramek Researchera (agent_approval_gates:
  model_selection mtier:, critical_escalation crit:) to OSOBNY mechanizm -
  patrz researcher.md.
