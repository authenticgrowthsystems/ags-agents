"""Test (22/08/2026): komenda z sufiksem '@nazwabota' trafia tam, gdzie bez sufiksu.

POWOD: rozmowa z botem przenosi sie z czatu prywatnego do SUPERGRUPY z watkami. W grupie
klient Telegrama dokleja do komendy nazwe bota - tap w menu wysyla '/karty@AGSbot', a przy
wielu botach w grupie sufiks jest WYMAGANY. Wzorce komend w tym repo sa zakotwiczone na '$',
wiec z sufiksem przestaja pasowac. Wiadomosc nie ginie: leci do LLM, ktory ja grzecznie
kwituje. Komenda nie dziala, ale COS odpowiada, wiec czlowiek nie widzi awarii - to rodzina
AP-306/AP-310/AP-315 ("cisza wyglada jak sukces"), tylko z gadatliwym objawem.

Ten test pilnuje TRZECH rzeczy naraz:
  1. SCIEZKA ALARMU - kazda rodzina komend z sufiksem MUSI trafic.
  2. REGRESJA - te same komendy bez sufiksu dzialaja jak dotad (czat prywatny sie nie zmienia),
     a zwykly tekst ('karty sa fajne') NIE jest lapany jako komenda.
  3. BRAMKA NA PRZYSZLOSC - statyczny skan zrodel. Siodma komenda dopisana bez sufiksu
     zapala sie tutaj sama, bez dopisywania przypadku recznie (AP-309: ta sama wada
     odrastala w kolejnych miejscach, bo naprawiano ja punktowo).

Stdlib only. Uruchomienie z KORZENIA repo: python -X utf8 cm-agent/tests/test_sufiks_bota_w_grupie.py"""
import datetime as _dt
import pathlib
import re
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

from app import brands_ui, conversation, sales  # noqa: E402

BOT = "AGSbot"
FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# (etykieta rodziny, dopasowywacz, komenda bez sufiksu, opcjonalny argument)
# Dopasowywacz zwraca cokolwiek prawdziwego, gdy komenda zostala rozpoznana.
RODZINY = [
    ("plan",               conversation._PREVIEW_RE.match, "/plan", ""),
    ("kolejka",            conversation._PREVIEW_RE.match, "/kolejka", ""),
    ("schowek",            conversation._SCHOWEK_RE.match, "/schowek", ""),
    ("karty",              conversation._KARTY_RE.match, "/karty", ""),
    ("karty + dzien",      conversation._KARTY_RE.match, "/karty", "jutro"),
    ("decyzje",            conversation._DECYZJE_RE.match, "/decyzje", ""),
    ("cancel",             conversation._CANCEL_RE.match, "/cancel", ""),
    ("kontekst",           conversation._KONTEKST_RE.match, "/kontekst", ""),
    ("kontekst + kanal",   conversation._KONTEKST_RE.match, "/kontekst", "linkedin"),
    ("brands",             brands_ui._CMD_RE.match, "/brands", ""),
    ("brand_on",           brands_ui._CMD_RE.match, "/brand_on", "AGS"),
    ("brand_off",          brands_ui._CMD_RE.match, "/brand_off", "AGS"),
    ("brand_add",          brands_ui._CMD_RE.match, "/brand_add", "TNM"),
    ("brand_remove",       brands_ui._CMD_RE.match, "/brand_remove", "TNM"),
    ("brand_config",       brands_ui._CMD_RE.match, "/brand_config", "AGS"),
    ("brand_export",       brands_ui._CMD_RE.match, "/brand_export", "AGS"),
    ("prospect",           sales._PROSPECT_RE.match, "/prospect", "Adamietz"),
    ("dziennik",           sales._DZIENNIK_RE.match, "/dziennik", "Adamietz"),
    ("pipeline",           sales._PIPELINE_RE.match, "/pipeline", ""),
    ("oferta",             sales._OFERTA_RE.match, "/oferta", "Adamietz"),
    ("add_sales_material", sales._ADDMAT_RE.match, "/add_sales_material", "ksiazka Hormozi"),
    ("anuluj material",    sales._ANULUJ_RE.match, "/anuluj", ""),
    ("cancel material",    sales._ANULUJ_RE.match, "/cancel", ""),
]

