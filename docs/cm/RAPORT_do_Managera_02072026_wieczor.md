# RAPORT do Managera AGS - 02/07/2026 wieczór (Build Engineer)

## TL;DR
Kanoniczna sekwencja: **krok 1 i krok 2 DOMKNIĘTE z dowodami**. Subagent X przeszedł E2E pod CM (realny tweet + callback). Subagent LinkedIn zbudowany od zera i LIVE (2 realne posty na profilu osobistym). Dwukanałowe E2E: jeden temat -> jeden approve -> równoległa publikacja X + LinkedIn (callbacki 2 s od siebie). Po drodze: krytyczny fix SDK w CM, pełna rotacja wyeksponowanych kluczy X, de-hardkod Schedulera. CM pozostaje SZKIELETEM (~10%) - nie raportować jako produkt.

## 1. E2E subagenta X (krok 1) - PASSED
- Item dc98c4ec: /request 202 -> Sonnet 5 + Haiku -> Telegram approve -> delegacja webhook -> tweet 2072558034060976411 -> callback (post_queue published + agent_messages RESPONSE od x-agent, przeczytany przez CM).
- **Root cause wcześniejszej blokady:** cm-agent miał pin `anthropic==0.42.0` (SDK bez parametru `thinking` -> TypeError -> busy-crash-loop, itemy wisiały w `planned`). Fix: `anthropic>=0.92` + fallback `rates_for_model` (commit 1ac385c). Lekcja systemowa: przy dodawaniu parametru API sprawdzać pin SDK KONKRETNEGO workera.

## 2. SECURITY - rotacja kluczy X + de-hardkod (zamknięte)
- Scheduler x1jJEbcWAe3FnpCa: nowy węzeł Get Keys (klucze X + telegram_bot_token z app_secrets), zero sekretów w definicji workflow (backup zachowany).
- Klucze OAuth 1.0 zregenerowane w portalu X (consumer + access; Bearer/OAuth2 nietknięte). Stare (wyeksponowane) = martwe. Weryfikacja: podpisany GET /2/users/me = 200 @tomasz_ags. Jedno źródło kluczy = app_secrets.
- Poza zakresem: rotacja tokena Telegram (hardkod usunięty, token ten sam - wymaga podmiany credentiala w HITL).

## 3. Subagent LinkedIn (krok 2) - LIVE
- Workflow `Subagent LinkedIn Publisher` (Uv9TvUMI8MRSqCLz) na kontrakcie konektora; **generyczny per cel** (secret_prefix) zgodnie z regułą Tomasza: subagent per KONTO (profil osobisty EN, strony TNM PL / AGS EN / RDC PL - każda z własnym toggle).
- Token: portalowy Token Generator (ścieżka z oficjalnej dokumentacji), `linkedin_access_token` + `linkedin_author_urn` w app_secrets; wygasa ~01/09/2026. Workflow OAuth callback zbudowany na przyszłość (wymaga poprawnego client_secret).
- Debug wg reguły "docs-first" (nowa TWARDA reguła od Tomasza: zero zgadywania, najpierw dokumentacja): n8n Code node nie pozwala na require('querystring'); 403 [/author] = obcięty URN w DB (9 znaków) - naprawione jednym UPDATE.
- Dowody: post testowy urn:li:share:7478539357377904641 + post E2E urn:li:share:7478540226701881345.

## 4. Dwukanałowe E2E (item 66c6357e) - PASSED
Jeden master_theme -> tekst-matka + 2 warianty -> jeden approve na Telegramie -> X (tweet 2072774532780167344, cb 20:08:53) + LinkedIn (cb 20:08:55) równolegle, oba published w post_queue, oba callbacki w agent_messages.

## 5. Nowe reguły od Tomasza (zapisane w pamięci)
- **Docs-first, zero zgadywania** - każda nieudana próba kosztuje realne pieniądze; przed integracją czytać oficjalną dokumentację (lub zlecić Researcherowi), dopytywać zamiast zakładać.
- **Granulacja subagentów per KONTO/CEL** (nie per platforma) z toggle - "bardzo, bardzo ważne".
- **Docelowa obsługa contentu tylko z Telegrama** (potem aplikacja/Slack) - ręczne triggery przeze mnie to tryb przejściowy.

## 6. Mózg CM (krok 3) - AKTUALIZACJA z końcówki sesji: PROJEKT GOTOWY I ZATWIERDZONY
Sesja poszła dalej niż zakładał ten raport:
- Tomasz wykonał RĘCZNIE głębokie researche (Gemini Deep Research + Manus na kontach premium, wg briefu `RESEARCH_BRIEF_TelegramMultiAgent_02072026.md`); wyniki w `docs/research/` - obie analizy ZBIEŻNE i potwierdzają nasz wzorzec (kolejka w PostgreSQL + workery; aiogram 3.x przy gatewayu; FSM w PG; dedup update_id; split 4096; ForceReply+/cancel+TTL).
- Architektura mózgu zaprojektowana i ZATWIERDZONA: `CM_BRAIN_DESIGN_v1.md` - 4 fazy (rozmowa+kolejka z jednym approve -> proaktywny planer -> pierwszy komentarz + język per cel -> media).
- Decyzje domknięte: D1 logi na istniejącego bota #2; D2 model jednego approve (plan hurtem, materiał jednym tapnięciem, publikacja automatycznie w slocie); D3 implementacja Fazy 1 od następnej sesji (resume `RESUME_MASTERPROMPT_03072026.md` sekcja 6 = dokładna lista budowy).
- Nowa reguła wykonawcza od Tomasza utrwalona: badania mogą być robione ręcznie na jego kontach premium - moja rola = kompletne prompty + instrukcje krok po kroku + format wyników czytelny dla agenta.

## Otwarte / do pilnowania
- Token LinkedIn: odnowienie ~01/09/2026 (Token Generator, 2 min).
- linkedin_client_secret w DB błędny (nieużywany; naprawić przy okazji, odblokuje re-auth linkiem).
- Kosmetyka HITL: tekst potwierdzenia po approve nie odzwierciedla delegacji webhook.
- App 2 (CMA, strony firmowe) - czekamy na review LinkedIn.
- Cost-reconcile DR/Manus/Anthropic vs realne rachunki (Tomasz przygotuje zrzuty).
