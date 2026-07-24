"""CRM relacji comment-radaru (BE-ENGAGEMENT 20/07, brief BRIEF_ENGAGEMENT_CRM_20072026).

Kanon od poczatku projektu: "zapisywac w jakie relacje wchodze z jakimi ludzmi".
Baza contacts (45 osob z migracji #71) przestaje lezec odlogiem: kazda propozycja
komentarza dopasowuje autora do contacts, NIEZNANY dostaje od razu STUB (contact_id
wypelnione ZAWSZE - DoD 5) + wymuszony intake profilu (zrzut -> wizja -> uzupelnienie
+ tier guzikami przez decisions.ask, typ 'crm_tier').

Stadium relacji (skala zatwierdzona guzikami 20/07): cold -> commented -> replied -> dm
-> offer -> client (tylko W PRZOD, bump przy potwierdzonym wklejeniu komentarza)
+ 'ghosted' jako stan BOCZNY (relacja ucichla; poza liniowym awansem, ustawiany recznie
albo przyszlymi akcjami). Skala w CHECK (db/026)."""
import datetime
import json
import re
import traceback

from psycopg.types.json import Jsonb

from . import db

STAGES = ["cold", "commented", "replied", "dm", "offer", "client"]  # liniowy awans
SIDE_STAGES = ["ghosted"]  # stany boczne w CHECK, poza kolejnoscia bump_stage

# Skala ICP (doktryna #71) + 'Inne' od 24/07 (decyzja Tomasza guzikami, paczka #1 pkt 4:
# dodac piata wartosc, legacy Premium/Mid/Free/Watch/N/A zostawic jako historie - twarde
# sciecie CHECK wywalilo by 45 zywych wierszy). Jedno miejsce prawdy dla kart i zapisu.
TIERS = ("Buyer", "Peer", "Competitor", "Partner", "Inne")
TIER_KEYS = {t.lower(): t for t in TIERS}
TIER_OPTIONS = [{"key": t.lower(), "label": t} for t in TIERS]

_INTAKE_KEY = "crm_intake_pending"      # stan: czekamy na zrzut PROFILU (brand_config, wzorzec matreview)
_INTAKE_TTL_MIN = 15

_BRANDS_ALLOWED = {"AGS", "TNM", "RDC"}  # CHECK contacts.brand_affinity (001) - reszta bez przypisania


def _state_get(key):
    from . import matreview
    return matreview._state_get(key)


def _state_set(key, obj):
    from . import matreview
    matreview._state_set(key, obj)


def norm_handle(h):
    """'@Jan_Kowalski ' -> 'jan_kowalski' (dopasowanie handli niezaleznie od @ i wielkosci liter)."""
    return (h or "").strip().lstrip("@").strip().lower()


def clean_author(a):
    """B3 INTAKE-UX (21/07): 'Djordje Klikovac • 2nd (He/Him) 🔹' -> 'Djordje Klikovac'.
    Wizja widzi te sama osobe z roznymi dopiskami platformy (stopien sieci, zaimki, emoji) -
    kazdy wariant zakladal NOWY stub i nowa karte 'Nowa osoba' (dowod: 3x karta dla Djordje).
    Zdejmujemy dopiski przed dopasowaniem I przed zapisem nazwy stuba."""
    a = (a or "").strip()
    a = re.sub(r"\((?:he|she|they|on|ona)[^)]*\)", " ", a, flags=re.IGNORECASE)
    a = re.sub(r"[•·|].*$", " ", a)  # wszystko od '•'/'·'/'|' to dopisek platformy
    a = re.sub(r"\b(1st|2nd|3rd|following|follows you|obserwuje(sz)?|premium)\b", " ", a,
               flags=re.IGNORECASE)
    a = "".join(ch for ch in a if ch.isalnum() or ch.isspace() or ch in "@._-'")
    return re.sub(r"\s+", " ", a).strip()


def _platform_family(channel):
    return (channel or "x").split("_")[0].lower()


