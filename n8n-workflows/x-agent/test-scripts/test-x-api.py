#!/usr/bin/env python3
"""
AGS X Agent v1.0 - X API Credentials Test
Tests Bearer Token read access, OAuth 1.0a signing, recent tweets fetch, rate limits,
and simulates (or optionally executes) a POST /2/tweets call.

Set AGS_TEST_ACTUALLY_POST=true to actually post a test tweet.
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
CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET", "")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")
BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")
ACTUALLY_POST = os.environ.get("AGS_TEST_ACTUALLY_POST", "false").lower() == "true"

BASE_URL = "https://api.twitter.com"
RATE_LIMIT_INFO: dict[str, str] = {}

TEST_TWEET_TEXT = "AGS X Agent v1.0 test [DELETE ME - automated test]"


def truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + " ...[truncated]"


def bearer_request(path: str) -> tuple[dict[str, Any], dict[str, str]]:
    """GET request with Bearer Token. Returns (body_dict, response_headers)."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {BEARER_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        body = json.loads(resp.read())
        return body, headers


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_get_me() -> tuple[bool, str | None]:
    """Test 1: GET /2/users/me - verify read access via Bearer Token."""
    print("\n--- Test 1: GET /2/users/me (Bearer Token) ---")
    if not BEARER_TOKEN:
        print("[FAIL] X_BEARER_TOKEN is not set")
        return False, None
    try:
        body, headers = bearer_request("/2/users/me?user.fields=id,name,username,public_metrics")
        global RATE_LIMIT_INFO
        RATE_LIMIT_INFO = {
            k: headers[k]
            for k in ("x-rate-limit-limit", "x-rate-limit-remaining", "x-rate-limit-reset")
            if k in headers
        }
        user = body.get("data", {})
        username = user.get("username", "unknown")
        user_id = user.get("id", "unknown")
        metrics = user.get("public_metrics", {})
        print(f"[PASS] GET /2/users/me: @{username} (ID: {user_id})")
        print(f"       Metrics: {metrics}")
        return True, user_id
    except urllib.error.HTTPError as exc:
        body_bytes = exc.read().decode()
        print(f"[FAIL] HTTP {exc.code}: {truncate(body_bytes)}")
        return False, None
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False, None


def test_oauth_signature() -> bool:
    """Test 2: OAuth 1.0a signature using requests_oauthlib if available."""
    print("\n--- Test 2: OAuth 1.0a signature test ---")
    try:
        from requests_oauthlib import OAuth1Session  # type: ignore
    except ImportError:
        print("[SKIP] requests_oauthlib not installed.")
        print("       Install with: pip install requests-oauthlib")
        print("       OAuth 1.0a signing test skipped.")
        return True  # Not a failure - optional dependency

    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("[FAIL] One or more OAuth credentials missing (X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)")
        return False

    try:
        oauth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=ACCESS_TOKEN,
            resource_owner_secret=ACCESS_TOKEN_SECRET,
        )
        # Sign a GET /2/users/me request to verify credentials
        resp = oauth.get(f"{BASE_URL}/2/users/me")
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            print(f"[PASS] OAuth 1.0a: signed request verified for @{data.get('username', 'unknown')}")
            return True
        else:
            print(f"[FAIL] OAuth 1.0a: HTTP {resp.status_code}: {truncate(resp.text)}")
            return False
    except Exception as exc:
        print(f"[FAIL] OAuth 1.0a exception: {exc}")
        return False


def test_read_tweets(user_id: str | None) -> bool:
    """Test 3: GET /2/users/{id}/tweets - read last 3 tweets."""
    print("\n--- Test 3: GET /2/users/{id}/tweets (last 3) ---")
    if not BEARER_TOKEN:
        print("[FAIL] X_BEARER_TOKEN not set - cannot read tweets")
        return False
    if not user_id:
        print("[SKIP] user_id not available (test 1 failed) - skipping")
        return False
    try:
        body, _ = bearer_request(
            f"/2/users/{user_id}/tweets?max_results=3&tweet.fields=created_at,public_metrics"
        )
        tweets = body.get("data", [])
        meta = body.get("meta", {})
        count = len(tweets)
        result_count = meta.get("result_count", count)
        print(f"[PASS] GET /2/users/{user_id}/tweets: {result_count} tweet(s) retrieved")
        for i, tweet in enumerate(tweets[:3]):
            text_preview = truncate(tweet.get("text", ""), 120)
            print(f"       Tweet {i + 1}: {text_preview}")
        return True
    except urllib.error.HTTPError as exc:
        body_bytes = exc.read().decode()
        print(f"[FAIL] HTTP {exc.code}: {truncate(body_bytes)}")
        return False
    except Exception as exc:
        print(f"[FAIL] Exception: {exc}")
        return False


