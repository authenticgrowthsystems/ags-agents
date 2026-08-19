"""Test bramki zakladania NOWEGO prospekta (D-021, 19/08/2026).

POWOD: Manager nie mial jak zapisac nowego czlowieka. Lancuch pekal dokladnie w chwili,
w ktorej pojawia sie nowy prospekt, czyli w jedynym momencie, ktory buduje lejek
(Rafal Petrykowski 11/08: wiadomosc poszla, wpis zostal w pliku na dysku).

TEST NAJWAZNIEJSZY - FRANCZYZA: dwa oddzialy tej samej domeny musza przejsc OBA. To jest
wada, ktorej ta bramka ma NIE miec. Dedup po samej domenie wyrzucil 27/07 trzy REALNE
prospekty Egurroli jako duplikaty; w lejku stoja dzis Grodzisk i Katowice, oba prawdziwe.

Reszta to SCIEZKA ALARMU, czyli bramka odpalona ZLYM wsadem (AP-314 - zabezpieczeniu,
ktorego nikt nie widzial przy pracy, nie wolno ufac):
  - proba zalozenia duplikatu (ta sama nazwa w innej kolejnosci slow),
  - polska nazwa wlasna z ogonkiem W SRODKU (AP-313, przypadek Chwalinskiego:
    "Chwalin" NIE WYSTEPUJE w "Chwaliński", bo nie ma tam zwyklego "n"),
  - nazwa, ktora zawiera sie w innej (niepewnosc - bramka pada ZAMKNIETA),
  - odrzucenie musi powiedziec, KTORY wiersz uznano za ten sam i CO przepadnie (AP-311),
  - to, co zapisane, rozroznia ZOBACZONE od WYWNIOSKOWANEGO (AP-317).

Stdlib only, bez bazy, bez sieci, bez LLM.
Uruchomienie: python -X utf8 cm-agent/tests/test_nowy_prospekt.py"""
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

