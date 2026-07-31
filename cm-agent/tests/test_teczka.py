"""Test pary zapisz_tekst + teczka (31/07/2026, zadanie Managera).

POWOD: teksty sprzedazowe pisane w Cowork ladowaly wylacznie w czacie. Zero sladu w bazie,
wiec nie dalo sie iterowac, policzyc ani wczytac w nowej rozmowie.

TEST WYMAGANY WPROST: zapisz trzy wpisy dla jednego kontaktu, teczka musi zwrocic je
W KOLEJNOSCI i z poprawnym nastepnym krokiem.

Dodatkowo pilnujemy trzech rzeczy, ktore latwo zepsuc po cichu:
  - nieznany identyfikator NIC nie zapisuje i nie zaklada nowego wiersza (wymog Managera),
  - szkic ma status 'draft', a NIE 'proposed' - inaczej straznik gotowcow zrobilby bramke
    z kazdego maila pisanego w Cowork,
  - historia sprzed DDL 036 (wpis bez pipeline_id, sama nazwa) nadal jest widoczna.

Zegar jest LICZNIKIEM, nie czasem systemowym - D-002 mowi, ze testy zalezne od pory dnia
sa dlugiem, a nie testami. Stdlib only. Uruchomienie: python cm-agent/tests/test_teczka.py"""
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

from app import db, teczka  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ------------------------------------------------------------------ atrapa bazy
P1 = "11111111-1111-1111-1111-111111111111"
P2 = "33333333-3333-3333-3333-333333333333"
K1 = "22222222-2222-2222-2222-222222222222"

LEJEK = [
    {"id": P1, "prospect_name": "Studio Tanca StandART", "stage": "prospect",
     "prospect_url": "https://standart.pl", "next_step": None, "next_followup_at": None,
     "offer_tier": None, "value": None, "currency": "PLN", "source": "import"},
    {"id": P2, "prospect_name": "Egurrola Dance Studio Krakow", "stage": "parked",
     "prospect_url": None, "next_step": None, "next_followup_at": None,
     "offer_tier": None, "value": None, "currency": "PLN", "source": "import"},
]
KONTAKTY = [
    {"id": K1, "name": "jasonfeifer", "status": "Cold", "email": None, "phone": None,
     "linkedin_url": None, "x_handle": "jasonfeifer", "website": None, "priority": "P3",
     "next_action": None, "next_action_due": None},
]
# Wpis sprzed DDL 036: ma nazwe w author_display, nie ma pipeline_id.
LOG = [
    {"created_at": "2026-07-24 10:00", "channel": "Other", "action_type": "other",
     "status": "proposed", "agent": "AGS:sprzedaz", "content": "stary gotowiec Sprzedawcy",
     "notes": "gotowiec outreach", "pipeline_id": None, "contact_id": None,
     "author_display": "Studio Tanca StandART"},
]
ZEGAR = [0]


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def _like(hay, pat):
    return _norm(pat).replace("%", "") in _norm(hay)


def fetchone(sql, params=None):
    p = params or ()
    if "FROM sales_pipeline WHERE id=" in sql:
        return next((dict(r) for r in LEJEK if r["id"] == p[0]), None)
    if "FROM contacts WHERE id=" in sql:
        return next((dict(r) for r in KONTAKTY if r["id"] == p[0]), None)
    return None


def fetchall(sql, params=None):
    p = params or ()
    if "prospect_name AS n" in sql:
        return [{"n": r["prospect_name"], "s": r["stage"]} for r in LEJEK
                if any(_like(r["prospect_name"], x) for x in p)]
    if "SELECT name AS n FROM contacts" in sql:
        return [{"n": r["name"]} for r in KONTAKTY if any(_like(r["name"], x) for x in p)]
    if "FROM sales_pipeline WHERE prospect_name ILIKE" in sql:
        return [dict(r) for r in LEJEK if _like(r["prospect_name"], p[0])]
    if "FROM contacts WHERE name ILIKE" in sql:
        return [dict(r) for r in KONTAKTY if _like(r["name"], p[0])]
    if "FROM engagement_log" in sql and "pipeline_id=" in sql:
        out = [r for r in LOG if r["pipeline_id"] == p[0]
               or (r["pipeline_id"] is None and _norm(r["author_display"]) == _norm(p[1]))]
        return sorted(out, key=lambda r: r["created_at"])
    if "FROM engagement_log WHERE contact_id=" in sql:
        return sorted([r for r in LOG if r["contact_id"] == p[0]], key=lambda r: r["created_at"])
    return []


def execute(sql, params=None):
    p = params or ()
    if "INSERT INTO engagement_log" in sql:
        ZEGAR[0] += 1
        LOG.append({"created_at": f"2026-07-31 12:{ZEGAR[0]:02d}", "action_type": p[0],
                    "channel": p[1], "agent": p[2], "content": p[3], "notes": p[4],
                    "contact_id": p[5], "pipeline_id": p[6], "status": p[7],
                    "author_display": p[8]})
        return
    if "UPDATE sales_pipeline" in sql:
        for r in LEJEK:
            if r["id"] == p[2]:
                r["next_step"] = p[0] if p[0] is not None else r["next_step"]
                r["next_followup_at"] = p[1] if p[1] is not None else r["next_followup_at"]
        return
    if "UPDATE contacts" in sql:
        for r in KONTAKTY:
            if r["id"] == p[2]:
                r["next_action"] = p[0] if p[0] is not None else r["next_action"]
                r["next_action_due"] = p[1] if p[1] is not None else r["next_action_due"]
        return


db.fetchone, db.fetchall, db.execute = fetchone, fetchall, execute


