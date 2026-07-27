# -*- coding: utf-8 -*-
"""IMPORT LISTY PROSPEKTOW do lejka - ogniwo 1 maszynki prospektowej (27/07/2026).

Kampania wychodzi poza szkoly tanca na cztery rodziny nisz. Lancuch od niszy do platnego
klienta ma osiem ogniw i mielismy cztery: nie ma niczego, co wysyla maila, nie ma zadnego
zrodla rejestrowego, a `/prospect` przyjmuje JEDEN podmiot naraz. Biala lista tanca
(276 wierszy) powstala poza systemem i system o niej nie wiedzial.

DLACZEGO IMPORT JEST PIERWSZY: definiuje KONTRAKT, w ktory wpinaja sie dwa pozostale ogniwa.
Zbieracz z rejestrow musi miec gdzie odlozyc wynik, wysylka musi miec skad wziac adresatow.
Zbudowana najpierw wysylka wymusilaby dorazny ksztalt odbiorcy i przerobke przy zbieraczu.

DECYZJA PROJEKTOWA (wazna, latwo ja przeoczyc): import lqduje w etapie **`parked`**, nie
`prospect`. Wrzucenie 161 zimnych wierszy jako otwartych zrobiloby z lejka liste zyczen -
dokladnie ta nieprawde, ktora Manager kazal usunac 26/07, tylko trzynascie razy wieksza.
Zimna lista JEST w bazie i NIE jest w grze. Osobna komenda `wake` budzi N najlepszych
z danej niszy, gdy Tomasz faktycznie siada do wysylki.

Obudzony wiersz celowo NIE dostaje `next_followup_at`. Termin pojawia sie dopiero przy
odhaczeniu wysylki (`sales.mark_outreach_sent`). Inaczej straznik terminow zrobilby
czterdziesci bramek z rzedu.

KWALIFIKACJA (`lead_score`) odpowiada na JEDNO pytanie: czy da sie do nich napisac i czy
jest do kogo. To nie jest ocena wartosci prospekta - te robi czlowiek i research, nie
arytmetyka na kolumnach arkusza.

Uruchomienie (SSH, Tomasz):
  docker exec cm-agent python -m app.prospect_import dry   <plik.xlsx> <nisza> [--wszystkie]
  docker exec cm-agent python -m app.prospect_import apply <plik.xlsx> <nisza> [--wszystkie]
  docker exec cm-agent python -m app.prospect_import wake-dry   <nisza> <ile>
  docker exec cm-agent python -m app.prospect_import wake-apply <nisza> <ile>
"""
import re
import sys
import unicodedata

from . import db

# Kolumny rozpoznajemy po ZNORMALIZOWANYM naglowku (male litery, bez ogonkow), bo listy
# z roznych zrodel nazywaja to samo inaczej, a polskie znaki w naglowku potrafia przyjsc
# w dowolnym kodowaniu. Pierwszy trafiony alias wygrywa.
_KOLUMNY = {
    "nazwa": ("nazwa", "name", "firma", "podmiot", "nazwa firmy", "nazwa podmiotu"),
    "typ": ("typ podmiotu", "typ", "kategoria", "branza"),
    "miasto": ("miasto", "city", "miejscowosc"),
    "region": ("wojewodztwo", "region", "voivodeship"),
    "adres": ("adres", "address", "ulica"),
    "telefon": ("telefon", "tel", "phone", "numer telefonu", "kontakt telefoniczny"),
    "email": ("e-mail", "email", "mail", "adres e-mail"),
    "www": ("www", "strona", "url", "website", "strona www"),
    "osoba": ("reprezentant / kontakt", "reprezentant", "osoba", "kontakt", "osoba kontaktowa"),
    "werdykt": ("werdykt_be", "werdykt", "status weryfikacji", "ocena"),
    "problemy": ("problemy", "uwagi", "notatki"),
}

_MAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_TEL_RE = re.compile(r"\d[\d\s\-()]{7,}")


