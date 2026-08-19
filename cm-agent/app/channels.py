"""Generic channel connector: stage per-channel variants into post_queue (the outbox) and, on approval,
publish per the channel's publish_mode. New channel = a registry row + (for webhook mode) a sub-agent adapter;
the CM core does not change. Sub-agents (e.g. x-agent) receive a delegate call on the async connector contract
and publish + report back via post_queue + agent_messages."""
import json
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


# LIMITY DLUGOSCI (02/08/2026, polecenie Managera). Zrodlem prawdy jest `channels.config.max_len`,
# zeby dalo sie je zmienic bez rebuildu; ponizsze to bezpieczne wartosci domyslne.
# x=25000 (konto Premium - system publikowal juz 556 znakow, wiec 280 nie obowiazuje),
# linkedin=3000 (limit platformy dla zwyklego posta), article=110000 (LinkedIn Article).
_LIMITY = {"x": 25000, "linkedin": 3000}
_LIMIT_ARTYKULU = 110000


def limit_znakow(channel_row, format_="post"):
    """Ile znakow wolno na tym kanale. JEDNO zrodlo prawdy dla walidacji i dla komunikatu."""
    if format_ == "article":
        return _LIMIT_ARTYKULU
    cfg = channel_row.get("config") or {}
    try:
        z_cfg = int(str((cfg or {}).get("max_len") or "").strip() or 0)
    except (TypeError, ValueError):
        z_cfg = 0
    return z_cfg or _LIMITY.get(channel_row.get("channel"), 3000)


