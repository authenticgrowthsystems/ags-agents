"""Test D-003 (02/08/2026): pola kontaktowe lejka zapisywalne RECZNIE i widoczne.

DWA OBJAWY jednej wady:
  1. `pipeline_text` POBIERALO `contact_person`, ale go NIE POKAZYWALO - prospekt z zapisana
     osoba dostawal etykiete "brak kontaktu". To ta sama rodzina co AP-312 i "BRAK nastepnego
     kroku" z 27/07: dane byly poprawne, klamala etykieta.
  2. `pipeline_add` i `pipeline_move` nie mialy pol kontaktowych, wiec wolal je wylacznie
     automat z researchu. Ciepłe dojscie podane przez czlowieka ("do Adamietza przez Piotra
     Hamryszaka") nie mialo gdzie zamieszkac i zylo poza systemem.

Stdlib only. Uruchomienie: python cm-agent/tests/test_kontakt_lejka.py"""
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

from app import db, sales  # noqa: E402

FAILS = []
EXEC = []
UTC = _dt.timezone.utc


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _wiersz(**kw):
    baza = {"prospect_name": "adamietz.pl", "stage": "qualified", "offer_tier": None,
            "value": None, "currency": "PLN", "next_followup_at": None,
            "updated_at": _dt.datetime.now(UTC), "notes": None,
            "contact_email": None, "contact_phone": None, "contact_person": None}
    baza.update(kw)
    return baza


STAN = {"rows": [], "one": {}}
db.fetchall = lambda sql, params=None: (STAN["rows"] if "FROM sales_pipeline" in sql else [])
db.fetchone = lambda sql, params=None: STAN["one"]
db.execute = lambda sql, params=None: EXEC.append((sql, params))


def widok(**kw):
    STAN["rows"] = [_wiersz(**kw)]
    STAN["one"] = {"won": 0, "lost": 0, "parked": 0, "won_value": 0}
    return sales.pipeline_text()


print("\n[objaw 1] etykieta 'brak kontaktu' przy WYPELNIONEJ osobie:")
t = widok(contact_person="Piotr Hamryszak (dojscie)")
check("osoba kontaktowa jest WIDOCZNA", "Piotr Hamryszak" in t, t[:300])
check("NIE mowi juz 'brak kontaktu'", "brak kontaktu" not in t, t[:300])

t2 = widok()
check("przy PUSTYCH polach nadal ostrzega", "brak kontaktu" in t2, t2[:300])

t3 = widok(contact_person="Piotr", contact_phone="600100200", contact_email="p@x.pl")
check("osoba idzie PIERWSZA - dojscie przez czlowieka jest cenniejsze niz numer",
      t3.index("Piotr") < t3.index("600100200") < t3.index("p@x.pl"), t3[:300])

print("\n[objaw 2] pola kontaktowe w schematach narzedzi:")
schematy = {s["name"]: s for s in getattr(sales, "_SALES_TOOLS", [])
            if isinstance(s, dict) and "name" in s}
check("znaleziono schematy narzedzi sprzedazy", bool(schematy), str(list(schematy)[:5]))
for nazwa in ("pipeline_add", "pipeline_move"):
    props = (schematy.get(nazwa, {}).get("input_schema") or {}).get("properties") or {}
    for pole in ("contact_person", "contact_email", "contact_phone"):
        check(f"{nazwa} przyjmuje {pole}", pole in props, f"brak w {nazwa}")

print("\n[zapis] dane z rozmowy faktycznie ida do bazy:")
STAN["one"] = None            # _find_pipeline -> brak duplikatu
EXEC.clear()
db.fetchone = lambda sql, params=None: ({"id": "x"} if "INSERT" in sql else None)
odp = sales._pipeline_add({"prospect_name": "Grupa Testowa",
                           "contact_person": "Jan Szuta", "contact_email": "j@x.pl",
                           "contact_phone": "694147748"})
check("dodanie prospekta zwraca potwierdzenie", "Grupa Testowa" in odp, odp)

STAN["one"] = _wiersz(id="p1")
db.fetchone = lambda sql, params=None: STAN["one"]
EXEC.clear()
odp2 = sales._pipeline_move({"prospect_fragment": "adamietz",
                             "contact_person": "przez Piotra Hamryszaka"})
zapis = " ".join(s for s, _ in EXEC)
check("aktualizacja pisze contact_person do bazy", "contact_person=%s" in zapis, zapis[:200])
check("potwierdzenie wymienia, co sie zmienilo",
      "Piotra" in odp2 or "osoba" in odp2, odp2[:200])

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
