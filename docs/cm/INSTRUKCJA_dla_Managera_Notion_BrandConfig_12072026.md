# INSTRUKCJA dla Managera AGS: baza Notion "Brand Config" (task #84, tokeny wizualne marek)

Od: BUILD ENGINEER | Data: 12/07/2026 | Udzial Tomasza: JEDNA wiadomosc na koncu (punkt 5).

## Po co (kontekst w 3 zdaniach)

System generuje grafiki marek (gpt-image) i potrzebuje DOKLADNYCH tokenow wizualnych (hexy,
fonty, motywy, zakazy) per marka. SSOT = baza Notion "Brand Config"; cm-agent sam ja czyta co
10 minut i wgrywa do PostgreSQL (tabela brand_tokens); kazda generacja obrazu wkleja tokeny
marki do promptu. Bez bazy dziala fallback (przyblizony) - z baza brand trzyma sie co do hexa.

## 1. Gdzie utworzyc baze (WAZNE - dziedziczenie Connection)

Utworz baze jako PODSTRONE strony JUZ POLACZONEJ z integracja API (Connection dziedziczy sie
w dol drzewa - lekcja AP-305): **Nawrocki Hub** albo **TNM Operations Hub** (obie maja
Connection od 05/07/2026). NIE tworz w nowym/oderwanym miejscu - API dostanie 404.

## 2. Schemat bazy (kolumny DOKLADNIE tak nazwane - parser jest po nazwach)

| Kolumna | Typ Notion | Uwagi |
|---|---|---|
| Token_Name | Title | nazwa tokenu, np. color.navy |
| Token_Type | Select | opcje: color / font / spacing / motyw / zakaz |
| AGS_Value | Text (Rich text) | wartosc dla AGS |
| TNM_Value | Text (Rich text) | wartosc dla TNM |

Przyszle marki = kolejna kolumna `<BRAND>_Value` (np. RDC_Value) - parser jest generyczny,
zero zmian w kodzie. Pusta komorka = marka nie ma tego tokenu (ok).

## 3. Wiersze AGS - GOTOWE DO WKLEJENIA (zrodlo: brand-canon/ags.md sekcja 3, CANONICAL)

| Token_Name | Token_Type | AGS_Value |
|---|---|---|
| color.background_light | color | Soft Sandstone #F5F5F5 (jasne powierzchnie, oddech) |
| color.surface_dark | color | Cosmic Navy #1A1A2E (dominujace ciemne powierzchnie, premium) |
| color.accent | color | Electric Cyan #00E0FF (MAX 1-2 male akcenty na kompozycje, nigdy wypelnienie) |
| color.premium | color | Muted Gold #D4AF37 (akcent premium: linia, slowo, pieczec) |
| color.negative | color | Subtle Red #C73E3A (WYLACZNIE oznaczenia 'zle/nie rob') |
| color.proportion | color | Navy + Sandstone = ~80% kazdej kompozycji; zero kolorow spoza palety |
| font.headline | font | Playfair Display Bold/SemiBold (naglowki, cytaty); na okladkach ze zdjeciem: DM Sans/Inter Bold |
| font.body | font | DM Sans 400/500 (tekst ciagly, opisy) |
| font.ui | font | Inter 400/600 (UI, guziki, male teksty) |
| font.mono | font | JetBrains Mono (kod, techniczne etykiety, chipy kategorii) |
| motyw.circuit | motyw | Cienka sciezka obwodu drukowanego ze zlotym pinem koncowym; tlo/most sekcji, opacity 5-10%, wlasna strefa, NIGDY nie nachodzi na tekst |
| motyw.monogram | motyw | Monogram G jako duzy watermark (60-70% wysokosci) w prawym dolnym rogu, opacity 5-15%, caly w kadrze, clear space 2-5% |
| spacing.logo | spacing | Clear space logo/monogramu = 4-5% wymiaru kadru z kazdej strony |
| zakaz.gradients | zakaz | Zero gradientow miedzy kolorami palety; zero teczowych/wielobarwnych tel |
| zakaz.stock | zakaz | Zero stock-photo look, zero AI-twarzy i AI-dloni |
| zakaz.cyber | zakaz | Zero palety cyber blue-purple-pink ('kolejna firma AI') |
| zakaz.clutter | zakaz | Zero emoji-clutter, zero infantylnych odrecznych ilustracji |

## 4. Wiersze TNM - baza kolorow z SOP, HEXY DO UZUPELNIENIA przez Ciebie

Kanon SOP dual-brand: **ciepla zielen (forest) + terakota (sienna) + krem**. Dokladne hexy
wyciagnij z zrodla prawdy, ktore prowadzisz (Claude Design / CSS landing tyniemusisz.pl -
klasy tnm-box-sienna, tnm-separator gradient forest->sienna) i wpisz w TNM_Value:

| Token_Name | Token_Type | TNM_Value (uzupelnij hex) |
|---|---|---|
| color.primary | color | ciepla zielen (forest) #______ dominujaca |
| color.accent | color | terakota (sienna) #______ akcenty, boxy kluczowe |
| color.background | color | krem #______ tla, oddech |
| font.headline | font | (z Claude Design - naglowki TNM) |
| font.body | font | (z Claude Design - tekst TNM) |
| motyw.separator | motyw | Tri-color separator: pasek gradientu forest -> sienna -> forest miedzy sekcjami zmieniajacymi tlo |
| motyw.box | motyw | Sienna left-border box TYLKO dla kluczowych mysli (rzadko = wazne) |
| zakaz.corporate | zakaz | Zero cyber-tech look, zero gradientow poza separatorem, zero stock-photo, zero AI-twarzy |

Zakazy wspolne (mozesz skopiowac z AGS_Value do TNM_Value): stock, AI-twarze, emoji-clutter.

## 5. Po wypelnieniu - JEDYNY krok Tomasza

Przekaz Tomaszowi **database_id** (32-znakowy identyfikator z URL bazy, fragment miedzy
ostatnim '/' a '?v='). Tomasz wysyla botowi @ags_social_bot jedna wiadomosc:

    /set brand_tokens_notion_db <database_id>

## 6. Weryfikacja (BE zrobi sam)

Do 10 minut od /set system zaciagnie tokeny (log '[brand_tokens] sync z Notion: {AGS: N, TNM: M}').
Dowod dla Ciebie: /brand_config AGS w bocie pokaze '✅ tokeny wizualne: N', a nastepna grafika
(🎨 Generuj) dostanie prompt z dokladnymi hexami. Kazda pozniejsza zmiana w Notion = sama
propaguje sie w <=10 min, zero deployu.
