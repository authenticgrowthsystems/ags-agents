"""Test straznika przypomnien po odglodzeniu (26/07/2026, sekcja 4.5 diagnozy).

Wada: `LIMIT 5` stal PRZED odsiewem wierszy z otwarta bramka, a odsiew robil sie dopiero
w Pythonie. Kazdy zablokowany wiersz zjadal slot i nie generowal niczego, wiec organ
zamieral. Dowod produkcyjny (sonda C, 26/07): siedem wierszy StandART, piec najstarszych
z bramkami #152-156 - zero przypomnien dla czegokolwiek, takze dla komentarzy i DM.

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_straznik_przypomnien.py"""
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

from app import engagement, db, decisions  # noqa: E402

FAILS = []
SQL = []
ASKED = []
ROWS = {"proposed": [], "tasks": []}


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _fetchall(sql, params=None):
    SQL.append(sql)
    if "FROM engagement_log" in sql:
        return list(ROWS["proposed"])
    if "FROM task_queue" in sql:
        return list(ROWS["tasks"])
    return []


db.fetchall = _fetchall
db.fetchone = lambda sql, params=None: None   # zaden wiersz nie ma bramki w drugim pasie
db.execute = lambda *a, **k: None
decisions.ask = lambda *a, **k: ASKED.append({"agent": a[0], "typ": a[2], "ctx": k.get("context")})


def _pozycja(sql, igla):
    return sql.find(igla)


# ---------------- odsiew przed limitem ----------------
print("\n[4.5] odsiew stoi PRZED limitem, nie po nim:")
ROWS["proposed"] = []
ROWS["tasks"] = []
SQL.clear()
engagement._watch_proposed()
sql_prop = SQL[-1]
check("propozycje: odsiew jest w SQL", "NOT EXISTS" in sql_prop, sql_prop)
check("propozycje: odsiew PRZED LIMIT-em",
      0 < _pozycja(sql_prop, "NOT EXISTS") < _pozycja(sql_prop, "LIMIT"),
      "to jest cala wada: LIMIT przed odsiewem zaglodzil organ")
check("propozycje: odsiew obejmuje OBA typy bramek",
      "stale_comment" in sql_prop and "stale_outreach" in sql_prop, sql_prop)
check("propozycje: bramka swieza (24h) tez blokuje",
      "answered_at" in sql_prop and "24 hours" in sql_prop, sql_prop)

SQL.clear()
engagement._watch_in_progress()
sql_task = SQL[-1]
check("zadania: odsiew jest w SQL (AP-309, drugie wystapienie)", "NOT EXISTS" in sql_task, sql_task)
check("zadania: odsiew PRZED LIMIT-em",
      0 < _pozycja(sql_task, "NOT EXISTS") < _pozycja(sql_task, "LIMIT"), sql_task)
check("zadania: klucz to task_id", "task_id" in sql_task, sql_task)


# ---------------- wiersze, ktore przeszly odsiew, generuja pytanie ----------------
print("\n[4.5] wiersz bez bramki dostaje przypomnienie wlasciwego rodzaju:")
ASKED.clear()
ROWS["proposed"] = [
    {"id": "e1", "agent": "AGS:sprzedaz", "author_display": "Klub Sportowy StandART"},
    {"id": "e2", "agent": "AGS:x", "author_display": "@ktos"},
]
engagement._watch_proposed()
typy = {a["agent"]: a["typ"] for a in ASKED}
check("gotowiec sprzedazy pyta jako stale_outreach",
      typy.get("AGS:sprzedaz") == "stale_outreach", str(typy))
check("propozycja komentarza pyta jako stale_comment",
      typy.get("AGS:x") == "stale_comment", str(typy))
check("oba wiersze obsluzone w jednym przebiegu", len(ASKED) == 2, str(len(ASKED)))
check("kazde pytanie niesie identyfikator wiersza",
      all((a["ctx"] or {}).get("engagement_id") for a in ASKED), str(ASKED))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
