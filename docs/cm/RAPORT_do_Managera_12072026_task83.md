# RAPORT do Managera - 12/07/2026: Task #83 cele TNM PL / AGS Page / RDC PL

Od: BUILD ENGINEER | Status: kod commit 80f4dfc + SQL 018 gotowy; czeka SSH+rebuild Tomasza
Termin briefu: 13/07 wieczor - dowiezione dzien wczesniej.

## Diagnoza (docs-first) - brief mial niepelna diagnoze

Cele **JUZ ISTNIALY** od 04/07: TNM/linkedin (pl, prefix linkedin_tnm), RDC/linkedin (pl,
prefix linkedin_rdc), AGS/linkedin_page (en, prefix linkedin_ags_page) - wszystkie 'ready';
marki AGS/TNM/RDC w brands. Realny bug: **_channels_snapshot() hardcode brand_id='AGS'** -
CM w rozmowie 12/07 10:52 widzial tylko 6 celow AGS i twierdzil, ze TNM nie ma.
Drugi brak: **TNM/RDC nie maja voice_bible w brand_config** (tylko AGS v3).

## Wykonane

1. **80f4dfc**: CM widzi cele WSZYSTKICH marek (grupowanie po marce w kontekscie rozmowy).
2. **SQL placeholdery** (SSH one-liner podany Tomaszowi): brands LYSY/PT/SDI (paused) +
   channels linkedin ready z prefixami linkedin_lysy/pt/sdi (idempotentne ON CONFLICT).
3. **db/018_tnm_voice_activation.sql (WERSJA FINALNA po adopcji)**: TNM Voice Bible PL v2.0
   od Managera TNM (konsolidacja 31/05) ADOPTOWANA przez Tomasza z 3 poprawkami BE:
   Hard Rule 4.11 Regula Prawdy (wniosek z truth-sweep 12/07), Aneks A = 5 filarow
   build-in-public z Brand Canonical (decyzja: obowiazuja jako tematyka), pozycja
   checklisty. Dollar-quote AP-303, idempotentny, wersja 2. + banned_vocab TNM
   (anglicyzmy z sekcji 5.1/5.2). Moj wczesniejszy destylat v1.0 = zastapiony
   (byl z kanonu kwietniowego, v2.0 nowsza i pelniejsza).

## Decyzje Tomasza (guziki + doprecyzowanie 12/07)

- ADOPT v2.0 z poprawkami (4.11 + Aneks A) - werdykt do przekazania Managerowi TNM,
  zeby zsyncowal canonical i Notion.
- **KANALY TNM (doprecyzowanie Tomasza): TNM na LinkedIn = TYLKO strona firmowa** (konto
  osobiste Tomasza = wylacznie EN; TNM tam drugorzednie). ZERO aktywacji przez token
  personal - cel TNM/linkedin zostaje 'ready' do App 2 CMA. Wkrotce osobny profil X TNM,
  pozniej IG/FB (nowe cele gdy powstana). LinkedIn = glowne zrodlo artykulow.
- Publikacje TNM do czasu App 2 = reczne + log przez intake [ZEWN].
- Kanon RLS: bez zmian (aktywacji operacyjnej 2. marki na razie nie ma).

## Zostaje w #83

- RDC voice_bible: wg kanonu glosu-DNA (Tomasz: "glos RDC to to samo") = rdzen wspolny +
  nakladka RDC; zrobie po ustaleniu wzorca na TNM w praktyce. RDC zostaje 'ready'.
- AGS linkedin_page + TNM strona: aktywacja po App 2 CMA review (blocker zewnetrzny).
- Zero DDL = SCHEMA_ags_crd.md bez zmian (regula 08/07 dotyczy DDL).

## Tap-test (po SSH 018 + rebuild)

Do CM: "jakie mamy cele publikacji?" -> lista z sekcjami MARKA AGS / TNM (ready) / RDC /
LYSY / PT / SDI. Potem: "napisz probny post TNM o decyzjach przed narzedziami" -> generacja
PO POLSKU w glosie v2.0 (mama-test, zero anglicyzmow, value-first).
