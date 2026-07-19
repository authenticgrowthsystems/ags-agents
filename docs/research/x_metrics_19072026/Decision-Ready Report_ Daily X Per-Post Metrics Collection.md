# Decision-Ready Report: Daily X Per-Post Metrics Collection

**Scope.** One X Premium account, under 1,000 followers, roughly 100 to 150 owned posts monthly, and a self-hosted Python-to-PostgreSQL collector. Research was completed on **19 July 2026**. Prices are vendor list prices and may exclude VAT.

## Executive decision

The best route is **X API Pay-Per-Use using Owned Reads**. Use `GET /2/users/{id}/tweets` with OAuth user context, daily snapshots, and a 30-day retention window for private metrics. It is policy-compliant, directly supports the requested click and impression fields, and costs about **$4.50 per month** at the stated volume. [1] [2] [3] [4]

Do not build a Playwright, cookie, or headless-browser collector against X Analytics. X explicitly prohibits scripting the website and says it can result in permanent suspension. A residential proxy, altered browser fingerprint, or lower request rate does not create a policy exception. [11] [12] [13]

Use Premium Account Analytics CSV only as a manual, policy-compliant fallback. It is useful for validation and short-term recovery, but its documented current export schema does not prove every requested per-post field. [8] [9] [10]

| Decision | Recommendation | Why it wins |
|---|---|---|
| **Primary collector** | X API Pay-Per-Use Owned Reads | Lowest verified compliant operating cost with native metric fields and daily raw snapshots. |
| **Authentication** | OAuth 2.0 Authorization Code with PKCE and refresh token | Supported for owned private metrics and operationally cleaner than storing a browser session. [3] [5] [6] |
| **Primary endpoint** | `GET /2/users/{id}/tweets` | Explicitly listed for Owned Read treatment. Avoid assuming the bulk post lookup receives that price. [1] [2] [4] |
| **New-follow data** | Optional Account Activity API webhook for account-level events | Exact follows and unfollows, but no post attribution. Add only if gross follow events matter. [7] |
| **Fallback** | Manual Premium Analytics CSV import, weekly or every few days | Compliant, low additional cost, and preserves a practical recovery path. [8] [9] |

## 1. X API Pay-Per-Use: verified answer

### What an Owned Read is

X announced on **16 April 2026** that Owned Reads would cost **$0.001** from **20 April 2026**. The documentation defines an Owned Read as a request by the developer’s own app for data owned by that developer, including their posts, bookmarks, followers, likes, and lists. [1] [2]

The qualifying identity condition matters. The requested `{id}` must match the authenticated user, and that user must own the developer app. This is not a discounted price for any public post merely because the caller can view it. [2]

The official announcement and current pricing documentation explicitly identify `GET /2/users/{id}/tweets` as an Owned Read route. X bills by returned resource, not simply by HTTP request. [1] [2]

### Endpoints, fields, authentication, and price certainty

| Item | What is verified | Decision consequence |
|---|---|---|
| `GET /2/users/{id}/tweets` | Explicit Owned Read coverage. It supports `public_metrics`, `non_public_metrics`, and `organic_metrics`; `max_results` is 5 to 100. [1] [4] | **Use this endpoint** as the collector’s primary read path. |
| `GET /2/tweets` | It supports the same metric fields and user-context authentication. It is not explicitly named in the Owned Read lists reviewed. [4] [5] | Do not assume $0.001 billing. Treat it as potentially standard post-read pricing until the console or X staff confirms otherwise. |
| `public_metrics` | Includes impressions, likes, replies, reposts, quotes, and bookmarks in the current data dictionary. [3] | Store it for public-total reconciliation and terminal snapshots. |
| `non_public_metrics` | Includes impressions, URL link clicks, user-profile clicks, and engagements. It is available only to the post owner with user-context authentication. [3] [5] | This is the required source for link clicks and profile visits. |
| `organic_metrics` | Returns the organic-context version of relevant performance values for an owned post. [3] | Store it separately from public totals, especially if promotion is introduced later. |
| OAuth 1.0a user context | Supported for owned private metrics. [3] [5] | Valid fallback authentication method. |
| OAuth 2.0 user context | Supported for owned private metrics. Authorization Code with PKCE supports user consent and refresh-token operation. [3] [5] [6] | Recommended for the VPS collector. |
| App-only Bearer token | Can read public data, but not the owner-only fields. [3] [5] | Insufficient for clicks and private impressions. |

