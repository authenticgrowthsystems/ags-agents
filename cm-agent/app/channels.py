"""Generic channel connector: stage per-channel variants into post_queue (the outbox) and, on approval,
publish per the channel's publish_mode. New channel = a registry row + (for webhook mode) a sub-agent adapter;
the CM core does not change. Sub-agents (e.g. x-agent) receive a delegate call on the async connector contract
and publish + report back via post_queue + agent_messages."""
import httpx

from . import db, config


def active_targets(brand_id, target_channels):
    """Channels CM manages for this item: rows that are SUPERVISED (CM toggle ON) AND active/draft.
    supervised=false = the channel runs STANDALONE (its own sub-agent loop + own Telegram), so CM leaves it
    alone - the toggle that makes each sub-agent a sellable object usable with or without CM. 'ready' channels
    are scaffolded slots, skipped until activated."""
    rows = db.fetchall(
        "SELECT channel, status, adapter_path, config, supervised FROM channels WHERE brand_id=%s AND channel = ANY(%s)",
        (brand_id, list(target_channels or [])),
    )
    return [r for r in rows if r.get("supervised") and r["status"] in ("active", "draft")]


def _split_paragraphs(text, target=500):
    """Mechaniczne ciecie dlugiego wariantu X na samodzielne posty (strażnik 19/07): pakuje
    cale akapity do czesci ~target znakow (nigdy nie tnie w pol zdania/akapitu; pojedynczy
    akapit dluzszy niz target zostaje w calosci jako wlasna czesc)."""
    paras = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    parts, cur = [], ""
    for p in paras:
        if cur and len(cur) + 2 + len(p) > target:
            parts.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur:
        parts.append(cur)
    return parts or [text]


def _pub_media(media):
    """A3 (21/07, incydent grafik): do kolejki publikacji ida TYLKO prawdziwe pliki (file_id).
    'Propozycje wizualne' (kind=suggestion, opis grafiki) zostaja na materiale - to zadanie
    do karty, nie zalacznik; publisher probowal wgrywac OPIS jako obraz (INIT 400)."""
    out = []
    for m in (media or []):
        if isinstance(m, dict) and m.get("file_id"):
            out.append(m)
    return out


def stage_variant(item, channel_row, variant_text):
    """Eager staging: write the variant as a post_queue row in 'review' (shown at the HITL gate).
    Media (etap 1, 06/07): zalaczniki materialu jada do wiersza kolejki - publisher wgrywa je przy publikacji.
    #90 korekta 12/07 ('rozbic na caly dzien'): SERIA X (===POST===) = OSOBNE wiersze kolejki,
    kazdy z KOLEJNYM wolnym slotem siatki dnia - samodzielne posty, nie nitka, nie kloc."""
    import json
    from . import slots as _slots
    # STRAZNIK JEZYKA 20/07 (incydent: polskie warianty trafily do kolejki kanalow EN i wyszly
    # po polsku na LinkedIn/X). Jezyk kanalu = channels.config.language_publish; wariant w zlym
    # jezyku tlumaczymy PRZED zapisem do kolejki, zeby karta HITL pokazywala to, co wyjdzie.
    try:
        from . import compliance as _comp, generate as _gen
        if (_gen._language_publish(item["brand_id"], channel_row["channel"]) == "en"
                and _comp.looks_polish(variant_text or "")):
            variant_text = _gen.translate_text(
                variant_text, "en", content_item_id=item.get("id")) or variant_text
    except Exception:
        pass  # tlumaczenie nie moze zablokowac stagingu; PL zlapie wtedy karta HITL
    if channel_row["channel"] == "x" and ("===POST===" in (variant_text or "")
                                          or len(variant_text or "") > 600):
        # STRAZNIK 19/07 (Tomasz: 'napraw tak, zeby nie trzeba bylo wracac'): dlugi wariant X
        # bez znacznikow NIE wychodzi jako kloc - tniemy mechanicznie po akapitach na serie
        # samodzielnych postow (kanon #90; grafika TYLKO przy czesci 1 - patrz i == 0 nizej).
        if "===POST===" in (variant_text or ""):
            parts = [p.strip() for p in variant_text.split("===POST===") if p.strip()]
        else:
            parts = _split_paragraphs(variant_text)
        ids = []
        for i, part in enumerate(parts):
            # kazda czesc = KOLEJNY wolny slot (bez dziedziczenia slotu materialu - czesc 1
            # ladowala po czesciach 2-4, gdy material mial stary slot w przyszlosci)
            try:
                slot = _slots.next_slot(item["brand_id"], ["x"], prefer_today=True)
            except Exception:
                slot = None
            row = db.fetchone(
                """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
                   VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb) RETURNING id""",
                (part, item["brand_id"], "x", item.get("master_theme"), item["id"],
                 _slots.humanize_slot(slot),  # kanon 19/07: niepelne godziny +/-15 min
                 json.dumps(_pub_media(item.get("media")) if i == 0 else [])),
            )
            if row:
                ids.append(row["id"])
        return ids[0] if ids else None
    row = db.fetchone(
        """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id, scheduled_for, media)
           VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb) RETURNING id""",
        (variant_text, item["brand_id"], channel_row["channel"], item.get("master_theme"),
         item["id"], _slots.humanize_slot(item.get("scheduled_for")),  # kanon 19/07: niepelne godziny
         json.dumps(_pub_media(item.get("media")))),
    )
    return row["id"] if row else None


