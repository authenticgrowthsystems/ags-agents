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
P3 = "44444444-4444-4444-4444-444444444444"
K1 = "22222222-2222-2222-2222-222222222222"

LEJEK = [
    {"id": P1, "prospect_name": "Studio Tanca StandART", "stage": "prospect",
     "prospect_url": "https://standart.pl", "next_step": None, "next_followup_at": None,
     "offer_tier": None, "value": None, "currency": "PLN", "source": "import", "katalog": None},
    {"id": P2, "prospect_name": "Egurrola Dance Studio Krakow", "stage": "parked",
     "prospect_url": None, "next_step": None, "next_followup_at": None,
     "offer_tier": None, "value": None, "currency": "PLN", "source": "import", "katalog": None},
    # AP-313: nazwa z ogonkiem W SRODKU. Katalog na dysku nazywa sie "Chwalinski" (bez ogonka,
    # taka jest regula), wiec czlowiek wpisze wlasnie tak - i musi trafic.
    {"id": P3, "prospect_name": "Grupa Chwaliński", "stage": "qualified",
     "prospect_url": "https://grupachwalinski.pl", "next_step": None, "next_followup_at": None,
     "offer_tier": None, "value": None, "currency": "PLN", "source": "manual",
     "katalog": "Klienci\\Chwalinski"},
]
KONTAKTY = [
    {"id": K1, "name": "jasonfeifer", "status": "Cold", "email": None, "phone": None,
     "linkedin_url": None, "x_handle": "jasonfeifer", "website": None, "priority": "P3",
     "next_action": None, "next_action_due": None},
]
# Wpis sprzed DDL 036: ma nazwe w author_display, nie ma pipeline_id.
# UWAGA na ksztalt: gotowiec Sprzedawcy trzyma w `content` sama ETYKIETE, a caly mail
# w `response` (sales.py). Tap-test na zywych danych StandART 31/07 pokazal, ze czytanie
# samego `content` wyswietlalo siedem razy etykiete i ANI SLOWA z tresci maili.
LOG = [
    {"created_at": "2026-07-24 10:00", "channel": "Other", "action_type": "other",
     "status": "proposed", "agent": "AGS:sprzedaz",
     "content": "outreach email: Studio Tanca StandART",
     "response": "Dzien dobry, pisze w sprawie zapisow na zajecia - mam pomysl na przedsionek.",
     "notes": "gotowiec outreach", "pipeline_id": None, "contact_id": None,
     "author_display": "Studio Tanca StandART"},
]
ZEGAR = [0]


def _norm(s):
    return " ".join(str(s or "").split()).strip().lower()


def _bez(s):
    """Atrapa SQL-owego translate() z AP-313 - kolumna traci ogonki przed porownaniem."""
    return str(s or "").translate(str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ"))


def _like(hay, pat):
    # Wzorzec przychodzi juz bez ogonkow (robi to kod), kolumne rozogonkowuje SQL.
    return _norm(pat).replace("%", "") in _bez(_norm(hay))


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
    if "FROM sales_pipeline WHERE" in sql and "ILIKE" in sql:
        return [dict(r) for r in LEJEK if _like(r["prospect_name"], p[0])]
    if "FROM contacts WHERE" in sql and "ILIKE" in sql:
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
                    "channel": p[1], "agent": p[2], "content": p[3], "response": None,
                    "notes": p[4], "contact_id": p[5], "pipeline_id": p[6], "status": p[7],
                    "author_display": p[8]})
        return
    if "UPDATE sales_pipeline SET katalog" in sql:
        for r in LEJEK:
            if r["id"] == p[1]:
                r["katalog"] = p[0]
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
check("historia sprzed DDL 036 tez jest widoczna", "outreach email" in t)
check("stary wpis jest PIERWSZY (chronologia, nie kolejnosc wstawiania)",
      t.find("outreach email") < i1)

# Wada zlapana tap-testem na produkcji 31/07: teczka pokazywala ETYKIETE zamiast maila.
check("gotowiec Sprzedawcy pokazuje TRESC MAILA, nie sama etykiete",
      "przedsionek" in t, t[t.find("outreach email"):][:300])
check("etykieta zostaje jako kontekst, cytatem", "> outreach email" in t,
      t[t.find("outreach email") - 20:][:200])
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

# --------------------------------------------------- most miedzy katalogiem a lejkiem (DDL 037)
print("\n[katalog] most do plikow na dysku:")

t0 = teczka.teczka_text("StandART")
check("teczka mowi WPROST, ze katalogu nie ma", "Katalog: BRAK - nie ustalony" in t0, t0[:400])

teczka.zapisz("StandART", "email", "pierwszy kontakt", "sent", katalog="Klienci/StandART")
check("katalog zapisany", LEJEK[0]["katalog"] == "Klienci\\StandART", str(LEJEK[0]["katalog"]))
check("ukosnik zamieniony na windowsowy", "/" not in (LEJEK[0]["katalog"] or ""))
check("teczka pokazuje katalog", "Katalog: Klienci\\StandART" in teczka.teczka_text("StandART"))


