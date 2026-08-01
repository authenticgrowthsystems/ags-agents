"""TECZKA PROSPEKTA (31/07/2026) - para zapisz_tekst + teczka jako JEDEN kontrakt.

POWOD (zadanie Managera): teksty sprzedazowe pisane w Cowork ladowaly wylacznie w czacie.
Zero sladu w bazie, wiec nie dalo sie iterowac, policzyc ani wczytac w nowej rozmowie.

DLACZEGO JEDEN PLIK: zapis i odczyt dziela slownik kanalow, rozstrzyganie identyfikatora
i ksztalt wpisu. Rozdzielone na dwa moduly rozjechalyby sie przy pierwszej zmianie kanalu.

USTALENIE, KTORE UKSZTALTOWALO PROJEKT (odczyt produkcji 31/07):
  contacts        194 wiersze, 0 z mailem  - uchwyty z X i LinkedIna (radar komentarzy)
  sales_pipeline  133 wiersze, 0 z contact_id - prospekty kampanii (szkoly tanca)
  pokrycie po nazwie: 1 na 133
Dwie rozlaczne populacje. Prospekt kampanii NIE MA wiersza w contacts, wiec identyfikator
rozstrzygamy wobec OBU rejestrow i zawsze mowimy, w ktorym trafil. Nie dosypujemy contacts
pod prospekty, bo kanon z 22/07 mowi: zrodlem prawdy o prospekcie jest sales_pipeline.
"""
import re
import traceback

from . import db

# Kanal z kontraktu -> (action_type, channel) w engagement_log. Wartosci 'SMS' i 'WhatsApp'
# dolozone w DDL 036. 'dm' celuje w LinkedIn, bo to kanal DM kampanii - jesli kiedys dojda
# DM-y na X, dokladamy tu 'dm:x', nie zgadujemy po tresci.
_KANALY = {
    "email": ("email", "Email"),
    "sms": ("other", "SMS"),
    "whatsapp": ("other", "WhatsApp"),
    "dm": ("linkedin_dm", "LinkedIn"),
    "telefon": ("call", "Phone"),
}
# 'draft' NIE jest recyklingiem 'proposed' - patrz DDL 036 pkt 1: 'proposed' budzi straznika
# gotowcow i kazdy szkic pisany w Cowork zrodzilby po dobie bramke do tapniecia.
_STATUSY = ("draft", "sent")

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_AGENT = "AGS:manager"

# Katalog klienta: sciezka WZGLEDNA, np. 'Klienci\\Chwalinski'. Bez polskich znakow, bo nazwa
# ma byc identyczna z ta na dysku, a system NIGDY katalogow nie tworzy ani nie przenosi -
# rozjazd o jeden ogonek zostawilby wiersz wskazujacy na nieistniejacy folder.
_POLSKIE = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
_KATALOG_OK = re.compile(r"^[A-Za-z0-9_\-. \\/]+$")


class Blad(Exception):
    """Blad kontraktu - tresc jest przeznaczona dla czlowieka i wraca do czatu."""


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip())


# ---------------------------------------------------------------- rozstrzyganie identyfikatora
def _z_lejka(row):
    return {"rodzaj": "lejek", "id": str(row["id"]), "nazwa": row["prospect_name"], "wiersz": row}


def _z_kontaktow(row):
    return {"rodzaj": "kontakt", "id": str(row["id"]), "nazwa": row["name"], "wiersz": row}


def _podobne(fragment, limit=8):
    """Lista podobnych nazw, gdy identyfikator nie trafil. Szukamy po KAZDYM slowie osobno -
    'Szkola Tanca Rytm' nie trafia dokladnie, ale 'Rytm' trafia."""
    slowa = [w for w in re.split(r"[\s,;/]+", _norm(fragment)) if len(w) >= 3][:4]
    if not slowa:
        return []
    warunki = " OR ".join(["prospect_name ILIKE %s"] * len(slowa))
    out = []
    try:
        for r in db.fetchall(
                f"SELECT prospect_name AS n, stage AS s FROM sales_pipeline WHERE {warunki} "
                f"ORDER BY updated_at DESC LIMIT {limit}", tuple(f"%{w}%" for w in slowa)) or []:
            out.append(f"{r['n']} (lejek, {r['s']})")
        warunki_k = " OR ".join(["name ILIKE %s"] * len(slowa))
        for r in db.fetchall(
                f"SELECT name AS n FROM contacts WHERE {warunki_k} "
                f"ORDER BY updated_at DESC LIMIT {limit}", tuple(f"%{w}%" for w in slowa)) or []:
            out.append(f"{r['n']} (kontakt)")
    except Exception:
        traceback.print_exc()
    return out[:limit]


