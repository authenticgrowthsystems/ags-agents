# Komponent: ROZMOWA CM I SUBAGENTOW (route, narzedzia, pamiec 3 warstwy)

**STATUS GOTOWOSCI: CZESCIOWY (komendy configu deterministyczne; poza nimi test prawdy: paragon). Warstwa INTAKE-UX 21/07 (pamiec watku subagenta, menu intencji, HTML) w galezi build/intake-ux - czeka merge + rebuild + tap-testy DoD** (macierz: docs/GOTOWOSC_PRODUKTU.md; aktualizuj przy kazdej zmianie zachowania)

## Co robi

Dwukierunkowa rozmowa Tomasza z agentami na Telegramie (@ags_social_bot).
Jeden czat, wielu agentow: /agents przelacza aktywnego agenta
(active_agent = 'idea' | 'cm' | 'subagent:<brand>:<channel>'). CM = partner
dialogiczny (wlasne zdanie + trafne pytanie, patrzy zanim pyta); subagent =
ten sam KOD co CM (`_subagent_handle`), inna konfiguracja z channels.

## Route wiadomosci (kolejnosc ma znaczenie)

```
Telegram -> n8n HITL (Detect Update Type; przepustka komend /karty /schowek
  /decyzje /brand*) -> POST /message {chat_id, text, update_id, active_agent}
conversation.handle:
  1. dedup update_id (processed_updates)
  2. brands_ui.try_handle (/brands, /brand_on|off|add|remove|config|export -
     deterministyczne, bez LLM)
  3. _config_route: DETERMINISTYCZNE komendy configu PRZED LLM (fix incydentu
     "Zrobione" bez wykonania):
     - _USTAW_OKNO_RE: "ustaw okno [publikacji] dla <brand> <channel> na
       HH:MM-HH:MM" -> _target_update(publish_windows) -> paragon ⚙️
     - _USTAW_KEY_RE: "ustaw <key> dla <brand> <channel> na <value>" - TYLKO
       klucze z allowlisty _CONFIG_KEYS (publish_windows, publish_mode,
       language_publish, posts_per_day, follower_count, thread_enabled,
       voice_note, secret_prefix, emergency_publish); klucz spoza listy na
       ISTNIEJACYM celu = szczera odmowa z lista kluczy
  3b. LACZNIK 22/07 (przed sales.try_command!): '[raport pracy' w tekscie ->
     engagement.apply_work_report (parser bez LLM, potwierdzenie z licznikami);
     /kontekst [x|linkedin|sprzedaz|all] -> reports.send_kontekst (stan gry bez LLM,
     tekst albo plik .md; wymaga przepustki n8n hitl-kontekst-command-22072026.cjs)
  4. _KARTY_RE i inne skroty -> dopiero potem LLM
```

- CM: model z brand_config `cm_tier_conversation` (default Opus), PETLA
  AGENTOWA do 5 krokow (wynik narzedzia wraca do modelu), max_tokens 4000.
- Subagent: Sonnet default, PETLA AGENTOWA jak CM (10/07), max_tokens 2000.
  Jezyk rozmowy: brand_config `language_comm`.
- Zdjecie przy aktywnym CM -> rozmowa CM (pyta o intencje); przy subagencie ->
  KARTA INTENCJI (INTAKE-UX 21/07, nizej); przy Idea Bocie -> triage. Dokumenty
  .md/.txt <=120KB -> `handle_document` -> tresc jako [DOKUMENT: nazwa] do
  rozmowy aktywnego agenta.
- FORMATOWANIE (B4 21/07): kazda wiadomosc agenta idzie przez `_reply` ->
  `_send_rendered`: znaczniki markdownu (`**`, `###`, backticki) konwertowane
  do parse_mode=HTML w TYM JEDNYM miejscu; tekst bez znacznikow idzie plain;
  blad renderowania = fallback plain (wiadomosc zawsze dochodzi).

## Wrzutka zrzutu przy subagencie = MENU INTENCJI (INTAKE-UX 21/07)

Zrzut(y) przy aktywnym subagencie NIE odpalaja od razu propozycji komentarzy.
Trasa: n8n Photo Route -> POST /message 'skomentuj ostatni zrzut' -> regex ->
`_sub_comment_vision(menu=True)`:
1. uzbrojony intake CRM ma pierwszenstwo (zrzut = PROFIL),
2. album media_group_id = jeden kontekst (claim + pauza 4 s),
3. zrzuty osobno <60 s = pytanie 'jeden post czy rozne?' (photo_group),
4. potem `_intent_menu_open`: wizja-klasyfikacja (`_screen_shots`: co widac -
   post/DM/profil + osoby) -> JEDNA karta "CO WIDZE + PROPONUJE" z guzikami
   intencji przez decisions.ask, typ **intent_menu**: [Skomentuj] [Odpowiedz
   na DM] [Poznaj osobe (intake)] [Wszystko po kolei] [Tylko zapisz].
Tap -> `apply_intent_menu`: wykonanie SEKWENCYJNE (komentarze = tor cmt: per
autor; DM = `_dm_reply_run`, ten sam tor gotowca; intake = od razu z zrzutow
gdy widac profil, inaczej arm_intake), KAZDY watek domkniety paragonem
"✅ Watek ... domkniety", po ostatnim "co dalej?". Pojedynczy wybor przy
pozostalych intencjach = nowa karta z POZOSTALYMI opcjami (+ [Nic wiecej]).
WATEK INTENCJI JEST OBIEKTEM W DB (agent_decisions.context: insp_ids,
contact_id, screening, done_keys) - przyszly konektor UI (Slack watki, webapp
lista wiszacych zadan - kierunek produktowy SNAPSHOT) tylko inaczej go
wyswietli. DEDUP (B3): ta sama osoba (match przez contacts) z OTWARTA karta
<24h = doklejka insp_ids do jej kontekstu, zero drugiej karty.
Jawne narzedzie `suggest_comment_from_image` w rozmowie = bez menu, od razu
propozycje (stara sciezka); 'odpowiedz na ten DM' = `subagent_reply_dm`
(siega po ostatnie zrzuty watku, nie prosi o powtorzenie).