def find_contact(author, channel):
    """Dopasuj wyswietlanego autora do contacts: po handle (x_handle / handles jsonb rodziny
    platformy) i po nazwie (name / full_name, case-insensitive; takze po nazwie OCZYSZCZONEJ
    z dopiskow platformy - B3 21/07). Zwraca wiersz albo None."""
    author = (author or "").strip()
    if not author:
        return None
    fam = _platform_family(channel)
    h = norm_handle(author)
    cleaned = clean_author(author) or author
    try:
        row = db.fetchone(
            """SELECT id, name, icp_tier, relationship_stage, handles FROM contacts
               WHERE lower(trim(both '@' from COALESCE(x_handle,''))) = %s
                  OR lower(COALESCE(handles->>%s, '')) = %s
                  OR lower(name) IN (lower(%s), lower(%s))
                  OR lower(COALESCE(full_name, '')) IN (lower(%s), lower(%s))
               ORDER BY updated_at DESC LIMIT 1""",
            (h, fam, h, author, cleaned, author, cleaned))
        return row
    except Exception:
        traceback.print_exc()
        return None


def ensure_contact(author, brand, channel):
    """Znajdz kontakt albo zaloz STUB (CRM obowiazkowy - kazda interakcja ma contact_id).
    Zwraca (contact_id, is_new). Autor zaczynajacy sie od '@' = handle platformy.
    B3 (21/07): nazwa stuba = wersja OCZYSZCZONA (bez '• 2nd' itd.) - kolejne warianty
    wyswietlania tej samej osoby trafiaja w ten sam wiersz, nie w nowy stub."""
    author = (author or "").strip()
    if not author:
        return None, False
    row = find_contact(author, channel)
    if row:
        return str(row["id"]), False
    fam = _platform_family(channel)
    is_handle = author.startswith("@")
    name = (clean_author(author.lstrip("@")) or author.lstrip("@").strip())[:200]
    handles = {fam: norm_handle(author)} if is_handle else {}
    try:
        row = db.fetchone(
            """INSERT INTO contacts (name, x_handle, handles, brand_affinity, source, status,
                                     relationship_stage, first_contact_date, narration)
               VALUES (%s,%s,%s,%s,'Comment','Cold','cold',CURRENT_DATE,%s) RETURNING id""",
            (name, norm_handle(author) if (is_handle and fam == "x") else None,
             Jsonb(handles), brand if brand in _BRANDS_ALLOWED else None,
             f"Stub z comment-radaru {fam} (autor ze zrzutu; profil do uzupelnienia intakiem)"))
        return (str(row["id"]) if row else None), True
    except Exception:
        traceback.print_exc()
        return None, False


def relation_context(contact_id):
    """Kontekst relacji do naglowka propozycji: 'komentowales 3x (ostatnio 12/07), stadium:
    commented, tier: Peer'. None gdy brak danych (nie zgadujemy)."""
    if not contact_id:
        return None
    try:
        c = db.fetchone(
            "SELECT name, icp_tier, relationship_stage, who_is_who FROM contacts WHERE id=%s::uuid",
            (contact_id,))
        if not c:
            return None
        e = db.fetchone(
            """SELECT COUNT(*) AS n, MAX(created_at) AS last FROM engagement_log
               WHERE contact_id=%s::uuid AND status IN ('sent','approved','logged')""", (contact_id,))
        n = int((e or {}).get("n") or 0)
        parts = []
        if n:
            last = e.get("last")
            parts.append(f"komentowales {n}x" + (f" (ostatnio {last.strftime('%d/%m')})" if last else ""))
        parts.append(f"stadium: {c.get('relationship_stage') or 'cold'}")
        if c.get("icp_tier"):
            parts.append(f"tier: {c['icp_tier']}")
        # pkt 5 paczki #1 (24/07): kto jest kim po stronie klienta - rola i wplyw na decyzje
        # widoczne tam, gdzie pisze sie do czlowieka (naglowek propozycji i gotowca).
        w = c.get("who_is_who") or {}
        if isinstance(w, dict):
            if w.get("role"):
                parts.append(f"rola: {str(w['role'])[:60]}")
            if w.get("influence_level"):
                parts.append(f"wplyw: {str(w['influence_level'])[:30]}")
        return ", ".join(parts)
    except Exception:
        traceback.print_exc()
        return None


