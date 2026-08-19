# -*- coding: utf-8 -*-
"""Test D-022 (19/08/2026): kanal WYLACZONY mowi, ze jest wylaczony; tryb NIEZNANY nie milczy.

SPROSTOWANIE DO OPISU DLUGU, ZROBIONE ODCZYTEM. Wpis mowil, ze wartosc `publish_mode='none'`
"przechodzi przez cala funkcje i nie dzieje sie nic - bez wyjatku, bez wpisu w dzienniku, bez
sladu". Odczyt `channels.dispatch_item` pokazal co innego: galaz `else` NIE jest galezia trybu
'draft', tylko lapaczem wszystkiego, wiec `none` konczylo na `status='held'`. Skutek byl GORSZY
niz cisza - `worker._send_manual_paste_kits` przysylal Tomaszowi pelna tresc z poleceniem
"wklej recznie", czyli system prosil o reczna publikacje na kanale ustawionym jako niepublikujacy.

CZEGO TEN TEST PILNUJE - TRZECH SCIEZEK, W TYM DWOCH ALARMOWYCH:
  1. tryb WYLACZONY ('none'): wiersz nie idzie do publikacji, dostaje stan terminalny i zostawia
     slad; NIE konczy na 'held', bo 'held' oznacza gotowiec do recznej wklejki;
  2. tryb NIEZNANY (literowka, tryb z przyszlosci): NIE MILCZY i NIE zamienia sie po cichu
     w tryb reczny; wiersz zostaje nietkniety, zeby dalo sie go uratowac poprawka ustawienia;
  3. tryby zwykle ('post_queue', 'draft', 'webhook'): przechodza dokladnie jak przed zmiana -
     to jest regresja, ktora przy dokladaniu galezi najlatwiej narobic.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_tryb_publikacji_wylaczony.py"""
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

from app import channels, config, db, logbot, worker  # noqa: E402

ZAPISY = []      # kazdy UPDATE/INSERT, ktory dispatch wykonal
MELDUNKI = []    # kazda wiadomosc na kanal logowy
DELEGACJE = []   # kazde zlecenie do subagenta
WIERSZ = {"r": None}

MATERIAL = {"id": "m-1", "brand_id": "AGS", "master_theme": "Granica miedzy dwoma agentami"}


def _execute(sql, params=None):
    ZAPISY.append((" ".join(str(sql).split()), params))


def _fetchall(sql, params=None):
    return [WIERSZ["r"]] if "post_queue pq JOIN channels" in " ".join(str(sql).split()) else []


db.execute = _execute
db.fetchall = _fetchall
db.fetchone = lambda sql, params=None: None
logbot.send = lambda tekst, silent=False: MELDUNKI.append(tekst)
channels._delegate = lambda item, r: DELEGACJE.append(r["id"])
channels._auto_obraz_wlaczony = lambda brand_id, platform: False


def dispatch(tryb, platform="sprzedaz", adapter_path=None, content="tresc"):
    ZAPISY.clear()
    MELDUNKI.clear()
    DELEGACJE.clear()
    WIERSZ["r"] = {"id": 501, "platform": platform, "content": content, "media": [],
                   "config": {"publish_mode": tryb} if tryb is not None else {},
                   "adapter_path": adapter_path}
    return channels.dispatch_item(dict(MATERIAL))


def nowe_statusy():
    return [p for (p, _) in ZAPISY if "UPDATE post_queue" in p]


def teksty_meldunkow():
    return "\n".join(MELDUNKI)


print("\n[stala] tryb wylaczony ma NAZWE, a lista znanych trybow jest jedna:")
check("config zna PUBLISH_NONE", getattr(config, "PUBLISH_NONE", None) == "none")
check("'none' jest na liscie trybow znanych", config.tryb_publikacji_znany("none"))
check("literowka NIE jest trybem znanym", not config.tryb_publikacji_znany("post-queue"))
check("pusta wartosc NIE jest trybem znanym", not config.tryb_publikacji_znany(""))

print("\n[ALARM 1] kanal WYLACZONY ('none'): pomija publikacje i zostawia slad:")
h = dispatch("none")
check("nie ma delegacji do subagenta", DELEGACJE == [], str(DELEGACJE))
check("wiersz NIE konczy na 'held' (to jest gotowiec do wklejki)",
      not any("status='held'" in p for p in nowe_statusy()), str(nowe_statusy()))
check("wiersz dostaje stan terminalny 'rejected'",
      any("status='rejected'" in p for p in nowe_statusy()), str(nowe_statusy()))
check("jest wpis w dzienniku agent_logs",
      any("INSERT INTO agent_logs" in p for (p, _) in ZAPISY), str([p[:40] for (p, _) in ZAPISY]))
check("czlowiek dostaje paragon", len(MELDUNKI) == 1, str(len(MELDUNKI)))
check("paragon mowi WPROST, ze kanal jest wylaczony",
      "KANAL WYLACZONY" in teksty_meldunkow(), teksty_meldunkow()[:120])
