# -*- coding: utf-8 -*-
"""Jednorazowy RE-SLOTTER kolejki X (25/07/2026, zgloszenie Tomasza).

Kolejka X urosla do 64 wierszy przez ~2 tygodnie i wiele dni ma WIECEJ niz kadencja
(25/07=7, 28/07=7, 30/07=9, 31/07=7), bo serie z jednego materialu rozlewaly sie ponad
sufit ZANIM sufit kadencji powstal (slots._daily_cap, 25/07). Ten skrypt sprzata to, co
juz w kolejce lezy - kanon "zalegle dane po naprawie".

ZASADA (dokladnie to, o co prosil Tomasz: "poustawiac tak by sie zgadzalo, a nadmiar
merytorycznie i logicznie spojnie przerzucic na nastepne dni"):
- Kazdy dzien zachowuje PIERWSZE `cap` publikacji chronologicznie - NIETKNIETE (ich sloty
  i grafiki zostaja; nie ruszamy tego, co dzis juz zaplanowane z zalacznikami).
- NADMIAR (6., 7., ... danego dnia) + wiersze BEZ slotu kaskaduja na najblizsze dni z
  wolnym miejscem, w KOLEJNOSCI - a poniewaz kolejnosc jest chronologiczna, a kazda seria
  jest chronologiczna, czesci serii ladują dalej w swojej kolejnosci (spojnosc zachowana).
- Nowy slot: wolne gniazdo z rownomiernej siatki dnia (10:00/12:30/15:00/17:30/20:00),
  z ludzka minuta (humanize_slot), >30 min od kazdego istniejacego slotu dnia, w przyszlosci.
- Media (grafiki Tomasza) NIE sa ruszane - zmieniamy WYLACZNIE scheduled_for.

Uruchomienie (SSH, Tomasz):
  docker exec cm-agent python -m app.reslot dry     # podglad planu, zero zmian
  docker exec cm-agent python -m app.reslot apply    # wykonanie (UPDATE post_queue + content_items)
"""
import datetime
import sys
from zoneinfo import ZoneInfo

from . import db
from .slots import humanize_slot, _parse_window, _daily_cap

WARSAW = ZoneInfo("Europe/Warsaw")
ACTIVE_STATUSES = ("review", "scheduled", "queued", "held")
# rownomierna siatka dnia (do `cap` gniazd); humanize_slot doda ludzka minute i +/-15
GRID = [datetime.time(10, 0), datetime.time(12, 30), datetime.time(15, 0),
        datetime.time(17, 30), datetime.time(20, 0)]
MIN_GAP_MIN = 30  # nowy slot nie blizej niz 30 min od istniejacego tego dnia


def _cfg(brand_id, channel):
    r = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s", (brand_id, channel))
    return (r or {}).get("config") or {}


def _rows(brand_id, channel):
    """Wiersze kolejki do rozplanowania: przyszle albo bez slotu. Kolejnosc = intencja
    (scheduled_for rosnaco, NULL na koniec, potem id) - trzyma serie w porzadku."""
    now = datetime.datetime.now(WARSAW)
    today0 = datetime.datetime.combine(now.date(), datetime.time(0, 0), WARSAW)
    return db.fetchall(
        """SELECT id, content_item_id, scheduled_for, status, left(content, 70) AS tresc
           FROM post_queue
           WHERE brand=%s AND platform=%s AND status = ANY(%s)
             AND (scheduled_for IS NULL OR scheduled_for >= %s)
           ORDER BY scheduled_for ASC NULLS LAST, id ASC""",
        (brand_id, channel, list(ACTIVE_STATUSES), today0))