> **Important retention constraint.** `non_public_metrics`, `organic_metrics`, and promoted metrics are available only for posts created within the prior 30 days. A collector started later cannot reconstruct those private snapshots for older posts. [3]

### Billing setup and real monthly cost

X’s current API model is prepaid, credit-based, and has **no subscriptions or minimum spend** documented. A developer account, project and app are still required. Credits are purchased in the Developer Console, where a payment method supports auto-recharge and a billing-cycle spending cap. [2] [5]

The official wording proves no mandatory $200 Basic subscription. It does **not** publish the smallest possible checkout top-up increment, so confirm that small purchase detail in the console before implementation. [2]

| Scenario | Returned resources each month | Unit price | Variable API cost |
|---|---:|---:|---:|
| 150 active owned posts, one snapshot daily for 30 days | 4,500 post resources | $0.001 Owned Read | **$4.500** |
| Same volume if priced as standard post reads | 4,500 post resources | $0.005 | **$22.500** |
| Add one daily own-profile read for follower-count history | 30 user resources | $0.001, if it receives Owned Read pricing | **$0.030** incremental |
| Core posts plus one daily profile read | 4,530 resources | $0.001 | **$4.530** |
| Daily full scan of 1,000 followers | 30,000 additional user resources | $0.001 | **$30.000** incremental |

The stated **$4.50/month** is the correct steady-state estimate for 4,500 qualifying post resources. Taxes, accidental standard reads, and any future X price change remain outside that estimate. [1] [2]

Avoid a daily full follower-list diff. It costs more than the post collector and still cannot attribute a follow to a specific post. A daily profile count gives net follower change cheaply, while the Account Activity API gives exact follow and unfollow events if that distinction justifies its setup effort. [7]

### Which requested metrics are available

| Requested metric | Native API field or route | Availability for this design | Important limitation |
|---|---|---|---|
| Impressions | `public_metrics.impression_count`; also owner-only private and organic contexts | Yes | Retain all contexts separately. Private and organic fields expire after 30 days. [3] |
| Likes | `public_metrics.like_count`; organic counterpart | Yes | Public total and organic value can differ if promotion is used. [3] |
| Replies | `public_metrics.reply_count`; organic counterpart | Yes | Counts are snapshots, not an event stream. [3] |
| Reposts | `public_metrics.retweet_count` in the current API data dictionary; organic counterpart | Yes | API field naming retains legacy terminology. [3] |
| Bookmarks | `public_metrics.bookmark_count` | Yes | Store the documented public metric exactly as returned. [3] |
| Link clicks | `non_public_metrics.url_link_clicks`; organic context where returned | Yes, for owned posts | Requires OAuth user context and a post younger than 30 days. [3] [5] |
| Profile visits | `non_public_metrics.user_profile_clicks`; organic context where returned | Yes, for owned posts | This is post-attributed profile clicking, not all profile traffic. [3] [5] |
| New follows attributed to a post | No documented post metric | **No** | Do not infer attribution from timing. [3] [7] |
| New follows for the account | Account Activity `follow_events` | Yes, optional | Exact event but has no post ID. Requires webhook access and OAuth 1.0a subscription. [7] |
| Net follower change | Daily own-user `public_metrics.followers_count` | Yes, optional | Net change combines follows and unfollows. [3] |

## 2. Recommended self-hosted collector design

The collector should be deliberately narrow. It should use the official API once each UTC day, request only the owner’s timeline, and stop reading a post after its private metrics age out. That gives durable snapshots without browser-state risk.

