# X per-post analytics research notes

## Official X API pricing and Owned Reads

- **Official announcement:** X Developer Community, 16 April 2026, "X API Pricing Update: Owned Reads Now $0.001 + Other Changes Effective April 20, 2026." It defines Owned Reads as requests by a developer's own app for their own posts, bookmarks, followers, likes, lists, and more. It explicitly lists `GET /2/users/{id}/tweets` among qualifying endpoints, effective 20 April 2026. URL: https://devcommunity.x.com/t/x-api-pricing-update-owned-reads-now-0-001-other-changes-effective-april-20-2026/263025
- **Current official pricing docs:** X API is credit-based, pay-per-use, with no subscriptions. Owned Reads are $0.001 per returned resource when `{id}` matches the authenticated user and that user owns the developer app. `GET /2/users/{id}/tweets` qualifies. Docs say duplicate resources are generally deduplicated within each 24-hour UTC window, but call it a soft guarantee. URL: https://docs.x.com/x-api/getting-started/pricing
- Standard Post reads are $0.005 per returned resource. Pay-per-use plans are capped at 2 million Post reads per monthly billing cycle.
- Credits are prepaid in the Developer Console. A saved payment method is required for auto-recharge. Developers can configure a billing-cycle spending limit. Current per-endpoint rates are in the console.
- The usage endpoint docs state prerequisites: approved developer account, project/app, and bearer token. It demonstrates `GET /2/usage/tweets` with a bearer token. URL: https://docs.x.com/x-api/usage/introduction

## Initial cost calculation

- Assuming 150 posts are returned each day for 30 days: 4,500 returned post resources monthly.
- At $0.001 per qualifying Owned Read: **$4.50/month** before taxes and any non-qualifying reads.
- If 24-hour per-resource deduplication works and all requests occur only once per UTC day, there is no material same-day duplication. If collection fetches only post IDs requiring snapshots, daily bulk retrieval remains 4,500 resources over 30 days.
- Need verify whether `GET /2/tweets` qualifies, availability of `organic_metrics` and `non_public_metrics`, required authentication, and minimum credit purchase or plan activation.

## Evidence status

- Primary-source verified above.
- Pending official reference pages for endpoint field availability, authentication, and data owner restrictions.

## Source retrieval dates

- Official announcement published 2026-04-16; retrieved 2026-07-19.
- Documentation retrieved current on 2026-07-19.


## Official API endpoint and private-metric verification

- The official metrics guide states that public metrics are accessible with any authentication. It lists `public_metrics.impression_count`, `like_count`, `reply_count`, `retweet_count`, `quote_count`, and `bookmark_count`. It lists private `non_public_metrics.url_link_clicks`, `non_public_metrics.user_profile_clicks`, and `non_public_metrics.engagements`. Private metric availability is restricted to a post owner using user-context authentication. URL: https://docs.x.com/x-api/fundamentals/metrics
- The same guide gives the crucial **30-day availability limit**: `non_public_metrics`, `organic_metrics`, and `promoted_metrics` are available only for posts created within the last 30 days. It explicitly says OAuth 1.0a user context **or** OAuth 2.0 user context can retrieve private metrics for posts the authenticated user owns.
- `organic_metrics` provides a non-promoted breakdown and includes impressions, likes, replies, reposts, URL clicks, and profile clicks. `public_metrics` is documented as combined public total for organic and promoted activity. Exact field semantics must be kept separate in the final design.
- The official post lookup integration guide says `non_public_metrics`, `organic_metrics`, and `promoted_metrics` require user-context authentication. OAuth 2.0 Authorization Code with PKCE and OAuth 1.0a User Context both can access private metrics for the authorized user’s posts. URL: https://docs.x.com/x-api/posts/lookup/integrate
- The endpoint reference for `GET /2/users/{id}/tweets` allows Bearer Token, OAuth 2.0 user token (`tweet.read`, `users.read`), or OAuth 1.0a user token. Its supported `tweet.fields` includes `public_metrics`, `non_public_metrics`, and `organic_metrics`, and its `max_results` range is 5–100. URL: https://docs.x.com/x-api/users/get-posts
- `GET /2/tweets` supports up to 100 IDs and the same authentication options, but it is **not included** in the explicit qualifying endpoint list in the pricing page or April announcement. The final report should state this conservatively: only `/2/users/{id}/tweets` has explicit official Owned Read coverage. Do not assume own-post multi-lookup is $0.001 without confirming actual console billing or staff confirmation. Official reference: https://docs.x.com/x-api/posts/get-posts-by-ids
- Pay-per-use launch announcement (6 February 2026) says public-utility apps retain scaled free access, recently active Legacy Free users receive a one-time $10 voucher, and Basic/Pro subscribers can opt into PPU. It does **not** say that a Basic subscription is required for a new PPU app. URL: https://devcommunity.x.com/t/announcing-the-launch-of-x-api-pay-per-use-pricing/256476
- Current "Make Your First Request" guide says a developer account with app credentials is required. Current usage docs list an approved developer account, Project and App, and Bearer Token as prerequisites. Together with the current pricing page's "no subscriptions" language, the primary-source conclusion is: developer approval, app/project, and prepaid credits are required; no $200/month Basic tier is documented as required for PPU. URL: https://docs.x.com/x-api/getting-started/make-your-first-request

