# AGS X Agent v1.0 - Setup & Deployment Guide

Version: 1.0.0 | Date: 2026-05-31

---

## Overview

This guide deploys the AGS X (Twitter) Agent - an n8n automation that pulls insights from your Notion X Content Queue, generates tweet drafts via Claude, sends them to you for approval via Telegram, and posts to X on approval.

What you are deploying:
- 3 n8n workflows (main agent, HITL handler, analytics)
- PostgreSQL schema (contacts, engagement_log, hitl_sessions)
- 6 n8n credentials wired to live services

Estimated time: 30-45 minutes following this guide exactly.

---

## Prerequisites Checklist

Confirm all of these before starting:

- [ ] n8n self-hosted running at `https://ivy147-20147.mikrus.cloud`
- [ ] PostgreSQL container `pg_n8n` running on `n8n_network`
- [ ] Telegram `@ags_social_bot` token available in credentials file
- [ ] X API app ID `32798547` with Read/Write permissions (confirmed 2026-05-31)
- [ ] Notion `n8n-AGS` integration token available in credentials file
- [ ] Anthropic API key already configured in n8n as `AGS-n8n`

> [!WARNING]
> Do not proceed if any item above is unchecked. Each part of this guide depends on these foundations being in place.

---

## Part 1: PostgreSQL CRD Setup (10 min)

**1.** SSH into your Mikrus server:

```
ssh user@ivy147-20147.mikrus.cloud
```

**2.** Exec into the PostgreSQL container:

```
docker exec -it pg_n8n psql -U ags_crd_user -d ags_crd
```

**3.** Paste the full contents of `scripts/crd-migrations/001_initial_schema.sql` into the psql prompt. Press Enter to execute.

**4.** Verify the migration succeeded by running:

```
\dt
```

Expected output: 3 tables listed - `contacts`, `engagement_log`, `hitl_sessions`.

> [!WARNING]
> If you see fewer than 3 tables, the migration did not fully execute. Re-paste the SQL in full before continuing.

**5.** Exit psql: `\q`

**6.** Add the PostgreSQL credential in n8n:

- Navigate to: `https://ivy147-20147.mikrus.cloud` > Credentials > New Credential
- Type: `PostgreSQL`
- Fill in exactly:

| Field | Value |
|-------|-------|
| Name | `PostgreSQL CRD ags-agents` |
| Host | `pg_n8n` |
| Port | `5432` |
| Database | `ags_crd` |
| Username | `ags_crd_user` |
| Password | from `AGS_Credentials_Internal.md` |

> [!WARNING]
> The credential name must be exactly `PostgreSQL CRD ags-agents` - the workflow JSON references this name by string match. A typo means all database nodes will show errors.

**7.** Click "Test Connection". Confirm green success message, then Save.

---

## Part 2: Telegram Bot Configuration (5 min)

**1.** Open Telegram and send `/start` to `@ags_social_bot`.

**2.** Get your Telegram chat ID using one of two methods:

- Method A (test script): `python n8n-workflows/x-agent/test-scripts/test-telegram.py` - the script prints your `chat_id`
- Method B (n8n): In n8n, open the HITL Handler webhook URL, view a recent execution, and extract `chat.id` from the incoming update payload

**3.** Note the `chat_id` value. You will need it in Part 6.

**4.** Add the Telegram credential in n8n:

- n8n > Credentials > New > Telegram API
- Name: `Telegram @ags_social_bot`
- Access Token: from credentials file
- Save

> [!TIP]
> If you are unsure which token to use, it is the one labeled "HTTP API Token" from BotFather, starting with digits followed by a colon.

---

## Part 3: X API Setup (5 min)

**1.** Add the OAuth 1.0a write credential:

- n8n > Credentials > New > OAuth1 API
- Name: `X API AGS Content Automation`

| Field | Value |
|-------|-------|
| Consumer Key | from credentials file |
| Consumer Secret | from credentials file |
| Access Token | from credentials file (Access Token R/W) |
| Access Token Secret | from credentials file |