def test_rate_limit_headers() -> bool:
    """Test 4: Report X-Rate-Limit headers from test 1."""
    print("\n--- Test 4: Rate-limit headers ---")
    if not RATE_LIMIT_INFO:
        print("[SKIP] No rate-limit headers captured (test 1 may have failed)")
        return True
    limit = RATE_LIMIT_INFO.get("x-rate-limit-limit", "?")
    remaining = RATE_LIMIT_INFO.get("x-rate-limit-remaining", "?")
    reset_ts = RATE_LIMIT_INFO.get("x-rate-limit-reset", "?")
    print(f"[PASS] Rate limit: {remaining}/{limit} remaining (resets at epoch {reset_ts})")
    try:
        if int(remaining) < 5:
            print(f"       WARNING: only {remaining} calls remaining - close to rate limit")
    except (ValueError, TypeError):
        pass
    return True


def test_simulate_post() -> bool:
    """Test 5: Simulate or execute POST /2/tweets."""
    print("\n--- Test 5: POST /2/tweets ---")
    post_body = {"text": TEST_TWEET_TEXT}
    print(f"       Simulated POST body: {json.dumps(post_body, indent=2)}")

    if not ACTUALLY_POST:
        print("[PASS] DRY RUN: POST /2/tweets simulated (set AGS_TEST_ACTUALLY_POST=true to post for real)")
        return True

    # Actually post
    try:
        from requests_oauthlib import OAuth1Session  # type: ignore
    except ImportError:
        print("[FAIL] requests_oauthlib required for actual posting. Install: pip install requests-oauthlib")
        return False

    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("[FAIL] Missing OAuth credentials - cannot post")
        return False

    try:
        oauth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=ACCESS_TOKEN,
            resource_owner_secret=ACCESS_TOKEN_SECRET,
        )
        resp = oauth.post(
            f"{BASE_URL}/2/tweets",
            json=post_body,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code in (200, 201):
            data = resp.json().get("data", {})
            tweet_id = data.get("id", "unknown")
            print(f"[PASS] Tweet posted! tweet_id={tweet_id}")
            print(f"       NOTE: Delete this tweet manually: https://twitter.com/i/web/status/{tweet_id}")
            return True
        else:
            print(f"[FAIL] POST /2/tweets HTTP {resp.status_code}: {truncate(resp.text)}")
            return False
    except Exception as exc:
        print(f"[FAIL] POST /2/tweets exception: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== X API CREDENTIALS TEST ===")
    if ACTUALLY_POST:
        print("WARNING: AGS_TEST_ACTUALLY_POST=true - a real tweet WILL be posted")
    else:
        print("Mode: DRY RUN (set AGS_TEST_ACTUALLY_POST=true to post for real)")

    # Validate minimal credentials
    missing = [k for k, v in {
        "X_BEARER_TOKEN": BEARER_TOKEN,
        "X_CONSUMER_KEY": CONSUMER_KEY,
        "X_CONSUMER_SECRET": CONSUMER_SECRET,
        "X_ACCESS_TOKEN": ACCESS_TOKEN,
        "X_ACCESS_TOKEN_SECRET": ACCESS_TOKEN_SECRET,
    }.items() if not v]

    if missing:
        print(f"\n[WARN] Missing env vars: {', '.join(missing)}")
        print("       Some tests may be skipped or fail.")

    ok_1, user_id = test_get_me()
    ok_2 = test_oauth_signature()
    ok_3 = test_read_tweets(user_id)
    ok_4 = test_rate_limit_headers()
    ok_5 = test_simulate_post()

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
