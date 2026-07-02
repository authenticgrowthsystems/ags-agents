# RESEARCH BRIEF: Telegram jako UI sieci agentów AI (mózg CM)
Data: 02/07/2026. Wykonawca: Tomasz ręcznie (Gemini Advanced + Manus na kontach premium). Odbiorca wyników: Build Engineer (Claude) - projekt mózgu CM.

## Po co ten research
Decyzje już podjęte: (a) n8n = tylko transport, logika konwersacji w Pythonie (FastAPI worker per agent); (b) JEDEN bot interaktywny dla wszystkich agentów z przełączaniem kontekstu + drugi bot/kanał czysto logowy; (c) CM = menadżer: dyskusja -> jedno zatwierdzenie -> sam kolejkuje i publikuje. Research ma dostarczyć NAJLEPSZE WZORCE IMPLEMENTACJI zanim napiszemy kod (reguła docs-first).

## Format plików wynikowych (WAŻNE - dla czytelności dla agenta)
- Markdown, nagłówki `##` dokładnie wg pytań badawczych 1-5 poniżej.
- Każde twierdzenie z linkiem źródłowym (URL w nawiasie).
- Fragmenty kodu w blokach ``` z nazwą biblioteki i wersją.
- Na końcu sekcja `## Rekomendacja` : 4 opcje architektury (nazwa, opis, plusy, minusy) + jedna rekomendowana.
- Nazwy plików: `CM_RESEARCH_gemini.md`, `CM_RESEARCH_manus.md`. Zapisz do: `docs/research/` w repo (albo dostarcz w czacie nowej sesji).

---

## PROMPT A - Gemini (tryb Deep Research)
Instrukcja: konto z Gemini Advanced -> nowy czat -> włącz "Deep Research" -> wklej całość poniżej -> po zakończeniu wyeksportuj raport do Markdown.

```
Przeprowadź głęboki research architektury konwersacyjnego bota Telegram, który jest interfejsem dla SIECI agentów AI (multi-agent), dla solo-przedsiębiorcy, docelowo produkt sprzedawany klientom jako modułowy system (klient dokupuje agenta = nowa pozycja w tym samym bocie).

Stack docelowy: Python (FastAPI, osobny worker-serwis per agent) + PostgreSQL (stan rozmów i treści) + n8n wyłącznie jako transport webhooków + Telegram Bot API. Istnieje już produkcyjny bot z dużym handlerem w n8n (206 węzłów) jako jedynym konsumentem webhooka - kierunek migracji: bot = UI, mózg = Python.

Pytania badawcze (odpowiedz w tej strukturze, każde twierdzenie ze źródłem URL):

## 1. Przełączanie kontekstu agentów w JEDNYM bocie
Najlepsze wzorce: komendy (/cm, /manager), menu setMyCommands, inline keyboards, reply keyboards, deep-linking (t.me/bot?start=...), stan rozmowy per czat w bazie. Co jest najprostsze dla NIEtechnicznego użytkownika (test: "moja mama ma sobie poradzić")? Jak robią to produkcyjne boty multi-funkcyjne?

## 2. Dwa boty: interaktywny + logowy
Wzorzec: bot A = rozmowa dwustronna z agentami, bot B = wyłącznie powiadomienia/logi (opublikowano post, raporty). Porównaj z alternatywą: kanał Telegram na logi zamiast drugiego bota. Plusy/minusy, limity API, doświadczenie użytkownika.

## 3. Routing wiadomości do agentów
Webhook bota -> router -> HTTP POST do właściwego serwisu agenta (odpowiedź asynchroniczna 202, agent odpisuje przez sendMessage). Wzorce: kolejkowanie odpowiedzi, długie odpowiedzi (dzielenie wiadomości, limit 4096 znaków), edycja wysłanych wiadomości z guzikami (editMessageText), obsługa timeoutów, deduplikacja update'ów, secret token webhooka.

## 4. Konwersacyjny human-in-the-loop
Zatwierdzanie/odrzucanie/edycja/prośba o inny wariant treści w NATURALNEJ rozmowie (nie tylko inline guziki). Wzorce łączenia guzików z odpowiedziami tekstowymi (ForceReply, reply_to_message), stan oczekiwania na odpowiedź, wychodzenie ze stanu. Przykłady z produkcyjnych botów do zarządzania treścią/social media.

## 5. Biblioteki i gotowe wzorce
aiogram 3.x vs python-telegram-bot v21+ vs czyste HTTP API: porównanie dla przypadku "router + serwisy agentów za HTTP" (długotrwałe operacje, wiele backendów). Wskaż 3-5 open-source'owych botów agentowych/AI na GitHubie wartych skopiowania wzorców (z linkami), szczególnie: multi-context, kolejki, HITL.

## Rekomendacja
4 opcje architektury (nazwa, opis, plusy, minusy, szacunkowa złożoność wdrożenia dla solo operatora 2-4h/dzień) + jedna rekomendowana z uzasadnieniem.

Raport po polsku, źródła mogą być angielskie. Zero marketingowego lania wody, tylko fakty i wzorce z kodem.
```

