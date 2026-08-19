# -*- coding: utf-8 -*-
"""Test D-020 (19/08/2026, decyzja Managera Z-4): ustawienie publish_mode='webhook' pada GLOSNO
w kodzie, a nie jest tylko odradzane w dokumencie.

DOWOD, KTORY GO ZAMOWIL. Tryb `webhook` jest zabroniony od 22/07 po incydencie AP-307 (4-5 postow
X w godzine, wiersze z mediami wyslane bez mediow, polski post na anglojezycznym profilu, callback
oznaczajacy 'published' WSZYSTKIE wiersze materialu). Zakaz zyl wylacznie w dokumentach - i
`DEPLOY_CHECKLIST` przez trzy tygodnie PO incydencie nadal instruowal, zeby ten tryb ustawic.
Warunek zapisany w dokumencie jest zalozeniem, nie zabezpieczeniem (AP-314, AP-316).

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314 punkt 4): SCIEZKI ALARMU. Podajemy ZLY wsad - dokladnie
ten napis, ktory wywolal incydent - i sprawdzamy, ze bramka odmawia ORAZ ze do bazy nie poszedl
zaden zapis. Bramka, ktorej nie widziales przy pracy, jest zalozeniem.

DRUGA POLOWA, rownie wazna: blokada NIE MOZE psuc zakladania celow i marek. Dwa z szesciu miejsc
dotykajacych publish_mode nie ustawialy trybu na niczyje zadanie - mialy 'webhook' jako WARTOSC
DOMYSLNA. Bezpiecznik, ktory zabija dzialajaca sciezke, sam jest awaria (AP-312), wiec sprawdzamy
tez, ze `/brand_add` i `target_create` dalej dzialaja, tylko juz nie w zabronionym trybie.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_blokada_webhook.py"""
import datetime as _dt
import os
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:   # maszyna bez tzdata - te samo podstawienie co w pozostalych testach
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

os.environ.pop("PUBLISH_WEBHOOK_ODBLOKOWANY", None)

from app import brands_ui, config, conversation, db  # noqa: E402

# ---------------------------------------------------------------- podstawka bazy
ZAPISY = []            # kazdy UPDATE/INSERT, ktory dotarl do "bazy"
KONFIGI = {("AGS", "x"): {"publish_mode": "webhook", "language_publish": "en"}}
MARKI = set()


def _fetchone(sql, params=None):
    s = " ".join((sql or "").split())
    if s.startswith("UPDATE channels SET config"):
        ZAPISY.append(("UPDATE channels", params))
        return {"channel": params[2]}
    if s.startswith("SELECT config FROM channels"):
        cfg = KONFIGI.get((params[0], params[1]))
        return {"config": dict(cfg)} if cfg else None
    if s.startswith("INSERT INTO channels"):
        ZAPISY.append(("INSERT INTO channels", params))
        return {"id": 700 + len(ZAPISY)}
    if "FROM brands WHERE brand_id" in s:
        return {"brand_id": params[0]} if params[0] in MARKI else None
    return None


def _execute(sql, params=None):
    s = " ".join((sql or "").split())
    if s.startswith("INSERT INTO brands"):
        MARKI.add(params[0])
    ZAPISY.append((s[:22], params))
    return None


db.fetchone = _fetchone
db.fetchall = lambda sql, params=None: []
db.execute = _execute


def _tryb(inp):
    """Skrot na droge swiadomego ustawienia trybu."""
    return conversation._target_update({"brand_id": "AGS", "channel": "x", **inp})


# ================================================================ SCIEZKA ALARMU
print("\n[ALARM] zly wsad: dokladnie ten tryb, ktory wywolal incydent 20/07:")
przed = len(ZAPISY)
odp = _tryb({"key": "publish_mode", "value": "webhook"})
check("bramka ODMAWIA (nie 'zrobione')", odp.startswith("⛔"), repr(odp[:80]))
check("do bazy NIE poszedl zaden zapis", len(ZAPISY) == przed,
      repr(ZAPISY[przed:]))