- Save

**2.** Add the Bearer Token read credential:

- n8n > Credentials > New > HTTP Header Auth
- Name: `X API Bearer AGS`

| Field | Value |
|-------|-------|
| Name (header field) | `Authorization` |
| Value | `Bearer ` followed by bearer token from credentials file |

> [!WARNING]
> Include the word `Bearer` and a single space before the token. Without this prefix, all analytics read calls will return 401 Unauthorized.

- Save

---

## Part 4: Anthropic API Credential

**1.** In n8n > Credentials, search for `AGS-n8n`.

**2.** If found: no action needed - continue to Part 5.

**3.** If not found, create it:

- New > HTTP Header Auth
- Name: `Anthropic API AGS-n8n`
- Header Name: `x-api-key`
- Value: your Anthropic API key
- Save

---

## Part 5: Notion Setup (5 min)

**1.** Open the AGS Operations Hub in Notion.

**2.** Click Share (top right) > Invite > search for `n8n-AGS` > invite with "Can edit" permission.

> [!WARNING]
> You must enable "Include sub-pages" during the invite step. Without this, the X Content Queue (a sub-page of Ops Hub) will not be accessible and the workflow will silently return 0 items to process.

**3.** Verify or create the Notion credential in n8n:

- If `Notion n8n-AGS` already exists in Credentials: skip to step 4
- If not: New > Notion API > Name: `Notion n8n-AGS` > Integration Token: `__NOTION_TOKEN__` from credentials file > Save

**4.** Run the access verification script:

```
python n8n-workflows/x-agent/test-scripts/test-notion.py
```

All 4 tests must show `[PASS]` before continuing.

> [!WARNING]
> If any test shows `[FAIL]`, stop and fix Notion access before continuing. The main workflow will fail silently if Notion returns empty results.

---

## Part 6: Workflow Import and Configuration (10 min)

> [!WARNING]
> Import order matters. The HITL Handler must be active before the main workflow is imported. If the main workflow fires a HITL callback and the handler is not running, the approval webhook has no listener and the post is dropped.

**1.** Import the HITL Handler workflow:

- n8n > Workflows > Import from JSON > paste contents of `ags-hitl-handler-v1.json`
- On the imported workflow, set credentials on every node that shows a yellow warning icon
- Toggle the workflow to Active (ON)
- Confirm the toggle turns green before proceeding

**2.** Import the Analytics workflow:

- n8n > Workflows > Import from JSON > paste contents of `ags-analytics-v1.json`
- Set credentials on all nodes with warnings
- Toggle to Active (ON)

**3.** Import the Main workflow:

- n8n > Workflows > Import from JSON > paste contents of `ags-x-agent-v1.json`
- Set credentials on all highlighted nodes
- Find every "Telegram Send Message" node in the workflow

> [!TIP]
> Use the workflow search (Ctrl+F or Cmd+F in n8n) and search for "Telegram" to jump to each Telegram node quickly.

**4.** In each Telegram Send Message node, update the `chatId` parameter to your actual chat ID noted in Part 2 Step 3.

**5.** Do NOT activate the main workflow yet. Leave it OFF until Part 8.

---

## Part 7: Test Mode Walkthrough (5-10 min)

**1.** Add a test insight to your X Content Queue in Notion:

- Open: `https://www.notion.so/371c00c90b9381a0bc29e1dc22e5c244`
- Add a new bullet: `[HIGH] [Test] n8n X Agent build complete. 6h total. Telegram HITL approval before every post.`

**2.** Run the test scripts in order:

```
cd C:\Claude-CoWork\AGS\ags-agents\n8n-workflows\x-agent\test-scripts
python test-telegram.py
python test-notion.py
python test-x-api.py
python test-end-to-end.py
```

Each script should exit with all checks passed. Fix any failure before moving to the next script.

**3.** Trigger the main workflow manually in n8n:

