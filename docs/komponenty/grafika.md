# Komponent: GRAFIKA (prompt graficzny, visual canon, kanon mediow)

**STATUS GOTOWOSCI: AUTO-GENEROWANIE OBRAZOW WYLACZONE (kanon 25/07 - tylko prompty do recznej roboty)** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## KANON 25/07: prompty, nie auto-obrazy (feedback Tomasza POWTORZONY)

Zgloszenie: "materialy graficzne generowane nie sa w sposob zadowalajacy - dopoki nie bedzie
dedykowanego agenta do tych spraw to chce to robic recznie - mam dostawac tylko szczegolowe
prompty." Auto-grafika gpt-image wychodzila slabo (dowod 25/07: "One Key Prevents Double
Charges", "Outside ICP Is Not a Verdict"), a slaba grafika szkodzi marce bardziej niz jej brak.

Co to znaczy w kodzie:
- `worker._auto_generate_image` NIE generuje juz obrazu - dolacza do materialu SZCZEGOLOWY
  PROMPT (`kind='visual_prompt'`, 150-250 slow z kanonu wizualnego). Karta pokazuje go jako
  "📋 SZCZEGOLOWY PROMPT", pelny pod guzikiem 📋 Prompt.
- `channels._ensure_li_graphic` (dispatch) = celowy NO-OP. Post bez dolaczonego pliku idzie
  TEKSTOWO; grafike Tomasz dodaje sam przed zatwierdzeniem, gdy chce.
- Flagi zgaszone: `brand_config.cm_auto_image=false`, `channels.config.auto_image=false`
  (X + LinkedIn) - docs/ops/grafiki_off_25072026.sql. To COFA P4 Managera (auto_image X ON).
- Guzik 🎨 Generuj NA ZADANIE zostaje (swiadome klikniecie to nie automat).
- Zniesienie kanonu: dopiero dedykowany Agent Wizualny (backlog, wstrzymany przez Tomasza).

## Co robi (stan po 25/07)

Pisze SZCZEGOLOWY PROMPT graficzny do materialu (Sonnet z kanonu wizualnego marki) i daje
agentom "wzrok" (opis cudzej grafiki w rozmowie). Obrazu NIE generuje sam - to robi Tomasz
recznie w swoim narzedziu, na podstawie promptu. Guzik 🎨 Generuj (gpt-image-2) zostaje na
wyrazne zadanie.

## Przeplyw

```
canonical gotowy -> generate_media_hint (podpowiedz medium)
  -> hint_wants_generated_graphic? -> generate_image_prompt (Sonnet; kanon
     wizualny + temat + guidance)
  -> media jsonb: kind='visual_prompt' (prompt do RECZNEJ roboty) - ZERO auto-obrazu (25/07)
Wyzwalacze OBRAZU (tylko na zadanie): guzik 🎨 Generuj na karcie,
  narzedzie generate_material_image w rozmowie CM. AUTO-obraz przed karta i przy
  dispatchu = WYLACZONE (kanon 25/07).
Guzik 📋 Prompt: wysyla media[].image_prompt (takze z visual_prompt) do skopiowania
  w generator Tomasza; wynik wraca przez ➕ Media (Telegram file_id)
describe_material_image: agent OGLADA grafike materialu (vision) i rozmawia
  o niej; suggest_comment_from_image: vision na cudzych postach (subagent)
```

## Zrodla kanonu wizualnego (kolejnosc w _visual_canon)

1. `brand_tokens` (SSOT = baza Notion "Brand Config"; puller co 10 min ->
   PG; JSON W3C DTCG wklejany do promptu, "hexy litera w litere").
2. `brand_config` klucz visual_canon (per marka).
3. Fallback w kodzie (AGS destylat; TNM ciepla zielen + terakota + krem).

Obejmuje WSZYSTKICH konsumentow grafiki - kazdy idzie przez
generate_image_prompt.

## Wejscia-wyjscia i tabele

- `content_items.media` / `post_queue.media` (jsonb): descriptory mediow -
  obrazy (Telegram file_id / bytes), image_prompt, review_copy, dup_warning
  (UWAGA: media to WOREK descriptorow roznych typow, nie tylko obrazy).
- `brand_tokens`: brand_id PK, tokens jsonb {nazwa: {type, value}}, source.
- Publikacja z mediami: X media v2 chunked (adapter n8n), LinkedIn obrazy
  dzialaja; Telegram file_id trwaly (limit getFile 20MB).

## Kanon mediow multi-platforma (Tomasz 19/07)

- JEDNA grafika/zdjecie = reuse na wszystkie kanaly materialu (automat).
- Platforma wymagajaca INNEGO medium (np. Instagram = wideo) dostaje JAWNE
  zadanie w karcie: "wygeneruj albo nagraj" - zero wracania po fakcie.