## Native analytics UI and CSV export

- Official X Business Analytics page says the **Post Activity Dashboard (PAD)** provides metrics for every post, explicitly listing seen, reposted, liked, and replied counts. It says a user can adjust the date range and export data as a CSV. URL: https://business.x.com/en/advertising/analytics
- The same official page describes Account Home, PAD, Video Activity Dashboard, and a Business Insights Dashboard. It does not state that these views require X Premium, nor does it enumerate link clicks, profile visits, bookmarks, or per-post follows in the CSV export.
- Direct navigation to `https://x.com/i/account_analytics` on 19 July 2026 redirects an unauthenticated browser to X login. It is therefore a logged-in account feature, but this unauthenticated check cannot verify exact Premium entitlement or current export columns.

## Open questions still requiring verification

- Minimum credit-purchase amount or whether credits can be purchased below $5/$10.
- Whether PPU access is instant after developer approval in a newly created app, or whether some approval gate delays it.
- Whether the current logged-in `x.com/i/account_analytics` interface is the same as the legacy Analytics PAD and whether its download emits direct CSV or another format.
- Internal GraphQL or JSON operation names used by the current UI.


## Phase 2: Native UI and browser-path evidence

The official X Business Analytics page confirms that the legacy/natively branded **Post Activity Dashboard** offers metrics for every post and a date-adjustable CSV export. It explicitly names views, reposts, likes, and replies. This is primary-source evidence for a native CSV path, but it does not state the exact CSV schema, an automation interface, or a Premium-only entitlement. Source: https://business.x.com/en/advertising/analytics (retrieved 2026-07-19).

A direct unauthenticated visit to `https://x.com/i/account_analytics` redirected to login on 2026-07-19. That establishes an authenticated account requirement but does not establish feature availability, export columns, or Premium tier gating. Do not overstate it.

A practitioner repository, cross-mind/crossmind-cli, shows current use of `https://x.com/i/api/graphql` with `auth_token` and `ct0` cookies, routed through a `curl_cffi` bridge using Chrome TLS. Its July 17, 2026 commit history documents credential fallbacks, guest-cookie downgrades, and a failure caused by a non-existent home-timeline REST endpoint. It supports the conclusion that private web-client paths are brittle and cookie/session dependent. It **does not document an Account Analytics-specific operation name or prove access to private post analytics**. Source: https://github.com/cross-mind/crossmind-cli (observed 2026-07-19).

No primary source or credible 2024-2026 practitioner source has yet been found that names a stable, public, Account Analytics-specific GraphQL operation for per-post metrics. The final report should name the generic web-client base only (`/i/api/graphql`) and label analytics operation names as unverified rather than inventing them.


## Official Premium Analytics entitlement and export evidence

An official `@premium` post, rendered on X and retrieved on 2026-07-19, states: "We've just released a few improvements to Analytics! Subscribe to Premium to see your stats." The embedded/quoted post from Zach Warunek dated 1 November 2024 states: "You can now select a time range on the Account Analytics content tab! And for a little bonus that many have asked for, you can now export all of your total post metrics within the selected time range." Source: https://x.com/premium/status/1852537530706731244.

