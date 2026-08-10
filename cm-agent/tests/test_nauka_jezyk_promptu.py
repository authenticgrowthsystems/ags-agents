# -*- coding: utf-8 -*-
"""Test (10/08/2026, AP-315 trzecia przyczyna): regulki nauczone wchodza tylko w jezyku wyjscia.

DOWOD, KTORY GO ZAMOWIL. Dwa wycieki - post z 04/08 zyjacy szesc dni na LinkedInie i karta
z 10/08 - to NIE byla ta sama awaria co dwie wczesniejsze diagnozy sugerowaly. Odczyt produkcji
pokazal, ze `brand_config.style_learned` dla AGS zawiera szesc regulek TAKICH:

    - Zamiast "Trzeba zaprojektowac" pisze "To wymaga konkretnej pracy. Trzeba zaprojektowac"
    - Zamiast "kiedy cos nie zadziala, i kto" pisze "kiedy cos nie zadziala i kto"
    - Przed spojnikiem "i" nie stawia sie przecinka.

Sa PO POLSKU (powstaly z korekt polskich tekstow) i maja ksztalt POLECENIA. Wstrzykniete
do promptu, ktorego wyjscie ma byc ANGIELSKIE, przestaja byc preferencja stylu i staja sie
DRUGIM ZADANIEM. Model wykonuje to drugie: wylicza, co dostal, i prosi o tekst do poprawy.

Zgadza sie to co do punktu ze spisem, ktory model sam zrobil na karcie 10/08:
"Instrukcja, jak mam poprawiac polski" (regula przecinka + pary Zamiast/pisze),
"Moja analiza jakiegos polskiego tekstu" (cytaty w tych parach, bez tekstu zrodlowego),
"Pytanie o angielski/polski do LinkedIna" (lang_guide).

To takze OBALA moja wczesniejsza diagnoze, ze zrodlem byl `compliance._rewrite`: tamta funkcja
NIE przekazuje bloku systemowego, wiec wolany przez nia model fizycznie nie widzi Voice Bible -
a tekst z 04/08 zaczyna sie od "I've reviewed the canonical text and Voice Bible".

CZEGO TEN TEST PILNUJE (AP-314): nie tego, ze funkcja przyjmuje parametr. Karmi ja SZESCIOMA
PRAWDZIWYMI regulkami z produkcji i zada, zeby przy jezyku angielskim blok byl PUSTY, a przy
polskim - pelny. Osobno pilnuje, zeby OBA miejsca wstrzykiwania podawaly jezyk, bo jedno
z nich (tekst-matka) umknelo pierwszemu odczytowi.

Stdlib only. Uruchomienie: python cm-agent/tests/test_nauka_jezyk_promptu.py"""
import json
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

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

from app import generate  # noqa: E402

# ---------------------------------------------------------------- prawdziwe regulki z produkcji
REGULY_PL = [
    'Zamiast "Trzeba zaprojektować" pisze "To wymaga konkretnej pracy. Trzeba zaprojektować" '
    '(złagodzenie kategoryczności poprzez dodanie kontekstu)',
    'Zamiast "kiedy coś nie zadziała, i kto" pisze "kiedy coś nie zadziała i kto" '
    '(usunięcie przecinka przed "i")',
    'Przed spójnikiem "i" nie stawia się przecinka.',
    'Zamiast kategorycznych twierdzeń ("To nieuczciwe") używa łagodniejszych sformułowań '
    '("To nie jest do końca uczciwe")',
    'Zamiast "poprawiania promptu o jedno zdanie" pisze "iteracyjnego poprawiania" (bardziej precyzyjnie)',
    'Zamiast bezpośredniego imperatywu ("Następny krok to...") używa "Pamiętaj więc, że..." (bardziej płynnie)',
]
REGULY_EN = [
    'Prefers concrete numbers over adjectives ("12 posts this week", not "a lot of posts")',
    'Opens with a scene, not a claim.',
]


def _podstaw(reguly):
    generate._db.fetchone = lambda sql, params=None: {
        "config_value": json.dumps({"rules": list(reguly)}, ensure_ascii=False)}


