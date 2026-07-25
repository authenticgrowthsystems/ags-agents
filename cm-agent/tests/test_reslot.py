"""Test re-slottera kolejki X (25/07): przeladowane dni schodza do sufitu, pierwsze `cap`
kazdego dnia zostaja nietkniete, nadmiar kaskaduje w kolejnosci (serie spojne).
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


def _fetchall(sql, params=None):
    if "FROM channels" in sql:
        return [{"config": {"posts_per_day": "3-5", "publish_windows": "09:00-21:00"}}]
    if "FROM post_queue" in sql:
        return list(QUEUE)
    return []


def _fetchone(sql, params=None):
    if "FROM channels" in sql:
        return {"config": {"posts_per_day": "3-5", "publish_windows": "09:00-21:00"}}
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


# Zbuduj przeladowana kolejke: dzien "za 2 dni" ma 7 postow (dwie serie), dzien "+3" ma 3.
baza = (_dt.datetime.now(WARSAW) + _dt.timedelta(days=2)).date()
dzien2 = baza + _dt.timedelta(days=1)
QUEUE = [
    # seria A (ci='AAA') - 4 czesci tego samego dnia
    {"id": 1, "content_item_id": "AAA", "scheduled_for": _slot(baza, 10, 5), "status": "scheduled", "tresc": "A1"},
    {"id": 2, "content_item_id": "AAA", "scheduled_for": _slot(baza, 12, 40), "status": "scheduled", "tresc": "A2"},
    {"id": 3, "content_item_id": "AAA", "scheduled_for": _slot(baza, 15, 3), "status": "scheduled", "tresc": "A3"},
    {"id": 4, "content_item_id": "AAA", "scheduled_for": _slot(baza, 17, 33), "status": "scheduled", "tresc": "A4"},
    # seria B (ci='BBB') - 3 czesci tego samego dnia (to one wypchna dzien ponad 5)
    {"id": 5, "content_item_id": "BBB", "scheduled_for": _slot(baza, 19, 2), "status": "scheduled", "tresc": "B1"},
    {"id": 6, "content_item_id": "BBB", "scheduled_for": _slot(baza, 20, 11), "status": "scheduled", "tresc": "B2"},
    {"id": 7, "content_item_id": "BBB", "scheduled_for": _slot(baza, 20, 55), "status": "scheduled", "tresc": "B3"},
    # dzien +3: tylko 2 posty (miejsce na nadmiar)
    {"id": 8, "content_item_id": "CCC", "scheduled_for": _slot(dzien2, 11, 7), "status": "scheduled", "tresc": "C1"},
    {"id": 9, "content_item_id": "CCC", "scheduled_for": _slot(dzien2, 16, 20), "status": "scheduled", "tresc": "C2"},
    # jeden bez slotu (ma trafic na koniec)
    {"id": 10, "content_item_id": "DDD", "scheduled_for": None, "status": "review", "tresc": "D1"},
]

changes, rozklad, cap = reslot.plan("AGS", "x")

print("\n[reslot] sufit i rozklad:")
check("cap = 5 (gorna granica 3-5)", cap == 5, cap)
check("zaden dzien nie przekracza sufitu", all(n <= cap for n in rozklad.values()), rozklad)

print("\n[reslot] pierwsze 5 przeladowanego dnia ZOSTAJA (nietkniete):")
zmienione_ids = {c[0] for c in changes}
check("#1-#5 (pierwsze 5 chronologicznie) nie ruszone",
      zmienione_ids.isdisjoint({1, 2, 3, 4, 5}), zmienione_ids)
check("#6 i #7 (nadmiar 6. i 7.) przeniesione", {6, 7}.issubset(zmienione_ids), zmienione_ids)
check("#10 (bez slotu) dostal slot", 10 in zmienione_ids, zmienione_ids)

print("\n[reslot] nowe sloty poprawne:")
now = _dt.datetime.now(WARSAW)
for _id, _ci, _old, new, _t in changes:
    check(f"#{_id} nowy slot w przyszlosci", new > now, new)
    check(f"#{_id} ludzka minuta (nie rowny kwadrans)", new.minute % 15 != 0, new.minute)
    check(f"#{_id} w oknie 09-21", 9 <= new.hour <= 21, new.hour)

print("\n[reslot] serie zachowuja kolejnosc:")
# #6 (B2) i #7 (B3) - nadmiar serii B - po przeniesieniu #7 nie przed #6
b_nowe = {c[0]: c[3] for c in changes if c[0] in (6, 7)}
if 6 in b_nowe and 7 in b_nowe:
    check("B2 (#6) przed B3 (#7) po przeniesieniu", b_nowe[6] < b_nowe[7], b_nowe)

print("\n[reslot] idempotencja: drugi przebieg nic nie zmienia:")
# zasymuluj zastosowanie: podmien sloty w QUEUE na nowe, usun None
applied = {c[0]: c[3] for c in changes}
for r in QUEUE:
    if r["id"] in applied:
        r["scheduled_for"] = applied[r["id"]]
changes2, rozklad2, _ = reslot.plan("AGS", "x")
check("po zastosowaniu planu drugi przebieg = 0 zmian", len(changes2) == 0, len(changes2))

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