The screenshot visible in that official post shows Account Analytics with tabs **Overview**, **Audience**, and **Content**. Its content table visibly contains columns including **Post**, **Date**, **Impressions**, **Likes**, **Replies**, and **Reposts**. The official source does not show the complete export schema or prove inclusion of bookmarks, link clicks, profile clicks, or per-post follows.

This is the strongest available official evidence that Premium grants Account Analytics and an export for all total post metrics in a selected date range. It is dated November 2024, so the final report must phrase it as an official feature announcement still discoverable on X, not as a current 2026 UI field-by-field guarantee.

## Current source register

1. X Developer Community, 16 Apr 2026: Owned Reads announcement — https://devcommunity.x.com/t/x-api-pricing-update-owned-reads-now-0-001-other-changes-effective-april-20-2026/263025
2. X API pricing documentation — https://docs.x.com/x-api/getting-started/pricing
3. X API metrics documentation — https://docs.x.com/x-api/fundamentals/metrics
4. X API post lookup integration guide — https://docs.x.com/x-api/posts/lookup/integrate
5. X API user timeline reference — https://docs.x.com/x-api/users/get-posts
6. X API multi-post lookup reference — https://docs.x.com/x-api/posts/get-posts-by-ids
7. X API getting access guide — https://docs.x.com/x-api/getting-started/getting-access
8. X OAuth 2 PKCE docs — https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code
9. Official X Business Analytics page — https://business.x.com/en/advertising/analytics
10. Official @premium Analytics/export post — https://x.com/premium/status/1852537530706731244
11. Practitioner crossmind repository (brittleness evidence only) — https://github.com/cross-mind/crossmind-cli
12. X Activity API docs — https://docs.x.com/x-api/activity/introduction


## Official Premium Analytics scope from launch and video update

Official @premium launch post, dated 8 June 2024 and retrieved 2026-07-19, says "Subscribe to Premium to unlock advanced account analytics." Its image says "Upgrade to Premium for daily growth insights" and visibly lists: **Impressions**, **Engagement rate**, **Profile visits**, **Link clicks**, **New followers**, **Replies**, **Likes**, and **Reposts**. The visual also shows selectable periods: 7D, 28D, 3M, and 1Y. Source: https://x.com/premium/status/1799251492391846189.

Official @premium video update, dated 13 January 2025 and retrieved 2026-07-19, says: "Another major addition to Premium Analytics! Check out the new Video Analytics tab - track key video metrics and completion rates. Sort videos by views and publish date. More to come. Available now in Premium Hub." Its embedded announcement says `Premium > Analytics > Video` and confirms video views, watch time, completion rate, average watch time, charts over time, and sorting. Source: https://x.com/premium/status/1878891474223571100.

The official evidence supports this conservative 2026 description: Premium Account Analytics is an interactive dashboard with overview/account growth metrics, content-level tabular post metrics, audience content (tab visible in the official 2024 screenshot), and a video analytics tab. The headline account-level metrics include impressions, engagement rate, profile visits, link clicks, new followers, replies, likes, and reposts. The Content tab/export displays at minimum post, date, impressions, likes, replies, and reposts. **No official source found shows bookmarks or proves that native CSV includes link clicks, profile visits, or new follows per individual post.**

The native UI meets interactive review and manual export needs. It is not a documented programmatic feed, and the current public product evidence does not establish a safe or durable direct URL for automatic CSV download.


## Phase 3: Session automation policy and risk evidence

### Primary policy position (retrieved 2026-07-19)

The X Terms of Service states that users may not access services except through currently available published interfaces, explicitly stating that they cannot scrape the services without X's express written permission, work around technical limits, or disrupt service operation. It also reserves enforcement rights that include discontinuing access. Source: https://x.com/tos.

The official X Automation Rules are marked **Updated April 2026**. They say: "Use non-API-based forms of automation, such as scripting the X website. The use of these techniques may result in the permanent suspension of your account." The same page says X users are responsible for activities conducted through their account or associated applications and that action can include account suspension. Source: https://help.x.com/en/rules-and-policies/x-automation.

