# -*- coding: utf-8 -*-
"""Test (11/08/2026): przeklad ma byc PRZEKLADEM, a `translate_text` ma wiedziec, czy jego wynik
idzie do publikacji.

DWA PROBLEMY, JEDNA FUNKCJA.

(1) KOPIA PL ROZJEZDZA SIE ZE ZRODLEM. Karta z 10/08 niosla polski "odpowiednik do przegladu"
    ze zdaniem, ktorego w angielskim oryginale NIE BYLO ("Albo: Agent A decyduje, czy w ogole
    odpowiadamy. Agent B decyduje jak."). Ta kopia jest opisana na karcie jako tekst DO PRZEGLADU -
    czyli to JA czyta czlowiek, zatwierdzajac. Gdy rozni sie trescia od tego, co wychodzi,
    **bramka ludzka ocenia nie ten tekst**. Rodzina AP-315: kontrola pyta o co innego niz publikacja.

(2) TA SAMA FUNKCJA PRODUKUJE TEKSTY, KTORE PUBLIKUJA. `translate_text` ma cztery wywolania
    i **dwa z nich pisza do `post_queue`**: straznik jezyka w `channels.stage_variant` (polski
    wariant na kanale EN tlumaczony PRZED zapisem do kolejki) oraz wklejka wlasnej tresci
    w `conversation`. A prompt mowil im obu: "To kopia do przegladu wlasciciela, NIE do publikacji".
    Model dostawal nieprawde o przeznaczeniu swojego wyniku - AP-312 w wersji dla modelu.

CZEGO TEN TEST PILNUJE NAJMOCNIEJ (AP-314): **nie tego, ze funkcja cos zwraca, tylko ze lapie
PRZYPADEK, DLA KTOREGO POWSTALA.** Pierwsza wersja `sprawdz_przeklad` mierzyla akapity, liczby
i dlugosc - i na prawdziwym rozjezdzie z 10/08 dala ZERO zastrzezen, bo dodane zdanie nie zmienia
liczby akapitow, a 90 znakow w 700 miesci sie w pasmie dlugosci. Miare zdan dolozono dopiero
po tym pomiarze. Ten test trzyma OBIE strony progu na prawdziwych parach.

Stdlib only. Uruchomienie: python -X utf8 cm-agent/tests/test_przeklad_wiernosc.py"""
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


# Ladujemy SAME funkcje czyste: `generate` ciagnie anthropic/db, a te tutaj sa arytmetyka na tekscie.
_src = (APP / "generate.py").read_text(encoding="utf-8")
_ns = {"re": re}
for _wzor in (r"^_CYFRY = .*$", r"^_KONIEC_ZDANIA = .*$",
              r"^def _zdan\(.*?\n    return len\(\[s for s in _KONIEC_ZDANIA\.split\(\(t or \"\"\)\.strip\(\)\) if len\(s\.strip\(\)\) > 2\]\)$",
              r"^def sprawdz_przeklad\(.*?\n    return uwagi$"):
    _m = re.search(_wzor, _src, re.M | re.S)
    if not _m:
        print(f"FAIL: nie znalazlem w generate.py wzorca {_wzor!r}")
        sys.exit(1)
    exec(_m.group(0), _ns)
sprawdz = _ns["sprawdz_przeklad"]

# ---------------------------------------------------------------- prawdziwe teksty z karty
ZRODLO_EN = """I built four agents that started pinging back and forth all afternoon.

So I asked: what does each agent own that the other one doesn't?

If you can't answer that in one sentence, you don't have two agents. You have one agent wearing two name tags.

A real boundary is a sentence like this: Agent A owns matching a request to a known pattern. Agent B owns executing that pattern against live data.

In a twelve-agent system, that same ambiguity compounds fast."""

# WIERNE: para EN/PL przepisana z karty 14:09 - tlumacz nie dodal ani nie zgubil zdania.
PRZEKLAD_WIERNY = """Zbudowałem czterech agentów, którzy pingowali się nawzajem przez całe popołudnie.

Więc zapytałem: co każdy agent posiada, czego nie ma drugi?

Jeśli nie umiesz odpowiedzieć w jednym zdaniu, nie masz dwóch agentów. Masz jednego agenta w dwóch identyfikatorach.

Prawdziwa granica to zdanie takie jak to: Agent A odpowiada za dopasowanie żądania do znanego wzorca. Agent B odpowiada za wykonanie tego wzorca na danych na żywo.

W systemie dwunastu agentów ta sama niejednoznaczność narasta szybko."""

# ROZJECHANE: to samo plus zdanie, ktorego w zrodle NIE BYLO - dokladnie jak na karcie 10/08.
PRZEKLAD_ROZJECHANY = PRZEKLAD_WIERNY.replace(
    "Agent B odpowiada za wykonanie tego wzorca na danych na żywo.",
    "Agent B odpowiada za wykonanie tego wzorca na danych na żywo. "
    "Albo: Agent A decyduje, czy w ogóle odpowiadamy. Agent B decyduje jak.")

