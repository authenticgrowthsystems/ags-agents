# RAPORT do Managera: build ENGAGEMENT-CRM (BE-ENGAGEMENT, 20/07/2026)

Brief: docs/briefs/BRIEF_ENGAGEMENT_CRM_20072026.md | Galaz: build/engagement-crm
(od claude/silly-blackwell-dfc32d 0fdcf23) | Komponent: docs/komponenty/engagement-crm.md

## 1. Problem (feedback Tomasza z pierwszej realnej sesji komentowania na telefonie)

Comment-radar dzialal E2E, ale: osoby komentowane NIE trafialy do CRM (baza contacts
z 45 osobami lezala odlogiem od #71), decyzje byly batchowe i ginely w prozie notes,
przeskoczone propozycje znikaly bez sladu, a 2 zrzuty jednego dlugiego posta produkowaly
dwoch "autorow-duchow" (incydent Dhairya/Vladimir).

## 2. Co zbudowane (A-E briefu, wszystko w jednej paczce)

A. **Propozycja per AUTOR = wlasny rekord + wlasne guziki.** Trzy wiadomosci per autor:
   naglowek z kontekstem CRM / czysta wklejka / guziki cmt:ok|angle|no POD ta propozycja.
   "Inny kat" regeneruje TEGO autora (nie caly zrzut). Zero decyzji z prozy - cykl zycia
   w kolumnie engagement_log.status (proposed/approved/rejected/sent/skipped, DDL 026).
B. **CRM obowiazkowy.** Dopasowanie autora do contacts po handle (x_handle + handles jsonb
   multi-platforma) i nazwie; znany = "komentowales 3x, stadium: commented, tier: Peer"
   w naglowku; NIEZNANY = natychmiastowy stub (contact_id ZAWSZE wypelnione) + wymuszony
   intake: zrzut profilu -> wizja -> bio/handle + tier proponowany przez model, zatwierdzany
   guzikami (decisions 'crm_tier', Buyer/Peer/Competitor/Partner wg doktryny ICP #71).
   Stadium relacji cold->commented->replied->dm->offer->client (bump tylko w przod przy
   potwierdzonym wklejeniu).
C. **Pamiec watku + domykanie petli.** "Co wisi?" listuje deterministycznie; po 24h
   przypomnienia guzikami: proposed -> [Wyslalem][Pomin][Pokaz jeszcze raz], zatwierdzone
   niepotwierdzone -> [Tak, odhacz][Nie, pomin]. Wzorzec stale_approval, throttle w DB.
D. **Multi-zrzut = jeden post.** Album Telegram (media_group_id) -> jedna sklejona analiza
   wielu obrazow (patch n8n dopisuje pole do metadata; plik w repo, uruchamia integrator).
   Zrzuty wyslane OSOBNO w <60 s -> JEDNO pytanie guzikami "jeden post czy rozne?"
   (dziala tez BEZ patcha n8n jako fallback).
E. **Dokumentacja w tym samym commicie:** komponent engagement-crm.md, SCHEMA (026),
   SYSTEM_DATAFLOW indeks, GOTOWOSC_PRODUKTU (Subagent X: CRM relacji w kolumnie
   "dojedzie w cenie" do czasu wdrozenia), rozmowa-cm.md, masterprompt.

## 3. Pliki

- cm-agent/db/026_engagement_crm.sql (idempotentne; AP-304: stan zastany z 001 + audytu 04/07)
- cm-agent/app/crm.py (NOWY), conversation.py, engagement.py, decisions.py, worker.py,
  generate.py (comment_from_image multi-obraz + format POST:/KOMENTARZ:; profile_from_image)
- n8n-workflows/patches/hitl-photo-mediagroup-20072026.cjs (backup + deactivate/activate w srodku)
- py_compile: PASS na wszystkich zmienionych modulach.

## 4. Decyzje architektoniczne (do wiadomosci Managera)

1. Guziki intake/tier/przypomnien jada ISTNIEJACYMI galeziami n8n (cmt: i dec:) - zero
   nowych wezlow routingu, jedyna zmiana n8n to jedno pole w Prepare Idea Photo.
2. icp_tier: CHECK poszerzony o doktryne #71 zamiast migracji 45 legacy wierszy -
   konsolidacja zdublowanych kolumn contacts pozostaje osobnym, znanym dlugiem (audyt 04/07).
3. Nowe typy decyzji (crm_tier, stale_comment, stale_comment_task, photo_group) wpiete
   w decisions.ask = kazda odpowiedz Tomasza uczy (agent_learning_log) i moze z czasem
   przejsc na semi-auto (NIGDY zatwierdzanie tresci).

## 5. Czego NIE ruszalem (zgodnie z briefem)

Fix czystej wklejki 20/07 (kod przejal jego wzorzec 1:1), publikacja, planner, dedup,
Notion contacts (DB=SSOT), konsolidacja kolumn contacts.

## 6. Wdrozenie (integrator + Tomasz)

merge build/engagement-crm -> psql 026 PRZED rebuildem -> rebuild cm-agent -> node patch
n8n -> tap-testy DoD (5): nieznany autor z intakiem, znany z kontekstem, przypomnienie
24h + "co wisi?", album 2 zrzutow = 1 analiza, contact_id wypelnione. Skala stadiow
ZATWIERDZONA przez Tomasza guzikami 20/07 (jeszcze w sesji buildu): pelna liniowa
cold->client + 'ghosted' jako stan boczny (ozywienie relacji = bump jak z cold).

## 7. Postulat do Managera

Stadium relacji + tier na kontakcie to gotowe wejscie pod przyszlego Opiekuna Relacji /
Sprzedawce (Blueprint) - raporty tygodniowe subagenta moglyby od wdrozenia liczyc
"nowe osoby w CRM / awanse stadium" jako metryke relacji, nie tylko zasieg.
