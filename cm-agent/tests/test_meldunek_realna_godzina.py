# -*- coding: utf-8 -*-
"""Test (03/08/2026, zgloszenie Tomasza): meldunek o slocie podaje godzine, o ktorej post
NAPRAWDE wyjdzie - nie godzine z siatki planowania.

POWOD. Kanon 19/07 mowi, ze publikacje wychodza o NIEPELNYCH godzinach: `post_queue` dostaje
czas po humanizacji (do 15 minut obok), a `content_items` trzyma czysty slot planu. Roznica
jest ZAMIERZONA. Wada byla gdzie indziej: `assign_if_needed` zwracalo czysty slot, wiec bot
meldowal "CM przydzielil slot: Tue 04/08 16:00", podczas gdy w kolejce stalo 15:49 i o tej
godzinie post faktycznie wychodzil. Tomasz zobaczyl obie liczby i slusznie zapytal, ktora jest
prawdziwa - to jest AP-312 w wydaniu liczbowym: **meldunek obiecywal godzine, ktora nie nastapi**.

PULAPKA, KTORA TEN TEST PILNUJE NAJMOCNIEJ: `humanize_slot` LOSUJE przy kazdym wywolaniu.
Naprawa "zawolajmy humanize_slot takze w meldunku" dalaby TRZECIA, jeszcze inna godzine -
i wygladalaby na dzialajaca, bo obie liczby bylyby "niepelne". Dlatego test nie sprawdza,
ze meldunek jest zhumanizowany. Sprawdza, ze niesie DOKLADNIE te wartosc, ktora poszla
do bazy.

Stdlib only. Uruchomienie: python cm-agent/tests/test_meldunek_realna_godzina.py"""
import datetime as _dt
import pathlib
import re
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)
WARSAW = _zi.ZoneInfo("Europe/Warsaw")

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class _Any:
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Any()

    def __getattr__(self, _n):
        return _Any()


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m


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
pkg.__path__ = [str(APP)]
sys.modules["app"] = pkg

from app import db, slots  # noqa: E402

# ---------------------------------------------------------------- podstawka
ZAPISY = []
db.execute = lambda sql, params=None: ZAPISY.append((" ".join((sql or "").split()), params))

SLOT = _dt.datetime.now(WARSAW).replace(microsecond=0, second=0, minute=0) + _dt.timedelta(days=1)
slots.next_slot = lambda *a, **k: SLOT

ITEM = {"id": "00000000-0000-0000-0000-000000000001", "brand_id": "AGS",
        "scheduled_for": None, "target_channels": ["linkedin"], "master_theme": "temat testowy"}


def _pola(fragment):
    """Parametry pierwszego zapisu, ktorego SQL zawiera podany fragment."""
    for sql, params in ZAPISY:
        if fragment in sql:
            return params
    return None


print("\n[ksztalt] funkcja oddaje TRZY rzeczy, w tym godzine realna:")
wynik = slots.assign_if_needed(dict(ITEM))
check("assign_if_needed zwraca trojke", isinstance(wynik, tuple) and len(wynik) == 3, repr(wynik))
slot, changed, realny = wynik
check("drugi element mowi, ze slot zostal przydzielony", changed is True, repr(changed))
check("trzeci element nie jest pusty przy przydzieleniu", realny is not None)

print("\n[sedno] godzina z meldunku to DOKLADNIE ta, ktora poszla do kolejki:")
pq = _pola("UPDATE post_queue SET scheduled_for")
ci = _pola("UPDATE content_items SET scheduled_for")
check("byl zapis do post_queue", pq is not None)
check("byl zapis do content_items", ci is not None)
check("trzeci element == czas zapisany do post_queue",
      pq is not None and realny == pq[0], f"realny={realny} pq={pq[0] if pq else None}")
check("content_items dostaje CZYSTY slot planu (roznica zamierzona, kanon 19/07)",
      ci is not None and ci[0] == SLOT, f"ci={ci[0] if ci else None} slot={SLOT}")

print("\n[anty-regresja] meldunek NIE moze losowac po raz drugi:")
# Gdyby naprawa wolala humanize_slot ponownie, ta asercja przechodzilaby tylko przypadkiem.
# Powtarzamy przydzial wielokrotnie: za kazdym razem zwrocona wartosc ma sie zgadzac z zapisem.
rozne = 0
for i in range(40):
    ZAPISY.clear()
    _s, _c, _r = slots.assign_if_needed(dict(ITEM))
    _pq = _pola("UPDATE post_queue SET scheduled_for")
    if _pq is None or _r != _pq[0]:
        check(f"przebieg {i}: zwrocona godzina rozjechala sie z zapisem", False,
              f"zwrocono={_r} zapisano={_pq[0] if _pq else None}")
        break
    if _r != SLOT:
        rozne += 1
else:
    check("40 przebiegow: zwrocona godzina ZAWSZE rowna tej z kolejki", True)
check("humanizacja faktycznie zachodzi (inaczej test nie mialby czego pilnowac)",
      rozne > 0, f"na 40 przebiegow zhumanizowanych: {rozne}")

print("\n[sciezki puste] brak przydzialu tez oddaje trojke:")
teraz = _dt.datetime.now(WARSAW)
w2 = slots.assign_if_needed(dict(ITEM, scheduled_for=teraz + _dt.timedelta(hours=3)))
check("slot juz aktualny -> trojka z changed=False", isinstance(w2, tuple) and len(w2) == 3
      and w2[1] is False, repr(w2))
slots.next_slot = lambda *a, **k: None
w3 = slots.assign_if_needed(dict(ITEM))
check("brak wolnego slotu -> trojka z changed=False", isinstance(w3, tuple) and len(w3) == 3
      and w3[1] is False, repr(w3))

print("\n[zrodlo] worker melduje godzine realna, nie czysty slot (AP-309):")
src = (APP / "worker.py").read_text(encoding="utf-8")
check("worker rozpakowuje trojke", "slot, changed, realny = slots.assign_if_needed(item)" in src)
check("worker liczy godzine meldunku z 'realny'", re.search(r"kiedy\s*=\s*realny\s+or\s+slot", src) is not None)
blok = src[src.find("slot, changed, realny"):src.find("slot, changed, realny") + 900]
check("tresc meldunku uzywa 'kiedy', a nie 'slot'",
      "kiedy.strftime" in blok and "slot.strftime" not in blok)
check("wartosc zwracana z petli tez pokazuje godzine realna",
      "slot_assigned({kiedy:" in blok, blok[-200:])

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
