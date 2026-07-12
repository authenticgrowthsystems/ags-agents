# RAPORT do Managera - 12/07/2026: Task #86 Brand Management UI (v1 tekstowa)

Od: BUILD ENGINEER | Status: kod + DDL 021 + przepustka n8n LIVE; czeka SSH+rebuild+tapy.
Zbudowane w dniu briefu (termin byl 17/07).

## Decyzja wykonawcza (godz. ~23:30)

v1 = KOMENDY TEKSTOWE deterministyczne (zero LLM, zero nowych galezi callbackow w n8n -
tylko przepustka /brand* w Detect Update Type, patch LIVE). Guziki-toggle (zielony/szary
per marka) = nastepna sesja z tapem Tomasza (nowa rodzina callbackow brd: w HITL, AP-301).

## Wykonane

- **db/021**: brands.status CHECK + 'archived' (soft-delete per brief; bylo tylko
  active|paused - dowod pg_get_constraintdef). SCHEMA w tym samym commicie.
- **app/brands_ui.py** (nowy modul, wpiety PRZED LLM w conversation.handle):
  /brands (lista: ikona statusu, nazwa, cele aktywne/wszystkie), /brand_on, /brand_off,
  /brand_add NAZWA (marka paused + cel linkedin ready + checklista kompletnosci = zalazek
  wizarda), /brand_remove (archived + aktywne cele -> paused, dane zostaja),
  /brand_config NAZWA (kompletnosc: voice_bible/tokeny wizualne/cele/execution_mode),
  /brand_export NAZWA (pelny JSON jako plik .json - config+glos+cele+tokeny, 'klient
  zabiera swoja marke').

## Zakres NA POZNIEJ

- Guziki toggle + wizard krok-po-kroku FSM (voice->visual->ICP->kanaly->execution_mode) -
  v1 daje checkliste i komendy; pelny wizard po decyzji o priorytecie vs adapter Articles.
- Egzekwowanie execution_mode w petli (semi/auto) - progi per subagent = decyzje Tomasza.

## Tap-test (po SSH 021 + rebuild, ~1 min)

/brands -> lista 6 marek; /brand_config TNM -> ✅ voice v2 + cele; /brand_add TEST_BRAND ->
checklista; /brand_remove TEST_BRAND -> archiwum; /brand_export AGS -> plik .json.
