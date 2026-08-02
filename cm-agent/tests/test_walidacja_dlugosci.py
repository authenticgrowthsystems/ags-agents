"""Test walidacji dlugosci + pola formatu (02/08/2026, polecenie Managera odblokowane).

POLECENIE: "odrzucenie materialu przekraczajacego limit kanalu z jawnym komunikatem,
NIGDY z cichym obcieciem".

DRUGA RZECZ, ZNALEZIONA PRZY OKAZJI: decyzja Managera z 29/07 "X dostaje JEDEN wpis na material,
koniec serii" NIGDY NIE WESZLA DO KODU. Dane wyczyszczono tego samego dnia (21 materialow
wycofanych), ale `channels.py` nadal rozbijal wariant X dluzszy niz 600 znakow na serie.
Kolejka byla pusta, wiec przez cztery dni nikt tego nie zauwazyl.

Stdlib only. Uruchomienie: python cm-agent/tests/test_walidacja_dlugosci.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

# Podmiana PRZED importem modulow aplikacji: `channels.stage_variant` robi leniwy
# `from . import slots`, a slots.py woła ZoneInfo("Europe/Warsaw") juz przy imporcie.
try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)

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

from app import channels, db  # noqa: E402

FAILS = []
WSTAWIONE = []
POWIADOMIENIA = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _fetchone(sql, params=None):
    if "INSERT INTO post_queue" in sql:
        WSTAWIONE.append(params)
        return {"id": f"pq{len(WSTAWIONE)}"}
    return None


db.fetchone = _fetchone
db.execute = lambda sql, params=None: None
db.fetchall = lambda sql, params=None: []

_stub("app.logbot", send=lambda text, silent=True: POWIADOMIENIA.append(text),
      _admin_chat_id=lambda: 1)
channels._c = types.SimpleNamespace(strip_meta_header=lambda s: s)
channels._slots = types.SimpleNamespace(next_slot=lambda *a, **k: None,
                                        humanize_slot=lambda s: s)
channels._pub_media = lambda m: []


def staging(tekst, kanal="x", cfg=None, format_materialu="post"):
    WSTAWIONE.clear()
    POWIADOMIENIA.clear()
    item = {"id": "m1", "brand_id": "AGS", "master_theme": "Temat testowy",
            "media": [], "scheduled_for": None, "format": format_materialu}
    ch = {"channel": kanal, "config": cfg or {}}
    return channels.stage_variant(item, ch, tekst)


print("\n[limity] jedno zrodlo prawdy, z mozliwoscia nadpisania w konfiguracji:")
check("X domyslnie 25000 (konto Premium, nie 280)",
      channels.limit_znakow({"channel": "x", "config": {}}) == 25000)
check("LinkedIn domyslnie 3000", channels.limit_znakow({"channel": "linkedin", "config": {}}) == 3000)
check("artykul ma wlasny, duzo wyzszy limit",
      channels.limit_znakow({"channel": "linkedin", "config": {}}, "article") > 100000)
check("konfiguracja kanalu NADPISUJE wartosc domyslna",
      channels.limit_znakow({"channel": "x", "config": {"max_len": 500}}) == 500)
check("smiec w konfiguracji nie wysadza - wraca wartosc domyslna",
      channels.limit_znakow({"channel": "x", "config": {"max_len": "duzo"}}) == 25000)

print("\n[odrzucenie] za dlugi wariant NIE trafia do kolejki i NIE jest obcinany:")
wynik = staging("x" * 4000, kanal="linkedin")
check("nic nie wstawiono do kolejki", not WSTAWIONE, str(len(WSTAWIONE)))
check("funkcja zwraca None, nie udaje sukcesu", wynik is None, str(wynik))
check("czlowiek dostaje powiadomienie", len(POWIADOMIENIA) == 1, str(POWIADOMIENIA))
p = POWIADOMIENIA[0] if POWIADOMIENIA else ""
check("komunikat podaje limit i faktyczna dlugosc", "3000" in p and "4000" in p, p[:200])
check("komunikat podaje, o ile za duzo", "1000" in p, p[:200])
check("komunikat mowi WPROST, ze nie obcina", "NIE obcinam" in p, p[:200])
check("komunikat nazywa material", "Temat testowy" in p, p[:200])

print("\n[przepuszczenie] mieszczacy sie wariant przechodzi normalnie:")
staging("y" * 2999, kanal="linkedin")
check("wiersz wstawiony", len(WSTAWIONE) == 1, str(len(WSTAWIONE)))
check("bez powiadomienia o bledzie", not POWIADOMIENIA, str(POWIADOMIENIA))
check("format zapisany jako 'post'", "post" in [str(x) for x in (WSTAWIONE[0] or ())],
      str(WSTAWIONE[0]))

print("\n[SERIA ZNIESIONA] dlugi wariant X nie jest juz dzielony na kawalki:")
# Przed 02/08: tekst X > 600 znakow ALBO ze znacznikiem ===POST=== byl ciety na serie.
dlugi_x = ("akapit pierwszy. " * 40) + "\n\n" + ("akapit drugi. " * 40)
staging(dlugi_x, kanal="x")
check("dlugi wariant X daje DOKLADNIE JEDEN wiersz, nie serie",
      len(WSTAWIONE) == 1, f"wierszy: {len(WSTAWIONE)}")
staging("czesc A ===POST=== czesc B ===POST=== czesc C", kanal="x")
check("znacznik ===POST=== tez nie tworzy juz serii",
      len(WSTAWIONE) == 1, f"wierszy: {len(WSTAWIONE)}")

print("\n[format artykulu] material oznaczony jako artykul ma inny limit:")
staging("z" * 5000, kanal="linkedin", format_materialu="article")
check("artykul 5000 znakow PRZECHODZI (limit posta by go odrzucil)",
      len(WSTAWIONE) == 1 and not POWIADOMIENIA, f"wstawione={len(WSTAWIONE)}")
check("format zapisany jako 'article'", "article" in [str(x) for x in (WSTAWIONE[0] or ())],
      str(WSTAWIONE[0]))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
