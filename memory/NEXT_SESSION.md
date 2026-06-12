# AGS Agents - Resume Point (saved 2026-06-12 ~22:50)

Paste the MASTERPROMPT block (bottom) into a fresh Cowork session tomorrow. Cowork auto-loads CLAUDE.md + memory; this adds the specific resume context.

---

## CURRENT LIVE STATE (works right now)

**The system:** Telegram content pipeline. Capture idea (text / voice / photo) -> Sonnet 4.6 + Voice Bible draft in PL+EN -> review -> publish (now / scheduled / queue).

**Live n8n workflows** (Mikrus ivy147, `https://ivy147-20147.mikrus.cloud`, API via public API key):
- HITL handler `U5pUZjy2yAhR1sWg` (174 nodes) - bot brain: capture, triage, Zrob post, PL+EN gen, edit (PL->EN sync), voice memory, Zapisz-do-kolejki.
- X-agent `TbHt6ZwfqmMarx18` (45 nodes) - cron 14/18/22: serve queue (priority) else generate + HITL preview.
- Scheduler `x1jJEbcWAe3FnpCa` (5 nodes) - every minute, publishes post_queue `scheduled` at scheduled_for.

**DB** (Postgres, n8n cred id `aHDeZ1ywfPihvVxH`): inspirations, post_queue (priority int + status queued/scheduled/published), hitl_sessions, conversation_state, voice_notes, voice_samples, published_posts.

**Verified live today:** full edit loop (PL edit -> EN re-sync, no double-capture), queue auto-publish (14:00 slot, ok=True, posted to X), 2 voice samples captured.

**Models / creds:** generation `claude-sonnet-4-6` (cred `w2iuB1ttk7ekS2ix`); voice `whisper-1`, photo `gpt-4o-mini` vision (OpenAI cred `8dfgnu2L2JxcMICs`).

**Repo:** committed through the 3 end-of-session fixes. Branch `claude/fervent-cray-d13fc3`. Workflows in repo are SANITIZED (secrets -> placeholders).

## KEY OPERATIONAL RULES (do not relearn the hard way)
- After EVERY PUT to a live workflow: deactivate + activate (else the old def keeps running - n8n caches the active snapshot).
- n8n branch execution order is NOT connection-order; make mutual-exclusion data-dependent, not order-dependent.
- Build workflow-edit scripts with the Write tool, run with python (bash-embedded python mangles $json / Polish chars).
- Verify generation pieces via temp-webhook + execution inspection BEFORE asking Tomasz to test.
- Sanitize secrets (Telegram bot token + 4 X OAuth1 keys) before any repo export; scan after. PUT body = {name, nodes, connections, settings}.
- post_queue + inspirations owned by DB superuser -> ALTER blocked (CREATE TABLE works, owns it). Use existing columns.

## NEXT PRIORITIES (in order)
1. **MEDIA (Tomasz's #1):** attach the original photo to the tweet. Store the Telegram file ref with the photo idea (file_id / file_path in inspirations.metadata); on publish do OAuth1 media upload (`upload.twitter.com/1.1/media/upload`, chunked or simple) -> get media_id -> attach to the tweet (`media.media_ids`). Touches: photo capture (store ref), and all 3 publish points (HITL `Post To X Approve`, X-agent `Publish Queued To X`, scheduler `Publish To X`).
2. **Style Bible:** Tomasz fills `brand-canon/STYLE_BIBLE_QUESTIONNAIRE.md` (async) -> generate `STYLE_BIBLE.md` -> wire into the generation prompt.
3. **voice_notes editable from the bot** (a command to add a narrative note without touching the DB).
4. (parked, separate sessions) LinkedIn/IG publisher modules, AI NEWS (RSS), CRM, content archive, performance metrics.

## WATCH
- Sonnet occasionally near/over 280 (prompt hardened, HITL shows count). If it recurs, add a hard regenerate-if-over guard.
- Build-in-public content for the whole pipeline build not yet drafted (offered to Tomasz).
- X-agent now publishes directly (queue server) - it has inline OAuth1 keys; keep sanitization in mind on export.

---

## MASTERPROMPT (paste tomorrow)

Jestem Tomasz (AGS / Authentic Growth Systems). Wczoraj zbudowaliśmy kompletny pipeline treści na Telegramie: złap pomysł (tekst/głos/zdjęcie) -> Sonnet 4.6 + Voice Bible -> draft PL+EN -> przejrzyj (Opublikuj teraz / Zaplanuj / Zapisz do kolejki + priorytet / Edytuj / Inny kąt / Odrzuć) -> publikuj. Edycja po polsku auto-syncuje wersję EN; moje próbki głosu (voice_samples) i reguły (voice_notes) karmią każdą generację; serwer kolejki auto-publikuje w slotach 14/18/22 priorytetowo (zweryfikowane live). Wszystko w n8n na Mikrus, zacommitowane.

Najpierw przeczytaj: `memory/NEXT_SESSION.md` (pełny stan + reguły operacyjne), ostatni wpis w `memory/build-log.md`, `brand-canon/ags.md`, `C:\Claude-CoWork\AGS\VOICE_BIBLE.md`, oraz pliki pamięci. Trzymaj się reguł operacyjnych (reaktywacja po każdym PUT, Write-tool do skryptów, sanityzacja sekretów, weryfikacja generacji przez temp-webhook).

Dziś robimy **MEDIA**: dołączenie oryginalnego zdjęcia do tweeta. Zacznij od planu (gdzie trzymamy referencję pliku Telegram przy pomyśle-zdjęciu, jak zrobić OAuth1 media upload, które węzły publikujące to dotyka), potem prowadź mnie jeden atomowy krok na raz.
