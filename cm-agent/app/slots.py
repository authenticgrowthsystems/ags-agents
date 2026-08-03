# -*- coding: utf-8 -*-
"""Okna publikacji + przydzial slotow (decyzja Tomasza 06/07: TOMASZ zatwierdza TRESC,
CM proponuje KIEDY). Zrodlo okien: channels.config.publish_windows ("HH:MM-HH:MM", zmienialne
z czatu przez target_update); kadencja: kanon 11d (X posts_per_day w oknie; LinkedIn pon-pt 1 post
~10:00, sob nic, nd artykul ~11:00). Material 'approved' bez slotu albo ze slotem MINIONYM nie
publikuje sie juz natychmiast - dostaje najblizszy wolny slot i Tomasz jest informowany (bot #2)."""
import datetime
import random
from zoneinfo import ZoneInfo

from . import db, config

WARSAW = ZoneInfo("Europe/Warsaw")

def _teraz():
    """Jedno miejsce, w ktorym modul pyta o czas (D-002, naprawione 02/08/2026).

    Produkcja nie zmienia zachowania - to nadal `datetime.now(WARSAW)`. Istnieje po to,
    zeby TEST mogl podstawic staly moment. Dwa testy (`test_kadencja_sufit`, `test_reslot`)
    padaly zaleznie od PORY DNIA, bo liczyly sloty z okna 13:00-22:00 wzgledem zegara
    systemowego. Czerwony test, ktory zawsze bywa czerwony, uczy ignorowania czerwonych."""
    return datetime.datetime.now(WARSAW)

DEFAULT_WINDOWS = {"x": "09:00-21:00", "linkedin": "08:00-18:00"}
# Stany MATERIALU trzymajace slot (content_items). D-008: nazwa z jednego zrodla.
BUSY_STATUSES = ("planned", "drafting", "needs_approval", "approved", config.STATUS_HANDED_OFF)
GRANULARITY_MIN = 30
LOOKAHEAD_DAYS = 14


def _parse_window(spec, channel):
    spec = (spec or DEFAULT_WINDOWS.get(channel.split("_")[0], "09:00-19:00")).strip()
    try:
        a, b = spec.split("-")
        h1, m1 = (int(x) for x in a.split(":"))
        h2, m2 = (int(x) for x in b.split(":"))
        return datetime.time(h1, m1), datetime.time(h2, m2)
    except (ValueError, AttributeError):
        return datetime.time(9, 0), datetime.time(19, 0)


def _parse_grid(cfg):
    """SIATKA SLOTOW (propozycja subagenta x, zatwierdzana przez CM): config.slot_grid =
    ["14:00","16:00","18:00","20:00"] - przydzielacz celuje w te godziny zamiast skanu co 30 min."""
    g = cfg.get("slot_grid")
    if not g:
        return None
    items = g if isinstance(g, list) else str(g).split(",")
    out = []
    for s in items:
        try:
            h, m = str(s).strip().split(":")
            out.append(datetime.time(int(h), int(m)))
        except (ValueError, AttributeError):
            continue
    return sorted(set(out)) or None


