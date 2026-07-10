# Synteza researchu: modele grafiki/wideo dla Agenta Wizualnego (10/07/2026)

Zrodla: 3 deep researche zlecone przez Tomasza (ChatGPT DR = wideo, Gemini DR = obraz,
Manus 1.6 = spojnosc brandu; brand_consistency_report.pdf = duplikat raportu Manusa, zero
nowych danych). Pliki zrodlowe: C:\Claude-CoWork\AGS\RESEARCH_VISUAL_AGENT_*.md + PDF.
UWAGA metodyczna: obraz i wideo NIE maja krzyzowej weryfikacji (po jednym rankingu kazdy);
czesc cen [GEM] z resellerow (EvoLink/EmpirioLabs), nie z oficjalnych docs - weryfikacja
docs-first przed hardcode w adapterze kosztow.

## Najwazniejszy wniosek (zgodny we WSZYSTKICH zrodlach)

**Typografia = kod, dyfuzja = tlo/ilustracja.** Hex w prompcie nie dziala (Manus, badanie
ΔE2000: prompt = blad 11.25 widoczny golym okiem; swatch referencyjny = 0.90 niedostrzegalny;
poprawa 11x). Zaden model wideo nie obiecuje typografii - tekst nakladac serwerowo (FFmpeg/
Remotion) na clean plate. Wyjatki z natywna kontrola hex w obrazie: TYLKO Ideogram (16 hexow
w JSON) i Recraft (hex w API + natywny SVG).

## OBRAZ - top wg [GEM] (jedyny ranking obrazu)

1. **Ideogram 4.0**: typografia 0.97 OCR (najlepsza na rynku), natywny lock do 16 hexow,
   $0.03-0.10/obraz, custom training na 20-100 zdjeciach (w tym twarz) $40 jednorazowo,
   kompozycja deklarowana wspolrzednymi. IDEALNE dopasowanie do naszych potrzeb
   (naglowek litera w litere + paleta AGS).
2. **Recraft V4/V4.1**: NATYWNY SVG z API ($0.08) - podmiana hexow w XML na serwerze =
   deterministyczny brand bez budowania wlasnego renderera; Style Lock z 5-10 referencji;
   raster $0.04.
3. **Flux 2 Flex** (BFL): typografia drobnego tekstu, do 10 obrazow referencyjnych,
   ~$0.039, endpoint EU (api.eu.bfl.ai, RODO), otwarte wagi = self-host przy skali,
   baza do LoRA na fal.ai ($2/trening).

gpt-image-2 (nasz obecny): $0.165 High, tekst >95%, ALE brak kontroli hex + restrykcyjne
filtry deepfake na twarze + gpt-image-1 sunset 1.12.2026. Zostaje jako fallback ilustracyjny.
Midjourney: DYSKWALIFIKACJA (brak oficjalnego API, wrappery lamia ToS).
Canva Connect API autofill: technicznie mozliwe, ale Enterprise-only (~$1000+/mies) i autofill
tylko tekst+obraz - NIE dla solo-operatora. Middle path: Templated.io $29/mies / Layerre $9.99.

## WIDEO - top wg [GPT] (jedyny ranking wideo)

1. **Runway gen4.5/turbo**: najdojrzalsze API, $0.05-0.12/s, prawa komercyjne jasne.
2. **Veo 3.1**: najwyzsza jakosc, $0.10-0.40/s, niuanse (us-central1, konflikt docs audio).
3. **Wan 2.7** (Alibaba): najlepszy format-fit (2-15s, wszystkie ratio), $0.10-0.15/s,
   twarze wspierane (r2v/s2v).
Rezerwowy: **MiniMax Hailuo 2.3** - najlepszy koszt (~$0.032-0.082/s efektywnie) + JEDYNY
z jawnie dokumentowanym subject_reference ze zdjecia twarzy.
SPRZECZNOSCI cen do weryfikacji: Kling ($0.112/s [GPT] vs $0.075/s [MANUS]), Seedance
("macierz nieczytelna, CN-only" [GPT] vs "$0.0247/s najtanszy" [MANUS]).
Sora 2: NIE WDRAZAC (API sunset 24.09.2026).

## Twarz zalozyciela

Konsensus: **face LoRA trenowana raz** (Astria ~$1.50 trening + $0.10/output; wlasna twarz =
ToS czyste) > IP-Adapter/InstantID (dryf) > face swap (uncanny). W wideo: Hailuo
subject_reference / Wan r2v. gpt-image moze blokowac nawet wlasna twarz (filtry deepfake).
COMPLIANCE: EU AI Act - oznaczanie tresci AI machine-readable od sierpnia 2026 (backlog!).
WYMAGANIE WSTEPNE: baza zdjec referencyjnych (brand_assets) - wciaz pusta.

## LoRA stylu dla solo-operatora

WARTO: fal.ai FLUX LoRA $2/trening, 10-20 obrazow, inference $0.01-0.05; prog oplacalnosci
50+ ilustracji/mies. Alternatywy: Ideogram training $40, Stability Brand Studio $50/mies.

## Koszty przy ~100 grafik + 10 wideo/mies

Hybryda wg Manusa: $50-80/mies. Czysta dyfuzja obrazu: $3 (Ideogram Turbo) do $16.50
(gpt-image High) - koszt obrazu POMIJALNY, decyduja typografia/hex/referencje. Wideo:
$3.20 (Hailuo) do $40 (Veo standard) - tu wybor ma znaczenie budzetowe.

## REKOMENDACJA MANAGERA (selekcja adapterow startowych)

Sekwencja "build each layer when you need it" (Manus) nalozona na nasza spec
(SPEC_VISUAL_AGENT_10072026.md):

1. **Adapter IDEOGRAM** (grafiki typograficzne/diagramy = 90% naszych potrzeb): natywny hex
   lock + najlepsza typografia + tanio. Pierwszy do budowy; moze wejsc do tymczasowego
   organu CM od razu (wymiana silnika, kontrakt bez zmian).
2. **Adapter RECRAFT (SVG)**: pokrywa role planowanego svg_engine BEZ budowy renderera -
   SVG z API, hexy podmieniane w XML na serwerze. Drugi.
3. **gpt_image zostaje** jako fallback ilustracyjny (juz wdrozony); docelowo ilustracje =
   **style LoRA na fal.ai** ($2) po zebraniu 10-20 wzorcowych grafik.
4. **Twarz**: face LoRA (Astria) - BLOKADA: najpierw zdjecia referencyjne do brand_assets.
5. **Wideo NA KONCU** (zgodnie z sekwencja Manusa): start od Hailuo (koszt+twarz) albo
   Runway (niezawodnosc) - decyzja po weryfikacji docs-first cen Kling/Seedance.

Przed implementacja kazdego adaptera: weryfikacja oficjalnego cennika i API w docs dostawcy
(czesc liczb z resellerow) - AP/doktryna docs-first.