def plan(brand_id="AGS", channel="x"):
    """Zwraca (zmiany, rozklad_dni). zmiany = [(id, stary_slot, nowy_slot, tresc)];
    rozklad_dni = {date: liczba_postow_po}. Zero zapisu do bazy."""
    cfg = _cfg(brand_id, channel)
    cap = _daily_cap(cfg, channel) or 5
    ws, we = _parse_window(cfg.get("publish_windows"), channel)
    now = datetime.datetime.now(WARSAW)
    rows = _rows(brand_id, channel)

    # 1) podzial: pierwsze `cap` chronologicznie kazdego dnia ZOSTAJA; reszta + NULL -> nadmiar
    keep_by_day = {}          # date -> [slot,...] (zajete, nietkniete)
    kept_ids = set()
    overflow = []
    dated = [r for r in rows if r["scheduled_for"] is not None]
    undated = [r for r in rows if r["scheduled_for"] is None]
    by_day = {}
    for r in dated:
        d = r["scheduled_for"].astimezone(WARSAW).date()
        by_day.setdefault(d, []).append(r)
    for d in sorted(by_day):
        day_rows = sorted(by_day[d], key=lambda r: (r["scheduled_for"], r["id"]))
        for r in day_rows[:cap]:
            keep_by_day.setdefault(d, []).append(r["scheduled_for"].astimezone(WARSAW))
            kept_ids.add(r["id"])
        overflow.extend(day_rows[cap:])
    overflow.extend(undated)
    # nadmiar w kolejnosci intencji (czas rosnaco, NULL na koniec, id)
    overflow.sort(key=lambda r: (r["scheduled_for"] or datetime.datetime.max.replace(tzinfo=WARSAW), r["id"]))

    # 2) rozklad nadmiaru na wolne gniazda kolejnych dni (od dzis)
    changes = []
    day = now.date()
    for r in overflow:
        placed = None
        probe = day
        for _ in range(60):  # bezpiecznik: max 60 dni w przod
            existing = keep_by_day.get(probe, [])
            if len(existing) < cap:
                for gt in GRID:
                    cand = datetime.datetime.combine(probe, gt, WARSAW)
                    if cand <= now + datetime.timedelta(minutes=5):
                        continue
                    if not (ws <= gt <= we):
                        continue
                    if all(abs((cand - e).total_seconds()) >= MIN_GAP_MIN * 60 for e in existing):
                        placed = humanize_slot(cand)
                        break
            if placed:
                keep_by_day.setdefault(probe, []).append(placed)
                break
            probe = probe + datetime.timedelta(days=1)
        if placed:
            changes.append((r["id"], r["content_item_id"], r["scheduled_for"], placed, r["tresc"]))
        day = probe  # kolejny nadmiar zaczyna szukac od ostatnio uzytego dnia (rownomiernie w przod)

    rozklad = {d: len(v) for d, v in sorted(keep_by_day.items())}
    return changes, rozklad, cap


def _print_plan(brand_id, channel):
    changes, rozklad, cap = plan(brand_id, channel)
    print(f"\n=== RE-SLOT {brand_id}/{channel} (sufit {cap}/dzien) ===", flush=True)
    print("\nROZKLAD PO ZMIANIE (dzien: liczba postow):", flush=True)
    for d, n in rozklad.items():
        flag = "  <-- PELNY" if n >= cap else ""
        print(f"  {d.strftime('%d/%m %a')}: {n}{flag}", flush=True)
    print(f"\nPRZENIESIENIA ({len(changes)} wierszy; reszta zostaje jak jest):", flush=True)
    for _id, _ci, old, new, tresc in changes:
        olds = old.astimezone(WARSAW).strftime("%d/%m %H:%M") if old else "bez slotu"
        news = new.strftime("%d/%m %H:%M")
        print(f"  #{_id}: {olds} -> {news} | {(tresc or '').strip()[:55]}", flush=True)
    return changes


def apply(brand_id="AGS", channel="x"):
    changes = _print_plan(brand_id, channel)
    if not changes:
        print("\nNic do przeniesienia - kolejka juz sie zgadza.", flush=True)
        return
    for _id, ci, _old, new, _t in changes:
        # tylko scheduled_for; media (grafiki Tomasza) nietkniete
        db.execute("UPDATE post_queue SET scheduled_for=%s WHERE id=%s", (new, _id))
        if ci:
            # content_items trzyma CZYSTY slot planu (bez jittera) - dla higieny ci<->pq
            db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s",
                       (new.replace(second=0, microsecond=0), ci))
    print(f"\nWYKONANE: przeniesiono {len(changes)} wierszy. Kolejka zgodna z sufitem {_daily_cap(_cfg(brand_id, channel), channel)}/dzien.",
          flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dry"
    bid = sys.argv[2] if len(sys.argv) > 2 else "AGS"
    ch = sys.argv[3] if len(sys.argv) > 3 else "x"
    if cmd == "apply":
        apply(bid, ch)
    else:
        _print_plan(bid, ch)
