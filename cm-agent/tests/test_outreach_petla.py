"""Testy domkniecia petli outreachu (26/07/2026, sekcje 4.2-4.4 diagnozy).

Co jest udowadniane, kazdy punkt z dowodem produkcyjnym za plecami:
  4.2  nowy gotowiec uniewaznia poprzedni w tym samym kanale (StandART: 7 wierszy, 0 sent),
  4.3  obie drogi odhaczenia ida przez jeden rdzen i ustawiaja termin nastepnego kontaktu,
  4.4  stopka obiecuje dokladnie to, co kod robi (nie obiecuje przesuniecia etapu),
  4.8  licznik stopki liczy WLASNE gotowce, nie wiersze Lacznika,
  AP-308 sprzatanie zaleglych wierszy jest deterministyczne (dry == plan apply).

Stdlib only, bez bazy, bez sieci, bez LLM.
Uruchomienie: python cm-agent/tests/test_outreach_petla.py"""
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

from app import sales, outreach_cleanup, db  # noqa: E402

FAILS = []
EXEC = []       # (sql, params) kazdego db.execute
FETCHALL = []   # (sql, params) kazdego db.fetchall
ROWS = {"gotowce": []}


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _fetchall(sql, params=None):
    FETCHALL.append((sql, params))
    if "FROM engagement_log" in sql and "status='proposed'" in sql:
        return list(ROWS["gotowce"])
    return []


def _fetchone(sql, params=None):
    if "FROM engagement_log" in sql and "COUNT(*)" in sql:
        return ROWS.get("licznik") or {"otwarte": 0, "wyslane": 0}
    if "FROM engagement_log" in sql:
        return ROWS.get("wiersz")
    return None


db.execute = lambda sql, params=None: EXEC.append((sql, params))
db.fetchall = _fetchall
db.fetchone = _fetchone
outreach_cleanup.db = db

UTC = _dt.timezone.utc


def _g(i, kto="Klub Sportowy StandART", kanal="Email", godz=9):
    return {"id": f"0000000-{i}", "author_display": kto, "channel": kanal,
            "created_at": _dt.datetime(2026, 7, 24, godz, 0, tzinfo=UTC), "podglad": f"tekst {i}"}


# ---------------- 4.2: nowy gotowiec uniewaznia poprzedniego ----------------
print("\n[4.2] szukanie zywych gotowcow zaweza sie do wlasnych wierszy i jednego kanalu:")
FETCHALL.clear()
ROWS["gotowce"] = [_g(1), _g(2, godz=11)]
sales._open_outreach_rows("Klub Sportowy StandART", "Email")
sql, params = FETCHALL[-1]
check("dopasowanie po author_display, nie po substringu tresci", "author_display=%s" in sql, sql)
check("filtr rodzaju odcina wiersze Lacznika", "notes" in sql and "ILIKE" in sql, sql)
check("zawezenie do jednego kanalu", "channel=%s" in sql, sql)
check("parametr kanalu przekazany", params[-1] == "Email", str(params))

FETCHALL.clear()
sales._open_outreach_rows("Klub Sportowy StandART")
check("bez kanalu nie ma warunku channel", "channel=%s" not in FETCHALL[-1][0])

EXEC.clear()
sales._close_outreach_rows(["a", "b"], "rejected", "ZASTAPIONE nowszym gotowcem")
check("zamkniecie wierszy wykonane", any("engagement_log SET status=%s" in s for s, _ in EXEC))
# Wygaszanie bramek idzie przez fetchall (potrzebujemy RETURNING id, zeby zdjac guziki z kart).
_caly_sql = [s for s, _ in EXEC] + [s for s, _ in FETCHALL]
check("bramki wierszy wygaszone w tym samym kroku",
      any("agent_decisions SET status='expired'" in s for s in _caly_sql),
      "bez tego lista decyzji pyta o gotowiec, ktorego nie ma")
check("wygaszanie zwraca id, zeby dalo sie zdjac guziki z kart",
      any("agent_decisions SET status='expired'" in s and "RETURNING id" in s for s in _caly_sql),
      "bez RETURNING karta w Telegramie zostaje klikalna na zawsze")