check("komunikat nazywa AP-307", "AP-307" in odp, repr(odp[:200]))
check("komunikat mowi, CO sie wtedy stalo - burst", "4-5 postow X" in odp, repr(odp[:400]))
check("komunikat mowi o zgubionych mediach", "BEZ mediow" in odp)
check("komunikat mowi o obcym jezyku publicznie", "anglojezycznym profilu LinkedIn" in odp)
check("komunikat mowi o bazie klamiacej o stanie", "baza klamala" in odp)
check("komunikat podaje, czego uzyc zamiast", "post_queue" in odp and "draft" in odp)
check("komunikat podaje droge swiadomego zdjecia blokady",
      "PUBLISH_WEBHOOK_ODBLOKOWANY=AP-307-callback-naprawiony" in odp)
check("komunikat odsyla do pelnego opisu anty-wzorca",
      "docs/anti-patterns/AP-307" in odp)

print("\n[ALARM] obejscia, ktore 'przypadkiem' by przeszly:")
for wsad in ("WEBHOOK", " webhook ", "Webhook"):
    przed = len(ZAPISY)
    odp = _tryb({"key": "publish_mode", "value": wsad})
    check(f"'{wsad}' tez zatrzymany", odp.startswith("⛔") and len(ZAPISY) == przed, repr(odp[:60]))

print("\n[ALARM] wartosc 'prawdziwa' zmiennej NIE zdejmuje blokady:")
for udawane in ("true", "1", "TAK", "AP-307", "ap-307-callback-naprawiony"):
    os.environ["PUBLISH_WEBHOOK_ODBLOKOWANY"] = udawane
    przed = len(ZAPISY)
    odp = _tryb({"key": "publish_mode", "value": "webhook"})
    check(f"PUBLISH_WEBHOOK_ODBLOKOWANY='{udawane}' nadal blokuje",
          odp.startswith("⛔") and len(ZAPISY) == przed, repr(odp[:60]))
os.environ.pop("PUBLISH_WEBHOOK_ODBLOKOWANY", None)

# ================================================================ SCIEZKA ZDJECIA BLOKADY
print("\n[zdjecie blokady] jawna decyzja w srodowisku dziala i NIE jest cicha:")
os.environ["PUBLISH_WEBHOOK_ODBLOKOWANY"] = config.WEBHOOK_HASLO_ODBLOKOWANIA
przed = len(ZAPISY)
odp = _tryb({"key": "publish_mode", "value": "webhook"})
check("zapis przechodzi", len(ZAPISY) == przed + 1, repr(odp[:80]))
check("zapisano wlasnie publish_mode=webhook",
      ZAPISY[-1][1][0] == {"publish_mode": "webhook"}, repr(ZAPISY[-1][1]))
check("paragon OSTRZEGA, ze blokada jest zdjeta", "blokada trybu 'webhook' jest ZDJETA" in odp,
      repr(odp))
check("ostrzezenie przypomina o niesprawnym callbacku", "callback publishera" in odp, repr(odp))
os.environ.pop("PUBLISH_WEBHOOK_ODBLOKOWANY", None)

przed = len(ZAPISY)
odp = _tryb({"key": "publish_mode", "value": "webhook"})
check("po zdjeciu zmiennej blokada wraca BEZ restartu procesu",
      odp.startswith("⛔") and len(ZAPISY) == przed, repr(odp[:60]))

# ================================================================ ZWYKLE TRYBY BEZ ZMIAN
print("\n[bez zmian] dozwolone tryby i inne klucze przechodza jak dotad:")
for wartosc in ("post_queue", "draft"):
    przed = len(ZAPISY)
    odp = _tryb({"key": "publish_mode", "value": wartosc})
    check(f"publish_mode='{wartosc}' zapisany z paragonem ⚙️",
          odp.startswith("⚙️") and len(ZAPISY) == przed + 1, repr(odp[:70]))
    check(f"paragon przy '{wartosc}' NIE straszy ostrzezeniem", "UWAGA" not in odp, repr(odp))

przed = len(ZAPISY)
odp = _tryb({"key": "publish_windows", "value": "webhook"})
check("bramka pilnuje TYLKO publish_mode (inny klucz przechodzi)",
      odp.startswith("⚙️") and len(ZAPISY) == przed + 1, repr(odp[:70]))

