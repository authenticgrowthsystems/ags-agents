"""Test kanonu 25/07: zamiast auto-generowanego OBRAZU material dostaje SZCZEGOLOWY PROMPT.
Zgloszenie Tomasza (powtorzone): grafiki generuje recznie, chce tylko prompty.
Stdlib only, zero sieci, zero LLM (generate podstawiony stubem).
Uruchomienie: python cm-agent/tests/test_grafiki_prompt.py"""
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


for n in ("psycopg", "psycopg_pool", "httpx", "anthropic", "openai", "uvicorn", "openpyxl"):
    _stub(n)
_stub("psycopg.types")
_stub("psycopg.types.json", Jsonb=lambda o: o)
_stub("psycopg.rows", dict_row=lambda *a, **k: None)
_stub("fastapi", FastAPI=_Any, Header=lambda **k: None, HTTPException=Exception)

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

# generate: prompt dziala, ale generate_image WYWALA - test pilnuje, ze NIE jest wolane
OBRAZ_WOLANY = {"n": 0}


def _boom_image(*a, **k):
    OBRAZ_WOLANY["n"] += 1
    raise AssertionError("generate_image NIE POWINNO byc wolane po kanonie 25/07")


_stub("app.generate",
      hint_wants_generated_graphic=lambda hint: "grafik" in (hint or "").lower() or "diagram" in (hint or "").lower(),
      generate_image_prompt=lambda brand, theme, body, hint, content_item_id=None:
          "SZCZEGOLOWY PROMPT: kompozycja centralna, paleta granat i piaskowy, "
          "typografia Playfair, naglowek doslowny 'One Key', 200 slow opisu... " * 3,
      generate_image=_boom_image)
_stub("app.db", fetchone=lambda *a, **k: None, execute=lambda *a, **k: None,
      fetchall=lambda *a, **k: [])
_stub("app.hitl", _admin_chat_id=lambda: 123)
_stub("app.matreview", _tg_upload_photo=lambda *a, **k: "SHOULD_NOT_HAPPEN")

# reszta importow workera (nie wolane w tescie, ale import ich dotyka)
for n, attrs in (("app.config", {}), ("app.research", {}), ("app.compliance", {}),
                 ("app.channels", {}), ("app.slots", {}), ("app.content_memory", {}),
                 ("app.logbot", {"send": lambda *a, **k: None}), ("app.tasks", {}),
                 ("app.x_collector", {}), ("app.metrics_import", {}), ("app.sync", {}),
                 ("app.decisions", {}), ("app.engagement", {}), ("app.proactive", {}),
                 ("app.sunday_brief", {}), ("app.crm", {}), ("app.sales", {}),
                 ("app.brand", {"load_brand": lambda b: {"brand_id": b}})):
    _stub(n, **attrs)
_stub("app.conversation", _tg=lambda *a, **k: None, language_comm=lambda: "pl")
_stub("app.planner", plan_text=lambda b: "")

import re  # noqa: E402
import traceback as _tb  # noqa: E402

# Worker importuje pol systemu top-level, wiec zamiast stubowac wszystko IZOLUJEMY sama funkcje
# ze zrodla: _auto_generate_image zalezy TYLKO od modulu 'generate' i 'traceback'. Wycinamy jej
# blok (do nastepnego def na tym samym wcieciu) i exec-ujemy w kontrolowanym namespace.
src = (BASE / "worker.py").read_text(encoding="utf-8")
m = re.search(r"\ndef _auto_generate_image\(.*?(?=\ndef )", src, re.DOTALL)
assert m, "nie znalazlem _auto_generate_image w worker.py"
ns = {"generate": sys.modules["app.generate"], "traceback": _tb, "print": lambda *a, **k: None}
exec(compile(m.group(0), "worker_fragment", "exec"), ns)
worker = types.SimpleNamespace(_auto_generate_image=ns["_auto_generate_image"])

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


brand = {"brand_id": "AGS"}
item = {"id": "abc", "master_theme": "Idempotency prevents double charges",
        "canonical_body": "Long body about retry logic."}

print("\n[grafiki 25/07] material 'proszacy sie o grafike':")
media = worker._auto_generate_image(item, brand, "diagram sekwencji retry", [])
check("generate_image NIE zostalo wolane", OBRAZ_WOLANY["n"] == 0)
check("dolaczono wpis visual_prompt", any(m.get("kind") == "visual_prompt" for m in media), media)
vp = next((m for m in media if m.get("kind") == "visual_prompt"), {})
check("prompt jest szczegolowy (dlugi)", len(vp.get("text") or "") > 100, len(vp.get("text") or ""))
check("wpis ma image_prompt (guzik Prompt go znajdzie)", bool(vp.get("image_prompt")), vp)
check("ZERO file_id (zaden obraz nie poszedl)", not any(m.get("file_id") for m in media), media)

print("\n[grafiki 25/07] material ze ZDJECIEM Tomasza - nie dokladamy nic:")
media2 = worker._auto_generate_image(item, brand, "diagram", [{"file_id": "foto123", "kind": "photo"}])
check("zdjecie Tomasza nietkniete, brak promptu", len(media2) == 1 and media2[0].get("file_id") == "foto123",
      media2)

print("\n[grafiki 25/07] hint NIE o grafike (zdjecie/wideo = zadanie czlowieka):")
media3 = worker._auto_generate_image(item, brand, "zdjecie z wydarzenia", [])
check("brak hintu graficznego = brak promptu", media3 == [], media3)

print("\n[grafiki 25/07] regeneracja nie dubluje promptu:")
media4 = worker._auto_generate_image(item, brand, "diagram", [{"kind": "visual_prompt", "text": "juz jest"}])
check("istniejacy visual_prompt nie jest dublowany",
      sum(1 for m in media4 if m.get("kind") == "visual_prompt") == 1, media4)

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
