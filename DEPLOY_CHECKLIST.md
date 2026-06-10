# Social Publishing Agent - Deploy Checklist

Client-facing pre-install requirements and deployment guide. Complete every item in Part 1 BEFORE installation begins.

Product: an AI social publishing agent. Reads your content insights, adapts them to platform-native posts, runs a brand-voice compliance check, sends you a preview with Approve / Reject / Edit buttons in chat (Telegram, optionally Slack), and publishes on approval. High-priority items can auto-publish after a configurable timeout. All state lives in PostgreSQL.

---

## Part 0 - What this product needs (the short version)

| Need | Required? | Who provides |
|------|-----------|--------------|
| Linux server with Docker | Yes | Client |
| PostgreSQL 15+ | Yes (bundled with stack) | Auto / Client |
| n8n (self-hosted) | Yes | Auto / Client |
| Anthropic API key (Claude) | Yes | Client |
| X (Twitter) Developer App | Yes (for X publishing) | Client |
| Telegram bot | Yes (approval channel) | Client |
| Slack app | Optional (alt approval channel) | Client |
| Notion integration | Optional (if Notion = content source) | Client |
| Domain + HTTPS | Recommended | Client |

---

## Part 1 - CLIENT PREPARES BEFORE INSTALL

### 1A. Infrastructure
- [ ] Linux server / VPS (2 GB RAM minimum, 4 GB recommended). Docker + Docker Compose installed.
- [ ] A domain or subdomain pointing to the server (for n8n + webhooks), with HTTPS (Caddy/Traefik/Cloudflare). Webhooks need a public HTTPS URL.
- [ ] SSH access to the server.
- [ ] Decision: bundled PostgreSQL (in the Docker stack) or external managed PostgreSQL. Bundled is fine for single-client.

### 1B. Anthropic (Claude) - the brain
- [ ] Account at console.anthropic.com
- [ ] API key created (starts with `sk-ant-`)
- [ ] Billing enabled with a spend cap (suggest $10 min / $30 monthly cap to start)
- [ ] Models used: Haiku (fast, for adapt + brand-canon check). Sonnet optional for heavier reasoning.
- Cost estimate: ~$5-30/month at a few posts/day.

### 1C. X (Twitter) Developer App - to publish
- [ ] Developer account at developer.x.com
- [ ] An App created inside a Project
- [ ] App permissions set to **Read and Write** (default is Read only - must change BEFORE generating tokens)
- [ ] App type: Web App / Automated App or Bot
- [ ] Generate and save ALL of these:
  - [ ] API Key (Consumer Key)
  - [ ] API Key Secret (Consumer Secret)
  - [ ] Access Token (must be generated AFTER setting Read+Write)
  - [ ] Access Token Secret
  - [ ] Bearer Token (for reads / analytics)
- [ ] Tier awareness: Free tier allows ~1,500 posts/month (writes). Some READ endpoints (metrics, search) may require Basic (~$100/month). Publishing works on Free; analytics may not.
- Note: if you regenerate App permissions, you MUST regenerate the Access Token + Secret afterward.

### 1D. Telegram bot - the approval channel
- [ ] Open Telegram, message @BotFather
- [ ] `/newbot` - choose a name and username, save the bot token (format `1234567890:AA...`)
- [ ] Each approver sends `/start` to the bot once (so the bot can message them)
- [ ] Capture each approver's numeric chat_id (the installer pulls it from the bot's getUpdates)
- One bot per client. Do not share bots across clients.

### 1E. Slack (optional - alternative approval channel)
- [ ] Slack workspace admin access
- [ ] Create a Slack App (api.slack.com/apps)
- [ ] Bot token scopes: `chat:write`, `commands`, `im:history`
- [ ] Install to workspace, save Bot User OAuth Token (`xoxb-...`) + Signing Secret
- [ ] Target channel ID or DM
- Note: Slack channel is a roadmap item; confirm availability for your install.

### 1F. Notion (optional - only if Notion is your content source)
- [ ] Internal integration at notion.so/my-integrations, save token (`ntn_...` or `secret_...`)
- [ ] Share the content-source page/database with the integration (enable "Apply to sub-pages")
- [ ] Capture the page/database IDs
- If you do NOT use Notion, content goes straight into the PostgreSQL `post_queue` table (the product direction). Confirm your content-source choice with the installer.

