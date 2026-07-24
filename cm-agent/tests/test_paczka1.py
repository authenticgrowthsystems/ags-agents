"""Testy lokalne paczki #1 Managera (24/07): heurystyka interpunkcji PL (pkt 8)
i deterministyczny parser linii kpi_snapshot (pkt 1). Stdlib only, bez serwera i bez bazy.
Uruchomienie: python cm-agent/tests/test_paczka1.py

Wzorzec z test_x_collector.py: stuby zaleznosci wchodza do sys.modules PRZED importem
modulow app.*, wiec test nie potrzebuje psycopg ani polaczenia z PG."""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

# --- stuby zaleznosci (przed importem app.compliance / app.engagement) ---
psycopg = types.ModuleType("psycopg")
psycopg_types = types.ModuleType("psycopg.types")
psycopg_json = types.ModuleType("psycopg.types.json")


class Jsonb:  # noqa: D101 - stub
    def __init__(self, obj):
        self.obj = obj


psycopg_json.Jsonb = Jsonb
psycopg.types = psycopg_types
psycopg_types.json = psycopg_json
sys.modules["psycopg"] = psycopg
sys.modules["psycopg.types"] = psycopg_types
sys.modules["psycopg.types.json"] = psycopg_json

fake_httpx = types.ModuleType("httpx")
fake_httpx.post = lambda *a, **k: None
sys.modules["httpx"] = fake_httpx

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

fake_config = types.ModuleType("app.config")
fake_config.TELEGRAM_BOT_TOKEN = None
sys.modules["app.config"] = fake_config

fake_db = types.ModuleType("app.db")
fake_db.rows = []
fake_db.fetchone = lambda sql, p=None: None
fake_db.fetchall = lambda sql, p=None: []
fake_db.execute = lambda sql, p=None: fake_db.rows.append((sql, p))
sys.modules["app.db"] = fake_db

fake_tasks = types.ModuleType("app.tasks")
fake_tasks.model_for = lambda kind: ("stub-model", "haiku", "test")
fake_tasks.log_task = lambda *a, **k: None
sys.modules["app.tasks"] = fake_tasks

fake_generate = types.ModuleType("app.generate")
fake_generate.client = lambda: (_ for _ in ()).throw(RuntimeError("LLM w tescie zabroniony"))
sys.modules["app.generate"] = fake_generate

fake_decisions = types.ModuleType("app.decisions")
fake_decisions.ask = lambda *a, **k: "stub-ask"
sys.modules["app.decisions"] = fake_decisions

fake_hitl = types.ModuleType("app.hitl")
fake_hitl._admin_chat_id = lambda: None
sys.modules["app.hitl"] = fake_hitl

fake_conversation = types.ModuleType("app.conversation")
fake_conversation._tg = lambda method, payload: None
sys.modules["app.conversation"] = fake_conversation

from app import compliance, engagement  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---------------- pkt 8: heurystyka interpunkcji PL ----------------
print("\n[pkt 8] interpunkcja PL - powinno FLAGOWAC (brak przecinka):")
POZYTYWNE = [
    ("Wiem że to działa od tygodnia.", "że"),
    ("System publikuje sam bo nikt go nie pilnuje.", "bo"),
    ("Zbudowałem agenta który sam pisze raporty.", "który"),
    ("Odezwę się gdy skończę wdrożenie.", "gdy"),
    ("Zadzwoń jeśli coś przestanie działać.", "jeśli"),
    ("Robię to żeby nie tracić wieczorów.", "żeby"),
]
for txt, word in POZYTYWNE:
    flags = compliance.pl_comma_flags(txt)
    check(f"'{txt[:38]}...' -> flaga ({word})", len(flags) == 1 and word in flags[0], flags)

print("\n[pkt 8] interpunkcja PL - NIE powinno flagowac (poprawne albo niegroźne):")
NEGATYWNE = [
    "Wiem, że to działa od tygodnia.",
    "System, który publikuje sam, nie potrzebuje niani.",
    "Gdy skończę wdrożenie, odezwę się od razu.",
    "Który agent pisze te raporty?",
    "To jest projekt, w którym wszystko liczy się z danych.",
    "Zrobiłem to, mimo że termin był wczoraj.",
    "Działa, nawet jeśli serwer się restartuje.",
    "Powód jest prosty: bo tak jest taniej.",
    "Trzy rzeczy - że działa, że jest tanie, że nikt tego nie pilnuje.",
    "This is an English post that works without commas.",
]
for txt in NEGATYWNE:
    flags = compliance.pl_comma_flags(txt)
    check(f"'{txt[:44]}...' -> brak flagi", not flags, flags)

