# RAPORT do Managera: ESKALACJA+NAUKA - krok [2] planu dnia (19/07/2026)

Od: BE. Brief: docs/briefs/BRIEF_ESKALACJA_19072026.md. Kanon 19/07 pkt 3 zrealizowany
w warstwie mechanizmu.

## Co zbudowane

1. **DDL 024**: agent_decisions (ledger decyzji: typ, pytanie, opcje jsonb, rekomendacja,
   status pending/answered/auto, odpowiedz) + decision_modes (tryb per subagent+typ:
   supervised/semi_autonomous). SCHEMA w tym samym commicie.
2. **app/decisions.py**: ask() = wiadomosc z guzikami (⭐ rekomendacja pierwsza; callback
   dec:<id>:<key>); handle() = zapis odpowiedzi + wpis agent_learning_log (accepted/replaced
   wzgledem rekomendacji) + zdjecie guzikow z oryginalu + paragon NOWA wiadomoscia (kanon 05/07).
   NAUKA: >=10 odpowiedzi typu i >=80% zgodnosci w ostatnich 20 -> system SAM proponuje
   przejscie na semi-auto, ale propozycja to tez decyzja z guzikami (mode_transition) - tryb
   zmienia sie WYLACZNIE tapnieciem Tomasza. W semi-auto: ask() wybiera rekomendacje, loguje
   do agent_learning_log i wysyla paragon informacyjny - pelna widocznosc, zero cichych decyzji.
3. **worker.py**: POST /decnav (wzorzec /cmt). **conversation.py**: tool escalate_decision
   (opis uczy CM kiedy eskalowac i ze zatwierdzanie TRESCI to nie to) + standard ESKALACJA
   DECYZJI w prompcie + /decyzje pokazuje tez czekajace decyzje ustrukturyzowane.
4. **n8n HITL LIVE**: galaz dec: wpieta w lancuch callbackow (Is Cmt Callback? FALSE ->
   Is Dec Callback? -> Dec Secret -> Dec Fire). Backup bk_hitl_deccb_*.json; deactivate+activate;
   po PUT zweryfikowane: active=true, 252 wezly, binaryMode=separate nietkniety.
5. **Kanon w prompcie CM**: usunieta linia "Brak reakcji Tomasza 24h = publikacja awaryjna"
   (mechanizm z kodu wyleci w kroku [3]).

## Granica bezpieczenstwa (kanon 19/07)

Semi-auto obejmuje TYLKO decyzje operacyjne (sloty, podmiany, priorytety). Zatwierdzanie
tresci do publikacji NIE przechodzi przez ten mechanizm i nigdy nie bedzie automatyczne.

## Dowody

py_compile OK (decisions, worker, conversation); n8n wiring zweryfikowany GET-em po PUT
(Cmt FALSE -> Is Dec Callback?; Dec Secret -> Dec Fire; binaryMode=separate).

## Udzial Tomasza (w paczce deploy po kroku [3])

1. SSH: `docker exec -i pg_n8n psql -U n8n -d ags_crd < ~/ags-agents/cm-agent/db/024_agent_decisions.sql`
2. Push + rebuild. 3. Tap-test guzika decyzji.