def znajdz(ident):
    """Rozstrzyga identyfikator wobec OBU rejestrow. UUID albo fragment nazwy.

    Zero trafien albo wiele trafien = Blad z lista. NIGDY nie zaklada nowego wiersza -
    ciche tworzenie kontaktu produkuje duchy, ktorych nikt pozniej nie odroznia od prawdziwych."""
    frag = _norm(ident)
    if not frag:
        raise Blad("Podaj identyfikator: UUID prospekta z lejka, UUID kontaktu albo fragment nazwy.")

    if _UUID.match(frag):
        r = db.fetchone("SELECT * FROM sales_pipeline WHERE id=%s::uuid", (frag,))
        if r:
            return _z_lejka(r)
        r = db.fetchone("SELECT * FROM contacts WHERE id=%s::uuid", (frag,))
        if r:
            return _z_kontaktow(r)
        raise Blad(f"Nie ma takiego identyfikatora ani w lejku, ani wsrod kontaktow: {frag}. "
                   f"Podaj fragment nazwy zamiast UUID, to pokaze podobne.")

    lejek = db.fetchall(
        """SELECT * FROM sales_pipeline WHERE prospect_name ILIKE %s
           ORDER BY updated_at DESC LIMIT 12""", (f"%{frag}%",)) or []
    kontakty = db.fetchall(
        """SELECT * FROM contacts WHERE name ILIKE %s
           ORDER BY updated_at DESC LIMIT 12""", (f"%{frag}%",)) or []

    trafienia = [_z_lejka(r) for r in lejek] + [_z_kontaktow(r) for r in kontakty]
    if len(trafienia) == 1:
        return trafienia[0]
    if not trafienia:
        p = _podobne(frag)
        raise Blad(f"Nie znajduje \"{frag}\" ani w lejku, ani wsrod kontaktow.\n"
                   + ("Podobne nazwy:\n" + "\n".join("  - " + x for x in p) if p
                      else "Nic podobnego tez nie ma. Sprawdz, czy prospekt jest w lejku.")
                   + "\nNIC nie zapisalem i niczego nie zalozylem.")

    # Dokladne dopasowanie nazwy rozstrzyga wieloznacznosc (franczyzy: "Egurrola Warszawa"
    # kontra "Egurrola Krakow" - fragment "Egurrola" trafia w oba, pelna nazwa w jeden).
    dokladne = [t for t in trafienia if _norm(t["nazwa"]).lower() == frag.lower()]
    if len(dokladne) == 1:
        return dokladne[0]
    lista = "\n".join(f"  - {t['nazwa']} ({t['rodzaj']}, id {t['id']})" for t in trafienia[:12])
    raise Blad(f"\"{frag}\" pasuje do {len(trafienia)} wpisow - doprecyzuj nazwe albo podaj UUID:\n"
               f"{lista}\nNIC nie zapisalem.")