def _delegate(item, row):
    """Delegate publishing to a channel SUB-AGENT adapter (connector contract). The adapter publishes and
    writes back post_queue 'published' + an agent_messages RESPONSE, so CM just fires + marks 'dispatching'."""
    db.execute("UPDATE post_queue SET status='dispatching' WHERE id=%s", (row["id"],))
    try:
        httpx.post(config.N8N_BASE_URL + row["adapter_path"],
                   json={"content_item_id": str(item["id"]), "brand_id": item["brand_id"],
                         "content": row.get("content") or "", "correlation_id": str(item["id"]),
                         "media": row.get("media") or []},
                   headers={"X-Researcher-Secret": config.RESEARCHER_WEBHOOK_SECRET}, timeout=25)
    except Exception:
        pass  # sub-agent unreachable; row stays 'dispatching', retriable


def _ensure_li_graphic(item, r):
    """REGULA Tomasza 23/07 (#280 wyszedl na LinkedIn bez grafiki): post LinkedIn bez pliku
    graficznego dostaje AUTO-generowany obraz przy dispatchu, PRZED publikacja (LinkedIn =
    1 post/dzien, grafika zawsze podnosi dwell). Porazka generacji NIE blokuje publikacji -
    post idzie tekstowo, slad w logu. Obraz laduje tez na Telegramie (podglad) i materiale."""
    import json as _json
    import traceback as _tb
    media = r.get("media") or []
    if isinstance(media, str):
        try:
            media = _json.loads(media)
        except Exception:
            media = []
    if any(isinstance(m, dict) and m.get("file_id") for m in media):
        return
    try:
        from . import generate, matreview, hitl
        from .brand import load_brand
        hint = next((m.get("text") for m in (item.get("media") or [])
                     if isinstance(m, dict) and m.get("kind") == "suggestion"), "")
        brand = load_brand(item.get("brand_id") or "AGS")
        try:
            prompt = generate.generate_image_prompt(
                brand, item.get("master_theme"), r.get("content") or item.get("canonical_body"),
                hint, content_item_id=item["id"])
        except Exception:
            prompt = (f"Professional social media graphic for a LinkedIn post. Theme: "
                      f"{(item.get('master_theme') or '')[:300]}. Clean, modern tech aesthetic, "
                      f"high contrast, no watermarks, no real faces, no fake event photos.")
        png = generate.generate_image(prompt)
        chat = hitl._admin_chat_id()
        fid = matreview._tg_upload_photo(
            chat, png, f"🎨 AUTO-grafika (LinkedIn bez pliku) do #{r['id']}: "
                       f"{(item.get('master_theme') or '')[:80]}") if chat else None
        if not fid:
            return
        desc = {"source": "telegram", "file_id": fid, "kind": "photo", "generated": True,
                "auto": "li_dispatch", "image_prompt": prompt[:3000]}
        db.execute("UPDATE post_queue SET media = %s::jsonb WHERE id=%s",
                   (_json.dumps([desc]), r["id"]))
        db.execute("UPDATE content_items SET media = COALESCE(media,'[]'::jsonb) || %s::jsonb "
                   "WHERE id=%s", (_json.dumps([desc]), item["id"]))
        r["media"] = [desc]
    except Exception:
        _tb.print_exc()


def dispatch_item(item):
    """On approval: publish this item's staged 'review' rows by channel publish_mode.
    webhook mode -> DELEGATE to the channel sub-agent adapter (e.g. X); post_queue mode -> 'scheduled'
    (existing per-minute Scheduler); draft mode -> 'held' (manual, e.g. LinkedIn until its API is wired).
    NOTE (backlog b): dispatching is NOT publishing. Every mode here just HANDS OFF - the real publish
    happens later (Scheduler minute-cron / sub-agent callback / Tomasz pasting). Returns a per-channel
    handoff summary so the caller reports the truth ('wyslane/zaplanowane/czeka recznie'), not a premature
    'opublikowal'. reconcile_publications fires the real success/failure report on the callback."""
    rows = db.fetchall(
        """SELECT pq.id, pq.platform, pq.content, pq.media, c.config, c.adapter_path
           FROM post_queue pq JOIN channels c ON c.brand_id=pq.brand AND c.channel=pq.platform
           WHERE pq.content_item_id=%s AND pq.status='review'""",
        (item["id"],),
    )
    handoff = []
    for r in rows:
        mode = (r.get("config") or {}).get("publish_mode", config.PUBLISH_DRAFT)
        # Task #90 (12/07): ARTYKUL X (dluga tresc bez ===TWEET===) NIE idzie do publishera tweetow
        # (limit znakow by go rozjechal) - tryb reczny do czasu adaptera POST /2/articles/draft+publish
        # (endpointy zweryfikowane docs-first 12/07; sonda tieru przy budowie adaptera).
        content = r.get("content") or ""
        if (r["platform"] == "x" and len(content) > 600 and "===TWEET===" not in content):
            mode = config.PUBLISH_DRAFT
        if mode == config.PUBLISH_WEBHOOK and r.get("adapter_path"):
            _delegate(item, r)
        elif mode == config.PUBLISH_POST_QUEUE:
            if r["platform"] == "linkedin":
                _ensure_li_graphic(item, r)  # regula 23/07: LinkedIn bez pliku = auto-obraz
            db.execute("UPDATE post_queue SET status='scheduled', scheduled_for=COALESCE(scheduled_for, NOW()) WHERE id=%s", (r["id"],))
        else:
            db.execute("UPDATE post_queue SET status='held' WHERE id=%s", (r["id"],))
        handoff.append({"platform": r["platform"], "mode": mode, "queue_id": r["id"]})
    return handoff
