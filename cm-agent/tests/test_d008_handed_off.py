# -*- coding: utf-8 -*-
"""Test D-008 (03/08/2026): stara nazwa stanu materialu NIE WRACA - ani do kodu, ani do DDL.

POWOD. `content_items.status='dispatching'` brzmialo jak stan PRZELOTNY ("wysylam"), a znaczy
"rozeslane do kolejki, czekam az wszystkie wiersze serii przestana sie ruszac" - czyli stan,
ktory normalnie trwa DNI. 27/07 Manager zglosil zawieszony post; odczyt pokazal siedem
materialow, WSZYSTKIE ZDROWE, najstarszy 51 godzin i poprawnie. To AP-312.

DLACZEGO TEN TEST JEST TRUDNIEJSZY, NIZ WYGLADA. Ten sam napis 'dispatching' zyje w DWOCH
ROZLACZNYCH slownikach:

  content_items.status = 'dispatching'  -> PRZEMIANOWANE na 'handed_off'   (D-008)
  post_queue.status    = 'dispatching'  -> ZOSTAJE BEZ ZMIAN               (osobna sprawa)

Zywy wezel n8n "AGS Scheduler v1" ma OBIE naraz w JEDNYM zapytaniu. Dlatego ten test pilnuje
w obie strony: ze stara wartosc nie wrocila do materialu ORAZ ze nie zostala wycieta z kolejki.
Podmiana "po calym pliku" wywala go tak samo jak cofniecie poprawki.

Stdlib only. Uruchomienie: python cm-agent/tests/test_d008_handed_off.py"""
import datetime as _dt
import pathlib
import re
import sys
import types
import zoneinfo as _zi

# Ta sama proteza, co w test_stan_rozsylki: Windows bez pakietu `tzdata` nie zna stref IANA,
# a moduly aplikacji budują ZoneInfo("Europe/Warsaw") juz przy imporcie. Test nie dotyka czasu.
try:
    _zi.ZoneInfo("Europe/Warsaw")
except Exception:
    _zi.ZoneInfo = lambda key: _dt.timezone(_dt.timedelta(hours=2), key)

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"
DB = BASE / "db"

STARA = "dispatching"
NOWA = "handed_off"

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- import app
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
_stub("fastapi", FastAPI=_Any, Request=_Any, BackgroundTasks=_Any, Body=lambda *a, **k: None)
_stub("uvicorn", run=lambda *a, **k: None)
_stub("openpyxl", load_workbook=lambda *a, **k: _Any())

pkg = types.ModuleType("app")
pkg.__path__ = [str(APP)]
sys.modules["app"] = pkg

from app import config, matreview, slots, proactive  # noqa: E402

# ---------------------------------------------------------------- 1. stala
print("\n[stala] jedno zrodlo nazwy, nie literal w dwudziestu miejscach:")
check("config.STATUS_HANDED_OFF istnieje i ma nowa wartosc",
      getattr(config, "STATUS_HANDED_OFF", None) == NOWA,
      repr(getattr(config, "STATUS_HANDED_OFF", None)))
check("stan rozsylki NIE jest na liscie stanow, ktore petla sama przesuwa "
      "(item czeka na callback, nie ma byc przechwycony ponownie)",
      NOWA not in config.ACTIONABLE_STATUSES and STARA not in config.ACTIONABLE_STATUSES,
      str(config.ACTIONABLE_STATUSES))

# ---------------------------------------------------------------- 2. slowniki w pamieci
print("\n[slowniki materialu] znaja NOWA wartosc i NIE znaja starej:")
check("matreview._VIEW_STATUS_PL ma klucz nowej wartosci",
      NOWA in matreview._VIEW_STATUS_PL, str(list(matreview._VIEW_STATUS_PL)))
check("matreview._VIEW_STATUS_PL nie ma juz klucza starej wartosci",
      STARA not in matreview._VIEW_STATUS_PL, str(list(matreview._VIEW_STATUS_PL)))
check("slots.BUSY_STATUSES przeszlo na nowa wartosc",
      NOWA in slots.BUSY_STATUSES and STARA not in slots.BUSY_STATUSES,
      str(slots.BUSY_STATUSES))
check("proactive.ACTIVE_FOR_SLOTS przeszlo na nowa wartosc",
      NOWA in proactive.ACTIVE_FOR_SLOTS and STARA not in proactive.ACTIVE_FOR_SLOTS,
      str(proactive.ACTIVE_FOR_SLOTS))

# ---------------------------------------------------------------- 3. slowniki KOLEJKI nietkniete
print("\n[slowniki kolejki] stara wartosc ma tu ZOSTAC - to inny slownik:")
check("matreview._PQ_CZEKA nadal zna 'dispatching' (stan wiersza post_queue)",
      STARA in matreview._PQ_CZEKA, str(matreview._PQ_CZEKA))
check("matreview._PQ_CZEKA NIE dostalo nowej wartosci przez pomylke",
      NOWA not in matreview._PQ_CZEKA, str(matreview._PQ_CZEKA))

