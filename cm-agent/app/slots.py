# -*- coding: utf-8 -*-
"""Okna publikacji + przydzial slotow (decyzja Tomasza 06/07: TOMASZ zatwierdza TRESC,
CM proponuje KIEDY). Zrodlo okien: channels.config.publish_windows ("HH:MM-HH:MM", zmienialne
z czatu przez target_update); kadencja: kanon 11d (X posts_per_day w oknie; LinkedIn pon-pt 1 post
~10:00, sob nic, nd artykul ~11:00). Material 'approved' bez slotu albo ze slotem MINIONYM nie
publikuje sie juz natychmiast - dostaje najblizszy wolny slot i Tomasz jest informowany (bot #2)."""
import datetime
from zoneinfo import ZoneInfo

from . import db

WARSAW = ZoneInfo("Europe/Warsaw")
DEFAULT_WINDOWS = {"x": "09:00-21:00", "linkedin": "08:00-18:00"}
BUSY_STATUSES = ("planned", "drafting", "needs_approval", "approved", "dispatching")
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


def _busy(brand_id, channel, day_start, day_end):
    rows = db.fetchall(
        """SELECT scheduled_for FROM content_items
           WHERE brand_id=%s AND %s = ANY(target_channels) AND status = ANY(%s)
             AND scheduled_for >= %s AND scheduled_for < %s""",
        (brand_id, channel, list(BUSY_STATUSES), day_start, day_end))
    return sorted(r["scheduled_for"].astimezone(WARSAW) for r in rows if r.get("scheduled_for"))


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
    now = datetime.datetime.now(WARSAW)
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


def assign_if_needed(item):
    """Dla 'approved': slot NULL albo miniony -> przydziel najblizszy wolny i zapisz.
    Zwraca (slot|None, changed:bool). Wolane z petli workera PRZED dispatchem."""
    now = datetime.datetime.now(WARSAW)
    cur = item.get("scheduled_for")
    if cur is not None and cur.astimezone(WARSAW) > now - datetime.timedelta(minutes=10):
        return cur, False  # slot aktualny (10 min laski na przelot petli)
    is_article = str(item.get("master_theme") or "").startswith("[ARTYKUL]")
    slot = next_slot(item["brand_id"], item.get("target_channels") or ["x"], is_article=is_article)
    if slot is None:
        return cur, False
    db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s",
               (slot, item["id"]))
    return slot, True
