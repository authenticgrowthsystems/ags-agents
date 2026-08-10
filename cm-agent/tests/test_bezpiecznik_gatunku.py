# -*- coding: utf-8 -*-
"""Test (10/08/2026, AP-315, decyzja Managera): bezpiecznik GATUNKU tekstu, dwie klasy fraz.

DOWOD, KTORY GO ZAMOWIL. Post LinkedIn z 04/08 zyl szesc dni pod nazwiskiem Tomasza,
87 wyswietlen, a jego trescia byla notatka recenzyjna CM: "I've reviewed the canonical
text and Voice Bible. (...) strong content. However, I need to flag an issue before...".

DLACZEGO PRZESZEDL. `strip_meta_header` zdejmuje meta-linie o KSZTALCIE naglowka
("## Wersja LinkedIn:", "Oto post:"). Tamten tekst byl PROZA, wiec zaden wzorzec ksztaltu
go nie dotknal. `compliance.enforce` sprawdzal myslniki, zakazane slownictwo i polszczyzne,
czyli FORME. Nikt nie pytal o GATUNEK: czy to jest tekst dla czlowieka, czy model mowiacy
o tekscie. Na tym polega AP-315.

DWIE KLASY (korekta Managera 10/08). TWARDE to nazwy naszej maszynerii - blokada bez furtki.
MIEKKIE to zwykle slowa, ktorych Tomasz uzywa piszac po angielsku o systemach - pierwsze
trafienie blokuje i melduje FRAZE, drugie zatwierdzenie TEGO SAMEGO tekstu przepuszcza.
Powod rozdzialu: wpadka 04/08 wziela sie z ODRUCHOWEGO tapniecia, wiec furtka "tapnij drugi
raz" bez rozdzialu odtwarzalaby ten sam tryb awarii.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314: bramke trzeba ZOBACZYC przy pracy):
nie sprawdza, ze funkcja istnieje. Przepuszcza przez PRAWDZIWA petle `worker.process_item`
szesc scenariuszy i patrzy, czy `dispatch_item` zostal wolany, czy nie. Osobno karmi
bezpiecznik dwoma PRAWDZIWYMI dobrymi postami z tego samego tygodnia i zada, zeby ich nie
tknal - bezpiecznik blokujacy wszystko jest tak samo bezuzyteczny jak ten, ktory nie blokuje nic.

Stdlib only. Uruchomienie: python cm-agent/tests/test_bezpiecznik_gatunku.py"""
import datetime as _dt
import hashlib
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

from app import compliance, channels, worker, db, slots, logbot, config  # noqa: E402

# ---------------------------------------------------------------- prawdziwe teksty
# WYCIEK: post opublikowany 04/08 16:01, urn:li:share:7490406444618387458, zdjety recznie 10/08.
WYCIEK = ("I've reviewed the canonical text and Voice Bible. This is a technical article about "
          "agent responsibility separation, strong content. However, I need to flag an issue "
          "before it goes out.")
# DOBRE: dwa posty z tego samego tygodnia, ktore wyszly prawidlowo.
DOBRY_358 = ("I looked at the table from my notebook. Two tasks, the same quality threshold, "
             "costs differing by an order of magnitude. One task costs a fifth of the price "
             "of the previous one.")
DOBRY_0308 = ("Twelve automation ideas rotting in a doc. Half made sense three weeks ago and "
              "half never did. The list was the problem, not the ideas.")
# MIEKKI: prawdziwe angielskie zdanie techniczne, ktore Tomasz moglby napisac naprawde.
MIEKKI = ("The canonical example of this failure is an agent that reports success before the "
          "callback ever arrives. Build for the callback, not for the optimism.")

print("\n[dowod] tekst, ktory NAPRAWDE wyszedl, jest zatrzymany - i to TWARDO:")
twarde, miekkie = compliance.bezpiecznik_gatunku(WYCIEK)
check("wyciek z 04/08 lapie fraze TWARDA", "voice bible" in twarde, repr(twarde))
check("wyciek lapie takze frazy miekkie", len(miekkie) >= 3, repr(miekkie))
for f in ("i've reviewed", "canonical", "strong content", "i need to flag"):
    check(f"wyciek lapie miekka '{f}'", f in miekkie, repr(miekkie))

print("\n[brak falszywych alarmow] prawdziwe dobre posty przechodza nietkniete:")
check("post #358 przechodzi", compliance.bezpiecznik_gatunku(DOBRY_358) == ([], []),
      repr(compliance.bezpiecznik_gatunku(DOBRY_358)))
check("post z 03/08 przechodzi", compliance.bezpiecznik_gatunku(DOBRY_0308) == ([], []),
      repr(compliance.bezpiecznik_gatunku(DOBRY_0308)))

