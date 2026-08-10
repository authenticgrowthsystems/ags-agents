# -*- coding: utf-8 -*-
"""Test (10/08/2026, zgloszenie Tomasza): meldunek rozroznia "system nie publikowal"
od "nic nie wyszlo", a publikacja spoza systemu ma droge zapisu.

DOWOD, KTORY GO ZAMOWIL. Meldunek dnia powiedzial **"Poszlo: nic w ostatnich 24h"** w dniu,
w ktorym wyszly DWA artykuly opublikowane recznie. Zdanie bylo prawdziwe o SYSTEMIE i falszywe
o SWIECIE - klasyczne AP-312. Ksiega `published_posts` nie ma jak dowiedziec sie o publikacji,
ktora ja ominela, wiec brak WLASNEGO dzialania byl meldowany jako brak dzialania W OGOLE.

DWIE RZECZY NAPRAWIONE NARAZ, bo osobno kazda jest polowiczna:
  1. meldunek nazywa CZYJE dzialanie liczy ("System opublikowal" / "System nie publikowal"),
     a publikacje odnotowane recznie pokazuje w osobnej linii;
  2. `wyszlo <kanal> <link> [temat]` daje droge zapisu dla publikacji spoza systemu.
Bez (2) meldunek bylby uczciwy, ale nadal slepy. Bez (1) zapis nie mialby gdzie sie pokazac.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314): nie tego, ze funkcje istnieja, tylko ze OBIE
BRAMKI trasy zapisu odmawiaja - literowka w nazwie kanalu i ten sam link drugi raz. Wpis
do ksiegi z nieistniejacym kanalem jest cichym smieciem: zaden raport go nie pokaze, bo raporty
chodza po kanalach z tabeli `channels`.

Stdlib only. Uruchomienie: python cm-agent/tests/test_publikacja_reczna.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:   # maszyna bez tzdata - te same podstawienie co w pozostalych testach
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)

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

from app import conversation, db  # noqa: E402

# ---------------------------------------------------------------- podstawka bazy
KANALY = {("AGS", "linkedin"), ("AGS", "x")}
KSIEGA = {}          # url -> {"id":..., "published_at":...}
ZAPISY = []          # (sql, params) z INSERT-ow


def _fetchone(sql, params=None):
    s = " ".join((sql or "").split())
    if "FROM channels WHERE brand_id" in s:
        return {"?column?": 1} if (params[0], params[1]) in KANALY else None
    if "FROM published_posts WHERE post_url" in s:
        return KSIEGA.get(params[0])
    if s.startswith("INSERT INTO published_posts"):
        ZAPISY.append((s, params))
        KSIEGA[params[3]] = {"id": 900 + len(ZAPISY), "published_at": "2026-08-10 21:30:00"}
        return {"id": 900 + len(ZAPISY)}
    return None


def _fetchall(sql, params=None):
    s = " ".join((sql or "").split())
    if "SELECT channel FROM channels" in s:
        return [{"channel": c} for (b, c) in sorted(KANALY) if b == params[0]]
    return []


db.fetchone = _fetchone
db.fetchall = _fetchall

print("\n[zapis] publikacja spoza systemu trafia do ksiegi:")
odp = conversation._wyszlo_route("wyszlo linkedin https://www.linkedin.com/feed/update/urn:li:share:111")
check("trasa rozpoznaje polecenie", odp is not None and "Odnotowane" in odp, repr(odp))
check("byl dokladnie jeden zapis", len(ZAPISY) == 1, repr(ZAPISY))
_sql, _p = ZAPISY[0]
check("zapisany kanal to linkedin", _p[0] == "linkedin", repr(_p))
check("zapisana marka to AGS", _p[1] == "AGS", repr(_p))
check("zrodlo to manual_external", "manual_external" in _sql, _sql[:160])
check("tresc zostaje PUSTA (nie zgadujemy jej z linku)", "VALUES (%s,%s,'',%s,%s,''" in _sql,
      _sql[:200])
check("paragon mowi, ze czas zapisano jako TERAZ", "TERAZ" in odp, repr(odp))

print("\n[BRAMKA 1] literowka w nazwie kanalu NIE tworzy cichego smiecia:")
przed = len(ZAPISY)
odp = conversation._wyszlo_route("wyszlo linkedln https://example.com/a")
check("odmowa, nie zapis", odp is not None and "Nic nie zapisalem" in odp, repr(odp))
check("nic nie doszlo do ksiegi", len(ZAPISY) == przed, repr(ZAPISY))
check("odpowiedz WYMIENIA znane kanaly", "linkedin" in odp and "x" in odp, repr(odp))

print("\n[BRAMKA 2] ten sam link drugi raz nie dubluje statystyk:")
przed = len(ZAPISY)
odp = conversation._wyszlo_route("wyszlo linkedin https://www.linkedin.com/feed/update/urn:li:share:111")
check("odmowa z numerem istniejacego wpisu", odp is not None and "juz jest w ksiedze" in odp,
      repr(odp))
check("nic nie doszlo do ksiegi", len(ZAPISY) == przed, repr(ZAPISY))

print("\n[warianty zapisu] rozne formy polecenia i marka jawna:")
for fraza, oczek_kanal, oczek_marka in (
        ("wyszlo x https://x.com/i/web/status/222", "x", "AGS"),
        ("opublikowane linkedin https://li.example/3", "linkedin", "AGS"),
        ("wyszlo AGS:x https://x.com/i/web/status/444", "x", "AGS")):
    przed = len(ZAPISY)
    odp = conversation._wyszlo_route(fraza)
    ok = len(ZAPISY) == przed + 1 and ZAPISY[-1][1][0] == oczek_kanal and ZAPISY[-1][1][1] == oczek_marka
    check(f"'{fraza[:34]}...' zapisane jako {oczek_marka}:{oczek_kanal}", ok,
          repr(ZAPISY[-1][1] if ZAPISY else None))

print("\n[temat] ogon polecenia laduje w kolumnie temat:")
przed = len(ZAPISY)
conversation._wyszlo_route("wyszlo linkedin https://li.example/9 granica miedzy agentami")
check("temat zapisany", ZAPISY[-1][1][2] == "granica miedzy agentami", repr(ZAPISY[-1][1]))

print("\n[nie lapie za duzo] zwykla rozmowa NIE jest poleceniem zapisu:")
for zdanie in ("wyszlo dobrze", "co wyszlo wczoraj?", "opublikowane materialy sa w kolejce",
               "wyszlo linkedin bez linku"):
    check(f"'{zdanie}' idzie do LLM, nie do zapisu",
          conversation._wyszlo_route(zdanie) is None, repr(conversation._wyszlo_route(zdanie)))

print("\n[meldunek] zdanie mowi, CZYJE dzialanie liczy:")
src = (APP / "proactive.py").read_text(encoding="utf-8")
# Sprawdzamy WYSYLANE linie, nie caly plik: slowo "Poszlo" zostaje w komentarzu, ktory cytuje
# stara tresc, i ma tam zostac - bez niego za miesiac nikt nie odtworzy, co i dlaczego zmieniono.
wysylane = [l for l in src.splitlines() if "lines.append" in l]
check("zadna WYSYLANA linia nie mowi juz 'Poszlo'",
      not any("Poszlo" in l for l in wysylane),
      repr([l.strip()[:70] for l in wysylane if "Poszlo" in l]))
check("stara tresc zostaje w komentarzu jako slad zmiany", "Poszlo: nic w ostatnich 24h" in src)
check("meldunek mowi 'System nie publikowal'", "System nie publikowal nic w ostatnich 24h" in src)
check("wersja pozytywna tez nazywa sprawce", "System opublikowal:" in src)
check("publikacje reczne maja wlasna linie", "Recznie odnotowane:" in src)
check("przy pustej ksiedze meldunek PODPOWIADA droge zapisu", "wyszlo <kanal> <link>" in src)

print("\n[meldunek] rozdzial liczony po zrodle, nie po czymkolwiek innym:")
check("zapytanie czyta metadata->>'source'", "metadata->>'source'" in src)
check("publikacje systemu to te BEZ prefiksu manual",
      'if not str(p.get("zrodlo") or "").startswith("manual")' in src)
check("publikacje reczne to te Z prefiksem manual",
      'if str(p.get("zrodlo") or "").startswith("manual")' in src)

print("\n[podlaczenie] trasa jest wpieta PRZED LLM:")
csrc = (APP / "conversation.py").read_text(encoding="utf-8")
i_route = csrc.find("def _config_route")
blok = csrc[i_route:i_route + 400]
check("_config_route wola _wyszlo_route", "_wyszlo_route(text)" in blok, blok[:200])

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
