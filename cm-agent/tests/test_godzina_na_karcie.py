# -*- coding: utf-8 -*-
"""Test D-015, domkniecie 19/08/2026: karta materialu podaje TE SAMA godzine, co meldunek bota.

CZEGO DOTYCZY. Meldunek zamknieto 10/08 regula `max(slot planu, czas kolejki)`
(`worker._godzina_publikacji`). Karta w `/karty` zostala przy czystym slocie z `content_items`,
wiec przy kolejce wypadajacej POZNIEJ niz slot obiecywala godzine do 15 minut za wczesna.
Dwie powierzchnie, jedna sprawa, dwie liczby - AP-312 w wydaniu liczbowym. Rozstrzygniecie
19/08: karta pokazuje DOKLADNIE to, co meldunek, a nie druga liczbe obok (AP-309).

CZEGO TEN TEST PILNUJE - SCIEZKI ALARMU, NIE SUKCESU:
  1. kolejka POZNIEJ niz slot (przypadek, dla ktorego dlug w ogole powstal) - karta ma pokazac
     czas kolejki i NIE MA prawa pokazac slotu planu;
  2. kolejka WCZESNIEJ niz slot (#344, #358) - karta ma pokazac slot planu, bo wczesniejsza
     godzina jest martwa: trzyma ja bramka `db.claim_item`;
  3. BRAK wiersza kolejki - karta ma powiedziec, CZEGO NIE WIE (AP-317), zamiast podstawic
     slot planu jako pewnik.

Trzeci przypadek jest tu najwazniejszy. Material widziany na karcie bywa PRZED wysylka, wiec
godziny po prostu nie ma. Domysl zapisany jak fakt jest gorszy niz brak danych - a przedzial
(slot, slot+15 min) znamy i wolno go podac, bo wynika z `humanize_slot` i z bramki claim_item.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_godzina_na_karcie.py"""
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
WARSAW = _zi.ZoneInfo("Europe/Warsaw")

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

from app import db, matreview, worker  # noqa: E402

# Slot planu: poniedzialek 19/08/2030 16:00. Data w przyszlosci swiadomie - inaczej karta
# dokleilaby linie "SLOT MINAL" i test mierzylby cos innego niz godzine.
SLOT = _dt.datetime(2030, 8, 19, 16, 0, tzinfo=WARSAW)
KOLEJKA_POZNIEJ = SLOT.replace(minute=12)   # 16:12 - przypadek, dla ktorego dlug powstal
KOLEJKA_WCZESNIEJ = SLOT.replace(minute=49) - _dt.timedelta(hours=1)   # 15:49, jak #344

MATERIAL = {"id": "m-1", "brand_id": "AGS", "master_theme": "Granica miedzy dwoma agentami",
            "target_channels": ["x"], "scheduled_for": SLOT,
            "canonical_body": "tresc materialu", "media": [], "status": "approved"}

ODCZYTY = {"n": 0, "wiersz": None}


def _fetchone(sql, params=None):
    ODCZYTY["n"] += 1
    return ODCZYTY["wiersz"]


db.fetchone = _fetchone
db.fetchall = lambda sql, params=None: [dict(MATERIAL)]
matreview.pending_items = lambda brand_id=None: [dict(MATERIAL)]


def ustaw_kolejke(czas):
    """czas=None -> material nie ma jeszcze zadnego wiersza w kolejce."""
    ODCZYTY["wiersz"] = {"czeka": czas, "dowolny": czas} if czas else {"czeka": None, "dowolny": None}


def linia_godziny(tekst):
    for l in tekst.split("\n"):
        if l.startswith("🕐"):
            return l
    return "(brak linii z godzina)"


print("\n[regula] karta liczy godzine TYM SAMYM kodem, co meldunek:")
check("_godzina_karty wola worker._godzina_publikacji",
      "_godzina_publikacji" in (matreview._godzina_karty.__doc__ or "")
      or "_godzina_publikacji" in (matreview.__dict__.get("_godzina_karty").__code__.co_names
                                   + matreview._godzina_karty.__code__.co_names))
ustaw_kolejke(KOLEJKA_POZNIEJ)
kiedy, pewna = matreview._godzina_karty(MATERIAL)
check("wynik karty == wynik reguly meldunku",
      kiedy == worker._godzina_publikacji(SLOT, KOLEJKA_POZNIEJ), str(kiedy))