print("\n[dowod] szesc PRAWDZIWYCH regulek z produkcji przy wyjsciu angielskim:")
_podstaw(REGULY_PL)
blok_en = generate._learned_style("AGS", "en")
check("blok jest PUSTY", blok_en == "", repr(blok_en[:120]))
check("czyli zaden polski cytat nie wchodzi do promptu",
      "Zamiast" not in blok_en and "przecinka" not in blok_en)

print("\n[brak nadgorliwosci] te same regulki przy wyjsciu polskim wchodza w calosci:")
blok_pl = generate._learned_style("AGS", "pl")
check("blok NIE jest pusty", blok_pl != "")
for i, r in enumerate(REGULY_PL):
    check(f"regulka {i + 1} jest w bloku", r in blok_pl)

print("\n[mieszanka] kazda regulka trafia do swojego jezyka:")
_podstaw(REGULY_PL + REGULY_EN)
b_en = generate._learned_style("AGS", "en")
b_pl = generate._learned_style("AGS", "pl")
for r in REGULY_EN:
    check(f"angielska '{r[:34]}...' w bloku EN", r in b_en)
    check(f"angielska '{r[:34]}...' NIE w bloku PL", r not in b_pl)
for r in REGULY_PL[:2]:
    check(f"polska '{r[:34]}...' w bloku PL", r in b_pl)
    check(f"polska '{r[:34]}...' NIE w bloku EN", r not in b_en)

print("\n[zgodnosc wstecz] brak podanego jezyka nie zmienia starego zachowania:")
_podstaw(REGULY_PL + REGULY_EN)
bez_jezyka = generate._learned_style("AGS")
check("bez jezyka wchodzi WSZYSTKO", all(r in bez_jezyka for r in REGULY_PL + REGULY_EN))

print("\n[odpornosc] pusto i smiecie nie wysadzaja generacji:")
_podstaw([])
check("brak regulek -> pusty napis", generate._learned_style("AGS", "en") == "")
generate._db.fetchone = lambda sql, params=None: None
check("brak wiersza w brand_config -> pusty napis", generate._learned_style("AGS", "en") == "")
generate._db.fetchone = lambda sql, params=None: {"config_value": "to nie jest json"}
check("zepsuty JSON -> pusty napis, bez wyjatku", generate._learned_style("AGS", "en") == "")

print("\n[jezyk marki] tekst-matka nie ma kanalu, wiec bierze dominujacy jezyk marki:")
generate._db.fetchall = lambda sql, params=None: [
    {"config": {"language_publish": "en"}}, {"config": {"language_publish": "en"}},
    {"config": {"language_publish": "pl"}}]
check("trzy kanaly, dwa EN -> 'en'", generate._jezyk_marki("AGS") == "en",
      generate._jezyk_marki("AGS"))
generate._db.fetchall = lambda sql, params=None: [{"config": {"language_publish": "pl"}}]
check("jedyny kanal PL -> 'pl'", generate._jezyk_marki("TNM") == "pl")
generate._db.fetchall = lambda sql, params=None: []
check("marka bez kanalow -> 'en' (bezpieczny domysl)", generate._jezyk_marki("X") == "en")
generate._db.fetchall = lambda sql, params=None: [{"config": None}]
check("kanal bez konfiguracji nie wysadza", generate._jezyk_marki("X") == "en")

print("\n[podlaczenie] OBA miejsca wstrzykiwania podaja jezyk:")
src = (APP / "generate.py").read_text(encoding="utf-8")
check("wariant podaje jezyk kanalu",
      "_learned_style(brand.get('brand_id', 'AGS'), lang)" in src)
check("wariant filtruje takze skrot nauki",
      "_learning_digest(brand.get('brand_id', 'AGS'), lang)" in src)
check("tekst-matka podaje jezyk marki",
      "_learned_style(brand.get('brand_id', 'AGS'), _jez)" in src)
check("tekst-matka filtruje takze skrot nauki",
      "_learning_digest(brand.get('brand_id', 'AGS'), _jez)" in src)
check("nie zostalo ZADNE wywolanie bez jezyka",
      "_learned_style(brand.get('brand_id', 'AGS'))" not in src)

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
