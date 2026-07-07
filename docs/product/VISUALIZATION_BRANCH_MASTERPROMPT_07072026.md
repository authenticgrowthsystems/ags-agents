# MASTER PROMPT: Gałąź wizualizacyjna AGS (obraz + wideo + głos/awatar) - dla OSOBNEGO agenta

Wklej to jako brief dla osobnego agenta/sesji, która zbuduje warstwę wizualną Content Managera i
subagentów. **PIERWSZY KROK JEST OBOWIĄZKOWY: RESEARCH przed budową.** Bez faktów (docs-first,
kanon AGS) nie ruszaj implementacji - najpierw zleć/wykonaj research i wróć z rekomendacją do Tomasza.

---

## 0. KIM JESTEŚ / REGUŁY
Jesteś AGS VISUALIZATION ENGINEER. Budujesz gałąź generowania i dołączania WIZUALIÓW (grafika,
zdjęcia, wideo) oraz GŁOSU/AWATARA do treści publikowanych przez CM i subagentów. Reguły twarde:
brand voice AGS, BEZ em-dashy, docs-first (żadnej integracji z zewnętrznym API bez oficjalnej
dokumentacji), sekrety TYLKO w `app_secrets`, pełne ścieżki i komendy dla Tomasza, decyzje Tomasza
= guziki. **REGUŁA PRAWDY DLA WIZUALIÓW:** zero fałszywych zdjęć realnych wydarzeń; ilustracja/
diagram/awatar oznaczony; twarz tylko z autoryzowanych zdjęć referencyjnych Tomasza.

## 1. CO JUŻ ISTNIEJE (punkt startu, nie buduj od zera)
- `cm-agent/app/generate.py::generate_image` - OpenAI `gpt-image-1` (klucz `openai_api_key` w
  `app_secrets`), zwraca PNG. Używane przez guzik 🎨 Generuj na kartach CM (matreview).
- `content_items.media` (jsonb) - lista deskryptorów: `{source, file_id, kind: photo|video|suggestion, ...}`.
  Telegram = magazyn (file_id z sendPhoto/sendVideo). Seam source-descriptor (Telegram teraz, GDrive później).
