# RAPORT ZAMKNIECIA dla AGS BUILD ENGINEERA - Build INTAKE-UX (22/07/2026 ~00:35)

Budowniczy: BE-INTAKE-UX (okno rownolegle wg protokolu sesji). Brief:
docs/briefs/BRIEF_INTAKE_UX_21072026.md (STATUS w briefie zaktualizowany).
Raport wykonawczy dla Managera: docs/cm/RAPORT_do_Managera_21072026_intake_ux.md.

## STAN: DONE - WDROZONE LIVE, TAP-TESTY DoD 4/4 PASS

Galaz build/intake-ux, commity (wszystkie zmergowane do claude/silly-blackwell-dfc32d
i wdrozone rebuildami cm-agenta tej nocy, /health ok):
- 00226bf - rdzen B1-B4 (opis nizej) + fix martwego guzika "Inny kat" (TRUTH_GUARD)
- 2c5a545 - iteracja po tapach b+d: [Wkleilem]/[Wyslalem] = cmt:sent (JEDNO tapniecie
  domyka cykl: sent + stadium CRM, bez task_queue i drugiego gotowca; cmt:ok/done =
  legacy dla starych kart) + naglowek "🎯 brand/kanal • publikacja: EN/PL" + kontrola
  po polsku dla tresci nie-PL (translate_text)
- 5b09cb5 - fix po tapie a: kontrola PL po TRESCI (_looks_polish), nie po jezyku kanalu
  + koniec DRUGIEJ linii guzikow (legacy panel _send_comment_controls czyszczony
  w _send_author_proposal)
- b8de7bb - fix jezyka DM: jawny krok "ustal jezyk OSTATNIEJ wiadomosci rozmowcy"
  + deklaracja JEZYK w formacie (model odpowiadal po polsku na angielski DM)

Zero DDL, zero patchy n8n (galezie cmt:/dec: routuja po prefiksie - zweryfikowane
na zywo). Dotkniete pliki: conversation.py, crm.py, decisions.py, engagement.py
+ komponenty rozmowa-cm.md i engagement-crm.md (w tych samych commitach).

## Co weszlo (B1-B4)

- B1 PAMIEC WATKU: przyczyna = trasy deterministyczne subagenta robily return PRZED
  zapisem historii; fix `_sub_record` (ten sam kontrakt co CM), karta intencji i paragony
  laduja w historii, prompt kaze sprawdzic historie zanim poprosi o powtorzenie;
  narzedzie `subagent_reply_dm` siega po ostatnie zrzuty samo.
- B2 MENU INTENCJI: wrzutka -> `_screen_shots` (wizja-klasyfikacja) -> JEDNA karta
  "CO WIDZE + PROPONUJE" (decisions.ask typ `intent_menu`; watek = OBIEKT w
  agent_decisions.context: insp_ids/contact_id/screening/done_keys - gotowe pod przyszly
  konektor Slack/webapp) -> `apply_intent_menu` sekwencyjnie z potwierdzeniami, po
  ostatnim "co dalej?", pojedynczy wybor -> karta z POZOSTALYMI intencjami.
- B3 DEDUP OSOBY: `crm.clean_author` (warianty '• 2nd'/emoji/zaimki -> jedna osoba),
  doklejka zrzutow do OTWARTEJ karty <24h, 1 decyzja crm_tier per osoba/24h, karta
  "Nowa osoba" max 1/24h (brand_config crm_intake_offered).
- B4 HTML: `_reply` -> `_send_rendered` -> `_md_to_html` (**/###/backtick -> HTML,
  tekst bez znacznikow plain, blad renderu = fallback plain).

## Tap-testy DoD (21-22/07 noc, z Tomaszem)

- d PASS: pogrubienia bez gwiazdek (subagent linkedin + x).
- b PASS: album Neila Patela -> JEDNA karta (dec #8) -> Skomentuj + intake po kolei
  z potwierdzeniami -> "co dalej" (dec #9, #10 crm_tier=Competitor).
- c PASS: ten sam profil 2x -> "Doklejone do OTWARTEGO watku" (dec #11), zero 2. karty.
- a PASS: streszczenie DM -> 3 wiadomosci dalej "odpowiedz na ten DM" bez proszenia
  o powtorzenie; re-test po fixie jezyka: odpowiedz PO ANGIELSKU (jezyk rozmowy
  Djordje), jeden rzad guzikow, [Wyslalem] domknal jednym tapnieciem.

## Otwarte drobiazgi / backlog (nie blokuja DONE)

1. Do potwierdzenia u Tomasza: czy "🇵🇱 Kontrola po polsku" byla widoczna nad guzikami
   przy angielskiej odpowiedzi DM (tapniecie nadpisuje te wiadomosc potwierdzeniem,
   zrzut jej nie lapie). Jesli nie byla - sprawdzic wyjatek translate_text w logach.
2. Slownictwo: Tomasz woli "POTWIERDZENIE" zamiast "paragon" w tekstach bota -
   zamiana w komunikatach widocznych przy nastepnej iteracji (pamiec:
   feedback_potwierdzenie_nie_paragon).
3. sales.py: ta sama poprawka ** (markdown->HTML przez _send_rendered) - poza zakresem
   briefu ("NIE DOTYKASZ sales.py"), 1 linia przy nastepnym buildzie sprzedawcy.
4. Stare brudne stuby contacts sprzed clean_author - scalic SQL-em przy pierwszym dublu.
5. Jednorazowa cisza po "Usun #194 z kolejki bo opublikowalem recznie" (23:51) - repro
   "usun #194" zadzialalo z potwierdzeniem 🗑; jesli sie powtorzy, logi z okna zdarzenia.
6. Tapniecie [Wyslalem] nadpisuje tresc wiadomosci z kontrola PL - kontrola znika z czatu
   po decyzji; jesli Tomasz zechce ja zachowac, potwierdzenie moze isc NOWA wiadomoscia.

## Nastepny ruch wg planu

LACZNIK SYNCHRONIZACYJNY (decyzja Tomasza TAK, START po DONE INTAKE-UX - warunek
spelniony). Koncept: docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md (commit fb10ea9).
Sesja lacznika pisze wlasny brief wg protokolu (docs/briefs/PROTOKOL_SESJI.md).
