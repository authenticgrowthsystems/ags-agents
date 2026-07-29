"""Test sladu audytowego zrodla slotu (29/07/2026, DDL 035, decyzja Managera).

POWOD: 28/07 piec wpisow wyszlo na X w piec minut, o 09:00, poza oknem 13:00-22:00, na koncie
ktore trzy dni wczesniej dostalo 403 za wykryta automatyzacje. Ustalenie, KTORA trasa nadala
ten slot, udalo sie wylacznie przez eliminacje wszystkich pozostalych - w danych nie bylo ani
jednego sladu. Ten test pilnuje, zeby kazdy zapis slotu zostawial etykiete.

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_slot_source.py"""
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

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def zrodlo(sql):
    """Wyciaga etykiete przypisana slot_source w danym SQL (albo None)."""
    import re
    m = re.search(r"slot_source\s*=\s*'([a-z]+)'", sql)
    if m:
        return m.group(1)
    m = re.search(r"slot_source\s*\)?[^)]*VALUES[^)]*'([a-z]+)'", sql, re.S)
    return None


# ---------------- kazdy zapis slotu ma etykiete ----------------
print("\n[DDL 035] kazda trasa zapisujaca slot zostawia etykiete zrodla:")

ZRODLA = pathlib.Path(BASE)
import re

def czytaj(nazwa):
    return (ZRODLA / nazwa).read_text(encoding="utf-8")


chan = czytaj("channels.py")
conv = czytaj("conversation.py")
slt = czytaj("slots.py")
rsl = czytaj("reslot.py")

check("staging (seria) wpisuje 'staging'",
      "'staging'" in chan and "slot_source" in chan)
check("staging INSERT-y maja kolumne w liscie",
      chan.count("scheduled_for, media, slot_source") == 2,
      f"znaleziono {chan.count('scheduled_for, media, slot_source')} z 2")
check("dispatch etykietuje TYLKO gdy sam nadaje slot",
      "CASE WHEN scheduled_for IS NULL THEN 'dispatch'" in chan,
      "inaczej nadpisze etykiete prawdziwego autora slotu")
check("przesuniecie materialu przez rozmowe wpisuje 'rozmowa'",
      "slot_source='rozmowa'" in conv)
check("przesuniecie POJEDYNCZEGO wiersza tez wpisuje 'rozmowa'",
      conv.count("slot_source='rozmowa'") == 2,
      f"znaleziono {conv.count(chr(39).join(['slot_source=', 'rozmowa', '']))}")
check("assign_if_needed wpisuje 'planner'", "slot_source='planner'" in slt)
check("reslot wpisuje 'reslot'", "slot_source='reslot'" in rsl)


# ---------------- zaden zapis slotu nie zostal bez etykiety ----------------
print("\n[DDL 035] nie ma zapisu slotu bez etykiety (AP-309: policz miejsca):")

def zapisy_slotu(tekst, nazwa):
    """Linie, ktore ustawiaja post_queue.scheduled_for."""
    out = []
    for blok in re.findall(r"(UPDATE post_queue[^\"']*?(?:\"\"\"|'))", tekst, re.S):
        if "scheduled_for" in blok and "SET" in blok:
            out.append((nazwa, blok))
    for blok in re.findall(r"(INSERT INTO post_queue.*?RETURNING id)", tekst, re.S):
        if "scheduled_for" in blok:
            out.append((nazwa, blok))
    return out


wszystkie = (zapisy_slotu(chan, "channels.py") + zapisy_slotu(conv, "conversation.py")
             + zapisy_slotu(slt, "slots.py") + zapisy_slotu(rsl, "reslot.py"))
bez_etykiety = [(n, b[:70]) for n, b in wszystkie if "slot_source" not in b]
check(f"wszystkie {len(wszystkie)} zapisow slotu maja etykiete",
      not bez_etykiety, str(bez_etykiety))

# Zapisy statusu BEZ slotu (np. 'held') nie musza etykietowac - nie ruszaja scheduled_for.
check("zapis samego statusu nie jest wymuszany do etykietowania",
      "UPDATE post_queue SET status='held' WHERE id=%s" in chan,
      "ten UPDATE nie rusza scheduled_for, wiec slusznie nie ma etykiety")

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
