#!/usr/bin/env python3
"""
AGS X Agent v1.0 - Telegram Connectivity Test
Tests bot token validity, recent updates, message send, and inline keyboard send.
"""

import json
import os
import sys

# Load .env - try dotenv first, fallback to os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # os.environ already available

import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _request(path: str, payload: dict | None = None) -> dict:
    url = f"{BASE_URL}/{path}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_get_me() -> bool:
    print("\n--- Test 1: getMe ---")
    try:
        result = _request("getMe")
        if not result.get("ok"):
            print(f"[FAIL] getMe returned ok=false: {truncate(str(result))}")
            return False
        bot = result["result"]
        username = bot.get("username", "unknown")
        bot_id = bot.get("id", "unknown")
        print(f"[PASS] getMe: @{username} (ID: {bot_id})")
        print(f"       Full response: {truncate(str(bot))}")
        return True
    except urllib.error.HTTPError as exc:
        print(f"[FAIL] HTTP {exc.code}: {exc.reason} - check TELEGRAM_BOT_TOKEN")
        return False
    except Exception as exc:
        print(f"[FAIL] getMe exception: {exc}")
        return False


def test_get_updates() -> bool:
    print("\n--- Test 2: getUpdates ---")
    try:
        result = _request("getUpdates?limit=3&offset=-3")
        if not result.get("ok"):
            print(f"[FAIL] getUpdates returned ok=false: {truncate(str(result))}")
            return False
        updates = result.get("result", [])
        count = len(updates)
        print(f"[PASS] getUpdates: {count} recent update(s) found")
        for i, upd in enumerate(updates):
            msg = upd.get("message") or upd.get("callback_query", {})
            summary = truncate(str(msg))
            print(f"       Update {i + 1}: {summary}")
        return True
    except Exception as exc:
        print(f"[FAIL] getUpdates exception: {exc}")
        return False


def test_send_message() -> bool:
    print("\n--- Test 3: sendMessage ---")
    if not CHAT_ID:
        print("[SKIP] TELEGRAM_CHAT_ID not set - skipping send test")
        return True  # not a failure - optional
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "AGS X Agent v1.0 - Telegram test [DELETE]",
        }
        result = _request("sendMessage", payload)
        if not result.get("ok"):
            print(f"[FAIL] sendMessage returned ok=false: {truncate(str(result))}")
            return False
        msg_id = result["result"].get("message_id")
        print(f"[PASS] Test message sent to chat_id={CHAT_ID} (message_id={msg_id})")
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"[FAIL] HTTP {exc.code}: {truncate(body)}")
        return False
    except Exception as exc:
        print(f"[FAIL] sendMessage exception: {exc}")
        return False


def test_inline_keyboard() -> bool:
    print("\n--- Test 4: Inline keyboard ---")
    if not CHAT_ID:
        print("[SKIP] TELEGRAM_CHAT_ID not set - skipping inline keyboard test")
        return True
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "AGS X Agent v1.0 - Inline keyboard test",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "Test Approve", "callback_data": "test:approve"},
                        {"text": "Test Reject", "callback_data": "test:reject"},
                    ]
                ]
            },
        }
        result = _request("sendMessage", payload)
        if not result.get("ok"):
            print(f"[FAIL] Inline keyboard send returned ok=false: {truncate(str(result))}")
            return False
        msg_id = result["result"].get("message_id")
        print(f"[PASS] Inline keyboard test sent to chat_id={CHAT_ID} (message_id={msg_id})")
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"[FAIL] HTTP {exc.code}: {truncate(body)}")
        return False
    except Exception as exc:
        print(f"[FAIL] Inline keyboard exception: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== TELEGRAM CONNECTIVITY TEST ===")

    if not BOT_TOKEN:
        print("[FAIL] TELEGRAM_BOT_TOKEN is not set. Set it in .env or environment.")
        sys.exit(1)

    results = [
        test_get_me(),
        test_get_updates(),
        test_send_message(),
        test_inline_keyboard(),
    ]

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
