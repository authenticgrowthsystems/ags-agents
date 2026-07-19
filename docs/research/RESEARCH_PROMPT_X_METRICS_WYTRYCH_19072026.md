# Prompt badawczy: wytrych metryk X dla subagenta (19/07/2026)

Do recznego uruchomienia przez Tomasza (ChatGPT Deep Research / Gemini DR; najlepiej 2 narzedzia
krzyzowo). Cel: subagent X przestaje byc slepy - per-post metryki wlasnych publikacji do
PostgreSQL na VPS, najtaniej i bez ryzyka konta. Wyniki -> BE (kolektor = build po raporcie).

KLUCZOWY TROP DO WERYFIKACJI: devcommunity.x.com "X API Pricing Update: Owned Reads Now $0.001
(effective April 20, 2026)" - jesli odczyt WLASNYCH postow jest pay-per-use, oficjalna droga
moze kosztowac grosze zamiast $200/mies.

--- PROMPT (wklej calosc) ---

I run a single X (Twitter) Premium account (@handle, under 1000 followers, ~100-150 own posts
per month) and need PER-POST metrics of MY OWN posts only (impressions, likes, replies,
reposts, bookmarks, link clicks if available, profile visits, new follows) collected DAILY by
a self-hosted Python service on a small Linux VPS into PostgreSQL. Historically the X API read
access required the $200/month Basic tier, which is not acceptable. Research the CHEAPEST
RELIABLE ways to get these metrics in 2026 and give me a decision-ready report.

Investigate and verify with primary sources:

1. **X API pay-per-use "Owned Reads"**: there was an official announcement "X API Pricing
   Update: Owned Reads Now $0.001 (+ other changes) effective April 20, 2026" on
   devcommunity.x.com. Verify: what exactly is an "owned read", which endpoints it covers
   (GET /2/tweets, GET /2/users/:id/tweets with tweet.fields=public_metrics,non_public_metrics,
   organic_metrics), which auth (OAuth 1.0a user context? OAuth2?), which API tier is required
   to enable pay-per-use, whether non_public_metrics (impressions, url clicks, profile visits)
   are included for one's own tweets, billing setup, and the REAL monthly cost for ~150 posts
   polled once daily for 30 days each (~4500 reads/month).

2. **X Premium Analytics UI**: what does the native analytics dashboard (Account Analytics)
   offer for Premium in 2026, is there ANY export (CSV) per post, and are there internal JSON
   endpoints that a logged-in browser session calls (name them if documented by practitioners).

3. **Automating one's OWN analytics with one's own session** (Playwright/headless on a VPS
   using own auth cookies): documented practitioner experience in 2024-2026 - account
   suspension risk for reading ONE'S OWN data at low frequency (1x/day), ToS clauses that
   apply, mitigations (residential IP vs VPS IP, rate, fingerprint), and whether anyone runs
   this stably long-term. Honest risk assessment, not hand-waving.

4. **Third-party tools with metrics API/export included in cheap plans**: Typefully, Hypefury,
   Buffer, Publer, Metricool, Fedica and similar - which of them (a) collect per-post X metrics
   on their side, (b) expose them via THEIR API, webhook, CSV or email report that a script can
   ingest, (c) at what monthly price, (d) how reliable/complete vs native analytics.

5. **Fallbacks**: X email notifications/digests parsing; what metrics are visible publicly
   without login on post pages (like/repost/reply counts via oEmbed or syndication endpoints)
   and whether impressions appear there.

Finish with: comparison table (path | metrics coverage | setup effort | monthly cost | ToS/ban
risk | reliability), a TOP recommendation for a solo self-hosted collector with concrete
endpoints/fields and polling design, and a fallback plan. Cite sources with dates; flag
anything you could not verify in primary sources.
