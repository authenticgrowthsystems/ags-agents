"""Test D-006 (02/08/2026): stan rozsylki materialu widoczny, nie domyslany.

POWOD: 27/07 Manager zglosil "zawieszony post" - status `dispatching` nie mial limitu czasu,
a ani system, ani CM nie potrafili powiedziec, czy material jest w trakcie wysylki, czy zawisl.
Odczyt pokazal siedem materialow w tym stanie, WSZYSTKIE ZDROWE: najstarszy siedzial 51 godzin
i bylo to poprawne, bo re-slotter rozrzucil jego serie az do 4 sierpnia.

Wada nie byla w danych. Byla w tym, ze **nazwa stanu obiecywala sekundy** (AP-312), a widok
nie pokazywal ANI ILE WIERSZY zostalo, ANI NA KIEDY. Sama nazwa tego nie rozstrzygnie i nie
ma jak - rozstrzyga liczba wierszy i ich terminy.

Stdlib only. Uruchomienie: python cm-agent/tests/test_stan_rozsylki.py"""
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


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


class _Any:
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Any()

    def __getattr__(self, _n):
        return _Any()


_stub("psycopg", connect=lambda *a, **k: _Any(), Error=Exception)
_stub("psycopg.types")
_stub("psycopg.types.json", Jsonb=lambda o: o)
_stub("psycopg_pool", ConnectionPool=_Any)
_stub("psycopg.rows", dict_row=lambda *a, **k: None)
_stub("httpx", post=lambda *a, **k: _Any(), get=lambda *a, **k: _Any(), Client=_Any,
      TransportError=Exception)
_stub("anthropic", Anthropic=_Any)
_stub("openai", OpenAI=_Any)
_stub("fastapi", FastAPI=_Any, Request=_Any, BackgroundTasks=_Any, Body=lambda *a, **k: None)
_stub("uvicorn", run=lambda *a, **k: None)
_stub("openpyxl", load_workbook=lambda *a, **k: _Any())

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

from app import db, matreview  # noqa: E402

FAILS = []
STAN = {}


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


db.fetchone = lambda sql, params=None: STAN.get("wiersz")


def ustaw(wszystkie, czeka, najblizszy=None, ostatni=None):
    STAN["wiersz"] = {"wszystkie": wszystkie, "czeka": czeka,
                      "najblizszy": najblizszy, "ostatni": ostatni}


D1 = _dt.datetime(2026, 8, 3, 14, 15, tzinfo=WARSAW)
D2 = _dt.datetime(2026, 8, 7, 19, 40, tzinfo=WARSAW)

print("\n[etykieta] nazwa nie moze obiecywac sekund przy stanie, ktory trwa dniami:")
check("stan rozsylki NIE nazywa sie juz 'W PUBLIKACJI'",
      matreview._VIEW_STATUS_PL.get("dispatching") != "W PUBLIKACJI",
      matreview._VIEW_STATUS_PL.get("dispatching"))
check("nowa etykieta mowi, CO SIE STALO, a nie co sie dzieje",
      "ROZESLANY" in (matreview._VIEW_STATUS_PL.get("dispatching") or ""),
      matreview._VIEW_STATUS_PL.get("dispatching"))

print("\n[zdrowe czekanie] widac ILE i NA KIEDY:")
ustaw(wszystkie=5, czeka=3, najblizszy=D1, ostatni=D2)
t = matreview._stan_rozsylki("m1")
check("podaje, ile wierszy czeka z ilu", "czeka 3 z 5 wpisow" in t, t)
check("podaje najblizszy termin", "najblizszy 03/08 14:15" in t, t)
check("podaje OSTATNI termin - stad wiadomo, jak dlugo stan potrwa",
      "ostatni 07/08 19:40" in t, t)
check("nie straszy ostrzezeniem, bo nie ma czym", "⚠️" not in t, t)

print("\n[jedyny prawdziwy objaw zawieszenia] zero oczekujacych, a material nadal czeka:")
ustaw(wszystkie=5, czeka=0)
t0 = matreview._stan_rozsylki("m1")
check("ostrzega wprost", "⚠️" in t0 and "zawieszenie" in t0, t0)
check("mowi, ze WSZYSTKIE wpisy sa juz zamkniete", "wszystkie 5 wpisow" in t0, t0)

print("\n[brak wierszy] cisza zamiast falszywego alarmu:")
ustaw(wszystkie=0, czeka=0)
check("material bez kolejki nie generuje zadnego dopisku",
      matreview._stan_rozsylki("m1") == "", repr(matreview._stan_rozsylki("m1")))

STAN["wiersz"] = None
check("brak odpowiedzi z bazy tez nie generuje dopisku",
      matreview._stan_rozsylki("m1") == "")

print("\n[wydajnosc] jedno zapytanie, nie N+1:")
LICZNIK = {"n": 0}


def _liczaca(sql, params=None):
    LICZNIK["n"] += 1
    return {"wszystkie": 5, "czeka": 2, "najblizszy": D1, "ostatni": D2}


db.fetchone = _liczaca
matreview._stan_rozsylki("m1")
check("jeden odczyt na material", LICZNIK["n"] == 1, str(LICZNIK["n"]))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