# ------------------------------------------- TEST GLOWNY: trzy wpisy, kolejnosc, nastepny krok
print("\n[glowny] trzy wpisy dla jednego kontaktu:")

teczka.zapisz("StandART", "email", "Pierwszy mail: przedsionek, nie zamiennik zapisow.", "sent")
teczka.zapisz("StandART", "whatsapp", "Drugi: przypominam sie po mailu.", "sent")
teczka.zapisz("StandART", "email", "Trzeci, szkic dogrywki - jeszcze nie wyslany.", "draft",
              next_step="Telefon do wlasciciela", next_step_date="2026-08-04 10:00")

t = teczka.teczka_text("StandART")

i1, i2, i3 = t.find("Pierwszy mail"), t.find("Drugi:"), t.find("Trzeci,")
check("wszystkie trzy wpisy sa w teczce", min(i1, i2, i3) > -1, f"{i1},{i2},{i3}")
check("wpisy sa W KOLEJNOSCI zapisu", i1 < i2 < i3, f"{i1},{i2},{i3}")
check("historia sprzed DDL 036 tez jest widoczna", "stary gotowiec" in t)
check("stary wpis jest PIERWSZY (chronologia, nie kolejnosc wstawiania)",
      t.find("stary gotowiec") < i1)
check("naglowek liczy wszystkie cztery wpisy", "## Historia (4)" in t, t[:400])

check("nastepny krok ma TRESC", "Telefon do wlasciciela" in t, t)
check("nastepny krok ma TERMIN", "2026-08-04" in t, t)
check("kanaly sa rozroznione", "WhatsApp" in t and "Email" in t, t)
check("statusy sa widoczne", "draft" in t and "sent" in t, t)
check("teczka mowi, ze to prospekt z LEJKA", "(lejek," in t, t[:200])
check("teczka pokazuje etap", "Etap: prospect" in t, t[:400])

print("\n[status] szkic NIE moze byc 'proposed' - inaczej obudzi straznika gotowcow:")
nowe = [r for r in LOG if r["agent"] == "AGS:manager"]
check("trzy nowe wpisy zapisane", len(nowe) == 3, str(len(nowe)))
check("zaden nowy wpis nie ma statusu 'proposed'",
      not [r for r in nowe if r["status"] == "proposed"], str([r["status"] for r in nowe]))
check("szkic ma status 'draft'", nowe[2]["status"] == "draft", nowe[2]["status"])
check("wpisy wisza na pipeline_id, nie na napisie",
      all(r["pipeline_id"] == P1 for r in nowe), str([r["pipeline_id"] for r in nowe]))

print("\n[pusta teczka] brak nastepnego kroku musi byc WIDOCZNY, nie pusty:")
pusta = teczka.teczka_text("jasonfeifer")
check("kontakt bez historii mowi to wprost", "Teczka pusta" in pusta, pusta)
check("brak nastepnego kroku jest nazwany", "BRAK ustalonego nastepnego kroku" in pusta, pusta)
check("teczka mowi, ze to KONTAKT, nie prospekt", "(kontakt," in pusta, pusta[:200])


# ------------------------------------------------------- identyfikator, ktory nie istnieje
print("\n[nieznany] blad z lista podobnych, zero cichego zakladania:")
PRZED = len(LOG)


def blad(ident, kanal="email", tresc="tresc"):
    try:
        teczka.zapisz(ident, kanal, tresc, "draft")
        return None
    except teczka.Blad as e:
        return str(e)


e = blad("Szkola Tanca Rytm Wroclaw")
check("nieznana nazwa daje blad", e is not None)
check("blad mowi wprost, ze NIC nie zapisano", e and "NIC nie zapisalem" in e, str(e))
check("blad podaje liste podobnych", e and "Podobne nazwy" in e, str(e))
# "Szkola Tanca Rytm Wroclaw" nie pasuje w calosci do niczego, ale slowo "Tanca" pasuje do
# "Studio Tanca StandART" - to jest sens listy podobnych: podpowiedziec, a nie wzruszyc ramionami.
check("podobne znalezione po POJEDYNCZYM slowie", e and "Studio Tanca StandART" in e, str(e))
check("nic nie doszlo do bazy", len(LOG) == PRZED, f"{len(LOG)} != {PRZED}")

e = blad("00000000-0000-0000-0000-000000000000")
check("nieznany UUID daje blad", e is not None)
check("blad podpowiada, zeby podac nazwe", e and "fragment nazwy" in e, str(e))
check("nadal nic nie doszlo do bazy", len(LOG) == PRZED, f"{len(LOG)} != {PRZED}")

e = blad("Studio")
check("wieloznaczna nazwa daje blad zamiast losowego trafienia", e is not None, str(e))
check("blad wylicza kandydatow", e and "StandART" in e and "Egurrola" in e, str(e))
check("wieloznacznosc tez nic nie zapisuje", len(LOG) == PRZED, f"{len(LOG)} != {PRZED}")

e = blad("Egurrola Dance Studio Krakow")
check("pelna nazwa rozstrzyga wieloznacznosc (franczyzy)", e is None, str(e))
check("po rozstrzygnieciu wpis doszedl", len(LOG) == PRZED + 1)

print("\n[kontrakt] kanal i status spoza slownika nie przechodza:")
check("nieznany kanal odrzucony", blad("StandART", kanal="golab") is not None)
check("pusta tresc odrzucona", blad("StandART", tresc="   ") is not None)
try:
    teczka.zapisz("StandART", "email", "x", "wyslane_moze")
    check("nieznany status odrzucony", False, "przeszedl")
except teczka.Blad:
    check("nieznany status odrzucony", True)

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
