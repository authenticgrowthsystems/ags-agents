# -*- coding: utf-8 -*-
"""Test (10/08/2026, AP-315 druga tura): filtr ma POPRAWIAC tekst, a nie o nim ROZMAWIAC.

DOWOD, KTORY GO ZAMOWIL. Kilka godzin po wdrozeniu bezpiecznika gatunku przyszla karta
materialu "Granica miedzy dwoma agentami" z wariantem LinkedIn o tresci:

    "Rozumiem Twoja prosbe, ale widze niejasnosc: nie podales mi tekstu do poprawy. (...)
     Przeslij go, a otrzymasz zwrotnie wylacznie poprawiony tekst (zero komentarzy,
     zero em dashy, zero angielskich kalk)."

Trzy ostatnie sformulowania to DOSLOWNE echo promptu `polish_pl`. Model nie poprawil tekstu -
odpowiedzial O tekscie, a `_rewrite` oddal te odpowiedz jako tresc posta (`return out or text`).
Ten sam kanal odpowiada prawdopodobnie za publikacje z 04/08.

DLACZEGO POKRYCIE SLOW, A NIE KOLEJNA LISTA FRAZ. Bezpiecznik gatunku z rana dal na tej karcie
`([], [])` - ZERO trafien - bo to inna awaria tego samego rodzaju, o zupelnie innym slownictwie.
Lista zawsze bedzie o krok za modelem. Pokrycie mierzy co innego: **przerobka zachowuje slowa
oryginalu, rozmowa o przerobce ich nie ma.** Kazdy z trzech promptow wolajacych `_rewrite`
obiecuje zachowanie sensu i dlugosci, wiec to jest KONTRAKT tych filtrow, nie heurystyka.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314): nie tego, ze funkcja liczy jakas liczbe. Sprawdza
OBIE strony progu na realistycznych parach - prawdziwa odpowiedz-rozmowa musi wypasc pod progiem,
a cztery rodzaje UCZCIWEJ przerobki (korekta polszczyzny, usuniecie zakazanego slownictwa,
skrocenie, tlumaczenie-w-miejscu odrzucone jako niedozwolone) musza wypasc nad nim. Bramka,
ktora blokuje wszystko, jest tak samo bezuzyteczna jak ta, ktora nie blokuje nic.

OGRANICZENIE, KTORE TRZEBA ZNAC: dokladnego tekstu, ktory wszedl do `polish_pl` na produkcji,
nie mam - to wymagaloby odczytu wiersza z bazy, a sesja nie ma dostepu do serwera. Wejscie ponizej
jest ODTWORZONE (polski wariant o tej samej tresci, co material). Wyjscie jest PRAWDZIWE,
przepisane z karty w Telegramie.

Stdlib only. Uruchomienie: python cm-agent/tests/test_bramka_wyjscia_filtra.py"""
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parents[1]
APP = BASE / "app"

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# Ladujemy SAME funkcje bramki, bez pakietu - compliance.py ciagnie za soba db/tasks/generate,
# a bramka jest czysta arytmetyka na tekscie i nie potrzebuje niczego z tamtych.
_src = (APP / "compliance.py").read_text(encoding="utf-8")
_ns = {"re": re}
for _wzor in (r"^_OGONKI = .*$", r"^PROG_POKRYCIA_FILTRA = .*$", r"^_SLOWO_RE = .*$",
              r"^def pokrycie_slow\(.*?\n    return len\(we & wy\) / len\(we\)$"):
    _m = re.search(_wzor, _src, re.M | re.S)
    if not _m:
        print(f"FAIL: nie znalazlem w compliance.py wzorca {_wzor!r}")
        sys.exit(1)
    exec(_m.group(0), _ns)
pokrycie = _ns["pokrycie_slow"]
PROG = _ns["PROG_POKRYCIA_FILTRA"]

# ---------------------------------------------------------------- prawdziwe dane
# WYJSCIE: przepisane z karty w Telegramie, 10/08, material "Granica miedzy dwoma agentami".
ODPOWIEDZ_MODELU = """Rozumiem Twoją prośbę, ale widzę niejasność: nie podałeś mi tekstu do poprawy.

W wiadomości jest:
- Instrukcja, jak mam poprawiać polski
- Moja analiza jakiegoś polskiego tekstu (który sam sobie wymyśliłem)
- Pytanie o angielski/polski do LinkedIna

Potrzebuję od Ciebie:

Konkretny polski tekst, który chcesz, żebym poprawił na nienaganną polszczyznę.

Prześlij go, a otrzymasz zwrotnie wyłącznie poprawiony tekst (zero komentarzy, zero em dashy,
zero angielskich kalk)."""

# WEJSCIE: odtworzone (patrz naglowek) - polski wariant tresci materialu.
WEJSCIE_PL = """Jeden agent. Udający dwóch.

To pułapka, w którą wpada prawie każdy, kto projektuje system rozbity na agentów. Wygląda
jak podział pracy. W rzeczywistości to jeden agent z rozdwojeniem jaźni, opakowany w ładny
diagram.

Sprawdzian jest prosty. Granica między dwoma agentami to jedno zdanie: agent A robi X,
agent B robi Y, a jeśli X zawiedzie, to Z o tym wie. Jeśli nie umiesz napisać tego zdania,
granicy nie ma. Masz jednego agenta w przebraniu."""

