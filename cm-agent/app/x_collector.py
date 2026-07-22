"""Kolektor metryk WLASNYCH postow X - Owned Reads $0.001/read (BRIEF_KOLEKTOR_METRYK_X_19072026).

Sciezka zamknieta selekcja 19/07 (3 zbiezne raporty DR w docs/research/x_metrics_19072026/):
GET /2/users/{id}/tweets z tweet.fields=public/non_public/organic_metrics, OAuth 1.0a user
context (te same klucze co publisher: x_consumer_key/secret + x_access_token/secret).
Prywatne metryki (impression_count organic, url_link_clicks, user_profile_clicks) istnieja
TYLKO dla postow <30 dni - dzienny snapshot utrwala je w x_post_metric_snapshots (DDL 025)
zanim znikna. Followers: 1 odczyt /2/users/me dziennie -> channel_metrics_daily (DDL 023).

Wejscia w szyne:
- worker.loop() -> tick() raz na obieg (tani; durable dzienny guard po MAX(snapshot_date),
  restart kontenera NIE robi drugiego platnego zbioru tego samego dnia UTC);
- reports.refresh_metrics (stats_mode 'x_owned_reads') -> refresh_published_metrics():
  merge NAJNOWSZEGO snapshotu per post do published_posts.engagement_metrics - ZERO
  odczytow API przy raportach, placimy wylacznie w collect().

Guardraile kosztow (brief): >ALERT_RESOURCES zasobow/dzien -> alert na bota logow;
HARD_STOP_RESOURCES = twardy stop paginacji (Spend Cap $20/cykl w konsoli = 2. linia).

Sonda (DoD krok 1, Tomasz przez SSH, PRZED wlaczeniem stats_mode):
  docker exec cm-agent python -m app.x_collector probe
Reczny zbior (po wlaczeniu, bez czekania na tick):
  docker exec cm-agent python -m app.x_collector collect

ZAKAZY (brief sekcja 3): zadnego GET /2/tweets (Owned Read niepotwierdzony), zadnego
scrapingu. 30-dniowa granica prywatnych metryk -> start_time = now-29d (margines 1 dnia
na ryzyko 400 gdy post przekracza 30 dni miedzy stronami paginacji)."""
import base64
import datetime
import hashlib
import hmac
import json
import secrets as pysecrets
import sys
import time
import traceback
import urllib.parse

import httpx

from . import db, logbot

API = "https://api.x.com/2"
TWEET_FIELDS = "created_at,referenced_tweets,public_metrics,non_public_metrics,organic_metrics"
WINDOW_DAYS = 29            # twarde 30 dni prywatnych metryk minus 1 dzien marginesu
PAGE_SIZE = 100
ALERT_RESOURCES = 300       # guardrail: alert logbot powyzej. 22/07: podniesiony z 200 -
                            # okno 29 dni obejmuje jeszcze powodz postow 13-19/07 (~205 szt.),
                            # wiec 200 halasowalo CODZIENNIE przy normalnej pracy; koszt widac
                            # w samym alercie ($0.001/zasob), 300 nadal lapie anomalie.
HARD_STOP_RESOURCES = 500   # twardy stop paginacji (nie powinien nigdy zagrac przy ~150 postach)
CHECK_INTERVAL_S = 600      # jak brand_tokens_pull: nie odpytuj channels czesciej niz co 10 min
_last_check = [0.0]


# ---------------- OAuth 1.0a (HMAC-SHA1, stdlib - zero nowych zaleznosci) ----------------
def _pct(s):
    """RFC 3986 percent-encoding (quote nie koduje ALPHA/DIGIT/'_.-~' - dokladnie unreserved)."""
    return urllib.parse.quote(str(s), safe="")


def oauth1_signature(method, url, params, oauth_params, consumer_secret, token_secret):
    """Podpis bazowy OAuth 1.0a: sortowanie PO zakodowaniu, klucz = enc(cs)&enc(ts).
    Czysta funkcja - testowana lokalnie na wektorze z oficjalnej dokumentacji."""
    pairs = sorted((_pct(k), _pct(v)) for k, v in {**params, **oauth_params}.items())
    pstr = "&".join(f"{k}={v}" for k, v in pairs)
    base = f"{method.upper()}&{_pct(url)}&{_pct(pstr)}"
    key = f"{_pct(consumer_secret)}&{_pct(token_secret)}"
    return base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()