# ---------------- fail-closed przed wykluczeniem z lejka (paczka #1 Managera pkt 7) ----------
# Tier, ktory wyklucza czlowieka z lejka, jest decyzja NIEODWRACALNA w praktyce: nikt nie wraca
# do listy "Competitor" szukac klienta. Dlatego zanim taki tier zostanie ZAREKOMENDOWANY, system
# sprawdza, czy z ta osoba nie ma juz historii rozmow. Jest historia = rekomendacji nie ma
# (a w trybie semi_autonomous decyzja NIE zapadnie sama - ask() bez rekomendacji zawsze pyta
# Tomasza). Historii DM nie duplikujemy w contacts: zrodlem jest engagement_log.
_EXCLUDING_TIERS = {"competitor", "competitor-adjacent", "inne", "out_of_icp", "poza icp"}
_DM_STAGES = ("dm", "offer", "client")


def dm_history(contact_id):
    """(liczba wpisow DM, data ostatniego, stadium relacji) dla kontaktu. Marker [DM] w notes
    zostawiaja obie sciezki: propozycje subagenta i linie dm_* z RAPORTU PRACY."""
    if not contact_id:
        return 0, None, None
    try:
        r = db.fetchone(
            """SELECT (SELECT COUNT(*) FROM engagement_log e
                        WHERE e.contact_id=c.id
                          AND (e.notes ILIKE '%%[DM]%%' OR e.action_type ILIKE '%%dm%%')) AS n,
                      (SELECT MAX(e.created_at) FROM engagement_log e
                        WHERE e.contact_id=c.id
                          AND (e.notes ILIKE '%%[DM]%%' OR e.action_type ILIKE '%%dm%%')) AS last,
                      c.relationship_stage AS stage
               FROM contacts c WHERE c.id=%s::uuid""", (str(contact_id),))
        if not r:
            return 0, None, None
        return int(r.get("n") or 0), r.get("last"), r.get("stage")
    except Exception:
        traceback.print_exc()
        return 0, None, None


def fail_closed_note(contact_id, proposed_tier):
    """Czy wolno REKOMENDOWAC ten tier + notka z dowodem. Zwraca (wolno, notka|None).
    Fail-closed dziala tylko na tiery wykluczajace - Buyer/Peer/Partner ida normalnie."""
    if (proposed_tier or "").strip().lower() not in _EXCLUDING_TIERS:
        return True, None
    n, last, stage = dm_history(contact_id)
    if not n and (stage or "cold") not in _DM_STAGES:
        return True, None
    kiedy = f", ostatni {last.strftime('%d/%m')}" if last else ""
    ile = f"{n} wpisow z rozmow DM{kiedy}" if n else "brak wpisow DM w logu"
    return False, ("UWAGA: to jest wykluczenie z lejka, a z ta osoba juz cos bylo - "
                   f"{ile}, stadium relacji '{stage or 'cold'}'. Nie podpowiadam odpowiedzi; "
                   "zdecyduj sam. Wykluczyc zdazymy zawsze, odzyskac zamknieta rozmowe - nie.")


def bump_stage(contact_id, stage):
    """Podnies stadium relacji TYLKO W PRZOD (klient nie spada do 'commented' po komentarzu)
    + odswiez last_interaction. Wolane przy potwierdzonym wklejeniu komentarza (cmt:done)."""
    if not (contact_id and stage in STAGES):
        return
    try:
        row = db.fetchone("SELECT relationship_stage FROM contacts WHERE id=%s::uuid", (contact_id,))
        cur = (row or {}).get("relationship_stage") or "cold"
        if STAGES.index(stage) > STAGES.index(cur if cur in STAGES else "cold"):
            db.execute("UPDATE contacts SET relationship_stage=%s WHERE id=%s::uuid", (stage, contact_id))
        db.execute(
            """UPDATE contacts SET last_interaction_date=CURRENT_DATE, last_interaction_type='Comment'
               WHERE id=%s::uuid""", (contact_id,))
    except Exception:
        traceback.print_exc()


# ---------------- intake profilu (wymuszony dla nieznanych) ----------------
_OFFERED_KEY = "crm_intake_offered"  # {contact_id: iso_ts} - strażnik B3: karta 'Nowa osoba' max 1/24h