print("\n[ALARM] kolejka POZNIEJ niz slot - to jest przypadek, dla ktorego dlug powstal:")
ustaw_kolejke(KOLEJKA_POZNIEJ)
t_a = matreview._card()[0]
check("karta pokazuje czas kolejki (16:12)", "16:12" in linia_godziny(t_a), linia_godziny(t_a))
check("karta NIE pokazuje juz slotu planu (16:00)", "16:00" not in t_a, linia_godziny(t_a))
check("nie dokleja zastrzezenia - te godzine ZNA",
      "nie znam" not in linia_godziny(t_a), linia_godziny(t_a))
print("       tekst: " + linia_godziny(t_a))

print("\n[odwrotny] kolejka WCZESNIEJ niz slot (#344 15:49) - ta godzina jest martwa:")
ustaw_kolejke(KOLEJKA_WCZESNIEJ)
t_b = matreview._card()[0]
check("karta pokazuje slot planu (16:00)", "16:00" in linia_godziny(t_b), linia_godziny(t_b))
check("karta NIE pokazuje czasu kolejki (15:49)", "15:49" not in t_b, linia_godziny(t_b))
print("       tekst: " + linia_godziny(t_b))

print("\n[AP-317] brak wiersza kolejki - karta ma powiedziec, CZEGO NIE WIE:")
ustaw_kolejke(None)
t_c = matreview._card()[0]
check("podaje slot planu jako dolna granice", "16:00" in linia_godziny(t_c), linia_godziny(t_c))
check("mowi wprost, ze dokladnej godziny nie zna",
      "nie znam" in linia_godziny(t_c), linia_godziny(t_c))
check("mowi, DLACZEGO nie zna (brak wpisu w kolejce)",
      "brak wpisu w kolejce" in linia_godziny(t_c), linia_godziny(t_c))
check("podaje przedzial, ktory ZNA (do 15 minut pozniej)",
      "15 minut" in linia_godziny(t_c), linia_godziny(t_c))
print("       tekst: " + linia_godziny(t_c))

print("\n[AP-317, wariant drugi] baza nie oddaje wiersza - to tez jest 'nie wiem', nie 'brak':")
ODCZYTY["wiersz"] = None
t_d = matreview._card()[0]
check("zachowuje sie jak przy braku kolejki", "nie znam" in linia_godziny(t_d), linia_godziny(t_d))

print("\n[druga powierzchnia] karta PODGLADU (approved/handed_off/published) liczy tak samo:")
ustaw_kolejke(KOLEJKA_POZNIEJ)
t_v = matreview._view_card(dict(MATERIAL))[0]
check("podglad pokazuje czas kolejki (16:12)", "16:12" in linia_godziny(t_v), linia_godziny(t_v))
check("podglad NIE pokazuje slotu planu (16:00)", "16:00" not in t_v, linia_godziny(t_v))
ustaw_kolejke(None)
t_v2 = matreview._view_card(dict(MATERIAL))[0]
check("podglad bez kolejki tez mowi, czego nie wie",
      "nie znam" in linia_godziny(t_v2), linia_godziny(t_v2))

print("\n[wydajnosc] jeden dodatkowy odczyt na karte, nie N+1:")
ustaw_kolejke(KOLEJKA_POZNIEJ)
ODCZYTY["n"] = 0
matreview._card()
check("dokladnie jeden odczyt kolejki na karte", ODCZYTY["n"] == 1, str(ODCZYTY["n"]))

print("\n[anty-regresja] regula nie ma prawa zostac przepisana w karcie:")
src = (APP / "matreview.py").read_text(encoding="utf-8")
check("karta NIE liczy maksimum wlasnym porownaniem",
      "> slot" not in src and "> kolejka" not in src)
check("_card bierze godzine z _godzina_karty", "kiedy, pewna = _godzina_karty(it)" in src)
check("_view_card bierze godzine z _godzina_karty", src.count("_godzina_karty(it)") >= 2)

print("\n[zgodnosc powierzchni] raport i stan_gry licza tym samym kodem:")
from app import reports  # noqa: E402
check("raport ma wspolna funkcje godziny", hasattr(reports, "_godzina_wiersza"))
check("raport zwraca to samo, co meldunek",
      reports._godzina_wiersza({"slot_planu": SLOT, "scheduled_for": KOLEJKA_WCZESNIEJ}) == SLOT)
check("raport bierze pod uwage pozniejsza kolejke",
      reports._godzina_wiersza({"slot_planu": SLOT, "scheduled_for": KOLEJKA_POZNIEJ}) == KOLEJKA_POZNIEJ)

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