def _creds():
    vals = [db.get_secret(k) for k in ("x_consumer_key", "x_consumer_secret",
                                       "x_access_token", "x_access_token_secret")]
    if not all(vals):
        raise RuntimeError("brak kompletu kluczy OAuth1 X w app_secrets (x_consumer_key/secret, x_access_token/secret)")
    return vals


def _oauth1_get(url, params, creds):
    """GET z naglowkiem OAuth1. Query string budowany RECZNIE tym samym enkodowaniem co podpis
    (httpx nie moze przekodowac inaczej niz baza podpisu - inaczej 401)."""
    ck, cs, at, ats = creds
    oauth = {
        "oauth_consumer_key": ck,
        "oauth_nonce": pysecrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": at,
        "oauth_version": "1.0",
    }
    oauth["oauth_signature"] = oauth1_signature("GET", url, params, oauth, cs, ats)
    auth = "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))
    full = url + ("?" + "&".join(f"{_pct(k)}={_pct(v)}" for k, v in sorted(params.items())) if params else "")
    return httpx.get(full, headers={"Authorization": auth}, timeout=30)


# ---------------- pomocnicze ----------------
def _channel_cfg(brand_id, channel):
    ch = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s", (brand_id, channel))
    return (ch or {}).get("config") or {}


def _user_id(brand_id, channel, cfg, creds):
    """Numeryczne id uzytkownika: raz z /2/users/me, potem cache w channels.config.x_user_id
    (brief: 'user id zapisac raz'; decyzja ze szkieletu D2: channels.config celu)."""
    uid = str(cfg.get("x_user_id") or "").strip()
    if uid:
        return uid
    r = _oauth1_get(f"{API}/users/me", {}, creds)
    r.raise_for_status()
    uid = r.json()["data"]["id"]
    db.execute(
        """UPDATE channels SET config = jsonb_set(COALESCE(config,'{}'::jsonb),'{x_user_id}', to_jsonb(%s::text))
           WHERE brand_id=%s AND channel=%s""",
        (uid, brand_id, channel))
    print(f"[x_collector] x_user_id={uid} zapisany w channels.config {brand_id}/{channel}", flush=True)
    return uid


def _start_time():
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=WINDOW_DAYS)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_timeline(uid, creds):
    """Paginacja timeline'u wlasnych postow w oknie 29 dni. Zwraca (tweets, resources_read).
    Kazdy zwrocony post = 1 platny Owned Read - licznik jest zrodlem guardraila."""
    tweets, resources, token = [], 0, None
    while True:
        params = {"max_results": PAGE_SIZE, "start_time": _start_time(),
                  "tweet.fields": TWEET_FIELDS, "exclude": "retweets"}
        if token:
            params["pagination_token"] = token
        r = _oauth1_get(f"{API}/users/{uid}/tweets", params, creds)
        if r.status_code != 200:
            raise RuntimeError(f"X API {r.status_code}: {r.text[:300]}")
        data = r.json()
        page = data.get("data") or []
        tweets.extend(page)
        resources += len(page)
        token = (data.get("meta") or {}).get("next_token")
        if not token or not page:
            break
        if resources >= HARD_STOP_RESOURCES:
            logbot.send(f"⛔ x_collector: twardy stop paginacji na {resources} zasobach "
                        f"(limit {HARD_STOP_RESOURCES}) - sprawdz co sie dzieje w Developer Console")
            break
    return tweets, resources


def _followers(creds):
    r = _oauth1_get(f"{API}/users/me", {"user.fields": "public_metrics"}, creds)
    if r.status_code != 200:
        return None
    return ((r.json().get("data") or {}).get("public_metrics") or {}).get("followers_count")


def _store_snapshots(brand_id, channel, tweets):
    for t in tweets:
        db.execute(
            """INSERT INTO x_post_metric_snapshots
                 (brand_id, channel, tweet_id, created_at_x, public_metrics, non_public_metrics, organic_metrics, raw)
               VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb)
               ON CONFLICT (tweet_id, snapshot_date) DO UPDATE SET
                 observed_at = NOW(),
                 public_metrics = EXCLUDED.public_metrics,
                 non_public_metrics = EXCLUDED.non_public_metrics,
                 organic_metrics = EXCLUDED.organic_metrics,
                 raw = EXCLUDED.raw""",
            (brand_id, channel, t.get("id"), t.get("created_at"),
             json.dumps(t.get("public_metrics")), json.dumps(t.get("non_public_metrics")),
             json.dumps(t.get("organic_metrics")), json.dumps(t)))


