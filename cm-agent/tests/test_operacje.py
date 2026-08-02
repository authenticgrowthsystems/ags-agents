"""Test D-007 (02/08/2026): operacja hurtowa zostawia slad czytelny dla DRUGIEGO agenta.

POWOD: po wycofaniu 21 materialow Content Manager zapytal, PO CZYM ma je rozpoznac.
Nie brakowalo danych - byly NIEODROZNIALNE od odrzucen sprzed miesiaca.

Stdlib only. Uruchomienie: python cm-agent/tests/test_operacje.py"""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"


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

from app import db, operacje  # noqa: E402

FAILS = []
EXEC = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


db.execute = lambda sql, params=None: EXEC.append((sql, params))
db.fetchone = lambda sql, params=None: {"op_id": "wycofanie-serii-29072026",
                                        "kiedy": "2026-07-29 00:00:00+02", "kto": "BE",
                                        "opis": "Wycofanie 21 materialow X",
                                        "warunek": "status rejected + X + >1 wiersz",
                                        "wierszy": 21}
db.fetchall = lambda sql, params=None: []

print("\n[rejestracja] operacja opisuje sie ZANIM zadziala:")
EXEC.clear()
op = operacje.zarejestruj("wycofanie-serii-29072026", "BE", "Wycofanie 21 materialow X",
                          warunek="status rejected + X + >1 wiersz")
check("identyfikator znormalizowany", op == "wycofanie-serii-29072026", op)
check("wpis idzie do rejestru", any("bulk_operations" in s for s, _ in EXEC))
check("ponowne wolanie nie duplikuje", any("ON CONFLICT" in s for s, _ in EXEC))


def blad(*a, **k):
    try:
        operacje.zarejestruj(*a, **k)
        return None
    except operacje.Blad as e:
        return str(e)


print("\n[kontrakt] identyfikator ma byc pisany z pamieci, wiec ograniczony:")
check("polskie znaki odrzucone", blad("wycofanie-serii-Chwaliński", "BE", "x") is not None)
# Wielkosc liter NIE jest bledem - identyfikator pisze sie z pamieci, a karanie za shift
# byloby pedanteria. Kod normalizuje do malych liter i to jest zachowanie wlasciwe.
check("wielkie litery NORMALIZOWANE, nie odrzucane",
      operacje.zarejestruj("Wycofanie-Serii-Testowej", "BE", "x") == "wycofanie-serii-testowej")
check("spacja odrzucona", blad("wycofanie serii", "BE", "x") is not None)
check("za krotki odrzucony", blad("abc", "BE", "x") is not None)
check("operacja BEZ OPISU odrzucona - bez opisu slad jest bezuzyteczny",
      blad("jakas-operacja-x", "BE", "  ") is not None)
check("poprawny przechodzi", blad("import-listy-27072026", "BE", "Import listy prospektow") is None)

print("\n[stempel] dotkniete wiersze niosa identyfikator operacji:")
EXEC.clear()
n = operacje.oznacz("wycofanie-serii-29072026", "content_items", ["a", "b", "c"])
check("oznaczono trzy wiersze", n == 3, str(n))
check("UPDATE trafia we wskazana tabele", any("UPDATE content_items" in s for s, _ in EXEC))
check("licznik operacji przeliczony", any("SET wierszy" in s for s, _ in EXEC))

check("pusta lista nie generuje zapisu",
      operacje.oznacz("x", "content_items", []) == 0)

# Nazwa tabeli jest wklejana do SQL, wiec MUSI przechodzic przez biala liste.
try:
    operacje.oznacz("x", "content_items; DROP TABLE contacts", ["a"])
    check("nieznana tabela odrzucona", False, "przeszla")
except operacje.Blad:
    check("nieznana tabela odrzucona (biala lista, nie interpolacja)", True)

print("\n[odczyt] drugi agent dostaje odpowiedz, a nie surowy identyfikator:")
o = operacje.opis("wycofanie-serii-29072026")
check("opis mowi, co to bylo", "Wycofanie 21 materialow" in o, o[:120])
check("opis podaje warunek", "warunek" in o.lower(), o[:200])
check("opis podaje liczbe wierszy", "21" in o, o[:200])

db.fetchone = lambda sql, params=None: None
check("nieznana operacja nie udaje, ze wie", "Nie znam operacji" in operacje.opis("nieistniejaca-op"))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
