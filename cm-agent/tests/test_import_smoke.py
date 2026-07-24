"""Dym: czy moduly cm-agenta w ogole sie IMPORTUJA po zmianach (cykle importow, literowki
w nazwach, brakujace importy). py_compile tego nie lapie - sprawdza tylko skladnie.
Ciezkie zaleznosci (psycopg, anthropic, httpx, openai) podstawione stubami; ZERO sieci i bazy.
Uruchomienie: python cm-agent/tests/test_import_smoke.py"""
import importlib
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
    """Obiekt, ktory udaje cokolwiek (klasa, klient, kursor) - do stubow bibliotek."""

    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Any()

    def __getattr__(self, _n):
        return _Any()


psycopg = _stub("psycopg", connect=lambda *a, **k: _Any(), Error=Exception)
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

# Windows bez pakietu tzdata nie zna 'Europe/Warsaw' (kontener linuksowy zna) - podstawiamy
# stala strefe, zeby test sprawdzal KOD, a nie baze stref systemu.
import datetime as _dt  # noqa: E402
import zoneinfo as _zi  # noqa: E402

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)  # noqa: A003

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

MODULY = ["brand", "compliance", "channels", "crm", "engagement", "decisions", "generate",
          "matreview", "planner", "proactive", "reports", "sales", "slots", "sunday_brief",
          "content_memory", "research", "tasks", "conversation"]

FAILS = []
for m in MODULY:
    try:
        importlib.import_module(f"app.{m}")
        print(f"  OK   import app.{m}")
    except Exception as e:
        print(f"  FAIL import app.{m} -> {type(e).__name__}: {e}")
        FAILS.append(m)

# po imporcie: czy glos idzie w CALOSCI (bug voice_bible[:2000], zgloszenie Managera 24/07)
from app import brand  # noqa: E402

fake = {"brand_id": "AGS", "voice_bible": "B" * 22000, "voice_dna_core": "R" * 4000}
blok = brand.voice_block(fake)
ok_dlugosc = len(blok["text"]) > 25000
ok_cache = blok.get("cache_control", {}).get("type") == "ephemeral"
ok_dna = "R" * 4000 in blok["text"]
print(f"  {'OK  ' if ok_dlugosc else 'FAIL'} blok glosu niesie CALA Voice Bible ({len(blok['text'])} znakow)")
print(f"  {'OK  ' if ok_dna else 'FAIL'} blok glosu niesie CALY voice_dna_core")
print(f"  {'OK  ' if ok_cache else 'FAIL'} blok glosu oznaczony do prompt-cache")
FAILS += [n for n, ok in (("dlugosc glosu", ok_dlugosc), ("dna w glosie", ok_dna),
                          ("cache glosu", ok_cache)) if not ok]

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
