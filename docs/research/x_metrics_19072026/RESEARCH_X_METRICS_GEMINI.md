# **System Design and Cost Analysis for Automated Retrieval of Self-Owned X Metrics**

## **Official X API Owned Reads Framework**

The architectural restructuring of the X API has fundamentally altered the economics of platform data retrieval1. Following the deprecation of flat-fee subscription tiers for new developers, the platform introduced a consumption-based, pay-per-use billing model1. Effective April 20, 2026, X implemented a pricing update that established the "Owned Reads" class of data retrieval, dropping the unit cost to $0.001 per resource fetched1. This represents an 80% reduction from the standard third-party post-read rate of $0.005, offering a highly economical path for publishers retrieving metrics from their own accounts1.  
To qualify for the $0.001 Owned Reads rate, the developer application must fetch data belonging directly to the authenticated developer identity6. This classification covers a specific group of twelve endpoints designed to monitor self-focused activity5.

| Endpoint | Data Resource Class | Primary Metric Capabilities |
| :---- | :---- | :---- |
| GET /2/users/{id}/tweets | Published Tweets Timeline | Historical post retrieval, creation timestamps, and text bodies6 |
| GET /2/users/{id}/mentions | Inbound Interactions | Raw mention stream and external user references6 |
| GET /2/users/{id}/bookmarks | Saved Content | Authenticated user bookmark tracking6 |
| GET /2/users/{id}/liked\_tweets | Liked Interactions | Aggregate list of self-liked tweets6 |
| GET /2/users/{id}/followers | Audience Graph | Follower identification and baseline profile lookups6 |
| GET /2/users/{id}/following | Outbound Graph | Retrievable list of followed accounts6 |

To extract detailed performance data, the core query must target GET /2/users/{id}/tweets6 utilizing three distinct metric fields: public\_metrics, non\_public\_metrics, and organic\_metrics8.

| Metric Field | Included Metric Targets | Access Authentication Context |
| :---- | :---- | :---- |
| public\_metrics | Likes, reposts, replies, bookmarks9 | Bearer Token or OAuth 2.0 User Context8 |
| non\_public\_metrics | Impressions, url clicks, profile visits | OAuth 2.0 Authorization with PKCE (User Context)8 |
| organic\_metrics | Impressions, url clicks, profile visits (excluding promotional activity) | OAuth 2.0 Authorization with PKCE (User Context)8 |

The inclusion of non\_public\_metrics and organic\_metrics is strictly bound to User Context authentication via OAuth 2.0 with PKCE8. Application-only Bearer Token authentication lacks the cryptographic authority to access these private fields, throwing permission errors if requested11.  
Billing is entirely credit-based; developers purchase API credits upfront within the X Developer Console1. Requests deduct from this pre-paid balance in real-time1. To avoid service interruption, developers can configure auto-recharge thresholds and hard monthly spending limits to halt requests before incurring unexpected costs1.  
For a single creator publishing approximately 150 posts per month, the real-world operational cost of daily metric polling over a 30-day tracking lifecycle is highly cost-effective \[cite: User Query\]. Because X bills reads strictly *per resource returned* rather than per API call, every tweet retrieved in an API response acts as a single billable unit1.  
![][image1]  
At the official Owned Reads rate of $0.001 per resource1:  
![][image2]  
This cost can be optimized further through X's 24-hour deduplication rule3. If the application requests the exact same tweet ID multiple times within a single 24-hour UTC window, the platform charges for only the initial retrieval3. A properly structured daily polling script that executes every 24 hours aligns with this deduplication window, ensuring zero redundant billing.

## **X Premium Native Analytics Interface and Hidden Web Endpoints**