| Component | Concrete design |
|---|---|
| Identity | Resolve and persist the account’s numeric user ID once. Use the same X account as the OAuth user and developer-app owner. [2] [4] |
| OAuth | Register an OAuth 2.0 Authorization Code with PKCE app. Request `tweet.read`, `users.read`, and `offline.access`; encrypt refresh tokens at rest. OAuth 1.0a remains necessary only for Account Activity subscription. [4] [6] [7] |
| Daily query | `GET https://api.x.com/2/users/{id}/tweets?start_time={now_minus_30d}&max_results=100&tweet.fields=created_at,author_id,referenced_tweets,public_metrics,non_public_metrics,organic_metrics` with OAuth 2 user token. Paginate until the 30-day boundary. [4] [5] |
| Cadence | Run once daily after a consistent UTC boundary. The pricing documentation offers duplicate-resource deduplication within a UTC day as a soft guarantee, but do not depend on it for correctness. [2] |
| Storage | Insert an immutable snapshot per `tweet_id`, `observed_at`, and metric namespace. Preserve raw JSON for schema changes and auditability. |
| Completion rule | Poll a post while `created_at >= now - 30 days`. Persist its final private snapshot when it leaves the window. [3] |
| Content scope | Store `referenced_tweets` so replies, quotes, originals, and reposts can be classified. Exclude reposts only if your analysis definition excludes them. [3] [4] |
| Cost guardrail | Alert if returned resources exceed 200 daily or if a response is billed as a non-Owned Read. Set a small credit spending cap, such as $10, then raise only after billing verification. [2] |
| Data-quality rule | Treat a missing private field as unavailable, not zero. Record response errors and field absence explicitly. [3] |

A simple PostgreSQL model is sufficient. Keep a `x_posts` table for immutable post metadata, an `x_post_metric_snapshots` table for observations, and an optional `x_account_daily` table for account-level follower totals. Keep each namespace as separate columns or a versioned JSONB payload.

```text
x_posts
  tweet_id PK | created_at | author_id | post_kind | conversation_id | raw_post JSONB

x_post_metric_snapshots
  tweet_id | observed_at | public_metrics JSONB | non_public_metrics JSONB
  organic_metrics JSONB | request_id | raw_response JSONB
  PRIMARY KEY (tweet_id, observed_at)

x_account_daily
  observed_date PK | followers_count | following_count | post_count | raw_user JSONB

x_follow_events_optional
  event_id PK | occurred_at | source_user_id | target_user_id | event_type | raw_event JSONB
```

## 3. Premium Analytics UI and CSV

Premium Account Analytics is useful, but it is not a documented API substitute. An official Premium post says subscribers can select a time range on the Content tab and export total post metrics for that range. The visible official screenshot confirms at least post, date, impressions, likes, replies, and reposts. [9]

The Premium launch material also shows account-level impressions, engagement rate, profile visits, link clicks, new followers, replies, likes, and reposts. A later Premium update confirms a Video Analytics tab. [10]

The legacy X Business Analytics page says the Post Activity Dashboard offers metrics for every post and CSV export. It explicitly names views, reposts, likes, and replies. [8]

| Native analytics question | Evidence-based answer |
|---|---|
| Is Account Analytics part of Premium? | Official Premium product posts say to subscribe to Premium to see analytics. [9] [10] |
| Can it export? | Yes. Official material describes export of total post metrics for a selected time range, and the Business Analytics page describes CSV export. [8] [9] |
| Does current public evidence prove per-post link clicks, profile visits, bookmarks, and follows in the CSV? | No. Those fields are not shown in the official export screenshot or enumerated in current official export text. [8] [9] |
| Is there a documented automatic CSV endpoint? | No primary source found. Treat native export as manual. |
| Are internal JSON endpoints documented? | No stable Account Analytics-specific operation name was found. The only practitioner evidence found identifies the generic web-client base `https://x.com/i/api/graphql`, not an analytics contract. [30] |

## 4. Why session-based browser automation is the wrong route

