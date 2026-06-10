#!/usr/bin/env python3
"""
AGS X Agent v1.0 - End-to-End Workflow Simulation
Dry-run by default. Simulates the full pipeline: read -> adapt -> canon check ->
preview -> publish sim -> log sim.

Set AGS_TEST_DRY_RUN=false AND TELEGRAM_CHAT_ID to send a real Telegram preview.
Set NOTION_API_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any

# Load .env - try dotenv first, fallback to os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NOTION_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DRY_RUN = os.environ.get("AGS_TEST_DRY_RUN", "true").lower() != "false"

NOTION_VERSION = "2022-06-28"
X_QUEUE_BLOCK_ID = "371c00c90b9381a0bc29e1dc22e5c244"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

FALLBACK_INSIGHT = (
    "6h build session. n8n workflow for X posting live. "
    "HITL approval before every post. First automation that actually saves my time."
)

# Step tracking
STEPS_TOTAL = 7
step_results: list[tuple[str, bool, str]] = []  # (label, passed, detail)


def truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def log_step(num: int, label: str, passed: bool, detail: str = "") -> None:
    symbol = "[PASS]" if passed else "[FAIL]"
    suffix = f": {detail}" if detail else ""
    print(f"STEP {num}/{STEPS_TOTAL} {label} ... {symbol}{suffix}")
    step_results.append((label, passed, detail))


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------
def notion_get(path: str) -> dict[str, Any]:
    url = f"https://api.notion.com/v1{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def extract_rich_text(rich_text_list: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def block_to_text(block: dict) -> str:
    btype = block.get("type", "")
    block_data = block.get(btype, {})
    if isinstance(block_data, dict):
        return extract_rich_text(block_data.get("rich_text", []))
    return ""


def read_x_content_queue() -> str | None:
    """Pull first non-empty insight text from X Content Queue."""
    result = notion_get(f"/blocks/{X_QUEUE_BLOCK_ID}/children?page_size=10")
    blocks = result.get("results", [])
    for block in blocks:
        text = block_to_text(block).strip()
        if text:
            return text
    return None


# ---------------------------------------------------------------------------
# Anthropic helpers
# ---------------------------------------------------------------------------
def claude_haiku(system: str, user: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": HAIKU_MODEL,
        "max_tokens": 512,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["content"][0]["text"].strip()


ADAPT_SYSTEM = """You are the AGS X Adapter. Convert raw founder insights into punchy X posts.

Rules:
- Max 280 characters (hard limit)
- Lead with the insight or contrast, not "I"
- No em dashes - use hyphens or restructure
- No buzzwords (game-changer, groundbreaking, revolutionary)
- Direct, confident, specific
- Add 1-2 relevant hashtags only if they fit naturally

Output ONLY the X post text. No explanation. No preamble."""

CANON_SYSTEM = """You are the AGS Canon Checker. Check if an X post follows AGS brand voice rules.

Rules to check:
1. No em dashes (use hyphens or restructure)
2. No buzzwords: game-changer, groundbreaking, revolutionary, disrupting, transformative
3. Value-first: lead with insight/problem, not price or promotion
4. No first-person brag opener starting with "I" as the first word
5. Max 280 characters
6. Confident but not arrogant tone