# ---------------------------------------------------------------- 4. zrodla: AP-309
# Sedno: nie ufamy pamieci ani jednemu grepowi - kazde wystapienie starej wartosci W KODZIE
# (nie w komentarzu) musi byc na liscie znanych miejsc post_queue. Nowe wystapienie gdziekolwiek
# indziej wywala test, nawet jesli ktos "tylko dopisal jedno zapytanie".
# Listy, nie zbiory - dwie trasy w conversation.py maja DOSLOWNIE te sama linie i licza sie
# osobno. Zbior zjadlby ten duplikat i test przepuscilby usuniecie jednej z dwoch tras.
DOZWOLONE_PQ = {
    "channels.py": [
        "writes back post_queue 'published' + an agent_messages RESPONSE, "
        "so CM just fires + marks 'dispatching'.\"\"\"",
        'db.execute("UPDATE post_queue SET status=\'dispatching\' WHERE id=%s", (row["id"],))',
    ],
    "conversation.py": [
        "WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued','dispatching')\"\"\",",
        "WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued','dispatching')\"\"\",",
        "WHERE brand=%s AND platform=%s AND status IN ('review','scheduled','queued','held','dispatching')",
    ],
    "matreview.py": [
        '_PQ_CZEKA = ("review", "held", "scheduled", "queued", "dispatching")',
    ],
    "reports.py": [
        '"dispatching": "w wysylce"}.get(st, st)',
    ],
    "slots.py": [
        "WHERE brand=%s AND platform=%s AND status IN ('review','scheduled','queued','dispatching')",
        "AND status IN ('review','held','scheduled','queued','dispatching')\"\"\",",
    ],
    "worker.py": [
        '_DISPATCH_PENDING = ("review", "dispatching", "scheduled", "queued")',
    ],
}

print("\n[zrodla] kazde pozostale 'dispatching' w kodzie nalezy do KOLEJKI:")
komentarz = re.compile(r"^\s*#")
znalezione = {}
nieznane = []
for plik in sorted(APP.glob("*.py")):
    dozwolone = {_norm(x) for x in DOZWOLONE_PQ.get(plik.name, [])}
    for i, linia in enumerate(plik.read_text(encoding="utf-8").splitlines(), 1):
        if STARA not in linia or komentarz.match(linia):
            continue
        znalezione[plik.name] = znalezione.get(plik.name, 0) + 1
        if _norm(linia) not in dozwolone:
            nieznane.append(f"{plik.name}:{i}: {_norm(linia)[:90]}")

check("zero NIEZNANYCH wystapien starej wartosci w cm-agent/app/",
      not nieznane, " | ".join(nieznane) or "-")

# Kontrola w DRUGA strone, per plik. Gdyby ktos wyciol slownik kolejki razem z materialem,
# petla wyzej nic by nie zauwazyla - brak trafien to tez "zero nieznanych". Liczymy wiec jawnie
# i osobno dla kazdego pliku, zeby ubytek w jednym nie zostal przykryty nadmiarem w drugim.
print("\n[zrodla] slownik post_queue ma komplet miejsc (nikt go nie zmigrowal przy okazji):")
for nazwa, linie in sorted(DOZWOLONE_PQ.items()):
    check(f"{nazwa}: {len(linie)} wystapien kolejki",
          znalezione.get(nazwa, 0) == len(linie), f"jest {znalezione.get(nazwa, 0)}")

print("\n[zrodla] stara wartosc nie stoi juz w zadnym zapytaniu o content_items:")
zle = []
for plik in sorted(APP.glob("*.py")):
    tresc = plik.read_text(encoding="utf-8")
    for i, linia in enumerate(tresc.splitlines(), 1):
        if "content_items" in linia and STARA in linia and not komentarz.match(linia):
            zle.append(f"{plik.name}:{i}")
check("zero linii laczacych content_items ze stara wartoscia", not zle, " | ".join(zle) or "-")

print("\n[zrodla] jedyny pisarz i jedyny czytelnik ida przez stala:")
worker_src = (APP / "worker.py").read_text(encoding="utf-8")
check("worker zapisuje stan przez config.STATUS_HANDED_OFF, nie przez literal",
      "db.set_item_status(item[\"id\"], config.STATUS_HANDED_OFF)" in worker_src)
check("reconcile_publications wybiera materialy PARAMETREM, nie wklejonym napisem",
      "WHERE status=%s" in worker_src and "(config.STATUS_HANDED_OFF,)" in worker_src)

# ---------------------------------------------------------------- 5. DDL
print("\n[DDL] ograniczenie CHECK zna nowa wartosc we wszystkich plikach schematu:")
DDL_Z_CHECKIEM = ["001_init.sql", "003_brain_phase1.sql", "010_notion_ssot.sql",
                  "042_status_handed_off.sql"]
for nazwa in DDL_Z_CHECKIEM:
    p = DB / nazwa
    tresc = p.read_text(encoding="utf-8") if p.exists() else ""
    check(f"{nazwa}: istnieje i zna '{NOWA}'", bool(tresc) and f"'{NOWA}'" in tresc)

# Stara wartosc w CHECK-ach jest dzis DOZWOLONA i CELOWA - to droga odwrotu na czas okna.
# Znika w osobnym oknie (docs/ops/SQL_d008b_sprzatanie_check_PO_OKNIE.sql). Test pilnuje tylko,
# zeby ten plik sprzatajacy istnial - inaczej "przejsciowe" zostaje na zawsze.
sprzatanie = BASE.parent / "docs" / "ops" / "SQL_d008b_sprzatanie_check_PO_OKNIE.sql"
check("plik sprzatajacy CHECK istnieje (inaczej 'przejsciowo' znaczy 'na zawsze')",
      sprzatanie.exists(), str(sprzatanie))

migracja = BASE.parent / "docs" / "ops" / "SQL_d008_handed_off_03082026.sql"
check("migracja danych ma BRAMKE na liczbie wierszy (runbook punkt 4)",
      migracja.exists() and "RAISE EXCEPTION" in migracja.read_text(encoding="utf-8"))
check("migracja ma SQL odwrotny w tym samym pliku (runbook punkt 7)",
      migracja.exists()
      and "UPDATE content_items SET status = 'dispatching'" in migracja.read_text(encoding="utf-8"))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