### 1G. Decisions the client must make (config inputs)
Prepare answers to these - they become the agent's runtime settings:
- [ ] **Brand voice rules** (the "voice bible"): tone, hard rules, first vs third person, any non-negotiables
- [ ] **Banned vocabulary**: words/acronyms the agent must never use
- [ ] **Posting windows** per platform (e.g., X at 09:00 / 14:00 / 18:00 / 22:00)
- [ ] **Max posts per day** per platform
- [ ] **Active hours** (timezone + start/end - no posting outside)
- [ ] **Auto-publish policy**: which priorities auto-publish (e.g., HIGH only), and the timeout before auto-publish (e.g., 30 min). Default is hard human gate (no auto-publish).
- [ ] **Who approves**: which person(s) get the preview and click Approve

---

## Part 2 - INSTALL (installer runs)

- [ ] Provision Docker stack: n8n + PostgreSQL + reverse proxy (HTTPS)
- [ ] CRITICAL n8n env vars (the agent signs requests in Code nodes):
  - `NODE_FUNCTION_ALLOW_BUILTIN=crypto,https`
  - These MUST be set in the docker run / compose file, not just the live container (auto-updaters wipe live-only env vars).
- [ ] Run database migrations: create tables (`post_queue`, `published_posts`, `hitl_sessions`, `brand_config`, `conversation_state`, `inspirations`, `task_queue`, `contacts`, `engagement_log`)
- [ ] Create n8n credentials (one each): Anthropic (header auth), X OAuth 1.0a, Telegram, PostgreSQL, Notion (if used), Slack (if used)
- [ ] Import workflows: main publisher, HITL handler (the approval/publish brain), analytics, timeout checker
- [ ] Activate: HITL handler + (optionally) timeout checker. Activate main publisher after the test cycle.

---

## Part 3 - CONFIGURE (seed brand_config)

All runtime settings live in the `brand_config` table as key/value rows, scoped by `brand_id`. Seed these from the client's Part 1G answers:

| config_key | example value | meaning |
|------------|---------------|---------|
| `voice_bible` | full ruleset text | brand voice the adapter enforces |
| `banned_vocab` | CSV of words | never-use vocabulary |
| `publish_windows` | `{"x":["09:00","14:00","18:00","22:00"]}` | allowed post times |
| `max_posts_per_day` | `{"x":3}` | rate caps |
| `active_hours_cet` | `{"start":"08:00","end":"22:00"}` | no posting outside |
| `hitl_timeout_active_min` | `30` | auto-publish timeout (day) |
| `auto_publish_priorities` | `["high"]` | which priorities auto-publish |

(Two-way config from the chat bot - changing these via a Telegram/Slack command - is a roadmap feature. Until then, settings are seeded at install and edited in the DB.)

---

## Part 4 - VERIFY (test cycle before go-live)

- [ ] Telegram: bot responds, approver receives a test message
- [ ] X API: read own profile succeeds (confirms credentials)
- [ ] Notion (if used): content source is readable by the integration
- [ ] End-to-end dry run: add one test insight -> preview appears in chat WITH buttons -> click Approve -> post appears on X -> item marked published -> confirmation returns to chat
- [ ] Confirm the published post is logged in `published_posts`
- [ ] Only after a clean test: activate the main publisher (and timeout checker if auto-publish is wanted)

---

## Part 5 - OPERATIONS (client day-to-day)

- Add insights to the content source (Notion queue or `post_queue`)
- Receive previews in chat, click Approve / Reject / Edit
- High-priority items auto-publish after the timeout (if enabled)
- Daily analytics digest in chat
- All errors surface to chat (no silent failures)

---

## Appendix - Credential summary (one page for the client to fill)

```
ANTHROPIC_API_KEY=
X_API_KEY=                 (Consumer Key)
X_API_SECRET=              (Consumer Secret)
X_ACCESS_TOKEN=            (Read+Write)
X_ACCESS_TOKEN_SECRET=
X_BEARER_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_APPROVER_CHAT_ID=
NOTION_API_KEY=            (optional)
NOTION_SOURCE_PAGE_ID=     (optional)
SLACK_BOT_TOKEN=           (optional)
SLACK_SIGNING_SECRET=      (optional)
POSTGRES_PASSWORD=         (set at install)
SERVER_DOMAIN=             (HTTPS, for webhooks)
```

Security: never commit filled credentials to git. The installer keeps them in the server's environment + the n8n credential store only.
