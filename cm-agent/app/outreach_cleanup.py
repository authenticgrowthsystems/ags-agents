# -*- coding: utf-8 -*-
"""Jednorazowe SPRZATANIE zaleglych gotowcow outreachu (26/07/2026).

Kanon "zalegle dane po naprawie" (rodzina AP-307): poprawka `_draft_outreach` uniewaznia
poprzednika OD TERAZ, ale w bazie leza wiersze wyprodukowane przed poprawka. Dowod z sondy
26/07: Klub Sportowy StandART ma SIEDEM wierszy 'proposed' z 24/07 (09:44-13:49) i ZERO
'sent', a piec z nich trzyma otwarte bramki #152-156, ktore zajmuja cala piatke strazniki
przypomnien (`engagement._watch_proposed` ma LIMIT 5 PRZED odsiewem).

ZASADA (deterministyczna, bez losowosci - warunek idempotencji i AP-308):
- Grupujemy zywe gotowce po (author_display, channel).
- W kazdej grupie zostaje NAJNOWSZY (ostatnia wersja tekstu = ta, ktora Tomasz czytal).
- Starsze ida na 'rejected' z nota "ZASTAPIONE nowszym gotowcem (sprzatanie 26/07)".
- Bramki `stale_outreach` w statusie 'pending', ktore wskazuja na wiersz NIE bedacy juz
  'proposed', ida na 'expired'. Dotyczy to takze sierot sprzed tego sprzatania.
- Wiersze 'sent', 'skipped' i cudze (Lacznik, komentarze) NIE sa ruszane.

Uruchomienie (SSH, Tomasz):
  docker exec cm-agent python -m app.outreach_cleanup dry     # podglad, zero zmian
  docker exec cm-agent python -m app.outreach_cleanup apply   # wykonanie
"""
import sys

from . import db

OUTREACH_NOTE = "gotowiec outreach"


def _zywe_gotowce():
    """Wszystkie zywe gotowce sprzedazowe, deterministycznie posortowane."""
    return db.fetchall(
        """SELECT id, author_display, channel, created_at, LEFT(COALESCE(response,''), 60) AS podglad
           FROM engagement_log
           WHERE agent='AGS:sprzedaz' AND status='proposed'
             AND COALESCE(notes,'') ILIKE %s
           ORDER BY author_display, channel, created_at, id""",
        (f"%{OUTREACH_NOTE}%",)) or []


def _bramki_sieroty():
    """Bramki 'stale_outreach' czekajace na guzik, ktorych wiersz nie jest juz propozycja.
    Po zamknieciu nadmiarowych gotowcow to wlasnie one blokuja straznika."""
    return db.fetchall(
        """SELECT d.id, d.context->>'engagement_id' AS eng_id, e.status AS status_wiersza,
                  e.author_display, d.created_at
           FROM agent_decisions d
           LEFT JOIN engagement_log e ON e.id::text = d.context->>'engagement_id'
           WHERE d.decision_type='stale_outreach' AND d.status='pending'
             AND (e.id IS NULL OR e.status <> 'proposed')
           ORDER BY d.id""") or []


def plan():
    """Zwraca (do_zamkniecia, zostaja, bramki) - czysty odczyt, zero zapisow."""
    wiersze = _zywe_gotowce()
    grupy = {}
    for r in wiersze:
        grupy.setdefault((r.get("author_display") or "", r.get("channel") or ""), []).append(r)
    do_zamkniecia, zostaja = [], []
    for _, rows in sorted(grupy.items()):
        zostaja.append(rows[-1])            # najnowszy w grupie
        do_zamkniecia.extend(rows[:-1])     # cala reszta
    return do_zamkniecia, zostaja, grupy


def main():
    tryb = (sys.argv[1] if len(sys.argv) > 1 else "dry").lower()
    if tryb not in ("dry", "apply"):
        print("Uzycie: python -m app.outreach_cleanup [dry|apply]")
        return 2

    do_zamkniecia, zostaja, grupy = plan()

    print(f"=== SPRZATANIE GOTOWCOW OUTREACHU ({tryb.upper()}) ===")
    print(f"Zywych gotowcow: {len(do_zamkniecia) + len(zostaja)} w {len(grupy)} grupach "
          f"(prospekt + kanal).")
    print()
    for (kto, kanal), rows in sorted(grupy.items()):
        print(f"--- {kto or '(bez nazwy)'} / {kanal or '(bez kanalu)'}: {len(rows)} wierszy")
        for r in rows:
            znacznik = "ZOSTAJE " if r is rows[-1] else "zamykam "
            print(f"    {znacznik} {r['id']}  {r['created_at']}  {r.get('podglad') or ''}")
    print()

    if tryb == "dry":
        # Sieroty liczymy PO hipotetycznym zamknieciu: bramki wskazujace na wiersze z listy
        # do zamkniecia beda sierotami, nawet jesli dzis jeszcze nimi nie sa.
        ids = {str(r["id"]) for r in do_zamkniecia}
        przyszle = db.fetchall(
            """SELECT id, context->>'engagement_id' AS eng_id FROM agent_decisions
               WHERE decision_type='stale_outreach' AND status='pending' ORDER BY id""") or []
        trafione = [b for b in przyszle if (b.get("eng_id") or "") in ids]
        juz_sieroty = _bramki_sieroty()
        print(f"Do zamkniecia wierszy: {len(do_zamkniecia)}. Zostaje: {len(zostaja)}.")
        print(f"Bramek do wygaszenia: {len(trafione)} (po zamknieciu) "
              f"+ {len(juz_sieroty)} juz osieroconych.")
        for b in trafione + juz_sieroty:
            print(f"    bramka #{b['id']} -> wiersz {b.get('eng_id')}")
        print("\nDRY - nic nie zapisano. Uruchom z 'apply', zeby wykonac.")
        return 0

    zamkniete = 0
    if do_zamkniecia:
        db.execute(
            """UPDATE engagement_log SET status='rejected',
                      notes = COALESCE(notes,'') || ' | ZASTAPIONE nowszym gotowcem (sprzatanie 26/07)'
               WHERE id = ANY(%s::uuid[])""",
            ([str(r["id"]) for r in do_zamkniecia],))
        zamkniete = len(do_zamkniecia)

    sieroty = _bramki_sieroty()
    wygaszone = 0
    if sieroty:
        db.execute("UPDATE agent_decisions SET status='expired' WHERE id = ANY(%s)",
                   ([b["id"] for b in sieroty],))
        wygaszone = len(sieroty)

    print(f"APPLY: zamknietych wierszy {zamkniete}, wygaszonych bramek {wygaszone}, "
          f"zywych gotowcow zostalo {len(zostaja)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