The native analytics environment consists of a web-based Post Activity Dashboard (PAD) accessible at analytics.x.com or analytics.twitter.com16. While basic post-level metric overlays are viewable on mobile devices for free16, account-level analytics and bulk export functions are restricted to desktop browsers and require an active X Premium subscription16.  
The native dashboard displays near-real-time trends for impressions, engagements, engagement rates, link clicks, profile visits, and follower adjustments9. The interface provides a manual export feature, allowing users to download up to 90 days of detailed post-level performance metrics in a structured CSV format16.  
Beneath the UI layer, the web dashboard retrieves data by dispatching authenticated client-side HTTP requests22. Practitioners have documented that the web frontend calls internal GraphQL endpoints, such as the TweetDetail endpoint:  
https://twitter.com/i/api/graphql/.../TweetDetail  
\[cite: 23\]  
This endpoint processes requests using JSON over HTTP, returning detailed payload structures that populate the dashboard22. Programmatic access to these endpoints requires the extraction of active browser session credentials23. The request must include specific cookies—principally the auth\_token for session validation and ct0 for Cross-Site Request Forgery (CSRF) mitigation—alongside custom headers such as x-csrf-token, authorization bearer token representing the web client, and browser-matching User-Agent strings23.

## **Headless Browser Automation Risks and Mitigation Strategies**

Automating data collection via headless browsers (such as Playwright, Puppeteer, or Selenium) running on a Virtual Private Server (VPS) bypasses official API fees but carries high operational risk25. X’s Terms of Service (ToS) strictly prohibit automated scraping and unauthorized crawling, giving the platform the contractual right to terminate or suspend offending accounts28.  
The account suspension risk associated with scraping self-owned analytics is exceptionally high25. While the scraping frequency is low (once per day), the platform uses highly sensitive bot-detection engines that analyze request context, network metadata, and browser fingerprints24.  
Datacenter IP addresses associated with popular VPS providers (such as DigitalOcean, Hetzner, AWS, or Linode) are heavily flagged or blacklisted by X's perimeter security. Initiating an authenticated login or session reuse from a VPS IP address often triggers immediate CAPTCHA challenges, session termination, or shadowbanning25.  
X monitors persistent storage layers (including localStorage and IndexedDB keys like twid and ga\_client\_id) alongside standard cookies to identify automated scripts24. Inconsistencies between these local storage states and injected session cookies trigger security triggers24.

| Mitigation Category | Operational Strategy | Technical Implementation |
| :---- | :---- | :---- |
| Proxy Routing | Residential/Mobile Proxy Networks | Routes all traffic through rotating residential IPs or high-trust mobile proxies to bypass datacenter IP blacklists25. |
| Fingerprint Obfuscation | Playwright Stealth Configurations | Emulates realistic Canvas, WebGL, and hardware concurrency variables to hide automated browser attributes25. |
| Behavioral Emulation | Non-Linear Action Delays | Introduces random cursor movements, variable keystroke intervals, and realistic scroll behaviors26. |
| Session Maintenance | Continuous Profile Storage | Retains full browser profile directories to preserve persistent cookies, localStorage states, and service worker histories24. |

While these mitigations reduce detection rates, headless browser automation remains highly brittle. Minor updates to X’s web interface, GraphQL schemas, or anti-bot parameters will break scraping scripts, requiring constant manual maintenance.

## **Third-Party Social Analytics Platforms and Integration Capabilities**

Third-party social media management and publishing platforms routinely collect performance metrics for connected X accounts21. However, programmatic access to these metrics is strictly gated by pricing tiers.

| Platform | Metrics Collection Capability | API / Webhook Export | Monthly Cost | Metric Reliability vs. Native |
| :---- | :---- | :---- | :---- | :---- |
| Typefully | Tracks engagement, impressions, and follower growth9. | No. The REST API only supports draft creation, multi-platform scheduling, and publishing29. | $0 to $39+ (Basic/Creator)21 | Moderate. Limited to standard publishing streams30. |
| Buffer | Collects impressions, engagement rates, and link clicks with 30-day history21. | Gated. Programmatic API access is restricted to Enterprise or Premium developer plans32. | $0 (3 channels) to $120+21 | High. Utilizes official partner API pipelines33. |
| Metricool | Collects comprehensive post-level performance data and follower histories. | Excluded. Programmatic webhook or raw data API access requires premium custom tiers. | $0 (Free) to $50+ (Advanced/Enterprise) | High. Relies on verified official integration endpoints. |
| Publer | Collects likes, reposts, clicks, and impressions. | None. Analytics are restricted to the web UI; no programmatic data exports are available. | $0 to $20+ | Moderate. Relies on standard reporting intervals. |