def _store_followers(brand_id, channel, followers):
    """Followers dnia -> channel_metrics_daily (source 'x_api' przy insercie; przy konflikcie
    NIE nadpisujemy zrodla ani metryk z innych zrodel - tylko pola followers)."""
    if followers is None:
        return
    today = datetime.datetime.now(datetime.timezone.utc).date()
    prev = db.fetchone(
        """SELECT followers_total FROM channel_metrics_daily
           WHERE brand_id=%s AND channel=%s AND metric_date < %s AND followers_total IS NOT NULL
           ORDER BY metric_date DESC LIMIT 1""",
        (brand_id, channel, today))
    new_f = followers - prev["followers_total"] if prev and prev.get("followers_total") is not None else None
    db.execute(
        """INSERT INTO channel_metrics_daily (brand_id, channel, metric_date, new_followers, followers_total, source, raw)
           VALUES (%s,%s,%s,%s,%s,'x_api',%s::jsonb)
           ON CONFLICT (brand_id, channel, metric_date) DO UPDATE SET
             followers_total = EXCLUDED.followers_total,
             new_followers = COALESCE(EXCLUDED.new_followers, channel_metrics_daily.new_followers),
             raw = COALESCE(channel_metrics_daily.raw,'{}'::jsonb) || COALESCE(EXCLUDED.raw,'{}'::jsonb)""",
        (brand_id, channel, today, new_f, followers,
         json.dumps({"x_followers_total": followers})))


def snapshot_to_metrics(public_metrics, non_public_metrics):
    """Mapowanie namespaces API -> klucze engagement_metrics (METRIC_KEYS z reports.py).
    Czysta funkcja - test lokalny. impressions: prywatny impression_count ma priorytet
    (pelniejszy), fallback publiczny; reshares = retweet + quote."""
    pub = public_metrics or {}
    npm = non_public_metrics or {}
    m = {"impressions": npm.get("impression_count", pub.get("impression_count", 0)) or 0,
         "reactions": pub.get("like_count", 0) or 0,
         "comments": pub.get("reply_count", 0) or 0,
         "reshares": (pub.get("retweet_count", 0) or 0) + (pub.get("quote_count", 0) or 0),
         "clicks": npm.get("url_link_clicks", 0) or 0,
         "profile_clicks": npm.get("user_profile_clicks", 0) or 0}
    inter = m["reactions"] + m["comments"] + m["reshares"] + m["clicks"]
    if m["impressions"]:
        m["engagement_rate"] = round(inter / m["impressions"], 5)
    return m


def refresh_published_metrics(brand_id, channel, days=WINDOW_DAYS):
    """Szew reports.refresh_metrics (stats_mode 'x_owned_reads'): najnowszy snapshot per post
    -> merge do published_posts.engagement_metrics (match post_id=tweet_id). Zero API."""
    rows = db.fetchall(
        """SELECT DISTINCT ON (s.tweet_id) s.tweet_id, s.public_metrics, s.non_public_metrics,
                  p.id AS pub_id
           FROM x_post_metric_snapshots s
           JOIN published_posts p ON p.post_id = s.tweet_id AND p.brand=%s AND p.platform=%s
           WHERE s.brand_id=%s AND s.snapshot_date > CURRENT_DATE - %s::int
           ORDER BY s.tweet_id, s.snapshot_date DESC""",
        (brand_id, channel, brand_id, days))
    n = 0
    for r in rows:
        m = snapshot_to_metrics(r.get("public_metrics"), r.get("non_public_metrics"))
        m["source"] = "x_api"
        m["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute(
            "UPDATE published_posts SET engagement_metrics = COALESCE(engagement_metrics,'{}'::jsonb) || %s::jsonb WHERE id=%s",
            (json.dumps(m), r["pub_id"]))
        n += 1
    return n