przed = len(ZAPISY)
odp = _tryb({"key": "posts_per_day", "value": "2"})
check("liczby dalej ida do bazy jako liczby", ZAPISY[-1][1][0] == {"posts_per_day": 2},
      repr(ZAPISY[-1][1]))

print("\n[podlaczenie] deterministyczna trasa 'ustaw ... na ...' idzie przez te sama bramke:")
przed = len(ZAPISY)
odp = conversation._config_route("ustaw publish_mode dla AGS x na webhook")
check("fraza z Telegrama tez zatrzymana", (odp or "").startswith("⛔"), repr((odp or "")[:70]))
check("i tu do bazy nic nie poszlo", len(ZAPISY) == przed, repr(ZAPISY[przed:]))

# ================================================================ NIC NIE ZEPSUTE
print("\n[nie zepsute] zakladanie CELU dziala, tylko juz nie w zabronionym trybie:")
przed = len(ZAPISY)
odp = conversation._target_create({"brand_id": "AGS", "channel": "youtube", "language_publish": "pl"})
check("cel zalozony", odp.startswith("🎯") and len(ZAPISY) == przed + 1, repr(odp[:90]))
_cfg = ZAPISY[-1][1][2]
check("domyslny tryb nowego celu to 'draft', nie 'webhook'",
      _cfg.get("publish_mode") == "draft", repr(_cfg))
check("paragon MOWI, w jakim trybie cel powstal", "tryb publikacji: draft" in odp, repr(odp[:160]))

print("\n[nie zepsute] zakladanie MARKI dziala (/brand_add):")
przed = len(ZAPISY)
odp = brands_ui._add("TESTOWA")
check("marka utworzona z checklista", odp.startswith("🆕"), repr(odp[:80]))
_ins = [p for (s, p) in ZAPISY[przed:] if s.startswith("INSERT INTO channels")]
check("cel linkedin zalozony", len(_ins) == 1, repr(ZAPISY[przed:]))
check("config nowej marki NIE zawiera 'webhook'", "webhook" not in (_ins[0][1] if _ins else "x"),
      repr(_ins[0][1] if _ins else None))
check("config nowej marki ma tryb 'draft'", '"publish_mode": "draft"' in (_ins[0][1] if _ins else ""),
      repr(_ins[0][1] if _ins else None))

print("\n[dziedziczenie] 'webhook' nie wejdzie tylnymi drzwiami przez kopiowanie configu:")
przed = len(ZAPISY)
odp = conversation._target_create({"brand_id": "AGS", "channel": "mastodon",
                                   "copy_from_channel": "x"})
check("kopiowanie z celu w trybie webhook ODMAWIA glosno", odp.startswith("⛔"), repr(odp[:80]))
check("cel NIE powstal polowicznie", len(ZAPISY) == przed, repr(ZAPISY[przed:]))

# ================================================================ ZRODLO
print("\n[zrodlo] zabroniony napis nie wraca jako wartosc domyslna (AP-316):")
for plik in ("conversation.py", "brands_ui.py"):
    src = (APP / plik).read_text(encoding="utf-8")
    linie = [l for l in src.splitlines()
             if "publish_mode" in l and '"webhook"' in l and not l.strip().startswith("#")]
    check(f"{plik}: zaden ZYWY wiersz nie przypisuje publish_mode='webhook'", not linie,
          repr([l.strip()[:70] for l in linie]))

print("\n[zrodlo] bramka jest JEDNA, a nie kopiowana po plikach:")
gniazda = []
for plik in sorted(APP.glob("*.py")):
    if plik.name == "config.py":
        continue
    if "sprawdz_tryb_publikacji" in plik.read_text(encoding="utf-8"):
        gniazda.append(plik.name)
check("decyzja o zakazie mieszka wylacznie w config.py",
      "def sprawdz_tryb_publikacji" in (APP / "config.py").read_text(encoding="utf-8"))
check("pozostale pliki tylko ja WOLAJA (2 punkty wejscia)", len(gniazda) == 2, repr(gniazda))

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