The current X Developer Guidelines calls out an "Official API Only?" requirement and says the non-API browser-automation scenario can result in **permanent suspension**. The data/research table explicitly marks an app that "scrapes X via browser automation (not API)" as not allowed, saying "Permanent suspension - API only." Source: https://docs.x.com/developer-guidelines.

### Practitioner evidence (not causal proof)

`mikf/gallery-dl` issue #6020 (14 Aug 2024) contains multiple user reports of X account suspensions while downloading media from a few profiles and reports of suspensions during high-volume activity. The reports are self-selected anecdotes, involve workloads incomparable with a once-daily own-analytics read, and do not establish causality. They demonstrate that accounts have been suspended in connection with cookie-based scraping workloads. Source: https://github.com/mikf/gallery-dl/issues/6020.

`mikf/gallery-dl` issue #5532 (30 Apr 2024) reports aggressive rate limiting, forced logouts, and account suspensions when scraping X search. One reporter said attempts from different IP addresses and user-agent changes did not stop quick suspensions. The repository owner later added rate-limit waiting behavior. This is **not a recommended mitigation** and is unrelated to an own-data collector, but it is useful evidence that changing IPs or headers is not a durable safety control. Source: https://github.com/mikf/gallery-dl/issues/5532.

### Provisional risk conclusion

There is no current X policy exception for "only my own data," low frequency, or a personal session cookie. A once-per-day view has a smaller operational footprint than the cited scraping cases, so its detection likelihood is plausibly lower, but its **policy status remains prohibited**. Risk is therefore not quantifiable, yet non-zero and potentially severe because the stated consequence includes permanent suspension. No legitimate choice of VPS IP, residential IP, fingerprint spoofing, or cookie rotation changes that policy status. Do not propose proxy or fingerprint-evasion tactics in the report.

No credible 2024-2026 source was found that independently demonstrates an owner-operated, Playwright-based X Analytics collector running stably long term without locks or policy exposure. The final report should say "not verified," rather than extrapolating from scraper testimonials.


## Phase 4: Third-party tools - primary pricing-page validation

- **Typefully:** Its official pricing page confirms that Pro includes `X analytics`, detailed metrics, profile conversion rate, CSV download, API and MCP integrations. The extracted page did not render the numeric prices. Therefore the report may cite the feature inclusion as primary-source verified, but mark the `$10/month` figure from the parallel research as **price not independently rendered in main-source extraction**, subject to checkout confirmation. URL: https://typefully.com/pricing.
- **Hypefury:** The official pricing page lists Essentials at `$6/month` for one channel and describes post analytics, like and retweet counts, follower growth, profile clicks, and impressions. Crucially, its FAQ explicitly says: **"Does Hypefury still support 𝕏/Twitter? Nope! Hypefury no longer supports 𝕏 :("** It is therefore not a candidate for current X collection, despite legacy X-related product copy remaining on the page. URL: https://hypefury.com/features-pricing/.
- **Buffer:** The official pricing page lists Essentials at `$5/month per channel`, billed `$60 yearly`, and includes Advanced analytics plus API access (3 API keys, 7,500 API requests per month). It lists X as a connectable channel. This verifies product pricing and general analytical/API capability but does not alone establish that Buffer’s API exposes X Insights data. URL: https://buffer.com/pricing.
- **Publer:** The official plans page could not be cleanly parsed because of a long consent payload. Do not treat its plan price as independently confirmed until its official help and/or pricing page is checked by a secondary route. URL: https://publer.com/plans.

This validation overturns the tentative Hypefury result. Final table should place **Hypefury: not viable for X, current official FAQ says no X support**.


### Typefully - primary docs verified (retrieved 2026-07-19)

Typefully’s analytics help article, updated **2026-01-26**, says its X analytics cover posts made directly on X as well as those published through Typefully. It defines engagements as likes, retweets, replies, profile clicks and link clicks, and says it cannot access media views or opens through the X API. It exports analytics chart data as CSV. Its documented refresh schedule is hourly during the first two hours, every six hours through day two, and a final refresh on day three. It says an extended copy beyond the default last 30 days requires support. This makes Typefully potentially suitable for **near-term final snapshots**, but not a verified replacement for daily per-post day-by-day history over 30 days. Source: https://support.typefully.com/en/articles/8718148-analytics-page-metrics.

