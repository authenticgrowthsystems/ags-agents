"""Test wpiecia Voice Bible v2.2 sekcja 23 (test szatni). LLM (Haiku) jest stubowany, wiec
sprawdzamy BRAMKI i ROUTING, nie sama tresc przepisania:
- test_szatni na EN nie rusza LLM (gate looks_polish),
- test_szatni na PL wola LLM i nie wywraca przy bledzie (fallback = tekst),
- enforce wola test_szatni TYLKO dla marek PL (TNM/RDC), nie dla AGS.
Stdlib only. Uruchomienie: python cm-agent/tests/test_voice_v22.py"""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

psycopg = types.ModuleType("psycopg")
psycopg_types = types.ModuleType("psycopg.types")
psycopg_json = types.ModuleType("psycopg.types.json")
psycopg_json.Jsonb = lambda o: o
psycopg.types = psycopg_types
psycopg_types.json = psycopg_json
sys.modules["psycopg"] = psycopg
sys.modules["psycopg.types"] = psycopg_types
sys.modules["psycopg.types.json"] = psycopg_json

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

fake_config = types.ModuleType("app.config")
sys.modules["app.config"] = fake_config
fake_db = types.ModuleType("app.db")
fake_db.fetchone = lambda *a, **k: None
fake_db.execute = lambda *a, **k: None
sys.modules["app.db"] = fake_db

# licznik wywolan LLM - test szatni ma nie ruszac go dla EN
LLM = {"calls": 0}
fake_tasks = types.ModuleType("app.tasks")
fake_tasks.model_for = lambda k: ("stub-model", "haiku", "test")
fake_tasks.log_task = lambda *a, **k: None
sys.modules["app.tasks"] = fake_tasks


def _client():
    LLM["calls"] += 1
    raise RuntimeError("LLM niedostepny w tescie (celowo) - test_szatni ma zwrocic fallback")


fake_generate = types.ModuleType("app.generate")
fake_generate.client = _client
sys.modules["app.generate"] = fake_generate

from app import compliance  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


print("\n[sekcja 23] bramka jezyka (EN nie rusza LLM):")
LLM["calls"] = 0
en = "This is an English draft about retry logic and idempotency for payment agents."
out_en = compliance.test_szatni(en)
check("EN zwrocony bez zmian", out_en == en, out_en)
check("EN nie wywolal LLM (gate looks_polish)", LLM["calls"] == 0, LLM["calls"])

print("\n[sekcja 23] tekst PL wola LLM i nie wywraca przy bledzie:")
LLM["calls"] = 0
pl = "Robimy to, bo działa, a klientów, którzy odeszli, można łatwo odzyskać, jeśli się pośpieszysz."
out_pl = compliance.test_szatni(pl)
check("PL wywolal LLM", LLM["calls"] == 1, LLM["calls"])
check("blad LLM nie wywraca - fallback zwraca tekst", out_pl == pl, out_pl)

print("\n[sekcja 23] enforce routuje test szatni TYLKO dla marek PL:")
LLM["calls"] = 0
compliance.enforce({"brand_id": "AGS", "banned_vocab": []},
                   "Some English brand content without polish diacritics here.")
check("AGS (EN) - test szatni NIE odpalony", LLM["calls"] == 0, LLM["calls"])

LLM["calls"] = 0
compliance.enforce({"brand_id": "TNM", "banned_vocab": []},
                   "Robimy to, bo działa, a klientów, którzy odeszli, można łatwo odzyskać.")
# TNM PL: polish_pl (1) + test_szatni (1) = 2 wywolania (oba przez _rewrite->client)
check("TNM (PL) - test szatni odpalony (LLM wolany dla marki PL)", LLM["calls"] >= 1, LLM["calls"])

print("\n[sekcja 23] prompt niesie 4 anty-wzorce i wzorzec canonical:")
p = compliance.TEST_SZATNI_PROMPT
check("prompt ma aforyzm Kto...ten", "Kto..., ten" in p or "Aforyzm" in p, "brak AW-1")
check("prompt ma rzeczownik odczasownikowy", "odczasownikow" in p, "brak AW-2")
check("prompt ma wzorzec canonical Tomasza", "pod ich wplywem odpuszczaja" in p, "brak wzorca")
check("prompt trzyma przecinki PL", "ze/zeby/ktory" in p, "brak reguly interpunkcji")
check("prompt zero em dash", "Zero em dashes" in p, "brak reguly em-dash")

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
