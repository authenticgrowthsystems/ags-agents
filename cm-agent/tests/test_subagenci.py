"""Testy wejscia do rozmowy z subagentami (audyt 24/07):
1) prefiks adresujacy 'x: ...' / 'li: ...' - kieruje wiadomosc BEZ zmiany aktywnego agenta,
2) meldunek dnia subagenta - tresc, badge i zaproszenie do odpowiedzi prefiksem.
Stdlib only, zero bazy, zero sieci, zero LLM.
Uruchomienie: python cm-agent/tests/test_subagenci.py"""
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

from app import conversation, proactive, reports, crm  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---------------- 1) prefiks adresujacy ----------------
print("\n[prefiks] adresowanie agenta bez zmiany slotu:")
PRZYPADKI = [
    ("x: pokaz kolejke", "subagent:AGS:x", "pokaz kolejke"),
    ("X: pokaz kolejke", "subagent:AGS:x", "pokaz kolejke"),
    ("li: co dzis poszlo?", "subagent:AGS:linkedin", "co dzis poszlo?"),
    ("linkedin: raport", "subagent:AGS:linkedin", "raport"),
    ("cm: przesun material na jutro", "cm", "przesun material na jutro"),
    ("sprzedaz: pokaz lejek", "subagent:AGS:sprzedaz", "pokaz lejek"),
    ("x:   dwie spacje po dwukropku", "subagent:AGS:x", "dwie spacje po dwukropku"),
]
for tekst, oczek_agent, oczek_tresc in PRZYPADKI:
    m = conversation._PREFIKS_AGENTA_RE.match(tekst)
    agent = conversation._PREFIKS_AGENCI.get(m.group(1).lower()) if m else None
    tresc = (m.group(2) or "").strip() if m else None
    check(f"'{tekst[:32]}' -> {oczek_agent}", agent == oczek_agent and tresc == oczek_tresc,
          (agent, tresc))

print("\n[prefiks] NIE lapiemy zwyklych zdan:")
NIETYKALNE = ["cm ma racje, przesuwamy", "x jest za drogi", "napisz do klienta: dzien dobry",
              "godzina 15: publikacja", "li", "x:"]
for tekst in NIETYKALNE:
    m = conversation._PREFIKS_AGENTA_RE.match(tekst)
    trafiony = bool(m) and conversation._PREFIKS_AGENCI.get(m.group(1).lower())
    check(f"'{tekst[:32]}' nie zmienia adresata", not trafiony, m.group(0) if m else None)


# ---------------- 2) meldunek dnia ----------------
print("\n[meldunek] tresc, badge i zaproszenie prefiksem:")
proactive.BRIEF_WINDOW = (0, 0, 23, 59)          # test nie czeka na wieczor
WYSLANE = []
proactive._send = lambda text, kb=None: (WYSLANE.append(text), True)[1]
proactive._state_get = lambda key: {}
proactive._state_set = lambda key, obj: None
proactive.db.fetchall = lambda sql, p=None: (
    [{"channel": "x"}, {"channel": "linkedin"}] if "FROM channels" in sql
    else [{"content": "Retry without idempotency is not resilience.",
           "engagement_metrics": {"impressions": 66}}] if "published_posts" in sql
    else [])
reports._queue_upcoming = lambda brand, ch, limit=10: [
    {"id": 1, "status": "review", "content": "Tekst w kolejce",
     "scheduled_for": _dt.datetime(2026, 7, 25, 14, 10, tzinfo=_dt.timezone.utc)}]
crm.pending_text = lambda brand, ch: "PROPOZYCJE BEZ DECYZJI:\n- 24/07 20:00 @ktos"

proactive.subagent_briefs("AGS")
check("meldunek poszedl dla obu kanalow", len(WYSLANE) == 2, len(WYSLANE))
if len(WYSLANE) == 2:
    x_txt, li_txt = WYSLANE
    check("badge X w naglowku", x_txt.startswith("🐦 X MELDUNEK DNIA"), x_txt[:40])
    check("badge LinkedIn w naglowku", li_txt.startswith("🔗 LinkedIn MELDUNEK DNIA"), li_txt[:40])
    check("meldunek mowi CO POSZLO", "Poszlo: 1 publikacja" in x_txt, x_txt)
    check("meldunek niesie metryki", "impressions" in x_txt or "66" in x_txt, x_txt)
    check("meldunek mowi CO CZEKA", "Czeka: 1 w kolejce" in x_txt, x_txt)
    check("meldunek mowi CZEGO POTRZEBA", "Potrzebuje decyzji:" in x_txt, x_txt)
    check("zaproszenie prefiksem dla X", "`x: <tresc>`" in x_txt, x_txt[-120:])
    check("zaproszenie prefiksem dla LinkedIn", "`li: <tresc>`" in li_txt, li_txt[-120:])
    check("meldunek NIE jest dluzszy niz 4000 znakow", all(len(t) <= 4000 for t in WYSLANE))

print("\n[meldunek] pusta kolejka nazwana wprost:")
WYSLANE.clear()
reports._queue_upcoming = lambda brand, ch, limit=10: []
proactive.db.fetchall = lambda sql, p=None: (
    [{"channel": "x"}] if "FROM channels" in sql else [])
crm.pending_text = lambda brand, ch: "Nic nie wisi - wszystkie propozycje rozstrzygniete."
proactive.subagent_briefs("AGS")
check("brak publikacji nazwany wprost", "Poszlo: nic" in WYSLANE[0], WYSLANE[0])
check("pusta kolejka = luka, nie sukces", "to jest luka, nie sukces" in WYSLANE[0], WYSLANE[0])
check("brak wiszacych decyzji tez jest powiedziany",
      "Potrzebuje decyzji: nic." in WYSLANE[0], WYSLANE[0])

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