- Warianty formatu per platforma (LI 4:5, X 16:9) = Agent Wizualny
  (ZAMROZONY; spec docs/product/SPEC_VISUAL_AGENT_10072026.md).

## Konfiguracja

- `brand_config`: `cm_auto_image` (on/off auto-grafiki),
  `brand_tokens_notion_db` (id bazy Notion; /set), jakosc obrazu w kodzie
  (`generate._image_quality`).
- `app_secrets`: openai_api_key (gpt-image-2), anthropic (prompt), notion_api_key
  (puller).

## Punkty zaczepienia w kodzie

- `cm-agent/app/generate.py`: `generate_media_hint`,
  `hint_wants_generated_graphic`, `generate_image_prompt`, `generate_image`,
  `_visual_canon`, `describe_published_screenshot`, `inspect_image`,
  `comment_from_image`.
- `cm-agent/app/worker.py`: `_auto_generate_image`, `_auto_image_enabled`.
- `cm-agent/app/matreview.py`: guziki 🎨 / ➕ Media (`media_attach_watch`,
  `_note_attach`) / 📋 Prompt; `_send_media_preview`, `_tg_upload_photo`.
- `cm-agent/app/conversation.py`: `_generate_material_image`,
  `_describe_material_image`, `_attach_last_photo`.
- `cm-agent/app/sync/brand_tokens_pull.py`: `pull_once`, `tick`.

## Kanony ktore go dotycza

- Docs-first: bump gpt-image-1 -> gpt-image-2 zrobiony z dokumentacji, nie
  z pamieci modelu.
- Brand canon: kolory/fonty/zakazy z brand_tokens sa nadrzedne wobec inwencji
  promptu.
- Kanon mediow multi-platforma (sekcja wyzej).

## Regula grafik LinkedIn (23/07, incydent #280 bez grafiki)

- Post LinkedIn bez pliku graficznego dostaje AUTO-generowany obraz przy DISPATCHU
  (channels._ensure_li_graphic: prompt Sonnetem z tresci, gpt-image-2, upload na
  Telegram jako podglad, dopiecie do wiersza kolejki i materialu). Porazka generacji
  nie blokuje publikacji (post idzie tekstowo).
- Karta zatwierdzenia ostrzega "BEZ GRAFIKI (LinkedIn)" gdy material celuje w
  LinkedIn bez pliku - mozna dopiac wlasna 🎨/➕ przed zatwierdzeniem.

## Jezyk napisow na grafice (fix 24/07)

Objaw: material "Klasyfikacja kontaktu przed werdyktem" poszedl na AGS LinkedIn po angielsku,
a plansza wyszla POLSKA (naglowek "Poza ICP to nie werdykt", polskie przyklady w tabeli).
Polska grafika pod angielskim postem lamie separacje marek (AGS mowi po angielsku, polskie
idzie na TNM).

Przyczyna: generator promptu dostawal `master_theme` i tekst-matke (oba po polsku - tak
powstaja materialy), a jezyka publikacji CELU nie widzial wcale. Tlumaczenie postu dzieje sie
pozniej, przy wysylce, wiec grafika zostawala w jezyku surowca.

Fix: `generate.jezyk_grafiki(brand_id, content_item_id)` czyta `channels.config.language_publish`
celu materialu (fallback: AGS = en, pozostale marki = pl) i wstrzykuje do promptu twarde
zdanie: WSZYSTKIE napisy widoczne na grafice (naglowek, etykiety, przyklady w tabelach,
podpisy) MUSZA byc w tym jezyku, niezaleznie od jezyka tematu i tekstu-matki.

**Wybor recznie:** guzik 🎨 Generuj przyjmuje wskazowke wlasciciela, ktora ma PRIORYTET nad
domyslnym jezykiem - wystarczy dopisac "po polsku" albo "po angielsku". Parametr `jezyk=`
w `generate_image_prompt` pozwala wymusic jezyk z kodu (np. przy wariantach per kanal).

## Znane pulapki

- media jsonb niesie TAKZE dup_warning i review_copy - kod czytajacy media
  musi filtrowac po kind, nie zakladac "wszystko to obrazy".
- Notion Connection na bazie Brand Config wymagana RECZNIE (AP-305) - puller
  bez niej milczy (log '[brand_tokens] sync z Notion' w docker logs =
  dziala).
- Galeria mediow tylko na zadanie (mgal) - wysylanie galerii przy kazdej
  karcie bylo floodem (naprawione 19/07).
- Prompt graficzny bez zapisu ginal - dzis ZAWSZE laduje w media[].image_prompt
  (guzik 📋 z niego czyta).
