# BRIEF BUILDU: LACZNIK ETAP 2 - zero kopiowania (22072026) - budowniczy: BE-LACZNIK-E2

Wywolanie (Fable 5 max 2 prompty -> Opus 4.8 konczy):
`@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_LACZNIK_ETAP2_22072026.md zbuduj`
CZYTAJ NAJPIERW: docs/komponenty/lacznik.md (Etap 1 = fundament, NIE ruszac parsera!)
+ docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md + n8n-transport.md.
DECYZJA Tomasza 22/07 wieczor: "nie mam czasu, chce natychmiast" - sygnal skali PADL,
Etap 2 wchodzi przed 48h obserwacji (obserwacja publikacji biegnie rownolegle,
ten build NIE DOTYKA maszynerii publikacji).

## 0. Tryb rownolegly

Worktree+galaz `build/lacznik-e2` od origin/claude/silly-blackwell-dfc32d (PO pushu
0dd5989+). n8n: NOWY osobny workflow (zero dotykania HITL i Schedulera!). cm-agent:
tylko ewentualny cienki endpoint (parser i kontekst JUZ istnieja).

## 1. CEL

Praca Tomasza w czacie na abonamencie raportuje sie do systemu SAMA i czat czyta stan
gry SAM - zero kopiowania w obie strony. Czatowy agent dostaje NARZEDZIA zamiast
instrukcji "wklej Tomaszowi".

## 2. CO budujemy

1. **Serwer narzedzi w n8n dla czatu** - preferowany wariant A: MCP Server Trigger
   (n8n >= 1.88; NAJPIERW zweryfikuj wersje n8n na Mikrusie - docker image tag /
   Settings About; jesli za stara, wariant B nizej). Workflow "Lacznik Chat Tools"
   z DWOMA narzedziami:
   - `wyslij_raport_pracy(kanal, raport_md)` -> POST do cm-agent /message
     (chat_id = admin, text = raport) -> istniejacy parser [RAPORT PRACY robi reszte
     (idempotencja juz jest); zwrot = potwierdzenie z licznikami.
   - `stan_gry(kanal)` -> GET stanu przez istniejacy reports.kontekst_text
     (cm-agent /kontekst przez /message albo cienki GET /stan?secret=...) -> zwraca
     md. To ZASTEPUJE czytanie Notion w rytuale startowym (Notion zostaje lustrem
     i fallbackiem).
   Autoryzacja: sekret w naglowku/URL z app_secrets (nowy klucz lacznik_e2_secret);
   NIE wystawiac bez sekretu.
2. **Wariant B (fallback, gdy brak MCP Triggera):** zwykly webhook n8n
   POST /webhook/chat-raport {secret, kanal, raport} + GET /webhook/stan-gry?secret=
   - a po stronie czatu ChatGPT Custom GPT z Action (schemat OpenAPI w briefie
   budowniczego) LUB pozostaje wklejka dla Claude. Preferuj A (Tomasz pracuje
   glownie na Claude).
3. **Masterprompty czatowe v3** (X i LinkedIn, pelna polszczyzna): rytual startu =
   wywolaj narzedzie stan_gry; rytual konca = wywolaj wyslij_raport_pracy z blokiem
   RAPORT PRACY v1 (format BEZ zmian - ten sam parser!). Fallback: gdy narzedzia
   niedostepne, stary rytual (Notion + plik). Pliki: docs/product/masterprompty-czat/
   (pelne nowe wersje, nie diffy).
4. **Instrukcja podpiecia dla Tomasza** (docs/product/masterprompty-czat/README):
   claude.ai -> Settings -> Connectors -> Add custom connector -> URL serwera MCP
   z n8n; krok po kroku ze zrzutami slow.

## 3. Czego NIE robic

Parser, /kontekst, strona Notion, formaty raportu - BEZ ZMIAN (Etap 2 = transport,
nie logika). Zadnych zmian w publikacji/planner/sales/decisions. Zadnego LLM w n8n.

## 4. DoD (tap-testy z Tomaszem)

a) W sesji czatowej Claude z konektorem: "pokaz stan gry x" -> agent woła narzedzie
   i streszcza stan zgodny z baza (sonda read-only potwierdza zrodlo).
b) Sesja konczy sie JEDNYM poleceniem "wyslij raport" -> narzedzie -> potwierdzenie
   z licznikami wraca DO CZATU + wpisy w engagement_log (sonda) + Telegram dostaje
   kopie potwierdzenia.
c) Podwojne wyslanie tego samego raportu -> "pominiete duplikaty" (idempotencja).
d) Wylaczony konektor -> masterprompt v3 sam przechodzi na fallback (Notion+plik).
Dokumentacja W TYM SAMYM commicie: komponent lacznik.md sekcja Etap 2 + README
podpiecia + masterprompt (backlog: wpis DONE).

## 5. Udzial Tomasza
Weryfikacja wersji n8n (1 komenda SSH od budowniczego), dodanie konektora w claude.ai
(instrukcja), tap-testy a-d.

## 6. Zamkniecie: raport + STATUS tu. STATUS = READY (22/07 ~18:20)