print("\n[rozdzial klas] nazwy maszynerii sa TWARDE:")
for fraza in ("Voice Bible", "masterprompt", "stan_gry", "matreview", "Bramka:"):
    tw, mk = compliance.bezpiecznik_gatunku(f"Zwykle zdanie. {fraza} i dalej reszta akapitu.")
    check(f"'{fraza}' jest twarda", bool(tw) and not mk, f"tw={tw} mk={mk}")

print("\n[rozdzial klas] zwykle slowa jezyka sa MIEKKIE:")
for fraza in ("canonical", "I've reviewed", "I have reviewed", "I need to flag",
              "strong content", "zatwierdzam", "proponuje zmiane", "kolejka", "meldunek"):
    tw, mk = compliance.bezpiecznik_gatunku(f"Zwykle zdanie. {fraza} i dalej reszta akapitu.")
    check(f"'{fraza}' jest miekka", bool(mk) and not tw, f"tw={tw} mk={mk}")

print("\n[prog twardosci] prawdziwe polskie zdania TNM nie sa blokowane na twardo:")
# Korekta Managera 10/08: TNM pisze po polsku do uslug lokalnych. Te zdania MOGA sie
# zatrzymac (miekko, z furtka), ale NIGDY na twardo - twarda blokada na zwyklym rzeczowniku
# odpalilaby raz, w najgorszym momencie, i wygladalaby jak zepsuty system.
for zdanie in ("Kolejka klientow w recepcji to najlepszy moment na rozmowe o karnecie.",
               "Kolejka chetnych na zajecia rosnie, a nikt jej nie obsluguje.",
               "Nikt nie lubi stac w kolejce, wiec zapisy ida przez telefon.",
               "Dostajesz meldunek, gdy klient nie wrocil przez czternascie dni."):
    tw, mk = compliance.bezpiecznik_gatunku(zdanie)
    check(f"'{zdanie[:38]}...' nie jest twarde", not tw, f"tw={tw}")

print("\n[AP-313] ogonki nie omijaja bezpiecznika:")
check("'proponuję zmianę' (z ogonkami) trafia",
      "proponuje zmiane" in compliance.bezpiecznik_gatunku("Przeczytalem i proponuję zmianę.")[1])
check("'VOICE BIBLE' wielkimi literami trafia",
      "voice bible" in compliance.bezpiecznik_gatunku("Zgodnie z VOICE BIBLE to jest ok.")[0])

print("\n[odpornosc] pusty wsad nie wysadza bezpiecznika:")
check("None przechodzi", compliance.bezpiecznik_gatunku(None) == ([], []))
check("pusty napis przechodzi", compliance.bezpiecznik_gatunku("") == ([], []))

# ---------------------------------------------------------------- podstawka petli
KOLEJKA = []          # wiersze, ktore "leza" w post_queue dla materialu
ZAPISY = []           # (status, pola) z db.set_item_status
MELDUNKI = []         # tresci wyslane na kanal logowy
DISPATCH = []         # kazde wolanie = material ODDANY do publikacji


def _fetchall(sql, params=None):
    if "post_queue" in sql:
        return list(KOLEJKA)
    return []


db.fetchall = _fetchall
db.set_item_status = lambda iid, status, **pola: ZAPISY.append((status, pola))
logbot.send = lambda txt, *a, **k: MELDUNKI.append(txt)
channels.dispatch_item = lambda item: DISPATCH.append(item["id"]) or []
slots.assign_if_needed = lambda item: (item.get("scheduled_for"), False, None)
worker._dispatch_ack = lambda item, handoff: "ack"


def przebieg(tresc, media=None):
    """Jeden obrot petli dla materialu 'approved' z podana trescia w kolejce."""
    KOLEJKA[:] = [{"id": 344, "platform": "linkedin", "content": tresc}]
    ZAPISY.clear(); MELDUNKI.clear(); DISPATCH.clear()
    item = {"id": "00000000-0000-0000-0000-000000000001", "brand_id": "AGS",
            "status": "approved", "master_theme": "temat testowy",
            "scheduled_for": _dt.datetime.now(_zi.ZoneInfo("Europe/Warsaw")),
            "media": media or []}
    return worker.process_item(item)


def _znacznik_dla(tresc):
    """Znacznik, jaki bezpiecznik zapisalby po zatrzymaniu DOKLADNIE tej tresci."""
    return [{"kind": "ap315_blok",
             "odcisk": hashlib.sha1(tresc.encode("utf-8")).hexdigest()[:16]}]