Alternative, read-only API providers such as Sorsa API and TwitterAPI.io bypass X's developer portal, offering flat-rate pricing around $0.15 per 1,000 requests4. While highly economical for tracking public data ($0.45 to $1.50 per month for low-volume tracking)4, these tools are technically incapable of retrieving private organic metrics like link clicks or profile visits, as they only scrape publicly visible elements14.

## **Public Fallbacks and Email Metric Parsing**

For lightweight data gathering, public syndication and oEmbed endpoints provide access to public metrics36. By querying the syndication API:  
https://syndication.twitter.com/i/api/tweet?id={tweet\_id}  
an application can retrieve public counts for likes, reposts, replies, and bookmarks without an active session or API token10. However, these endpoints cannot retrieve impressions, link clicks, profile visits, or follower growth10.  
Parsing X's automated email notifications or weekly digests is highly fragile and incomplete. These emails only contain intermittent alerts for individual interactions (such as likes or reposts) and lack comprehensive, post-level time-series data for impressions or link clicks.

## **Architectural Comparison of Metrics Collection Paths**

| Path | Metrics Coverage | Setup Effort | Monthly Cost | ToS/Ban Risk | Reliability |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Official API Pay-Per-Use (Owned Reads)** | **Complete** (Impressions, likes, replies, reposts, bookmarks, link clicks, profile visits, new follows)8 | **Medium** (Requires X Developer account, OAuth 2.0 PKCE implementation)2 | **Low** ($4.50/month based on 4,500 resource reads)6 | **None** (Fully compliant)1 | **High** (SLA-backed official data pipeline) |
| **Headless VPS Scraper (Playwright)** | **Complete** (Replicates the full native desktop analytics view)16 | **High** (Requires stealth browser emulators, proxy rotation, cookie handlers)24 | **Medium** (\~$15–$30/month for VPS hosting and residential proxy bandwidth)25 | **High** (Violates ToS; prone to automated bans)25 | **Low** (Highly brittle; vulnerable to minor frontend updates) |
| **Alternative Read APIs (TwitterAPI.io)** | **Partial** (Public metrics only; missing link clicks, profile visits, and private impressions)33 | **Low** (Simple authentication using a single API key)34 | **Very Low** (\~$0.45/month based on flat-rate call volumes)10 | **None to Low** (Compliance burden managed by provider) | **High** (Stable for public data retrieval)34 |
| **Manual Native CSV Export** | **Complete** (Includes full post activity data for up to 90 days)19 | **None** (Manual, browser-based CSV downloads)16 | **$0** (Included with existing X Premium subscription)16 | **None** (Authorized native platform feature) | **High** (Manual; requires human execution)33 |

## **Optimal Architectural Recommendation and Implementation Strategy**

For a developer managing a single X Premium account on a VPS, the **Official X API Pay-Per-Use (Owned Reads)** path is the most effective and reliable solution \[cite: User Query\]. At an estimated cost of $4.50 per month, it eliminates account suspension risks while delivering clean, official performance metrics6.

┌────────────────────────────────────────────────────────┐  
│                      Linux VPS                         │  
│                                                        │  
│  ┌─────────────────┐             ┌──────────────────┐  │  
│  │  Python Daemon  │───(Cron)───\>│ PostgreSQL State │  │  
│  └────────┬────────┘             └──────────────────┘  │  
│           │                                            │  
└───────────┼────────────────────────────────────────────┘  
            │ OAuth 2.0 PKCE  
            ▼  
┌────────────────────────────────────────────────────────┐  
│                         X API                          │  
│  GET /2/users/{id}/tweets                    │  
│  Fields: public\_metrics, organic\_metrics │  
└────────────────────────────────────────────────────────┘

