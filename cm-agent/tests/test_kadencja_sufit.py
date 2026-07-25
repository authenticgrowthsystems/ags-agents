"""Test twardego sufitu kadencji (kanon 25/07): seria X nie rozlewa sie ponad posts_per_day.
Zgloszenie Tomasza: 7-8 tweetow na dzien zamiast 3-5. Stdlib only, baza podstawiona stubem.
Uruchomienie: python cm-agent/tests/test_kadencja_sufit.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

# Windows bez tzdata nie zna 'Europe/Warsaw' (kontener linuksowy zna) - podstawiamy stala strefe
# PRZED importem slots (slots.py woła ZoneInfo na poziomie modulu).
try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)
WARSAW = _zi.ZoneInfo("Europe/Warsaw")

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

# Stub bazy: konfiguracja kanalu X z posts_per_day=5, plus zajete sloty (busy) sterowane z testu.
STATE = {"posts_per_day": "3-5", "busy_ci": [], "busy_pq": []}


def _fetchall(sql, params=None):
    if "FROM channels" in sql:
        return [{"channel": "x", "config": {"posts_per_day": STATE["posts_per_day"],
                                            "publish_windows": "09:00-21:00"}}]
    # _busy filtruje po dniu w SQL (day_start, day_end = ostatnie 2 parametry) - stub musi
    # zrobic to samo, inaczej kazdy dzien widzi WSZYSTKIE sloty i wyglada na pelny.
    if "FROM content_items" in sql or "FROM post_queue" in sql:
        d0, d1 = params[-2], params[-1]
        src = STATE["busy_ci"] if "content_items" in sql else STATE["busy_pq"]
        return [{"scheduled_for": s} for s in src if d0 <= s < d1]
    return []


db_stub = types.ModuleType("app.db")
db_stub.fetchall = _fetchall
db_stub.fetchone = lambda *a, **k: None
db_stub.execute = lambda *a, **k: None
sys.modules["app.db"] = db_stub

from app import slots  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _sloty_dnia(dzien, n):
    """n slotow rozlozonych w oknie 09-21 danego dnia (symulacja zajetosci)."""
    return [_dt.datetime.combine(dzien, _dt.time(9 + i, 0), WARSAW) for i in range(n)]


print("\n[sufit kadencji] _daily_cap:")
check("X '3-5' -> gorna granica 5", slots._daily_cap({"posts_per_day": "3-5"}, "x") == 5)
check("X '4' -> 4", slots._daily_cap({"posts_per_day": "4"}, "x") == 4)
check("X domyslnie 5", slots._daily_cap({}, "x") == 5)
check("LinkedIn -> 1", slots._daily_cap({}, "linkedin") == 1)
check("linkedin_page -> 1", slots._daily_cap({}, "linkedin_page") == 1)

print("\n[sufit kadencji] dzien pelny przechodzi na jutro:")
jutro = (_dt.datetime.now(WARSAW) + _dt.timedelta(days=1)).date()
pojutrze = jutro + _dt.timedelta(days=1)
# dzis i jutro pelne (5 postow), pojutrze puste -> next_slot ma wskazac pojutrze
STATE["busy_ci"] = []
STATE["busy_pq"] = _sloty_dnia(_dt.datetime.now(WARSAW).date(), 5) + _sloty_dnia(jutro, 5)
slot = slots.next_slot("AGS", ["x"], prefer_today=True)
check("pelny dzis i jutro -> slot dopiero pojutrze",
      slot is not None and slot.date() == pojutrze, slot)

print("\n[sufit kadencji] dzien z miejscem dostaje slot:")
STATE["busy_pq"] = _sloty_dnia(_dt.datetime.now(WARSAW).date(), 2)  # tylko 2 dzis, limit 5
slot2 = slots.next_slot("AGS", ["x"], prefer_today=True)
check("2 z 5 zajete dzis -> slot jeszcze dzis",
      slot2 is not None and slot2.date() == _dt.datetime.now(WARSAW).date(), slot2)

print("\n[sufit kadencji] symulacja rozlewania serii (rdzen zgloszenia Tomasza):")
# Zaczynamy od 3 postow zaplanowanych na dzis; dokladamy serie 5 czesci PO KOLEI.
# Kazda czesc bierze next_slot i "zajmuje" go (jak stage_variant). Sprawdzamy, ze na dzien
# nie wejdzie wiecej niz 5 (limit), reszta przechodzi na kolejne dni.
STATE["busy_ci"] = []
STATE["busy_pq"] = _sloty_dnia(_dt.datetime.now(WARSAW).date(), 3)
przydzielone = []
for _ in range(5):  # 5-czesciowa seria
    s = slots.next_slot("AGS", ["x"], prefer_today=True)
    assert s is not None
    przydzielone.append(s)
    STATE["busy_pq"].append(s)  # symuluj zapis czesci do kolejki
per_dzien = {}
for s in przydzielone:
    per_dzien[s.date()] = per_dzien.get(s.date(), 0) + 1
dzis = _dt.datetime.now(WARSAW).date()
check("dzis dostalo tylko 2 czesci (3 juz byly, sufit 5)", per_dzien.get(dzis, 0) == 2, per_dzien)
check("zaden dzien nie przekroczyl sufitu 5",
      all(v <= 5 for v in per_dzien.values()), per_dzien)
check("cala seria zostala rozlozona (5 czesci)", len(przydzielone) == 5)
check("nadmiar przeszedl na kolejne dni", len(per_dzien) >= 2, per_dzien)

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
