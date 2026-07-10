# SPEC: Agent Wizualny (grafika + wideo) v0 - wymagania Tomasza 10/07/2026

Zrodlo: decyzja Tomasza 10/07 (ODRZUCONA budowa silnika SVG w cm-agent - "do grafiki i filmow
ma byc oddzielny agent"). Ten dokument zastepuje luzna wizje T6 konkretnymi wymaganiami;
VISUALIZATION_BRANCH_MASTERPROMPT_07072026.md pozostaje masterpromptem badawczym.

## 1. Wymagania twarde (slowa Tomasza, 10/07)

1. **Oddzielny agent** do tworzenia grafik i filmow wideo - nie organ CM, nie funkcja subagenta
   kanalowego. Sprzedawalny obiekt jak kazdy subagent (kanon object+toggle).
2. **Przygotowuje media dla INNYCH agentow i subagentow** - CM i subagenci kanalowi zamawiaja
   u niego grafike/wideo do materialow w kolejce (agent->agent, bez Tomasza w petli zamowienia).
3. **Realizuje prosby Tomasza POZA kolejka** - "bede chcial opublikowac tresc z pominieciem
   subagentow i potrzebuje grafiki". Bezposrednia rozmowa, wynik do reki.
4. Publikacja reczna poza systemem: Tomasz PO FAKCIE wysyla screena do CM ("opublikowalem to
   i tam") -> CM loguje publikacje zewnetrzna. (Wymaganie na CM, nie na agenta wizualnego -
   osobna pozycja backlogu: intake publikacji zewnetrznej ze zrzutu.)
5. **Multi-model**: gpt-image to tylko jeden z modeli. Takze Seedream/Seedance (ByteDance,
   Tomasz: "Seedens 2.0" - doprecyzowac w researchu) i kolejne. Rozne modele do zdjec,
   grafik i filmow - bedzie ich wiecej, architektura ma to przyjac.
6. **Baza referencyjna marki**: logotypy, jasno okreslony brand (kolory, fonty), zdjecia
   referencyjne dozwolone przy generacji. Bez tego zadna generacja nie jest "w brandzie".

## 2. Architektura proponowana (BE, do zatwierdzenia przed budowa)

Wzorzec = Researcher (sprawdzony): standalone FastAPI na Mikrusie, wlasna kolejka, adaptery
zrodel na jednym kontrakcie, event-driven webhook, koszty w ledgerze.

- **Kolejka**: task_queue task_type='generate_media' (JUZ istnieje w CHECK constraint - dowod
  10/07). Payload: brief, brand_id, format (grafika/zdjecie-styl/wideo), target (content_item_id
  albo 'direct'), guidance.
- **Adaptery modeli** (kontrakt jak zrodla Researchera, pluggable): gpt_image (jest),
  seedream/seedance, svg_engine (typografia/diagramy - deterministyczny brand co do piksela),
  nastepne po researchu. Router brief->model + cost-ledger per generacja.
- **Baza aktywow**: tabela brand_assets (brand_id, kind: logo|font|reference_photo|palette,
  zrodlo file_id/sciezka, metadane, dozwolone_uzycie) + folder zrodlowy
  C:\Claude-CoWork\AGS\brand_assets\ (przewidziany w brand-canon sekcja 3.3, wciaz pusty).
  Kanon wizualny (kolory/fonty/zakazy) = brand_config 'visual_canon' (wdrozone 10/07, fallback
  w kodzie).
- **Interfejsy**: (a) agent->agent: /request webhook + task_queue (kanon async event-driven);
  (b) Tomasz: pozycja w /agents (rozmowa jak z subagentem kanalowym, prosby direct);
  (c) wynik: media descriptor (telegram file_id / GDrive dla >19MB) wpinany do
  content_items.media albo zwracany Tomaszowi wprost.
- **Migracja z CM**: dzisiejsze organy (generate_image_prompt premium, auto-grafika przed karta,
  generate_material_image z rozmowy) zostaja w CM do czasu startu agenta, potem CM DELEGUJE
  (kontrakt dla Tomasza bez zmian - karta dalej przychodzi z grafika).

## 3. Research-first (kanon T6 - przed budowa, nie po)

Deep research (Researcher LIVE, cascade): landscape modeli image/video 2026 - gpt-image,
Seedream/Seedance (ByteDance), Flux, Veo, Kling, Runway; wsparcie obrazow referencyjnych
(twarz/logo/styl marki), spojnosc stylu miedzy generacjami, API + ceny + licencje komercyjne,
co dziala z serwera (Mikrus). Wynik = wybor 2-3 adapterow startowych + kosztorys.

## 4. Potrzebne od Tomasza (przed/w trakcie budowy)

1. **Aktywa do bazy referencyjnej**: logotypy AGS (wordmark + monogram G, wszystkie warianty),
   zdjecia referencyjne (portrety/sylwetka do przyszlej generacji z twarza) -> folder
   C:\Claude-CoWork\AGS\brand_assets\ (albo wyslac botowi, opiszemy i zapiszemy file_id).
2. Decyzja o gradientach w kanonie wizualnym (otwarta z 10/07 rano).
3. Po researchu: wybor modeli startowych + akceptacja kosztorysu.

## 5. Czego NIE robimy

- Nie budujemy silnika SVG w cm-agent (decyzja 10/07) - svg_engine = adapter przyszlego agenta.
- Nie kupujemy/nie integrujemy Canva Connect API bez researchu (brand kitu AGS w Canva nie ma;
  konektor Cowork zostaje do roboty recznej ad-hoc).
- Nie generujemy twarzy Tomasza dopoki nie ma bazy zdjec referencyjnych i sprawdzonego modelu.