print("[alarm] komenda z sufiksem @nazwabota (tak wyglada tap w menu w GRUPIE):")
for etykieta, dopasuj, cmd, arg in RODZINY:
    tekst = f"{cmd}@{BOT}" + (f" {arg}" if arg else "")
    check(f"{etykieta}: '{tekst}' rozpoznane", bool(dopasuj(tekst)), "poszloby do LLM")

print("\n[regresja] ta sama komenda BEZ sufiksu (czat prywatny ma dzialac jak dotad):")
for etykieta, dopasuj, cmd, arg in RODZINY:
    tekst = cmd + (f" {arg}" if arg else "")
    check(f"{etykieta}: '{tekst}' rozpoznane", bool(dopasuj(tekst)))

print("\n[regresja] argument nie gubi sie przez sufiks:")
m = brands_ui._CMD_RE.match(f"/brand_on@{BOT} AGS")
check("brands_ui: komenda i marka odczytane osobno",
      bool(m) and m.group(1).lower() == "brand_on" and m.group(2) == "AGS",
      str(m.groups() if m else None))
m = conversation._KARTY_RE.match(f"/karty@{BOT} jutro")
check("karty: filtr dnia przezyl sufiks", bool(m) and (m.group(1) or "").lower() == "jutro",
      str(m.groups() if m else None))
m = conversation._KONTEKST_RE.match(f"/kontekst@{BOT} sprzedaz")
check("kontekst: kanal przezyl sufiks", bool(m) and (m.group(1) or "").lower() == "sprzedaz",
      str(m.groups() if m else None))
m = sales._PROSPECT_RE.match(f"/prospect@{BOT} Adamietz Sp. z o.o.")
check("prospect: nazwa firmy przezyla sufiks", bool(m) and m.group(1) == "Adamietz Sp. z o.o.",
      str(m.groups() if m else None))
m = sales._OFERTA_RE.match(f"/oferta@{BOT}")
check("oferta bez argumentu: pusty argument, nie brak dopasowania",
      bool(m) and m.group(1).strip() == "", str(m.groups() if m else None))

print("\n[regresja] wariant slowny bez slasha nadal dziala (Tomasz pisze po ludzku):")
check("'karty' bez slasha", bool(conversation._KARTY_RE.match("karty")))
check("'anuluj' bez slasha", bool(conversation._CANCEL_RE.match("anuluj")))
check("'plan' bez slasha", bool(conversation._PREVIEW_RE.match("plan")))
check("'kontekst' bez slasha", bool(conversation._KONTEKST_RE.match("kontekst")))

print("\n[regresja] zwykly tekst NIE moze byc lapany jako komenda:")
NIE_KOMENDY = [
    ("karty sa fajne", conversation._KARTY_RE.match),
    ("plan na jutro wyglada slabo", conversation._PREVIEW_RE.match),
    ("decyzje zapadly wczoraj", conversation._DECYZJE_RE.match),
    ("anuluj to spotkanie", conversation._CANCEL_RE.match),
    ("kontekst tej rozmowy jest inny", conversation._KONTEKST_RE.match),
    ("/kartyzator", conversation._KARTY_RE.match),
    ("/brandsy", brands_ui._CMD_RE.match),
    ("/pipeline_extra", sales._PIPELINE_RE.match),
    ("anulujemy", sales._ANULUJ_RE.match),
]
for tekst, dopasuj in NIE_KOMENDY:
    check(f"'{tekst}' NIE jest komenda", not dopasuj(tekst), "zlapane jako komenda")

# Sufiks to nazwa bota, a nie dowolny ogon: '/karty@' ani '/karty@AGS bot' nie moga przejsc.
print("\n[regresja] sufiks musi wygladac jak nazwa bota:")
check("'/karty@' odrzucone", not conversation._KARTY_RE.match("/karty@"))
check("'/brands@' odrzucone", not brands_ui._CMD_RE.match("/brands@"))