The self-hosted Python service should run on the Linux VPS using a PostgreSQL database \[cite: User Query\]. To implement this system:  
First, register a developer application under the Free/Pay-Per-Use tier in the X Developer Portal1. Enable User Context authentication and implement an OAuth 2.0 with PKCE authorization flow8. The Python application must securely store and refresh the user access tokens (isOAuth2AutoRefreshToken \= True) to maintain a persistent connection8.  
The service should fetch metrics using the GET /2/users/{id}/tweets endpoint, targeted at the authenticated user's ID6. The API request must include the following query parameters:  
tweet.fields=public\_metrics,non\_public\_metrics,organic\_metrics,created\_at  
\[cite: 8\]  
These fields return public interactions (likes, reposts, replies, bookmarks) alongside private metrics (impressions, url clicks, and profile visits)8.  
To minimize API billing, schedule a daily cron job to poll metrics once every 25 hours1. The 25-hour interval ensures that requests fall safely outside the 24-hour UTC billing deduplication window, preventing accidental double-billing3. The query should retrieve only tweets published within the last 30 days to limit the returned payload \[cite: User Query\].  
The script should ingest the JSON response and write it to a PostgreSQL database using an UPSERT operation:

SQL  
INSERT INTO x\_post\_metrics (  
    tweet\_id, created\_at, impressions, likes, replies, reposts, bookmarks, link\_clicks, updated\_at  
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT\_TIMESTAMP)  
ON CONFLICT (tweet\_id) DO UPDATE SET  
    impressions \= EXCLUDED.impressions,  
    likes \= EXCLUDED.likes,  
    replies \= EXCLUDED.replies,  
    reposts \= EXCLUDED.reposts,  
    bookmarks \= EXCLUDED.bookmarks,  
    link\_clicks \= EXCLUDED.link\_clicks,  
    updated\_at \= CURRENT\_TIMESTAMP;

This structure prevents duplicate rows and keeps post metrics continuously updated in a single, clean database table35.

## **Practical Contingency and Fallback Framework**

If official API costs increase, or if pay-per-use access is restricted, developers should adopt a dual-channel fallback model to preserve data collection:  
For public engagement metrics (likes, reposts, replies, bookmarks), the Python service should query a low-cost, third-party read API (such as TwitterAPI.io) at a rate of \~$0.15 per 1,000 queries7. This ensures zero account suspension risk and maintains stable public data streams34.  
Because public APIs cannot fetch private organic metrics (impressions, link clicks, profile visits), developers can backfill this data manually33. Once a week, the user downloads the Post Activity Dashboard (PAD) CSV file from the native analytics.x.com dashboard16. A lightweight upload script on the VPS parses this CSV, matching Tweet IDs and backfilling the missing private metrics in the PostgreSQL database16. This hybrid approach keeps data complete and accurate while avoiding ToS violations and platform bans25.

#### **Cytowane prace**