def _odrzuc_za_dlugi(item, channel_row, tekst, limit, format_):
    """Odrzucenie JAWNE: material NIE trafia do kolejki, a czlowiek dowiaduje sie DLACZEGO.

    Polecenie Managera 02/08: "odrzucenie materialu przekraczajacego limit kanalu z jawnym
    komunikatem, NIGDY z cichym obcieciem". Ciche obciecie jest gorsze niz odrzucenie, bo
    tekst wychodzi do klienta urwany w polowie zdania i nikt sie o tym nie dowiaduje."""
    ile = len(tekst or "")
    powod = (f"❌ WARIANT ZA DLUGI - nie wstawiam do kolejki.\n"
             f"Kanal: {channel_row.get('channel')} ({format_}), limit {limit} znakow, "
             f"wariant ma {ile} - o {ile - limit} za duzo.\n"
             f"Material: {str(item.get('master_theme') or '')[:120]}\n"
             f"Skroc tekst i wygeneruj ponownie. NIE obcinam automatycznie - urwany w polowie "
             f"zdania post jest gorszy niz brak posta.")
    # Log ma byc czysto ASCII: konsola bywa cp1250 (Windows) i emoji wysadza `print`,
    # czyli straznik dlugosci zabijalby proces zamiast go chronic. Emoji zostaje
    # WYLACZNIE w wiadomosci do czlowieka, gdzie faktycznie cos wnosi.
    print(f"[channels] WARIANT ZA DLUGI: {channel_row.get('channel')} {format_} "
          f"{ile}/{limit} znakow, material {str(item.get('id'))}", flush=True)
    try:
        db.execute(
            """INSERT INTO agent_logs (agent, level, message, context)
               VALUES ('CM','warn',%s,%s::jsonb)""",
            (f"wariant za dlugi: {channel_row.get('channel')} {ile}/{limit}",
             json.dumps({"content_item_id": str(item.get("id")), "znakow": ile,
                         "limit": limit, "format": format_})))
    except Exception:
        traceback.print_exc()
    try:
        from . import logbot as _logbot
        _logbot.send(powod, silent=False)   # nie silent: to jest rzecz, ktora ma obudzic
    except Exception:
        traceback.print_exc()   # AP-306: powiadomienie moze pasc, ale NIE cicho
    return None


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
            # do_publikacji=True (11/08): ten przeklad IDZIE DO KOLEJKI i wychodzi w tej postaci.
            # Wczesniej prompt mowil modelowi, ze to kopia do przegladu - nieprawda i licencja
            # na luz w miejscu, w ktorym luzu byc nie moze.
            zrodlo = variant_text
            variant_text = _gen.translate_text(
                variant_text, "en", content_item_id=item.get("id"), do_publikacji=True) or variant_text
            # Zastrzezenia NIE blokuja stagingu (tekst i tak jest lepszy niz polski na kanale EN,
            # incydent 20/07), ale nie moga zniknac po cichu - inaczej rozjazd przekladu jest
            # nieodroznialny od poprawnego tlumaczenia. To ta sama zasada co przy AP-306.
            for uwaga in _gen.sprawdz_przeklad(zrodlo, variant_text):
                print(f"[channels] PRZEKLAD ROZJECHANY {item.get('id')}: {uwaga}", flush=True)
                try:
                    db.execute(
                        """INSERT INTO agent_logs (agent, level, message, context)
                           VALUES ('CM','warn',%s,%s::jsonb)""",
                        (f"przeklad do publikacji rozjechany: {uwaga}",
                         json.dumps({"content_item_id": str(item.get("id")),
                                     "kanal": channel_row.get("channel"), "uwaga": uwaga})))
                except Exception:
                    traceback.print_exc()
    except Exception:
        # AP-306: tlumaczenie nie blokuje stagingu, ale cicha awaria = polski tekst
        # w kanale angielskim (incydent 20/07). Karta HITL to zlapie, log mowi DLACZEGO.
        traceback.print_exc()
    # FORMAT (DDL 041): 'article' bierze sie z materialu, reszta to zwykly post.
    format_ = "article" if str(item.get("format") or "post") == "article" else "post"
    limit = limit_znakow(channel_row, format_)
    if len(variant_text or "") > limit:
        return _odrzuc_za_dlugi(item, channel_row, variant_text, limit, format_)

    # ROZBIJANIE SERII ZNIESIONE 02/08/2026. Manager zdecydowal 29/07: "X dostaje JEDEN wpis
    # na material, koniec serii" - dane wyczyszczono tego samego dnia (21 materialow wycofanych),
    # ale TEN KOD ZOSTAL i nadal dzielil wariant X dluzszy niz 600 znakow. Kolejka byla pusta,
    # wiec nikt tego nie zauwazyl przez cztery dni. Od teraz za dlugi wariant jest ODRZUCANY
    # jawnie (wyzej), a nie ciety na kawalki.
    if False:
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
                                           scheduled_for, media, slot_source, format)
                   VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb,'staging',%s) RETURNING id""",
                (part, item["brand_id"], "x", item.get("master_theme"), item["id"],
                 _slots.humanize_slot(slot),  # kanon 19/07: niepelne godziny +/-15 min
                 json.dumps(_pub_media(item.get("media")) if i == 0 else []), format_),
            )
            if row:
                ids.append(row["id"])
        return ids[0] if ids else None
    row = db.fetchone(
        """INSERT INTO post_queue (content, brand, platform, topic, status, content_item_id,
                                   scheduled_for, media, slot_source, format)
           VALUES (%s,%s,%s,%s,'review',%s,%s,%s::jsonb,'staging',%s) RETURNING id""",
        (variant_text, item["brand_id"], channel_row["channel"], item.get("master_theme"),
         item["id"], _slots.humanize_slot(item.get("scheduled_for")),  # kanon 19/07: niepelne godziny
         json.dumps(_pub_media(item.get("media"))), format_),
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


def sprawdz_gatunek(item):
    """AP-315 (10/08): przepusc przez bezpiecznik gatunku DOKLADNIE te teksty, ktore wyjda
    publicznie - czyli tresc WIERSZY KOLEJKI, nie canonical_body. Wariant bywa inny niz
    canonical (stage_variant przepisuje go per kanal), a publikuje sie wariant.

    Zwraca liste slownikow {qid, platform, twarde, miekkie, odcisk}; pusta = droga wolna.
    `odcisk` jest liczony z TRESCI, nie z trafien: furtka "drugie zatwierdzenie" ma puszczac
    TEN SAM tekst, ktory czlowiek widzial w meldunku. Tekst przepisany, ktory trafia w te sama
    fraze, jest NOWYM tekstem i ma zostac zatrzymany po raz pierwszy."""
    from . import compliance as _c   # jak w stage_variant: import lokalny, nie modulowy
    import hashlib
    rows = db.fetchall(
        "SELECT id, platform, content FROM post_queue WHERE content_item_id=%s AND status='review'",
        (item["id"],))
    zle = []
    for r in rows:
        tresc = r.get("content") or ""
        twarde, miekkie = _c.bezpiecznik_gatunku(tresc)
        if twarde or miekkie:
            zle.append({"qid": r["id"], "platform": r["platform"],
                        "twarde": twarde, "miekkie": miekkie,
                        "odcisk": hashlib.sha1(tresc.encode("utf-8")).hexdigest()[:16]})
    return zle


def _slad_w_dzienniku(poziom, wiadomosc, kontekst):
    """Wpis do `agent_logs` - ten sam sposob zostawiania sladu, ktorego uzywa `_odrzuc_za_dlugi`.
    Dziennik jest tu po to, zeby dalo sie PO FAKCIE odpowiedziec na pytanie "czemu ten material
    nie wyszedl", gdy wiadomosc na Telegramie dawno zniknela z ekranu."""
    try:
        db.execute(
            """INSERT INTO agent_logs (agent, level, message, context)
               VALUES ('CM',%s,%s,%s::jsonb)""",
            (poziom, wiadomosc[:400], json.dumps(kontekst, ensure_ascii=False)))
    except Exception:
        traceback.print_exc()


