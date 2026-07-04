"""R3 raporty subagentow: kolektor metryk per cel + raport dzienny/tygodniowy + push na kanal logowy.
stats_mode per cel (channels.config): 'manual' (default; X - read API zablokowane na tierze),
'member_api' (LinkedIn profil osobisty: memberCreatorPostAnalytics, scope r_member_postAnalytics),
'org_api' (strona firmowa: organizationalEntityShareStatistics, rw_organization_admin + config.org_urn).
Fakty API: docs/research/LINKEDIN_STATISTICS_API_2026.md. Tokeny bez wymaganego scope -> kolektor
pomija cel bez crashy (metryki LinkedIn wchodza po review App 2 CMA)."""
import datetime
import json
import urllib.parse
from zoneinfo import ZoneInfo

import httpx
from psycopg.types.json import Jsonb

from . import db, config, tasks, logbot
from .generate import client

WARSAW = ZoneInfo("Europe/Warsaw")
METRIC_KEYS = ("impressions", "unique_reach", "reactions", "comments", "reshares", "clicks")
_MEMBER_MAP = {"IMPRESSION": "impressions", "MEMBERS_REACHED": "unique_reach", "REACTION": "reactions",
               "COMMENT": "comments", "RESHARE": "reshares", "LINK_CLICKS": "clicks"}