# ---------------------------------------------------------------------------------- zapis
def zapisz(ident, kanal, tresc, status="draft", next_step=None, next_step_date=None, temat=None,
           katalog=None):
    """Zapisuje tekst przy kontakcie, z data. Zwraca potwierdzenie dla czlowieka.

    next_step jest opcjonalny, ale to JEDYNA droga, ktora ustala nastepny krok z trescia -
    bez niego teczka moglaby zwrocic tylko date. Swiadomie siedzi w zapisie, a nie osobno:
    kto wysyla tekst, ten wie, co ma sie zdarzyc potem."""
    cel = znajdz(ident)

    k = _norm(kanal).lower()
    if k not in _KANALY:
        raise Blad(f"Nieznany kanal \"{kanal}\". Dozwolone: {', '.join(sorted(_KANALY))}.")
    st = _norm(status).lower() or "draft"
    if st not in _STATUSY:
        raise Blad(f"Nieznany status \"{status}\". Dozwolone: {', '.join(_STATUSY)}.")
    body = str(tresc or "").strip()
    if not body:
        raise Blad("Pusta tresc - nie ma czego zapisac.")
    # Katalog walidowany PRZED zapisem: inaczej bledna sciezka zostawia zapisany tekst
    # I blad naraz, a czlowiek ponawia probe i robi duplikat.
    plan_katalogu = _waliduj_katalog(cel, katalog) if _norm(katalog) else None

    action_type, channel = _KANALY[k]
    nota = f"teczka: {k} ({st})" + (f" | temat: {_norm(temat)[:120]}" if temat else "")
    db.execute(
        """INSERT INTO engagement_log (action_type, channel, agent, content, notes,
                                       contact_id, pipeline_id, status, author_display)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (action_type, channel, _AGENT, body[:20000], nota,
         cel["id"] if cel["rodzaj"] == "kontakt" else None,
         cel["id"] if cel["rodzaj"] == "lejek" else None,
         st, _norm(cel["nazwa"])[:200]))

    krok = ""
    if next_step or next_step_date:
        krok = _ustaw_krok(cel, next_step, next_step_date)
    kat = _zapisz_katalog(cel, plan_katalogu) if plan_katalogu else ""
    return (f"Zapisane w teczce: {cel['nazwa']} ({cel['rodzaj']}) | {k} | {st} | "
            f"{len(body)} znakow.{krok}{kat}")


def _sprawdz_katalog(sciezka):
    """Waliduje sciezke katalogu. Zwraca znormalizowana albo rzuca Blad.

    System NIGDY nie tworzy, nie przenosi i nie kasuje katalogow - zapisuje wylacznie NAPIS.
    Dlatego walidacja jest jedyna obrona przed wierszem, ktory wskazuje w prozne miejsce."""
    s = _norm(sciezka).replace("/", "\\").strip("\\")
    if not s:
        raise Blad("Pusta sciezka katalogu.")
    zle = [z for z in s if z in _POLSKIE]
    if zle:
        raise Blad(f"Nazwa katalogu ma polskie znaki ({''.join(sorted(set(zle)))}). "
                   f"Katalogi nazywamy bez ogonkow, zeby napis w bazie byl identyczny "
                   f"z nazwa na dysku - system katalogow NIE TWORZY, wiec sam ich nie poprawi.")
    # Litera dysku PRZED filtrem znakow: dwukropek i tak nie przechodzi przez filtr, ale
    # komunikat "niedozwolone znaki" nie powiedzialby czlowiekowi, o co naprawde chodzi.
    # Kolejnosc sprawdzen decyduje o tym, ktore zdanie zobaczy - to ta sama rodzina wad,
    # co AP-312: etykieta ma znaczyc to, co obiecuje.
    if re.match(r"^[A-Za-z]:", s):
        raise Blad(f"Podaj sciezke WZGLEDNA (np. Klienci\\Chwalinski), nie z litera dysku. "
                   f"Korzen jest cecha maszyny, nie prospekta.")
    if ".." in s:
        raise Blad("Sciezka nie moze zawierac \"..\".")
    if not _KATALOG_OK.match(s):
        raise Blad(f"Niedozwolone znaki w sciezce \"{s}\". Dozwolone: litery bez ogonkow, "
                   f"cyfry, podkreslenie, myslnik, kropka, spacja i ukosnik.")
    return s


def _waliduj_katalog(cel, sciezka):
    """Sprawdza WSZYSTKO, zanim cokolwiek trafi do bazy. Zwraca (nowa, obecna).

    Rozdzielone od zapisu SWIADOMIE: pierwsza wersja walidowala PO wstawieniu wiersza do
    engagement_log, wiec bledna sciezka zostawiala zapisany tekst i blad na wyjsciu naraz.
    Czlowiek widzial blad, ponawial - i robil duplikat wpisu. Zlapane wlasnym testem 01/08.

    Katalog ustala sie RAZ i nigdy nie zmienia (polecenie Tomasza 01/08). Powod nie jest
    kosmetyczny: skoro system katalogow nie przenosi, to podmiana napisu zostawilaby wiersz
    wskazujacy na nieistniejaca lokalizacje - czyli dokladnie ten rozjazd dysku z baza,
    ktoremu ten most ma zapobiec."""
    if cel["rodzaj"] != "lejek":
        raise Blad("Katalog trzymamy przy prospekcie z LEJKA. Ten identyfikator wskazuje "
                   "na kontakt spolecznosciowy, ktory katalogu nie ma.")
    nowa = _sprawdz_katalog(sciezka)
    obecna = _norm((cel.get("wiersz") or {}).get("katalog"))
    if obecna and obecna.lower() != nowa.lower():
        raise Blad(f"{cel['nazwa']} ma juz katalog \"{obecna}\" i NIE zmieniam go na \"{nowa}\". "
                   f"Nazwa katalogu jest ustalana raz przy pierwszym kontakcie. Jesli naprawde "
                   f"trzeba ja zmienic, najpierw przenies folder na dysku, potem popraw wiersz "
                   f"recznym SQL - swiadomie, a nie mimochodem przy zapisie maila.")
    return nowa, obecna


def _zapisz_katalog(cel, plan):
    nowa, obecna = plan
    if obecna:
        return f"\nKatalog: {obecna} (bez zmian)"
    db.execute("UPDATE sales_pipeline SET katalog=%s, updated_at=NOW() WHERE id=%s::uuid",
               (nowa, cel["id"]))
    return f"\nKatalog ustalony: {nowa} (raz na zawsze - system go nie zmieni)"


def _ustaw_krok(cel, next_step, next_step_date):
    """Nastepny krok idzie tam, gdzie mieszka prospekt: lejek ma next_step + next_followup_at,
    kontakt ma next_action + next_action_due. Kolumny contacts.next_action nie zapisywal dotad
    NIKT (0 wierszy w produkcji na 31/07) - to jej pierwszy pisarz."""
    tresc = _norm(next_step) or None
    data = _norm(next_step_date) or None
    try:
        if cel["rodzaj"] == "lejek":
            db.execute(
                """UPDATE sales_pipeline
                      SET next_step = COALESCE(%s, next_step),
                          next_followup_at = COALESCE(%s::timestamptz, next_followup_at),
                          updated_at = NOW()
                    WHERE id=%s::uuid""", (tresc, data, cel["id"]))
        else:
            db.execute(
                """UPDATE contacts
                      SET next_action = COALESCE(%s, next_action),
                          next_action_due = COALESCE(%s::date, next_action_due),
                          updated_at = NOW()
                    WHERE id=%s::uuid""", (tresc, data, cel["id"]))
    except Exception:
        traceback.print_exc()
        return "  UWAGA: tekst zapisany, ale nastepnego kroku NIE udalo sie ustawic."
    return f"\nNastepny krok: {tresc or '(bez zmian)'}" + (f", termin {data}" if data else "")


# ---------------------------------------------------------------------------------- odczyt
def _wpisy(cel):
    """Wszystko, co poszlo do tego kontaktu, chronologicznie - najstarsze pierwsze.

    Dla prospekta z lejka bierzemy pipeline_id ORAZ dokladna nazwe z author_display: gotowce
    Sprzedawcy sprzed DDL 036 maja tylko nazwe, a teczka ma pokazac PELNA historie, nie te
    jej czesc, ktora akurat powstala po migracji."""
    if cel["rodzaj"] == "lejek":
        return db.fetchall(
            """SELECT created_at, channel, action_type, status, agent, content, response, notes
                 FROM engagement_log
                WHERE pipeline_id=%s::uuid
                   OR (pipeline_id IS NULL AND lower(btrim(COALESCE(author_display,''))) = lower(%s))
                ORDER BY created_at""", (cel["id"], _norm(cel["nazwa"]))) or []
    return db.fetchall(
        """SELECT created_at, channel, action_type, status, agent, content, response, notes
             FROM engagement_log WHERE contact_id=%s::uuid ORDER BY created_at""",
        (cel["id"],)) or []


def _tresc_wpisu(w):
    """Rozdziela to, co PRZYSZLO, od tego, co MY napisalismy.

    Wszystkie tory zapisu trzymaja te sama konwencje: `content` to wejscie (komentarz, DM)
    albo etykieta, a `response` to NASZ tekst. Gotowiec Sprzedawcy ma w `content` sam napis
    "outreach email: <nazwa>", a caly mail w `response` - czytanie samego `content` pokazywalo
    wiec etykiete zamiast tresci, czyli ukrywalo dokladnie to, po co teczka istnieje.
    Zlapane tap-testem na ZYWYCH danych StandART 31/07: siedem wpisow, w kazdym sama etykieta."""
    przyszlo = _norm(w.get("content"))
    nasze = _norm(w.get("response"))
    if nasze and przyszlo and nasze != przyszlo:
        return [f"> {przyszlo[:600]}", nasze[:2000] + ("..." if len(nasze) > 2000 else "")]
    tresc = nasze or przyszlo
    return [tresc[:2000] + ("..." if len(tresc) > 2000 else "")] if tresc else ["_(pusty wpis)_"]


def _naglowek(cel):
    w = cel["wiersz"]
    if cel["rodzaj"] == "lejek":
        # Katalog PIERWSZY: to jedyna rzecz w teczce, ktora prowadzi poza baze - do plikow.
        # Brak jest wypisany slowami, bo pusta linia nie odroznia "nie ma" od "nie sprawdzilem".
        pola = [("Katalog", w.get("katalog") or "BRAK - nie ustalony"),
                ("Etap", w.get("stage")), ("Oferta", w.get("offer_tier")),
                ("Wartosc", f"{w['value']} {w.get('currency') or ''}".strip() if w.get("value") else None),
                ("Strona", w.get("prospect_url")), ("Zrodlo", w.get("source"))]
    else:
        pola = [("Status", w.get("status")), ("Mail", w.get("email")), ("Telefon", w.get("phone")),
                ("LinkedIn", w.get("linkedin_url")), ("X", w.get("x_handle")),
                ("Strona", w.get("website")), ("Priorytet", w.get("priority"))]
    return [f"- {n}: {v}" for n, v in pola if v]


def _krok(cel):
    w = cel["wiersz"]
    if cel["rodzaj"] == "lejek":
        tresc, data = w.get("next_step"), w.get("next_followup_at")
    else:
        tresc, data = w.get("next_action"), w.get("next_action_due")
    if not tresc and not data:
        # Brak musi byc WIDOCZNY. Pusta linia w raporcie lejka byla jedna z przyczyn tego,
        # ze przez tygodnie nikt nie zauwazyl prospektow bez nastepnego kroku (diagnoza 26/07).
        return "**BRAK ustalonego nastepnego kroku.**"
    return (f"**{tresc or '(krok bez opisu, sama data)'}**"
            + (f" - termin {str(data)[:16]}" if data else " - BEZ TERMINU"))


def teczka_text(ident):
    """Cala teczka w jednym wywolaniu: kim jest, co do niego poszlo, co dalej."""
    cel = znajdz(ident)
    wpisy = _wpisy(cel)
    L = [f"# TECZKA: {cel['nazwa']}",
         f"({cel['rodzaj']}, id {cel['id']})", ""]
    L += _naglowek(cel)
    L += ["", "## Nastepny krok", _krok(cel), "", f"## Historia ({len(wpisy)})"]
    if not wpisy:
        L.append("Nic jeszcze nie poszlo. Teczka pusta.")
    for i, w in enumerate(wpisy, 1):
        kiedy = str(w["created_at"])[:16]
        L.append(f"\n**{i}. {kiedy} | {w.get('channel') or '?'} | {w.get('status')}** "
                 f"({w.get('agent') or '?'})")
        if w.get("notes"):
            L.append(f"_{_norm(w['notes'])[:200]}_")
        L += _tresc_wpisu(w)
    return "\n".join(L)
