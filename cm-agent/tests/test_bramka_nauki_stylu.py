# -*- coding: utf-8 -*-
"""Test (19/08/2026, D-019): bramka na ZAPIS nauczonych regul stylu. Odczyt zostaje nietkniety.

DOWOD, KTORY GO ZAMOWIL. AP-315: `brand_config.style_learned` dla AGS zawieral szesc regulek
w ksztalcie POLECENIA ("Przed spojnikiem 'i' nie stawia sie przecinka"), po polsku, i szly one
do KAZDEJ generacji. Dwa razy skonczylo sie to publicznym postem, ktory byl wypowiedzia modelu
zamiast tresci. Filtr jezykowy z 10/08 zamknal DROGE, ktora znamy. Decyzja Managera Z-3 zamyka
KLASE: "Przy zerowym przychodzie nie potrzebujemy, zeby system uczyl sie szybciej. Potrzebujemy
zera incydentow."

USTALENIE Z ODCZYTU, ktorego nie bylo przy podejmowaniu Z-3: pisarzy byli DWAJ, nie jeden.
`_distill_style_rules` (model destyluje z korekty) i `add_style_rule` (Tomasz dyktuje wprost).
Manager rozstrzygnal 19/08: bramka obejmuje OBIE drogi, w JEDNYM wspolnym miejscu, bo roznica
miedzy preferencja a poleceniem lezy w SFORMULOWANIU, nie w autorstwie.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314 pkt 4: bramka, ktorej nie widziales przy pracy, jest
zalozeniem). Nie tego, ze funkcje maja flage. SCIEZKI ALARMU: karmi obie drogi prawdziwa regula
i zada, zeby do bazy NIE poszedl zaden zapis pod klucz stylu. Osobno pilnuje, zeby bramka nie
padla przez trzeciego pisarza - wola `_state_set` z kluczem stylu WPROST, z pominieciem obu
organow. I osobno tego, ze ODCZYT istniejacych regulek dziala dalej bez zmian, bo to jest
regresja, ktorej przy takiej poprawce najlatwiej narobic.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_bramka_nauki_stylu.py"""
import datetime as _dt
import json
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

from app import matreview  # noqa: E402
from app import generate   # noqa: E402

# ---------------------------------------------------------------- atrapa bazy
ZAPISY = []   # (klucz, wartosc) - wszystko, co naprawde poszlo do brand_config
STAN = {}     # to, co baza juz ma


def _fake_execute(sql, params=None):
    if "INSERT INTO brand_config" in sql:
        ZAPISY.append((params[0], params[1]))
        STAN[params[0]] = params[1]
    return None


def _fake_fetchone(sql, params=None):
    if "brand_config" in sql and params:
        v = STAN.get(params[0])
        return {"config_value": v} if v is not None else None
    return None


matreview.db.execute = _fake_execute
matreview.db.fetchone = _fake_fetchone


def _zapisy_stylu():
    return [z for z in ZAPISY if z[0] == matreview.KLUCZ_STYLU]


# ---------------------------------------------------------------- prawdziwe regulki z produkcji
REGULA_TOMASZA = 'Przed spojnikiem "i" nie stawia sie przecinka.'
REGULY_W_BAZIE = [
    'Zamiast "Trzeba zaprojektować" pisze "To wymaga konkretnej pracy. Trzeba zaprojektować"',
    'Przed spójnikiem "i" nie stawia się przecinka.',
]

print("\n[sciezka alarmu, droga 1] Tomasz dyktuje regule wprost ('zapamietaj na zawsze'):")
ZAPISY.clear(); STAN.clear()
odp = matreview.add_style_rule(REGULA_TOMASZA)
check("ZERO zapisow pod klucz stylu", _zapisy_stylu() == [], repr(_zapisy_stylu()))
check("odpowiedz jest tekstem, nie licznikiem", isinstance(odp, str), repr(type(odp)))

print("\n[sciezka alarmu, droga 2] model destyluje regulki z recznej korekty:")
ZAPISY.clear()
wywolan_modelu = []
generate.client = lambda *a, **k: wywolan_modelu.append(1) or _Any()
rules = matreview._distill_style_rules({"brand_id": "AGS"}, "tekst przed", "tekst po", "item-1")
check("ZERO zapisow pod klucz stylu", _zapisy_stylu() == [], repr(_zapisy_stylu()))
check("destylacja zwraca pusto, wiec karta NIE melduje nauki", rules == [], repr(rules))
check("model nie zostal wolany, wiec nie placimy za wynik do kosza",
      wywolan_modelu == [], repr(wywolan_modelu))

print("\n[wada przywrocona celowo] destylacja z ZYWA odpowiedzia modelu, bramka zdjeta:")


class _Blok:
    type = "text"
    text = "- Zamiast 'X' pisze 'Y'\n- Unika slowa Z"


class _Odpowiedz:
    content = [_Blok()]
    usage = None


