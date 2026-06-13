# RAPORT STATUSU — AGS Content Pipeline

**Do:** Manager AGS (orchestrator)
**Od:** Manager AGS — sesja build 11–12/06/2026
**Data:** 12/06/2026
**Stage:** 0–1 (build-in-public, bez płacących klientów)

---

## 1. Sedno

Backbone produktu (Content Manager) **stoi i działa na produkcji.** Od pomysłu w telefonie do publikacji na X, głosem founder'a, w dwóch językach, z pętlą uczenia. To nie prototyp - 12/06 o 14:00 system **sam** opublikował post na X.

## 2. Dowiezione w tej sesji

- Pełny pipeline: capture (tekst / głos / zdjęcie z OCR) → draft **PL+EN** (Sonnet 4.6 + pełny Voice Bible) → przegląd (6 trybów decyzji) → publikacja (teraz / harmonogram / kolejka priorytetowa).
- **Pętla uczenia głosu:** edycje founder'a → `voice_samples` → karmią każdą kolejną generację. 2 prawdziwe próbki już w bazie.
- Edycja po polsku z auto-synchronizacją wersji angielskiej.
- Serwer kolejki z priorytetami, auto-drip w slotach 14/18/22.

## 3. Stan produkcyjny (live)

| Workflow | ID | Rola | Węzły |
|---|---|---|---|
| HITL bot | `U5pUZjy2yAhR1sWg` | mózg: capture, generacja, edycja, pamięć, kolejka | 174 |
| X-agent | `TbHt6ZwfqmMarx18` | cron 14/18/22: kolejka → publikuj, inaczej generuj | 45 |
| Scheduler | `x1jJEbcWAe3FnpCa` | co minutę: publikuj zaplanowane | 5 |

DB: Postgres (inspirations, post_queue, hitl_sessions, conversation_state, **voice_notes, voice_samples**, published_posts).

Modele: generacja `claude-sonnet-4-6`; głos `whisper-1`; zdjęcie `gpt-4o-mini` vision.

## 4. Zweryfikowane twardo

- Pętla edycji PL→EN bez podwójnego łapania (exec 2796: edit OK, capture NIE).
- Auto-publikacja z kolejki o 14:00 (`ok=True`, post na X).
- Wszystkie egzekucje testowe: `success`.

## 5. Bugi rozbrojone (4)

1. **Auto-publikacja śmiecia** (retry gubił insight) - fix 3-warstwowy.
2. **Podwójne łapanie edycji** (wyścig stanu) - fix deterministyczny.
3. **Edycja X-agenta** (SQL `JSON.stringify` → podwójne cudzysłowy) - naprawiona.
4. **Cache n8n po PUT** - usystematyzowane (reaktywacja po każdym PUT).

## 6. Ryzyka / otwarte

- **Media:** posty są tekstowe, bez zdjęć - to #1 ból founder'a.
- 280 znaków: Sonnet sporadycznie ociera się o limit (prompt wzmocniony, HITL pokazuje licznik).
- Handoff między sesjami: git worktree izoluje pliki - **naprawione**, stan przeniesiony do auto-memory (`project_resume_point.md`).

## 7. Następne priorytety + czego trzeba od Tomasza

| Priorytet | Akcja | Blokada |
|---|---|---|
| **MEDIA** | zdjęcie do tweeta (OAuth1 media upload) | następna sesja |
| Style Bible | wepnę w prompt | **Tomasz wypełnia 100 pytań** (jego input) |
| voice_notes z bota | komenda do dodawania reguł | - |
| Moduły LinkedIn/IG | osobne sesje | klucze API kont gdy ruszymy |

## 8. Ocena strategiczna

Backbone gotowy = **produkt sprzedawalny** (architektura multi-tenant zachowana, produktyzacja świadomie odłożona). Media + Style Bible domkną efekt "wow". Potem moduły kanałów = ścieżka do oferty. Stage 0–1 utrzymany: zero fałszywych roszczeń, wszystko realne i działające.

**Rekomendacja:** następna sesja - media. Równolegle Tomasz wypełnia Style Bible (jedyne co blokuje skok jakości głosu).
