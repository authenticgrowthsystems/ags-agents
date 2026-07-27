"""Testy importu listy prospektow (27/07/2026, ogniwo 1 maszynki prospektowej).

Mina, ktora ten import musi przezyc: arkusze pomijaja puste komorki, wiec czytanie po
POZYCJI przesuwa kolumny (w bialej liscie tanca pod 'WWW' wpadal styl tanca). Dlatego
kolumny rozpoznajemy po ZNORMALIZOWANYM naglowku, a to, co nie wyglada jak adres,
nie jest adresem.

Stdlib only, bez bazy, bez sieci. Uruchomienie: python cm-agent/tests/test_prospect_import.py"""
import pathlib
import sys
import types

BASE = pathlib.Path(__file__).resolve().parents[1] / "app"

pkg = types.ModuleType("app")
pkg.__path__ = [str(BASE)]
sys.modules["app"] = pkg

db_stub = types.ModuleType("app.db")
LEJEK = []
EXEC = []
db_stub.fetchall = lambda sql, params=None: (list(LEJEK) if "sales_pipeline" in sql else [])
db_stub.fetchone = lambda sql, params=None: None
db_stub.execute = lambda sql, params=None: EXEC.append((sql, params))
sys.modules["app.db"] = db_stub

from app import prospect_import as pi  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("  OK   " if cond else "  FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def rec(**kw):
    base = {"nazwa": "X", "typ": "", "miasto": "", "region": "", "adres": "",
            "telefon": "", "email": "", "www": "", "osoba": "", "werdykt": "", "problemy": ""}
    base.update(kw)
    base["wynik"] = pi.wynik(base)
    return base


# ---------------- rozpoznanie kolumn ----------------
print("\n[kolumny] naglowek rozpoznawany mimo ogonkow i wielkosci liter:")
mapa, nieroz = pi._mapuj_kolumny(["ID", "Nazwa", "Typ podmiotu", "Miasto", "Województwo",
                                  "Telefon", "E-mail", "WWW", "Reprezentant / kontakt",
                                  "WERDYKT_BE", "PROBLEMY", "Cos dziwnego"])
check("nazwa znaleziona", mapa.get("nazwa") == 1, str(mapa))
check("wojewodztwo mimo ogonkow -> region", mapa.get("region") == 4, str(mapa))
check("e-mail z myslnikiem", mapa.get("email") == 6, str(mapa))
check("reprezentant -> osoba", mapa.get("osoba") == 8, str(mapa))
check("werdykt zrodla rozpoznany", mapa.get("werdykt") == 9, str(mapa))
check("nierozpoznane naglowki zwracane, nie przemilczane",
      "Cos dziwnego" in nieroz, str(nieroz))

mapa2, _ = pi._mapuj_kolumny(["firma", "city", "phone", "mail", "url"])
check("dziala tez na liscie angielskiej",
      mapa2.get("nazwa") == 0 and mapa2.get("miasto") == 1 and mapa2.get("email") == 3, str(mapa2))


# ---------------- czyszczenie wartosci ----------------
print("\n[wartosci] telefon, mail, domena:")
check("dwa numery po sredniku -> pierwszy",
      pi._czysty_tel("669 757 675; 669 455 668").replace(" ", "") == "669757675")
check("smiec zamiast numeru -> pusto", pi._czysty_tel("brak") == "")
check("za krotki numer odrzucony", pi._czysty_tel("12 34") == "")
check("mail wyluskany z tekstu", pi._czysty_mail("kontakt: Ala@Szkola.PL ") == "ala@szkola.pl")
check("brak maila -> pusto", pi._czysty_mail("nie podano") == "")
check("domena bez www i sciezki", pi._domena("https://www.Iskierka.pl/kontakt/") == "iskierka.pl")
check("tekst bez kropki to nie domena", pi._domena("taniec") == "",
      "to jest ta mina: w kolumnie WWW bialej listy siedzial styl tanca")


# ---------------- kwalifikacja ----------------
print("\n[kwalifikacja] wynik liczy KONTAKTOWALNOSC, nie wartosc firmy:")
pelny = rec(email="a@b.pl", telefon="600 100 200", www="https://b.pl", osoba="Jan")
check("komplet kanalow = 100", pelny["wynik"] == 100, str(pelny["wynik"]))
check("sam telefon wazy mniej niz sam mail",
      rec(telefon="600 100 200")["wynik"] < rec(email="a@b.pl")["wynik"])
check("brak MX odejmuje", rec(email="a@wp.pl", problemy="domena wp.pl bez MX")["wynik"]
      < rec(email="a@wp.pl")["wynik"])
check("werdykt PODEJRZANE odejmuje",
      rec(email="a@b.pl", werdykt="PODEJRZANE")["wynik"] < rec(email="a@b.pl")["wynik"])
check("wynik nigdy ponizej zera",
      rec(problemy="nieczynne, bez MX", werdykt="PODEJRZANE")["wynik"] == 0)
check("ten sam rekord daje ten sam wynik (idempotencja)",
      pi.wynik(pelny) == pi.wynik(pelny) == 100)


# ---------------- plan importu ----------------
print("\n[plan] dedup wobec bazy I wewnatrz pliku:")
LEJEK[:] = [{"prospect_name": "Iskierka Lancut", "prospect_url": "https://iskierka.pl",
             "contact_email": "stary@mail.pl", "notes": ""}]
rekordy = [
    rec(nazwa="Iskierka Lancut", email="nowy@mail.pl"),                       # dup po nazwie
    rec(nazwa="Inna Szkola", www="https://iskierka.pl", telefon="600 100 200"),  # dup po domenie
    rec(nazwa="Trzecia", email="stary@mail.pl"),                              # dup po mailu
    rec(nazwa="Czwarta", email="ok@ok.pl", telefon="600 100 200"),            # wchodzi
    rec(nazwa="Czwarta", email="ok@ok.pl"),                                   # dup WEWNATRZ pliku
    rec(nazwa="Piata"),                                                        # bez kanalu
    rec(nazwa="Szosta", email="s@s.pl", werdykt="PODEJRZANE"),                # odsiane domyslnie
]
do_zapisu, dupy, odsiane = pi.plan(rekordy)
nazwy = [r["nazwa"] for r in do_zapisu]
check("wchodzi tylko jeden rekord", nazwy == ["Czwarta"], str(nazwy))
check("duplikat po nazwie zlapany", any("nazwa" in p for _, p in dupy), str(dupy))
check("duplikat po domenie zlapany", any("domena" in p for _, p in dupy), str(dupy))
check("duplikat po mailu zlapany", any("mail" in p for _, p in dupy), str(dupy))
check("duplikat WEWNATRZ pliku zlapany", len(dupy) == 4, str([p for _, p in dupy]))
check("rekord bez kanalu odsiany, nie zapisany",
      any("kanalu" in p for _, p in odsiane), str(odsiane))
check("PODEJRZANE odsiane domyslnie", any("PODEJRZANE" in p for _, p in odsiane), str(odsiane))

# Franczyza: ta sama domena, rozne miasta, rozne maile = TYLU klientow, ile oddzialow.
# Regresja z prawdziwych danych 27/07: dedup po samej domenie wyrzucil trzy oddzialy
# Egurroli (Katowice, Krakow, Warszawa) jako duplikaty jednego wpisu.
LEJEK[:] = []
siec = [
    rec(nazwa="Egurrola Dance Studio Warszawa", miasto="Warszawa",
        www="https://egurrola.com", email="warszawa@egurrola.com"),
    rec(nazwa="Katowice Egurrola Dance Studio", miasto="Katowice",
        www="https://egurrola.com", email="katowice@egurrola.com"),
    rec(nazwa="Krakow Egurrola Dance Studio", miasto="Krakow",
        www="https://egurrola.com", email="krakow@egurrola.com"),
]
do_siec, dup_siec, _ = pi.plan(siec)
check("oddzialy sieci NIE sa duplikatami (domena plus miasto)",
      len(do_siec) == 3 and not dup_siec,
      f"zapisane={len(do_siec)}, duplikaty={[p for _, p in dup_siec]}")

# ...ale dwa razy ten sam oddzial to juz duplikat.
ten_sam = [rec(nazwa="Egurrola Katowice", miasto="Katowice", www="https://egurrola.com",
               telefon="600 100 200"),
           rec(nazwa="Egurrola Dance Katowice", miasto="Katowice", www="https://egurrola.com",
               telefon="600 100 300")]
do_ts, dup_ts, _ = pi.plan(ten_sam)
check("ten sam oddzial dwa razy = duplikat", len(do_ts) == 1 and len(dup_ts) == 1,
      f"zapisane={len(do_ts)}, duplikaty={len(dup_ts)}")

LEJEK[:] = [{"prospect_name": "Iskierka Lancut", "prospect_url": "https://iskierka.pl",
             "contact_email": "stary@mail.pl", "notes": ""}]
do2, _, odsiane2 = pi.plan(rekordy, tylko_ok=False)
check("--wszystkie przepuszcza PODEJRZANE",
      "Szosta" in [r["nazwa"] for r in do2], str([r["nazwa"] for r in do2]))
check("ale brak kanalu odsiany nawet wtedy",
      any("kanalu" in p for _, p in odsiane2), str(odsiane2))

posortowane = [r["wynik"] for r in pi.plan([rec(nazwa="A", email="a@a.pl"),
                                            rec(nazwa="B", email="b@b.pl", telefon="600 100 200",
                                                www="https://b.pl", osoba="Jan")])[0]]
check("najlepiej kontaktowalne ida pierwsze", posortowane == sorted(posortowane, reverse=True),
      str(posortowane))


# ---------------- zapis i budzenie ----------------
print("\n[zapis] zimna lista laduje POZA gra, budzenie nie ustawia terminu:")
EXEC.clear()
pi.zapisz([rec(nazwa="Czwarta", email="ok@ok.pl", miasto="Opole")], "taniec", "lista.xlsx")
sql, params = EXEC[-1]
check("etap 'parked', nie 'prospect'", "'parked'" in sql, sql)
check("nisza zapisana", "niche" in sql and "taniec" in params, str(params))
check("wynik kwalifikacji zapisany", "lead_score" in sql, sql)
check("zrodlo oznaczone jako lista", "'lista'" in sql, sql)
check("notatka niesie pochodzenie", any("import lista.xlsx" in str(p) for p in params), str(params))

EXEC.clear()
pi.wake(["a", "b"])
sql_w = EXEC[-1][0]
check("budzenie ustawia etap prospect", "stage='prospect'" in sql_w, sql_w)
check("budzenie NIE ustawia terminu", "next_followup_at" not in sql_w,
      "inaczej straznik terminow zrobilby tyle bramek, ilu obudzonych")
check("pusta lista nie generuje zapisu", pi.wake([]) == 0)


# ---------------- wzbogacanie istniejacych wierszy ----------------
print("\n[wzbogacanie] duplikat nie jest smieciem, tylko moze niesc brakujace dane:")
LEJEK[:] = [
    {"id": "p1", "prospect_name": "Dance4Kids", "contact_email": None, "contact_phone": None,
     "prospect_url": None, "stage": "prospect"},
    {"id": "p2", "prospect_name": "Klub Sportowy StandART", "contact_email": "recepcja@standart.org",
     "contact_phone": "510-555-099", "prospect_url": None, "stage": "qualified"},
    {"id": "p3", "prospect_name": "Wroclawska Stepownia", "contact_email": "dudzikdariusz@gmail.com",
     "contact_phone": None, "prospect_url": None, "stage": "qualified"},
]
lista = [
    rec(nazwa="Dance4Kids", email="dance4kids.edu@gmail.com", telefon="530 749 205"),
    rec(nazwa="Klub Sportowy StandART", email="biuro@klubsportowystandart.org",
        telefon="510 555 099"),
    rec(nazwa="Wroclawska Stepownia", email="dudzikdariusz@gmail.com", telefon="501 130 016"),
    rec(nazwa="Kogo Nie Ma W Lejku", email="x@x.pl"),
]
uzup, konf, bez = pi.plan_wzbogacenia(lista)
nazwy_uzup = {w["prospect_name"] for w, _, _ in uzup}
check("pusty kontakt zostaje uzupelniony", "Dance4Kids" in nazwy_uzup, str(nazwy_uzup))
check("brakujacy telefon dolozony przy istniejacym mailu",
      any(w["prospect_name"] == "Wroclawska Stepownia" and "contact_phone" in p
          for w, _, p in uzup), str([(w["prospect_name"], p) for w, _, p in uzup]))
check("istniejacy mail NIE jest nadpisywany po cichu",
      not any("contact_email" in p for w, _, p in uzup if w["prospect_name"].endswith("StandART")),
      str([(w["prospect_name"], p) for w, _, p in uzup]))
check("rozny mail zglaszany jako konflikt do decyzji czlowieka",
      any(w["prospect_name"].endswith("StandART") for w, _, _ in konf), str(konf))
check("ten sam mail to nie konflikt",
      not any(w["prospect_name"] == "Wroclawska Stepownia" for w, _, s in konf
              for k, _, _ in s if k == "contact_email"), str(konf))
check("podmiot spoza lejka jest pomijany, nie dopisywany",
      all(w["prospect_name"] != "Kogo Nie Ma W Lejku" for w, _, _ in uzup))

EXEC.clear()
pi.wzbogac(uzup, "lista.xlsx")
check("wzbogacanie robi UPDATE, nie INSERT",
      all("UPDATE sales_pipeline" in s for s, _ in EXEC) and EXEC, str(EXEC[:1]))
check("nie dotyka etapu", not any("stage" in s for s, _ in EXEC), str(EXEC[:1]))
check("dopisuje slad w notatce", any("uzupelnione z listy" in str(p) for _, p in EXEC), str(EXEC[:1]))

print("\n" + ("WSZYSTKO PRZESZLO" if not FAILS else f"BLEDY: {FAILS}"))
sys.exit(1 if FAILS else 0)
