# SPEC: zdjęcie ma iść do AKTYWNEGO agenta, nie zawsze do Idea Bota (n8n)

Status: **WDROZONE 08/07 (patcher hitl-photo-routing.cjs, HITL 244 wezly, active; backup bk_hitl_photoroute_*).**
Implementacja = spec + 2 korekty docs-first: (1) Save Idea zbiera 4 typy (tekst/glos/foto/wideo) ->
RETURNING +idea_type, gate TYLKO dla 'photo'; (2) tryb ➕ Media (cm_pending_madd swiezy) ma
pierwszenstwo -> ga³az triage (wycisza sie istniejacym guardem), zeby zdjecie do dopiecia nie
wywolywalo auto-komentarza. Wezly: Photo Route Lookup (pg 2.4: active_agent + secret jedna kwerenda),
Photo Route Decide (code 2), Is Photo For Subagent? (if 2.2), Photo To Subagent (http 4.2 -> POST
/message 'skomentuj ostatni zrzut'). CZEKA: tap-test E2E Tomasza (sekcja Kroki pkt 4).
Feedback Tomasza 08/07 23:03: „nie może się idea bot tu włączać" - był w Subagencie X, wysłał zrzut
posta do skomentowania, a Idea Bot go przechwycił (triage „Co z tym zrobić?").

## Workflow: AGS HITL Handler v1.0 (id U5pUZjy2yAhR1sWg, ACTIVE, 240 węzłów)

## Obecny przepływ zdjęcia (bez sprawdzenia active_agent)
`Telegram Trigger -> Route By Update Type (switch) -> [photo] -> Photo GetFile -> Photo Download ->
Prepare Photo Vision -> OpenAI Vision -> Prepare Idea Photo -> Save Idea -> Prepare Triage Reply ->
Telegram Send Triage` (triage: Research/Zapisz/Zrób post/Odrzuć).

Istniejące gate'y do reuse: `Idea Gate Check` (postgres v2.4), `Idea Not Editing?` (if v2.2) - już robią
per-chat lookup (prawdopodobnie tryb edycji). Wzorce typeVersion z tego workflow: postgres 2.4, if 2.2,
switch 3.2, httpRequest 4.2, code 2.

## Zmiana (minimalna, bezpieczna)
Po `Save Idea` (obraz JUŻ w inspirations z metadata.media.file_id - to czyta subagent
suggest_comment_from_image) wstaw GATE na active_agent:
1. **Postgres Lookup Active Agent** (v2.4): `SELECT active_agent FROM user_agent_state WHERE chat_id=$chat`.
2. **IF Subagent Active?** (if v2.2): active_agent LIKE 'subagent:%' (albo != 'idea'/'' /null).
   - **TRUE (subagent aktywny):** POST do cm-agent `/message` {chat_id, text:"skomentuj ostatni zrzut",
     active_agent} (httpRequest v4.2, nagłówek X-Researcher-Secret) -> subagent auto-komentuje z wizji
     (regex 'skomentuj ostatni zrzut' + suggest_comment_from_image już są w cm-agent). ŻADNEGO triażu.
   - **FALSE (Idea Bot/domyślny):** dotychczasowy `Prepare Triage Reply -> Telegram Send Triage`.
3. Przepnij: `Save Idea -> Postgres Lookup Active Agent -> IF -> (TRUE: HTTP cm-agent /message) / (FALSE: triage)`.

Analogicznie dla CM aktywnego (opcja): active_agent='cm' -> zapis do schowka + info, bez triażu.

## Kroki wykonania
1. Pobierz workflow (read-only), zrzuć typeVersion `Save Idea`/`Idea Gate Check`/`Telegram Send Triage`.
2. Patcher (ags-media-spike): dodaj 2-3 węzły (Lookup Active Agent, IF, HTTP cm-agent /message),
   przepnij connection z `Save Idea` outputu.
3. PUT {name,nodes,connections,settings przefiltrowane}; **deactivate+activate** (AP n8n).
4. Tap-test: w Subagencie X wyślij zrzut -> BEZ triażu Idea Bota, subagent od razu proponuje komentarz
   per autor; w trybie Idea Bot (default) -> triage jak dziś.

## Ryzyka
- AP-301: nowe węzły z typeVersion z DZIAŁAJĄCEGO węzła tego workflow.
- Sprawdzić strukturę $chat/chat_id w Prepare Idea Photo (skąd brać chat_id do lookupu).
- Nie zepsuć głównej gałęzi triażu (Idea Bot musi działać dla default).