class _Wiadomosci:
    def create(self, **kw):
        return _Odpowiedz()


class _Klient:
    messages = _Wiadomosci()


generate.client = lambda *a, **k: _Klient()
from app import tasks as _tasks  # noqa: E402
_tasks.model_for = lambda t: ("haiku", "low", "test")
_tasks.log_task = lambda *a, **k: None

ZAPISY.clear()
matreview.ZAPIS_STYLU_WYLACZONY = False
r_wada = matreview._distill_style_rules({"brand_id": "AGS"}, "przed", "po", "item-2")
check("bez bramki regulki modelu WCHODZA do stylu (dowod, ze test mierzy bramke, nie atrape)",
      len(_zapisy_stylu()) == 1 and bool(r_wada),
      f"zapisy={_zapisy_stylu()!r} rules={r_wada!r}")

ZAPISY.clear()
matreview.ZAPIS_STYLU_WYLACZONY = True
r_ok = matreview._distill_style_rules({"brand_id": "AGS"}, "przed", "po", "item-2")
check("bramka z powrotem: ZERO zapisow", _zapisy_stylu() == [], repr(_zapisy_stylu()))
check("bramka z powrotem: zero meldunku o nauce", r_ok == [], repr(r_ok))

ZAPISY.clear()
matreview.ZAPIS_STYLU_WYLACZONY = False              # sprawdzenie w destylacji celowo otwarte
_prawdziwy_set = matreview._state_set
matreview._state_set = lambda k, o: False if k == matreview.KLUCZ_STYLU else _prawdziwy_set(k, o)
r_gate = matreview._distill_style_rules({"brand_id": "AGS"}, "przed", "po", "item-2")
matreview._state_set = _prawdziwy_set
matreview.ZAPIS_STYLU_WYLACZONY = True
check("gwarancje daje `_state_set`, nie sprawdzenie w destylacji: sama odmowa zapisu "
      "wystarcza, zeby karta nie zameldowala nauki", r_gate == [], repr(r_gate))

print("\n[trzeci pisarz] bramka trzyma takze przy wolaniu z pominieciem obu organow:")
ZAPISY.clear()
wynik = matreview._state_set(matreview.KLUCZ_STYLU, {"rules": ["cokolwiek"]})
check("`_state_set` zwraca False", wynik is False, repr(wynik))
check("ZERO zapisow pod klucz stylu", _zapisy_stylu() == [], repr(_zapisy_stylu()))

print("\n[brak nadgorliwosci] bramka nie zamyka NICZEGO poza kluczem stylu:")
ZAPISY.clear()
check("stan przegladu kart zapisuje sie normalnie",
      matreview._state_set("cm_matnav_batch", {"count": 3}) is True)
check("klucz o podobnej nazwie NIE jest blokowany",
      matreview._state_set(matreview.KLUCZ_STYLU_ODLOZONE, {"notatki": []}) is True)
check("obydwa zapisy doszly do bazy", len(ZAPISY) == 2, repr(ZAPISY))

print("\n[droga zastepcza] regula Tomasza nie przepada, tylko laduje jako notatka:")
ZAPISY.clear(); STAN.clear()
matreview.add_style_rule(REGULA_TOMASZA)
odlozone = [z for z in ZAPISY if z[0] == matreview.KLUCZ_STYLU_ODLOZONE]
check("jest dokladnie jeden zapis notatki", len(odlozone) == 1, repr(ZAPISY))
notatki = json.loads(odlozone[0][1])["notatki"] if odlozone else []
check("notatka jest jedna", len(notatki) == 1, repr(notatki))
n = notatki[0] if notatki else {}
check("niesie tresc reguly", n.get("regula") == REGULA_TOMASZA, repr(n.get("regula")))
check("niesie jezyk", n.get("jezyk") == "pl", repr(n.get("jezyk")))
check("niesie rodzaj", "rodzaj" in n, repr(n))
check("niesie pochodzenie 'czlowiek'", n.get("pochodzenie") == "czlowiek", repr(n.get("pochodzenie")))
check("niesie powod", n.get("powod") == "D-019", repr(n.get("powod")))
check("niesie date", bool(n.get("ts")), repr(n.get("ts")))

print("\n[AP-317] notatka odroznia ZAOBSERWOWANE od WYWNIOSKOWANEGO:")
u = n.get("ustalenie") or {}
check("pochodzenie oznaczone jako zaobserwowane", u.get("pochodzenie") == "zaobserwowane", repr(u))
check("jezyk oznaczony jako wywnioskowany", u.get("jezyk") == "wywnioskowane", repr(u))
check("rodzaj NIE jest zgadniety, tylko jawnie nieustalony",
      u.get("rodzaj") == "nieustalone" and n.get("rodzaj") == "nieokreslony",
      f"rodzaj={n.get('rodzaj')!r} ustalenie={u.get('rodzaj')!r}")