def _norm(s):
    """Male litery, bez ogonkow, sklejone biale znaki. Do porownan, nigdy do zapisu."""
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def _domena(url):
    """Domena bez www i sciezki - klucz deduplikacji mocniejszy niz nazwa."""
    u = _norm(url).replace("https://", "").replace("http://", "")
    u = u.split("/")[0].split("?")[0]
    u = u[4:] if u.startswith("www.") else u
    return u if "." in u else ""


def _mapuj_kolumny(naglowek):
    """Indeks kolumny per pole. Zwraca (mapa, nierozpoznane_naglowki)."""
    mapa, uzyte = {}, set()
    znorm = [_norm(h) for h in naglowek]
    for pole, aliasy in _KOLUMNY.items():
        for alias in aliasy:
            if alias in znorm:
                i = znorm.index(alias)
                if i not in uzyte:
                    mapa[pole] = i
                    uzyte.add(i)
                    break
    nierozpoznane = [h for i, h in enumerate(naglowek) if i not in uzyte and str(h or "").strip()]
    return mapa, nierozpoznane


def _wartosc(wiersz, mapa, pole):
    i = mapa.get(pole)
    if i is None or i >= len(wiersz):
        return ""
    return str(wiersz[i] or "").strip()


def _czysty_mail(s):
    m = _MAIL_RE.search(s or "")
    return m.group(0).lower() if m else ""


def _czysty_tel(s):
    """Pierwszy SENSOWNY numer z pola.

    Listy trzymaja po dwa numery ('669 757 675; 669 455 668'), a chciwy regex sklejal je
    w jeden osiemnastocyfrowy potworek i odrzucal jako za dlugi. Dlatego najpierw dzielimy
    pole po separatorach, dopiero potem szukamy numeru w kazdym kawalku."""
    for kawalek in re.split(r"[;,/]|\blub\b|\bi\b", str(s or ""), flags=re.IGNORECASE):
        m = _TEL_RE.search(kawalek)
        if not m:
            continue
        cyfry = re.sub(r"\D", "", m.group(0))
        if 9 <= len(cyfry) <= 15:
            return m.group(0).strip()
    return ""


def wynik(rec):
    """Kwalifikacja KONTAKTOWALNOSCI 0-100, deterministyczna (warunek idempotencji dry-run).

    Waga idzie za tym, czym mozna FAKTYCZNIE zaczac rozmowe: mail wazy najwiecej, bo
    wysylka bedzie mailowa; telefon jest drugi, bo dziala od razu, ale nie skaluje.
    Znane problemy z listy zrodlowej (np. 'domena wp.pl bez MX') odejmuja - ktos juz
    to sprawdzil i nie bedziemy sprawdzac drugi raz.
    """
    p = 0
    if rec["email"]:
        p += 45
    if rec["telefon"]:
        p += 25
    if rec["www"]:
        p += 15
    if rec["osoba"]:
        p += 15
    problem = _norm(rec.get("problemy"))
    if "bez mx" in problem or "brak mx" in problem:
        p -= 30          # adres istnieje na papierze, poczta nie dojdzie
    if "nieczynn" in problem or "zamkni" in problem:
        p -= 40
    if _norm(rec.get("werdykt")) == "podejrzane":
        p -= 15
    return max(0, min(100, p))


def czytaj(sciezka):
    """Zwraca (rekordy, nierozpoznane_naglowki, odrzucone_bez_nazwy)."""
    import openpyxl
    wb = openpyxl.load_workbook(sciezka, read_only=True, data_only=True)
    ws = wb.active
    wiersze = list(ws.iter_rows(values_only=True))
    if not wiersze:
        return [], [], 0
    mapa, nierozpoznane = _mapuj_kolumny(wiersze[0])
    if "nazwa" not in mapa:
        raise ValueError("W arkuszu nie ma kolumny z nazwa podmiotu (szukalem: "
                         + ", ".join(_KOLUMNY["nazwa"]) + ")")
    rekordy, bez_nazwy = [], 0
    for w in wiersze[1:]:
        nazwa = _wartosc(w, mapa, "nazwa")
        if not nazwa:
            bez_nazwy += 1
            continue
        rec = {
            "nazwa": nazwa[:200],
            "typ": _wartosc(w, mapa, "typ"),
            "miasto": _wartosc(w, mapa, "miasto"),
            "region": _wartosc(w, mapa, "region"),
            "adres": _wartosc(w, mapa, "adres"),
            "telefon": _czysty_tel(_wartosc(w, mapa, "telefon")),
            "email": _czysty_mail(_wartosc(w, mapa, "email")),
            "www": _wartosc(w, mapa, "www"),
            "osoba": _wartosc(w, mapa, "osoba"),
            "werdykt": _wartosc(w, mapa, "werdykt"),
            "problemy": _wartosc(w, mapa, "problemy"),
        }
        # Kolumna WWW bywa zanieczyszczona (w bialej liscie tanca wpadl tam styl tanca),
        # wiec za adres uznajemy tylko to, co wyglada jak adres.
        if not _domena(rec["www"]):
            rec["www"] = ""
        rec["wynik"] = wynik(rec)
        rekordy.append(rec)
    return rekordy, nierozpoznane, bez_nazwy