def _melduj(tekst):
    """Paragon na kanal logowy. Import lokalny jak w `_odrzuc_za_dlugi` (logbot ciagnie config)."""
    try:
        from . import logbot as _logbot
        _logbot.send(tekst, silent=False)
    except Exception:
        traceback.print_exc()   # AP-306: powiadomienie moze pasc, ale NIE cicho


def _pomin_kanal_wylaczony(item, r):
    """D-022 (19/08/2026): kanal z `publish_mode='none'` jest CELOWO wylaczony z publikacji.

    CO BYLO DO 19/08 - i to jest sprostowanie do opisu dlugu. Wartosc `none` NIE przechodzila
    przez dispatch bez sladu. Wpadala do galezi zbiorczej `else`, ktora nie jest galezia trybu
    'draft', tylko lapaczem wszystkiego - i wiersz konczyl na 'held'. Skutek byl gorszy niz cisza:
    `worker._send_manual_paste_kits` przysylal Tomaszowi PELNA TRESC z poleceniem "wklej recznie
    i odpisz `wklejone <id>`" dla kanalu, ktory ma byc wylaczony. Ustawienie mowilo "nie publikuj",
    a system prosil czlowieka o reczna publikacje. To AP-312 co do znaku.

    CO ROBIMY TERAZ. Wiersz dostaje stan terminalny 'rejected' - wartosc, ktora juz istnieje
    w slowniku kolejki i ktora system pisze przy odrzuceniu karty, wiec zadnej migracji ani nowej
    wartosci tu nie ma. 'rejected' znaczy dokladnie tyle: ten wiersz nie pojdzie. Dzieki temu
    nie ma gotowca do wklejania i nie ma alarmu o zwisie, bo stan jest terminalny.

    Paragon idzie na kanal logowy, a powod do dziennika - dokladnie tak, jak przy odrzuceniu
    wariantu za dlugiego. Kanal wylaczony ma MOWIC, ze jest wylaczony."""
    db.execute("UPDATE post_queue SET status='rejected' WHERE id=%s", (r["id"],))
    print(f"[channels] KANAL WYLACZONY (publish_mode=none): {r['platform']} "
          f"material {str(item.get('id'))} wiersz {r['id']}", flush=True)
    _slad_w_dzienniku("warn", f"kanal wylaczony (publish_mode=none): {r['platform']}",
                      {"content_item_id": str(item.get("id")), "queue_id": r["id"],
                       "platform": r["platform"], "dlug": "D-022"})
    _melduj(f"🚫 KANAL WYLACZONY - nie publikuje tam nic.\n"
            f"Kanal: {r['platform']} (ustawienie publish_mode='none').\n"
            f"Material: {str(item.get('master_theme') or '')[:120]}\n"
            f"Wpis w kolejce zamkniety bez publikacji. To NIE jest awaria - tak jest ustawione.\n"
            f"Jesli ten kanal ma znowu publikowac, zmien mu tryb na 'post_queue' (Scheduler) "
            f"albo 'draft' (gotowiec do recznej wklejki).")