X’s Terms prohibit scraping without express written permission. Its Automation Rules, updated April 2026, specifically identify scripting the X website as a practice that may result in permanent suspension. The Developer Guidelines make the same official-API-only distinction. [11] [12] [13]

> “Use non-API-based forms of automation, such as scripting the X website. The use of these techniques may result in the permanent suspension of your account.” [11]

A once-daily own-data read is smaller than bulk scraping. It remains outside the documented exception set, because X offers no exemption for your own account, low frequency, Premium subscription, personal cookies, or a VPS. [11] [12] [13]

Practitioner evidence does not establish a safe long-term pattern. A current repository shows cookie-dependent `/i/api/graphql` interaction and recurring session fallback issues, while public scraper issues report forced logouts and suspensions at unrelated higher volumes. These reports are anecdotal, but they reinforce fragility rather than validating a durable collector. [30] [31] [32]

| Factor | Evidence-based assessment |
|---|---|
| Policy status | Prohibited without X’s express permission. [11] [12] [13] |
| Account-ban risk | **High consequence, unquantified probability.** Official policy explicitly permits permanent suspension. [11] |
| VPS versus residential IP | No X source says either makes browser automation allowed. Practitioner reports do not establish proxy switching as a safety control. [31] [32] |
| Fingerprint or cookie rotation | Not a compliance mitigation. It increases fragility and can resemble evasion. |
| Long-term stable owner-only Playwright evidence | **Not verified.** No credible 2024-2026 evidence found. |
| Recommendation | Do not operate this route for an account you value. |

## 5. Third-party tools: pricing, ingestion routes, and limits

The table separates vendor-side collection from a usable machine ingestion path. A dashboard or CSV can be useful, but it does not equal an API that can feed your PostgreSQL service daily.

| Tool | Lowest relevant list price | Does it collect own X metrics? | Script-ingest route verified | Coverage versus your requirement | Assessment |
|---|---:|---|---|---|---|
| **Typefully Pro** | **$8/month** per social set | Yes, including posts made directly on X. [14] [16] | Yes. X-only API endpoint and CSV. [14] [15] | Impressions, likes, replies, reposts, quotes, profile clicks, link clicks, and optional saves. No documented per-post follows. Refreshing ends after day three. [14] [15] | Good secondary source for early lifecycle, not a 30-day daily snapshot system. |
| **Buffer Essentials** | **$5/month per channel**, billed $60 yearly | API collects metrics from networks it publishes to. Existing direct X-post coverage is not documented. [17] [18] | Experimental personal-key GraphQL metrics API and ZIP CSV export. [18] [19] | X basics such as impressions, normalized likes, reposts, and comments. No documented X link clicks, profile clicks, bookmarks, or follows. [18] | Low-cost but incomplete and publication-workflow dependent. |
| **Publer Business** | **$10/month**, or $8/month billed yearly | Yes. It syncs inside and outside Publer posts daily. [20] [21] | Reports plus product API access, but analytics-read API scopes were not verified. [20] | Views/reach, video views, likes, replies, reposts, quotes, post clicks, link clicks, and engagement. No documented bookmarks or per-post follows. [21] | Useful UI/report alternative. Do not buy it for automated ingestion without trial-verifying analytics reads. |
| **Metricool Advanced + X add-on** | From **$63/month** monthly, or from **€53/month** annual pricing | Yes. Full X analytics requires Advanced or Custom. [22] [23] | API access is listed for Advanced; exact X analytics read endpoint was not verified. [22] | Strongest third-party coverage: impressions, likes, reposts, replies, quotes, link clicks, profile clicks, bookmarks, follows, and unfollows. [23] | Most complete third-party UI option, but far too expensive for this use case. |
| **Fedica Publish** | **$15/month**, or $10/month billed yearly | Markets analytics, but exact own-post X coverage is not clear in the public matrix. [24] | Public API is publishing-only. Export claims exist, but a scheduled analytics export API is not documented. [24] [25] | Impressions and link-click claims appear, but the complete field contract remains unclear. | Not suitable as the collector’s API source. |
| **Hypefury** | Legacy pricing visible | No current X support. [26] | Not applicable | Its own FAQ says it no longer supports X. [26] | Eliminate from consideration. |