def _li_headers(token):
    return {"Authorization": f"Bearer {token}",
            "LinkedIn-Version": config.LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0"}


def _collect_member_api(post_urn, token):
    """memberCreatorPostAnalytics: JEDNA metryka per wywolanie (fakt z docs)."""
    out = {}
    kind = "ugc" if ":ugcPost:" in (post_urn or "") else "share"
    ent = f"({kind}:{urllib.parse.quote(post_urn, safe='')})"
    for qt, key in _MEMBER_MAP.items():
        try:
            r = httpx.get(f"https://api.linkedin.com/rest/memberCreatorPostAnalytics?q=entity&entity={ent}&queryType={qt}",
                          headers=_li_headers(token), timeout=15)
            if r.status_code != 200:
                return None  # brak scope/entitlementu -> caly cel pomijamy (czekamy na App 2)
            els = r.json().get("elements") or []
            out[key] = int(els[0]["count"]) if els else 0
        except Exception:
            return None
    return out


def _collect_org_api(post_urn, token, org_urn):
    """organizationalEntityShareStatistics per share (strony firmowe)."""
    try:
        q = (f"https://api.linkedin.com/rest/organizationalEntityShareStatistics?q=organizationalEntity"
             f"&organizationalEntity={urllib.parse.quote(org_urn, safe='')}"
             f"&shares=List({urllib.parse.quote(post_urn, safe='')})")
        r = httpx.get(q, headers=_li_headers(token), timeout=15)
        if r.status_code != 200:
            return None
        els = r.json().get("elements") or []
        if not els:
            return {k: 0 for k in METRIC_KEYS}
        s = els[0].get("totalShareStatistics") or {}
        return {"impressions": s.get("impressionCount", 0), "unique_reach": s.get("uniqueImpressionsCount", 0),
                "reactions": s.get("likeCount", 0), "comments": s.get("commentCount", 0),
                "reshares": s.get("shareCount", 0), "clicks": s.get("clickCount", 0),
                "engagement_rate": s.get("engagement", 0.0)}
    except Exception:
        return None


def refresh_metrics(brand_id, channel, days=7):
    """Odswiez engagement_metrics dla publikacji celu wg stats_mode. 'manual' = nic (wpisy reczne)."""
    ch = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s", (brand_id, channel))
    cfg = (ch or {}).get("config") or {}
    mode = cfg.get("stats_mode", "manual")
    if mode == "manual":
        return 0
    prefix = cfg.get("secret_prefix", "linkedin")
    token = db.get_secret(f"{prefix}_access_token")
    if not token:
        return 0
    rows = db.fetchall(
        """SELECT id, post_id FROM published_posts
           WHERE brand=%s AND platform=%s AND post_id <> '' AND published_at > NOW() - make_interval(days => %s)""",
        (brand_id, channel, days))
    n = 0
    for r in rows:
        if mode == "member_api":
            m = _collect_member_api(r["post_id"], token)
        elif mode == "org_api" and cfg.get("org_urn"):
            m = _collect_org_api(r["post_id"], token, cfg["org_urn"])
        else:
            m = None
        if m is None:
            break  # scope/entitlement missing -> nie mlocic API dla reszty
        m["source"] = "api"
        m["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute("UPDATE published_posts SET engagement_metrics = COALESCE(engagement_metrics,'{}'::jsonb) || %s WHERE id=%s",
                   (Jsonb(m), r["id"]))
        n += 1
    return n


def set_manual_metrics(published_id, values, brand_id, channel):
    """Reczne wprowadzenie metryk (X: decyzja Managera #2). values = dict z METRIC_KEYS (czesciowy OK)."""
    m = {k: int(values[k]) for k in METRIC_KEYS if values.get(k) is not None}
    if not m:
        return None
    imp = m.get("impressions") or 0
    inter = sum(m.get(k, 0) for k in ("reactions", "comments", "reshares", "clicks"))
    if imp:
        m["engagement_rate"] = round(inter / imp, 5)
    m["source"] = "manual"
    m["fetched_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = db.fetchone(
        """UPDATE published_posts SET engagement_metrics = COALESCE(engagement_metrics,'{}'::jsonb) || %s
           WHERE id=%s AND brand=%s AND platform=%s RETURNING id""",
        (Jsonb(m), published_id, brand_id, channel))
    return m if row else None


# ---------------- raporty ----------------
def _sum_metrics(rows):
    total = {k: 0 for k in METRIC_KEYS}
    have = False
    for r in rows:
        em = r.get("engagement_metrics") or {}
        for k in METRIC_KEYS:
            if em.get(k) is not None:
                total[k] += int(em[k])
                have = True
    if total["impressions"]:
        inter = sum(total[k] for k in ("reactions", "comments", "reshares", "clicks"))
        total["engagement_rate"] = round(inter / total["impressions"], 5)
    return total if have else {}


def _decisions_since(brand_id, channel, hours):
    try:
        return db.fetchall(
            """SELECT log_type, rationale, created_at FROM agent_logs
               WHERE agent_id=%s AND log_type='AUTONOMOUS_DECISION' AND created_at > NOW() - make_interval(hours => %s)
               ORDER BY created_at""",
            (f"{brand_id}:{channel}", hours))
    except Exception:
        return []


def _queue_upcoming(brand_id, channel, limit=10):
    return db.fetchall(
        """SELECT id, status, content, scheduled_for FROM post_queue
           WHERE brand=%s AND platform=%s AND status IN ('review','scheduled','queued','held')
           ORDER BY scheduled_for NULLS LAST, id LIMIT %s""",
        (brand_id, channel, limit))


def _fmt_metrics(m):
    if not m:
        return "(brak metryk; X: wpisz w rozmowie z subagentem, LinkedIn: wejda po review App 2)"
    parts = [f"{k}: {m[k]}" for k in METRIC_KEYS if m.get(k)]
    if m.get("engagement_rate"):
        parts.append(f"engagement: {m['engagement_rate']:.2%}")
    return ", ".join(parts) or "(zera)"


def daily_report(brand_id, channel):
    """Raport dzienny (deterministyczny; push na kanal logowy bot #2). Zwraca report_text."""
    refresh_metrics(brand_id, channel, days=2)
    pub = db.fetchall(
        """SELECT id, content, post_url, engagement_metrics FROM published_posts
           WHERE brand=%s AND platform=%s AND published_at > NOW() - interval '24 hours' ORDER BY published_at""",
        (brand_id, channel))
    dec = _decisions_since(brand_id, channel, 24)
    queue = _queue_upcoming(brand_id, channel)
    lines = [f"📣 Raport dzienny {brand_id} {channel} ({datetime.datetime.now(WARSAW).strftime('%d/%m')})", ""]
    lines.append(f"OPUBLIKOWANE (24h): {len(pub)}")
    for p in pub:
        lines.append(f"- #{p['id']} {(p['content'] or '')[:60]} | {_fmt_metrics(p.get('engagement_metrics') or {})}")
    lines.append(f"\nMETRYKI (suma): {_fmt_metrics(_sum_metrics(pub))}")
    lines.append(f"\nDECYZJE AUTONOMICZNE: {len(dec)}")
    for d in dec:
        lines.append(f"- {d['rationale'][:100]}")
    lines.append(f"\nKOLEJKA (najblizsze): {len(queue)}")
    for q in queue[:5]:
        when = q["scheduled_for"].astimezone(WARSAW).strftime("%d/%m %H:%M") if q.get("scheduled_for") else "brak slotu"
        lines.append(f"- #{q['id']} [{q['status']}] {(q['content'] or '')[:50]} | {when}")
    text = "\n".join(lines)
    db.execute(
        """INSERT INTO subagent_daily_reports (brand_id, channel, report_date, published_count, engagement_metrics,
                                               autonomous_decisions, queue_snapshot, report_text)
           VALUES (%s,%s,CURRENT_DATE,%s,%s,%s,%s,%s)
           ON CONFLICT (brand_id, channel, report_date) DO UPDATE SET published_count=EXCLUDED.published_count,
             engagement_metrics=EXCLUDED.engagement_metrics, autonomous_decisions=EXCLUDED.autonomous_decisions,
             queue_snapshot=EXCLUDED.queue_snapshot, report_text=EXCLUDED.report_text, created_at=NOW()""",
        (brand_id, channel, len(pub), Jsonb(_sum_metrics(pub)),
         Jsonb([{"rationale": d["rationale"], "at": d["created_at"].isoformat()} for d in dec]),
         Jsonb([{"id": q["id"], "status": q["status"]} for q in queue]), text))
    logbot.send(text)
    return text


def weekly_report(brand_id, channel):
    """Raport tygodniowy: agregaty 7 dni + best/worst + rekomendacje (LLM tier 'weekly_report' gdy sa dane)."""
    refresh_metrics(brand_id, channel, days=7)
    pub = db.fetchall(
        """SELECT id, content, post_url, engagement_metrics, published_at FROM published_posts
           WHERE brand=%s AND platform=%s AND published_at > NOW() - interval '7 days' ORDER BY published_at""",
        (brand_id, channel))
    total = _sum_metrics(pub)
    scored = [p for p in pub if (p.get("engagement_metrics") or {}).get("impressions")]
    scored.sort(key=lambda p: (p["engagement_metrics"].get("engagement_rate") or 0), reverse=True)
    best, worst = scored[:3], scored[-3:] if len(scored) > 3 else []
    dec = _decisions_since(brand_id, channel, 24 * 7)
    reco = None
    if pub:
        try:
            model, tier, source = tasks.model_for("weekly_report")
            posts_txt = "\n".join(f"- {(p['content'] or '')[:100]} | {_fmt_metrics(p.get('engagement_metrics') or {})}" for p in pub)
            from . import conversation
            resp = client().messages.create(
                model=model, max_tokens=600, thinking={"type": "disabled"},
                messages=[{"role": "user", "content":
                           f"Jestes subagentem publikacji {brand_id}/{channel}. {conversation.comm_guide()} "
                           f"Na bazie tygodnia publikacji nizej napisz 3 zwiezle rekomendacje strategiczne dla "
                           f"Content Managera na nastepny tydzien (co powtorzyc, czego unikac, jaki kat wzmocnic). "
                           f"Zero lania wody.\n\n{posts_txt}"}])
            tasks.log_task("weekly_report", tier, model, source, getattr(resp, "usage", None))
            reco = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        except Exception:
            reco = None
    week_start = (datetime.datetime.now(WARSAW) - datetime.timedelta(days=7)).date()
    lines = [f"📊 Raport tygodniowy {brand_id} {channel} (od {week_start.strftime('%d/%m')})", ""]
    lines.append(f"PUBLIKACJE: {len(pub)} | METRYKI 7 DNI: {_fmt_metrics(total)}")
    if best:
        lines.append("\nNAJLEPSZE:")
        lines += [f"- #{p['id']} {(p['content'] or '')[:60]} | {_fmt_metrics(p['engagement_metrics'])}" for p in best]
    if worst:
        lines.append("NAJSLABSZE:")
        lines += [f"- #{p['id']} {(p['content'] or '')[:60]} | {_fmt_metrics(p['engagement_metrics'])}" for p in worst]
    lines.append(f"\nDECYZJE AUTONOMICZNE (7 dni): {len(dec)}")
    if reco:
        lines.append(f"\nREKOMENDACJE NA NASTEPNY TYDZIEN:\n{reco}")
    text = "\n".join(lines)
    db.execute(
        """INSERT INTO subagent_weekly_reports (brand_id, channel, week_start, metrics_7d, best_content, worst_content,
                                                recommendations, report_text)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (brand_id, channel, week_start) DO UPDATE SET metrics_7d=EXCLUDED.metrics_7d,
             best_content=EXCLUDED.best_content, worst_content=EXCLUDED.worst_content,
             recommendations=EXCLUDED.recommendations, report_text=EXCLUDED.report_text, created_at=NOW()""",
        (brand_id, channel, week_start, Jsonb(total),
         Jsonb([{"id": p["id"], "metrics": p["engagement_metrics"]} for p in best]),
         Jsonb([{"id": p["id"], "metrics": p["engagement_metrics"]} for p in worst]), reco, text))
    logbot.send(text)
    return text


def run_all(kind):
    """Cron entrypoint: raport dla KAZDEGO supervised celu (open/closed: nowy wiersz channels = nowy raport)."""
    chans = db.fetchall("SELECT brand_id, channel FROM channels WHERE supervised = true AND status IN ('active','draft')")
    fn = daily_report if kind == "daily" else weekly_report
    done = 0
    for c in chans:
        try:
            fn(c["brand_id"], c["channel"])
            done += 1
        except Exception:
            import traceback
            traceback.print_exc()
    return done