- Open the main workflow
- Click "Execute Workflow" (play button)
- Watch execution nodes - they should turn green sequentially

**4.** Watch for the Telegram message:

- You should receive a tweet preview with approval buttons within 30 seconds
- If no message arrives after 60 seconds, check n8n execution logs for the last failed node

> [!TIP]
> A common reason for no Telegram message: the `chatId` in the Telegram nodes was not updated in Part 6 Step 4. Double-check the value matches what `test-telegram.py` printed.

**5.** Test the approval flow:

- In Telegram, tap the Approve button on the preview message
- Confirm the HITL Handler workflow shows a new execution in n8n
- Confirm the main workflow resumes (check execution history)
- Check `@tomasz_ags` on X - the test tweet should appear

> [!WARNING]
> This test will publish a real tweet to your X account. Use a clearly marked test phrase so it is easy to delete afterward.

**6.** Delete the test tweet from X after confirming it posted correctly.

**7.** In Notion, mark the test insight bullet as `[STATUS: TEST | DONE]` or remove it from the queue.

---

## Part 8: Production Activation Checklist

Complete every item before activating:

- [ ] PostgreSQL: 3 tables created, test connection green in n8n
- [ ] Telegram: credential saved, chat ID confirmed, test message received
- [ ] X API: OAuth 1.0a saved, Bearer Token saved, profile read test passed
- [ ] Notion: n8n-AGS integration has access to Ops Hub including sub-pages, all 4 test script checks PASS
- [ ] HITL Handler workflow: toggled ACTIVE
- [ ] Analytics workflow: toggled ACTIVE
- [ ] Main workflow: all credentials set, no yellow warning icons on any node
- [ ] Main workflow: Telegram chat ID updated in all Telegram Send Message nodes
- [ ] Test run completed: Approve button worked end-to-end, tweet published to X
- [ ] Test tweet deleted from X
- [ ] Test insight removed or marked in Notion queue

When all items above are checked:

**1.** Open the main workflow in n8n.

**2.** Toggle to Active (ON).

**3.** First automated run: next 09:00 CET.

---

## Part 9: Daily Operations

**Monitoring:** Check Telegram each morning. The analytics digest arrives at 10:00 CET with previous day performance.

**Adding content to queue:** Add bullet points to the X Content Queue page in Notion. The workflow picks up any item without a `[STATUS: PUBLISHED]` or `[STATUS: SKIP]` marker. Use `[HIGH]`, `[MED]`, or `[LOW]` prefix for priority (optional - defaults to MED if omitted).

**Manual trigger:** Available in n8n any time. Open main workflow > Execute Workflow. Useful for processing a time-sensitive item immediately.

**Rate limit:** The workflow enforces a maximum of 5 posts per day regardless of how many items are in the queue.

**Error alerts:** Any workflow failure sends an automatic error message to your Telegram with the failed node name and error text.

---

## Appendix: Credential Name Reference

Names must match exactly as listed - no trailing spaces, no capitalization differences.

| System | n8n Credential Name | Type |
|--------|--------------------|----|
| Telegram Bot | `Telegram @ags_social_bot` | Telegram API |
| X API write | `X API AGS Content Automation` | OAuth1 API |
| X API read | `X API Bearer AGS` | HTTP Header Auth |
| Notion | `Notion n8n-AGS` | Notion API |
| PostgreSQL CRD | `PostgreSQL CRD ags-agents` | PostgreSQL |
| Anthropic | `Anthropic API AGS-n8n` | HTTP Header Auth |

---

## Appendix: Rollback

**To undo the database migration:**

1. SSH into Mikrus
2. `docker exec -it pg_n8n psql -U ags_crd_user -d ags_crd`
3. Paste contents of `scripts/crd-migrations/001_rollback.sql`
4. Verify with `\dt` - tables should be gone

**To deactivate the agent:**

1. n8n > open main workflow
2. Toggle to OFF (inactive)
3. The HITL Handler and Analytics workflows can remain active - they have no effect when the main workflow is off
