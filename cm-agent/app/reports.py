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
    if mode == "x_owned_reads":
        # Kolektor X (app/x_collector.py, DDL 025) zapisuje dzienne snapshoty raz na dobe -
        # tu TYLKO merge najnowszego snapshotu per post z DB (zero platnych odczytow w raportach).
        from . import x_collector
        return x_collector.refresh_published_metrics(brand_id, channel, days)
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
def _profile_lines(brand_id, channel, days=7):
    """Sekcja PROFIL z channel_metrics_daily (DDL 023; import xlsx / wpis reczny). Pusta lista gdy brak
    danych. Gdy ostatni wpis starszy niz 3 dni - prosba o swiezy eksport (koniec slepoty metrycznej)."""
    rows = db.fetchall(
        """SELECT metric_date, impressions, reactions, new_followers, followers_total
           FROM channel_metrics_daily WHERE brand_id=%s AND channel=%s
             AND metric_date > CURRENT_DATE - make_interval(days => %s) ORDER BY metric_date""",
        (brand_id, channel, days))
    if not rows:
        return []
    imp = sum(r["impressions"] or 0 for r in rows)
    reac = sum(r["reactions"] or 0 for r in rows)
    nf = sum(r["new_followers"] or 0 for r in rows)
    total = next((r["followers_total"] for r in reversed(rows) if r["followers_total"] is not None), None)
    last = rows[-1]["metric_date"]
    line = f"PROFIL ({days}d): wyswietlenia {imp}, reakcje {reac}, nowi obserwujacy +{nf}"
    if total is not None:
        line += f", lacznie {total}"
    out = ["", line]
    if (datetime.date.today() - last).days > 3:
        out.append(f"(ostatnie dane z {last.strftime('%d/%m')} - wyslij swiezy eksport AggregateAnalytics)")
    return out


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
        """SELECT pq.id, pq.status, pq.content, pq.scheduled_for, ci.status AS item_status
           FROM post_queue pq LEFT JOIN content_items ci ON ci.id = pq.content_item_id
           WHERE pq.brand=%s AND pq.platform=%s
             AND pq.status IN ('review','scheduled','queued','held')
           ORDER BY pq.scheduled_for NULLS LAST, pq.id LIMIT %s""",
        (brand_id, channel, limit))


def _pq_label(r):
    """Etykiety kolejki PO LUDZKU (23/07, konfuzja: '[review]' Tomasz czytal jako
    'niezatwierdzone', a to czesci JUZ ZATWIERDZONYCH serii czekajace na dispatch.
    Zatwierdzanie dzieje sie na poziomie MATERIALU - wiersz tylko czeka na swoja kolej)."""
    st, it = r.get("status"), (r.get("item_status") or "")
    if st == "review":
        return "DO ZATWIERDZENIA" if it in ("needs_approval", "proposed", "draft", "brief") \
            else "zatwierdzone, czeka na start"
    return {"scheduled": "zaplanowane", "queued": "w kolejce", "held": "gotowiec reczny",
            "dispatching": "w wysylce"}.get(st, st)


def _fmt_metrics(m):
    if not m:
        # 25/07 (zgloszenie Tomasza "x nie pobiera metryk sam"): stara etykieta mowila "wpisz
        # w rozmowie z subagentem" i czytalo sie to jako obowiazek RECZNEGO wpisu. Kolektor X
        # zbiera SAM raz na dobe (Owned Reads), wiec swiezy post po prostu czeka na najblizszy
        # cykl - to nie jest brak mechanizmu. Etykieta mowi teraz prawde o tym, co sie stanie.
        return "(metryki wejda same: X przy dobowym zbiorze kolektora, LinkedIn po App 2 CMA)"
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
    lines += _profile_lines(brand_id, channel, days=7)
    lines.append(f"\nDECYZJE AUTONOMICZNE: {len(dec)}")
    for d in dec:
        lines.append(f"- {d['rationale'][:100]}")
    lines.append(f"\nKOLEJKA (najblizsze): {len(queue)}")
    for q in queue[:5]:
        when = q["scheduled_for"].astimezone(WARSAW).strftime("%d/%m %H:%M") if q.get("scheduled_for") else "brak slotu"
        lines.append(f"- #{q['id']} [{_pq_label(q)}] {(q['content'] or '')[:50]} | {when}")
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
    lines += _profile_lines(brand_id, channel, days=7)
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


# ---------------- LACZNIK (22/07): /kontekst = pakiet kontekstu serwer -> czat, BEZ LLM ----------------
# Kontrakt 2 konceptu docs/product/LACZNIK_SYNCHRONIZACYJNY_21072026.md: zwarty stan gry do
# skopiowania w czat na abonamencie. Czysty odczyt z bazy, format staly. To jest FALLBACK -
# preferowana droga to strona Notion "Stan gry AGS" (sync/stan_gry.py, ta sama tresc).

_KONTEKST_SCOPES = ("x", "linkedin", "sprzedaz", "all")


