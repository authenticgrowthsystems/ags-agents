# RAPORT do Managera - BE-PORZADKI (19/07/2026, tryb rownolegly)

Budowniczy: BE-PORZADKI, galaz `build/porzadki` (worktree build-porzadki, baza 2fa33ed).
Brief: docs/briefs/BRIEF_PORZADKI_DETERMINISTYCZNE_19072026.md. Zakaz deployu przestrzegany:
zero push na serwer, zero rebuild, zero psql, zero n8n. Sklada INTEGRATOR.

## Co zbudowane

### (A) Deterministyczny route komend konfiguracyjnych (conversation.py)

Incydent: CM odpowiedzial "Zrobione. AGS LinkedIn ma teraz okno 16:00-18:00" bez wywolania
target_update - DB niezmienione, zero paragonu ⚙️. Fix: regex route w `handle()` PRZED LLM
(zaraz po brands_ui, przed _KARTY_RE):

- `_USTAW_OKNO_RE`: "ustaw okno [publikacji] dla <brand> <channel> na HH:MM-HH:MM"
  -> `_target_update(publish_windows)` -> paragon ⚙️. Godziny walidowane (25:00 nie matchuje),
  normalizacja 9:05 -> 09:05, marka upper / kanal lower, toleruje kropke i spacje wokol '-'.
- `_USTAW_KEY_RE`: "ustaw <key> dla <brand> <channel> na <value>" -> `_target_update` TYLKO
  dla kluczy z allowlisty `_CONFIG_KEYS` (publish_windows, publish_mode, language_publish,
  posts_per_day, follower_count, thread_enabled, voice_note, secret_prefix, emergency_publish).
  Klucz spoza listy + ISTNIEJACY cel = szczera odmowa z lista kluczy (nie LLM - to on
  "zalatwial" bez wykonania). Klucz spoza listy + nieistniejacy cel (np. "ustaw temat dla
  jutrzejszego posta na...") = zwykla rozmowa, idzie do LLM jak dotad.

Allowlista celowo NIE zawiera kluczy listowych (rules) - te zostaja w /set i u LLM.
emergency_publish JEST na liscie: odwolanie blokady kanonu 19/07 ma byc deterministyczne.

### (B) Odrzucenie karty kasuje wiersze kolejki (matreview.py)

W galezi `ok/no` po `set_item_status`: przy 'no' dodatkowo
`UPDATE post_queue SET status='rejected' WHERE content_item_id=%s AND status IN
('review','held','scheduled','queued')`. Dowod potrzeby: pq 245 odrzuconego artykulu
wisial w 'review' na zawsze.

Uwaga dla integratora: galaz `matdec:drop` (odrzucenie na etapie intake, status draft)
NIE zostala ruszona - materialy draft nie maja jeszcze wierszy pq, a brief kazal dotknac
tylko akcji 'no'.

### (C) SQL sprzatajacy sieroty - DO WYKONANIA przez Tomasza (SSH), moze wziac integrator

```sql
UPDATE post_queue pq SET status='rejected' FROM content_items ci
WHERE ci.id=pq.content_item_id AND pq.status='review' AND ci.status IN ('rejected','archived');
```

## Weryfikacja lokalna

- `python -m py_compile cm-agent/app/conversation.py cm-agent/app/matreview.py` = OK.
- Test regexow (definicje wyciete ze zrodla przez exec, nie kopia): 14/14 PASS, w tym oba
  przypadki DoD, pulapki (zla godzina, fraza konwersacyjna, wielowyrazowy voice_note).
- Zero DDL, zero n8n - zgodnie z kontraktem dotkniete TYLKO conversation.py i matreview.py.

## Tap-testy po deployu (dla integratora / Tomasza)

1. "ustaw okno publikacji dla AGS x na 13:00-21:00" -> paragon ⚙️ AGS/x: publish_windows =
   13:00-21:00 + verify read-only w DB.
2. Odrzucenie karty (matnav no) -> wiersze pq materialu przechodza na 'rejected'.
3. Po SQL (C): sieroty = 0 (SELECT COUNT(*) FROM post_queue pq JOIN content_items ci ON
   ci.id=pq.content_item_id WHERE pq.status='review' AND ci.status IN ('rejected','archived')).