print("\n[dowod] PRAWDZIWY rozjazd z karty 10/08 jest zlapany:")
u = sprawdz(ZRODLO_EN, PRZEKLAD_ROZJECHANY)
check("sa zastrzezenia", bool(u), repr(u))
check("zastrzezenie mowi o ZDANIACH", any("zdania:" in x for x in u), repr(u))
check("i nazywa kierunek: przeklad DODAL", any("DODAL" in x for x in u), repr(u))

print("\n[brak falszywych alarmow] wierny przeklad tej samej tresci przechodzi:")
check("zero zastrzezen", sprawdz(ZRODLO_EN, PRZEKLAD_WIERNY) == [],
      repr(sprawdz(ZRODLO_EN, PRZEKLAD_WIERNY)))

print("\n[anty-regresja] miary sprzed 11/08 NIE wystarczaly - dlatego doszly zdania:")
# Ta sekcja pilnuje, zeby nikt nie "uproscil" funkcji z powrotem do akapitow i dlugosci.
akapity_z = len([p for p in ZRODLO_EN.split("\n\n") if p.strip()])
akapity_w = len([p for p in PRZEKLAD_ROZJECHANY.split("\n\n") if p.strip()])
check("akapity same NIE odroznily rozjazdu", akapity_z == akapity_w, f"{akapity_z} vs {akapity_w}")
p = len(PRZEKLAD_ROZJECHANY) / len(ZRODLO_EN)
check("dlugosc sama NIE odroznila rozjazdu (miesci sie w pasmie)", 0.6 <= p <= 1.8, f"{p:.0%}")

print("\n[liczby] cyfry przezywaja tlumaczenie, wiec ich brak to sygnal:")
check("zgubiona liczba", any("zgubione liczby" in x
      for x in sprawdz("We shipped 12 posts in 4 days.", "Wyslalismy posty w cztery dni.")))
check("dorobiona liczba", any("ktorych nie bylo" in x
      for x in sprawdz("We shipped posts fast.", "Wyslalismy 12 postow.")))
check("te same liczby nie alarmuja",
      sprawdz("We shipped 12 posts.", "Wyslalismy 12 postow.") == [])

print("\n[gruby rozjazd] obciecie i zapasc struktury:")
u2 = sprawdz(ZRODLO_EN, PRZEKLAD_WIERNY[:120])
check("skrocenie do 26% zrodla jest zlapane", bool(u2), repr(u2))
check("i mowi o dlugosci", any("dlugosc" in x for x in u2), repr(u2))

print("\n[odpornosc] pustka nie wysadza i nie alarmuje na pusto:")
check("puste zrodlo", sprawdz("", "cokolwiek") == [])
check("pusty wynik", sprawdz("cos", "") == [])
check("None", sprawdz(None, None) == [])
check("krotki tekst nie alarmuje na jedno zdanie roznicy",
      sprawdz("Jedno zdanie. Drugie zdanie.", "One sentence. Second sentence. Third.") == [])

print("\n[podlaczenie] kazde wywolanie wie, czy publikuje:")
gen = (APP / "generate.py").read_text(encoding="utf-8")
ch = (APP / "channels.py").read_text(encoding="utf-8")
cv = (APP / "conversation.py").read_text(encoding="utf-8")
wk = (APP / "worker.py").read_text(encoding="utf-8")
check("translate_text przyjmuje do_publikacji", "def translate_text(text, target_lang, content_item_id=None, do_publikacji=False)" in gen)
check("prompt mowi PRAWDE zaleznie od przeznaczenia",
      "PUBLIKUJE SIE w tej postaci" in gen and "nie do publikacji" in gen)
check("prompt zabrania dodawania zdan", "NIE dodawaj zdan, ktorych nie ma w zrodle" in gen)
# Asercje sprawdzaja WYWOLANIE, nie sam napis. Pierwsza wersja pytala o "do_publikacji=True"
# w calym pliku - i przechodzila na KOMENTARZU obok wywolania, gdy sam argument zniknal.
# Zlapane celowym przywroceniem wady 11/08: test swiecil na zielono przy zepsutym kodzie.
# To jest AP-314 popelniony we wlasnym tescie.
check("straznik jezyka publikuje -> flaga w WYWOLANIU",
      'content_item_id=item.get("id"), do_publikacji=True)' in ch,
      "brak flagi w wywolaniu translate_text w channels.stage_variant")
check("wklejka tresci publikuje -> flaga w WYWOLANIU",
      "generate.translate_text(raw, pub_lang, do_publikacji=True)" in cv,
      "brak flagi w wywolaniu translate_text w conversation")
check("kopia do przegladu NIE podaje flagi (domyslnie False)",
      'generate.translate_text(canonical, comm, content_item_id=item["id"])' in wk)
check("straznik jezyka zglasza zastrzezenia do agent_logs", "przeklad do publikacji rozjechany" in ch)
check("karta pokazuje rozjazd kopii CZLOWIEKOWI", "TA KOPIA ROZJECHALA SIE ZE ZRODLEM" in wk)
check("i mowi, czym sie kierowac", "Oceniaj po tekscie, ktory WYCHODZI" in wk)
check("wklejka mowi o rozjezdzie w paragonie", "przeklad rozjechal sie ze zrodlem" in cv)

print()
if FAILS:
    print(f"NIEUDANE ({len(FAILS)}): " + "; ".join(FAILS))
    sys.exit(1)
print("Wszystko przeszlo.")