print("\n[dowod] prawdziwa odpowiedz-rozmowa NIE jest przerobka:")
p = pokrycie(WEJSCIE_PL, ODPOWIEDZ_MODELU)
check("pokrycie ponizej progu", p < PROG, f"pokrycie={p:.2f} prog={PROG}")
check("i to nie jest ledwie ponizej", p < PROG / 2, f"pokrycie={p:.2f}")

print("\n[brak falszywych alarmow] UCZCIWE przerobki przechodza:")

KOREKTA = """Jeden agent. Udający dwóch.

To pułapka, w którą wpada prawie każdy, kto projektuje system rozbity na agentów. Wygląda
to jak podział pracy, ale w rzeczywistości jest to jeden agent z rozdwojeniem jaźni,
opakowany w ładny diagram.

Sprawdzian jest prosty. Granica między dwoma agentami to jedno zdanie: agent A robi X,
agent B robi Y, a jeśli X zawiedzie, Z o tym wie. Jeśli nie potrafisz napisać tego zdania,
granicy nie ma. Masz jednego agenta w przebraniu."""
p_kor = pokrycie(WEJSCIE_PL, KOREKTA)
check("korekta polszczyzny przechodzi", p_kor >= PROG, f"pokrycie={p_kor:.2f}")
check("korekta zostawia ZDECYDOWANA wiekszosc slow", p_kor > 0.85, f"pokrycie={p_kor:.2f}")

BEZ_ZAKAZANYCH = """Jeden agent. Udający dwóch.

To pułapka, w którą wpada prawie każdy przy projektowaniu systemu rozbitego na agentów.
Przypomina podział pracy. Naprawdę jest to jeden agent z rozdwojeniem jaźni w ładnym diagramie.

Sprawdzian jest prosty: granica między dwoma agentami to jedno zdanie. Agent A robi X,
agent B robi Y, a gdy X zawiedzie, Z o tym wie. Bez tego zdania granicy nie ma."""
p_bz = pokrycie(WEJSCIE_PL, BEZ_ZAKAZANYCH)
check("ostre przepisanie slownictwa przechodzi", p_bz >= PROG, f"pokrycie={p_bz:.2f}")

SKROT = """Jeden agent. Udający dwóch. Granica między dwoma agentami to jedno zdanie:
agent A robi X, agent B robi Y, a jeśli X zawiedzie, Z o tym wie. Nie umiesz go napisać?
Granicy nie ma."""
p_sk = pokrycie(WEJSCIE_PL, SKROT)
check("skrocenie o polowe nadal przechodzi", p_sk >= PROG, f"pokrycie={p_sk:.2f}")

print("\n[sedno] rozmowa i przerobka roznia sie o RZAD wielkosci, nie o wlos:")
check("najgorsza uczciwa przerobka bije rozmowe co najmniej trzykrotnie",
      min(p_kor, p_bz, p_sk) > 3 * p, f"uczciwe min={min(p_kor, p_bz, p_sk):.2f} rozmowa={p:.2f}")

print("\n[AP-313] ogonki nie zanizaja pokrycia:")
check("ten sam tekst bez ogonkow ma pokrycie 1.0",
      pokrycie("Udający jaźnią przebraniu", "udajacy jaznia przebraniu") == 1.0,
      repr(pokrycie("Udający jaźnią przebraniu", "udajacy jaznia przebraniu")))

print("\n[odpornosc] bramka nie moze padac na pustce (AP-314: ma padac ZAMKNIETA):")
check("puste wejscie daje 1.0, czyli przepuszcza", pokrycie("", "cokolwiek") == 1.0)
check("None na wejsciu daje 1.0", pokrycie(None, "cokolwiek") == 1.0)
check("puste wyjscie przy niepustym wejsciu daje 0.0", pokrycie("jakis dluzszy tekst", "") == 0.0)
check("None na wyjsciu daje 0.0", pokrycie("jakis dluzszy tekst", None) == 0.0)
check("tekst z samych krotkich slow nie wysadza", pokrycie("a b c do", "x") == 1.0)

print("\n[podlaczenie] _rewrite faktycznie pyta bramke i oddaje WEJSCIE:")
src = (APP / "compliance.py").read_text(encoding="utf-8")
check("bramka wolana w _rewrite",
      "if out and pokrycie_slow(text, out) < PROG_POKRYCIA_FILTRA:" in src)
i_bramka = src.find("if out and pokrycie_slow(text, out)")
blok = src[i_bramka:i_bramka + 260]
check("przy odrzuceniu wraca TEKST WEJSCIOWY, nie odpowiedz", "return text" in blok, blok[:200])
check("odrzucenie jest zglaszane, nie ciche", "_zglos_nie_przerobke" in blok)
check("zgloszenie ma wlasny typ w agent_logs",
      "COMPLIANCE_ODPOWIEDZ_NIE_PRZEROBKA" in src)
check("zgloszenie niesie poczatek odrzuconej odpowiedzi (inaczej nie da sie zdiagnozowac)",
      "poczatek_odrzuconej_odpowiedzi" in src)

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