def channel_rules(brand_id, channels_list):
    """[(channel, window_start, window_end, min_gap_min, grid)] z channels.config."""
    rows = db.fetchall(
        "SELECT channel, config FROM channels WHERE brand_id=%s AND channel = ANY(%s)",
        (brand_id, list(channels_list)))
    out = []
    for r in rows:
        cfg = r.get("config") or {}
        ws, we = _parse_window(cfg.get("publish_windows"), r["channel"])
        if r["channel"] == "x":
            per_day = int(str(cfg.get("posts_per_day", "4")).split("-")[0] or 4)
            window_min = (we.hour * 60 + we.minute) - (ws.hour * 60 + ws.minute)
            gap = max(60, window_min // max(per_day, 1))
        else:
            gap = 24 * 60  # linkedin: 1 material dziennie
        grid = _parse_grid(cfg)
        if grid and r["channel"] == "x":
            gap = 30  # siatka SAMA definiuje kadencje - odstepy = odstepy siatki
        out.append((r["channel"], ws, we, gap, grid))
    return out


def _daily_cap(cfg, channel):
    """Twardy SUFIT liczby publikacji na dzien (kanon 25/07, zgloszenie Tomasza: seria X
    rozlewala sie ponad kadencje - 7-8 postow zamiast 3-5).

    Gap w channel_rules wymusza tylko ODSTEP miedzy postami, nie ich LICZBE: seria wolana
    z prefer_today upycha kolejne czesci, az okno sie wypelni. Ten limit jest niezalezny od
    gap/siatki/jittera - gdy dzien ma juz `cap` postow, next_slot przechodzi na kolejny dzien.
    Dla X: GORNA granica posts_per_day ('3-5' -> 5 = maksimum kadencji). LinkedIn: 1 (kanon 11d).
    Zwraca None = brak limitu."""
    fam = channel.split("_")[0]
    if fam == "x":
        raw = str(cfg.get("posts_per_day", "5")).replace(" ", "")
        try:
            return max(int(p) for p in raw.split("-") if p.isdigit())
        except ValueError:
            return 5
    if fam == "linkedin":
        return 1
    return None


def _busy(brand_id, channel, day_start, day_end):
    rows = db.fetchall(
        """SELECT scheduled_for FROM content_items
           WHERE brand_id=%s AND %s = ANY(target_channels) AND status = ANY(%s)
             AND scheduled_for >= %s AND scheduled_for < %s""",
        (brand_id, channel, list(BUSY_STATUSES), day_start, day_end))
    # #90 korekta 12/07 (seria X po slotach dnia): wiersze KOLEJKI tez zajmuja sloty -
    # jeden material moze miec wiele wierszy pq z roznymi slotami (bez tego kazdy element
    # serii dostawalby ten sam 'wolny' slot)
    rows2 = db.fetchall(
        """SELECT scheduled_for FROM post_queue
           WHERE brand=%s AND platform=%s AND status IN ('review','scheduled','queued','dispatching')
             AND scheduled_for >= %s AND scheduled_for < %s""",
        (brand_id, channel, day_start, day_end))
    return sorted({r["scheduled_for"].astimezone(WARSAW)
                   for r in (rows + rows2) if r.get("scheduled_for")})


def day_ok(channels, day, is_article=False):
    """Czy tego DNIA wolno publikowac na tych kanalach (kanon 19/07). JEDNO zrodlo prawdy.

    D-001 NAPRAWIONE 02/08/2026: regula sobotnia zyla WYLACZNIE wewnatrz `next_slot`, a sloty
    zapisywaly cztery rozne trasy. Trzy z nich dnia tygodnia NIE ZNALY:
      * planer - slot przychodzi od modelu, walidowany tylko jako ISO,
      * guzik "koniec kolejki" - bierze MAX(slot)+1 dzien, wiec z PIATKU robil SOBOTE
        jednym tapnieciem,
      * re-slotter - siatka gniazd bez sprawdzenia dnia.
    Post na LinkedIn w sobote wychodzil wiec wbrew kanonowi, bez zadnego ostrzezenia.

    `channels` przyjmuje pojedynczy kanal ALBO liste - trasy maja rozne ksztalty danych
    i nie chcemy, zeby ktoras ominela guard tylko dlatego, ze trzyma kanal jako napis."""
    chans = [channels] if isinstance(channels, str) else list(channels or [])
    if any(str(c).startswith("linkedin") for c in chans):
        return _li_ok(day, is_article)
    return True


def _li_ok(day, is_article):
    """Kanon 11d: LinkedIn pon-pt post, sobota NIC, niedziela artykul."""
    if day.weekday() == 5:
        return False
    if day.weekday() == 6:
        return is_article
    return not is_article or True  # artykul w tygodniu dopuszczamy, planer i tak celuje w niedziele


def next_slot(brand_id, channels_list, is_article=False, prefer_today=True):
    """Najblizszy wolny slot spelniajacy okna WSZYSTKICH kanalow materialu + odstepy kadencji.
    Zwraca datetime (WARSAW) albo None (nic w LOOKAHEAD_DAYS - nie powinno sie zdarzyc)."""
    rules = channel_rules(brand_id, channels_list)
    if not rules:
        return None
    # SUFIT KADENCJI (kanon 25/07): ile publikacji dziennie wolno na KAZDYM kanale materialu.
    cfg_rows = db.fetchall(
        "SELECT channel, config FROM channels WHERE brand_id=%s AND channel = ANY(%s)",
        (brand_id, list(channels_list)))
    caps = {r["channel"]: _daily_cap(r.get("config") or {}, r["channel"]) for r in cfg_rows}
    now = _teraz()
    start_day = now.date() if prefer_today else (now + datetime.timedelta(days=1)).date()
    grids = [g for *_, g in rules if g]
    grid_times = sorted({t for g in grids for t in g}) if grids else None
    for d in range(LOOKAHEAD_DAYS):
        day = start_day + datetime.timedelta(days=d)
        if any(ch.startswith("linkedin") for ch, *_ in rules) and not _li_ok(day, is_article):
            continue
        # przeciecie okien wszystkich kanalow
        ws = max(w for _, w, _, _, _ in rules)
        we = min(w for _, _, w, _, _ in rules)
        if ws >= we:
            continue
        day_start = datetime.datetime.combine(day, datetime.time(0, 0), WARSAW)
        day_end = day_start + datetime.timedelta(days=1)
        busy = {ch: _busy(brand_id, ch, day_start, day_end) for ch, *_ in rules}
        # SUFIT KADENCJI: dzien, w ktorym KTORYKOLWIEK kanal materialu osiagnal juz swoj limit,
        # jest pelny - kolejna czesc serii idzie na nastepny dzien (kanon 25/07, twardy sufit).
        if any(caps.get(ch) is not None and len(busy[ch]) >= caps[ch] for ch, *_ in rules):
            continue
        # siatka (jesli ustawiona) > skan co GRANULARITY_MIN w oknie
        if grid_times:
            candidates = [datetime.datetime.combine(day, gt, WARSAW) for gt in grid_times
                          if ws <= gt <= we]
        else:
            candidates = []
            t = datetime.datetime.combine(day, ws, WARSAW)
            end = datetime.datetime.combine(day, we, WARSAW)
            while t <= end:
                candidates.append(t)
                t += datetime.timedelta(minutes=GRANULARITY_MIN)
        for t in candidates:
            if t <= now + datetime.timedelta(minutes=2):
                continue
            ok = True
            for ch, _, _, gap, _ in rules:
                if any(abs((t - b).total_seconds()) < gap * 60 for b in busy[ch]):
                    ok = False
                    break
            if ok:
                return t
    return None


def humanize_slot(dt, spread_min=15):
    """KANON 19/07 (Tomasz): publikacje wychodza o NIEPELNYCH godzinach (np. 16:02, 15:59, 16:07),
    maksymalny rozrzut +/-15 min od slotu planu. Losowy offset przy wpisie do post_queue; minuta
    nigdy rowna kwadransowi (:00/:15/:30/:45 wygladaja maszynowo). content_items trzyma CZYSTY slot
    planu - roznica ci vs pq do 15 min jest ZAMIERZONA (to nie rozjazd z lekcji 07/07)."""
    if dt is None:
        return None
    cand = dt
    for _ in range(8):
        cand = dt + datetime.timedelta(minutes=random.randint(-spread_min, spread_min))
        if cand.minute % 15 != 0:
            break
    now = _teraz()
    if cand <= now:  # jitter nie cofa publikacji w przeszlosc (Scheduler strzela od razu)
        cand = dt if dt > now else now + datetime.timedelta(minutes=random.randint(2, 7))
    return cand


def assign_if_needed(item):
    """Dla 'approved': slot NULL albo miniony -> przydziel najblizszy wolny i zapisz.
    Zwraca (slot|None, changed:bool). Wolane z petli workera PRZED dispatchem."""
    now = _teraz()
    cur = item.get("scheduled_for")
    if cur is not None and cur.astimezone(WARSAW) > now - datetime.timedelta(minutes=10):
        return cur, False  # slot aktualny (10 min laski na przelot petli)
    is_article = str(item.get("master_theme") or "").startswith("[ARTYKUL]")
    slot = next_slot(item["brand_id"], item.get("target_channels") or ["x"], is_article=is_article)
    if slot is None:
        return cur, False
    db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s",
               (slot, item["id"]))
    # FIX 07/07: trzymaj post_queue w zgodzie z content_item (zrodlo prawdy). Bez tego wiersze
    # post_queue zostawaly na starym slocie (subagent czytal 10:00, choc ci = 13:00) - rozjazd.
    # Kolejka dostaje czas ULUDZKI (kanon 19/07: +/-15 min, niepelna godzina); ci = czysty slot.
    # UWAGA (29/07): to jest DRUGA trasa, ktora jednym UPDATE-em dotyka WSZYSTKICH wierszy
    # materialu. Przy materiale wieloczesciowym daje im ten sam czas - salwa. Dzis nie boli,
    # bo humanize_slot rozrzuca +/-15 min i kanon idzie na jeden wpis na material, ale gdyby
    # serie wrocily, to jest miejsce do rozsuwania czesci. slot_source (DDL 035) sprawia,
    # ze nastepnym razem widac to odczytem, a nie eliminacja tras.
    db.execute("""UPDATE post_queue SET scheduled_for=%s, slot_source='planner'
                  WHERE content_item_id=%s
                  AND status IN ('review','held','scheduled','queued','dispatching')""",
               (humanize_slot(slot), item["id"]))
    return slot, True
