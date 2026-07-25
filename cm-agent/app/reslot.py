# -*- coding: utf-8 -*-
"""Jednorazowy RE-SLOTTER kolejki X (25/07/2026, zgloszenie Tomasza).

Kolejka X urosla do 64 wierszy przez ~2 tygodnie i wiele dni ma WIECEJ niz kadencja
(25/07=7, 28/07=7, 30/07=9, 31/07=7), bo serie z jednego materialu rozlewaly sie ponad
sufit ZANIM sufit kadencji powstal (slots._daily_cap, 25/07). Ten skrypt sprzata to, co
juz w kolejce lezy - kanon "zalegle dane po naprawie".

ZASADA (v2, decyzja Tomasza 25/07 "dopracuj: cale serie razem" - grupowanie po serii):
- Przeplanowujemy CALA przyszla kolejke od dzis: SERIE w ciaglych blokach, czesci w
  kolejnosci NARRACYJNEJ. Hook idzie przed rozwinieciem, seria nie jest porozrzucana.
- Kolejnosc czesci w serii = `id` ASC (kolejnosc wstawiania przez stage_variant =
  narracyjna). NIE scheduled_for - ten zostal rozproszony poprzednim re-slotem v1.
- Kolejnosc SERII = najnizsze id (material powstal wczesniej -> publikuje sie wczesniej).
- Sloty: rownomierna siatka dnia (10:00/12:30/15:00/17:30/20:00), max cap/dzien, ludzka
  minuta (humanize_slot), w oknie, w przyszlosci. Dzien pelny -> seria plynie na kolejny.
- Media (grafiki Tomasza) NIE sa ruszane - zmieniamy WYLACZNIE scheduled_for.

Uruchomienie (SSH, Tomasz):
  docker exec cm-agent python -m app.reslot dry     # podglad planu, zero zmian
  docker exec cm-agent python -m app.reslot apply    # wykonanie (UPDATE post_queue + content_items)
"""
import datetime
import sys
from zoneinfo import ZoneInfo

from . import db
from .slots import _parse_window, _daily_cap

WARSAW = ZoneInfo("Europe/Warsaw")
ACTIVE_STATUSES = ("review", "scheduled", "queued", "held")
# rownomierna siatka dnia (do `cap` gniazd); humanize_slot doda ludzka minute i +/-15
GRID = [datetime.time(10, 0), datetime.time(12, 30), datetime.time(15, 0),
        datetime.time(17, 30), datetime.time(20, 0)]
MIN_GAP_MIN = 30  # nowy slot nie blizej niz 30 min od istniejacego tego dnia


def _human_minute(base, row_id):
    """Ludzka minuta DETERMINISTYCZNA per wiersz (nie losowa jak humanize_slot). Determinizm
    jest tu konieczny: bez niego kazdy dry/apply dawalby inne sloty i re-slotter nie bylby
    idempotentny (drugi przebieg zawsze widzialby 'zmiany'). Gniazdo pelna godzina -> +3..+13
    minut z id: nigdy rowny kwadrans (:00/:15/:30/:45 wyglada maszynowo, kanon 19/07)."""
    return base + datetime.timedelta(minutes=3 + (row_id * 7) % 11)


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


def _sequence(rows):
    """Kolejnosc publikacji: SERIE w calosci, czesci w kolejnosci NARRACYJNEJ.

    Kolejnosc czesci w serii = `id` ASC (kolejnosc, w jakiej stage_variant je wstawial =
    narracyjna: hook, potem rozwiniecie). NIE scheduled_for - ten zostal rozproszony
    poprzednim re-slotem, wiec nie odzwierciedla juz kolejnosci mysli. Kolejnosc SERII =
    najnizsze id w serii (material powstal wczesniej -> idzie wczesniej). Wiersze bez
    content_item_id = seria jednoelementowa."""
    groups = {}
    for r in rows:
        key = r["content_item_id"] or f"single:{r['id']}"
        groups.setdefault(key, []).append(r)
    seq = []
    for key in sorted(groups, key=lambda k: min(x["id"] for x in groups[k])):
        seq.extend(sorted(groups[key], key=lambda x: x["id"]))
    return seq


def plan(brand_id="AGS", channel="x"):
    """Zwraca (zmiany, rozklad_dni, cap). zmiany = [(id, ci, stary_slot, nowy_slot, tresc)].
    Przeplanowuje CALA kolejke: serie w ciaglych blokach, czesci w kolejnosci narracyjnej,
    od dzis, max cap/dzien, rownomierna siatka, ludzka minuta. Zero zapisu do bazy."""
    cfg = _cfg(brand_id, channel)
    cap = _daily_cap(cfg, channel) or 5
    ws, we = _parse_window(cfg.get("publish_windows"), channel)
    now = datetime.datetime.now(WARSAW)
    seq = _sequence(_rows(brand_id, channel))

    changes = []
    used_by_day = {}   # date -> [slot,...] przydzielone w tym planie
    probe = now.date()
    for r in seq:
        placed = None
        for _ in range(120):  # bezpiecznik: max 120 dni w przod
            slots_today = used_by_day.get(probe, [])
            if len(slots_today) < cap:
                for gt in GRID[:cap]:
                    if not (ws <= gt <= we):
                        continue
                    cand = datetime.datetime.combine(probe, gt, WARSAW)
                    if cand <= now + datetime.timedelta(minutes=5):
                        continue
                    if all(abs((cand - e).total_seconds()) >= MIN_GAP_MIN * 60 for e in slots_today):
                        placed = _human_minute(cand, r["id"])  # deterministyczne -> idempotentne
                        break
            if placed:
                used_by_day.setdefault(probe, []).append(placed)
                break
            probe = probe + datetime.timedelta(days=1)   # dzien pelny -> nastepny (serie ciagle)
        if placed:
            old = r["scheduled_for"]
            # zglaszamy tylko realna zmiane (co do minuty) - reszta zostaje
            if old is None or abs((placed - old.astimezone(WARSAW)).total_seconds()) >= 60:
                changes.append((r["id"], r["content_item_id"], old, placed, r["tresc"]))

    rozklad = {d: len(v) for d, v in sorted(used_by_day.items())}
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
