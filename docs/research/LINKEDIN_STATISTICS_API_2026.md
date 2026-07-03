# LinkedIn statistics API - fakty z oficjalnych docs (03/07/2026, docs-first przed 1g)

Zrodlo: Microsoft Learn (learn.microsoft.com/en-us/linkedin), wersje li-lms-2026-04..06. Zweryfikowane po awarii
joba Researchera 728d02ba (bug syntezy naprawiony osobno, commit cf433dd).

## 1. PROFIL OSOBISTY (member) - JEST API (nowosc, historycznie niedostepne)
- **Endpoint:** `GET https://api.linkedin.com/rest/memberCreatorPostAnalytics`
- **Permission/scope:** `r_member_postAnalytics` ("Retrieve your posts and their reporting data")
- **Metryki (2026-04+):** IMPRESSION, MEMBERS_REACHED (unique), RESHARE, REACTION, COMMENT, POST_SAVE,
  POST_SEND, LINK_CLICKS, PREMIUM_CTA_CLICKS, FOLLOWER_GAINED_FROM_CONTENT, PROFILE_VIEW_FROM_CONTENT
- **JEDNA metryka per wywolanie** (queryType) -> pelny zestaw per post = kilka GET-ow
- **Findery:** `q=entity&entity=(share:urn...)` per post (tez `(ugc:urn...)`); `q=me` = agregat wszystkich postow membera
- **Agregacja:** TOTAL (default) / DAILY (DAILY nie dziala dla MEMBERS_REACHED, LINK_CLICKS, FOLLOWER_GAINED..., PROFILE_VIEW...)
- **Naglowki:** `LinkedIn-Version: YYYYMM` + `X-Restli-Protocol-Version: 2.0.0`
- **UWAGA dostep:** nasz obecny token (Token Generator, App 1: Share on LinkedIn + Sign In) NIE ma tego scope.
  Wymaga produktu z ta permission (rodzina Community Management) -> **App 2 (CMA) w review LinkedIn** pokrywa kierunek.
  Weryfikacja live po tokenie z odpowiednim scope: GET na znany share (np. urn:li:share:7478540226701881345).

## 2. STRONA FIRMOWA (organization)
- **Endpoint:** `GET https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:{id}`
- **Permission:** `rw_organization_admin` (rola ADMINISTRATOR strony) - produkt Community Management API
- **Metryki (totalShareStatistics):** impressionCount, uniqueImpressionsCount, clickCount, likeCount,
  commentCount, shareCount, engagement (double = (clicks+likes+comments+shares)/impressions)
- **Zakresy:** lifetime (bez timeIntervals) / time-bound (timeIntervals DAY|MONTH) / per share (shares=List(urn:li:share:...))
  / per ugcPost (ugcPosts=...); okno danych = ROLLING 12 MIESIECY; bez paginacji
- Do swiezych like/comment per post: endpoint `socialActions`

## 3. X (Twitter) - bez zmian
Read API (GET /2/tweets) ZABLOKOWANE na obecnym tierze aplikacji (fakt 15/06). Fallback per decyzja
Managera #2: **reczne wprowadzanie metryk w rozmowie z subagentem** ("wprowadz engagement ostatniego posta X").

## 4. Ujednolicony ksztalt engagement_metrics JSONB (published_posts + raporty)
```json
{"impressions": 0, "unique_reach": 0, "reactions": 0, "comments": 0, "reshares": 0, "clicks": 0,
 "engagement_rate": 0.0, "source": "api|manual", "fetched_at": "ISO", "extra": {}}
```
Mapowanie: LI member IMPRESSION->impressions, MEMBERS_REACHED->unique_reach, REACTION->reactions,
COMMENT->comments, RESHARE->reshares, LINK_CLICKS->clicks; LI org impressionCount->impressions,
uniqueImpressionsCount->unique_reach, likeCount->reactions, commentCount, shareCount->reshares,
clickCount->clicks, engagement->engagement_rate; X manual: pola wpisywane recznie, source='manual'.

## 5. Konsekwencje dla 1g
1. Raporty daily/weekly startuja z: publikacje + kolejka + decyzje + metryki 'manual' (X) i 'api' dla LinkedIn
   DOPIERO gdy token ze scope r_member_postAnalytics / rw_organization_admin (App 2 CMA po review).
2. Kolektor metryk pisany od razu pod oba endpointy (member + organization), wlaczany per cel przez
   channels.config (np. {"stats_mode": "member_api" | "org_api" | "manual"}).
3. published_posts.post_id/post_url MUSI byc zapisywane przy publikacji -> patch callbackow subagentow
   (przygotowany, czeka na zgode).