def _tryb_publikacji_nieznany(item, r, tryb):
    """D-022 (19/08/2026): tryb publikacji, ktorego kod NIE ZNA. To co innego niz wylaczenie.

    DLACZEGO OSOBNY PRZYPADEK. Do 19/08 kazda nieznana wartosc - literowka, tryb z przyszlosci,
    napis wklepany recznie do `channels.config` - zachowywala sie jak 'draft'. Blad konfiguracji
    byl wiec nieodroznialny od swiadomego ustawienia, a system sam wybieral za czlowieka, co ta
    wartosc "pewnie znaczy". Domysl podstawiony za decyzje to AP-317 w warstwie konfiguracji.

    CO ROBIMY. Wiersz zostaje NIETKNIETY w stanie 'review'. To jest wybor, nie zaniechanie:
      * nie publikujemy, bo nie wiemy czym - bramka pada ZAMKNIETA (AP-314);
      * nie zamieniamy trybu po cichu na zaden inny, bo cicha korekta wyglada jak sukces (AP-306);
      * nie kasujemy wiersza, bo po poprawieniu ustawienia material ma pojsc bez regeneracji;
      * stan nieterminalny sprawia, ze `worker._dispatch_timeout_alert` odezwie sie ponownie,
        jesli nikt nie zareaguje na pierwszy meldunek. Alarm, ktory sam sie powtarza, jest
        tanszy niz material, ktory po cichu nie wyszedl."""
    print(f"[channels] NIEZNANY TRYB PUBLIKACJI: {r['platform']} tryb={str(tryb)[:40]!r} "
          f"material {str(item.get('id'))} wiersz {r['id']}", flush=True)
    _slad_w_dzienniku("error", f"nieznany publish_mode: {r['platform']}={str(tryb)[:60]}",
                      {"content_item_id": str(item.get("id")), "queue_id": r["id"],
                       "platform": r["platform"], "publish_mode": str(tryb)[:60], "dlug": "D-022"})
    _melduj(f"⚠️ NIE WIEM, JAK OPUBLIKOWAC - wstrzymalem ten wpis.\n"
            f"Kanal: {r['platform']}, ustawienie publish_mode: '{str(tryb)[:60]}'.\n"
            f"Material: {str(item.get('master_theme') or '')[:120]}\n"
            f"Tej wartosci nie zna zaden konsument, wiec nie zgaduje, o co chodzilo. Wpis czeka "
            f"w kolejce nietkniety i pojdzie sam, gdy ustawienie bedzie poprawne.\n"
            f"Dozwolone tryby: 'post_queue' (publikuje Scheduler), 'draft' (gotowiec do recznej "
            f"wklejki), 'none' (kanal wylaczony).")


def dispatch_item(item):
    """On approval: publish this item's staged 'review' rows by channel publish_mode.
    webhook mode -> DELEGATE to the channel sub-agent adapter (e.g. X); post_queue mode -> 'scheduled'
    (existing per-minute Scheduler); draft mode -> 'held' (manual, e.g. LinkedIn until its API is wired).
    NOTE (backlog b): dispatch is NOT publishing. Every mode here just HANDS OFF - the real publish
    happens later (Scheduler minute-cron / sub-agent callback / Tomasz pasting). Returns a per-channel
    handoff summary so the caller reports the truth ('wyslane/zaplanowane/czeka recznie'), not a premature
    'opublikowal'. reconcile_publications fires the real success/failure report on the callback.

    D-022 (19/08/2026): tryb 'none' (kanal WYLACZONY) i tryb NIEZNANY maja wlasne, jawne galezie
    NA POCZATKU rozgalezienia. Wczesniej obie wartosci wpadaly do zbiorczego 'else' - a to nie
    jest galaz trybu 'draft', tylko lapacz wszystkiego - i po cichu stawaly sie trybem recznym."""
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
        if mode == config.PUBLISH_NONE:
            # D-022: kanal WYLACZONY. Jawna galaz zamiast wpadania do zbiorczego 'else'.
            _pomin_kanal_wylaczony(item, r)
        elif not config.tryb_publikacji_znany(mode):
            # D-022: tryb NIEZNANY. Wiersz zostaje w 'review' - nietkniety i naprawialny -
            # a czlowiek dowiaduje sie od razu. Cicha zamiana na tryb reczny byla dotad
            # domyslem zapisanym jak decyzja (AP-306, AP-312).
            _tryb_publikacji_nieznany(item, r, mode)
        elif mode == config.PUBLISH_WEBHOOK and r.get("adapter_path"):
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