from app import db, sales  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ------------------------------------------------------------------ atrapa bazy
# Stan wyjsciowy odwzorowuje lejek: jeden oddzial franczyzy, jedna nazwa z ogonkiem
# W SRODKU, jeden prospekt bez domeny (dziewieciu z dwunastu ma tylko skrzynke na gmailu).
LEJEK = [
    {"id": "11111111-1111-1111-1111-111111111111",
     "prospect_name": "Grodzisk Mazowiecki Egurrola Dance Studio", "stage": "parked",
     "prospect_url": "https://egurrola.com", "contact_email": None, "contact_phone": None,
     "contact_person": None, "notes": "import bialej listy", "source": "import",
     "updated_at": "2026-08-01"},
    {"id": "22222222-2222-2222-2222-222222222222",
     "prospect_name": "Grupa Chwaliński", "stage": "qualified",
     "prospect_url": "https://grupachwalinski.pl", "contact_email": "biuro@grupachwalinski.pl",
     "contact_phone": None, "contact_person": "Miroslaw Damczyk", "source": "manual",
     "notes": "Firma budowlana, Opole. Kontakt: przez formularz", "updated_at": "2026-08-02"},
    {"id": "33333333-3333-3333-3333-333333333333",
     "prospect_name": "Studio Tanca StandART", "stage": "prospect",
     "prospect_url": None, "contact_email": "recepcja@standart.pl", "contact_phone": None,
     "contact_person": None, "notes": "Szkola tanca, Dobrzykowice.", "source": "import",
     "updated_at": "2026-08-03"},
]
LICZNIK = [0]


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def _bez(s):
    """Atrapa SQL-owego translate() z AP-313 - kolumna traci ogonki przed porownaniem."""
    return str(s or "").translate(str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ"))


def _like(hay, pat):
    # Wzorzec przychodzi juz bez ogonkow (robi to kod), kolumne rozogonkowuje SQL.
    return _norm(pat).replace("%", "") in _bez(_norm(hay))


def fetchall(sql, params=None):
    p = list(params or ())
    if "FROM sales_pipeline" not in sql:
        return []
    out = []
    for r in LEJEK:
        trafil = False
        for war, wart in zip(_warunki(sql), p):
            if war == "nazwa" and _like(r["prospect_name"], wart):
                trafil = True
            elif war == "url" and r.get("prospect_url") and _like(r["prospect_url"], wart):
                trafil = True
            elif war == "mail" and r.get("contact_email") and _norm(r["contact_email"]) == _norm(wart):
                trafil = True
        if trafil:
            out.append(dict(r))
    return out


def _warunki(sql):
    """Kolejnosc warunkow w zapytaniu - odwzorowuje ja kolejnosc parametrow."""
    ws = []
    for kawalek in sql.split(" OR "):
        if "translate(prospect_name" in kawalek:
            ws.append("nazwa")
        elif "prospect_url" in kawalek:
            ws.append("url")
        elif "contact_email" in kawalek:
            ws.append("mail")
    return ws


def fetchone(sql, params=None):
    p = list(params or ())
    if "INSERT INTO sales_pipeline" in sql:
        LICZNIK[0] += 1
        row = {"id": f"nowy-{LICZNIK[0]}", "prospect_name": p[0], "prospect_url": p[1],
               "stage": p[2], "value": p[3], "currency": p[4], "notes": p[5],
               "contact_person": p[6], "contact_email": p[7], "contact_phone": p[8],
               "source": p[9], "updated_at": f"2026-08-19 {LICZNIK[0]:02d}:00"}
        LEJEK.append(row)
        return dict(row)
    return None


def execute(sql, params=None):
    return None


db.fetchall, db.fetchone, db.execute = fetchall, fetchone, execute


def zaloz(**kw):
    """Zwraca (potwierdzenie, blad) - dokladnie jedno z dwoch jest None."""
    try:
        return sales.zaloz_prospekta(**kw), None
    except sales.BladLejka as e:
        return None, str(e)


# ============================================================== FRANCZYZA (najwazniejsze)
print("\n[franczyza] dwa oddzialy tej samej domeny musza przejsc OBA:")

PRZED = len(LEJEK)
ok1, e1 = zaloz(nazwa="Katowice Egurrola Dance Studio", url="https://egurrola.com",
                email="katowice@egurrola.com", telefon="500 100 200")
check("oddzial Katowice PRZESZEDL mimo wiersza Grodzisk na tej samej domenie", ok1 is not None, str(e1))

ok2, e2 = zaloz(nazwa="Warszawa Egurrola Dance Studio", url="https://egurrola.com",
                email="warszawa@egurrola.com")
check("oddzial Warszawa PRZESZEDL mimo DWOCH wierszy na tej samej domenie", ok2 is not None, str(e2))

check("w lejku stoja teraz TRZY oddzialy Egurroli, nie jeden",
      len([r for r in LEJEK if "gurrola" in r["prospect_name"]]) == 3,
      str([r["prospect_name"] for r in LEJEK if "gurrola" in r["prospect_name"]]))
check("oba nowe wiersze maja WLASNY identyfikator", len(LEJEK) == PRZED + 2, f"{len(LEJEK)} != {PRZED + 2}")
check("potwierdzenie podaje id nowego wiersza", ok1 and "id nowy-1" in ok1, str(ok1))
check("potwierdzenie mowi, ile wierszy obejrzala bramka", ok1 and "obejrzala" in ok1, str(ok1))
check("potwierdzenie konczy sie konkretnym nastepnym dzialaniem",
      ok1 and "pipeline_move" in ok1, str(ok1))

# ================================================================= SCIEZKA ALARMU: duplikat
print("\n[alarm] proba zalozenia duplikatu:")

PRZED = len(LEJEK)
ok, e = zaloz(nazwa="Egurrola Dance Studio Katowice", url="http://www.egurrola.com/kontakt",
              telefon="500 100 200", email="nowy.adres@egurrola.com", osoba="Anna Nowak")
check("ta sama nazwa w innej kolejnosci slow ZOSTALA odrzucona", ok is None, str(ok))
check("odrzucenie mowi wprost, ze nic nie zapisano", e and "NIC nie zapisalem" in e, str(e))
check("odrzucenie podaje NAZWE wiersza uznanego za ten sam",
      e and "Katowice Egurrola Dance Studio" in e, str(e))
check("odrzucenie podaje IDENTYFIKATOR tego wiersza", e and "nowy-1" in e, str(e))
check("odrzucenie podaje POWOD (ta sama domena)", e and "ta sama domena egurrola.com" in e, str(e))
check("nic nie doszlo do lejka", len(LEJEK) == PRZED, f"{len(LEJEK)} != {PRZED}")

# AP-311: duplikat nie jest smieciem. Osoba i drugi mail nie moga zniknac razem z odrzuceniem.
check("odrzucenie wylicza, co NOWEGO wnosil wpis", e and "Nowe dane" in e, str(e))
check("wsrod nowych danych jest osoba, ktorej tamten wiersz nie ma",
      e and "osoba: Anna Nowak" in e, str(e))
check("odrzucenie mowi, co sie stanie, jesli te dane porzucic",
      e and "przepadna" in e, str(e))
check("odrzucenie daje DROGE dalej (pipeline_move do konkretnego wiersza)",
      e and "pipeline_move do wiersza nowy-1" in e, str(e))

# Ten sam mail = ten sam podmiot, niezaleznie od nazwy.
ok, e = zaloz(nazwa="EDS Katowice", url="https://egurrola.com", email="katowice@egurrola.com")
check("ten sam adres mailowy zatrzymuje mimo innej nazwy", ok is None, str(ok))
check("powodem jest wprost adres mailowy", e and "ten sam adres mailowy" in e, str(e))

# ======================================================== SCIEZKA ALARMU: AP-313, ogonek w srodku
print("\n[alarm][AP-313] polska nazwa wlasna z ogonkiem W SRODKU:")

PRZED = len(LEJEK)
ok, e = zaloz(nazwa="Grupa Chwalinski", url="https://grupachwalinski.pl",
              telefon="77 400 50 60")
check("nazwa BEZ ogonka trafila w wiersz Z ogonkiem", ok is None, str(ok))
check("odrzucenie pokazuje nazwe tak, jak stoi w bazie (z ogonkiem)",
      e and "Grupa Chwaliński" in e, str(e))
check("nic nie doszlo do lejka", len(LEJEK) == PRZED, f"{len(LEJEK)} != {PRZED}")
check("telefon, ktorego tamten wiersz nie ma, zostal wyliczony",
      e and "telefon: 77 400 50 60" in e, str(e))

# Sedno anty-wzorca: "Chwalin" NIE WYSTEPUJE w slowie "Chwaliński" (C-h-w-a-l-i-ń-s-k-i,
# nie ma tam zwyklego "n"). Bramka szukajaca po surowym napisie przepuscilaby duplikat.
check("fragment, ktory zawodzil w surowym SQL, dzis trafia",
      "Chwaliński" in (zaloz(nazwa="Chwalinski Serwis Opole",
                            url="https://grupachwalinski.pl")[1] or ""), "")

# I odwrotnie: nazwa Z ogonkiem podana do wiersza, ktory ogonek ma - tez ma trafic.
ok, e = zaloz(nazwa="Grupa Chwaliński", url="https://grupachwalinski.pl")
check("pisownia z ogonkiem tez trafia", ok is None, str(ok))
check("gdy wpis nie wnosi nic nowego, bramka mowi to WPROST",
      e and "nie wnosi nic" in e, str(e))

# =========================================================== SCIEZKA ALARMU: niepewnosc
print("\n[alarm] przy niepewnosci bramka pada ZAMKNIETA, nie otwarta:")

PRZED = len(LEJEK)
ok, e = zaloz(nazwa="Egurrola Dance Studio", url="https://egurrola.com")
check("nazwa zawierajaca sie w innej NIE zaklada wiersza", ok is None, str(ok))
check("bramka mowi, ze nie umie rozstrzygnac", e and "Nie umiem rozstrzygnac" in e, str(e))
check("bramka podpowiada pole oddzial jako droge wyjscia", e and "oddzial" in e, str(e))

ok, e = zaloz(nazwa="Katowice Egurola Dance Studio", url="https://egurrola.com")
check("literowka w nazwie marki zatrzymuje (Egurola kontra Egurrola)", ok is None, str(ok))
check("powodem jest wprost literowka", e and "literowk" in e, str(e))

ok, e = zaloz(nazwa="Studio Tanca StandART", url="https://standart-taniec.pl")
check("ta sama nazwa przy innej domenie zatrzymuje zamiast dublowac", ok is None, str(ok))

check("zadna z prob niepewnych nic nie zapisala", len(LEJEK) == PRZED, f"{len(LEJEK)} != {PRZED}")

# Bramka NIE moze padac zamknieta na wszystkim - to byloby zabezpieczenie bezuzyteczne.
ok, e = zaloz(nazwa="Rafal Petrykowski", osoba="Rafal Petrykowski",
              notatka="Kontakt pierwszego stopnia na LinkedInie, rozmowe odwrocil Tomasz.")
check("prospekt niepodobny do niczego w lejku PRZECHODZI", ok is not None, str(e))
check("zdarzenie zrodlowe D-021 ma wreszcie gdzie wyladowac",
      any(r["prospect_name"] == "Rafal Petrykowski" for r in LEJEK))

# Dwa rozne podmioty BEZ domeny po obu stronach: pusta domena nie moze udawac zgodnosci
# (porownanie z pustka przepuszcza albo blokuje po cichu - AP-314 punkt 2).
ok, e = zaloz(nazwa="Klub Fala Gdynia", email="kontakt@fala.example")
check("dwa podmioty bez domeny nie sklejaja sie w jeden", ok is not None, str(e))

# =============================================== droga wyjscia, ktora obiecuje komunikat odmowy
print("\n[oddzial wprost] nazwany wyroznik otwiera bramke, ktora sam domysl zostawia zamknieta:")

# To samo wolanie co wyzej ("Egurrola Dance Studio" na tej samej domenie) bylo odrzucone jako
# niepewne. Rozni je JEDNO pole: czlowiek nazwal oddzial. Bramka ma wtedy zalozyc wiersz,
# bo wyroznik przestal byc domyslem.
PRZED = len(LEJEK)
ok3, e3 = zaloz(nazwa="Egurrola Dance Studio", oddzial="Krakow", email="krakow@egurrola.com")
check("nazwany oddzial przechodzi tam, gdzie sam domysl nie przeszedl", ok3 is not None, str(e3))
check("wiersz doszedl", len(LEJEK) == PRZED + 1, f"{len(LEJEK)} != {PRZED + 1}")

# Ale nazwany oddzial NIE jest wytrychem: jesli stoi w nazwie tamtego wiersza, to duplikat.
ok, e = zaloz(nazwa="Egurrola Dance Studio", oddzial="Katowice", url="https://egurrola.com")
check("nazwany oddzial, ktory stoi w nazwie tamtego wiersza, to nadal duplikat", ok is None, str(ok))
check("powod nazywa to wprost", e and "stoi w nazwie tamtego wiersza" in e, str(e))

# ================================================================ AP-317: zobaczone kontra domysl
print("\n[AP-317] wpis rozroznia ZOBACZONE od WYWNIOSKOWANEGO:")

wiersz_katowice = next(r for r in LEJEK if r["prospect_name"] == "Katowice Egurrola Dance Studio")
check("oddzial wywnioskowany jest NAZWANY wprost w notatce",
      "WYWNIOSKOWANY" in (wiersz_katowice["notes"] or ""), str(wiersz_katowice["notes"]))
# "miasto: X" czyta jako FAKT bramka importu prospektow. Domysl nie ma prawa tam wejsc.
check("domyslu NIE zapisano pod etykieta, ktora automat czyta jako fakt",
      "miasto:" not in (wiersz_katowice["notes"] or ""), str(wiersz_katowice["notes"]))
check("potwierdzenie tez mowi, ze oddzial jest wywnioskowany",
      ok1 and "WYWNIOSKOWANY" in ok1, str(ok1))

wiersz_krakow = next(r for r in LEJEK if r["source"] == "lacznik"
                     and "Krakow" in (r["notes"] or ""))
check("oddzial podany wprost jest ZAOBSERWOWANY", "ZAOBSERWOWANY" in wiersz_krakow["notes"],
      wiersz_krakow["notes"])
check("dopiero wtedy laduje jako miasto (etykieta, ktora czyta automat)",
      "miasto: Krakow" in wiersz_krakow["notes"], wiersz_krakow["notes"])
check("wiersz niesie zrodlo, z ktorego przyszedl", wiersz_krakow["source"] == "lacznik",
      str(wiersz_krakow["source"]))
check("notatka czlowieka zostaje PIERWSZA linia (czyta ja podpowiedz tozsamosci)",
      next(r for r in LEJEK if r["prospect_name"] == "Rafal Petrykowski")["notes"]
      .startswith("Kontakt pierwszego stopnia"))

# ======================================================================== kontrakt wejscia
print("\n[kontrakt] zly wsad nie przechodzi:")

PRZED = len(LEJEK)
ok, e = zaloz(nazwa="   ")
check("pusta nazwa odrzucona", ok is None and e is not None, str(ok))
ok, e = zaloz(nazwa="Nowy Klub", etap="wyslane_moze")
check("nieznany etap odrzucony zamiast cichej podmiany na domyslny", ok is None, str(ok))
check("blad podaje doslownie wartosc, ktorej nie zna", e and "wyslane_moze" in e, str(e))
check("blad wylicza etapy dozwolone", e and "qualified" in e, str(e))
check("zaden zly wsad nic nie zapisal", len(LEJEK) == PRZED, f"{len(LEJEK)} != {PRZED}")

ok, e = zaloz(nazwa="Nowy Klub Ursynow", etap="qualified", oddzial="")
check("pusty ciag znaczy BRAK, a nie wartosc (kontrakt n8n)", ok is not None, str(e))
check("etap podany wprost zostal zapisany",
      next(r for r in LEJEK if r["prospect_name"] == "Nowy Klub Ursynow")["stage"] == "qualified")

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