---

## PROMPT B - Manus
Instrukcja: konto Manus -> nowe zadanie -> wklej całość -> jako deliverable zażądaj pliku Markdown.

```
Task: Research and deliver a Markdown report on production-grade patterns for a single Telegram bot acting as the UI for a NETWORK of AI agents (multi-agent), sellable as a modular product (customer buys a new agent module -> it appears as a new menu context in the SAME bot).

Target stack: Python FastAPI (one worker service per agent) + PostgreSQL (conversation + content state) + Telegram Bot API; n8n used only as webhook transport. An existing production bot has a single 206-node n8n consumer; migration direction: bot = UI, brain = Python.

Deliverable: ONE Markdown file named CM_RESEARCH_manus.md, in Polish (sources may be English), structured EXACTLY as sections 1-5 + Rekomendacja:
1. Agent context switching in ONE bot (commands /cm /manager, setMyCommands menus, inline vs reply keyboards, deep-linking, per-chat state in DB) - simplest UX for a non-technical user ("mom test"), with examples from real multi-function bots.
2. Two-bot pattern: interactive conversation bot + separate logs/notifications bot, versus a Telegram channel for logs - pros/cons, API limits, UX.
3. Message routing: bot webhook -> router -> async HTTP POST to the right agent service (202; agent replies via sendMessage) - queuing, 4096-char message splitting, editMessageText with buttons, timeouts, update dedup, webhook secret token.
4. Conversational human-in-the-loop for content approval (approve/reject/edit/"different angle" in natural conversation, not only inline buttons): ForceReply patterns, awaiting-reply state machines, escaping the state; examples from social-media management bots.
5. Library comparison for this case: aiogram 3.x vs python-telegram-bot v21+ vs raw HTTP API; plus 3-5 open-source AI/agent Telegram bots on GitHub worth stealing patterns from (links, what exactly to steal).
Final section "Rekomendacja": 4 architecture options (name, description, pros, cons, implementation complexity for a solo operator at 2-4h/day) + one recommended with justification.
Every claim must carry a source URL. Code snippets with library name + version. No fluff.
```

---

## LISTA ŹRÓDEŁ - do Firecrawla / ręcznego przejrzenia (uzupełnienie)
Oficjalne (fundament, zawsze aktualne):
1. https://core.telegram.org/bots/api - pełne API (sekcje: sendMessage, editMessageText, setMyCommands, CallbackQuery, ForceReply, setWebhook + secret_token)
2. https://core.telegram.org/bots/features - możliwości botów (menu, komendy, klawiatury, deep linking)
3. https://docs.aiogram.dev - aiogram 3.x (routery, FSM = maszyna stanów rozmowy)
4. https://docs.python-telegram-bot.org - python-telegram-bot (ConversationHandler)
5. https://github.com/python-telegram-bot/python-telegram-bot/wiki - wzorce (Architecture, ConversationHandler patterns)
6. GitHub search: "telegram bot multi agent python", "telegram bot AI assistant FSM" - wyłowić 3-5 żywych repo (gwiazdki, ostatni commit 2025+)

## Co się stanie z wynikami
Nowa sesja BE: wczytuję oba pliki MD + (opcjonalnie) zrzuty Firecrawla, konfrontuję z decyzjami z pamięci, projektuję architekturę mózgu CM (decyzje guzikami), dopiero potem kod.