def kat(sciezka, ident="StandART"):
    """Wlasna tresc-znacznik, zeby policzyc DOKLADNIE zapisy z tej sekcji."""
    try:
        teczka.zapisz(ident, "email", "PROBA_KATALOGU", "draft", katalog=sciezka)
        return None
    except teczka.Blad as e:
        return str(e)


# Regula Tomasza: ustalane RAZ przy pierwszym kontakcie i NIGDY niezmieniane. Nie jest to
# kosmetyka - system katalogow nie przenosi, wiec podmiana napisu zostawilaby wiersz
# wskazujacy na nieistniejacy folder, czyli dokladnie ten rozjazd, ktoremu most zapobiega.
e = kat("Klienci/StandART_nowy")
check("proba ZMIANY katalogu odrzucona", e is not None, str(e))
check("blad tlumaczy, ze najpierw przenosi sie folder", e and "przenies folder" in e, str(e))
check("stara wartosc NIE zostala nadpisana", LEJEK[0]["katalog"] == "Klienci\\StandART")

check("ta sama wartosc ponownie nie jest bledem", kat("Klienci\\StandART") is None)

e = kat("Klienci/Chwaliński")
check("polskie znaki odrzucone", e is not None and "polskie znaki" in (e or ""), str(e))
check("blad wymienia winny znak", e and "ń" in e, str(e))

e = kat("C:\\Claude-CoWork\\TyNieMusisz\\Klienci\\Egurrola", ident="Egurrola Dance Studio Krakow")
check("sciezka bezwzgledna odrzucona", e is not None and "WZGLEDNA" in (e or ""), str(e))

e = kat("Klienci\\..\\..\\Windows", ident="Egurrola Dance Studio Krakow")
check("wyjscie w gore drzewa odrzucone", e is not None, str(e))

e = kat("Klienci\\Test<>|", ident="Egurrola Dance Studio Krakow")
check("niedozwolone znaki odrzucone", e is not None and "Niedozwolone" in (e or ""), str(e))

e = kat("Klienci\\jasonfeifer", ident="jasonfeifer")
check("katalog przy kontakcie spolecznosciowym odrzucony", e is not None, str(e))
check("blad mowi, ze katalog nalezy do LEJKA", e and "LEJKA" in e, str(e))

# Sedno: walidacja katalogu stoi PRZED zapisem. Szesc odrzuconych prob powyzej nie moze
# zostawic ani jednego wiersza - inaczej czlowiek dostaje blad, ponawia i robi duplikat.
# Pierwsza wersja walidowala PO wstawieniu wiersza; ten test ja na tym zlapal.
zapisow = len([r for r in LOG if r.get("content") == "PROBA_KATALOGU"])
check("szesc odrzuconych prob nie zapisalo NIC, zapisala sie tylko jedna udana",
      zapisow == 1, f"wierszy: {zapisow}, oczekiwano 1")

# ------------------------------------------------------------ AP-313: ogonki w nazwach wlasnych
print("\n[AP-313] nazwa z ogonkiem W SRODKU - most dysk-baza pekal wlasnie tu:")

# Katalog na dysku: "Chwalinski". Wiersz w bazie: "Grupa Chwaliński". Czlowiek wpisuje to,
# co widzi w katalogu. Przed poprawka dostawal "nie znajduje" - czyli komunikat brzmiacy jak
# BRAK KLIENTA, a nie jak usterka wyszukiwania.
t = teczka.teczka_text("Chwalinski")
check("nazwa katalogu (bez ogonka) ZNAJDUJE prospekta z ogonkiem",
      "Grupa Chwaliński" in t, t[:200])
check("teczka pokazuje jego katalog", "Klienci\\Chwalinski" in t, t[:400])

check("pelna nazwa Z ogonkiem tez dziala",
      "Grupa Chwaliński" in teczka.teczka_text("Grupa Chwaliński"))
check("pisownia mieszana tez dziala", "Grupa Chwaliński" in teczka.teczka_text("grupa chwalinski"))

# Sedno anty-wzorca: fragment "Chwalin" NIE ISTNIEJE w slowie "Chwaliński"
# (C-h-w-a-l-i-ń-s-k-i - nie ma tam zwyklego "n"). Po normalizacji obu stron - istnieje.
check("wlasnie ten fragment, ktory zawiodl w SQL, teraz trafia",
      "Grupa Chwaliński" in teczka.teczka_text("Chwalin"))

# Lista podobnych tez musi byc odporna, inaczej podpowiedz przy literowce milczy.
try:
    # Calosc nie pasuje do niczego, ale slowo "Chwalinski" (bez ogonka) musi wskazac
    # "Grupa Chwaliński" (z ogonkiem) - inaczej podpowiedz milczy akurat przy literowce.
    teczka.zapisz("Serwis Chwalinski Katowice", "email", "x", "draft")
    e313 = None
except teczka.Blad as ex:
    e313 = str(ex)
check("lista podobnych znajduje nazwe z ogonkiem po slowie bez ogonka",
      e313 is not None and "Chwaliński" in e313, str(e313))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
