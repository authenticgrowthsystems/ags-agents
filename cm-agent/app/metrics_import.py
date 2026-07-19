"""Import metryk LinkedIn z eksportu AggregateAnalytics (xlsx) - plan dnia 19/07 krok [1].

Sciezka: Tomasz wysyla xlsx jako dokument na Telegram HITL -> n8n (galaz document) -> POST
/metrics/xlsx {chat_id, file_id, file_name} -> ten modul pobiera plik (getFile), parsuje
i zapisuje: dzienne metryki do channel_metrics_daily (DDL 023), per-post wyswietlenia/reakcje
do published_posts.engagement_metrics (merge ||, source 'linkedin_xlsx'), demografie do
channel_audience_snapshots. Paragon idzie na czat.

Parsowanie POZYCYJNE po ksztalcie arkusza, nie po nazwach (naglowki zaleza od locale konta:
PL 'ODKRYWANIE/REAKCJE/OBSERWUJACY', EN 'DISCOVERY/ENGAGEMENT/FOLLOWERS'). Ksztalty
zweryfikowane na zywych plikach docs/evidence/screeny_13-19_07/AggregateAnalytics_*.xlsx:
- arkusz dzienny: wiersze [data D.M.YYYY, wyswietlenia, reakcje] (3 kolumny)
- arkusz obserwujacych: wiersz 1 = ('... na D.M.YYYY', total), potem [data, nowi] (2 kolumny)
- arkusz top publikacji: dwie polowki [url, data, reakcje] i [url, data, wyswietlenia]
- arkusz demografii: wiersze [kategoria, wartosc, 'NN%']
"""
import datetime
import io
import re

import httpx
from psycopg.types.json import Jsonb

from . import config, db

_URN_RE = re.compile(r"(?:ugcPost|share|activity)-(\d{8,})")
_DATE_RE = re.compile(r"^\s*(\d{1,2})[./](\d{1,2})[./](\d{4})\s*$")


def _tg(method, payload):
    tok = config.TELEGRAM_BOT_TOKEN
    if not tok:
        return None
    try:
        r = httpx.post(f"https://api.telegram.org/bot{tok}/{method}", json=payload, timeout=20)
        return r.json()
    except Exception:
        return None


def _reply(chat_id, text):
    if chat_id:
        _tg("sendMessage", {"chat_id": chat_id, "text": text[:4000]})


