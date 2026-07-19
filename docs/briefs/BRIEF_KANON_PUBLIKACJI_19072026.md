# BRIEF BUILDU: KANON PUBLIKACJI - usuniecie stanu awaryjnego (19072026)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_KANON_PUBLIKACJI_19072026.md zbuduj`
(Build wykonany w sesji dnia 19/07 - plan dnia krok [3].)

## 1. CO budujemy (definition of done)

Kanon 19/07 pkt 1-2: zatwierdzone publikuje sie ZAWSZE, niezatwierdzone NIGDY samo.
_emergency_promote USUNIETY Z KODU NA STALE (nie flaga); >24h ciszy na approve = eskalacja
guzikami (stale_approval przez decisions). Selektywne odmrozenie held wg DOWODU z DB.

DoD:
- [ ] worker.py bez _emergency_promote (git grep pusty); w petli _stale_approval_watch
- [ ] Komunikaty o "publikacji awaryjnej" usuniete z conversation/planner/promptu CM
- [ ] SQL sprzatajacy held wykonany (Tomasz SSH) + verify

## 2. KONTRAKT wpiecia w szyne

- Kod: worker.py (_stale_approval_watch -> decisions.ask typ 'stale_approval', throttle w DB:
  jedna otwarta/swieza decyzja per item), decisions.py (_apply_action: show=karta,
  reject=odrzucenie, wait=nic), conversation.py + planner.py (komunikaty po zatwierdzeniu planu).
- Zadnych nowych tabel/endpointow (jedzie na DDL 024 z kroku [2]).

## 3. Czego NIE dotykac

Scheduler i sciezka publikacji zatwierdzonych - dziala bez zmian (zatwierdzone MA wychodzic).
channels.config.emergency_publish zostaje w DB jako martwy klucz (nieczytany przez kod).

## 4. DOWOD z DB (verify-held-1907.cjs, 19/07): held = 22 wiersze

- 5 x item 'published', sloty minione 12-14/07 (restytucja = DUBLE starych postow)
- 2 x item 'rejected' (nie moga wyjsc)
- 15 x SIEROTY bez content_item i bez slotu (czesci nitek X z czerwca, sprzed pipeline'u)
- ZERO itemow approved/dispatching -> odmrozenie wg reguly "approved -> scheduled" = NO-OP.

## 5. Udzial Tomasza

SQL (SSH, po decyzji guzikami co do sierot - patrz raport):
```sql
-- (a) held z itemem published/rejected -> rejected (7 wierszy; nie moga wyjsc drugi raz)
UPDATE post_queue pq SET status='rejected'
FROM content_items ci WHERE ci.id = pq.content_item_id
  AND pq.status='held' AND ci.status IN ('published','rejected');
-- (b) SIEROTY (15 starych czesci nitek bez itemu i slotu) - OPCJA wg decyzji:
UPDATE post_queue SET status='rejected'
WHERE status='held' AND content_item_id IS NULL AND scheduled_for IS NULL;
```
Plus deploy paczki [1]+[2]+[3]: psql 023, psql 024, push, rebuild.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

STATUS = DONE-CODE (19/07): _emergency_promote usuniety, watcher eskalacyjny w petli,
komunikaty oczyszczone. CZEKA: SQL (a)(+b) + deploy + tap-test przypomnienia.
Raport: docs/cm/RAPORT_do_Managera_19072026_kanon_publikacji.md