def _kontekst_channels(scope):
    if scope in ("x", "linkedin"):
        return [scope]
    if scope == "sprzedaz":
        return []
    rows = db.fetchall(
        """SELECT channel FROM channels WHERE brand_id='AGS' AND supervised=true
           AND status IN ('active','draft') AND COALESCE(config->>'agent_kind','') <> 'sales'
           ORDER BY channel""")
    return [r["channel"] for r in rows]


def _kontekst_contacts(limit=20, platform=None):
    """Kontakty w grze. KANON WHO-IS-WHO (Tomasz 22/07): kontakt = JEDNA osoba,
    handles = mapa tozsamosci per kanal ({"x": ..., "linkedin": ..., przyszle "instagram",
    "youtube"} - nowy kanal to nowy klucz, zero DDL). platform filtruje po kluczu mapy
    i pokazuje handle WLASCIWY dla platformy (fix 22/07: scope linkedin nie pokazywal
    sekcji wcale, a scope all mieszal X-handle z kontaktami LinkedIn)."""
    cond = "COALESCE(relationship_stage,'cold') NOT IN ('cold')"
    params = []
    if platform == "x":
        cond += " AND (x_handle IS NOT NULL OR handles ? 'x')"
    elif platform:
        cond += " AND handles ? %s"
        params.append(platform)
    rows = db.fetchall(
        f"""SELECT name, x_handle, handles, icp_tier, relationship_stage, last_interaction_date
            FROM contacts WHERE {cond}
            ORDER BY last_interaction_date DESC NULLS LAST, updated_at DESC LIMIT %s""",
        (*params, limit))
    out = []
    for r in rows:
        hs = r.get("handles") or {}
        if platform:
            h = (hs.get(platform) if isinstance(hs, dict) else None) \
                or (r.get("x_handle") if platform == "x" else None)
            htxt = f" (@{h})" if h else ""
        else:
            # scope all: pokaz WSZYSTKIE tozsamosci per kanal (WHO IS WHO)
            pairs = []
            if isinstance(hs, dict):
                pairs = [f"{k}:@{v}" for k, v in sorted(hs.items()) if v]
            if not pairs and r.get("x_handle"):
                pairs = [f"x:@{r['x_handle']}"]
            htxt = f" ({', '.join(pairs)})" if pairs else ""
        bits = [r.get("relationship_stage") or "?"]
        if r.get("icp_tier"):
            bits.append(r["icp_tier"])
        if r.get("last_interaction_date"):
            bits.append(f"ostatnio {r['last_interaction_date'].strftime('%d/%m')}")
        out.append(f"- {r.get('name') or '(bez nazwy)'}{htxt} [{', '.join(bits)}]")
    return out


def _kontekst_kpi(channel, limit=3):
    """Ostatnie wpisy metryk KANALU z channel_kpi_snapshots (paczka #1 pkt 1, DDL 030).
    Domyka petle Lacznika: czat przepisuje liczby z panelu, nastepna sesja je widzi
    i nie musi pytac Tomasza o to samo. Brak tabeli (przed DDL) = cisza, nie awaria."""
    try:
        rows = db.fetchall(
            """SELECT metric_date, period, impressions, reactions, new_followers,
                      followers_total, profile_views
               FROM channel_kpi_snapshots WHERE brand_id='AGS' AND channel=%s
               ORDER BY metric_date DESC, updated_at DESC LIMIT %s""", (channel, limit))
    except Exception:
        return []
    out = []
    for r in rows:
        bits = [f"{k}: {r[c]}" for c, k in (("impressions", "wyswietlenia"), ("reactions", "reakcje"),
                                            ("new_followers", "nowi obserwujacy"),
                                            ("followers_total", "obserwujacy"),
                                            ("profile_views", "odslony profilu"))
                if r.get(c) is not None]
        if not bits:
            continue
        okres = "" if (r.get("period") or "dzien") == "dzien" else f" [{r['period']}]"
        out.append(f"- {r['metric_date'].strftime('%d/%m')}{okres} " + ", ".join(bits))
    return out


def _kontekst_radar(limit=10):
    rows = db.fetchall(
        """SELECT content, source, created_at FROM inspirations
           WHERE status='new' AND created_at > NOW() - interval '14 days'
           ORDER BY created_at DESC LIMIT %s""", (limit,))
    return [f"- {r['created_at'].strftime('%d/%m')} [{r.get('source') or '?'}] "
            + " ".join((r['content'] or '').split())[:160] for r in rows]


