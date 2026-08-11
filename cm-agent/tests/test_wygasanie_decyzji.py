# -*- coding: utf-8 -*-
"""Test (11/08/2026): straznik `stale_approval` ZAMYKA karty, zanim otworzy nowe.

DOWOD, KTORY GO ZAMOWIL. Odczyt produkcji 11/08, godzine po publikacji:

    kart 'pending': 15  |  MARTWE (material poszedl dalej): 15  |  ZYWE: 0

Jedenascie materialow odrzuconych, cztery OPUBLIKOWANE - w tym ten opublikowany godzine
wczesniej ("Granica miedzy dwoma agentami", karta #173, wisiala 14 dni). Lista "otwartych
decyzji" pokazywala czternascie pozycji czekajacych na czlowieka, a czekala **zero**.

Przyczyna: `worker._stale_approval_watch` zakladal karty i NIC ich nigdy nie zamykalo.
Material szedl dalej swoja sciezka, wpis w rejestrze stal nietkniety. To AP-311 od strony
ZAPISU: wpis czytany jako fakt o swiecie, gdy jest tylko faktem o rejestrze.

DLACZEGO `expired`, A NIE `answered`: Tomasz nie odpowiedzial. Nie `auto`: system nie zdecydowal.
Pytanie przestalo byc pytaniem - i slownik `agent_decisions.status` ma na to dokladnie te wartosc
od DDL 024, tylko nikt jej nie uzywal.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314): kolejnosci. Zamkniecie MUSI isc PRZED otwieraniem,
inaczej straznik w tym samym przebiegu zamyka karte i zaklada ja od nowa. Oraz tego, ze
**material nadal czekajacy NIE jest wygaszany** - bo to zabiloby jedyna rzecz, ktora ten
straznik ma robic.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_wygasanie_decyzji.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
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

from app import worker, db, decisions  # noqa: E402

# ---------------------------------------------------------------- podstawka
KOLEJNOSC = []      # co po czym sie wydarzylo - sedno tego testu
ZAPISY = []
PYTANIA = []
WYGASLE = [{"id": 163}, {"id": 173}]      # karty, ktorych material poszedl dalej
CZEKAJACE = [{"id": "aaaa", "brand_id": "AGS", "master_theme": "Material nadal czeka"}]


def _fetchall(sql, params=None):
    s = " ".join((sql or "").split())
    if "FROM agent_decisions d" in s:
        KOLEJNOSC.append("szukam wygaslych")
        return list(WYGASLE)
    if "FROM content_items WHERE status='needs_approval'" in s:
        KOLEJNOSC.append("szukam czekajacych")
        return list(CZEKAJACE)
    return []


def _fetchone(sql, params=None):
    return None      # brak throttlingu - kazdy czekajacy dostaje karte


def _execute(sql, params=None):
    s = " ".join((sql or "").split())
    ZAPISY.append((s, params))
    if "UPDATE agent_decisions SET status='expired'" in s:
        KOLEJNOSC.append("wygaszam")


db.fetchall = _fetchall
db.fetchone = _fetchone
db.execute = _execute
decisions.ask = lambda *a, **k: (KOLEJNOSC.append("zakladam karte"), PYTANIA.append(a))[0]

worker._stale_approval_watch()

print("\n[sedno] zamkniecie idzie PRZED otwieraniem:")
check("wygaszanie w ogole zaszlo", "wygaszam" in KOLEJNOSC, repr(KOLEJNOSC))
check("nowa karta w ogole powstala", "zakladam karte" in KOLEJNOSC, repr(KOLEJNOSC))
check("KOLEJNOSC zdarzen: wygaszam PRZED zakladam",
      KOLEJNOSC.index("wygaszam") < KOLEJNOSC.index("zakladam karte"), repr(KOLEJNOSC))
# Asercja na zdarzeniach NIE WYSTARCZA i zostalo to zmierzone celowa wada 11/08: gdy blok
# wygaszania wjedzie DO PETLI po materialach, sekwencja zdarzen nadal wyglada poprawnie
# (wygaszam, potem zakladam), a kod odpala zapytanie raz na material zamiast raz na przebieg.
# Dlatego druga asercja pyta o KOLEJNOSC W ZRODLE, nie o kolejnosc zdarzen.
# Szukamy WYLACZNIE w ciele tej jednej funkcji. Pierwsza wersja pytala o `for item in rows:`
# w calym pliku i trafiala w INNA funkcje kilkanascie kilobajtow wyzej - czyli asercja padala
# na zdrowym kodzie. Dopasowanie po frazie, ktora nie jest unikalna, to ta sama klasa bledu,
# ktora ten projekt zbiera od AP-309.
_plik = (APP / "worker.py").read_text(encoding="utf-8")
_od = _plik.find("def _stale_approval_watch")
_do = _plik.find("\ndef ", _od + 10)
_fn = _plik[_od:_do if _do > 0 else len(_plik)]
_i_wyg = _fn.find("wygasle = db.fetchall(")
_i_row = _fn.find("SELECT id, brand_id, master_theme FROM content_items")
_i_for = _fn.find("for item in rows:")
check("ciało funkcji zostalo znalezione", _od >= 0 and len(_fn) > 200, f"dlugosc {len(_fn)}")
check("KOLEJNOSC W ZRODLE: wygaszanie PRZED pobraniem czekajacych i PRZED petla",
      0 < _i_wyg < _i_row < _i_for, f"wygaszanie@{_i_wyg} czekajace@{_i_row} petla@{_i_for}")
# Zagniezdzenie mierzymy WCIECIEM, nie liczeniem slowa "for". Pierwsza wersja liczyla wystapienia
# "for " miedzy blokiem a petla i padala na ZDROWYM kodzie, bo w bloku stoi wyrazenie listowe
# `[r["id"] for r in wygasle]`. Liczylem slowo, a mierzyc chcialem poziom zagniezdzenia.
_linia_wyg = next(l for l in _fn.splitlines() if "wygasle = db.fetchall(" in l)
check("wygaszanie POZA petla - wciecie 4 spacje, czyli cialo funkcji",
      len(_linia_wyg) - len(_linia_wyg.lstrip()) == 4,
      f"wciecie {len(_linia_wyg) - len(_linia_wyg.lstrip())} spacji - blok wjechal do petli")

print("\n[zapis] wygaszenie uzywa wartosci ze slownika DDL 024:")
upd = [z for z in ZAPISY if "UPDATE agent_decisions" in z[0]]
check("byl dokladnie jeden UPDATE", len(upd) == 1, repr(upd))
check("status='expired', nie 'answered'",
      "status='expired'" in upd[0][0] and "answered'" not in upd[0][0].replace("answered_at", ""),
      upd[0][0])
check("ustawia answered_at", "answered_at=NOW()" in upd[0][0], upd[0][0])
check("dotyka DOKLADNIE znalezionych kart", upd[0][1] == ([163, 173],), repr(upd[0][1]))

print("\n[bezpieczenstwo] material NADAL czekajacy nie jest wygaszany:")
src = (APP / "worker.py").read_text(encoding="utf-8")
check("warunek pyta o status ROZNY od needs_approval",
      "ci.status <> 'needs_approval'" in src, "brak warunku - wygaszalby wszystko")
check("bierze tylko karty 'pending'", "d.status='pending'" in src)
check("i tylko typ stale_approval", "d.decision_type='stale_approval'" in src)

print("\n[odpornosc] zly content_item_id nie wywraca straznika:")
check("jest bramka na ksztalt uuid",
      "~ '^[0-9a-fA-F-]{36}$'" in src,
      "bez niej ::uuid rzuca wyjatkiem na jednym zlym wpisie i straznik pada CALY")

print("\n[cisza] wygaszenie nie zawraca glowy czlowiekowi:")
i = src.find("def _stale_approval_watch")
blok = src[i:i + 2000]
check("jest slad w logu kontenera", "print(f\"[cm] wygaszone karty" in blok)
check("NIE ma powiadomienia na kanal logowy",
      "logbot" not in blok,
      "sprzatanie po sobie to nie zdarzenie warte przerywania dnia")

print("\n[brak roboty] gdy nie ma czego wygasic, nie ma UPDATE:")
KOLEJNOSC.clear(); ZAPISY.clear(); WYGASLE.clear()
worker._stale_approval_watch()
check("zero UPDATE-ow agent_decisions",
      not [z for z in ZAPISY if "UPDATE agent_decisions" in z[0]], repr(ZAPISY))
check("ale karty nadal sie zakladaja", "zakladam karte" in KOLEJNOSC, repr(KOLEJNOSC))

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