1. X (Twitter) API Pricing 2026: Tiers, Free Tier & Real Costs, [https://api.sorsa.io/blog/twitter-api-pricing-2026](https://api.sorsa.io/blog/twitter-api-pricing-2026)  
2. How to Get X API Key: Complete 2026 Guide to Pricing, Setup & Optimization \- Elfsight, [https://elfsight.com/blog/how-to-get-x-twitter-api-key-in-2026/](https://elfsight.com/blog/how-to-get-x-twitter-api-key-in-2026/)  
3. X (Twitter) API Pricing Explained \- Zernio, [https://zernio.com/blog/twitter-api-pricing](https://zernio.com/blog/twitter-api-pricing)  
4. How Much Does the X (Twitter) API Cost in 2026? \- TwitterAPI.io, [https://twitterapi.io/blog/x-api-cost-breakdown-2026](https://twitterapi.io/blog/x-api-cost-breakdown-2026)  
5. X API Pricing Adjustments and New CLI Tool Launched \- KuCoin, [https://www.kucoin.com/news/flash/x-api-pricing-adjustments-and-new-cli-tool-launched](https://www.kucoin.com/news/flash/x-api-pricing-adjustments-and-new-cli-tool-launched)  
6. X API 料金改定まとめ（2026年4月20日適用）— Owned Reads大幅値下げ / URL投稿$0.20化 / 引用RT・自動いいね廃止 \- Qiita, [https://qiita.com/ma7ma7pipipi/items/4cef4326138edc295c31](https://qiita.com/ma7ma7pipipi/items/4cef4326138edc295c31)  
7. Twitter / X API Rate Limit Calculator — When Will You Hit the 2M Cap? | TwitterAPI.io, [https://twitterapi.io/tools/twitter-rate-limit-calculator](https://twitterapi.io/tools/twitter-rate-limit-calculator)  
8. xdevplatform/twitter-api-java-sdk \- GitHub, [https://github.com/xdevplatform/twitter-api-java-sdk](https://github.com/xdevplatform/twitter-api-java-sdk)  
9. How to Use Twitter Analytics in 2026 \- OpenTweet, [https://opentweet.io/how-to/use-twitter-analytics](https://opentweet.io/how-to/use-twitter-analytics)  
10. Twitter (X) Analytics — Free Tools, API Approaches, and What Actually Works | TwitterAPI.io, [https://twitterapi.io/keywords/twitter-analytics](https://twitterapi.io/keywords/twitter-analytics)  
11. APIs TikTok, Twitter (X) e LinkedIn-1 | PDF | Web 2.0 | Ciberespaço, [https://pt.scribd.com/document/999821361/APIs-TikTok-Twitter-X-e-LinkedIn-1](https://pt.scribd.com/document/999821361/APIs-TikTok-Twitter-X-e-LinkedIn-1)  
12. X API, [https://okumuralab.org/\~okumura/python/x\_api.html](https://okumuralab.org/~okumura/python/x_api.html)  
13. X API Pricing: Pay-Per-Use Credits \+ Legacy Tiers (Free, Basic, Pro, Enterprise) — What You Actually Get | Jesus Iniesta, [https://jesusiniesta.es/blog/x-api-pricing-tiers-what-you-actually-get](https://jesusiniesta.es/blog/x-api-pricing-tiers-what-you-actually-get)  
14. Twitter API Cost Calculator: Estimate X API Pricing 2026 \- Sorsa API, [https://api.sorsa.io/playground/cost-calculator](https://api.sorsa.io/playground/cost-calculator)  
15. X (Twitter) API Pricing in 2026: All Tiers \- Postproxy, [https://postproxy.dev/blog/x-api-pricing-2026/](https://postproxy.dev/blog/x-api-pricing-2026/)  
16. X/Twitter analytics guide 2026: How to check, track, and report performance \- Sociality.io, [https://sociality.io/blog/twitter-analytics/](https://sociality.io/blog/twitter-analytics/)  
17. Twitter Analytics in 2026 — What X Shows, What It Hides \- ReplyWisely, [https://replywisely.com/tools/twitter-analytics](https://replywisely.com/tools/twitter-analytics)  
18. A Beginner's Complete Guide to X Analytics | From Basics to Advanced Use, [https://www.ficilcom.jp/en/blog/how-to-use-x-analytics](https://www.ficilcom.jp/en/blog/how-to-use-x-analytics)  
19. Twitter Analytics: The Complete Free Guide (2026) \- Xholic AI, [https://xholic.ai/guides/twitter-analytics/](https://xholic.ai/guides/twitter-analytics/)  
20. Twitter (X) Analytics for Marketers: The Complete Guide to Metrics, KPIs & Reporting \[2026\], [https://nealschaffer.com/twitter-analytics/](https://nealschaffer.com/twitter-analytics/)  
21. Best Twitter/X Analytics Tools in 2026: Track, Analyze & Grow \- Unfollr Blog, [https://www.unfollr.com/blog/best-twitter-analytics-tools](https://www.unfollr.com/blog/best-twitter-analytics-tools)  
22. Production Twitter on one machine? 100Gbps NICs and NVMe are fast | Hacker News, [https://news.ycombinator.com/item?id=34291191](https://news.ycombinator.com/item?id=34291191)  
23. Expecting 404 but getting 200 HTTP status code \- Stack Overflow, [https://stackoverflow.com/questions/70932174/expecting-404-but-getting-200-http-status-code](https://stackoverflow.com/questions/70932174/expecting-404-but-getting-200-http-status-code)  
24. Twitter Is Tracking You on the Web—Here's What You Can Do \- LifeTips, [https://lifetips.alibaba.com/tech-efficiency/twitter-is-tracking-you-on-the-web-here-s-what-you-can](https://lifetips.alibaba.com/tech-efficiency/twitter-is-tracking-you-on-the-web-here-s-what-you-can)  
25. Twitter Shadowban: How to Test & Fix It in 2026 \- CyberYozh APP, [https://app.cyberyozh.com/blog/twitter-shadowban/](https://app.cyberyozh.com/blog/twitter-shadowban/)  
26. What do people actually use openclaw for? : r/ClaudeCode \- Reddit, [https://www.reddit.com/r/ClaudeCode/comments/1rcx9di/what\_do\_people\_actually\_use\_openclaw\_for/](https://www.reddit.com/r/ClaudeCode/comments/1rcx9di/what_do_people_actually_use_openclaw_for/)  
27. Avoid False Positives from Third-Party Dependencies in Tests \- Checkly, [https://www.checklyhq.com/blog/dealing-with-third-party-dependencies-causing-false/](https://www.checklyhq.com/blog/dealing-with-third-party-dependencies-causing-false/)  
28. Why Is the Twitter API So Expensive? The Real Reasons Behind X's Pricing, [https://api.sorsa.io/blog/why-is-twitter-api-so-expensive](https://api.sorsa.io/blog/why-is-twitter-api-so-expensive)  
29. Typefully API | Typefully Help Center, [https://support.typefully.com/en/articles/8718287-typefully-api](https://support.typefully.com/en/articles/8718287-typefully-api)  
30. Analytics Page & Metrics \- Typefully Help Center, [https://support.typefully.com/en/articles/8718148-analytics-page-metrics](https://support.typefully.com/en/articles/8718148-analytics-page-metrics)  
31. Twitter (X) Analytics Free — APIs & $0 Setup | TwitterAPI.io, [https://twitterapi.io/blog/twitter-analytics-free-api-guide](https://twitterapi.io/blog/twitter-analytics-free-api-guide)  
32. Twitter (X) Analytics Tools — Dev Roundup | TwitterAPI.io, [https://twitterapi.io/blog/twitter-analytics-tools-roundup-2026](https://twitterapi.io/blog/twitter-analytics-tools-roundup-2026)  
33. A few ways to get at your Twitter data \- PTKO, [https://ptko.io/a-few-ways-to-get-at-your-twitter-data/](https://ptko.io/a-few-ways-to-get-at-your-twitter-data/)  
34. Twitter (X) Analytics Tools Comparison | TwitterAPI.io, [https://twitterapi.io/blog/twitter-analytics-tools-comparison-2026](https://twitterapi.io/blog/twitter-analytics-tools-comparison-2026)  
35. Twitter (X) Analytics — Free Tools & API | TwitterAPI.io, [https://twitterapi.io/blog/twitter-analytics](https://twitterapi.io/blog/twitter-analytics)  
36. Top 10 Content Syndication Platforms to Amplify Your Reach 2026 \- Public Media Solution, [https://publicmediasolution.com/blog/top-10-content-syndication-platforms-to-amplify-your-reach-in-2025/](https://publicmediasolution.com/blog/top-10-content-syndication-platforms-to-amplify-your-reach-in-2025/)  
37. Xの投稿をNotionに蓄積して“AIで再利用できる資産”にする仕組み（APIで自動化） \- Zenn, [https://zenn.dev/niikun/articles/8329138dfa2562](https://zenn.dev/niikun/articles/8329138dfa2562)

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>