print("\n[pkt 8] limit i format:")
dlugi = " ".join(["Wiem że to działa."] * 10)
check("limit=3 przycina liste", len(compliance.pl_comma_flags(dlugi, limit=3)) <= 3)
check("pusty tekst = pusta lista", compliance.pl_comma_flags("") == [])
check("None = pusta lista", compliance.pl_comma_flags(None) == [])


# ---------------- pkt 1: parser linii kpi_snapshot ----------------
print("\n[pkt 1] parser kpi_snapshot:")
RAPORT = """[RAPORT PRACY v1] kanal: LinkedIn | data: 2026-07-24
- komentarz | @jan-kowalski | https://linkedin.com/x | Konkretna obserwacja.
- kpi_snapshot | 2026-07-24 | wyswietlenia=1234 | reakcje=56 | nowi_obserwujacy=7 | okres=7d
- kpi_snapshot | 2026-07-23 | wyswietlenia=980 | odslony_profilu=12
- kpi_snapshot | wyswietlenia=nie wiem
[KONIEC RAPORTU]"""
rep = engagement.parse_work_report(RAPORT)
kpi = [e for e in rep["entries"] if e[0] == "kpi_snapshot"]
check("parser widzi 3 linie kpi_snapshot", len(kpi) == 3, [e[1] for e in kpi])
check("komentarz nadal parsowany", any(e[0] == "komentarz" for e in rep["entries"]))

f1 = engagement._kpi_fields(kpi[0][1])
check("data z pierwszego pola", f1["metric_date"] == "2026-07-24", f1)
check("wyswietlenia -> impressions", f1["impressions"] == 1234, f1)
check("reakcje -> reactions", f1["reactions"] == 56, f1)
check("nowi_obserwujacy -> new_followers", f1["new_followers"] == 7, f1)
check("okres 7d", f1["period"] == "7d", f1)

f2 = engagement._kpi_fields(kpi[1][1])
check("odslony_profilu -> profile_views", f2["profile_views"] == 12, f2)
check("brak okresu = dzien", f2["period"] == "dzien", f2)
check("brak pola = None, nie zero", f2.get("reactions") is None, f2)

f3 = engagement._kpi_fields(kpi[2][1])
check("liczba nieczytelna = pole pomijane", f3.get("impressions") is None, f3)
check("bez daty = None (wolajacy podstawia dzis)", f3.get("metric_date") is None, f3)

f4 = engagement._kpi_fields(["2026-07-24", "wyswietlenia = 1 234", "obserwujacy=1 010"])
check("spacja jako separator tysiecy", f4["impressions"] == 1234, f4)
check("obserwujacy -> followers_total", f4["followers_total"] == 1010, f4)


# ---------------- pkt 7: fail-closed przed wykluczeniem z lejka ----------------
print("\n[pkt 7] fail-closed (rekomendacja tieru wykluczajacego):")
from app import crm  # noqa: E402

CID = "11111111-2222-3333-4444-555555555555"


def _stub_contact(n, last, stage):
    fake_db.fetchone = lambda sql, p=None: {"n": n, "last": last, "stage": stage}


class _Data:  # namiastka daty z bazy (ma strftime)
    def strftime(self, fmt):
        return "22/07"


_stub_contact(3, _Data(), "dm")
wolno, nota = crm.fail_closed_note(CID, "Competitor")
check("Competitor + historia DM -> BRAK rekomendacji", wolno is False and nota, (wolno, nota))
check("nota niesie dowod (liczba wpisow i stadium)", nota and "3" in nota and "dm" in nota, nota)

wolno, nota = crm.fail_closed_note(CID, "Buyer")
check("Buyer + historia DM -> rekomendacja dozwolona", wolno is True and nota is None, (wolno, nota))

_stub_contact(0, None, "cold")
wolno, nota = crm.fail_closed_note(CID, "Competitor")
check("Competitor bez historii -> rekomendacja dozwolona", wolno is True and nota is None, (wolno, nota))

_stub_contact(0, None, "offer")
wolno, nota = crm.fail_closed_note(CID, "out_of_icp")
check("out_of_icp + stadium offer -> BRAK rekomendacji", wolno is False and nota, (wolno, nota))

wolno, nota = crm.fail_closed_note(CID, None)
check("brak propozycji tieru -> bez ingerencji", wolno is True and nota is None, (wolno, nota))

wolno, nota = crm.fail_closed_note(None, "Competitor")
check("brak kontaktu -> bez ingerencji", wolno is True and nota is None, (wolno, nota))

print("\n" + ("WSZYSTKIE TESTY PASS" if not FAILS else f"FAIL: {len(FAILS)} -> {FAILS}"))
sys.exit(1 if FAILS else 0)
