# CM BRAIN - projekt architektury v1 (02/07/2026)
Fundament: CM_RESEARCH_gemini.md + CM_RESEARCH_manus.md (zbieżne rekomendacje) + stan LIVE (SYSTEM_DATAFLOW.md sekcja E) + decyzje Tomasza z 02/07.

## 0. Decyzje wejściowe (już podjęte)
- n8n = TYLKO transport; logika konwersacji w Pythonie (cm-agent).
- JEDEN bot interaktywny dla wszystkich agentów (przełączanie kontekstu w menu; klient dokupuje moduł -> nowa pozycja w tym samym bocie) + osobny kanał logowy (bot #2, który Tomasz już ma).
- CM = menadżer: dyskusja o pomysłach/zanadrzu -> JEDNO zatwierdzenie materiału -> CM sam kolejkuje i publikuje we właściwym slocie + pierwszy komentarz pod postem.
- Subagent = obiekt per KONTO/CEL z toggle (profil EN, TNM PL, AGS EN, RDC PL).

## 1. Werdykt z researchu (co przejmujemy)
- **Docelowa architektura = "DB-Queue Distributed"** (Gemini opcja B = Manus opcja 4): router/gateway cienki, stan FSM i kolejki w PostgreSQL, każdy agent osobnym workerem. To jest NASZ ISTNIEJĄCY wzorzec (Researcher/CM już tak działają) - mózg CM go tylko rozszerza, zero rewolucji.
- **Biblioteka (gdy powstanie gateway):** aiogram 3.x; PTB odpada (ConversationHandler nie działa wieloprocesowo, issue #5225).
- **UX nawigacji:** Reply Keyboard jako stała kotwica ("🤖 Zmień agenta", "📋 Plan", "❌ Anuluj") + Inline Keyboard do akcji na materiale; komendy per czat przez setMyCommands(BotCommandScopeChat) - dokupiony moduł = nowa komenda tylko u tego klienta.
- **Konwersacyjny HITL:** stan `awaiting_edit`/`awaiting_angle` w PG; guzik "✏️ Edytuj"/"🔄 Inny kąt" -> ForceReply -> tekst użytkownika trafia do CM jako instrukcja; `/cancel` i słowo "anuluj" wychodzą z KAŻDEGO stanu; TTL 30 min resetuje stan i gasi stare guziki (editMessageReplyMarkup).
- **Higiena transportu:** dedup po update_id (tabela processed_updates), odpowiedzi >4096 dzielone na granicach akapitów, placeholder "⏳..." edytowany wynikiem (editMessageText).
- **Limity:** 1 msg/s per czat, 20/min per grupa/kanał, 30/s globalnie -> logi NIE mogą iść do czatu rozmowy (osobny kanał logowy).

## 2. Architektura docelowa mózgu (rozszerzenie cm-agent)
```
Telegram bot (interaktywny)
  └─ webhook -> n8n HITL (TRANSPORT: guziki cm:/crit:/mtier: zostają; NOWA gałąź:
       tekst + komendy agentowe -> POST cm-agent /message {chat_id, text, message_id, reply_to})
           └─ cm-agent (Python):
                ConversationRouter: user_agent_state (active_agent, fsm_state, fsm_data)
                  ├─ intencje: plan/pokaż/zmień/pomysł/status + swobodna dyskusja (Sonnet 5 + brand voice)
                  ├─ Planner: propozycja planu tygodnia z brand_strategy + channels.config (cadence per cel)
                  ├─ Preview: lista planu/kolejki (content_items + post_queue) w 1 wiadomości
                  └─ odpowiedzi: sendMessage bezpośrednio (token z app_secrets), split 4096
       publikacja: pętla CM claimuje item 'approved' DOPIERO gdy scheduled_for <= now
           └─ dispatch (istniejący kontrakt webhook) -> subagenci X/LinkedIn -> callback
                └─ NOWE: first_comment w payloadzie -> subagent publikuje komentarz po poście
       logi/potwierdzenia -> bot logowy #2 (istniejący, token do app_secrets)
```
Gateway aiogram jako OSOBNY serwis wchodzi dopiero, gdy dojdzie drugi rozmowny agent (Manager) - wtedy HITL-transport oddaje webhook gatewayowi, kontrakt /message się nie zmienia.

## 3. Zmiany w DB (addytywne)
| Tabela | Zmiana | Po co |
|---|---|---|
| `user_agent_state` (NOWA) | chat_id PK, active_agent, fsm_state, fsm_data jsonb, updated_at | stan rozmowy/HITL per czat |
| `processed_updates` (NOWA) | update_id PK, processed_at | dedup webhooków (czyszczenie >24h) |
| `content_items` | +`first_comment` TEXT, +status 'proposed' (pozycja planu przed akceptacją planu) | plan + komentarz zatwierdzany razem z materiałem |
| `channels.config` | konwencja kluczy: `language`, `posts_per_week`, `slots` (np. ["Tue 10:00","Thu 14:00"]), `narrative`, `first_comment` (on/off) | konfiguracja per CEL (profil EN, TNM PL...) |
| `app_secrets` | +`log_bot_token` (bot #2) | kanał logowy |

## 4. Fazy budowy (każda = działająca wartość, testowalna E2E)
**Faza 1 - Rozmowa + kolejka z jednym approve (fundament):**
gałąź transportowa w HITL (tekst -> /message); ConversationRouter w cm-agent; intencje: "pokaż plan/kolejkę", "opublikuj o HH:MM", swobodna dyskusja o pomyśle -> propozycja materiału; approve materiału = koniec klikania (CM czeka ze slotem, publikuje, potwierdza w kanale logowym); dispatch dopiero o scheduled_for.
**Faza 2 - Proaktywny planer:** cron /plan (n8n, już istnieje jako stub) -> CM proponuje plan tygodnia (tematy+cele+sloty z brand_strategy i cadence) jedną wiadomością; akceptacja/korekta w rozmowie; zaakceptowane pozycje -> generacja wyprzedzająca (T-24h) -> pojedyncze approve materiałów.
**Faza 3 - Pierwszy komentarz + język per cel:** first_comment generowany z wariantem (widoczny przy approve); X = reply do tweeta (OAuth1, systemowe); LinkedIn = socialActions (ZWERYFIKOWAĆ docs przed implementacją; fallback = gotowy tekst w powiadomieniu); `language` z channels.config w generate_variant (profil EN, TNM/RDC PL).
**Faza 4 - Media:** zdjęcia do postów (X v2 chunked upload - fakty zweryfikowane w reference_x_media_api_2026; LinkedIn assets API).

## 5. Otwarte decyzje (Tomasz, guziki)
D1: kanał logowy = istniejący bot #2 (rekomendacja) czy prywatny kanał Telegram?
D2: potwierdzenie modelu "jednego approve": plan akceptowany HURTEM w rozmowie (lekko), materiał JEDNYM approve, publikacja automatyczna w slocie - tak?
D3: start implementacji Fazy 1 - następna sesja (rekomendacja: świeży kontekst, ten dokument + research jako wsad) czy natychmiast?

## 6. Wzorce do skopiowania (z researchu, na etapie implementacji)
- telegramify-markdown (bezpieczny split MarkdownV2) - jeśli wyjdziemy poza plain text.
- pavel-molyanov/telegram-ai-agent - "live stream" (edycja jednej wiadomości postępem) + config per wątek.
- langchain-ai/social-media-agent - pełny cykl HITL generuj->zatwierdź->publikuj (wzorzec, nie kod).
- vlymar1/aiogram-bot-template / BushlanovDev/aiogram-fastapi-bot-template - szkielet gatewaya (dopiero przy wydzielaniu gatewaya).