Typefully's public API documentation exposes `GET /v2/social-sets/{social_set_id}/analytics/x/posts`, is currently X-only, supports date ranges up to 366 days and a 100-post page size, and has `include_replies=true`. The returned normalized post metrics explicitly include impressions, comments/replies, likes, profile_clicks, quotes, shares/reposts, total engagement, optional link_clicks, and optional saves/bookmarks. It does **not** document per-post new follows. It also exposes `GET /v2/social-sets/{social_set_id}/analytics/x/followers`, a daily *total follower count* series, not exact follower-acquisition attribution per post. API key authentication is bearer-key based. Source: https://typefully.com/docs/api.

The Typefully official docs provide unusually strong evidence for API ingestion. However, their own stated refresh policy means the script can only pull what Typefully chooses to refresh, rather than schedule raw X metrics at a user-defined daily cadence through 30 days.


### Buffer, Publer, Metricool, and Fedica - primary docs checked (retrieved 2026-07-19)

**Buffer:** Official Insights documentation says paid plans can export the current filtered analytics view as a ZIP containing `summary.csv`, `posts.csv`, and `timeseries.csv`, or as Markdown/PDF. The per-post export includes post ID, time, excerpt, URL, tags, and every metric the specific channel reports; its stated examples include impressions, reach, reactions, comments, shares, saves and engagement rate. Daily follower data is in the time-series export. The documentation does not, in the extracted section, certify a dedicated public *analytics* API endpoint. Its general product API is not automatically evidence that Insights data is API-readable. Source: https://support.buffer.com/article/950-using-insights-in-buffer.

**Publer:** Its official analytics documentation states it uses the social networks' official APIs, automatically pulls data daily, can manually Sync Insights in real time, and analyzes posts published both inside and outside Publer once posts are synced. It warns that account insights begin only from the moment of upgrade. The visible extraction did not reach its X/Twitter-specific metrics section, so do not claim those metrics until a targeted extraction is obtained. Source: https://publer.com/help/en/article/what-metricsanalytics-are-gathered-for-each-social-network-1ibwz3q/.

**Metricool:** Its dedicated X/Twitter add-on guide states that the service uses a paid add-on because X charges for every API connection. A premium plan (Starter or higher) is mandatory, plus `€10/$10 per month` per connected X account as of **2026-07-13**. The new add-on alone costs €120/$120 annually, and prior customers may retain a $5/month legacy price. Therefore a new user’s all-in price is the Starter plan **plus** $10/month, not the Starter plan alone. Source: https://help.metricool.com/your-guide-to-the-x-twitter-add-on-wt5wy.

**Fedica:** A vendor-authored post dated **2024-12-09** claims official API access, own-post analytics including link and profile clicks, and export to Excel/Google Sheets/CSV/PDF. It positions its Grow plan for own-post analytics and Research for other-account/listening analytics. These are product claims rather than independent performance proof. Pricing and a public customer API entitlement remain unverified from this source. Source: https://fedica.com/blog/twitter-tweet-analytics-x/.


### Publer - primary pricing and metrics now verified (retrieved 2026-07-19)

Publer’s public pricing page shows Professional at **$5/month billed monthly** or **$4/month billed yearly** for one social account, and Business at **$10/month monthly** or **$8/month yearly**. Professional includes X integration; Business adds analytics insights and reports plus access to the Publer API. The page states that X accounts require a paid subscription because of X Enterprise API cost. Therefore the minimum plan to get X analytics UI/export is Business, while a programmatic route is also Business, subject to validating the API's analytic read scopes. VAT is not included. Source: https://publer.com/plans (retrieved 2026-07-19).

Publer’s official X/Twitter metric list confirms per-post reach/views, video views, likes, replies, reposts and quotes combined as shares, post clicks defined as clicks on the name, handle, or author profile photo, link clicks, engagement rate, and click-through rate. It documents historical follower count from the time it begins collecting. It does **not** document X bookmarks, a direct profile-visits metric separate from post clicks, or per-post new follows. Source: https://publer.com/help/en/article/what-metricsanalytics-are-gathered-for-each-social-network-1ibwz3q/.


### Metricool - primary pricing and metric coverage verified (retrieved 2026-07-19)

