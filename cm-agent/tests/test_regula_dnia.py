"""Test D-001 (02/08/2026): regula dnia tygodnia pilnowana we WSZYSTKICH czterech trasach.

POWOD: sobota byla twardo wycieta dla LinkedIna, ale WYLACZNIE wewnatrz `slots.next_slot`.
Sloty zapisywaly CZTERY rozne trasy i trzy z nich dnia tygodnia nie znaly:
  * planer - slot od modelu, walidowany tylko jako ISO,
  * guzik "koniec kolejki" - MAX(slot)+1 dzien, wiec z PIATKU robil SOBOTE jednym tapnieciem,
  * re-slotter - siatka gniazd bez sprawdzenia dnia.
Post na LinkedIn w sobote wychodzil wbrew kanonowi 19/07, bez zadnego ostrzezenia.

Test pilnuje DWOCH rzeczy: samej reguly ORAZ tego, ze wszystkie cztery trasy o nia pytaja
(AP-309 - jedna naprawa, wiele miejsc).

Stdlib only. Uruchomienie: python cm-agent/tests/test_regula_dnia.py"""
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

from app import slots  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# 2026-08-07 to piatek, 08 sobota, 09 niedziela, 10 poniedzialek.
PT = _dt.datetime(2026, 8, 7, 10, 0, tzinfo=WARSAW)
SO = _dt.datetime(2026, 8, 8, 10, 0, tzinfo=WARSAW)
ND = _dt.datetime(2026, 8, 9, 10, 0, tzinfo=WARSAW)
PN = _dt.datetime(2026, 8, 10, 10, 0, tzinfo=WARSAW)

print("\n[kalendarz] sanity - dni tygodnia zgadzaja sie z zalozeniem testu:")
check("piatek", PT.weekday() == 4)
check("sobota", SO.weekday() == 5)
check("niedziela", ND.weekday() == 6)

print("\n[regula] kanon 19/07: LinkedIn pon-pt post, sobota NIC, niedziela artykul:")
check("sobota zabroniona dla LinkedIna", slots.day_ok(["linkedin"], SO) is False)
check("piatek dozwolony", slots.day_ok(["linkedin"], PT) is True)
check("poniedzialek dozwolony", slots.day_ok(["linkedin"], PN) is True)
check("niedziela TYLKO artykul", slots.day_ok(["linkedin"], ND, is_article=True) is True)
check("niedziela: zwykly post zabroniony", slots.day_ok(["linkedin"], ND) is False)

print("\n[zakres] regula dotyczy LinkedIna, nie wszystkiego:")
check("X w sobote dozwolony", slots.day_ok(["x"], SO) is True)
check("material X+LinkedIn w sobote ZABRONIONY (decyduje kanal ostrzejszy)",
      slots.day_ok(["x", "linkedin"], SO) is False)
check("brak kanalow nie blokuje", slots.day_ok([], SO) is True)
check("None nie wysadza", slots.day_ok(None, SO) is True)

# Trasy trzymaja kanal w roznych ksztaltach: lista (planer, karta) albo napis (re-slotter).
# Gdyby funkcja przyjmowala tylko liste, re-slotter cicho ominalby guard.
print("\n[ksztalt danych] napis dziala tak samo jak lista:")
check("kanal jako NAPIS tez jest sprawdzany", slots.day_ok("linkedin", SO) is False)
check("napis 'x' przechodzi", slots.day_ok("x", SO) is True)
check("wariant z sufiksem (linkedin_tnm) tez lapie", slots.day_ok("linkedin_tnm", SO) is False)

print("\n[AP-309] wszystkie CZTERY trasy zapisujace slot pytaja o regule:")
ZRODLA = {
    "slots.next_slot (trasa pierwotna)": ("cm-agent/app/slots.py", "_li_ok(day, is_article)"),
    "planer (slot od modelu)": ("cm-agent/app/planner.py", "day_ok("),
    "guzik koniec kolejki": ("cm-agent/app/matreview.py", "day_ok("),
    "re-slotter": ("cm-agent/app/reslot.py", "day_ok("),
}
for opis, (plik, wzor) in ZRODLA.items():
    src = pathlib.Path(plik).read_text(encoding="utf-8")
    check(f"{opis} pyta o regule", wzor in src, f"brak '{wzor}' w {plik}")

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
