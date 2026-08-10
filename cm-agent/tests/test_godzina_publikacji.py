# -*- coding: utf-8 -*-
"""Test (10/08/2026, D-015 domkniete): meldunek podaje MAX ze slotu planu i czasu kolejki.

HISTORIA W TRZECH KROKACH, BO SAMA REGULA BEZ NIEJ WYGLADA NA KAPRYS.

  1. Do 03/08 meldunek podawal CZYSTY SLOT PLANU (16:00), a w kolejce stalo 15:49. Tomasz
     zobaczyl dwie liczby i zapytal, ktora jest prawdziwa.
  2. Poprawka z 03/08 (d5cd43e) przestawila meldunek na CZAS KOLEJKI. Wygladalo to na
     domkniecie sprawy - bo faktycznie kolejka jest blizej rzeczywistosci... czasami.
  3. 10/08 odczyt bazy pokazal, ze OBIE wersje myla sie w polowie przypadkow.

DLACZEGO. Publikacje pilnuja DWIE bramki, obie z warunkiem "<= NOW()":
  * `db.claim_item` nie bierze materialu `approved`, dopoki nie minie `content_items.scheduled_for`
    (czyli SLOT PLANU) - wiec wczesniejszy czas kolejki jest martwy;
  * Scheduler n8n publikuje `post_queue` w stanie 'scheduled', a wiersz wchodzi w ten stan
    dopiero w dispatchu, czyli PO otwarciu pierwszej bramki.
`humanize_slot` losuje symetrycznie +/-15 min, wiec w polowie przebiegow kolejka wypada
WCZESNIEJ niz slot - i wtedy nie ma zadnego znaczenia.

DOWOD, NIE TEORIA:
  #344  kolejka 15:49, slot planu 16:00  ->  opublikowane 04/08 16:01
  #358  kolejka 15:50, slot planu 16:00  ->  opublikowane 05/08 16:01
Poszlaka: wszystkie zaobserwowane publikacje (13:48, 16:10, 16:31, 16:59, 17:48, 19:12,
20:23, 10:01) wypadaja PO najblizszym okraglym slocie, ani jedna przed. Przy losowaniu
symetrycznym polowa powinna wypasc wczesniej.

CZEGO TEN TEST PILNUJE: nie tego, ze meldunek jest "zhumanizowany" ani ze "rowna sie kolejce" -
oba te sformulowania byly juz raz uznane za prawde i oba byly polprawda. Pilnuje REGULY:
podana godzina nigdy nie jest WCZESNIEJSZA niz slot planu, bo taka godzina nie moze nastapic.

Stdlib only. Uruchomienie: python cm-agent/tests/test_godzina_publikacji.py"""
import datetime as _dt
import pathlib
import random
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
_stub("fastapi", FastAPI=_Any, Request=_Any, BackgroundTasks=_Any, Body=lambda *a, **k: None,
      Header=lambda *a, **k: None, HTTPException=Exception)
_stub("uvicorn", run=lambda *a, **k: None)
_stub("openpyxl", load_workbook=lambda *a, **k: _Any())

pkg = types.ModuleType("app")
pkg.__path__ = [str(APP)]
sys.modules["app"] = pkg

from app import worker  # noqa: E402

G = worker._godzina_publikacji
SLOT = _dt.datetime(2026, 8, 4, 16, 0, tzinfo=WARSAW)

print("\n[przypadek 344 i 358] kolejka WCZESNIEJ niz slot -> liczy sie slot planu:")
for minuta, etykieta in ((49, "#344 kolejka 15:49"), (50, "#358 kolejka 15:50")):
    kolejka = SLOT.replace(minute=minuta) - _dt.timedelta(hours=0)
    kolejka = _dt.datetime(2026, 8, 4, 15, minuta, tzinfo=WARSAW)
    check(f"{etykieta} -> meldunek podaje 16:00, nie 15:{minuta}",
          G(SLOT, kolejka) == SLOT, f"dostano {G(SLOT, kolejka)}")

print("\n[przypadek odwrotny] kolejka POZNIEJ niz slot -> liczy sie kolejka:")
for minuta in (1, 7, 10, 12, 15):
    kolejka = _dt.datetime(2026, 8, 4, 16, minuta, tzinfo=WARSAW)
    check(f"kolejka 16:{minuta:02d} -> meldunek podaje 16:{minuta:02d}",
          G(SLOT, kolejka) == kolejka, f"dostano {G(SLOT, kolejka)}")

print("\n[regula] podana godzina NIGDY nie jest wczesniejsza niz slot planu:")
# 200 losowan po tym samym rozkladzie, ktorego uzywa humanize_slot (+/-15 min). Jeden przebieg
# zgodzilby sie przypadkiem - lekcja z testu meldunku z 03/08.
wczesniej = pozniej = 0
zle = None
for _ in range(200):
    off = random.randint(-15, 15)
    kolejka = SLOT + _dt.timedelta(minutes=off)
    wynik = G(SLOT, kolejka)
    if wynik < SLOT:
        zle = (off, wynik)
        break
    if off < 0:
        wczesniej += 1
    elif off > 0:
        pozniej += 1
check("200 losowan: ani razu godzina sprzed slotu planu", zle is None, repr(zle))
check("losowanie faktycznie schodzi ponizej slotu (inaczej test nie ma czego pilnowac)",
      wczesniej > 0, f"ponizej slotu: {wczesniej}")
check("losowanie faktycznie wychodzi powyzej slotu", pozniej > 0, f"powyzej slotu: {pozniej}")

print("\n[anty-regresja] zadna z DWOCH poprzednich wersji nie przechodzi tego testu:")
# Ta sekcja jest tu po to, zeby przyszla "uproszczajaca" poprawka od razu widziala,
# ze obie oczywiste jednolinijkowki byly juz probowane i obie sa polprawda.
stary = lambda s, r: s                    # do 03/08: zawsze slot planu   # noqa: E731
d5cd43e = lambda s, r: r or s             # 03/08: zawsze czas kolejki    # noqa: E731
pozno = _dt.datetime(2026, 8, 4, 16, 10, tzinfo=WARSAW)
wczesno = _dt.datetime(2026, 8, 4, 15, 49, tzinfo=WARSAW)
check("wersja sprzed 03/08 myli sie, gdy kolejka wypada POZNIEJ", stary(SLOT, pozno) != pozno)
check("wersja d5cd43e myli sie, gdy kolejka wypada WCZESNIEJ", d5cd43e(SLOT, wczesno) != SLOT)
check("obecna regula trafia w OBU przypadkach",
      G(SLOT, pozno) == pozno and G(SLOT, wczesno) == SLOT)

print("\n[sciezki puste] brak ktorejkolwiek liczby nie wysadza meldunku:")
check("brak czasu kolejki -> slot planu", G(SLOT, None) == SLOT)
check("brak slotu -> czas kolejki", G(None, pozno) == pozno)
check("brak obu -> None", G(None, None) is None)

print("\n[zrodlo] worker faktycznie uzywa reguly, a nie starej jednolinijkowki:")
src = (APP / "worker.py").read_text(encoding="utf-8")
check("meldunek liczy godzine przez _godzina_publikacji",
      "kiedy = _godzina_publikacji(slot, realny)" in src)
check("stara wersja 'realny or slot' znikla z petli", "kiedy = realny or slot" not in src)

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