def _fetch_document(file_id):
    """getFile -> download (limit Telegrama 20MB; eksport ma ~20KB). Zwraca bytes albo None."""
    tok = config.TELEGRAM_BOT_TOKEN
    if not (tok and file_id):
        return None
    try:
        r = _tg("getFile", {"file_id": file_id})
        path = ((r or {}).get("result") or {}).get("file_path")
        if not path:
            return None
        resp = httpx.get(f"https://api.telegram.org/file/bot{tok}/{path}", timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def _date(val):
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    m = _DATE_RE.match(str(val or ""))
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime.date(y, mo, d)
    except ValueError:
        return None


def _num(val):
    if val is None:
        return None
    s = str(val).replace("\xa0", "").replace(" ", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_aggregate_xlsx(blob):
    """Klasyfikacja arkuszy po ksztalcie. Zwraca dict:
    {daily: {date: {impressions, reactions}}, followers: {date: n}, followers_total,
     posts: [{urn, url, impressions, reactions, published}], demographics: [{category, value, pct}]}"""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
    out = {"daily": {}, "followers": {}, "followers_total": None, "posts": {}, "demographics": []}
    for ws in wb.worksheets:
        rows = [[c for c in r] for r in ws.iter_rows(values_only=True)]
        if not rows:
            continue
        joined = " ".join(str(c) for r in rows[:60] for c in r if c)
        if "linkedin.com/posts" in joined or "linkedin.com/feed" in joined:
            _parse_posts_sheet(rows, out)
            continue
        # arkusz demografii: 3 kolumny, trzecia konczy sie '%'
        pct_rows = [r for r in rows if len(r) >= 3 and r[2] is not None and str(r[2]).strip().endswith("%")]
        if len(pct_rows) >= 5:
            out["demographics"] = [{"category": str(r[0] or "").strip(), "value": str(r[1] or "").strip(),
                                    "pct": str(r[2]).strip()} for r in pct_rows]
            continue
        # arkusze z wierszami datowanymi: 3 kolumny = dzienny (wysw+reakcje), 2 = obserwujacy
        dated = [(r, _date(r[0])) for r in rows if r and _date(r[0])]
        if not dated:
            continue
        three = [(d, r) for r, d in dated if len([c for c in r if c is not None]) >= 3]
        two = [(d, r) for r, d in dated if len([c for c in r if c is not None]) == 2]
        if len(three) >= len(two):
            for d, r in three:
                out["daily"][d] = {"impressions": _num(r[1]), "reactions": _num(r[2])}
        else:
            for d, r in two:
                out["followers"][d] = _num(r[1])
            # wiersz 1: ('Obserwujacy ogolem na D.M.YYYY', total)
            for r in rows[:3]:
                if r and len(r) >= 2 and _num(r[1]) is not None and _date(r[0]) is None and r[0]:
                    out["followers_total"] = _num(r[1])
                    break
    wb.close()
    out["posts"] = list(out["posts"].values())
    return out


def _parse_posts_sheet(rows, out):
    """Dwie polowki w jednym arkuszu: [url, data, reakcje] kol 0-2 i [url, data, wyswietlenia] kol 4-6.
    Naglowki PL maja 'Reakcje' po lewej i 'Wyswietlenia' po prawej - ksztalt staly w eksportach 2026."""
    posts = out["posts"]

    def _touch(url, pub, key, val):
        m = _URN_RE.search(url or "")
        if not m or val is None:
            return
        p = posts.setdefault(m.group(1), {"urn": m.group(1), "url": url, "published": pub,
                                          "impressions": None, "reactions": None})
        p[key] = val
        if pub and not p.get("published"):
            p["published"] = pub

    for r in rows:
        if not r:
            continue
        if len(r) >= 3 and r[0] and "linkedin.com" in str(r[0]):
            _touch(str(r[0]), _date(r[1]), "reactions", _num(r[2]))
        if len(r) >= 7 and r[4] and "linkedin.com" in str(r[4]):
            _touch(str(r[4]), _date(r[5]), "impressions", _num(r[6]))


def import_linkedin_xlsx(brand_id, channel, blob):
    """Zapis do DB. Zwraca podsumowanie dict (paragon buduje handle_telegram_xlsx)."""
    parsed = parse_aggregate_xlsx(blob)
    days = 0
    all_dates = sorted(set(parsed["daily"]) | set(parsed["followers"]))
    last_date = all_dates[-1] if all_dates else datetime.date.today()
    for d in all_dates:
        dm = parsed["daily"].get(d) or {}
        db.execute(
            """INSERT INTO channel_metrics_daily (brand_id, channel, metric_date, impressions, reactions,
                                                  new_followers, followers_total, source, raw)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'linkedin_xlsx',%s)
               ON CONFLICT (brand_id, channel, metric_date) DO UPDATE SET
                 impressions = COALESCE(EXCLUDED.impressions, channel_metrics_daily.impressions),
                 reactions = COALESCE(EXCLUDED.reactions, channel_metrics_daily.reactions),
                 new_followers = COALESCE(EXCLUDED.new_followers, channel_metrics_daily.new_followers),
                 followers_total = COALESCE(EXCLUDED.followers_total, channel_metrics_daily.followers_total),
                 raw = COALESCE(EXCLUDED.raw, channel_metrics_daily.raw), imported_at = NOW()""",
            (brand_id, channel, d, dm.get("impressions"), dm.get("reactions"), parsed["followers"].get(d),
             parsed["followers_total"] if d == last_date else None,
             Jsonb({"impressions": dm.get("impressions"), "reactions": dm.get("reactions"),
                    "new_followers": parsed["followers"].get(d)})))
        days += 1
    matched = unmatched = 0
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for p in parsed["posts"]:
        m = {k: p[k] for k in ("impressions", "reactions") if p.get(k) is not None}
        if not m:
            continue
        m["source"] = "linkedin_xlsx"
        m["fetched_at"] = now_iso
        row = db.fetchone(
            """UPDATE published_posts SET engagement_metrics = COALESCE(engagement_metrics,'{}'::jsonb) || %s
               WHERE brand=%s AND platform=%s AND post_id LIKE %s RETURNING id""",
            (Jsonb(m), brand_id, channel, f"%{p['urn']}%"))
        if row:
            matched += 1
        else:
            unmatched += 1
    if parsed["demographics"]:
        db.execute(
            """INSERT INTO channel_audience_snapshots (brand_id, channel, captured_date, followers_total,
                                                       demographics, source)
               VALUES (%s,%s,%s,%s,%s,'linkedin_xlsx')
               ON CONFLICT (brand_id, channel, captured_date) DO UPDATE SET
                 followers_total = COALESCE(EXCLUDED.followers_total, channel_audience_snapshots.followers_total),
                 demographics = EXCLUDED.demographics, created_at = NOW()""",
            (brand_id, channel, last_date, parsed["followers_total"], Jsonb(parsed["demographics"])))
    return {"days": days, "range": (all_dates[0].strftime("%d/%m"), last_date.strftime("%d/%m")) if all_dates else None,
            "posts_matched": matched, "posts_unmatched": unmatched,
            "followers_total": parsed["followers_total"], "demographics": bool(parsed["demographics"])}


def handle_telegram_xlsx(body):
    """Watek tla dla POST /metrics/xlsx {chat_id, file_id, file_name}. Kazda sciezka konczy sie
    wiadomoscia na czacie (REGULA PRAWDY - zero cichych porazek)."""
    chat_id = body.get("chat_id")
    file_name = str(body.get("file_name") or "")
    try:
        blob = _fetch_document(body.get("file_id"))
        if not blob:
            _reply(chat_id, "❌ Nie udalo sie pobrac pliku z Telegrama (getFile). Sprobuj wyslac ponownie.")
            return
        # eksport profilu osobistego Tomasza = cel AGS/linkedin (konto osobiste, EN); strony firmowe
        # wejda przez API po App 2 CMA - wtedy routing per nazwa pliku/konto.
        brand_id, channel = "AGS", "linkedin"
        s = import_linkedin_xlsx(brand_id, channel, blob)
        if not s["days"] and not s["posts_matched"]:
            _reply(chat_id, f"⚠️ Plik {file_name or 'xlsx'} przeczytany, ale nie rozpoznalem zadnych metryk. "
                            "To na pewno eksport AggregateAnalytics z LinkedIn?")
            return
        rng = f" ({s['range'][0]}-{s['range'][1]})" if s.get("range") else ""
        lines = [f"📊 Import metryk LinkedIn -> {brand_id}/{channel}:",
                 f"- dni metryk: {s['days']}{rng}",
                 f"- posty dopasowane: {s['posts_matched']}" + (f" (bez dopasowania: {s['posts_unmatched']})" if s["posts_unmatched"] else "")]
        if s.get("followers_total") is not None:
            lines.append(f"- obserwujacy lacznie: {s['followers_total']}")
        if s.get("demographics"):
            lines.append("- demografia: zapisana (snapshot)")
        lines.append("Raporty subagenta widza te dane od nastepnego cyklu.")
        _reply(chat_id, "\n".join(lines))
    except Exception as e:
        _reply(chat_id, f"❌ Import metryk padl: {type(e).__name__}: {str(e)[:200]}")