print("\n[A] miekka fraza, pierwszy raz -> ZATRZYMANE, nic nie wyszlo:")
wynik = przebieg(MIEKKI)
check("petla melduje zatrzymanie", "zablokowany_gatunek" in str(wynik), repr(wynik))
check("material NIE zostal oddany", DISPATCH == [], repr(DISPATCH))
check("material wrocil do needs_approval", ZAPISY and ZAPISY[0][0] == "needs_approval", repr(ZAPISY))
check("meldunek nazywa fraze", any("canonical" in m for m in MELDUNKI), repr(MELDUNKI))
check("meldunek mowi, ze drugie zatwierdzenie przejdzie",
      any("drugi raz" in m for m in MELDUNKI), repr(MELDUNKI))
check("zapisany zostal znacznik", ZAPISY and any(
    (m or {}).get("kind") == "ap315_blok" for m in (ZAPISY[0][1].get("media") or [])), repr(ZAPISY))

print("\n[B] miekka fraza, TEN SAM tekst drugi raz -> PRZECHODZI, ale glosno:")
wynik = przebieg(MIEKKI, media=_znacznik_dla(MIEKKI))
check("material zostal oddany", len(DISPATCH) == 1, repr(DISPATCH))
check("nie ma powrotu do needs_approval",
      all(s != "needs_approval" for s, _ in ZAPISY), repr(ZAPISY))
check("poszlo ostrzezenie o przepuszczeniu",
      any("PRZEPUSZCZA" in m for m in MELDUNKI), repr(MELDUNKI))

print("\n[C] TWARDA fraza mimo znacznika -> nadal ZATRZYMANE (furtki nie ma):")
TWARDY = "Zgodnie z Voice Bible ten material jest gotowy do publikacji."
wynik = przebieg(TWARDY, media=_znacznik_dla(TWARDY))
check("material NIE zostal oddany", DISPATCH == [], repr(DISPATCH))
check("material wrocil do needs_approval", ZAPISY and ZAPISY[0][0] == "needs_approval", repr(ZAPISY))
check("meldunek mowi wprost, ze drugie zatwierdzenie nic nie da",
      any("NIC nie da" in m for m in MELDUNKI), repr(MELDUNKI))

print("\n[D] PRAWDZIWY wyciek z 04/08 mimo znacznika -> ZATRZYMANY na twardej:")
wynik = przebieg(WYCIEK, media=_znacznik_dla(WYCIEK))
check("wyciek NIE zostalby oddany nawet przy drugim tapnieciu", DISPATCH == [], repr(DISPATCH))

print("\n[E] miekka fraza, ale tekst ZMIENIONY -> liczy sie od nowa:")
INNY = MIEKKI.replace("optimism.", "optimism. One more sentence changes the text.")
wynik = przebieg(INNY, media=_znacznik_dla(MIEKKI))   # znacznik od STAREJ tresci
check("zmieniony tekst jest zatrzymany", DISPATCH == [], repr(DISPATCH))
check("i wraca do needs_approval", ZAPISY and ZAPISY[0][0] == "needs_approval", repr(ZAPISY))

print("\n[F] czysty tekst -> idzie normalnie, bezpiecznik milczy:")
wynik = przebieg(DOBRY_0308)
check("material zostal oddany", len(DISPATCH) == 1, repr(DISPATCH))
check("zapisano handed_off", ZAPISY and ZAPISY[0][0] == config.STATUS_HANDED_OFF, repr(ZAPISY))
check("zaden meldunek nie mowi o bezpieczniku",
      not any("BEZPIECZNIK" in m for m in MELDUNKI), repr(MELDUNKI))

print("\n[odcisk] furtka jest przywiazana do TRESCI, nie do trafien:")
KOLEJKA[:] = [{"id": 344, "platform": "linkedin", "content": MIEKKI}]
a = channels.sprawdz_gatunek({"id": "x"})
KOLEJKA[:] = [{"id": 344, "platform": "linkedin", "content": INNY}]
b = channels.sprawdz_gatunek({"id": "x"})
check("dwie rozne tresci daja rozne odciski", a[0]["odcisk"] != b[0]["odcisk"],
      f"{a[0]['odcisk']} vs {b[0]['odcisk']}")
KOLEJKA[:] = [{"id": 344, "platform": "linkedin", "content": MIEKKI}]
c = channels.sprawdz_gatunek({"id": "x"})
check("ta sama tresc daje ten sam odcisk", a[0]["odcisk"] == c[0]["odcisk"])

print("\n[kolejnosc] bezpiecznik stoi PRZED zapisem handed_off:")
src = (APP / "worker.py").read_text(encoding="utf-8")
i_bezp = src.find("channels.sprawdz_gatunek(item)")
i_hand = src.find('db.set_item_status(item["id"], config.STATUS_HANDED_OFF)')
check("kolejnosc w zrodle jest wlasciwa", 0 < i_bezp < i_hand, f"{i_bezp} vs {i_hand}")
check("znacznik odchodzi przy pisaniu tekstu od nowa", "_AP315_KIND) and not str" in src)

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
