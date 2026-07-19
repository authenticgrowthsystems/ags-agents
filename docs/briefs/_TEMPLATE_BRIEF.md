# BRIEF BUILDU: <nazwa> (<DDMMYYYY>)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_<aktualny>.md @docs/briefs/BRIEF_<nazwa>_<data>.md zbuduj`

## 1. CO budujemy (1-3 zdania + definition of done)
<zakres; DoD = lista dowodow: co musi dzialac i jak to zweryfikujemy (tap/SQL/log)>

## 2. KONTRAKT wpiecia w szyne (spojnosc z architektura)
- Tabele: <ktore czyta / ktore pisze; nowe DDL = kolejny wolny numer + SCHEMA w tym samym commicie>
- Endpointy/kolejki: <np. /request wzorzec Researchera, task_queue task_type=..., agent_messages, /wake po zapisie>
- Sekrety: <klucze w app_secrets, prefix>
- Telegram/n8n: <czy dotyka HITL; jesli tak - patcher z backupem + deactivate/activate + tap>

## 3. Czego NIE dotykac (guardrails)
<pliki/moduly/workflowy poza zakresem - np. "zero zmian w conversation.py", "nie ruszasz Schedulera">

## 4. Zaleznosci i stan zastany
<co juz istnieje i ma byc uzyte zamiast budowane od nowa; linki do specow/raportow>

## 5. Udzial Tomasza
<lista: ktore kroki wymagaja SSH/push/tap/decyzji guzikami - jak najkrotsza>

## 6. Zamkniecie sesji (OBOWIAZKOWE)
Raport docs/cm/RAPORT_do_Managera_<data>_<nazwa>.md + aktualizacja RESUME_MASTERPROMPT
(sekcje: STAN LIVE, backlog, next DDL) + pamiec trwala (project_resume_point) + wpis
w docs/briefs/<ten plik>: STATUS = DONE/PARTIAL z dowodami.