Metricool's pricing page says the lowest paid tier is Starter **from $20/month** (or **from €16/month** in its displayed annual pricing) for up to five brands, and its X add-on guide adds **$10/€10 per month** per connected X account. Thus the stated starting all-in amount is **from $30/month** or **from €26/month**, before VAT, subject to the page's selected billing cadence. Starter has *reduced* Twitter/X analytics and only displays posts published through Metricool’s planner. The Advanced plan begins **from $53/month** (or €43/month in the displayed annual pricing) plus the add-on and includes complete X analytics and Metricool API access. The pricing page states a 30-day metric-storage limit for X/Twitter even on premium plans. Sources: https://metricool.com/pricing/ and https://help.metricool.com/your-guide-to-the-x-twitter-add-on-wt5wy.

Metricool's X metrics guide verifies Advanced/Custom includes per-post impressions, likes, reposts, replies, quotes, link clicks, profile clicks, video views, bookmarks, follows and unfollows. It also states that X does not expose every interaction through the API, so its engagement total is not a full native-X engagement total. The guide says post-level data is accumulated from publication up to yesterday, and Starter only lists posts published from Metricool's planner. Metrics cover organic data, with promotion status noted but ads not included. Source: https://help.metricool.com/x-twitter-metrics-g4v9t.


### Fedica - primary pricing and API distinction verified (retrieved 2026-07-19)

Fedica’s public pricing page lists Publish at **$10/month billed annually** or **$15/month billed monthly** for one account per platform. It labels Publish as "Advanced Publishing with Analytics" and lists advanced engagement metrics, including impressions, link clicks and hashtag clicks, while its comparison table advertises analysis export subject to platform limits. The public matrix is not explicit enough to verify every own-post X metric or whether CSV export is included at Publish rather than a higher tier. Its vendor blog claims CSV/Excel/Google Sheets/PDF exports, but that is marketing material, not a contract-level feature matrix. Source: https://fedica.com/signup/ and https://fedica.com/blog/twitter-tweet-analytics-x/.

Fedica's official public API documentation describes a **Publishing API only**: endpoints schedule posts, list pipelines/accounts, and upload media. It documents no read endpoint for analytics, no analytics webhook, and no analytics export API. Thus an automated collector could not be based on a verified Fedica analytics API. It may be able to ingest a manually exported file, but a machine-readable scheduled export is not documented. Source: https://fedica.com/social-media/publishing-api.


### Buffer - API evidence verified (retrieved 2026-07-19)

Buffer's official developer guide says its **experimental** Post Metrics feature is available only for personal workflows using a personal API key. The GraphQL `post` query exposes `metrics { type name value unit }` and `metricsUpdatedAt`; the API endpoint is `https://api.buffer.com`. It states metric values are collected on a **daily cadence** and a newly sent post can take up to about 24 hours to appear. It calls its metric surface experimental and says API field shapes and normalization rules may evolve. Sources: https://developers.buffer.com/guides/post-metrics.html and https://developers.buffer.com/examples/get-post-metrics.html.

For X, Buffer's documented normalized types confirm likes as `reactions`, retweets/reposts as `reposts`, and replies as `comments`; impressions may be reported where X returns them. The guide calls saves/follows network-specific to Instagram/Pinterest and quotes network-specific to Threads. It does **not** document X link clicks, profile clicks, bookmarks, or per-post follows in its public API, so those cannot be treated as available. The guide says Buffer collects data from the social networks it **publishes to**, so current documentation does not verify that it imports per-post metrics for existing/directly published X posts. This is a material limitation versus the stated requirement for all own posts.

Buffer's support article says the post-metrics API is limited and experimental. It also says `insightsRead` exists for a personal API key but cannot be granted to an OAuth App Client due to platform terms. That supports a self-hosted personal collector, but not a general SaaS integration. Source: https://support.buffer.com/article/859-does-buffer-have-an-api.


## Fallback research: email, public views, and embeds

X's official email-preferences documentation says activity emails may notify/refer to reposts, likes, mentions, replies, and new follows. Since June 2017 it sends a digest of unread activity rather than one email per event, and explicitly warns users may not receive a notice for every interaction. It does not document impressions, link clicks, profile visits, bookmarks, exact post-level totals, or a machine-readable analytics digest. Therefore parsing X email is **not reliable for daily per-post metrics**. Source: https://help.x.com/en/managing-your-account/updating-email-preferences.