def _klucz_domeny(dom, miasto):
    """Domena SAMA nie wystarczy do deduplikacji.

    Dowod z prawdziwej listy (27/07, pierwszy dry na bialej liscie tanca): siec Egurrola
    ma jedna domene i osobny oddzial w Katowicach, Krakowie, Warszawie i Grodzisku, kazdy
    z wlasnym mailem (grodzisk@egurrola.com). Dedup po samej domenie wyrzucil trzy REALNE
    prospekty jako duplikaty. Franczyza to nie duplikat - to tylu klientow, ile oddzialow.
    """
    return f"{dom}|{_norm(miasto)}" if dom else ""


def _istniejace():
    """Klucze juz obecne w lejku: znormalizowana nazwa, domena+miasto, mail."""
    rows = db.fetchall(
        """SELECT prospect_name, prospect_url, contact_email, notes
           FROM sales_pipeline WHERE brand_id='AGS'""") or []
    nazwy, domeny, maile = set(), set(), set()
    for r in rows:
        nazwy.add(_norm(r.get("prospect_name")))
        # Miasto istniejacego wiersza siedzi w notatce importu ("miasto: X") - gdy go nie ma,
        # klucz zostaje sam z domena i zachowuje sie jak dawniej (ostrozniej, nie luzniej).
        m_city = re.search(r"miasto:\s*([^|]+)", r.get("notes") or "")
        d = _domena(r.get("prospect_url"))
        if d:
            domeny.add(_klucz_domeny(d, m_city.group(1) if m_city else ""))
        m = (r.get("contact_email") or "").strip().lower()
        if m:
            maile.add(m)
    return nazwy, domeny, maile


def _rozne(kolumna, stara, nowa):
    """Czy to NAPRAWDE dwie rozne wartosci, czy ten sam fakt w innym zapisie.

    Pierwszy dry na produkcji (27/07) pokazal cztery "konflikty", z ktorych trzy byly szumem:
    `scorpiondanceteam.com` kontra `https://scorpiondanceteam.com/`, `510-555-099` kontra
    `510 555 099`, `lacultura.pl` kontra `https://lacultura.pl/`. Realny konflikt byl JEDEN
    (mail StandART: recepcja@ kontra biuro@) i utonal wsrod reszty.

    To ta sama wada co piec identycznych bramek: lista rzeczy do rozstrzygniecia, z ktorych
    wiekszosc nie wymaga rozstrzygniecia, uczy czlowieka przewijac zamiast czytac."""
    if kolumna == "prospect_url":
        return _domena(stara) != _domena(nowa)
    if kolumna == "contact_phone":
        return re.sub(r"\D", "", stara) != re.sub(r"\D", "", nowa)
    return _norm(stara) != _norm(nowa)


def _wiersze_lejka():
    return db.fetchall(
        """SELECT id, prospect_name, contact_email, contact_phone, prospect_url, stage
           FROM sales_pipeline WHERE brand_id='AGS'""") or []


