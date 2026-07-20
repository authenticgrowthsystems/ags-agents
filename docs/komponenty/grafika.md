# Komponent: GRAFIKA (generacja obrazow, visual canon, kanon mediow)

## Co robi

Generuje grafiki do materialow i daje agentom "wzrok": prompt graficzny pisze
Sonnet z kanonu wizualnego marki, obraz robi gpt-image-2 (quality high),
agent potrafi OPISAC wygenerowana grafike w rozmowie. Wynik laduje w media
jsonb materialu i idzie z publikacja (reuse na wszystkie kanaly).

## Przeplyw

```
canonical gotowy -> generate_media_hint (podpowiedz medium)
  -> hint_wants_generated_graphic? -> generate_image_prompt (Sonnet; kanon
     wizualny + temat + guidance) -> generate_image (gpt-image-2, high)
  -> media jsonb: obraz + media[].image_prompt (prompt ZAPAMIETANY)
Wyzwalacze: auto-grafika przed karta (brand_config cm_auto_image),
  guzik 🎨 Generuj na karcie, narzedzie generate_material_image w rozmowie CM
Guzik 📋 Prompt: wysyla media[].image_prompt do skopiowania w ZEWNETRZNY
  generator; wynik wraca przez ➕ Media (Telegram file_id)
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