X's official view-count help page says view counts are displayed next to the analytics icon and post timestamp and are visible to anyone on X. It confirms public posts can show total views, but does not document an unauthenticated read API, exports, or a guarantee that the web page is accessible without login. It does not make other private analytics public. Source: https://help.x.com/en/using-x/view-counts.

Official X oEmbed documentation states `https://publish.x.com/oembed` is unauthenticated and returns **an HTML snippet** for an embedded post or timeline. Its example response exposes embed metadata such as HTML, URL, provider, type, width/height and cache age, not an analytics schema. The response markup may change over time. Thus oEmbed is an embed-rendering service, not a supported source of likes/replies/reposts/impressions. Sources: https://docs.x.com/x-for-websites/oembed-api and https://docs.x.com/x-for-websites/embedded-posts/overview.


A non-authenticated test on 2026-07-19 of the commonly cited but **unofficial** endpoint `https://cdn.syndication.twimg.com/tweet-result?id=1799251492391846189&lang=en` returned HTTP 200 with an empty `{}` payload for a public official @premium post. It therefore did not provide usable metrics in this test. X does not document this endpoint in its current public developer documentation. The final report should classify syndication endpoints as unsupported/brittle and not a reliable collector fallback, rather than treating historic JSON schemas as an API contract.


## New-follower collection: official routes verified

The official v2 Account Activity API documentation confirms that Pay Per Use can receive real-time Follows and Unfollows for an owned/subscribed account through a publicly accessible HTTPS webhook. Pay Per Use permits up to 3 unique subscriptions and 1 webhook. The quickstart says it requires an approved developer account, a separate application for Account Activity API access, a public HTTPS webhook, and OAuth 1.0a three-legged user authentication to subscribe the account. Sources: https://docs.x.com/x-api/account-activity/introduction and https://docs.x.com/x-api/account-activity/quickstart.

A `follow_events` payload identifies the actor and target with a timestamp. It contains **no post ID**, so this route produces exact account-level follow/unfollow events only, not new follows attributable to a particular post. It also adds operational and approval complexity. The official Post data dictionary lists `non_public_metrics` as `impression_count`, `user_profile_clicks`, `url_link_clicks`, and `engagements`; it does not list a post-level follows metric. Source: https://docs.x.com/x-api/fundamentals/data-dictionary.

`GET /2/users/{id}/followers` can list followers using bearer, OAuth 2 user context (`follows.read`, `tweet.read`, `users.read`), or OAuth 1.0a, but it is a state-list read and not an event ledger. It can support daily count/diff logic at under 1,000 followers but cannot prove follows were caused by a particular post. Source: https://docs.x.com/x-api/users/get-followers.


## Cost and billing validation

The current official X pricing documentation describes prepaid credits, optional auto-recharge with a saved payment method, a configurable billing-cycle spending limit, and **"No contracts, subscriptions, or minimum spend."** Therefore there is no publicly documented mandatory $200 Basic tier or minimum ongoing spend for the pay-per-use route. Source: https://docs.x.com/x-api/getting-started/pricing (retrieved 2026-07-19).

Exact calculation for the stated volume: 150 returned post resources/day × 30 days = **4,500 Owned Reads/month**. At $0.001 each, the variable cost is **$4.500/month** before VAT/tax and any non-qualifying calls. The same volume at the standard post-read price of $0.005 would be **$22.500/month**. One daily own-profile user lookup would add 30 owned-user reads or **$0.030/month**, taking the simple total to **$4.530/month**. A full daily follower-list scan of 1,000 follower resources would add 30,000 owned-user reads or **$30.000/month**, and is not recommended when exact follower events can instead use AAA after access approval.


Typefully pricing was additionally checked in a live browser on 2026-07-19. Its public price components rendered **Free $0, Pro $8, Business $18 per social set per month**. The Pro card includes X analytics, while the page’s analytics section lists detailed metrics and CSV download. The pricing page’s public text also advertises API/MCP capability; Typefully’s API documentation is the authority for the analytics endpoint. Source: https://typefully.com/pricing.

