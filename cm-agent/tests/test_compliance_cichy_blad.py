"""Test: filtr jezykowy nie ma prawa paść po cichu (27/07, po nieudanym tap-tescie sekcji 23).

Tap-test sekcji 23 padl na braku klucza Anthropic (AP-306: jednorazowy `docker exec python -`
nie przechodzi przez worker._load_secrets). Sam blad byl moj, ale ODSLONIL rzecz gorsza:
`_rewrite` oddal tekst wejsciowy BAJT W BAJT, a jedynym sladem byl traceback w logach
kontenera. Na karcie taki tekst wyglada identycznie jak tekst, ktory bramke PRZESZEDL,
wiec czlowiek nie ma jak odroznic "poprawione" od "nie zadzialalo".

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_compliance_cichy_blad.py"""
import pathlib
import sys
import types

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

from app import compliance, db, tasks  # noqa: E402

FAILS = []
LOGI = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


db.execute = lambda sql, params=None: LOGI.append((sql, params))
db.fetchone = lambda sql, params=None: None
db.fetchall = lambda sql, params=None: []
tasks.model_for = lambda *a, **k: ("haiku", "low", "test")
tasks.log_task = lambda *a, **k: None

TEKST = "Zaadresujemy Państwa wyzwania w obszarze retencji w oparciu o najlepsze praktyki."


# ---------------- awaria filtru ----------------
print("\n[cichy blad] filtr, ktory padl, musi zostawic slad TAM, gdzie czlowiek patrzy:")


def _padnij():
    raise RuntimeError("Could not resolve authentication method")


compliance.client = lambda: _Any()
compliance.client = _padnij   # kazde wywolanie klienta wybucha

LOGI.clear()
wynik = compliance._rewrite("PROMPT", TEKST, None, task_name="test_szatni")

check("tekst wraca niezmieniony (degradacja, nie crash)", wynik == TEKST, wynik)
check("awaria trafia do agent_logs, nie tylko na stderr",
      any("agent_logs" in s for s, _ in LOGI), str(LOGI))
check("typ wpisu mowi wprost, ze filtr NIE zadzialal",
      any("COMPLIANCE_SKIPPED" in s for s, _ in LOGI), str(LOGI))
uzasadnienie = " ".join(str(p) for _, p in LOGI)
check("wpis nazywa filtr po imieniu", "test_szatni" in uzasadnienie, uzasadnienie[:200])
check("wpis mowi, ze tekst wyszedl NIEPOPRAWIONY", "NIEPOPRAWIONY" in uzasadnienie,
      uzasadnienie[:200])
check("wpis niesie rodzaj bledu", "RuntimeError" in uzasadnienie, uzasadnienie[:200])


# ---------------- awaria zapisu logu nie moze wywrocic filtru ----------------
def _tez_padnij(*a, **k):
    raise RuntimeError("baza tez nie odpowiada")


db.execute = _tez_padnij
wynik2 = compliance._rewrite("PROMPT", TEKST, None, task_name="polish_pl")
check("gdy nawet zapis logu padnie, filtr NADAL oddaje tekst zamiast wywracac przeplyw",
      wynik2 == TEKST, str(wynik2))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
