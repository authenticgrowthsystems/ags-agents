# RAPORT do Managera: BRAMKA TEMATOW - krok [4] planu dnia (19/07/2026)

Od: BE. Brief: docs/briefs/BRIEF_BRAMKA_TEMATOW_19072026.md.

## Co zrobione (kod)

1. **planner.build_plan**: prompt przebudowany - ZRODLA TEMATOW w obowiazkowej kolejnosci
   (1. filary marki, 2. problemy ICP, 3. schowek pomocniczo); ostatnie publikacje ZDEGRADOWANE
   do roli antydubla (nie inspiracji - to byla petla); BRAMKA META w prompcie z licznikiem
   "zostalo X na ten tydzien" + dowod z metryk (meta 2-44 wysw. vs narracja 2331).
2. **Twardy filtr za promptem** (LLM bywa glucha na limity): _meta_like (regex PL+EN:
   kadencja/sloty/kolejka/luki/cadence/empty slot/queue/autopilot/subagent + para
   "moj|nasz|my|our" x "system|agent|bot|pipeline") - przetestowany: 6/6 tematow z incydentu
   zlapanych, 0 falszywych trafien na tematach normalnych. Budzet META_MAX_WEEK=1 liczony
   z content_items (7 dni, bez rejected/archived) - wspolny dla plannera i gap-fillera.
3. **Limit planu**: _enforce_plan_cap - max 20 proposed, najstarsza nadwyzka -> archived.
   Plan 78 pozycji sie nie powtorzy.
4. **proactive._propose_for_gap** (gap-filler - glowny sprawca petli): te same zrodla
   (filary/ICP w prompcie), ta sama bramka z budzetem, twardy filtr przed INSERT.
5. **Jawnosc**: komunikat planu raportuje "odrzucilem N meta-tematow" i "N poszlo do
   archiwum" - zero cichych ciec (REGULA PRAWDY).

## Co zostalo Tomaszowi (zamkniecie kroku [4])

Po deployu paczki [1]-[4]: napisac do CM **"zaplanuj tydzien"** -> plan przyjdzie z bramka
(max 20 pozycji, meta <=1, tematy z filarow/ICP) -> przeglad guzikami -> zatwierdzenie.
Stary plan wyczyszczony 19/07 rano (78 proposed -> rejected, zweryfikowane).

## Dowody

py_compile OK (planner, proactive); test heurystyki w transkrypcie sesji (6/6 + 3/3 + 0 FP).
