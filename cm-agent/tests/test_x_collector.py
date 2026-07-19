"""Testy lokalne kolektora X (BRIEF_KOLEKTOR_METRYK_X_19072026) - stdlib only, bez serwera.
Uruchomienie: python cm-agent/tests/test_x_collector.py
Stuby app.db / app.logbot / httpx wchodza do sys.modules PRZED importem modulu, wiec test
nie potrzebuje psycopg ani polaczenia z PG (zakaz deployu w trybie rownoleglym)."""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

# --- stuby zaleznosci (przed importem app.x_collector) ---
fake_httpx = types.ModuleType("httpx")
fake_httpx.get = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("httpx.get nie podstawiony w tescie"))
sys.modules["httpx"] = fake_httpx

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

fake_db = types.ModuleType("app.db")
fake_db.calls = []
fake_db.get_secret = lambda k: f"stub_{k}"
fake_db.fetchone = lambda sql, p=None: None
fake_db.fetchall = lambda sql, p=None: []
fake_db.execute = lambda sql, p=None: fake_db.calls.append((sql, p))
sys.modules["app.db"] = fake_db

fake_logbot = types.ModuleType("app.logbot")
fake_logbot.sent = []
fake_logbot.send = lambda text: fake_logbot.sent.append(text)
sys.modules["app.logbot"] = fake_logbot

import importlib
xc = importlib.import_module("app.x_collector")

FAILURES = []


def check(name, cond, detail=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# --- 1. Podpis OAuth 1.0a: oficjalny wektor z docs.x.com "Creating a signature"
# (zweryfikowany WebFetch 19/07/2026: URL api.x.com/1.1, podpis Ls93hJiZbQ3akF3HF3x1Bz8/zU4=) ---
sig = xc.oauth1_signature(
    "POST", "https://api.x.com/1.1/statuses/update.json",
    {"status": "Hello Ladies + Gentlemen, a signed OAuth request!", "include_entities": "true"},
    {"oauth_consumer_key": "xvz1evFS4wEEPTGEFPHBog",
     "oauth_nonce": "kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg",
     "oauth_signature_method": "HMAC-SHA1",
     "oauth_timestamp": "1318622958",
     "oauth_token": "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
     "oauth_version": "1.0"},
    "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
    "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE")
check("oauth1_signature = wektor z docs", sig == "Ls93hJiZbQ3akF3HF3x1Bz8/zU4=", f"got {sig}")

# --- 2. Percent-encoding RFC 3986 ---
check("pct: spacja -> %20", xc._pct("a b") == "a%20b")
check("pct: '!' -> %21", xc._pct("a!") == "a%21")
check("pct: unreserved bez zmian", xc._pct("Az0-._~") == "Az0-._~")
check("pct: ':' w timestamp -> %3A", xc._pct("2026-07-19T00:00:00Z") == "2026-07-19T00%3A00%3A00Z")

# --- 3. Mapowanie snapshot -> engagement_metrics ---
m = xc.snapshot_to_metrics(
    {"impression_count": 100, "like_count": 5, "reply_count": 2, "retweet_count": 3, "quote_count": 1},
    {"impression_count": 613, "url_link_clicks": 9, "user_profile_clicks": 4})
check("map: impressions z non_public ma priorytet", m["impressions"] == 613)
check("map: reshares = retweet+quote", m["reshares"] == 4)
check("map: clicks/profile_clicks z non_public", m["clicks"] == 9 and m["profile_clicks"] == 4)
check("map: engagement_rate = (5+2+4+9)/613", m["engagement_rate"] == round(20 / 613, 5))

m2 = xc.snapshot_to_metrics({"impression_count": 50, "like_count": 1}, None)
check("map: fallback public impressions gdy brak non_public", m2["impressions"] == 50)
check("map: brakujace pola = 0", m2["clicks"] == 0 and m2["reshares"] == 0)

m3 = xc.snapshot_to_metrics({}, {})
check("map: zero impressions = brak engagement_rate", "engagement_rate" not in m3)

# --- 4. Paginacja timeline + twardy stop ---
class R:
    def __init__(self, payload):
        self.status_code = 200
        self._p = payload

    def json(self):
        return self._p


def pages(seq):
    it = iter(seq)

    def get(url, headers=None, timeout=None):
        return next(it)
    return get

# dwie strony: 100 + 30, potem koniec (brak next_token)
fake_httpx.get = pages([
    R({"data": [{"id": str(i)} for i in range(100)], "meta": {"next_token": "t2"}}),
    R({"data": [{"id": str(100 + i)} for i in range(30)], "meta": {}}),
])
tweets, res = xc._fetch_timeline("123", ("ck", "cs", "at", "ats"))
check("paginacja: 2 strony -> 130 postow", len(tweets) == 130 and res == 130)

# twardy stop: strony po 100 z wiecznym next_token -> stop na HARD_STOP_RESOURCES
fake_logbot.sent.clear()
fake_httpx.get = pages([R({"data": [{"id": str(j)} for j in range(100)],
                           "meta": {"next_token": "t"}}) for _ in range(20)])
tweets, res = xc._fetch_timeline("123", ("ck", "cs", "at", "ats"))
check("twardy stop na 500 zasobach", res == xc.HARD_STOP_RESOURCES, f"res={res}")
check("twardy stop wysyla alert logbot", len(fake_logbot.sent) == 1)

# blad API -> wyjatek (nie ciche zero)
class RBad:
    status_code = 429
    text = "rate limit"

    def json(self):
        return {}


fake_httpx.get = lambda *a, **k: RBad()
try:
    xc._fetch_timeline("123", ("ck", "cs", "at", "ats"))
    check("HTTP!=200 rzuca wyjatek", False)
except RuntimeError as e:
    check("HTTP!=200 rzuca wyjatek", "429" in str(e))

# --- podsumowanie ---
print(f"\n{'PASS - wszystkie testy OK' if not FAILURES else 'FAIL: ' + ', '.join(FAILURES)}")
sys.exit(1 if FAILURES else 0)
