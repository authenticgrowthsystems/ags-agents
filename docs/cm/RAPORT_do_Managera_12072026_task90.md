# RAPORT do Managera - 12/07/2026: Task #90 X follower_count + Article vs nitka

Od: BUILD ENGINEER | Status: rdzen GOTOWY (ddbb931), czeka rebuild + config + decyzja migracji.

## Docs-first (przed implementacja, per doktryna)

Brief zakladal "X Articles endpoint natywny" - ZWERYFIKOWANE w oficjalnych docs (docs.x.com):
- POST /2/articles/draft {title, content_state: DraftJS blocks} (+cover przez media upload)
- POST /2/articles/{id}/publish -> zwraca post_id
- OAuth 1.0a wspierany = NASZE istniejace klucze X
- NIEZNANE: wymogi tieru API i limity (docs milcza) -> zywa sonda przy budowie adaptera n8n.
Zrodla: docs.x.com/x-api/articles/introduction; Articles dla wszystkich Premium od 01/2026.

## Wykonane (ddbb931, zero DDL - config jsonb)

1. **Generacja**: kanal x czyta channels.config: follower_count < 1000 (i brak thread_enabled)
   = dluga tresc generowana jako JEDEN artykul (1. linia = tytul max 8 slow, akapity, zero
   ===TWEET===). >= 1000 albo thread_enabled=true = stara siatka nitek. Prog czytany na zywo -
   aktualizacja licznika bez deployu (target_update).
2. **Bezpiecznik dispatchu**: artykul X (>600 zn. bez separatorow) NIE idzie do publishera
   tweetow (limit znakow) - trafia w tryb reczny (held, meldunek 'gotowiec czeka'), publikacja
   przez 📄 + intake [ZEWN], jak dzisiejszy artykul AGS.
3. Dedup: bez zmian (semantyczny, format-agnostyczny) - artykul vs nitka = ta sama historia.

## ZOSTAJE w #90

- **Adapter n8n POST /2/articles** (draft+publish, DraftJS builder, sonda tieru na zywo) -
  wymaga sesji z tapem Tomasza; do tego czasu artykuly X = tryb reczny (bezpieczne).
- **Migracja nitek w kolejce** (decyzja Tomasza guzikami w czacie): w kolejce na pon-sr siedzi
  ~5 zatwierdzonych nitek X wygenerowanych przed kanonem.
- **Voice Bible v2.1 -> v2.2** (Manager przygotuje pelny plik): Sekcja 7 thread vs article per
  follower_count, Sekcja 13 Re-Intro (article=required, thread=optional), Sekcja 14 barwy per
  marka, Sekcja 15 waluta. Deploy wzorcem bumpa (brand_config v3->v4 + history + md5).

## Konfiguracja (Tomasz, 10 sekund, w czacie CM)

"ustaw follower_count 10 dla celu AGS x" (target_update; licznik z profilu; subagent upomni sie
o aktualizacje przy metrykach poniedzialkowych).
