#!/usr/bin/env python3
"""
AGS X Agent v1.0 - Notion API Access Test
Verifies integration token validity and access to specific AGS Notion pages/databases.

Page IDs under test:
  X Content Queue : 371c00c90b9381a0bc29e1dc22e5c244
  AGS Ops Hub    : 318c00c90b9381f69449ee3f8546ca33
  CRD doc page   : 371c00c90b9381ec9b13c1d910c9a547
"""

import json
import os
import sys
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
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

# Page / block IDs
X_QUEUE_BLOCK_ID = "371c00c90b9381a0bc29e1dc22e5c244"
AGS_OPS_HUB_BLOCK_ID = "318c00c90b9381f69449ee3f8546ca33"
CRD_PAGE_BLOCK_ID = "371c00c90b9381ec9b13c1d910c9a547"


def truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def notion_get(path: str) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def handle_notion_error(exc: urllib.error.HTTPError, page_label: str) -> None:
    body = exc.read().decode()
    try:
        err = json.loads(body)
        code = err.get("code", "")
        message = err.get("message", "")
    except json.JSONDecodeError:
        code = ""
        message = body

    if exc.code == 403 or code == "restricted_resource":
        print(f"[FAIL] 403 - Missing page access. Share [{page_label}] with the n8n-AGS integration.")
    elif exc.code == 404 or code == "object_not_found":
        print(f"[FAIL] 404 - Page/block not found: {page_label}. Check the block ID.")
    elif exc.code == 401:
        print(f"[FAIL] 401 - Invalid NOTION_API_TOKEN. Check your integration token.")
    else:
        print(f"[FAIL] HTTP {exc.code} on [{page_label}]: {truncate(message)}")


# ---------------------------------------------------------------------------
# Block text extraction helpers
# ---------------------------------------------------------------------------
def extract_rich_text(rich_text_list: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def block_to_text(block: dict) -> str:
    """Extract readable text from a Notion block object."""
    btype = block.get("type", "")
    block_data = block.get(btype, {})
    if isinstance(block_data, dict):
        rich_text = block_data.get("rich_text", [])
        if rich_text:
            return extract_rich_text(rich_text)
    return ""


def parse_insight(block: dict) -> dict:
    """Convert a content block into a minimal insight dict."""
    text = block_to_text(block)
    return {
        "block_id": block.get("id", ""),
        "type": block.get("type", ""),
        "text": text,
        "char_count": len(text),
        "has_content": bool(text.strip()),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_get_me() -> bool:
    """Test 1: GET /v1/users/me - verify integration token."""
    print("\n--- Test 1: GET /v1/users/me ---")
    if not NOTION_TOKEN:
        print("[FAIL] NOTION_API_TOKEN is not set")
        return False
    try:
        result = notion_get("/users/me")
        name = result.get("name", "unknown")
        bot = result.get("bot", {})
        workspace = bot.get("workspace_name", "unknown")
        user_type = result.get("type", "?")
        print(f"[PASS] Integration verified: '{name}' (type={user_type}, workspace='{workspace}')")
        print(f"       Full response: {truncate(str(result))}")
        return True
    except urllib.error.HTTPError as exc:
        handle_notion_error(exc, "users/me")
        return False
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False


def test_x_queue(block_id: str = X_QUEUE_BLOCK_ID) -> tuple[bool, dict | None]:
    """Test 2: GET /v1/blocks/{id}/children - X Content Queue, print first 2 items."""
    print(f"\n--- Test 2: X Content Queue ({block_id}) ---")
    if not NOTION_TOKEN:
        print("[FAIL] NOTION_API_TOKEN not set")
        return False, None
    try:
        result = notion_get(f"/blocks/{block_id}/children?page_size=5")
        blocks = result.get("results", [])
        count = len(blocks)
        print(f"[PASS] X Content Queue accessed: {count} top-level block(s) retrieved")
        first_insight = None
        shown = 0
        for block in blocks:
            text = block_to_text(block)
            if text.strip():
                if shown < 2:
                    print(f"       Item {shown + 1}: {truncate(text, 200)}")
                    shown += 1
                if first_insight is None:
                    first_insight = block
        if shown == 0:
            print("       (no text blocks with content found in first 5 blocks)")
        return True, first_insight
    except urllib.error.HTTPError as exc:
        handle_notion_error(exc, "X Content Queue")
        return False, None
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False, None


def test_ops_hub(block_id: str = AGS_OPS_HUB_BLOCK_ID) -> bool:
    """Test 3: GET /v1/blocks/{id} - AGS Ops Hub access."""
    print(f"\n--- Test 3: AGS Ops Hub ({block_id}) ---")
    if not NOTION_TOKEN:
        print("[FAIL] NOTION_API_TOKEN not set")
        return False
    try:
        result = notion_get(f"/blocks/{block_id}")
        btype = result.get("type", "unknown")
        block_id_resp = result.get("id", "?")
        print(f"[PASS] AGS Ops Hub block accessible (type={btype}, id={block_id_resp})")
        return True
    except urllib.error.HTTPError as exc:
        handle_notion_error(exc, "AGS Ops Hub")
        return False
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False


def test_crd_page(block_id: str = CRD_PAGE_BLOCK_ID) -> bool:
    """Test 4: GET /v1/blocks/{id} - CRD doc page access."""
    print(f"\n--- Test 4: CRD Doc Page ({block_id}) ---")
    if not NOTION_TOKEN:
        print("[FAIL] NOTION_API_TOKEN not set")
        return False
    try:
        result = notion_get(f"/blocks/{block_id}")
        btype = result.get("type", "unknown")
        block_id_resp = result.get("id", "?")
        print(f"[PASS] CRD doc page accessible (type={btype}, id={block_id_resp})")
        return True
    except urllib.error.HTTPError as exc:
        handle_notion_error(exc, "CRD doc page")
        return False
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False


def test_parse_insight(first_block: dict | None) -> bool:
    """Test 5: Parse first non-empty block into insight dict."""
    print("\n--- Test 5: Parse insight from X Queue block ---")
    if first_block is None:
        print("[SKIP] No block available from test 2 to parse")
        return True
    insight = parse_insight(first_block)
    if not insight["has_content"]:
        print("[WARN] Block found but contained no readable text")
    print(f"[PASS] Parsed insight dict:")
    print(f"       block_id  : {insight['block_id']}")
    print(f"       type      : {insight['type']}")
    print(f"       char_count: {insight['char_count']}")
    print(f"       text      : {truncate(insight['text'], 200)}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== NOTION API ACCESS TEST ===")

    if not NOTION_TOKEN:
        print("[FAIL] NOTION_API_TOKEN is not set. Set it in .env or environment.")
        sys.exit(1)

    ok_1 = test_get_me()
    ok_2, first_block = test_x_queue()
    ok_3 = test_ops_hub()
    ok_4 = test_crd_page()
    ok_5 = test_parse_insight(first_block)

    results = [ok_1, ok_2, ok_3, ok_4, ok_5]
    passed = sum(results)
    total = len(results)

    print(f"\n=== RESULT: {passed}/{total} TESTS PASSED ===")
    if passed == total:
        print("[PASS] ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("[FAIL] SOME TESTS FAILED - check output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
