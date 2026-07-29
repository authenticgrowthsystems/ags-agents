"""Generic channel connector: stage per-channel variants into post_queue (the outbox) and, on approval,
publish per the channel's publish_mode. New channel = a registry row + (for webhook mode) a sub-agent adapter;
the CM core does not change. Sub-agents (e.g. x-agent) receive a delegate call on the async connector contract
and publish + report back via post_queue + agent_messages."""
import traceback

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
    # STRAZNIK META-NAGLOWKA 24/07 (zgloszenie Tomasza ze zrzutu z X: post wyszedl z linia
    # "# X Adaptation" - wiersz kolejki #195). Model opisuje CO robi, a opis szedl do kolejki
    # doslownie; ani X, ani LinkedIn nie renderuja markdown, wiec to nie formatowanie, tylko
    # smiec widoczny dla klienta. To JEDYNE miejsce zapisu do post_queue, wiec straznik stoi
    # tutaj - kazda przyszla sciezka dostanie go za darmo (lekcja AP-307).
    from . import compliance as _c
    try:
        variant_text = _c.strip_meta_header(variant_text)
    except Exception:
        traceback.print_exc()  # higiena tekstu nie blokuje stagingu, ale NIE milczy (AP-306)
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
        # AP-306: tlumaczenie nie blokuje stagingu, ale cicha awaria = polski tekst
        # w kanale angielskim (incydent 20/07). Karta HITL to zlapie, log mowi DLACZEGO.
        traceback.print_exc()
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
            part = _c.strip_meta_header(part)  # kazda czesc serii bywa wlasnym "# Post 2"
            # kazda czesc = KOLEJNY wolny slot (bez dziedziczenia slotu materialu - czesc 1
            # ladowala po czesciach 2-4, gdy material mial stary slot w przyszlosci)
            try:
                slot = _slots.next_slot(item["brand_id"], ["x"], prefer_today=True)
            except Exception:
                slot = None
            row = db.fetchone(
                """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id,
                                           scheduled_for, media, slot_source)
                   VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb,'staging') RETURNING id""",
                (part, item["brand_id"], "x", item.get("master_theme"), item["id"],
                 _slots.humanize_slot(slot),  # kanon 19/07: niepelne godziny +/-15 min
                 json.dumps(_pub_media(item.get("media")) if i == 0 else [])),
            )
            if row:
                ids.append(row["id"])
        return ids[0] if ids else None
    row = db.fetchone(
        """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id,
                                   scheduled_for, media, slot_source)
           VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb,'staging') RETURNING id""",
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
        # AP-306: wiersz zostaje 'dispatching' i jest ponawialny, ale powod ma byc w logu
        traceback.print_exc()


def _auto_obraz_wlaczony(brand_id, platform):
    """Czy ten kanal sam dorabia grafike przy dispatchu (channels.config.auto_image).

    24/07 (parytet subagentow, zgloszenie Tomasza po poscie X bez grafiki): mechanizm byl wpiety
    NA SZTYWNO tylko dla LinkedIna. Teraz jest wspolny i sterowany flaga, wiec wlaczenie X to
    `/set` zamiast rebuildu. Domyslnie: linkedin TAK (regula 23/07, 1 post dziennie), pozostale
    NIE - X publikuje ~31 postow tygodniowo i kazdy obraz to koszt, wiec to ma byc swiadoma
    decyzja, nie efekt uboczny."""
    try:
        r = db.fetchone("SELECT config->>'auto_image' AS flaga FROM channels "
                        "WHERE brand_id=%s AND channel=%s LIMIT 1", (brand_id or "AGS", platform))
        flaga = ((r or {}).get("flaga") or "").strip().lower()
        if flaga in ("true", "1", "tak", "on"):
            return True
        if flaga in ("false", "0", "nie", "off"):
            return False
    except Exception:
        traceback.print_exc()  # AP-306: brak flagi to decyzja, blad odczytu to awaria - musi byc w logu
    return platform == "linkedin"


def _ensure_li_graphic(item, r):
    """KANON 25/07 (feedback Tomasza POWTORZONY - [[feedback_grafiki_tylko_prompty]]): przy
    dispatchu NIE generujemy juz obrazu automatycznie. Auto-grafika gpt-image wychodzila slabo,
    a slaba grafika szkodzi marce bardziej niz jej brak. Post bez dolaczonego pliku idzie
    TEKSTOWO (Tomasz woli tekst niz amatorski auto-obraz); szczegolowy prompt do recznego
    wygenerowania jest na KARCIE zatwierdzenia (kind='visual_prompt'), wiec grafike dodaje sam
    PRZED zatwierdzeniem, gdy chce. Funkcja zostaje jako no-op pod flaga auto_image na wypadek,
    gdyby ktos ja wlaczyl - ale domyslnie flaga jest OFF (patrz DDL / SQL 25/07)."""
    return  # celowy no-op: zero auto-generowania obrazu (kanon 25/07)


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
            # 24/07 parytet: nie "if linkedin", tylko flaga auto_image per kanal (domyslnie
            # linkedin=tak, reszta=nie). Wlaczenie X nie wymaga zmiany kodu.
            if _auto_obraz_wlaczony(item.get("brand_id"), r["platform"]):
                _ensure_li_graphic(item, r)
            # slot_source tylko wtedy, gdy TU nadajemy slot (pusty przed COALESCE) - inaczej
            # nadpisalibysmy etykiete prawdziwego autora slotu wlasnym 'dispatch' (DDL 035).
            db.execute("""UPDATE post_queue
                             SET status='scheduled',
                                 slot_source = CASE WHEN scheduled_for IS NULL THEN 'dispatch'
                                                    ELSE slot_source END,
                                 scheduled_for = COALESCE(scheduled_for, NOW())
                           WHERE id=%s""", (r["id"],))
        else:
            db.execute("UPDATE post_queue SET status='held' WHERE id=%s", (r["id"],))
        handoff.append({"platform": r["platform"], "mode": mode, "queue_id": r["id"]})
    return handoff
