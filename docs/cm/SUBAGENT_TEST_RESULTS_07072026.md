# Wyniki testów subagentów (07/07/2026) - iteracyjnie z Tomaszem

Plan: docs/cm/SUBAGENT_TEST_PLAN_07072026.md. Wynik per test: ✅ działa | ⚠️ częściowo | ❌ brak.
Po całości: BE buduje braki -> re-test -> Tomasz orzeka "przeszło" -> projekt IG/FB/TikTok.

| Test | Kanał | Wynik | Uwagi / co do naprawy |
|---|---|---|---|
| T1 Świadomość kanałów | LinkedIn | ✅ | Wzorcowo: 4 powierzchnie, statusy, języki, okna, głos/konto, strategia CM, pytanie o konto. Drobne: echo starej eskalacji 10:00 (stare pending do wyczyszczenia kiedyś). |
| T2 Przegląd+edycja treści | LinkedIn | ❌ | Potwierdzone: „pokaż kolejkę” OK (lista+#id+sloty), ale „pełna treść #96” = nie ma dostępu (tylko skróty), „edytuj #125” = brak narzędzia. BUDOWA B: subagent_show_post (pełny tekst) + subagent_edit_post (podmiana treści post_queue, ew. + canonical). Sloty 13-17 w oknie US = OK. |
| T3 Generowanie ad-hoc | LinkedIn | ✅ | Znakomicie: świetny post (choreografia→architektura, głos człowieka, Sovereign Architect). Sam ocenił „to pasuje do RDC nie AGS", dał opcje. FIX: wygenerowany post BEZ Re-Intro Line (v2.1) - wzmocnić generację (jawna instrukcja Re-Intro w CHANNEL_GUIDE linkedin). |
| T4 Sloty/okna/luki | LinkedIn | ✅ (obserwacja) | W T3: znał okno 13-18, past-window→następny dzień, wybrał wolny slot 11/07. Dedykowany test luki kadencji (escalate) do zrobienia osobno jeśli chcesz. |
| T5 Publikacja+callback | X + LinkedIn | ✅ | POTWIERDZONE w AGS Alerts wielokrotnie: „wysłał do publikacji (zlecone, potwierdzę po callbacku)" → „opublikował (opublikowane X/LI)". Fix (b) działa per kanał. |
| T6 Multimedia | LinkedIn | ❌ (arch) | Subagent kanału nie ma media (zgodnie z oczekiwaniem). DECYZJA ARCH Tomasza 07/07: NIE doklejać media do subagenta kanału - zbudować DEDYKOWANE subagenty grafiki/wideo (operatory modeli) na kontrakcie konektora; CM/subagent kanału DELEGUJĄ do nich. Master prompt zaktualizowany. |
| T7 Multi-konto routing | | | |
| T8 Język komunikacji/publikacji | | | |
| T9 Comment radar/engagement | | | |
| T10 Metryki/raporty | | | |
| T11 Tryb pracy/standalone | | | |
| T12 Jakość dialogu | | | |

## Notatki szczegółowe
(BE zapisuje tu obserwacje per krok w miarę testów)
