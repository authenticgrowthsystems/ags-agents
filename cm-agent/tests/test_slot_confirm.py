"""Test bramki potwierdzenia terminu (29/07/2026, decyzja Managera).

POWOD: 28/07 piec czesci jednego materialu wyszlo na X w PIEC MINUT, o 09:00, poza oknem
publikacji, na koncie ktore trzy dni wczesniej dostalo 403 za wykryta automatyzacje. Czlowiek
podal JEDEN termin i nie wiedzial, ze polecenie dotyczy PIECIU wpisow. Notatka po fakcie nie
miala czego zatrzymac.

WARUNEK (rozszerzony przez Managera): pytanie wyzwala sie, gdy termin jest POZA OKNEM **albo**
gdy polecenie dotyczy WIECEJ NIZ JEDNEGO wiersza. Dwa warunki NIEZALEZNE, nie koniunkcja.

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_slot_confirm.py"""
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

from app import conversation, db, decisions  # noqa: E402

FAILS = []
EXEC = []
ASKED = []
TG = []
STAN = {"wierszy": 1, "w_oknie": True}


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


MATERIAL = {"id": "m1", "master_theme": "Human-in-the-loop jako decyzja architektoniczna",
            "brand_id": "AGS", "target_channels": ["x"], "scheduled_for": None,
            "status": "approved"}


def _fetchone(sql, params=None):
    if "FROM content_items" in sql:
        return dict(MATERIAL)
    if "COUNT(*) AS n FROM post_queue" in sql:
        return {"n": STAN["wierszy"]}
    return None


db.fetchone = _fetchone
db.fetchall = lambda sql, params=None: []
db.execute = lambda sql, params=None: EXEC.append((sql, params))
decisions.ask = lambda *a, **k: ASKED.append({"typ": a[2], "pytanie": a[3], "opcje": a[4],
                                              "reko": k.get("recommendation"),
                                              "ctx": k.get("context")})
conversation._within_windows = lambda brand, chans, slot: STAN["w_oknie"]
conversation._tg = lambda m, p: TG.append(p.get("text", ""))

JUTRO = (_dt.datetime.now(WARSAW) + _dt.timedelta(days=1)).replace(hour=15, minute=7,
                                                                   second=0, microsecond=0)


def przesun(w_oknie=True, wierszy=1):
    STAN["w_oknie"], STAN["wierszy"] = w_oknie, wierszy
    EXEC.clear(); ASKED.clear(); TG.clear()
    return conversation._reschedule_material(
        {"theme_fragment": "Human-in-the-loop", "scheduled_for": JUTRO.isoformat()})


# ---------------- warunki wyzwalania ----------------
print("\n[warunek] dwa NIEZALEZNE powody, nie koniunkcja:")

odp = przesun(w_oknie=True, wierszy=1)
check("w oknie + jeden wiersz -> WYKONUJE bez pytania",
      not ASKED and any("content_items SET scheduled_for" in s for s, _ in EXEC), odp)

odp = przesun(w_oknie=False, wierszy=1)
check("POZA oknem + jeden wiersz -> PYTA", len(ASKED) == 1, odp)
check("poza oknem: nic nie zapisano przed odpowiedzia", not EXEC, str(EXEC))

odp = przesun(w_oknie=True, wierszy=5)
check("w oknie + PIEC wierszy -> PYTA", len(ASKED) == 1, odp)
check("wiele wierszy: nic nie zapisano przed odpowiedzia", not EXEC, str(EXEC))

odp = przesun(w_oknie=False, wierszy=5)
check("oba powody naraz -> PYTA raz", len(ASKED) == 1, odp)


# ---------------- karta niesie dowod ----------------
print("\n[karta] pytanie mowi, CO SIE STANIE, a nie tylko o co pyta:")
przesun(w_oknie=False, wierszy=5)
a = ASKED[0]
check("typ decyzji slot_confirm", a["typ"] == "slot_confirm", a["typ"])
check("karta podaje liczbe wpisow", "5 wpisow" in a["pytanie"], a["pytanie"])
check("karta ostrzega, ze wyjda JEDNA SERIA", "jedna seria" in a["pytanie"], a["pytanie"])
check("karta nazywa oba powody",
      "POZA oknem" in a["pytanie"] and "5 wpisow, nie jednego" in a["pytanie"], a["pytanie"])
check("karta podaje nowy termin", "15:07" in a["pytanie"], a["pytanie"])
check("BEZ rekomendacji (bramka bezpieczenstwa nie odpowiada sobie sama w semi-auto)",
      a["reko"] is None, str(a["reko"]))
check("kontekst niesie wszystko do wykonania",
      (a["ctx"] or {}).get("content_item_id") == "m1" and (a["ctx"] or {}).get("slot"),
      str(a["ctx"]))
check("dwa guziki", len(a["opcje"]) == 2, str(a["opcje"]))

przesun(w_oknie=True, wierszy=1)
przesun(w_oknie=True, wierszy=3)
check("przy jednym powodzie karta nie wymyśla drugiego",
      "POZA oknem" not in ASKED[0]["pytanie"], ASKED[0]["pytanie"])


# ---------------- guzik wykonuje to samo, co trasa bezposrednia ----------------
print("\n[guzik] potwierdzenie wykonuje, anulowanie zostawia bez zmian:")
CTX = {"context": {"content_item_id": "m1", "slot": JUTRO.isoformat(), "temat": "Human-in-the-loop",
                   "wierszy": 5, "poza_oknem": True}}

EXEC.clear(); TG.clear()
conversation.apply_slot_confirm(CTX, "tak", 1)
check("'Ustaw' zapisuje material", any("content_items SET scheduled_for" in s for s, _ in EXEC))
check("'Ustaw' zapisuje kolejke", any("post_queue SET scheduled_for" in s for s, _ in EXEC))
check("'Ustaw' etykietuje zrodlo jako rozmowa",
      any("slot_source='rozmowa'" in s for s, _ in EXEC), str(EXEC))
check("czlowiek dostaje potwierdzenie", any("Przesuniete" in t for t in TG), str(TG))

EXEC.clear(); TG.clear()
conversation.apply_slot_confirm(CTX, "nie", 1)
check("'Anuluj' NIC nie zapisuje", not EXEC, str(EXEC))
check("'Anuluj' mowi wprost, ze zostaje bez zmian",
      any("bez zmian" in t for t in TG), str(TG))

EXEC.clear()
conversation.apply_slot_confirm({"context": {}}, "tak", 1)
check("decyzja bez kontekstu nie robi nic", not EXEC, str(EXEC))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