check("pusta lista nie generuje zapisu", sales._close_outreach_rows([], "rejected", "x") == 0)


# ---------------- 4.3: jeden rdzen dla obu drog ----------------
print("\n[4.3] mark_outreach_sent domyka wiersz, rodzenstwo i termin:")
ROWS["gotowce"] = [_g(1, godz=9), _g(2, godz=11), _g(3, godz=13)]
EXEC.clear()
row = {"id": "p1", "prospect_name": "Klub Sportowy StandART", "next_followup_at": None}
_, opis = sales.mark_outreach_sent(row=row, zrodlo="narzedzie")
statusy = [p[0] for s, p in EXEC if "engagement_log SET status=%s" in s]
check("najnowszy gotowiec oznaczony jako wyslany", "sent" in statusy, str(statusy))
check("rodzenstwo zamkniete jako nieaktualne", "skipped" in statusy, str(statusy))
check("termin ustawiony gdy byl pusty",
      any("sales_pipeline SET next_followup_at" in s for s, _ in EXEC))
check("etap lejka nietkniety", not any("SET stage" in s for s, _ in EXEC),
      "qualified znaczy zakwalifikowany, nie skontaktowany")
check("opis mowi o zamknietym rodzenstwie", "nieaktualn" in opis, opis)

EXEC.clear()
row_stary = {"id": "p1", "prospect_name": "Klub Sportowy StandART",
             "next_followup_at": _dt.datetime(2026, 7, 20, 10, 0, tzinfo=UTC)}
_, opis2 = sales.mark_outreach_sent(row=row_stary, zrodlo="przypomnienie")
check("przeterminowany termin zostaje przesuniety",
      any("sales_pipeline SET next_followup_at" in s for s, _ in EXEC),
      "stary kod milczal i zostawial date z przeszlosci")
check("czlowiek dowiaduje sie, ze termin byl przeterminowany", "przeterminowan" in opis2, opis2)

EXEC.clear()
row_przyszly = {"id": "p1", "prospect_name": "Klub Sportowy StandART",
                "next_followup_at": _dt.datetime(2099, 1, 1, 10, 0, tzinfo=UTC)}
sales.mark_outreach_sent(row=row_przyszly, zrodlo="narzedzie")
check("termin w przyszlosci NIE jest nadpisywany",
      not any("sales_pipeline SET next_followup_at" in s for s, _ in EXEC))

ROWS["gotowce"] = []
_, opis3 = sales.mark_outreach_sent(row={"id": "p1", "prospect_name": "Nikt",
                                         "next_followup_at": None}, zrodlo="narzedzie")
check("brak gotowca jest powiedziany wprost", "nie znalazlem" in opis3.lower(), opis3)
check("nieznany prospekt nie wywraca sie", sales.mark_outreach_sent(row=None)[0] is None)


# ---------------- 4.4 + 4.8: stopka mowi prawde i liczy wlasne gotowce ----------------
print("\n[4.4 + 4.8] stopka gotowca:")
ROWS["licznik"] = {"otwarte": 0, "wyslane": 0}
stopka = sales._outreach_stopka({"prospect_name": "Klub Sportowy StandART", "stage": "qualified",
                                 "next_followup_at": None})
check("stopka NIE obiecuje przesuniecia etapu", "przesune etap" not in stopka, stopka)
check("stopka obiecuje odhaczenie i termin",
      "odhacze gotowiec" in stopka and "nastepnego" in stopka, stopka)
check("pierwszy kontakt bez ozdobnikow", "PIERWSZY kontakt" in stopka, stopka)

ROWS["licznik"] = {"otwarte": 2, "wyslane": 0}
s2 = sales._outreach_stopka({"prospect_name": "X", "stage": "prospect", "next_followup_at": None})
check("otwarte gotowce nie udaja wysylek", "zaden nie byl wyslany" in s2, s2)
ROWS["licznik"] = {"otwarte": 0, "wyslane": 3}
s3 = sales._outreach_stopka({"prospect_name": "X", "stage": "prospect", "next_followup_at": None})
check("wysylki licza sie jako kontakty", "3 wyslanych wczesniej" in s3, s3)