# ---------------- glowne wejscia ----------------
def collect(brand_id="AGS", channel="x"):
    """Dzienny zbior: timeline 29 dni -> snapshoty + followers. Zwraca podsumowanie."""
    creds = _creds()
    cfg = _channel_cfg(brand_id, channel)
    uid = _user_id(brand_id, channel, cfg, creds)
    tweets, resources = _fetch_timeline(uid, creds)
    _store_snapshots(brand_id, channel, tweets)
    followers = _followers(creds)
    _store_followers(brand_id, channel, followers)
    resources += 1  # odczyt /users/me (followers) tez liczymy do budzetu dnia
    if resources > ALERT_RESOURCES:
        logbot.send(f"⚠️ x_collector {brand_id}/{channel}: {resources} zasobow Owned Reads dzisiaj "
                    f"(prog alertu {ALERT_RESOURCES}). Koszt dnia ~${resources * 0.001:.2f} - "
                    f"sprawdz Developer Console.")
    summary = {"posts": len(tweets), "resources": resources, "followers": followers}
    print(f"[x_collector] collect {brand_id}/{channel}: {summary}", flush=True)
    return summary


def tick():
    """Petla workera (worker._x_collector_tick): raz na dobe UTC per cel z stats_mode
    'x_owned_reads'. Guard DURABLE po MAX(snapshot_date) - restart nie powtarza zbioru.
    Brak celow / przed wlaczeniem stats_mode = cisza (zero kosztow)."""
    if time.time() - _last_check[0] < CHECK_INTERVAL_S:
        return
    _last_check[0] = time.time()
    try:
        targets = db.fetchall(
            """SELECT brand_id, channel FROM channels
               WHERE status='active' AND config->>'stats_mode'='x_owned_reads'""")
        today = datetime.datetime.now(datetime.timezone.utc).date()
        for t in targets:
            row = db.fetchone(
                "SELECT MAX(snapshot_date) AS d FROM x_post_metric_snapshots WHERE brand_id=%s AND channel=%s",
                (t["brand_id"], t["channel"]))
            if row and row.get("d") and row["d"] >= today:
                continue  # dzisiejszy zbior juz byl
            res = collect(t["brand_id"], t["channel"])
            from . import reports  # lazy - unik cyklu importow
            n = reports.refresh_metrics(t["brand_id"], t["channel"], days=WINDOW_DAYS)
            print(f"[x_collector] {t['brand_id']}/{t['channel']}: snapshoty {res['posts']}, "
                  f"engagement_metrics odswiezone dla {n} publikacji", flush=True)
    except Exception:
        traceback.print_exc()


def probe(brand_id="AGS", channel="x"):
    """SONDA (DoD krok 1): 1 request z pelnymi polami, max_results=5, BEZ zapisu snapshotow.
    Po niej Tomasz sprawdza w Developer Console klase rozliczenia (Owned Read $0.001)
    PRZED wlaczeniem stats_mode. Uruchomienie: docker exec cm-agent python -m app.x_collector probe"""
    creds = _creds()
    cfg = _channel_cfg(brand_id, channel)
    uid = _user_id(brand_id, channel, cfg, creds)
    r = _oauth1_get(f"{API}/users/{uid}/tweets",
                    {"max_results": 5, "start_time": _start_time(), "tweet.fields": TWEET_FIELDS,
                     "exclude": "retweets"}, creds)
    print(f"[probe] HTTP {r.status_code}", flush=True)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:6000], flush=True)
    if r.status_code != 200:
        print("[probe] FAIL - request odrzucony (patrz body wyzej)", flush=True)
        return False
    data = r.json().get("data") or []
    if not data:
        print("[probe] UWAGA: zero postow w oknie 29 dni - sonda nic nie kosztowala, "
              "ale nie potwierdza non_public_metrics", flush=True)
        return False
    with_npm = [t for t in data if t.get("non_public_metrics")]
    print(f"[probe] postow: {len(data)}, z non_public_metrics: {len(with_npm)}", flush=True)
    ok = bool(with_npm)
    print(f"[probe] {'PASS' if ok else 'FAIL'} - non_public_metrics "
          f"{'obecne' if ok else 'BRAK (sprawdz auth/wiek postow)'}; teraz sprawdz w Developer "
          f"Console czy rozliczono jako Owned Read $0.001 (DoD wymaga PRZED wlaczeniem crona)", flush=True)
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"
    args = sys.argv[2:4]
    if cmd == "probe":
        probe(*args)
    elif cmd == "collect":
        collect(*args)
    else:
        print("uzycie: python -m app.x_collector [probe|collect] [brand_id] [channel]", flush=True)
