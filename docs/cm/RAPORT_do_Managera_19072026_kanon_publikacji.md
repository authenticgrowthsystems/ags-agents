# RAPORT do Managera: KANON PUBLIKACJI - krok [3] planu dnia (19/07/2026)

Od: BE. Brief: docs/briefs/BRIEF_KANON_PUBLIKACJI_19072026.md.

## Co zrobione (kod)

1. **_emergency_promote USUNIETY Z KODU** (worker.py) - na stale, zgodnie z kanonem 19/07
   pkt 2. Zadnego auto-zatwierdzania niezatwierdzonych, nigdy.
2. W jego miejsce **_stale_approval_watch**: material czekajacy >24h na approve = eskalacja
   GUZIKAMI (decisions.ask, typ 'stale_approval': ⭐ Pokaz karte / Odrzuc material /
   Przypomnij jutro; akcje w decisions._apply_action). Throttle w DB - jedna otwarta/swieza
   decyzja per item, zero flood-u.
3. Komunikaty "brak reakcji 24h = publikacja awaryjna" usuniete z: promptu CM (krok [2]),
   _plan_approve (conversation.py), approve-all (planner.py) - zastapione prawda kanonu.
4. channels.config.emergency_publish = martwy klucz (kod go nie czyta); usuniety z opisu
   target_update.

## Selektywne odmrozenie held - DOWOD zamiast zalozenia

Regula Tomasza brzmiala: "held z itemem approved/dispatching -> przywroc scheduled".
Sprawdzilem w DB (read-only, verify-held-1907.cjs): **w held NIE MA ani jednego wiersza
z itemem approved/dispatching**. Sklad 22 wierszy:
- 5 x item 'published' (sloty minione 12-14/07) - przywrocenie = DUBLE juz opublikowanych
- 2 x item 'rejected' - nie moga wyjsc
- 15 x sieroty bez content_item i bez slotu (czesci nitek X z czerwca, sprzed pipeline'u)

Wniosek: odmrozenie wg reguly = no-op; zamiast tego SQL sprzatajacy (a) 7 wierszy
published/rejected -> rejected (bezdyskusyjne), (b) sieroty -> rejected (DO DECYZJI Tomasza
guzikami - to stara tresc, nowy plan i tak powstaje w kroku [4]). SQL w briefie.

## Dowody

py_compile OK; `grep _emergency_promote` w repo -> tylko docs historyczne; watcher w petli
(worker.loop) z komentarzem kanonu.

## Udzial Tomasza

Deploy paczki [1]+[2]+[3] (komendy w podsumowaniu sesji): psql 023 + 024, SQL (a)(+b),
push, rebuild, tap-testy.