# ---------------- AP-308: sprzatanie jest deterministyczne ----------------
print("\n[AP-308] plan sprzatania zaleglych gotowcow:")
ROWS["gotowce"] = [_g(1, godz=9), _g(2, godz=11), _g(3, godz=13),
                   _g(4, kto="Inna Szkola", kanal="LinkedIn", godz=10)]
zamk, zost, grupy = outreach_cleanup.plan()
check("grupowanie po prospekcie i kanale", len(grupy) == 2, str(len(grupy)))
check("w kazdej grupie zostaje dokladnie jeden", len(zost) == 2, str(len(zost)))
check("zostaje NAJNOWSZY wiersz grupy",
      any(r["id"] == "0000000-3" for r in zost), str([r["id"] for r in zost]))
check("do zamkniecia trafiaja starsze", len(zamk) == 2, str([r["id"] for r in zamk]))
check("wiersz jedyny w grupie nie jest zamykany",
      all(r["id"] != "0000000-4" for r in zamk))
z2, s2b, g2 = outreach_cleanup.plan()
check("dwa przebiegi daja ten sam plan (idempotencja dry-run)",
      [r["id"] for r in zamk] == [r["id"] for r in z2] and
      [r["id"] for r in zost] == [r["id"] for r in s2b])

# ---------------- D-009: kanal zapisu i kanal wyszukiwania to TA SAMA wartosc ----------------
print("\n[D-009] slownik kanalow nie jest etykieta, tylko kluczem dopasowania:")

# Wartosci dozwolone przez ograniczenie engagement_log_channel_check (DDL 001 + 036).
DOZWOLONE = {"X", "LinkedIn", "Instagram", "Facebook", "Email", "Telegram",
             "Phone", "Other", "SMS", "WhatsApp"}
check("kazda wartosc slownika przechodzi ograniczenie tabeli",
      set(sales._ENG_CHANNEL.values()) <= DOZWOLONE,
      str(set(sales._ENG_CHANNEL.values()) - DOZWOLONE))

# Sedno D-009: 'email' mapowal sie na 'Other', mimo ze 'Email' istnieje w ograniczeniu
# od DDL 001. Ten sam kanal mial przez to w ksiedze dwie etykiety, bo teczka.py pisze 'Email'.
check("email mapuje sie na 'Email', nie na 'Other' (D-009)",
      sales._ENG_CHANNEL.get("email") == "Email", str(sales._ENG_CHANNEL))

# NIEZMIENNIK, ktorego zlamanie odtwarza wade StandART z 24/07: ta sama zmienna musi
# trafic do wyszukiwania poprzednich gotowcow I do zapisu nowego. Gdy sie rozjada,
# nowy gotowiec nie znajduje starego i prospekt zbiera otwarte wiersze bez konca.
import inspect  # noqa: E402
_zrodlo = inspect.getsource(sales._outreach) if hasattr(sales, "_outreach") else ""
if not _zrodlo:
    for _n in dir(sales):
        _o = getattr(sales, _n)
        if callable(_o) and getattr(_o, "__module__", "") == sales.__name__:
            try:
                _s = inspect.getsource(_o)
            except Exception:
                continue
            if "_open_outreach_rows(" in _s and "INSERT INTO engagement_log" in _s:
                _zrodlo = _s
                break
check("znaleziono funkcje piszaca gotowca", bool(_zrodlo))
check("kanal liczony JEDEN raz ze slownika", _zrodlo.count("_ENG_CHANNEL.get(") == 1, _zrodlo[:200])
check("ta sama zmienna idzie do wyszukiwania i do zapisu",
      "_open_outreach_rows(row[\"prospect_name\"], _eng_kanal)" in _zrodlo
      and "(_eng_kanal," in _zrodlo,
      "rozjazd miedzy kanalem wyszukiwania a kanalem zapisu")

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