def plan_wzbogacenia(rekordy):
    """Co lista WNOSI do wierszy, ktore juz sa w lejku.

    Powstalo z uwagi Tomasza 27/07: "prospekty nie sa martwe, tylko nieobsluzone". Mial racje
    podwojnie. Import traktowal trafienie w istniejacy wiersz jako duplikat i WYRZUCAL rekord,
    patrzac wylacznie na to, czy nazwa jest juz w lejku - a nie na to, czy przynosi cos, czego
    lejek NIE MA. Dowod: wszystkie dwanascie "duplikatow" z bialej listy tanca mialo mail
    i telefon, podczas gdy dziewiec odpowiadajacych im wierszy lejka swiecilo "brak kontaktu".
    Ci ludzie nie byli zaniedbani - system nigdy nie podal Tomaszowi ich adresow.

    Zwraca (uzupelnienia, konflikty, bez_zmian). Konflikt = lejek MA juz inna wartosc;
    takiego nie nadpisujemy po cichu, tylko pokazujemy czlowiekowi.
    """
    lejek = _wiersze_lejka()
    po_nazwie = {}
    for w in lejek:
        po_nazwie[_norm(w.get("prospect_name"))] = w
    uzupelnienia, konflikty, bez_zmian = [], [], 0
    for rec in rekordy:
        w = po_nazwie.get(_norm(rec["nazwa"]))
        if not w:
            continue
        pola, sporne = {}, []
        for kol, nowa in (("contact_email", rec["email"]),
                          ("contact_phone", rec["telefon"]),
                          ("prospect_url", rec["www"])):
            stara = (w.get(kol) or "").strip()
            if not nowa:
                continue
            if not stara:
                pola[kol] = nowa
            elif not _rozne(kol, stara, nowa):
                continue           # ta sama wartosc, inny zapis - nie zawracamy glowy
            else:
                sporne.append((kol, stara, nowa))
        if pola:
            uzupelnienia.append((w, rec, pola))
        if sporne:
            konflikty.append((w, rec, sporne))
        if not pola and not sporne:
            bez_zmian += 1
    return uzupelnienia, konflikty, bez_zmian


def wzbogac(uzupelnienia, zrodlo):
    """Dopisuje WYLACZNIE puste kolumny. Niczego nie nadpisuje - konflikty ida do czlowieka."""
    n = 0
    for w, rec, pola in uzupelnienia:
        sets = ", ".join(f"{k}=%s" for k in pola)
        db.execute(
            f"""UPDATE sales_pipeline SET {sets}, updated_at=NOW(),
                notes = COALESCE(notes,'') || %s WHERE id=%s""",
            (*pola.values(), f"\n27/07 uzupelnione z listy {zrodlo}: " + ", ".join(pola), w["id"]))
        n += 1
    return n


def plan(rekordy, tylko_ok=True):
    """Dzieli rekordy na (do_zapisu, duplikaty, odsiane). Czysty odczyt bazy, zero zapisow."""
    nazwy, domeny, maile = _istniejace()
    do_zapisu, duplikaty, odsiane = [], [], []
    for rec in sorted(rekordy, key=lambda r: (-r["wynik"], _norm(r["nazwa"]))):
        if not rec["email"] and not rec["telefon"]:
            odsiane.append((rec, "brak jakiegokolwiek kanalu kontaktu"))
            continue
        if tylko_ok and _norm(rec.get("werdykt")) == "podejrzane":
            odsiane.append((rec, "werdykt zrodla: PODEJRZANE"))
            continue
        klucz_nazwa = _norm(rec["nazwa"]) + "|" + _norm(rec["miasto"])
        dom = _domena(rec["www"])
        klucz_dom = _klucz_domeny(dom, rec["miasto"])
        mail = rec["email"]
        if _norm(rec["nazwa"]) in nazwy or klucz_nazwa in nazwy:
            duplikaty.append((rec, "nazwa juz w lejku"))
            continue
        if klucz_dom and klucz_dom in domeny:
            duplikaty.append((rec, f"ta sama domena I miasto ({dom}, {rec['miasto']})"))
            continue
        if mail and mail in maile:
            duplikaty.append((rec, f"mail {mail} juz w lejku"))
            continue
        do_zapisu.append(rec)
        nazwy.add(_norm(rec["nazwa"]))          # dedup TAKZE wewnatrz pliku
        if klucz_dom:
            domeny.add(klucz_dom)
        if mail:
            maile.add(mail)
    return do_zapisu, duplikaty, odsiane


