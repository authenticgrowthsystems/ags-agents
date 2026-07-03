# RAPORT Faza 1 / krok 1b: router active_agent + menu /agents + setMyCommands - od BE do Managera AGS

**Data:** 03/07/2026. **Status: WGRANE + ZWERYFIKOWANE STRUKTURALNIE LIVE (E2E tap-test u Tomasza w toku).**

## Co zbudowane (HITL U5pUZjy2yAhR1sWg: 208 -> 219 węzłów, PUT 200 + reactivate)
- **Rodzina callbacków `agsel:`** na czele łańcucha bramek (cm:/crit:/mtier:/idea:/synth: NIETKNIĘTE): `Is Agsel Callback?` -> `Parse Agsel Callback` (sanityzacja wartości regexem) -> `Agsel Save State` (UPSERT user_agent_state.active_agent) -> `Agsel Build` -> `Agsel Set Commands` (setMyCommands scope czatu, komendy per agent) -> `Agsel Confirm Msg`.
- **Menu `/agents`:** nowa reguła w Detect Update Type + 11. wyjście Route By Update Type -> `Agents Load Data` (channels supervised active/draft + active_agent) -> `Agents Build Menu` (inline keyboard: 💡 Idea Bot, 🧠 CM, 📣 per konto/cel z channels, ✅ przy aktywnym) -> `Agents Send Menu`. **Open/closed: nowy wiersz channels pojawia się w menu bez zmian kodu.**
- **Router tekstu:** `Idea Not Editing?` TRUE -> `Get Active Agent` (COALESCE default **'idea'**) -> `Active Is Idea?` -> TRUE = stary tor Idea Bota (Prepare Idea Text), FALSE = `CM Conversation Message` (POST cm-agent /message z `active_agent` w payloadzie; guard z app_secrets).
- **Komendy agentowe** `/plan /cancel /kolejka /raport` przechodzą jak tekst do aktywnego agenta.
- **Zero nowych hardkodów tokena** - wszystkie nowe węzły czytają telegram_bot_token + researcher_webhook_secret z app_secrets. (Uwaga: STARE węzły httpRequest w HITL nadal mają hardkod tokena w URL - znany dług "rotacja tokena Telegram", bez zmian w tym kroku.)
- Incydent przy wgraniu: pierwszy activate zwrócił 400 (wyścig po deactivate), drugi activate = 200, workflow aktywny. Zweryfikowane na live snapshocie: wszystkie 11 nowych węzłów + 5 przepięć obecne.

## Acceptance criteria (R2)
| Kryterium | Status |
|---|---|
| (a) /agents pokazuje min. 4 pozycje (Idea, CM, X, LinkedIn Personal EN) | STRUKTURA TAK (menu z channels: AGS x + AGS linkedin supervised); tap-test Tomasza = finalne potwierdzenie |
| (b)(c) rozmowa z subagentem o kolejce/publikacjach | N/D (krok 1d; do tego czasu wybór subagenta daje komunikat "w budowie" z cm-agent po deployu 1c) |
| (d) nowy wiersz channels widoczny w menu bez zmian kodu | TAK (menu budowane z SELECT po channels) |
| R1(a) default bez wyboru = Idea Bot (tor sprzed 03/07) | TAK (COALESCE 'idea') |

## INCYDENT + HOTFIX (03/07 ~10:45, wykryty w tap-teście Tomasza)
Objaw: po przełączeniu na CM tekst "Pokaż plan" złapał Idea Bot, CM milczał. Diagnoza Z DOWODU (egzekucja 39398, node-by-node): `Get Active Agent` zwrócił poprawnie 'cm', ale IF `Active Is Idea?` puścił item wyjściem TRUE. Przyczyna: oba nowe IF-y dostały `typeVersion: 1` z NOWYM formatem warunków (filter v2) - stary silnik IF ignoruje taki format i przepuszcza wszystko. Konsekwencja groźniejsza: `Is Agsel Callback?` przepuszczał WSZYSTKIE callbacki do gałęzi agsel (guziki approve/triage martwe od PUT 1b do hotfixu; nikt w tym oknie nie klikał approve - zero szkód; śmieć: tekst "Pokaż plan" zapisany jako pomysł w inspirations, Tomasz odrzuci guzikiem). HOTFIX: oba IF-y na typeVersion 2.2 + conditions options {version:2, typeValidation:'loose'} (wzorzec działających bramek), PUT 200 + reactivate 200, zweryfikowane na live snapshocie. LEKCJA do anti-patterns: nowe węzły n8n buduj na typeVersion WZIĘTYM z działającego węzła tego samego typu w tym workflow, nie z pamięci.

## Commit / artefakty
Kod HITL żyje w n8n (nie w repo); skrypt patcha: `Temp/ags-media-spike/hitl-1b-agent-router.cjs` (+ backup bk_hitl_1b_*.json). Raport w repo (commit razem z 1c).

**Next:** 1c (rozmowa CM za menu + save_to_zanadrze + Opus).
