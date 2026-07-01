# RAPORT DO MANAGERA AGS (02/07/2026, od BE)

Tomasz wkleja do czatu Manager AGS (Cowork). Stan od ostatniego raportu (Brama 2, 28-30/06).

## 1. CM zbudowany - Brama 3 PASSED, ale KOREKTA zakresu

- **Silnik wykonawczy CM LIVE + zweryfikowany:** 30/06 opublikował PRAWDZIWY tweet end-to-end (pomysł -> Sonnet tekst-matka -> Haiku wariant X -> compliance -> HITL approve guzikiem -> Scheduler -> tweet na @tomasz_ags). Serwis `cm-agent` na Mikrusie (port 8089, /health ok).
- **KOREKTA Tomasza (canonical, nie re-litygować):** to jest dopiero **kręgosłup wykonawczy (~10%)**, NIE Content Manager z wizji. Prawdziwy CM = **proaktywny planer tydzień/2 miesiące + dwustronna rozmowa przez Telegram + podgląd/harmonogram + pełne dowodzenie subagentami**. Tego jeszcze nie ma. NIE nazywać CM "gotowym".

## 2. Kanoniczna sekwencja budowy (Tomasz 30/06)

Subagenci PRZED mózgiem CM (bo CM musi mieć kim zarządzać):
1. **Agent X jako async subagent CM** ← ZROBIONE (patrz p.3)
2. **Dokończyć LinkedIn** (w toku, p.4)
3. **Dokończyć mózg CM** (planer + rozmowa Telegram + podgląd + dowodzenie)
4. Subagenci **FB / IG / YouTube**
5. Zebrać w całość -> dopiero następna budowa

## 3. Subagent X LIVE + zasada obiektu

- **Subagent X Publisher** (n8n workflow G3nEIt5lIkiKemiK): webhook `/webhook/subagent-x-publish`, klucze z `app_secrets` (guarded, zero hardkodu), OAuth1 publish, callback (post_queue published + agent_messages RESPONSE do CM). **Pierwszy prawdziwy subagent na kontrakcie konektora.**
- CM deleguje publikację X do subagenta (nie pasywne post_queue).
- **ZASADA PRODUKTU (canonical):** każdy subagent kanałowy = **sprzedawalny OBIEKT z przełącznikiem `supervised`**: STANDALONE (własny Telegram + własna pętla, kupowalny solo) LUB SUPERVISED (pod CM/Opus 4.8). Flaga `channels.supervised` już w bazie; CM zarządza tylko kanałami supervised. Na razie zbudowany organ supervised-publish; standalone-brain = warstwa dalej.

## 4. LinkedIn (w toku)

- Aplikacja 1 "TNM Content Manager" (Client ID 77whp1grre447n, zweryfikowana na stronie TNM): Share on LinkedIn (personal, w_member_social) + OpenID Connect (person URN). Personal gotowe do wpięcia.
- Strona firmowa wymaga **Community Management API** = osobna aplikacja (LinkedIn: CMA musi być JEDYNYM produktem na apce) -> Dev Tier -> review LinkedIn (dni). App 2 do utworzenia.

## 5. Sonnet 5 + bezpieczeństwo

- **Sonnet 5** (`claude-sonnet-5`) podmieniony w Researcher synth + CM tekst-matka (thinking disabled na tych callach; ten sam sticker $3/$15 ale ~30% więcej tokenów). LIVE w obu.
- **SECURITY:** klucze OAuth1 X były ZAHARDKODOWANE w węźle Schedulera + wyeksponowane w sesji -> **do rotacji** (X portal). Nowy subagent czyta z `app_secrets` (bezpiecznie).

## 6. Następny krok

E2E test subagenta X pod CM (content_item na X -> CM deleguje -> subagent publikuje -> callback). Potem LinkedIn, potem mózg CM.

---

*Od: AGS Build Engineer (Opus 4.8). Pełny stan techniczny: docs/RESUME_MASTERPROMPT_02072026.md.*
