"""Testy straznika meta-naglowka wariantu (zgloszenie Tomasza 24/07: post na X wyszedl
z linia "# X Adaptation"). Stdlib only, bez bazy i bez LLM.
Uruchomienie: python cm-agent/tests/test_meta_naglowek.py"""
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
for name, attrs in (("app.config", {}), ("app.db", {"fetchone": lambda *a, **k: None,
                                                    "fetchall": lambda *a, **k: [],
                                                    "execute": lambda *a, **k: None}),
                    ("app.tasks", {"model_for": lambda k: ("m", "t", "s"),
                                   "log_task": lambda *a, **k: None}),
                    ("app.generate", {"client": lambda: None})):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod

from app import compliance  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


TRESC = ("A payment agent hits the gateway. Network hangs 3 seconds. No response back, so it retries.\n\n"
         "Not hypothetical. This is the default behavior of every system that treats \"no answer\" "
         "as \"failed\" instead of \"unknown\".")

print("\n[meta] zdejmujemy meta-linie modelu:")
PRZYPADKI = [
    ("# X Adaptation\n\n" + TRESC, "naglowek z zrzutu Tomasza (#195)"),
    ("## LinkedIn version\n\n" + TRESC, "naglowek wersji LinkedIn"),
    ("**Wersja na X:**\n\n" + TRESC, "etykieta pogrubiona"),
    ("X:\n\n" + TRESC, "goła etykieta kanalu"),
    ("Oto adaptacja na X:\n\n" + TRESC, "zapowiedz po polsku"),
    ("Here's the X post:\n\n" + TRESC, "zapowiedz po angielsku"),
    ("```\n" + TRESC + "\n```", "oplotka kodu"),
    ("# X Adaptation\n\nHere's the post:\n\n" + TRESC, "dwie meta-linie pod rzad"),
]
for wejscie, opis in PRZYPADKI:
    out = compliance.strip_meta_header(wejscie)
    check(opis, out.startswith("A payment agent hits"), repr(out[:70]))
    check(f"   tresc nietknieta ({opis})", out.endswith('instead of "unknown".'), repr(out[-40:]))

print("\n[meta] NIE ruszamy tresci:")
NIETYKALNE = [
    (TRESC, "zwykly post"),
    ("#buildinpublic\n\n" + TRESC, "hasztag na poczatku (bez spacji po #)"),
    ("Retry without idempotency is not resilience.\n\n" + TRESC, "zdanie otwierajace"),
    ("3 rzeczy, ktore zepsulem dzis:\n\n" + TRESC, "lista z dwukropkiem, ale bez slowa meta"),
    ("Post mortem: co poszlo nie tak.\n\n" + TRESC, "'post mortem' to tresc, nie etykieta"),
]
for wejscie, opis in NIETYKALNE:
    out = compliance.strip_meta_header(wejscie)
    check(opis, out.strip() == wejscie.strip(), repr(out[:60]))

print("\n[meta] przypadki brzegowe:")
check("pusty tekst wraca bez zmian", compliance.strip_meta_header("") == "")
check("None nie wywraca", compliance.strip_meta_header(None) is None)
check("sam naglowek bez tresci = tekst zostaje (nie kasujemy wszystkiego)",
      compliance.strip_meta_header("# X Adaptation").strip() == "# X Adaptation")
dlugi = "# " + ("bardzo dlugi naglowek " * 6) + "\n\n" + TRESC
check("naglowek dluzszy niz 60 znakow zostaje (moze byc trescia)",
      compliance.strip_meta_header(dlugi).startswith("#"), repr(compliance.strip_meta_header(dlugi)[:40]))
check("limit 3 meta-linii", compliance.strip_meta_header(
    "# X post\nWersja:\nOto tekst:\n# Draft\n\n" + TRESC).startswith("# Draft"))

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