def kontekst_text(scope="all"):
    """Stan gry jako jeden tekst markdown. Sekcje wg konceptu: plan tygodnia (sloty+statusy),
    ostatnie publikacje z metrykami, kontakty w grze, otwarte decyzje, lejek, radar."""
    scope = scope if scope in _KONTEKST_SCOPES else "all"

    def _flat(text, n):
        # wycinek jednoliniowy: lamania linii w tresci rozjezdzaly bullety (tap-test b)
        return " ".join((text or "").split())[:n]

    now = datetime.datetime.now(WARSAW)
    lines = [f"# STAN GRY AGS ({scope}) - {now.strftime('%d/%m/%Y %H:%M')} Europe/Warsaw", ""]
    chans = _kontekst_channels(scope)
    if chans:
        try:
            from . import planner
            pt = planner.plan_text("AGS")
            if pt != "(brak propozycji planu)":
                lines += ["## PLAN TYGODNIA (propozycja do zatwierdzenia)", pt, ""]
        except Exception:
            lines += ["## PLAN TYGODNIA", "(nie moge odczytac planu - blad w logu)", ""]
        for ch in chans:
            q = _queue_upcoming("AGS", ch)
            lines.append(f"## KOLEJKA {ch.upper()} ({len(q)}):")
            for r in q:
                when = (r["scheduled_for"].astimezone(WARSAW).strftime("%d/%m %H:%M")
                        if r.get("scheduled_for") else "bez slotu")
                lines.append(f"- #{r['id']} [{_pq_label(r)}] {when} | {_flat(r['content'], 70)}")
            if not q:
                lines.append("- (pusto)")
            pub = db.fetchall(
                """SELECT id, content, post_url, engagement_metrics, published_at FROM published_posts
                   WHERE brand='AGS' AND platform=%s AND published_at > NOW() - interval '7 days'
                   ORDER BY published_at DESC LIMIT 10""", (ch,))
            lines.append(f"## OSTATNIE PUBLIKACJE {ch.upper()} (7 dni, {len(pub)}):")
            for p in pub:
                lines.append(f"- {p['published_at'].astimezone(WARSAW).strftime('%d/%m %H:%M')} "
                             f"{_flat(p['content'], 70)} | {_fmt_metrics(p.get('engagement_metrics') or {})}"
                             + (f" | {p['post_url']}" if p.get("post_url") else ""))
            if not pub:
                lines.append("- (brak publikacji w 7 dni)")
            kpi = _kontekst_kpi(ch)
            if kpi:
                lines.append(f"## METRYKI KANALU {ch.upper()} (ostatnie wpisy z panelu):")
                lines += kpi
            lines.append("")
    contacts = _kontekst_contacts(platform=(scope if scope in ("x", "linkedin") else None))
    _lab = f" {scope.upper()}" if scope in ("x", "linkedin") else ""
    lines.append(f"## KONTAKTY W GRZE{_lab} (stadium != cold, {len(contacts)}):")
    lines += contacts or ["- (zero kontaktow w grze na tej platformie)"]
    lines.append("")
    try:
        from . import decisions
        pend = decisions.pending_text()
    except Exception:
        pend = "(nie moge odczytac decyzji - blad w logu)"
    lines += ["## OTWARTE DECYZJE (czekaja na guzik):", pend, ""]
    if scope in ("sprzedaz", "all"):
        try:
            from . import sales
            lines += ["## LEJEK SPRZEDAZY", sales.pipeline_text(), ""]
        except Exception:
            lines += ["## LEJEK SPRZEDAZY", "(nie moge odczytac lejka - blad w logu)", ""]
    radar = _kontekst_radar()
    lines.append(f"## RADAR / OBSERWACJE (14 dni, {len(radar)}):")
    lines += radar or ["- (pusto)"]
    lines += ["", "---",
              "Na koniec sesji czatowej wygeneruj blok [RAPORT PRACY v1] i wklej go do Telegrama "
              "(bot AGS) - serwer zapisze prace do bazy."]
    return "\n".join(lines)


def send_kontekst(chat_id, scope="all"):
    """Wysylka pakietu: tekst gdy miesci sie w 4096, inaczej plik .md (wzorzec _tg_send_document).
    Kazda sciezka konczy sie wiadomoscia (REGULA PRAWDY)."""
    from . import conversation, matreview
    try:
        text = kontekst_text(scope)
    except Exception as e:
        import traceback
        traceback.print_exc()
        conversation._reply(chat_id, f"❌ Nie zlozylem pakietu kontekstu: {type(e).__name__}: {str(e)[:150]}")
        return
    if len(text) <= 4000:
        conversation._tg("sendMessage", {"chat_id": chat_id, "text": text,
                                         "disable_web_page_preview": True})
        return
    fname = f"kontekst_{scope}_{datetime.datetime.now(WARSAW).strftime('%d%m_%H%M')}.md"
    if matreview._tg_send_document(chat_id, fname, text,
                                   caption=f"📦 Pakiet kontekstu ({scope}) - skopiuj do czatu"):
        return
    for part in conversation._split(text):
        conversation._tg("sendMessage", {"chat_id": chat_id, "text": part,
                                         "disable_web_page_preview": True})


def run_all(kind):
    """Cron entrypoint: raport dla KAZDEGO supervised celu (open/closed: nowy wiersz channels = nowy raport)."""
    chans = db.fetchall(
        """SELECT brand_id, channel FROM channels WHERE supervised = true AND status IN ('active','draft')
           AND COALESCE(config->>'agent_kind','') <> 'sales'""")  # Agent Sprzedazy nie publikuje - bez raportu kanalu
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
