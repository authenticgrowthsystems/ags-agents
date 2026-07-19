# BRIEF BUILDU: ESKALACJA+NAUKA (19072026)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_ESKALACJA_19072026.md zbuduj`
(Build wykonany w sesji dnia 19/07 - plan dnia krok [2].)

## 1. CO budujemy (definition of done)

Kanon 19/07 pkt 3: pytania CM/subagentow do Tomasza = ustrukturyzowane decyzje z GUZIKAMI;
kazda odpowiedz -> agent_learning_log; typy decyzji z wysoka zgodnoscia przechodza (za
tapnieciem Tomasza) na semi_autonomous - wtedy system decyduje sam i wysyla paragon.

DoD:
- [ ] DDL 024 wgrany (agent_decisions + decision_modes) + SCHEMA w tym samym commicie
- [ ] CM w rozmowie eskaluje przez tool escalate_decision -> wiadomosc z guzikami (⭐ rekomendacja)
- [ ] Tap w guzik -> paragon nowa wiadomoscia + wpis agent_learning_log + guziki znikaja
- [ ] Po 10+ odpowiedziach z 80%+ zgodnoscia system proponuje semi-auto (guzikami)
- [ ] /decyzje pokazuje czekajace decyzje ustrukturyzowane

## 2. KONTRAKT wpiecia w szyne

- Tabele: NOWE agent_decisions, decision_modes (DDL 024); pisze agent_learning_log (020).
- Endpointy: POST /decnav {raw, chat_id, message_id} (guard, 202+watek; wzorzec /cmt).
- Telegram/n8n: callback 'dec:<id>:<key>'; HITL lancuch If-ow: Is Cmt Callback? FALSE ->
  NOWY Is Dec Callback? -> Dec Secret -> Dec Fire (/decnav); FALSE -> Is Cm Callback?.
  Patcher hitl-dec-callback.cjs z backupem; settings filtrowane (binaryMode nietykany).
- Modul: app/decisions.py (ask / handle / mode_for / pending_text; progi PROG_MIN=10,
  PROG_ZGODY=0.8, okno 20).

## 3. Czego NIE dotykac

- Zatwierdzanie TRESCI (karty matnav/hitl approve) - poza mechanizmem semi-auto NA ZAWSZE
  (kanon: niezatwierdzone nigdy samo).
- Istniejace galezie callbackow (plannav/mat/cmt/mtier...) - tylko wpiecie w FALSE lancucha.

## 4. Zaleznosci i stan zastany

agent_learning_log + execution_mode (#87, DDL 020), wzorzec approval-learning Researchera
(agent_approval_gates model_selection), admin chat = brand_config admin_chat_ids (hitl._admin_chat_id).

## 5. Udzial Tomasza

1. SSH: psql db/024. 2. Push + rebuild (paczka z krokami [1]+[3]). 3. Tap-test: poprosic CM
o decyzje (albo poczekac na pierwsza naturalna eskalacje) i tapnac guzik.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

STATUS = DONE-CODE (19/07): kod + n8n LIVE (galaz dec:, backup bk_hitl_deccb_*.json,
binaryMode zweryfikowany). Prompt CM: standard ESKALACJA DECYZJI dopisany; przy okazji
USUNIETA z promptu linia o publikacji awaryjnej 24h (kanon 19/07 - reszta w kroku [3]).
CZEKA: psql 024 + rebuild + tap-test. Raport: docs/cm/RAPORT_do_Managera_19072026_eskalacja.md