def _notatka(rec, zrodlo):
    bits = [f"import {zrodlo}"]
    for etykieta, pole in (("typ", "typ"), ("miasto", "miasto"), ("region", "region"),
                           ("adres", "adres")):
        if rec.get(pole):
            bits.append(f"{etykieta}: {rec[pole]}")
    if rec.get("problemy"):
        bits.append(f"uwagi zrodla: {rec['problemy'][:150]}")
    return " | ".join(bits)[:500]


def zapisz(do_zapisu, nisza, zrodlo):
    for rec in do_zapisu:
        db.execute(
            """INSERT INTO sales_pipeline
                   (brand_id, prospect_name, prospect_url, stage, niche, lead_score,
                    contact_email, contact_phone, contact_person, notes, source)
               VALUES ('AGS',%s,%s,'parked',%s,%s,%s,%s,%s,%s,'lista')""",
            (rec["nazwa"], rec["www"] or None, nisza, rec["wynik"],
             rec["email"] or None, rec["telefon"] or None, rec["osoba"] or None,
             _notatka(rec, zrodlo)))
    return len(do_zapisu)


# ---------------- budzenie partiami ----------------
def plan_wake(nisza, ile):
    return db.fetchall(
        """SELECT id, prospect_name, lead_score, contact_email, contact_phone, niche
           FROM sales_pipeline
           WHERE brand_id='AGS' AND stage='parked' AND niche=%s
           ORDER BY lead_score DESC NULLS LAST, prospect_name
           LIMIT %s""", (nisza, ile)) or []


def wake(ids):
    """Uspiony -> prospect. Terminu NIE ustawiamy: pojawi sie przy odhaczeniu wysylki.
    Inaczej straznik terminow zrobilby tyle bramek, ilu obudzonych."""
    if not ids:
        return 0
    db.execute(
        """UPDATE sales_pipeline
              SET stage='prospect',
                  notes = COALESCE(notes,'') || ' | obudzony do wysylki',
                  updated_at=NOW()
            WHERE id = ANY(%s::uuid[])""", ([str(i) for i in ids],))
    return len(ids)