## Narzedzia

- CM (22): propose_material, save_to_schowek, show_archive,
  find_similar_published, adapt_published, plan_build, plan_approve, plan_edit,
  target_create, target_update, escalate_decision, attach_last_photo,
  show_review_cards, add_style_rule, reschedule_material, replace_material,
  describe_material_image, generate_material_image, view_last_screenshot,
  hold_todays_queue (STOP przed doprecyzowaniem), sunday_world_brief,
  log_external_publication ([ZEWN]).
- Subagent (11): subagent_show_post, subagent_edit_post (edycja=akceptacja,
  PL->EN), subagent_remove_post, subagent_reschedule_post,
  subagent_set_metrics, propose_material (tylko wlasny kanal), escalate_to_cm,
  suggest_comment, suggest_comment_from_image, subagent_reply_dm (odpowiedz
  na DM z ostatnich zrzutow, 21/07), subagent_remember_rule.
- Komentarze: guziki cmt:* -> `handle_cmt`. Od buildu 20/07 (W BUDOWIE, czeka wdrozenie):
  propozycja per AUTOR z wlasnymi guzikami cmt:ok|angle|no, CRM obowiazkowy (contacts),
  intake nieznanych (cmt:intake|stub), przypomnienia 24h, album = 1 post - szczegoly:
  [engagement-crm.md](engagement-crm.md).

## Pamiec (3 warstwy)

1. Historia rozmowy: `user_agent_state.fsm_data.histories[agent]` - OSOBNY
   watek per agent, 16 tur, TTL 30 min (stan nie gnije). B1 INTAKE-UX (21/07):
   trasy DETERMINISTYCZNE subagenta (kolejka/raport/co wisi/wrzutki zrzutow/
   karty intencji/guziki intent_menu) tez zapisuja wymiane przez `_sub_record`
   - wczesniej odpowiadaly z pominieciem historii i subagent 3 wiadomosci
   pozniej "nie mial kontekstu" do wlasnego streszczenia DM (sesja 21/07).
   System prompt subagenta kaze SPRAWDZIC historie zanim poprosi o powtorzenie.
2. Skrot przy wygasaniu: `memory_tick` zapisuje podsumowanie watku
   (agent_logs CONVERSATION_SUMMARY) i wstrzykuje ostatnie skroty do kontekstu
   ("pamietasz o czym wczoraj" dziala).
3. Trwale (nigdy nie wygasa): channels.config.rules (subagent_remember_rule,
   max 20), reguly stylu (add_style_rule + style_learned), engagement_log
   (ostatnie 5 interakcji), content_memory/pgvector (archiwum semantyczne),
   inspirations (schowek), agent_messages (ustalenia z CM), agent_logs.
   Kontekst wstrzykiwany swiezo: kolejka, plan, cele, Voice Bible (cache).

## Punkty zaczepienia w kodzie

- `cm-agent/app/conversation.py`: `handle` (glowny route), `_config_route`,
  `_cm_tools`/`_dispatch_tool`, `_subagent_handle`/`_sub_dispatch_tool`,
  `handle_document`, `handle_cmt`, `memory_tick`, `_load_history`.
- `cm-agent/app/worker.py`: `POST /message`, `/docmsg`, `/cmt`, `/wake`.
- `cm-agent/app/brands_ui.py`: `try_handle` (komendy /brand*).
- `cm-agent/app/tasks.py`: `tier_for`/`model_for` (dobor modelu per task,
  brand_config cm_tier_<task_type>) + ledger cm_tasks.

## Kanony ktore go dotycza

- CM = partner dialogiczny (07/07 + 12/07): patrzy zanim pyta
  (view_last_screenshot), STOP przed doprecyzowaniem (hold_todays_queue),
  dedup proponuje PODMIANE.
- TEST PRAWDY: zmiana stanu bez paragonu z narzedzia (⚙️ przy configu) =
  NIEWYKONANA. Dlatego komendy configu ida deterministycznie przed LLM.
- Paragon kazdej decyzji nowa wiadomoscia; jeden atomowy krok.

## Znane pulapki

- Klasa incydentow "Zrobione"/"Zapisane" bez wywolania narzedzia (19-20/07):
  LLM potrafi zameldowac wykonanie bez wykonania - kazda nowa komenda zmiany
  stanu powinna dostac deterministyczny route albo twardy paragon.
- TTL 30 min czysci LUZNY watek - co ma przetrwac, musi trafic do warstwy
  trwalej (schowek, zasady, reguly).
- active_agent wartosci to 'idea'/'cm'/'subagent:<brand>:<channel>' - nie
  zgadywac innych (blad briefu #88).
- Karta intencji dodaje 1 wywolanie wizji (screening) per wrzutka - to celowy
  koszt za trafna akcje zamiast floodu; typ 'intent_menu' moze z czasem przejsc
  semi-auto przez petle nauki decisions (NIE dotyczy tresci).
- _md_to_html konwertuje TYLKO gdy tekst ma znaczniki - czyste wklejki
  (gotowce) ida przez _tg bez parse_mode i zostaja doslowne.
- fix 21/07: galaz 'Inny kat' (cmt:angle) nie importowala TRUTH_GUARD - kazde
  tapniecie padalo NameError polykanym przez except; naprawione.
