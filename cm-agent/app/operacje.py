"""REJESTR OPERACJI HURTOWYCH (D-007, 02/08/2026).

POWOD (zgloszenie Managera 29/07, szosta odslona AP-311): po wycofaniu 21 materialow Content
Manager zapytal, PO CZYM ma je rozpoznac. Nie brakowalo danych - dane byly NIEODROZNIALNE:
`status='rejected'` z operacji hurtowej wyglada identycznie jak `rejected` z przegladu kart
sprzed miesiaca. Zapytanie "X + rejected + wiecej niz jeden wiersz" zwracalo 26 materialow,
z czego z operacji bylo 21.

    "Ty wiesz, co wycofales, bo sam to robiles. CM patrzy na te sama baze i nie widzi roznicy
     miedzy materialem wycofanym a odrzuconym przy przegladzie miesiac temu." - Manager 29/07

ZASADA: kazda zmiana dotykajaca WIELU wierszy naraz najpierw sie REJESTRUJE, potem dziala,
a dotkniete wiersze niosa `op_id`. Wtedy drugi agent wycina dokladny zbior jednym warunkiem
i czyta, co to bylo za dzialanie - zamiast zgadywac po dacie.
"""
import re
import traceback

from . import db

# Identyfikator ma byc CZYTELNY DLA CZLOWIEKA i pisany z pamieci w zapytaniu.
# Stad ograniczenie: male litery, cyfry i myslniki. Bez ogonkow - AP-313 (nazwa z ogonkiem
# w srodku nie trafia we wzorcu wycietym "na oko").
_OP_ID = re.compile(r"^[a-z0-9][a-z0-9-]{4,60}$")

TABELE = ("content_items", "post_queue")


class Blad(Exception):
    """Blad kontraktu - tresc jest dla czlowieka."""


def zarejestruj(op_id, kto, opis, warunek=None, brand_id="AGS"):
    """Zaklada wpis operacji. Wolaj PRZED zmiana, nie po - jesli operacja padnie w polowie,
    chcesz wiedziec, ze w ogole sie zaczela, i na jakim warunku."""
    op = str(op_id or "").strip().lower()
    if not _OP_ID.match(op):
        raise Blad(f"Zly identyfikator operacji \"{op_id}\". Male litery, cyfry i myslniki, "
                   f"5-61 znakow, bez polskich znakow. Ma byc czytelny i pisany z pamieci, "
                   f"np. 'wycofanie-serii-29072026'.")
    if not str(opis or "").strip():
        raise Blad("Operacja bez opisu jest bezuzyteczna dla drugiego agenta - napisz CO i DLACZEGO.")
    db.execute(
        """INSERT INTO bulk_operations (op_id, kto, opis, warunek, brand_id)
           VALUES (%s,%s,%s,%s,%s)
           ON CONFLICT (op_id) DO NOTHING""",
        (op, str(kto or "?")[:80], str(opis).strip(), (warunek or None), brand_id))
    return op


def oznacz(op_id, tabela, ids):
    """Stempluje dotkniete wiersze. Zwraca ile oznaczono.

    Nazwa tabeli NIE moze pochodzic z zewnatrz - jest wklejana do SQL, wiec przechodzi
    przez biala liste. To jedyne miejsce w tym module, gdzie interpolacja jest konieczna."""
    if tabela not in TABELE:
        raise Blad(f"Nieznana tabela \"{tabela}\". Dozwolone: {', '.join(TABELE)}.")
    lista = [str(i) for i in (ids or []) if i]
    if not lista:
        return 0
    try:
        db.execute(f"UPDATE {tabela} SET op_id=%s WHERE id = ANY(%s::uuid[])", (op_id, lista))
    except Exception:
        traceback.print_exc()
        return 0
    _przelicz(op_id)
    return len(lista)


def _przelicz(op_id):
    try:
        db.execute(
            """UPDATE bulk_operations SET wierszy = (
                   (SELECT COUNT(*) FROM content_items WHERE op_id=%s)
                 + (SELECT COUNT(*) FROM post_queue    WHERE op_id=%s))
               WHERE op_id=%s""", (op_id, op_id, op_id))
    except Exception:
        traceback.print_exc()


def opis(op_id):
    """Co to byla za operacja - do wklejenia w odpowiedzi drugiemu agentowi."""
    r = db.fetchone(
        """SELECT op_id, kiedy, kto, opis, warunek, wierszy FROM bulk_operations
           WHERE op_id=%s""", (str(op_id or "").strip().lower(),))
    if not r:
        return f"Nie znam operacji \"{op_id}\"."
    return (f"🧾 {r['op_id']} ({str(r['kiedy'])[:10]}, {r['kto']}): {r['opis']}"
            + (f"\nWarunek: {r['warunek']}" if r.get("warunek") else "")
            + (f"\nDotknietych wierszy: {r['wierszy']}" if r.get("wierszy") is not None else ""))


def ostatnie(limit=5):
    """Lista ostatnich operacji - odpowiedz na pytanie 'co sie tu dzialo hurtem'."""
    rows = db.fetchall(
        """SELECT op_id, kiedy, kto, wierszy, left(opis, 90) AS skrot
           FROM bulk_operations ORDER BY kiedy DESC LIMIT %s""", (int(limit),)) or []
    if not rows:
        return "Brak zarejestrowanych operacji hurtowych."
    return "\n".join(f"• {r['op_id']} ({str(r['kiedy'])[:10]}, {r['kto']}, "
                     f"{r.get('wierszy') if r.get('wierszy') is not None else '?'} wierszy): {r['skrot']}"
                     for r in rows)