Output ONLY valid JSON in this format:
{"pass": true/false, "violations": ["list of violations or empty"], "char_count": 123}"""


# ---------------------------------------------------------------------------
# Telegram helper
# ---------------------------------------------------------------------------
def telegram_send(text: str) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
def step1_read_queue() -> tuple[bool, str]:
    """STEP 1/7 READ QUEUE"""
    print(f"\n--- STEP 1/{STEPS_TOTAL} READ QUEUE ---")
    if not NOTION_TOKEN:
        log_step(1, "READ QUEUE", False, "NOTION_API_TOKEN not set")
        return False, FALLBACK_INSIGHT

    try:
        insight = read_x_content_queue()
        if insight:
            print(f"       Found insight: {truncate(insight, 200)}")
            log_step(1, "READ QUEUE", True, f"{len(insight)} chars")
            return True, insight
        else:
            print(f"       WARNING: No insights found in X Queue. Using fallback insight.")
            print(f"       Fallback: {FALLBACK_INSIGHT}")
            log_step(1, "READ QUEUE", True, "no insights found - using fallback")
            return True, FALLBACK_INSIGHT
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        log_step(1, "READ QUEUE", False, f"HTTP {exc.code}: {truncate(body, 100)}")
        print(f"       Using fallback insight.")
        return False, FALLBACK_INSIGHT
    except Exception as exc:
        log_step(1, "READ QUEUE", False, str(exc))
        return False, FALLBACK_INSIGHT


def step2_adapt(insight: str) -> tuple[bool, str]:
    """STEP 2/7 ADAPT TO X"""
    print(f"\n--- STEP 2/{STEPS_TOTAL} ADAPT TO X ---")
    if not ANTHROPIC_KEY:
        log_step(2, "ADAPT TO X ", False, "ANTHROPIC_API_KEY not set")
        return False, ""

    try:
        draft = claude_haiku(ADAPT_SYSTEM, f"Raw insight to adapt:\n\n{insight}")
        char_count = len(draft)
        print(f"       Adapted draft ({char_count} chars):\n       {draft}")
        if char_count > 280:
            log_step(2, "ADAPT TO X ", False, f"draft is {char_count} chars - exceeds 280 limit")
            return False, draft
        log_step(2, "ADAPT TO X ", True, f"{char_count}/280 chars")
        return True, draft
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        log_step(2, "ADAPT TO X ", False, f"HTTP {exc.code}: {truncate(body, 100)}")
        return False, ""
    except Exception as exc:
        log_step(2, "ADAPT TO X ", False, str(exc))
        return False, ""


def step3_canon_check(draft: str) -> tuple[bool, dict]:
    """STEP 3/7 CANON CHECK"""
    print(f"\n--- STEP 3/{STEPS_TOTAL} CANON CHECK ---")
    if not ANTHROPIC_KEY:
        log_step(3, "CANON CHECK", False, "ANTHROPIC_API_KEY not set")
        return False, {}
    if not draft:
        log_step(3, "CANON CHECK", False, "no draft to check (step 2 failed)")
        return False, {}

    try:
        response_text = claude_haiku(CANON_SYSTEM, f"X post to check:\n\n{draft}")
        # Parse JSON response
        try:
            canon_result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                canon_result = json.loads(match.group())
            else:
                log_step(3, "CANON CHECK", False, f"could not parse JSON from: {truncate(response_text, 150)}")
                return False, {}

        passed = canon_result.get("pass", False)
        violations = canon_result.get("violations", [])
        char_count = canon_result.get("char_count", len(draft))

        if passed:
            print(f"       PASS - no violations ({char_count} chars)")
            log_step(3, "CANON CHECK", True, f"no violations, {char_count} chars")
        else:
            print(f"       FAIL - violations found:")
            for v in violations:
                print(f"         - {v}")
            log_step(3, "CANON CHECK", False, f"{len(violations)} violation(s)")

        return passed, canon_result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        log_step(3, "CANON CHECK", False, f"HTTP {exc.code}: {truncate(body, 100)}")
        return False, {}
    except Exception as exc:
        log_step(3, "CANON CHECK", False, str(exc))
        return False, {}


def step4_re_adapt_plan(canon_result: dict, draft: str, canon_passed: bool) -> bool:
    """STEP 4/7 RE-ADAPT PLAN"""
    print(f"\n--- STEP 4/{STEPS_TOTAL} RE-ADAPT PLAN ---")
    if canon_passed:
        print("       Canon check passed - no re-adapt needed")
        log_step(4, "RE-ADAPT   ", True, "skipped - canon passed")
        return True

    violations = canon_result.get("violations", [])
    print(f"       Canon failed with {len(violations)} violation(s). Re-adapt would:")
    for v in violations:
        print(f"         Fix: {v}")
    print(f"       Would re-run ADAPT prompt with violations list appended as constraints.")
    print(f"       (Not looping in test mode - this is a dry-run simulation)")
    log_step(4, "RE-ADAPT   ", True, f"plan logged - {len(violations)} violation(s) to fix")
    return True


def step5_preview(draft: str) -> bool:
    """STEP 5/7 TELEGRAM PREVIEW"""
    print(f"\n--- STEP 5/{STEPS_TOTAL} TELEGRAM PREVIEW ---")
    if not draft:
        log_step(5, "TG PREVIEW ", False, "no draft available")
        return False

    preview_text = (
        f"<b>AGS X Agent v1.0 - Post Preview</b>\n\n"
        f"{draft}\n\n"
        f"<i>Char count: {len(draft)}/280</i>\n\n"
        f"[This is a test preview - not for approval]"
    )
    print(f"       Formatted Telegram preview:\n{preview_text}")

    if DRY_RUN:
        print("       DRY RUN: Telegram preview NOT sent (set AGS_TEST_DRY_RUN=false to send)")
        log_step(5, "TG PREVIEW ", True, "dry run - message formatted but not sent")
        return True

    # Actually send
    if not TELEGRAM_TOKEN:
        log_step(5, "TG PREVIEW ", False, "TELEGRAM_BOT_TOKEN not set")
        return False
    if not TELEGRAM_CHAT_ID:
        log_step(5, "TG PREVIEW ", False, "TELEGRAM_CHAT_ID not set")
        return False

    try:
        result = telegram_send(preview_text)
        if result.get("ok"):
            msg_id = result["result"].get("message_id")
            print(f"       Preview sent to Telegram (message_id={msg_id})")
            log_step(5, "TG PREVIEW ", True, f"sent to chat_id={TELEGRAM_CHAT_ID}")
            return True
        else:
            log_step(5, "TG PREVIEW ", False, f"Telegram returned ok=false: {truncate(str(result))}")
            return False
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        log_step(5, "TG PREVIEW ", False, f"HTTP {exc.code}: {truncate(body, 100)}")
        return False
    except Exception as exc:
        log_step(5, "TG PREVIEW ", False, str(exc))
        return False


def step6_simulate_publish(draft: str) -> bool:
    """STEP 6/7 SIMULATE PUBLISH"""
    print(f"\n--- STEP 6/{STEPS_TOTAL} SIMULATE PUBLISH ---")
    if not draft:
        log_step(6, "PUBLISH SIM", False, "no draft available")
        return False

    post_body = {"text": draft}
    print(f"       X API POST /2/tweets would send:")
    print(f"       URL    : POST https://api.twitter.com/2/tweets")
    print(f"       Headers: Authorization: OAuth 1.0a ...")
    print(f"       Body   : {json.dumps(post_body, ensure_ascii=False, indent=2)}")
    print(f"       NOTE: Not posting - this is a dry run simulation")
    log_step(6, "PUBLISH SIM", True, "POST body logged - not sent")
    return True


def step7_log_sim(draft: str, insight: str) -> bool:
    """STEP 7/7 LOG SIMULATION"""
    print(f"\n--- STEP 7/{STEPS_TOTAL} LOG SIMULATION ---")
    ts = int(time.time())
    insert_sql = (
        f"INSERT INTO engagement_log "
        f"(tweet_id, tweet_text, posted_at, source_insight, likes, retweets, replies, impressions) "
        f"VALUES "
        f"('<tweet_id_here>', '{draft[:60].replace(chr(39), chr(39)*2)}...', "
        f"to_timestamp({ts}), '{insight[:40].replace(chr(39), chr(39)*2)}...', "
        f"0, 0, 0, 0);"
    )
    print(f"       Simulated PostgreSQL INSERT:")
    print(f"       {insert_sql}")
    print(f"       After posting, engagement_log.tweet_id would be filled with the real tweet ID.")
    log_step(7, "LOG SIM    ", True, "INSERT statement logged - no DB connection in test")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== AGS X AGENT v1.0 - END-TO-END WORKFLOW TEST ===")
    mode = "DRY RUN" if DRY_RUN else "LIVE (Telegram preview will be sent)"
    print(f"Mode: {mode}")
    print(f"Model: {HAIKU_MODEL}")

    missing = [k for k, v in {
        "NOTION_API_TOKEN": NOTION_TOKEN,
        "ANTHROPIC_API_KEY": ANTHROPIC_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_TOKEN,
    }.items() if not v]
    if missing:
        print(f"[WARN] Missing env vars: {', '.join(missing)} - some steps may fail")

    print()

    # Run pipeline
    ok_1, insight = step1_read_queue()
    ok_2, draft = step2_adapt(insight)
    ok_3, canon_result = step3_canon_check(draft)
    ok_4 = step4_re_adapt_plan(canon_result, draft, ok_3)
    ok_5 = step5_preview(draft)
    ok_6 = step6_simulate_publish(draft)
    ok_7 = step7_log_sim(draft, insight)

    # Summary
    results = [ok_1, ok_2, ok_3, ok_4, ok_5, ok_6, ok_7]
    passed = sum(results)
    ready = passed >= 6 and ok_2 and ok_3  # adapter + canon are critical

    print(f"\n{'=' * 55}")
    print(f"END-TO-END TEST: {passed}/{STEPS_TOTAL} steps passed.")
    print(f"Ready for production: {'YES' if ready else 'NO'}")
    print()

    for i, (label, step_ok, detail) in enumerate(step_results, 1):
        symbol = "[PASS]" if step_ok else "[FAIL]"
        print(f"  {symbol} Step {i}: {label.strip()}" + (f" - {detail}" if detail else ""))

    if not ready:
        print("\nFix failing steps before enabling the production workflow.")

    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
