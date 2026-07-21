# RAPORT do Managera - Build LACZNIK SYNCHRONIZACYJNY (22/07/2026)

Budowniczy: BE-LACZNIK (okno rownolegle, galaz build/lacznik od
origin/claude/silly-blackwell-dfc32d 01bbeec - zawiera zamkniecie INTAKE-UX 94c0362).
Brief: docs/briefs/BRIEF_LACZNIK_22072026.md. Koncept (zrodlo wymagan):
docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md (ZATWIERDZONY 21/07).

## STAN: ZBUDOWANY - czeka wdrozenie (integrator) + tap-testy DoD

## Commity

1. Mini-porzadki po INTAKE-UX (raport zamkniecia pkt 2):
   - (a) sales przez _send_rendered = NO-OP: sales._tg_send delegowal do
     conversation._reply od pierwszego commita, a _reply przeszlo na _send_rendered
     w INTAKE-UX B4 - po merge Sprzedawca renderuje HTML za darmo. Zero zmian w sales.py.
   - (b) "paragon" -> "potwierdzenie" w komunikatach WIDOCZNYCH: karta intent_menu
     (conversation) + pytanie mode_transition (decisions). Doktryna w docs zostaje.
   - (c) potwierdzenie po [Wyslalem]/[Wkleilem] NOWA wiadomoscia: edycja nadpisywala
     wiadomosc z kontrola PL; teraz z oryginalu schodza tylko guziki, potwierdzenie
     przychodzi osobno - kontrola PL zostaje w czacie.
2. Build LACZNIK etap 1 (4 klocki, ZERO DDL, zero LLM w parserze i /kontekst):
   - **Parser RAPORT PRACY** (engagement.apply_work_report + route w conversation.handle
     PRZED sales.try_command - uzbrojony material sprzedazowy nie zje raportu; dziala
     tez dla pliku .md przez handle_document). Typy: komentarz / dm_wyslany /
     dm_odebrany / reakcja / nowa_osoba / obserwacja. INSERTy: engagement_log (status
     wg typu) + contacts (clean_author z INTAKE-UX, stadium komentarz->commented,
     dm->dm) + inspirations (obserwacje, source='raport_pracy') + JEDNA karta crm_tier
     per nowa osoba/24h (dedup po agent_decisions). Idempotencja: sha256(kanal|linia)
     [:16] jako 'sync:<hash>' w notes - podwojna wklejka = "pominiete duplikaty: N".
     Potwierdzenie z licznikami + jawna lista niezrozumianych linii (REGULA PRAWDY).
   - **/kontekst [x|linkedin|sprzedaz|all]** (reports.kontekst_text/send_kontekst):
     plan tygodnia + kolejka per kanal + publikacje 7 dni z metrykami + kontakty w grze
     + otwarte decyzje + lejek + radar; tekst <=4000 albo plik .md
     (_tg_send_document). Przepustka n8n: patcher
     n8n-workflows/patches/hitl-kontekst-command-22072026.cjs (backup + deactivate+
     activate; kotwica po patchu sprzedazy 20/07).
   - **Strona Notion "Stan gry AGS"** (sync/stan_gry.py, tick z petli notion_workera):
     jedna strona NADPISYWANA (table_registry._re_render, soft-clear + mirror_state,
     bez wpisu w sync_registry), throttle 15 min (porazka Notion TEZ zuzywa okno -
     timeouts #71 nie mloca API), odcisk stanu md5 z max timestampow 6 tabel.
     Konfiguracja: brand_config stan_gry_page_id (SQL - /set nie zna klucza).
   - **Masterprompt czatowy X v1** (docs/product/masterprompty-czat/): tozsamosc +
     destylat glosu (regula prawdy, zero em dash, EN na X / jezyk rozmowcy w DM,
     comment-first) + rytual startu (stan gry z <LINK_STAN_GRY>, fallback prosba o
     /kontekst) + OBOWIAZKOWY blok [RAPORT PRACY v1] na koniec sesji. Wsad Tomasza
     (robocze masterprompty) scalimy przy dostarczeniu - pelny plik, podbicie wersji.

## Dokumentacja (te same commity)

Nowy komponent docs/komponenty/lacznik.md; aktualizacje: engagement-crm.md (warstwa
LACZNIK), sync-notion.md (strona Stan gry), rozmowa-cm.md (route 3b), masterprompt
RESUME_MASTERPROMPT_19072026.md (wpis BE-LACZNIK), STATUS w briefie.

## Wdrozenie (integrator; ZERO DDL)

merge build/lacznik -> rebuild cm-agent -> node patch hitl-kontekst-command -> Tomasz:
strona Notion "Stan gry AGS" (Connection integracji! AP-305) + SQL stan_gry_page_id
(gotowa komenda w komponencie) + podmiana <LINK_STAN_GRY> w masterprompcie.

## Tap-testy DoD (z briefu)

a) wklejka przykladowego RAPORTU (5 linii: 1 duplikat, 1 nowa osoba) -> potwierdzenie
   z licznikami + karta tieru; druga wklejka -> "pominiete duplikaty: 5";
b) /kontekst x -> stan zgodny z baza (sonda read-only);
c) strona Notion odswieza sie po zmianie (timestamp w callout);
d) masterprompt X w czacie na abonamencie: czyta stan z linku, konczy poprawnym RAPORTEM.

## Uzupelnienie: wsad masterpromptow Tomasza (22/07, ten sam dzien)

Tomasz dostarczyl 3 robocze masterprompty (LinkedIn SM, Content Manager 15/06,
X Comment Specialist 30/04). Scalone:
- **X_v2** (zastepuje v1): szablony reply A-D z balansem, 17 zelaznych zasad,
  prawdziwe historie Tomasza (jedyne dozwolone case studies), listy kont Tier 1-3/
  peers/competitors/big-tech, strategia QT; wyciete stan sesji i logowanie Notion.
- **LINKEDIN_AGS_v1** (nowy): reguly operacyjne (komentarz=obserwacja, DM bez
  Calendly, anti-fabrication, banned words), klasyfikacja Buyer/Peer/Partner/
  Competitor-adjacent, frame buyer-lane (anti-dryf w AI-educatorow); stan pipeline
  wyciety - zyje w stanie gry.
- **DECYZJA GUZIKAMI: Lead Tracker Notion = archiwum do odczytu.** Czat nie pisze
  do Notion; praca wraca WYLACZNIE raportem do bazy (kanon SSOT). Seed pipeline
  z Trackera = jednorazowy raport liniami nowa_osoba.
- **Czatowy CM bez wersji stalej** (serwerowy CM = orkiestrator; dublowanie prawdy).
  Prompty "content X/LinkedIn" nieuzywane - pominiete.
- **Parser rozszerzony o typ 'zaproszenie'** (`- zaproszenie | @slug | wyslane/
  przyjete | notka`; contact + logged, bez bumpu stadium - 'connected' nie istnieje
  w skali relacji).

## Ryzyka / uwagi

- Notion timeouts (#71): stan gry ma throttle i nie blokuje niczego; fallback /kontekst.
- Parser liczy na format z masterpromptu; niezrozumiane linie wracaja jawnie w
  potwierdzeniu (nic nie ginie po cichu).
- Etap 2 (MCP/endpoint read-only dla czatu) swiadomie NIE ruszony (brief pkt 3).
- NIE ruszone bez sygnalu: ujednolicenie zdjec przy CM, scalanie starych stubow.