check("paragon mowi, ze to NIE awaria", "NIE jest awaria" in teksty_meldunkow(), teksty_meldunkow()[:200])
check("paragon podaje, czym to odkrecic",
      "post_queue" in teksty_meldunkow() and "draft" in teksty_meldunkow())
print("       meldunek:\n       " + teksty_meldunkow().replace("\n", "\n       "))

print("\n[ALARM 2] tryb NIEZNANY: nie milczy i nie zamienia sie po cichu w tryb reczny:")
h = dispatch("post-queue")   # literowka, ktora do 19/08 stawala sie trybem recznym
check("czlowiek dostaje meldunek", len(MELDUNKI) == 1, str(len(MELDUNKI)))
check("meldunek mowi, ze CM nie wie, jak to opublikowac",
      "NIE WIEM, JAK OPUBLIKOWAC" in teksty_meldunkow(), teksty_meldunkow()[:120])
check("meldunek podaje DOSLOWNIE wartosc, ktorej nie zna",
      "post-queue" in teksty_meldunkow(), teksty_meldunkow()[:200])
check("wiersz NIE zostaje przestawiony na nic", nowe_statusy() == [], str(nowe_statusy()))
check("wpis w dzienniku ma poziom 'error'",
      any("INSERT INTO agent_logs" in p and params and params[0] == "error"
          for (p, params) in ZAPISY), str(ZAPISY))
check("nie ma delegacji do subagenta", DELEGACJE == [], str(DELEGACJE))
print("       meldunek:\n       " + teksty_meldunkow().replace("\n", "\n       "))

print("\n[REGRESJA] tryby zwykle przechodza dokladnie jak przedtem:")
dispatch("post_queue")
check("post_queue -> wiersz 'scheduled'",
      any("status='scheduled'" in p for p in nowe_statusy()), str(nowe_statusy()))
check("post_queue nie zawraca glowy meldunkiem o trybie", MELDUNKI == [], teksty_meldunkow())

dispatch("draft")
check("draft -> wiersz 'held' (gotowiec do wklejki)",
      any("status='held'" in p for p in nowe_statusy()), str(nowe_statusy()))
check("draft nie zawraca glowy meldunkiem o trybie", MELDUNKI == [], teksty_meldunkow())

dispatch(None)   # BRAK klucza publish_mode - domyslka config.PUBLISH_DRAFT, jak przed zmiana
check("brak klucza dalej wpada w domyslke 'draft'",
      any("status='held'" in p for p in nowe_statusy()), str(nowe_statusy()))
check("brak klucza nie jest traktowany jak tryb nieznany", MELDUNKI == [], teksty_meldunkow())

dispatch("webhook", platform="x", adapter_path="/x/publish")
check("webhook z adapterem -> delegacja do subagenta", DELEGACJE == [501], str(DELEGACJE))
check("webhook nie zawraca glowy meldunkiem o trybie", MELDUNKI == [], teksty_meldunkow())

dispatch("webhook", platform="x", adapter_path=None)
check("webhook BEZ adaptera dalej spada na 'held' (bez zmiany zachowania)",
      any("status='held'" in p for p in nowe_statusy()), str(nowe_statusy()))

print("\n[meldunek dispatchu] paragon zbiorczy tez mowi prawde o obu trybach:")
ack_none = worker._dispatch_ack(dict(MATERIAL), [{"platform": "sprzedaz", "mode": "none", "queue_id": 501}])
check("dla wylaczonego NIE prosi o reczne wklejenie",
      "reczne wklejenie" not in ack_none, ack_none)
check("dla wylaczonego mowi, ze nic nie poszlo",
      "WYLACZONY" in ack_none and "nic tam nie poszlo" in ack_none, ack_none)
ack_zly = worker._dispatch_ack(dict(MATERIAL), [{"platform": "x", "mode": "post-queue", "queue_id": 502}])
check("dla nieznanego mowi WSTRZYMANE i podaje wartosc",
      "WSTRZYMANE" in ack_zly and "post-queue" in ack_zly, ack_zly)

print("\n[anty-regresja] galezie stoja PRZED lapaczem, nie za nim:")
src = (APP / "channels.py").read_text(encoding="utf-8")
i_none = src.find("if mode == config.PUBLISH_NONE:")
i_nieznany = src.find("elif not config.tryb_publikacji_znany(mode):")
i_else = src.find("            db.execute(\"UPDATE post_queue SET status='held' WHERE id=%s\"")
check("galaz trybu wylaczonego istnieje", i_none > 0)
check("galaz trybu nieznanego istnieje", i_nieznany > 0)
check("obie stoja przed galezia zbiorcza", 0 < i_none < i_nieznany < i_else,
      f"{i_none}/{i_nieznany}/{i_else}")

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