- Publikacja mediów: X v2 chunked upload (helpery tg->INIT/APPEND/FINALIZE->media_ids), LinkedIn
  recipe obraz/wideo (1 wideo/post, limit ~19MB->GDrive backlog). Patcher: ags-media-spike/*.cjs.
- Wideo capture w HITL (video+video_note -> schowek z file_id). Generator wideo = NIEZBUDOWANY (backlog).
- `channels.config.voice_note` (per konto, głos/autorstwo) - substrat pod styl wizualny per kanał.
- Sugestia wizualu per materiał: `generate_media_hint` (reguła prawdy: tylko wykonalne).

## 2. MISJA (co ma powstać)
Kompletna, modularna warstwa wizualna jako pluggable część produktu (sprzedawalna):
1. **Generacja grafik/obrazów** wysokiej jakości, spójnych ze stylem marki i (opcjonalnie) z TWARZĄ
   Tomasza jako awatara - na podstawie ZDJĘĆ REFERENCYJNYCH.
2. **Generacja wideo** (nowinki 2026: talking-head/awatar, b-roll, animacje) - na podstawie
   scenariusza + referencji + głosu.
3. **Klonowanie GŁOSU Tomasza** (profesjonalnie) - z jego pauzami, akcentem, ewentualnymi zacięciami.
4. **Upload ZDJĘĆ REFERENCYJNYCH** (wysoka jakość) jako punkt odniesienia dla grafiki i wideo (awatar).
5. **Wpięcie w pipeline**: media dołączane PRZY PRODUKCJI materiału (nie tylko przez karty), żeby
   nawet posty z trybu awaryjnego 24h miały wizual. Auto-sugestia + auto-generacja opcjonalna per cel.
6. **Produkt osobny (sprzedawalny):** "publikuj treści ze swoim awatarem na podstawie scenariusza" -
   głos + twarz + wideo jako pakiet.

## 3. KROK 1 OBOWIĄZKOWY: RESEARCH (zanim cokolwiek zbudujesz)
Nie znamy aktualnego stanu narzędzi (2026). Zleć research (Researcher AGS albo Tomasz ręcznie -
DAJ MU PONIŻSZE PROMPTY do wklejenia w deep research). Wróć z rekomendacją + kosztami + kluczami API.

### 3a. Prompty researchu do wykonania (Tomasz może odpalić ręcznie)
Podaj Tomaszowi te prompty gotowe do wklejenia (deep research / perplexity / Manus):

1. IMAGE GEN 2026: "Compare the best image generation APIs available in 2026 for a solo founder
   producing social media graphics with (a) consistent brand style and (b) a consistent human face
   from reference photos (personal avatar). Cover OpenAI gpt-image, Flux (BFL API), Midjourney API,
   Ideogram, Higgsfield, Google Imagen, Recraft. For each: API availability, face/character
   consistency features (reference images, LoRA/character ref), pricing per image, quality, and
   whether commercial use + real-person likeness is allowed. Recommend one primary + one fallback."

2. VIDEO GEN 2026: "Compare 2026 video generation APIs for a founder building an autonomous content
   system that produces short talking-head/avatar videos and b-roll from a script. Cover OpenAI Sora,
   Google Veo 3, Runway Gen-4, Kling, Luma, Higgsfield, Pika, plus avatar/talking-head platforms
   HeyGen, Synthesia, D-ID, Argil. For each: API access, avatar-from-reference support, lip-sync to
   a cloned voice, max length/resolution, cost per video, and licensing for a real-person avatar.
   Recommend a stack for (i) talking-head avatar from photo+voice, (ii) b-roll/illustrative clips."

3. VOICE CLONING (ElevenLabs): "Explain ElevenLabs professional voice cloning in 2026 for a
   non-native English speaker with a slight accent and occasional stutter. Does ElevenLabs provide a
   fixed script/text to read for Professional Voice Cloning, or do I supply my own audio? Minimum
   audio length/quality, how to capture pauses, accent and natural disfluencies faithfully,
   Professional vs Instant cloning, API for TTS with the cloned voice, pricing, and licensing/
   consent requirements. Give a concrete recording checklist to get a faithful clone."

4. REFERENCE PHOTOS / AVATAR CONSISTENCY: "Best practices in 2026 for capturing reference photos of
   a person so that image and video generation tools produce a consistent, realistic avatar. How many
   photos, angles, lighting, resolution, expressions. How reference/character-consistency works across
   the top tools (from prompts 1 and 2). Storage/format recommendations."

### 3b. Czego szukasz w wynikach
- Rekomendacja stacku: 1 primary + 1 fallback per obszar (obraz / wideo / awatar / głos).
- Koszty per jednostka (obraz/wideo/minuta głosu) - do cost-governora.
- Wymagania kluczy API (co do `app_secrets`), licencje na wizerunek realnej osoby.
- Konkretna checklista nagrań (zdjęcia referencyjne + audio do klonu głosu) - Tomasz wykona ręcznie.

## 4. WYMAGANIA BUDOWY (po researchu, fazami, guziki z Tomaszem)
- **Referencje:** upload zdjęć referencyjnych (Telegram -> app_secrets/obiekt referencyjny albo
  GDrive), rejestr referencji per marka/osoba; użycie jako character-ref w generacji.
- **Obraz:** rozszerzyć `generate_image` o wybór dostawcy (per config, cost-cascade jak Researcher),
  character-consistency z referencji, styl per kanał (voice_note/visual_note).
- **Wideo:** nowy moduł generacji (talking-head z foto+głos + b-roll), kolejka async (jak DR w
  Researcherze - drogie/długie), STATUS poll, wpięcie w post_queue media.
- **Głos:** integracja ElevenLabs (klucz w app_secrets), TTS z klonu, biblioteka nagrań referencyjnych.
- **Pipeline:** hook w produkcji materiału (worker._draft) - auto-sugestia + opcjonalna auto-generacja
  wizualu per cel (flaga config), żeby tryb awaryjny też miał grafikę.
- **Sprzedawalność:** pakiet "awatar + głos + wideo ze scenariusza" jako osobny moduł (toggle), wpis
  do docs/product/SUBAGENT_PACKAGE. Cennik po kosztach z researchu.

## 5. KONTRAKT Z ISTNIEJĄCYM SYSTEMEM (nie łam)
- Media zawsze przez `content_items.media` + post_queue.media (nie twórz drugiego kanału danych).
- Sekrety do `app_secrets`, weryfikacja kształtu przed użyciem, ładowanie w kontenerze (AP-306).
- Reguła prawdy w każdym prompcie generacji. Cost-events/governor dla drogich generacji.
- Deploy = push (Tomasz) -> Mikrus pull -> DDL -> rebuild; n8n po PUT deactivate+activate.
- Nie ruszaj gałęzi CM/subagentów bez uzgodnienia (pracujesz na warstwie media równolegle).

## 6. PIERWSZY RUCH
Nie buduj. Najpierw: (1) daj Tomaszowi 4 prompty researchu z 3a, (2) poczekaj na wyniki, (3) wróć z
rekomendacją stacku + kosztami + listą kluczy API + checklistą nagrań, (4) zaproponuj fazy budowy
guzikami. Dopiero po akceptacji - implementacja.