Typefully is the only inexpensive third-party option with a clearly documented X analytics read API. Its three-day refresh policy disqualifies it from your specific requirement to retain a daily observation series through day 30. [14] [15]

Buffer’s public API is real and useful, but its analytics surface is expressly experimental. It also normalizes metrics and documents collection from networks it publishes to, which makes it a poor foundation for a history of posts made directly on X. [18]

Metricool has the broadest documented field coverage. Its price is at least an order of magnitude above the estimated API variable cost, and its X metric storage is limited to 30 days. [22] [23]

## 6. Fallback paths and their limits

| Fallback | What it can provide | What it cannot provide | Reliability and policy status |
|---|---|---|---|
| Premium Analytics CSV | Confirmed minimum columns: impressions, likes, replies, reposts. [8] [9] | Confirmed per-post bookmarks, link clicks, profile visits, and follows are not evidenced. | Manual but policy-compliant. Best fallback. |
| X email notification digest | Some likes, reposts, replies, mentions, and follows. [27] | Complete counts, impressions, clicks, bookmarks, and event completeness. X says notices may be omitted. [27] | Do not use as a metrics source. |
| Public post view count | A visible total view count for applicable posts. [28] | A documented unauthenticated API, clicks, bookmarks, profile visits, and daily history. | Human validation only. |
| oEmbed | HTML embed markup without authentication. [29] | A metric schema. oEmbed is not an analytics API. [29] | Not a collector. |
| Unofficial syndication endpoints | Historic practitioners sometimes cite JSON endpoints. | Any supported contract. A July 2026 test returned an empty object for a public post. | Unsupported and brittle. Do not use. |
| Session browser automation | Potentially whatever the UI shows. | Policy compliance, durability, and account safety. [11] [12] [13] | Reject. |

## 7. Concrete implementation sequence

Start with a narrowly scoped proof of billing and fields. This reduces the only material uncertainty: whether the app is correctly recognized as owned and whether your account receives every private field described in the documentation.

1. Create the X developer project and app under the same X identity that owns `@handle`.
2. Enable Pay-Per-Use credits, set a small spending limit, and save the billing configuration evidence.
3. Complete OAuth 2.0 PKCE authorization with `tweet.read`, `users.read`, and `offline.access`.
4. Issue one `GET /2/users/{id}/tweets` request for a recent owned post using all three metric namespaces.
5. Verify the response includes `non_public_metrics.url_link_clicks` and `non_public_metrics.user_profile_clicks` where applicable.
6. Verify the Developer Console prices that request as an Owned Read before enabling the daily schedule.
7. Implement the daily paginated timeline snapshot through the rolling 30-day boundary.
8. Import one Premium CSV manually and reconcile its known columns against the API snapshot table.
9. Add Account Activity only if gross new-follow and unfollow events are operationally valuable without post attribution.

## 8. What remains unverified

| Open item | Current status | Practical response |
|---|---|---|
| Owned Read pricing for `GET /2/tweets` bulk lookup | Not explicitly confirmed in the official price list reviewed. [1] [2] | Do not use it as the primary route. |
| Minimum credit top-up increment | No public primary source found. The docs promise no minimum spend, which is different. [2] | Check checkout before purchase. |
| Current Account Analytics CSV’s full field schema | Official evidence proves export and a core set of columns only. [8] [9] | Test one manual export before relying on it as a recovery path. |
| Stable Account Analytics GraphQL operation name | Not found. Only generic `/i/api/graphql` practitioner evidence exists. [30] | Do not build against it. |
| Exact Account Activity unit billing | Access is confirmed for Pay-Per-Use, but a per-event estimate was not publicly verified. [7] | Treat it as optional until console pricing is visible. |
| Publer analytics API read endpoint | Product API is listed, but analytics-read scope was not verified. [20] | Validate during a trial, not after commitment. |
| Fedica analytics export automation | UI/export claims exist, but its documented public API is publishing-only. [24] [25] | Do not treat it as a programmatic option. |

