"""Test re-slottera kolejki X v2 (25/07, "dopracuj: cale serie razem"): serie w ciaglych
blokach, czesci w kolejnosci narracyjnej (id), zaden dzien ponad sufit, ludzkie minuty.
Stdlib only, baza podstawiona stubem. Uruchomienie: python cm-agent/tests/test_reslot.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"
try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)
WARSAW = _zi.ZoneInfo("Europe/Warsaw")

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

QUEUE = []  # lista wierszy (dict) - ustawiana w tescie


WINDOW = {"v": "13:00-22:00"}  # okno X jak w produkcji (bug 25/07: siatka musi je respektowac)


def _fetchall(sql, params=None):
    if "FROM channels" in sql:
        return [{"config": {"posts_per_day": "3-5", "publish_windows": WINDOW["v"]}}]
    if "FROM post_queue" in sql:
        return list(QUEUE)
    return []


def _fetchone(sql, params=None):
    if "FROM channels" in sql:
        return {"config": {"posts_per_day": "3-5", "publish_windows": WINDOW["v"]}}
    return None


db_stub = types.ModuleType("app.db")
db_stub.fetchall = _fetchall
db_stub.fetchone = _fetchone
db_stub.execute = lambda *a, **k: None
sys.modules["app.db"] = db_stub

from app import reslot  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _slot(day, h, m):
    return _dt.datetime.combine(day, _dt.time(h, m), WARSAW)


# Kolejka jak PO pierwszym re-slocie: serie ROZPROSZONE (scheduled_for nie odzwierciedla juz
# kolejnosci narracyjnej), a id ja trzyma. Seria SS (id 1-6, 6 czesci) rozbita na rozne dni,
# w tym czesc #1 (hook) PO czesci #2 wg scheduled_for. Seria TT (id 10-12). Jeden bez slotu.
baza = (_dt.datetime.now(WARSAW) + _dt.timedelta(days=1)).date()
d2 = baza + _dt.timedelta(days=1)
d3 = baza + _dt.timedelta(days=2)
QUEUE = [
    # seria SS (ci='SS', id 1-6) - ROZPROSZONA: #1 (hook) ma pozniejszy slot niz #2-#4
    {"id": 1, "content_item_id": "SS", "scheduled_for": _slot(d3, 14, 3), "status": "scheduled", "tresc": "SS-hook"},
    {"id": 2, "content_item_id": "SS", "scheduled_for": _slot(baza, 10, 5), "status": "scheduled", "tresc": "SS-2"},
    {"id": 3, "content_item_id": "SS", "scheduled_for": _slot(baza, 12, 40), "status": "scheduled", "tresc": "SS-3"},
    {"id": 4, "content_item_id": "SS", "scheduled_for": _slot(baza, 15, 3), "status": "scheduled", "tresc": "SS-4"},
    {"id": 5, "content_item_id": "SS", "scheduled_for": _slot(d2, 17, 33), "status": "scheduled", "tresc": "SS-5"},
    {"id": 6, "content_item_id": "SS", "scheduled_for": _slot(d2, 19, 2), "status": "scheduled", "tresc": "SS-6"},
    # seria TT (ci='TT', id 10-12) - swiezo rozbita: IDENTYCZNY slot (kolejnosc tylko z id)
    {"id": 10, "content_item_id": "TT", "scheduled_for": _slot(d3, 14, 12), "status": "review", "tresc": "TT-1"},
    {"id": 11, "content_item_id": "TT", "scheduled_for": _slot(d3, 14, 12), "status": "review", "tresc": "TT-2"},
    {"id": 12, "content_item_id": "TT", "scheduled_for": _slot(d3, 14, 12), "status": "review", "tresc": "TT-3"},
    # wiersz bez serii i bez slotu
    {"id": 20, "content_item_id": None, "scheduled_for": None, "status": "review", "tresc": "solo"},
]

changes, rozklad, cap = reslot.plan("AGS", "x")
nowy = {c[0]: c[3] for c in changes}
# pelny nowy slot per id (zmienione + niezmienione) - do sprawdzenia kolejnosci calej sekwencji
wszystkie = dict(nowy)
for r in QUEUE:
    if r["id"] not in wszystkie and r["scheduled_for"] is not None:
        wszystkie[r["id"]] = r["scheduled_for"]

print("\n[reslot v2] sufit i rozklad:")
check("cap = 5 (gorna granica 3-5)", cap == 5, cap)
check("zaden dzien nie przekracza sufitu", all(n <= cap for n in rozklad.values()), rozklad)

print("\n[reslot v2] SERIA w kolejnosci narracyjnej (id), nie po starym slocie:")
ss = [wszystkie[i] for i in (1, 2, 3, 4, 5, 6)]
check("SS: #1(hook) < #2 < #3 < #4 < #5 < #6 wg NOWYCH slotow",
      all(ss[k] < ss[k + 1] for k in range(5)), [s.strftime('%d/%m %H:%M') for s in ss])
check("SS-hook (#1) PRZED SS-2 (#2) - mimo ze stary slot #1 byl pozniejszy",
      wszystkie[1] < wszystkie[2], (wszystkie[1], wszystkie[2]))

print("\n[reslot v2] SERIA jest CIAGLA (blok, bez obcych postow w srodku):")
# miedzy pierwszym a ostatnim slotem serii SS nie ma slotu z serii TT
ss_min, ss_max = min(ss), max(ss)
tt = [wszystkie[i] for i in (10, 11, 12)]
check("zaden post serii TT nie wpada w srodek bloku SS",
      not any(ss_min < t < ss_max for t in tt), [t.strftime('%d/%m %H:%M') for t in tt])
check("TT tez w kolejnosci id (#10<#11<#12)", tt[0] < tt[1] < tt[2],
      [t.strftime('%d/%m %H:%M') for t in tt])

print("\n[reslot v2] gniazda z OKNA kanalu (bug 25/07: siatka nie wykorzystywala okna):")
import datetime as _d2  # noqa: E402
grid5 = reslot._grid(_d2.time(13, 0), _d2.time(22, 0), 5)
check("okno 13-22, 5 gniazd -> wszystkie w oknie", all(_d2.time(13, 0) <= g <= _d2.time(22, 0) for g in grid5), grid5)
check("okno 13-22, 5 gniazd -> dokladnie 5", len(grid5) == 5, grid5)

print("\n[reslot v2] nowe sloty poprawne (okno 13-22):")
now = _dt.datetime.now(WARSAW)
for _id, _ci, _old, new, _t in changes:
    check(f"#{_id} w przyszlosci, ludzka minuta, w oknie",
          new > now and new.minute % 15 != 0 and 13 <= new.hour <= 22, new)

print("\n[reslot v2] gestosc sterowalna (per_day):")
ch3, roz3, nd3 = reslot.plan("AGS", "x", per_day=3)
check("per_day=3 -> max 3/dzien", nd3 == 3 and all(n <= 3 for n in roz3.values()), roz3)
ch9, roz9, nd9 = reslot.plan("AGS", "x", per_day=9)
check("per_day=9 -> przyciete do sufitu 5", nd9 == 5, nd9)

print("\n[reslot v2] idempotencja: drugi przebieg nic nie zmienia:")
for r in QUEUE:
    if r["id"] in nowy:
        r["scheduled_for"] = nowy[r["id"]]
changes2, _, _ = reslot.plan("AGS", "x")
check("po zastosowaniu planu drugi przebieg = 0 zmian", len(changes2) == 0, len(changes2))

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