def intake_recently_offered(contact_id):
    """B3 (21/07): czy karta 'Nowa osoba / dam zrzut profilu' poszla dla tej osoby w ostatnich 24h.
    Dowod wady: Djordje dostal 3x karte w jednej sesji."""
    st = _state_get(_OFFERED_KEY)
    ts = st.get(str(contact_id))
    if not ts:
        return False
    try:
        age = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.datetime.fromisoformat(ts)).total_seconds()
        return age < 24 * 3600
    except Exception:
        return False


def mark_intake_offered(contact_id):
    st = {k: v for k, v in _state_get(_OFFERED_KEY).items()
          if _fresh_iso(v, 24 * 3600)}  # przytnij stare wpisy przy okazji
    st[str(contact_id)] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _state_set(_OFFERED_KEY, st)


def _fresh_iso(ts, max_age_s):
    try:
        return (datetime.datetime.now(datetime.timezone.utc)
                - datetime.datetime.fromisoformat(ts)).total_seconds() < max_age_s
    except Exception:
        return False


def arm_intake(chat_id, contact_id, author, brand, channel):
    """Uzbroj stan: NASTEPNY zrzut od Tomasza = profil tej osoby (nie post do komentowania)."""
    _state_set(_INTAKE_KEY, {"chat_id": chat_id, "contact_id": contact_id, "author": author,
                             "brand": brand, "channel": channel,
                             "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()})


def get_intake(chat_id):
    """Swiezy (<= _INTAKE_TTL_MIN) uzbrojony intake dla tego czatu albo None."""
    st = _state_get(_INTAKE_KEY)
    if not (st.get("contact_id") and str(st.get("chat_id")) == str(chat_id)):
        return None
    try:
        age = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.datetime.fromisoformat(st["ts"])).total_seconds()
    except Exception:
        return None
    return st if age < _INTAKE_TTL_MIN * 60 else None


def clear_intake():
    _state_set(_INTAKE_KEY, {})


def process_profile_photo(intake, images):
    """Zrzut profilu -> wizja -> uzupelnienie stuba (imie, handle per platforma, bio-skrot)
    -> tier PROPONOWANY przez model, zatwierdzany guzikami (decisions.ask 'crm_tier').
    Zwraca tekst-paragon dla Tomasza."""
    from . import decisions
    from .generate import profile_from_image
    contact_id = intake["contact_id"]
    brand, channel = intake.get("brand") or "AGS", intake.get("channel") or "x"
    fam = _platform_family(channel)
    prof = profile_from_image(images, channel)
    clear_intake()
    if not prof:
        return ("Nie odczytalem profilu z tego zrzutu - sprobuj wyslac go jeszcze raz "
                "(intake trzeba uzbroic ponownie guzikiem przy propozycji).")
    name = (prof.get("name") or "").strip()[:200]
    handle = norm_handle(prof.get("handle"))
    bio = (prof.get("bio") or "").strip()[:400]
    tier = prof.get("proposed_tier") if prof.get("proposed_tier") in TIERS else None
    why = (prof.get("why") or "").strip()[:200]
    try:
        if name:
            db.execute("UPDATE contacts SET name=%s WHERE id=%s::uuid AND name <> %s",
                       (name, contact_id, name))
        if handle:
            db.execute(
                """UPDATE contacts SET handles = COALESCE(handles,'{}'::jsonb) || %s::jsonb
                   WHERE id=%s::uuid""", (json.dumps({fam: handle}), contact_id))
            if fam == "x":
                db.execute("UPDATE contacts SET x_handle=%s WHERE id=%s::uuid AND x_handle IS NULL",
                           (handle, contact_id))
        if bio:
            db.execute(
                "UPDATE contacts SET narration = COALESCE(narration,'') || %s WHERE id=%s::uuid",
                (f" | [intake {datetime.date.today().strftime('%d/%m')}] {bio}", contact_id))
    except Exception:
        traceback.print_exc()
        return "Nie zapisalem profilu (blad bazy - szczegoly w logu). Wpis w contacts zostal jako stub."
    disp = name or intake.get("author") or "nowa osoba"
    # B3 (21/07): JEDNA decyzja crm_tier per osoba w oknie 24h (dowod wady: Djordje dostal
    # decyzje #6 i #7 o ten sam tier). Otwarta albo swiezo rozstrzygnieta = nie pytamy drugi raz.
    dup = db.fetchone(
        """SELECT id, status, answer FROM agent_decisions
           WHERE decision_type='crm_tier' AND context->>'contact_id'=%s
             AND (status='pending' OR answered_at > NOW() - interval '24 hours')
           ORDER BY created_at DESC LIMIT 1""", (str(contact_id),))
    if dup:
        ask_note = (f"Decyzja tieru #{dup['id']} dla tej osoby juz CZEKA wyzej - nie dubluje."
                    if dup["status"] == "pending"
                    else f"Tier juz rozstrzygniety w ostatnich 24h (decyzja #{dup['id']}: "
                         f"{dup.get('answer')}) - nie pytam drugi raz.")
    else:
        # pkt 7 paczki #1 (24/07): tier wykluczajacy z lejka nie dostaje rekomendacji,
        # gdy z czlowiekiem byla juz rozmowa (fail-closed z DANYCH, nie z opinii modelu).
        wolno, fc_note = fail_closed_note(contact_id, tier)
        ask_note = decisions.ask(
            f"{brand}:{channel}", brand, "crm_tier",
            f"Klasyfikacja ICP dla {disp}" + (f" (@{handle})" if handle else "") + ":\n"
            + (f"BIO: {bio}\n" if bio else "")
            + (f"Propozycja modelu: {tier}" + (f" - {why}" if why else "") if tier
               else "Model nie mial pewnosci - wybierz tier.")
            + (f"\n{fc_note}" if fc_note else ""),
            list(TIER_OPTIONS),
            recommendation=((tier or "").lower() if (wolno and tier in TIERS) else None),
            context={"contact_id": contact_id, "fail_closed": (not wolno)})
    return (f"🧬 Profil zapisany w CRM: {disp}" + (f" (@{handle})" if handle else "")
            + (f"\nBIO: {bio}" if bio else "") + f"\n{ask_note}")


def apply_tier(row, key, chat=None):
    """Akcja decyzji 'crm_tier' (decisions._apply_action): zapis icp_tier na kontakcie."""
    tier = TIER_KEYS.get((key or "").lower())
    contact_id = (row.get("context") or {}).get("contact_id")
    if not (tier and contact_id):
        return
    db.execute("UPDATE contacts SET icp_tier=%s WHERE id=%s::uuid", (tier, contact_id))


def pending_text(brand, channel):
    """'Co wisi?' - propozycje bez decyzji + zatwierdzone-a-niepotwierdzone tego konta."""
    agent = f"{brand}:{channel}"
    lines = []
    try:
        rows = db.fetchall(
            """SELECT e.id, e.author_display, e.created_at, c.relationship_stage
               FROM engagement_log e LEFT JOIN contacts c ON c.id = e.contact_id
               WHERE e.agent=%s AND e.status='proposed'
               ORDER BY e.created_at DESC LIMIT 10""", (agent,))
        if rows:
            lines.append("PROPOZYCJE BEZ DECYZJI:")
            lines += [f"- {r['created_at'].strftime('%d/%m %H:%M')} {r.get('author_display') or '(autor?)'}"
                      + (f" [{r['relationship_stage']}]" if r.get("relationship_stage") else "")
                      for r in rows]
        tasks = db.fetchall(
            """SELECT id, payload, created_at FROM task_queue
               WHERE agent_id=%s AND task_type='comment' AND status='in_progress'
               ORDER BY created_at DESC LIMIT 10""", (agent,))
        if tasks:
            lines.append("ZATWIERDZONE, CZEKA POTWIERDZENIE WKLEJENIA:")
            lines += [f"- {t['created_at'].strftime('%d/%m %H:%M')} "
                      f"{((t.get('payload') or {}).get('author') or '(autor?)')}" for t in tasks]
    except Exception:
        traceback.print_exc()
        return "Nie moge odczytac wiszacych (blad bazy - szczegoly w logu)."
    return "\n".join(lines) if lines else "Nic nie wisi - wszystkie propozycje rozstrzygniete."
