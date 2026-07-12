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
3. **db/018_tnm_voice_activation.sql**: TNM Voice Bible v1.0 (destylat CANONICAL LOCKED
   TNM_Brand_And_Strategy.md - Symbioza, ICP PL, 8 twardych zasad jezyka, 5 filarow,
   dollar-quote AP-303, idempotentny) + banned_vocab TNM + AKTYWACJA celu TNM/linkedin
   (status active, secret_prefix -> 'linkedin' = istniejacy token personal).

## Decyzje Tomasza (guziki 12/07)

- "Glos TNM najpierw" - aktywacja dopiero z voice bible (wykonane w 018 jednym plikiem).
- **Swiadome odstapienie od kanonu RLS** dla wlasnych marek (TNM/RDC to marki Tomasza na
  wspolnej bazie, nie klienci); kanon RLS WRACA przed pierwszym klientem multi-tenant.

## Zostaje w #83

- RDC voice_bible (analogiczny destylat - brak zrodla kanonicznego RDC w repo; do wskazania
  przez Tomasza) - RDC zostaje 'ready'.
- AGS linkedin_page: config kompletny, aktywacja po App 2 CMA review (blocker zewnetrzny).
- Zero DDL = SCHEMA_ags_crd.md bez zmian (regula 08/07 dotyczy DDL).

## Tap-test (po SSH 018 + rebuild)

Do CM: "jakie mamy cele publikacji?" -> lista z sekcjami MARKA AGS / TNM (active) / RDC /
LYSY / PT / SDI. Potem: "zaproponuj pierwszy post TNM" -> generacja w glosie TNM po polsku.