# ---------------- wejscie ----------------
def _drukuj_import(rekordy, do_zapisu, duplikaty, odsiane, nierozpoznane, bez_nazwy, tryb):
    print(f"=== IMPORT LISTY PROSPEKTOW ({tryb.upper()}) ===")
    print(f"Wierszy w pliku: {len(rekordy) + bez_nazwy} (bez nazwy pominietych: {bez_nazwy})")
    if nierozpoznane:
        print(f"Kolumny nierozpoznane (ignorowane): {', '.join(str(n)[:30] for n in nierozpoznane[:8])}")
    print(f"Do zapisu: {len(do_zapisu)} | duplikaty: {len(duplikaty)} | odsiane: {len(odsiane)}")
    print()
    if do_zapisu:
        print("--- TOP 15 wg kontaktowalnosci ---")
        for rec in do_zapisu[:15]:
            kanal = rec["email"] or rec["telefon"] or "?"
            print(f"  {rec['wynik']:3d}  {rec['nazwa'][:44]:<44} {rec['miasto'][:16]:<16} {kanal[:34]}")
        rozklad = {}
        for rec in do_zapisu:
            prog = min(80, (rec["wynik"] // 20) * 20)
            rozklad[prog] = rozklad.get(prog, 0) + 1
        print("  rozklad: " + ", ".join(f"{k}-{min(100, k + 19)}: {v}"
                                        for k, v in sorted(rozklad.items(), reverse=True)))
        print()
    for etykieta, lista in (("DUPLIKATY", duplikaty), ("ODSIANE", odsiane)):
        if lista:
            print(f"--- {etykieta} (pierwsze 8 z {len(lista)}) ---")
            for rec, powod in lista[:8]:
                print(f"  {rec['nazwa'][:50]:<50} {powod}")
            print()


def main():
    a = sys.argv[1:]
    tryb = (a[0] if a else "").lower()

    if tryb in ("dry", "apply"):
        if len(a) < 3:
            print("Uzycie: python -m app.prospect_import dry|apply <plik.xlsx> <nisza> [--wszystkie]")
            return 2
        sciezka, nisza = a[1], a[2]
        tylko_ok = "--wszystkie" not in a
        rekordy, nierozpoznane, bez_nazwy = czytaj(sciezka)
        do_zapisu, duplikaty, odsiane = plan(rekordy, tylko_ok=tylko_ok)
        _drukuj_import(rekordy, do_zapisu, duplikaty, odsiane, nierozpoznane, bez_nazwy, tryb)
        if tryb == "dry":
            print(f"DRY - nic nie zapisano. Nisza: {nisza}. "
                  f"{'Odsiewam PODEJRZANE (--wszystkie zeby wziac wszystkie).' if tylko_ok else 'Biore takze PODEJRZANE.'}")
            return 0
        n = zapisz(do_zapisu, nisza, sciezka.split("/")[-1].split("\\")[-1])
        print(f"APPLY: zapisano {n} wierszy w etapie 'parked', nisza '{nisza}'.")
        print(f"Obudzenie do wysylki: python -m app.prospect_import wake-dry {nisza} 40")
        return 0

    if tryb in ("wzbogac-dry", "wzbogac-apply"):
        if len(a) < 2:
            print("Uzycie: python -m app.prospect_import wzbogac-dry|wzbogac-apply <plik.xlsx>")
            return 2
        sciezka = a[1]
        rekordy, _, _ = czytaj(sciezka)
        uzup, konf, bez = plan_wzbogacenia(rekordy)
        print(f"=== WZBOGACANIE LEJKA Z LISTY ({tryb.upper()}) ===")
        print(f"Wierszy lejka trafionych przez liste: {len(uzup) + len(konf) + bez}")
        print(f"Do uzupelnienia: {len(uzup)} | konflikty do decyzji: {len(konf)} | bez zmian: {bez}")
        print()
        if uzup:
            print("--- UZUPELNIE PUSTE POLA ---")
            for w, rec, pola in uzup:
                opis = ", ".join(f"{k}={v}" for k, v in pola.items())
                print(f"  [{w.get('stage'):<10}] {w['prospect_name'][:40]:<40} {opis[:70]}")
            print()
        if konf:
            print("--- KONFLIKTY (lejek ma juz INNA wartosc; NIE nadpisuje) ---")
            for w, rec, sporne in konf:
                for kol, stara, nowa in sporne:
                    print(f"  {w['prospect_name'][:36]:<36} {kol}: w lejku '{stara[:30]}' "
                          f"| na liscie '{nowa[:30]}'")
            print("  -> rozstrzyga czlowiek: zmiane robi sie przez pipeline_move albo recznym SQL.")
            print()
        if tryb == "wzbogac-dry":
            print("DRY - nic nie zapisano.")
            return 0
        n = wzbogac(uzup, sciezka.split("/")[-1].split("\\")[-1])
        print(f"APPLY: uzupelnionych wierszy {n}. Konfliktow NIE ruszalem ({len(konf)}).")
        return 0

    if tryb in ("wake-dry", "wake-apply"):
        if len(a) < 3:
            print("Uzycie: python -m app.prospect_import wake-dry|wake-apply <nisza> <ile>")
            return 2
        nisza, ile = a[1], int(a[2])
        rows = plan_wake(nisza, ile)
        print(f"=== BUDZENIE ({tryb.upper()}) === nisza '{nisza}', prosba o {ile}, znalezione {len(rows)}")
        for r in rows:
            print(f"  {r.get('lead_score') or 0:3d}  {r['prospect_name'][:46]:<46} "
                  f"{(r.get('contact_email') or r.get('contact_phone') or '?')[:34]}")
        if tryb == "wake-dry":
            print("\nDRY - nic nie zapisano.")
            return 0
        n = wake([r["id"] for r in rows])
        print(f"\nAPPLY: obudzonych {n}. Terminu nie ustawiam - pojawi sie przy odhaczeniu wysylki.")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