## Final recommendation

Build the **official Pay-Per-Use collector now**. It meets every requested per-post metric except post-attributed follows, costs roughly **$4.50/month**, and avoids the policy exposure of UI automation. [1] [2] [3]

Treat follows as a separate account-level metric. Use a daily net follower count by default, then add Account Activity API only if exact gross follows and unfollows justify webhook approval and operational complexity. [7]

Keep **Premium Analytics CSV** as a reconciliation and outage fallback. Do not substitute a headless browser, cookie session, email parser, oEmbed, or unofficial syndication endpoint for the official read path. [8] [11] [27] [29]

## References

[1]: https://devcommunity.x.com/t/x-api-pricing-update-owned-reads-now-0-001-other-changes-effective-april-20-2026/263025 "X Developer Community: X API Pricing Update: Owned Reads Now $0.001, 16 April 2026"
[2]: https://docs.x.com/x-api/getting-started/pricing "X API pay-per-usage pricing and credits"
[3]: https://docs.x.com/x-api/fundamentals/metrics "X API Metrics"
[4]: https://docs.x.com/x-api/users/get-posts "X API: Get posts by user"
[5]: https://docs.x.com/x-api/posts/lookup/integrate "X API Post Lookup integration guide"
[6]: https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code "X OAuth 2.0 Authorization Code with PKCE"
[7]: https://docs.x.com/x-api/account-activity/introduction "X v2 Account Activity API" 
[8]: https://business.x.com/en/advertising/analytics "X Business Analytics"
[9]: https://x.com/premium/status/1852537530706731244 "Official X Premium post on analytics time ranges and export, 1 November 2024"
[10]: https://x.com/premium/status/1799251492391846189 "Official X Premium account-analytics launch post, 8 June 2024"
[11]: https://help.x.com/en/rules-and-policies/x-automation "X Automation Rules, updated April 2026"
[12]: https://docs.x.com/developer-guidelines "X Developer Guidelines"
[13]: https://x.com/tos "X Terms of Service"
[14]: https://support.typefully.com/en/articles/8718148-analytics-page-metrics "Typefully: Analytics page and metrics, updated 26 January 2026"
[15]: https://typefully.com/docs/api "Typefully API documentation"
[16]: https://typefully.com/pricing "Typefully pricing"
[17]: https://buffer.com/pricing "Buffer pricing"
[18]: https://developers.buffer.com/guides/post-metrics.html "Buffer Post Metrics API guide"
[19]: https://support.buffer.com/article/950-using-insights-in-buffer "Buffer: Using Insights"
[20]: https://publer.com/plans "Publer plans"
[21]: https://publer.com/help/en/article/what-metricsanalytics-are-gathered-for-each-social-network-1ibwz3q/ "Publer: metrics gathered by social network"
[22]: https://metricool.com/pricing/ "Metricool pricing"
[23]: https://help.metricool.com/x-twitter-metrics-g4v9t "Metricool: X metrics"
[24]: https://fedica.com/signup/ "Fedica plans"
[25]: https://fedica.com/social-media/publishing-api "Fedica Publishing API documentation"
[26]: https://hypefury.com/features-pricing/ "Hypefury features and pricing"
[27]: https://help.x.com/en/managing-your-account/updating-email-preferences "X email notification preferences"
[28]: https://help.x.com/en/using-x/view-counts "X view counts"
[29]: https://docs.x.com/x-for-websites/oembed-api "X oEmbed API"
[30]: https://github.com/cross-mind/crossmind-cli "crossmind-cli practitioner repository, observed 19 July 2026"
[31]: https://github.com/mikf/gallery-dl/issues/6020 "gallery-dl issue #6020, 14 August 2024"
[32]: https://github.com/mikf/gallery-dl/issues/5532 "gallery-dl issue #5532, 30 April 2024"
