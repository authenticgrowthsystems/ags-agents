# AP-306: One-shot container assumes worker-loaded secrets and fails silently

**Anti-pattern (05-06/07/2026, BE, TWICE in two days):**
1. `drift_check` (one-shot `docker run ... python -m app.sync.drift_check`) called `logbot.send` -
   alert went nowhere because `log_bot_token` lives in app_secrets and only the MAIN worker loads it
   at startup (`worker._load_secrets`); the one-shot env has just POSTGRES_DSN.
2. `bulk_polish` (one-shot) called the Anthropic client - every LLM rewrite silently returned the
   original text (exceptions swallowed), reported "DONE" with 1/37 fixed; looked like the filter
   worked when it never ran.

**Why bad:** the failure is INVISIBLE - the tool prints success-shaped output while doing nothing;
wasted run, false confidence, user-facing gap (no alert / no correction).

**Correct:** every `python -m app.<tool>` one-shot MUST load its own secrets from app_secrets at
the top of main() (mirror `worker._load_secrets` for exactly the keys it needs) and FAIL LOUDLY
(print + exit) when a required key is missing. When adding a new one-shot, grep it for
`config.<ANY>_KEY/_TOKEN` usage and cover each. Never assume container env == worker env.

---

## Rozszerzenie kanonu (24/07/2026, decyzja Managera P5): CICHY `except` TO BLAD PROJEKTOWY

Trzeci przypadek tej samej klasy, tym razem bez kontenera jednorazowego. Do payloadu meldunku
Researchera wszedl `overall_confidence` czytany z NUMERIC, czyli `Decimal`. `Decimal` nie
serializuje sie do JSON, wiec INSERT do `agent_messages` lecial wyjatkiem - a wyjatek byl
POLYKANY. Joby konczyly sie `completed` z 11 faktami i ZEREM powiadomien (dowod: 91d8b597,
b55a9f58). Praca zostala wykonana i zaplacona, tylko nikt sie o niej nie dowiedzial.

**Regula (kanon):** cichy `except` na sciezce POWIADAMIANIA, ZAPISU WYNIKU albo NAUKI zamienia
awarie w niewidzialna cisze, a cisza wyglada dokladnie jak sukces. Dlatego:

1. `except: pass` jest dozwolony TYLKO wtedy, gdy cisza jest ZAMIERZONA i wyjasniona komentarzem
   w tej samej linii (przyklady legalne: timeout nasluchu w petli, parsowanie znacznika czasu
   z wartoscia domyslna). Bez komentarza = blad projektowy.
2. Kazdy inny `except` na tych sciezkach ma zostawic slad: minimum `traceback.print_exc()`
   (widoczne w `docker logs`), a przy powiadamianiu czlowieka - ESKALACJA (`_escalate` /
   log-bot), nie samo logowanie.
3. Nieudany zapis meldunku eskaluje. Sanityzujemy CALY payload przed zapisem
   (`_json_safe`: Decimal -> float, daty -> ISO, reszta -> str), zamiast liczyc na to,
   ze typy sie zgodza.

**Przeglad wykonany 24/07** (sprint domykajacy 20-26/07): przejrzane wszystkie `except: pass`
w `cm-agent/app` i `ags-researcher/app`. 17 miejsc dostalo `traceback.print_exc()` z powodem
w komentarzu (m.in. petla nauki `decisions._learn` i `matreview.log_learning`, ingest wynikow
researchu, `_admin_chat_id` Researchera - bez niego NIE MA zadnego powiadomienia, prosba
subagenta `_log_channel_need`, filtr polszczyzny `compliance._rewrite`, tlumaczenie wariantu
przed kolejka). 2 miejsca zostaly cicho, ale z uzasadnieniem w komentarzu (timeout nasluchu
NOTIFY, parsowanie znacznika throttla).

**Test dymu:** `python cm-agent/tests/test_import_smoke.py` - importuje wszystkie moduly ze
stubami zaleznosci. Skladnia (`py_compile`) nie lapie cykli importow ani literowek w nazwach
modulow, a wlasnie takie bledy lubia sie chowac za cichym `except` przy imporcie.
