"""Testy sciezki sprzedazowej: wybor adresu prospekta (dlug C3) i osoba decyzyjna ze strony
(dlug C2). Stdlib only, bez bazy, bez sieci, bez LLM.
Uruchomienie: python cm-agent/tests/test_sales_prospekt.py"""
import datetime as _dt
import pathlib
import sys
import types
import zoneinfo as _zi

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:  # Windows bez tzdata - kontener linuksowy strefy zna
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

from app import sales  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---------------- C3: ktory adres jest strona prospekta ----------------
print("\n[C3] wybor adresu prospekta z tekstu researchu:")

RESEARCH_STEPOWNIA = (
    "Wroclawska Stepownia prowadzi kursy stepowania. Autor wpisow: "
    "https://stepownia.pl/author/dudzikdariusz oraz strona glowna https://stepownia.pl/ "
    "i profil https://www.facebook.com/wroclawskastepownia")
check("archiwum autora NIE wygrywa z domena",
      sales._znajdz_strone_w_researchu("Wroclawska Stepownia", RESEARCH_STEPOWNIA) == "https://stepownia.pl",
      sales._znajdz_strone_w_researchu("Wroclawska Stepownia", RESEARCH_STEPOWNIA))

RESEARCH_PODSTRONA = ("Klub dziala pod adresem https://stepownia.pl/wroclawska_stepownia/ "
                      "w ramach wiekszego serwisu https://stepownia.pl/")
wynik = sales._znajdz_strone_w_researchu("Wroclawska Stepownia", RESEARCH_PODSTRONA)
check("sensowna podstrona zostaje, gdy niesie nazwe (krotszy adres tez ja niesie)",
      wynik in ("https://stepownia.pl", "https://stepownia.pl/wroclawska_stepownia/"), wynik)

RESEARCH_SMIECI = ("Zobacz https://klub.pl/tag/taniec i https://klub.pl/koszyk oraz "
                   "https://klub.pl/polityka-prywatnosci")
check("same sciezki-smieci -> zostaje korzen domeny",
      sales._znajdz_strone_w_researchu("Klub", RESEARCH_SMIECI) == "https://klub.pl",
      sales._znajdz_strone_w_researchu("Klub", RESEARCH_SMIECI))

check("arxiv i wikipedia odrzucone",
      sales._znajdz_strone_w_researchu("Klub", "https://arxiv.org/abs/1 https://pl.wikipedia.org/wiki/Klub")
      is None)

RESEARCH_TYLKO_SOCIAL = "Klub ma tylko https://www.facebook.com/klubtaneczny"
check("profil spolecznosciowy jako ostatecznosc",
      sales._znajdz_strone_w_researchu("Klub Taneczny", RESEARCH_TYLKO_SOCIAL)
      == "https://www.facebook.com/klubtaneczny")

check("pdf ze strony -> korzen, nie plik",
      sales._znajdz_strone_w_researchu("Stepownia", "cennik https://stepownia.pl/cennik2026.pdf")
      == "https://stepownia.pl")

# ---------------- C2: kto decyduje ----------------
print("\n[C2] osoba decyzyjna ze strony (instruktor to NIE decydent):")

STRONA_WLASCICIEL = ("Nasz zespol. Wlascicielka Anna Kowalska prowadzi klub od 2009 roku. "
                     "Instruktor Piotr Nowak uczy hip-hopu.")
k = sales.osoba_decyzyjna(STRONA_WLASCICIEL)
check("wlascicielka rozpoznana", k and k["osoba"] == "Anna Kowalska" and k["decyzyjna"], k)

STRONA_INSTRUKTORZY = "Instruktorzy: Piotr Nowak prowadzi zajecia dla dzieci, trener Marek Zielinski."
k2 = sales.osoba_decyzyjna(STRONA_INSTRUKTORZY)
check("sam instruktor = kontakt POMOCNICZY, nie decydent",
      k2 and k2["osoba"] == "Piotr Nowak" and k2["decyzyjna"] is False, k2)

STRONA_PO_NAZWISKU = "Dariusz Dudzik, wlasciciel Wroclawskiej Stepowni, tanczy od 30 lat."
k3 = sales.osoba_decyzyjna(STRONA_PO_NAZWISKU)
check("rola PO nazwisku tez dziala", k3 and k3["osoba"] == "Dariusz Dudzik" and k3["decyzyjna"], k3)

STRONA_MIESZANA = ("Instruktorka Ewa Malinowska prowadzi balet. Dyrektor Jan Kowalczyk "
                   "odpowiada za zapisy.")
k4 = sales.osoba_decyzyjna(STRONA_MIESZANA)
check("gdy sa oboje, wygrywa rola decyzyjna",
      k4 and k4["osoba"] == "Jan Kowalczyk" and k4["decyzyjna"], k4)

check("brak osob = None", sales.osoba_decyzyjna("Zapraszamy na zajecia w poniedzialki.") is None)
check("pusty tekst = None", sales.osoba_decyzyjna("") is None)
check("None = None", sales.osoba_decyzyjna(None) is None)

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
