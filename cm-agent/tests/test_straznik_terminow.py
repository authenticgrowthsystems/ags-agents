"""Test straznika terminow lejka (26/07/2026, sekcja 4.1 diagnozy, Level 2 zatwierdzony).

Wada: `next_followup_at` mialo wylacznie konsumentow PULL. Czternascie tickow petli workera,
zaden nie czytal tego pola; w n8n zero trafien. "Nastepny kontakt 28/07" nie uruchamialo
niczego, wiec termin kontaktu z najwiekszym prospektem zyl w pamieci jednego czlowieka.

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_straznik_terminow.py"""
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

from app import sales, db, decisions, engagement  # noqa: E402

FAILS = []
SQL = []
EXEC = []
ASKED = []
ROWS = {"lejek": []}
UTC = _dt.timezone.utc


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _fetchall(sql, params=None):
    SQL.append(sql)
    if "FROM sales_pipeline" in sql:
        return list(ROWS["lejek"])
    return []


db.fetchall = _fetchall
db.fetchone = lambda sql, params=None: None
db.execute = lambda sql, params=None: EXEC.append((sql, params))
decisions.ask = lambda *a, **k: ASKED.append({"subagent": a[0], "brand": a[1], "typ": a[2],
                                              "pytanie": a[3], "opcje": a[4],
                                              "ctx": k.get("context")})
engagement._tg = lambda *a, **k: None

PROSPEKT = {
    "id": "dde3a247", "prospect_name": "adamietz.pl", "stage": "qualified",
    "next_followup_at": _dt.datetime.now(UTC) - _dt.timedelta(days=2),
    "notes": "20/07 research zlecony\n25/07 material dla Piotra gotowy",
    "contact_email": None, "contact_phone": None, "contact_person": None,
}


# ---------------- zapytanie strazniki ----------------
print("\n[4.1] zapytanie straznika terminow:")
ROWS["lejek"] = []
SQL.clear()
sales.followup_watch()
sql = SQL[-1]
check("czyta next_followup_at (pole mialo zero konsumentow push)", "next_followup_at" in sql, sql)
check("bierze tylko terminy, ktore juz minely", "next_followup_at <= NOW()" in sql, sql)
check("pomija transakcje poza gra (won, lost, parked)",
      "NOT IN ('won','lost','parked')" in sql, sql)
check("odsiew otwartych bramek jest w SQL", "NOT EXISTS" in sql, sql)
check("odsiew PRZED LIMIT-em (AP-310)",
      0 < sql.find("NOT EXISTS") < sql.find("LIMIT"),
      "inaczej trzy zalegle prospekty zablokowalyby straznika tak jak przypomnienia")


# ---------------- etap 'parked' (DDL 033, decyzja Managera 27/07) ----------------
print("\n[parked] uspione prospekty wypadaja z gry, ale nie z bazy:")
check("'parked' jest legalnym etapem", "parked" in sales._STAGES, str(sales._STAGES))
check("etapy poza gra trzymane w JEDNYM miejscu (AP-309)",
      sales._STAGES_ZAMKNIETE == ("won", "lost", "parked"), str(sales._STAGES_ZAMKNIETE))
check("'parked' to nie 'lost' - osobna wartosc, nie alias",
      "parked" != "lost" and len(set(sales._STAGES_ZAMKNIETE)) == 3)
check("straznik terminow pomija uspione", "parked" in sql, sql)
check("uspiony etap ma wlasna ikone", sales._STAGE_ICON.get("parked"), str(sales._STAGE_ICON))
check("pipeline_move przyjmie 'parked' (jest w skali narzedzia)", "parked" in sales._STAGES)


# ---------------- karta niesie dowod ----------------
print("\n[4.1] karta decyzji niesie dowod, nie sama nazwe:")
ROWS["lejek"] = [PROSPEKT]
ASKED.clear()
sales.followup_watch()
check("zadano dokladnie jedno pytanie", len(ASKED) == 1, str(len(ASKED)))
a = ASKED[0] if ASKED else {"pytanie": "", "opcje": [], "ctx": {}, "typ": "", "subagent": ""}
check("typ decyzji to sales_followup", a["typ"] == "sales_followup", a["typ"])
check("pyta jako subagent sprzedazy", a["subagent"] == "AGS:sprzedaz", str(a["subagent"]))
check("karta podaje nazwe prospekta", "adamietz.pl" in a["pytanie"], a["pytanie"])
check("karta mowi ile po terminie", "2 dni temu" in a["pytanie"], a["pytanie"])
check("karta podaje etap", "qualified" in a["pytanie"], a["pytanie"])
check("brak kontaktu jest powiedziany wprost, nie przemilczany",
      "BRAK danych kontaktowych" in a["pytanie"], a["pytanie"])
check("karta pokazuje ostatnia notatke", "material dla Piotra" in a["pytanie"], a["pytanie"])
check("kontekst niesie identyfikator wiersza lejka",
      (a["ctx"] or {}).get("pipeline_id") == "dde3a247", str(a["ctx"]))
check("trzy guziki, kazdy rozstrzygajacy", len(a["opcje"]) == 3, str(a["opcje"]))
check("zaden guzik nie obiecuje zmiany etapu",
      not any("etap" in (o.get("label") or "").lower() for o in a["opcje"]), str(a["opcje"]))

with_kontakt = dict(PROSPEKT, contact_email="x@y.pl", contact_phone="500 100 200",
                    contact_person="Jan Kowalski")
karta = sales._followup_karta(with_kontakt)
check("gdy kontakt jest, karta go pokazuje", "x@y.pl" in karta and "500 100 200" in karta, karta)
check("osoba decyzyjna trafia na karte", "Jan Kowalski" in karta, karta)

dzis = dict(PROSPEKT, next_followup_at=_dt.datetime.now(UTC))
check("termin dzisiejszy nie mowi '0 dni temu'", "dzisiaj" in sales._followup_karta(dzis))


# ---------------- guziki robia to, co obiecuja ----------------
print("\n[4.1] kazdy guzik robi dokladnie to, co ma na etykiecie:")
CTX = {"context": {"pipeline_id": "dde3a247", "prospect": "adamietz.pl"}}

EXEC.clear()
sales.apply_followup(CTX, "done", 1)
check("'Skontaktowalem sie' przesuwa termin", any("next_followup_at=NOW()" in s for s, _ in EXEC))
check("'Skontaktowalem sie' daje 7 dni",
      any(p and sales._FOLLOWUP_PO_KONTAKCIE_DNI in p for _, p in EXEC), str(EXEC))
check("'Skontaktowalem sie' NIE rusza etapu", not any("stage" in s for s, _ in EXEC), str(EXEC))

EXEC.clear()
sales.apply_followup(CTX, "snooze", 1)
check("'Przypomnij' daje 3 dni",
      any(p and sales._FOLLOWUP_SNOOZE_DNI in p for _, p in EXEC), str(EXEC))

EXEC.clear()
sales.apply_followup(CTX, "park", 1)
check("'Odpuszczam' zdejmuje termin", any("next_followup_at=NULL" in s for s, _ in EXEC), str(EXEC))
check("'Odpuszczam' NIE kasuje prospekta z lejka",
      not any("DELETE" in s.upper() for s, _ in EXEC), str(EXEC))

EXEC.clear()
sales.apply_followup({"context": {}}, "done", 1)
check("decyzja bez identyfikatora nie robi nic", not EXEC, str(EXEC))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