check("wiadomo, czym ustalono jezyk",
      n.get("jezyk_wykrywacz") == "generate._wyglada_na_angielski", repr(n.get("jezyk_wykrywacz")))

print("\n[jeden wykrywacz jezyka] notatka pyta o jezyk to samo, co prompt (AP-309):")
check("regula angielska dostaje 'en'",
      matreview._jezyk_reguly("Prefers concrete numbers over adjectives and it is not vague") == "en")
check("regula polska dostaje 'pl'", matreview._jezyk_reguly(REGULA_TOMASZA) == "pl")
check("regula nierozpoznana laduje po stronie polskiej, nie angielskiej",
      matreview._jezyk_reguly("Krotko.") == "pl",
      "kierunek NIEsymetryczny - patrz generate._wyglada_na_angielski")
src_mrv = (APP / "matreview.py").read_text(encoding="utf-8")
check("nie powstal drugi wykrywacz jezyka obok pierwszego",
      "_wyglada_na_angielski" in src_mrv and "_EN_FUNKCYJNE" not in src_mrv)

print("\n[bez powtorek] ta sama regula podana dwa razy nie mnozy notatek:")
ZAPISY.clear()
matreview.add_style_rule(REGULA_TOMASZA)
check("drugi raz nie dopisuje niczego", ZAPISY == [], repr(ZAPISY))

print("\n[widocznosc] Tomasz DOWIADUJE sie, ze reguly nie ma w stylu (zero cichej odmowy):")
kom = matreview.KOMUNIKAT_D019
check("mowi wprost, ze nie zapisal", "Nie zapisalem tej reguly do stylu" in kom)
check("mowi, zeby na nia nie liczyc", "nie chce, zebys na nia liczyl" in kom)
check("podaje powod", "D-019" in kom)
check("mowi, ze regula zostala zachowana", "nie przepadla" in kom and "Odlozylem" in kom)
check("mowi, kiedy wroci", "odblokujemy" in kom)
check("daje wyjscie na teraz", "przy konkretnym tekscie" in kom)
check("odpowiedz narzedzia niesie ten komunikat w calosci", kom in odp)
check("kaze przekazac go doslownie", "PRZEKAZ TOMASZOWI DOSLOWNIE" in odp)
check("zero em-dashow (kanon RULE 1)", chr(0x2014) not in kom and chr(0x2013) not in kom)
for zargon in ("brand_config", "style_learned", "_state_set", "JSON", "klucz"):
    check(f"zero zargonu: '{zargon}'", zargon not in kom)

print("\n[REGRESJA] odczyt istniejacych regulek dziala DALEJ bez zmian:")
generate._db.fetchone = lambda sql, params=None: {
    "config_value": json.dumps({"rules": list(REGULY_W_BAZIE)}, ensure_ascii=False)}
blok_pl = generate._learned_style("AGS", "pl")
check("blok PL nie jest pusty", blok_pl != "")
for r in REGULY_W_BAZIE:
    check(f"regulka '{r[:30]}...' nadal wchodzi do promptu", r in blok_pl)
check("blok EN nadal odsiewa polskie regulki (filtr z AP-315 zyje)",
      generate._learned_style("AGS", "en") == "")
check("brak wiersza w bazie nadal nie wysadza generacji",
      (setattr(generate._db, "fetchone", lambda sql, params=None: None) or
       generate._learned_style("AGS", "pl")) == "")
src_gen = (APP / "generate.py").read_text(encoding="utf-8")
check("czytelnik nie zostal tkniety: nadal czyta ten sam klucz",
      "config_key='style_learned'" in src_gen)

print("\n[jedno miejsce] bramka nie rozlazla sie na latki:")
check("jest jeden predykat, ktory o tym decyduje", src_mrv.count("def zapis_stylu_wolno") == 1)
check("bramka stoi w `_state_set`",
      "def _state_set" in src_mrv and
      "if key == KLUCZ_STYLU and not zapis_stylu_wolno():" in src_mrv)
check("zaden organ nie pisze do klucza stylu z pominieciem `_state_set`",
      src_mrv.count('"style_learned"') == 1, "jedyne wystapienie to definicja KLUCZ_STYLU")

print("\n[podlaczenie] rozmowa NIE melduje Tomaszowi zapisu, ktorego nie bylo:")
src_conv = (APP / "conversation.py").read_text(encoding="utf-8")
check("narzedzie oddaje komunikat z `add_style_rule` bez wlasnej narracji",
      "return matreview.add_style_rule(inp.get(\"rule\"))" in src_conv,
      "WYMAGANA JEDNOLINIJKOWA ZMIANA w conversation._run_tool: stara wersja sklada "
      "f\"Regula stylu zapisana na stale (lacznie {n}).\" i to jest teraz NIEPRAWDA")
check("opis narzedzia nie obiecuje zapisu na stale",
      "Zapisz NA STALE regule stylu" not in src_conv,
      "opis uczy model, ze regula wchodzi na stale - po D-019 to nieprawda")

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
