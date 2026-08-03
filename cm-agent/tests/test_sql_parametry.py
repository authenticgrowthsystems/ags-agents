# -*- coding: utf-8 -*-
"""Test D-008 (03/08/2026), skutek uboczny: liczba znacznikow %s musi zgadzac sie z liczba
parametrow w KAZDYM zapytaniu skladanym ze stalych.

POWOD - wada zlapana w trakcie tego samego buildu. D-008 zamienilo osiem zapytan z wklejonym
napisem `'dispatching'` na zapytania z parametrem `%s`. Jedno z nich, `_generate_material_image`
w `conversation.py`, uzywa wspolnego fragmentu `base_q` w TRZECH miejscach, a trzecie lezalo
kilkadziesiat linii nizej, poza fragmentem czytanym przy poprawce. Fragment dostal `%s`,
wywolanie nie dostalo parametru. Skutek bylby taki:

    blad przy pierwszym zadaniu grafiki bez podanego fragmentu tematu

czyli awaria widoczna dopiero u Tomasza, nie w zestawie testow. Zaden test tresci tego nie lapal,
bo SQL byl skladniowo poprawny - psulo sie dopiero WYWOLANIE.

CZEGO TEN TEST NIE SPRAWDZA: zapytan, w ktorych parametry przychodza ze zmiennej (nie da sie ich
policzyc bez uruchomienia). Sprawdza wylacznie te, przy ktorych da sie policzyc jedno i drugie -
i tych jest w cm-agencie kilkaset.

Stdlib only. Uruchomienie: python cm-agent/tests/test_sql_parametry.py"""
import ast
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parents[1] / "app"
WOLANIA = ("fetchone", "fetchall", "execute")

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _zakres_nazw(wezel):
    """Napisy przypisane do nazw W TYM zakresie, z pominieciem zagniezdzonych funkcji.

    Zakres per funkcja, nie per plik - `conversation.py` ma DWIE rozne zmienne `base_q`
    w dwoch funkcjach i jeden slownik na caly plik mieszalby je ze soba (falszywy alarm
    na kodzie, ktory jest poprawny)."""
    nazwy = {}
    for w in ast.iter_child_nodes(wezel):
        if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for x in ast.walk(w):
            if (isinstance(x, ast.Assign) and len(x.targets) == 1
                    and isinstance(x.targets[0], ast.Name)
                    and isinstance(x.value, ast.Constant) and isinstance(x.value.value, str)):
                nazwy[x.targets[0].id] = x.value.value
    return nazwy


def _sql(wezel, nazwy):
    """Tresc zapytania, o ile da sie ja zlozyc ze stalych i nazw z tego zakresu."""
    if isinstance(wezel, ast.Constant) and isinstance(wezel.value, str):
        return wezel.value
    if isinstance(wezel, ast.Name):
        return nazwy.get(wezel.id)
    if isinstance(wezel, ast.BinOp) and isinstance(wezel.op, ast.Add):
        lewo, prawo = _sql(wezel.left, nazwy), _sql(wezel.right, nazwy)
        if lewo is not None and prawo is not None:
            return lewo + prawo
    return None


sprawdzone = 0
zle = []
for plik in sorted(APP.glob("*.py")):
    drzewo = ast.parse(plik.read_text(encoding="utf-8"))
    zakresy = [drzewo] + [z for z in ast.walk(drzewo)
                          if isinstance(z, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for zakres in zakresy:
        nazwy = _zakres_nazw(zakres)
        for w in ast.iter_child_nodes(zakres):
            if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for n in ast.walk(w):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                    continue
                if n.func.attr not in WOLANIA or not n.args:
                    continue
                sql = _sql(n.args[0], nazwy)
                if sql is None:
                    continue
                if len(n.args) < 2:
                    params = 0
                elif isinstance(n.args[1], (ast.Tuple, ast.List)):
                    params = len(n.args[1].elts)
                else:
                    continue  # parametry ze zmiennej - bez uruchomienia sie nie policzy
                sprawdzone += 1
                znaczniki = sql.count("%s")
                if znaczniki != params:
                    zle.append(f"{plik.name}:{n.lineno}: {znaczniki} znacznikow %s, "
                               f"{params} parametrow :: {' '.join(sql.split())[:90]}")

print(f"\n[zapytania] policzalnych wywolan: {sprawdzone}")
check("kazde policzalne zapytanie ma tyle parametrow, ile znacznikow %s",
      not zle, "\n         " + "\n         ".join(zle) if zle else "-")
check("test faktycznie cos policzyl (inaczej 'zero bledow' nic nie znaczy)",
      sprawdzone > 100, str(sprawdzone))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