# ---------------------------------------------------------------------------
# BRAMKA NA PRZYSZLOSC (AP-309). Ta sama wada zyla dalej w szesciu miejscach, bo poprzednia
# naprawa byla punktowa. Skan zrodel lapie SIODMA komende dopisana bez sufiksu.
print("\n[bramka] statyczny skan zrodel - kazda komenda ze slashem ma '(?:@\\w+)?':")
_SUFIKS = "(?:@\\w+)?"
# Wzorce, ktore NIE sa dopasowywaczami komend Telegrama (data, sciezka, identyfikator, fraza PL).
_POMIN = {"_KPI_DATE_ISO", "_KPI_DATE_PL", "_DATE_RE", "_KATALOG_OK", "_UUID", "_OP_ID",
          "_MD_MARK_RE", "_FENCE", "_META_ZAPOWIEDZ", "_WKLEJONE_RE", "_WYSZLO_RE",
          "_USTAW_OKNO_RE", "_USTAW_KEY_RE", "_PREFIKS_AGENTA_RE", "_ZRZUT_DO_SPRZEDAWCY_RE",
          "_INSTRUCTION_RE"}
_PRZYPISANIE = re.compile(r"^(_[A-Z_0-9]+)\s*=\s*re\.compile\(", re.MULTILINE)
# Sklejamy TYLKO literaly napisow, wiec komentarze i flagi (re.IGNORECASE) nie trafiaja do skanu
# i odtwarzamy prawdziwe zrodlo wzorca, takze rozbitego na kilka linii przez konkatenacje.
_LITERAL = re.compile(r'r?"((?:[^"\\]|\\.)*)"')


def _cialo_wywolania(zrodlo, i):
    """Wycina argumenty re.compile( ... ) liczac nawiasy POZA napisami. Ciecie na pustej linii
    nie wystarcza: kolejne wzorce stoja tu linia pod linia i pierwszy zjadalby nastepne."""
    glebokosc, w_napisie, ucieczka = 1, False, False
    for j in range(i, len(zrodlo)):
        c = zrodlo[j]
        if ucieczka:
            ucieczka = False
            continue
        if c == "\\":
            ucieczka = True
        elif c == '"':
            w_napisie = not w_napisie
        elif not w_napisie:
            if c == "(":
                glebokosc += 1
            elif c == ")":
                glebokosc -= 1
                if glebokosc == 0:
                    return zrodlo[i:j]
    return zrodlo[i:i + 1200]


def _zjedz_token(cialo, i):
    """Zwraca pozycje ZA nazwa komendy zaczynajaca sie na cialo[i] ('/' juz skonsumowany)
    albo None, gdy w tym miejscu nie ma komendy. Obsluguje dwie formy z tego repo:
    goly wyraz ('/karty') i grupe alternatyw ('/(brands|brand_on|...)')."""
    if i < len(cialo) and cialo[i] == "(":
        glebokosc = 0
        for j in range(i, len(cialo)):
            if cialo[j] == "(":
                glebokosc += 1
            elif cialo[j] == ")":
                glebokosc -= 1
                if glebokosc == 0:
                    return j + 1
        return None
    k = re.match(r"[a-z_]{2,30}", cialo[i:])
    return i + k.end() if k else None


zbadane = 0
for plik in sorted(BASE.glob("*.py")):
    zrodlo = plik.read_text(encoding="utf-8")
    for dop in _PRZYPISANIE.finditer(zrodlo):
        nazwa = dop.group(1)
        if nazwa in _POMIN:
            continue
        ogon = _cialo_wywolania(zrodlo, dop.end())
        cialo = "".join(m.group(1) for m in _LITERAL.finditer(ogon))
        if "^" not in cialo:
            continue  # wzorzec niezakotwiczony i tak nie ucierpi od sufiksu na koncu komendy
        i = 0
        while True:
            i = cialo.find("/", i)
            if i < 0:
                break
            po = i + 1
            if po < len(cialo) and cialo[po] == "?":  # '/?kontekst' - slash opcjonalny
                po += 1
            koniec = _zjedz_token(cialo, po)
            i += 1
            if koniec is None:
                continue
            token = cialo[po:koniec]
            fragment = cialo[koniec:koniec + len(_SUFIKS)]
            zbadane += 1
            check(f"{plik.name}:{nazwa} komenda /{token[:40]} ma sufiks",
                  fragment == _SUFIKS, f"po '/{token[:40]}' stoi '{fragment}'")

check("skan faktycznie cos przejrzal (pusty skan = falszywa zielen)", zbadane >= 14, str(zbadane))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
