# BRIEF BUILDU: KOLEKTOR METRYK X - Owned Reads (19072026)

Wywolanie sesji: `@docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_KOLEKTOR_METRYK_X_19072026.md zbuduj`

## 0. TRYB ROWNOLEGLY (Tomasz 19/07 ~22:45 - NADPISUJE sekwencyjnosc; przeczytaj PRZED praca)

Wszystkie 4 buildy ida ROWNOLEGLE w osobnych oknach. Zasady twarde:
1. PIERWSZY RUCH: utworz WLASNY worktree + galaz od galezi bazowej (NIE pracuj na sb-work!):
   `git -C "C:\Claude-CoWork\AGS\ags-agents" worktree add "C:\Claude-CoWork\AGS\ags-agents\.claude\worktrees\build-kolektor" -b build/kolektor-x origin/claude/silly-blackwell-dfc32d`
   Wszystkie sciezki i git -C w tej sesji = ten worktree. Committuj na build/kolektor-x.
2. ZAKAZ deployu: ZERO push na serwer, ZERO rebuild cm-agent, ZERO psql, ZERO zmian n8n
   (gdy brief wymaga DDL - plik db/0NN LEZY w commicie, wykona go INTEGRATOR). Kod + py_compile
   + testy lokalne (parser/regex - jak sie da bez serwera) + commit. Weryfikacje read-only
   (temp webhook) WOLNO.
3. Dotykaj TYLKO plikow z sekcji KONTRAKT swojego briefu - reszta nalezy do rownoleglych
   budowniczych (konflikty rozwiazuje integrator, nie mnoz ich).
4. Model: sesje zaczyna Fable 5 (max 2 prompty: wczytanie + szkielet decyzji), potem Tomasz
   przelacza na Opus 4.8, ktory KONCZY build w tym samym oknie (kontekst zostaje).
5. Zamkniecie: commit na build/kolektor-x + STATUS w tym briefie + raport per krok; masterprompt
   aktualizuje TYLKO INTEGRATOR (unik konfliktow na wspolnym pliku).

## 1. CO budujemy (definition of done)

Kolektor per-post metryk WLASNYCH postow X do PG, raz dziennie, na oficjalnym X API
pay-per-use **Owned Reads $0.001/read** (~$4.50/mies przy 150 postach x 30 dni).
SELEKCJA SCIEZKI ZAMKNIETA 19/07 na bazie trzech raportow deep research
(docs/research/x_metrics_19072026/ - ChatGPT DR, Gemini DR, raport decyzyjny; ZBIEZNE):

- Endpoint: **GET /2/users/{id}/tweets** (jedyny z POTWIERDZONYM Owned Read; GET /2/tweets
  NIEPOTWIERDZONY - nie uzywac), tweet.fields=created_at,referenced_tweets,public_metrics,
  non_public_metrics,organic_metrics, max_results=100, paginacja do granicy 30 dni.
- Auth: user context wymagany dla non_public/organic. **OAuth 1.0a user context DZIALA**
  (docs [3][5]) - mamy juz klucze OAuth1 od publikacji! Start na OAuth1; OAuth2 PKCE
  (tweet.read users.read offline.access) jako docelowe przy okazji.
- Prywatne metryki (url_link_clicks, user_profile_clicks, impressions organic) TYLKO dla
  postow <30 dni - kolektor NIE odtworzy historii; im szybszy start, tym mniej strat.
- Followers: dzienny odczyt wlasnego profilu (followers_count -> channel_metrics_daily).
  Per-post follows NIE ISTNIEJE w self-serve (tylko Enterprise) - nie obiecywac.
- ZAKAZ scrapingu/Playwright na sesji (Automation Rules 04/2026: permanent suspension).
  Fallback: reczny eksport CSV z PAD (30 dni / 3000 postow na plik).

DoD:
- [ ] Sonda: 1 request z pelnymi polami na swiezym poscie -> non_public_metrics obecne
- [ ] Developer Console potwierdza rozliczenie jako Owned Read (PRZED wlaczeniem crona)
- [ ] DDL 025: x_post_metric_snapshots (tweet_id, observed_at, 3 namespaces jsonb, raw)
      + zapis account-daily do channel_metrics_daily (source 'x_api')
- [ ] Dzienny tick w sync workerze / petli (raz na dobe po granicy UTC)
- [ ] refresh_metrics stats_mode 'x_owned_reads' zasila published_posts.engagement_metrics
      (szew juz jest w reports.py) -> raporty subagenta widza X bez recznego wpisu
- [ ] Guardrail kosztow: alert gdy >200 zasobow/dzien; limit kredytow $10

## 2. KONTRAKT wpiecia w szyne

- Tabele: NOWA x_post_metric_snapshots (DDL 025 + SCHEMA ten sam commit); pisze
  channel_metrics_daily (023, source 'x_api') + published_posts.engagement_metrics (merge).
- Sekrety: klucze OAuth1 X juz w app_secrets (prefix x/twitter - sprawdz ksztalt); user id
  numeryczny zapisac raz (brand_config albo channels.config).
- Konfiguracja: channels.config.stats_mode='x_owned_reads' dla AGS/x (target_update).
- Zero n8n (kolektor w cm-agent; tick z petli workera jak _brand_tokens_tick).

## 3. Czego NIE dotykac

Publikacja X (Scheduler/OAuth1 publish) bez zmian. Zadnego GET /2/tweets. Zadnego scrapingu.

## 4. Zaleznosci i stan zastany

reports.refresh_metrics ma szew 'x_owned_reads' (return 0 + komentarz). channel_metrics_daily
istnieje (DDL 023). Reczny wpis (set_manual_metrics) zostaje jako fallback. Koszty:
docs/research/x_metrics_19072026/x_cost_scenarios.txt.

## 5. Udzial Tomasza

1. [DONE 19/07 21:30] Developer Console skonfigurowana (zrzuty = evidence):
   - pay-per-use AKTYWNE, saldo $6.96 (kredyty juz zuzywane przez publikacje - wykres kosztow);
   - cykl rozliczeniowy Jul 19 - Aug 19; konto "Tomasz Nawrocki | AGS" (wlasciciel @tomasz_ags);
   - Auto Recharge ON ($10 przy saldzie $1) - ZOSTAJE (kanon: zatwierdzone publikuje sie zawsze;
     puste saldo zatrzymaloby tez publikacje);
   - Spend Cap $20/cykl (DECYZJA TOMASZA; rekomendacja BE byla $10) - max ekspozycja ograniczona;
   - zakupu nie bylo (saldo wystarcza) - otwarty punkt "minimalny top-up" bezprzedmiotowy.
2. Tap-test sondy (sesja buildu poda komende); potwierdzic w konsoli cene Owned Read PRZED cronem.
3. SSH: psql 025 + rebuild po buildzie.

## 6. Zamkniecie sesji (OBOWIAZKOWE)

Raport docs/cm/RAPORT_do_Managera_<data>_kolektor_x.md + masterprompt + pamiec + STATUS tu.

STATUS = READY-BILLING (19/07 21:30): billing skonfigurowany i udowodniony (sekcja 5 pkt 1) - build moze startowac od sondy. Wywolanie: @docs/RESUME_MASTERPROMPT_19072026.md @docs/briefs/BRIEF_KOLEKTOR_METRYK_X_19072026.md zbuduj
