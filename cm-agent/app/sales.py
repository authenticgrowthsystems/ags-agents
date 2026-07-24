"""Agent Sprzedazy Level 1 (BE-SPRZEDAWCA 20/07/2026, brief BRIEF_AGENT_SPRZEDAZY_MVP_20072026).

Rozmowny partner strategiczny + operacyjny wykonawca sprzedazy AGS:
- prospect research przez Researchera (kontrakt /request, tier medium; kanon kosztowy 20/07:
  critical NIGDY przez API - glebokie przeswietlenia Tomasz robi recznie na abonamentach),
- outreach w Voice Bible jako GOTOWIEC do recznego wyslania (HITL ZAWSZE - nic nie wychodzi samo),
- lejek sales_pipeline (paragony przy kazdej zmianie stanu),
- baza wiedzy sprzedazowej sales_knowledge (dokumenty przez Telegram -> chunk -> embedding
  -> semantic search przy outreach).

Wpiecie w istniejacy framework subagentow: wiersz channels (AGS, 'sprzedaz', agent_kind='sales')
sprawia, ze Sprzedawca pojawia sie w menu /agents (n8n buduje menu dynamicznie z channels);
active_agent = 'subagent:AGS:sprzedaz' routuje tu z conversation.handle. Komendy /prospect,
/oferta, /pipeline, /add_sales_material ida DETERMINISTYCZNIE przed LLM (wzorzec _config_route;
klasa incydentow 'Zrobione bez wykonania').

Frameworki sprzedazowe destylowane z Anthropic sales skills (draft-outreach, account-research,
pipeline-review) sa OSADZONE w promptcie systemowym (server-side nie ma Skill toola)."""
import datetime
import io
import json
import re
import traceback

import httpx

from . import db, config, tasks, research, content_memory, compliance
from .brand import load_brand
from .generate import client
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

AGENT_KEY = "subagent:AGS:sprzedaz"   # wartosc active_agent (z menu /agents przez agsel:)
AGENT_ID = "sales-agent"              # agent_registry (prawo do critical w Researcherze, DDL 027)
BRAND = "AGS"
_MAX_TOOL_STEPS = 5
_STATE_KEY = "sales_pending_material"  # brand_config: uzbrojony /add_sales_material
_PENDING_TTL_MIN = 120

_STAGES = ("prospect", "qualified", "proposal", "negotiation", "won", "lost")
_STAGE_ICON = {"prospect": "🔍", "qualified": "🎯", "proposal": "📄",
               "negotiation": "🤝", "won": "✅", "lost": "❌"}


# ---------------- stan (brand_config, wzorzec crm/_dispatch_alert) ----------------
def _state_get():
    r = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key=%s ORDER BY version DESC LIMIT 1",
        (_STATE_KEY,))
    try:
        return json.loads(r["config_value"]) if r and r.get("config_value") else {}
    except Exception:
        return {}


def _state_set(obj):
    db.execute(
        """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
           VALUES ('AGS',%s,%s,1,'sales-agent',NOW())
           ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
             version=brand_config.version+1, updated_by='sales-agent', updated_at=NOW()""",
        (_STATE_KEY, json.dumps(obj, ensure_ascii=False)))


def clear_pending():
    _state_set({})


def _pending_armed():
    st = _state_get()
    if not st.get("armed"):
        return None
    try:
        age = (datetime.datetime.now(WARSAW)
               - datetime.datetime.fromisoformat(st["ts"])).total_seconds()
    except Exception:
        age = 0
    if age > 60 * _PENDING_TTL_MIN:
        clear_pending()
        return None
    return st


# ---------------- kontekst z DB (zywe dane do promptu) ----------------
def _pricing_text():
    rows = db.fetchall(
        """SELECT ladder, tier_name, price, currency, features, meta_status
           FROM pricing_tiers WHERE brand_id='AGS' ORDER BY ladder, tier_name""")
    if not rows:
        return "(pricing_tiers puste - dopytaj Tomasza o cennik)"
    lines = []
    last = None
    for r in rows:
        if r["ladder"] != last:
            last = r["ladder"]
            tag = " [Pakiety PL - TOP OFFERING dla malych firm PL: DFY system retencji klientow]" \
                if last == "lokalna_automatyzacja" else ""
            lines.append(f"DRABINKA {last}{tag}:")
        feats = ""
        try:
            f = r.get("features") or {}
            if f:
                feats = " | " + json.dumps(f, ensure_ascii=False)[:220]
        except Exception:
            traceback.print_exc()  # AP-306: skladanie cennika
        lines.append(f"- {r['tier_name']}: {r.get('price') or '?'} {r.get('currency') or ''}"
                     f" ({r.get('meta_status')}){feats}")
    return "\n".join(lines)


def _icp_text():
    rows = db.fetchall(
        "SELECT name, definition FROM icp_definitions WHERE brand_id='AGS' ORDER BY created_at LIMIT 4")
    return "\n".join(f"- {r['name']}: {(r.get('definition') or '')[:500]}" for r in rows) \
        or "(brak definicji ICP w bazie)"


def _playbook_text():
    rows = db.fetchall(
        "SELECT section, title, content FROM sales_playbook WHERE brand_id='AGS' ORDER BY created_at LIMIT 6")
    return "\n".join(f"- [{r['section']}] {(r.get('title') or '')}: {(r.get('content') or '')[:350]}"
                     for r in rows) or "(sales_playbook pusty)"


def _knowledge_stats():
    row = db.fetchone(
        """SELECT COUNT(*) AS n, COUNT(DISTINCT material_name) AS docs FROM sales_knowledge
           WHERE brand_id='AGS'""") or {"n": 0, "docs": 0}
    if not row["n"]:
        return "(baza wiedzy pusta - Tomasz karmi ja przez /add_sales_material)"
    names = db.fetchall(
        """SELECT DISTINCT material_name FROM sales_knowledge WHERE brand_id='AGS'
           ORDER BY material_name LIMIT 8""")
    return (f"{row['docs']} materialow ({row['n']} kawalkow): "
            + ", ".join(n["material_name"][:40] for n in names)
            + ". Przy outreach/ofercie SIEGAJ po sales_knowledge_search.")


def pipeline_text():
    rows = db.fetchall(
        """SELECT prospect_name, stage, offer_tier, value, currency, next_followup_at, updated_at,
                  notes, contact_email, contact_phone
           FROM sales_pipeline WHERE brand_id='AGS' AND stage NOT IN ('won','lost')
           ORDER BY array_position(ARRAY['negotiation','proposal','qualified','prospect']::text[], stage),
                    updated_at DESC LIMIT 30""")
    closed = db.fetchone(
        """SELECT COUNT(*) FILTER (WHERE stage='won') AS won,
                  COUNT(*) FILTER (WHERE stage='lost') AS lost,
                  COALESCE(SUM(value) FILTER (WHERE stage='won'), 0) AS won_value
           FROM sales_pipeline WHERE brand_id='AGS'""") or {}
    if not rows and not (closed.get("won") or closed.get("lost")):
        return "📊 Lejek pusty. Start: /prospect <nazwa albo URL firmy>."
    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [f"📊 LEJEK SPRZEDAZY ({len(rows)} otwartych):"]
    for r in rows:
        bits = []
        if r.get("offer_tier"):
            bits.append(f"oferta: {r['offer_tier']}")
        if r.get("value"):
            bits.append(f"{r['value']:.0f} {r.get('currency') or ''}")
        if r.get("next_followup_at"):
            fu = r["next_followup_at"]
            late = " ⚠️ PO TERMINIE" if fu < now else ""
            bits.append(f"nastepny kontakt: {fu.astimezone(WARSAW).strftime('%d/%m %H:%M')}{late}")
        else:
            bits.append("⚠️ BRAK nastepnego kroku")
        stale = (now - r["updated_at"]).days if r.get("updated_at") else 0
        if stale >= 14:
            bits.append(f"⚠️ cisza {stale} dni")
        # Kontakt widoczny w lejku (DDL 029): dane z wizytowki i researchu maja sluzyc TU,
        # a nie tylko w naglowku gotowca - inaczej baza wie, a czlowiek nie.
        kontakt = " ".join(x for x in [f"☎️{r.get('contact_phone')}" if r.get("contact_phone") else "",
                                       f"✉️{r.get('contact_email')}" if r.get("contact_email") else ""] if x)
        if kontakt:
            bits.append(kontakt)
        elif r["stage"] in ("prospect", "qualified"):
            bits.append("⚠️ brak kontaktu")
        lines.append(f"{_STAGE_ICON.get(r['stage'], '•')} [{r['stage']}] {r['prospect_name'][:60]}"
                     + (" | " + ", ".join(bits) if bits else ""))
    lines.append(f"Zamkniete: won {closed.get('won', 0)} ({closed.get('won_value', 0):.0f}), "
                 f"lost {closed.get('lost', 0)}.")
    return "\n".join(lines)


def _find_pipeline(fragment):
    frag = (fragment or "").strip()
    if not frag:
        return None
    return db.fetchone(
        """SELECT * FROM sales_pipeline
           WHERE brand_id='AGS' AND (prospect_name ILIKE %s OR prospect_url ILIKE %s)
           ORDER BY updated_at DESC LIMIT 1""", (f"%{frag}%", f"%{frag}%"))


def _append_notes(row_id, note):
    # 22/07 (feedback do podsumowania klienta): pojedynczy wpis przycinany do 600 znakow -
    # bloby (caly research/strategia) zjadaly budzet 4000 i wypychaly historie (uciete
    # "Sekwen"). Pelne tresci zyja w sales_knowledge/plikach - notatka to OS CZASU, nie magazyn.
    clean = re.sub(r"\s+", " ", str(note or "")).strip()
    if len(clean) > 600:
        clean = clean[:597] + "..."
    db.execute(
        """UPDATE sales_pipeline
           SET notes = LEFT(COALESCE(notes,'') || %s, 4000), updated_at=NOW() WHERE id=%s""",
        (f"\n[{datetime.datetime.now(WARSAW).strftime('%d/%m %H:%M')}] {clean}", row_id))


# ---------------- Telegram (przez conversation, jeden transport) ----------------
def _tg_send(chat_id, text):
    from . import conversation
    conversation._reply(chat_id, text)


# ---------------- prompt systemowy ----------------
# Destylat GOTOWOSC_PRODUKTU.md (stan 22/07) - co WOLNO sprzedawac. Zrodlo prawdy = plik;
# aktualizacja tego bloku przy kazdej zmianie macierzy (kanon DOKUMENTACJA ZYJE).
_GOTOWOSC = (
    "CO SPRZEDAJEMY DZIS (macierz gotowosci 22/07, model done-for-you na NASZEJ infrastrukturze):\n"
    "- DIAGNOZA PRZEPLYWU INFORMACJI (enterprise/premium; decyzja Tomasza 22/07): osobista "
    "usluga architekta systemow dla firm POZA ICP pakietow (duza skala, holdingi - np. "
    "Adamietz). 2-4 tyg., mapa gdzie informacja ginie + plan. Cena 15-30 tys. PLN, PODLOGA "
    "12 tys. Zero pitchu platformy/AI bez case studies - sprzedajemy ekspertyze i raport, "
    "nie wdrozenie. Dla takich prospektow NIE proponuj Pakietow PL (strzal w stope) i NIE "
    "rekomenduj 'odpuscic' - gra idzie o diagnoze.\n"
    "- TOP OFFERING (male firmy PL): DFY 'system retencji klientow' na Pakietach PL 1-3 "
    "(2000-3000 / 3000-5000 / 5000-8000 PLN setup jednorazowo; narzedzie ok. 97-297 USD/mc "
    "klient placi SAM bezposrednio vendorowi). Setup = praca Tomasza: pipeline, sekwencje "
    "follow-up email/SMS, branding klienta, szkolenie 2-4 sesje, runbook.\n"
    "- Subagent X pod nadzorem (SPRZEDAWALNY MVP): plan tygodnia pod ICP klienta, tresci do "
    "akceptu 1 tapem, publikacja w slotach, metryki per post, komentarze pod widocznosc.\n"
    "- Idea Bot (SPRZEDAWALNY MVP): pomysl glosem/tekstem/zdjeciem -> research -> posty PL+EN.\n"
    "- Researcher (dodatek premium, z nota): badania 5 zrodel, koszt per job widoczny.\n"
    "- Subagent LinkedIn: CZESCIOWY (gotowce do recznej publikacji; auto-API czeka na review).\n"
    "- Blueprint 2000 USD (W1): landing LIVE z aplikacja; BRAK sciezki platnosci.\n"
    "CZEGO NIE SPRZEDAJEMY: Agent Wizualny (zamrozony), wdrozenie self-hosted u klienta "
    "(brak playbooka), pelna autonomia tresci (kanon: zatwierdza czlowiek), interfejs inny "
    "niz Telegram."
)

# Destylat Anthropic sales skills: draft-outreach + account-research + pipeline-review.
_FRAMEWORKS = (
    "FRAMEWORKI (destylat sprawdzonych playbookow - stosuj, nie recytuj):\n"
    "OUTREACH (research-first, NIGDY generyczny):\n"
    "- Hierarchia hooka: 1) trigger event (finansowanie, rekrutacje, premiera, news) "
    "2) wspolny kontakt 3) ICH tresc (post/artykul/wystapienie) 4) inicjatywa firmy "
    "5) pain point roli (ostatecznosc).\n"
    "- Struktura maila: temat <50 znakow spersonalizowany; otwarcie = konkret z researchu; "
    "1-2 zdania o ich problemie; JEDEN value prop / dowod; JEDNO niskoprogowe CTA "
    "(np. '15 minut rozmowy w tym tygodniu?'). Akapity 2-3 zdania.\n"
    "- ZAKAZY: 'mam nadzieje, ze u Pana wszystko dobrze', 'pisze, poniewaz...', wyliczanki "
    "funkcji, kilka value propow naraz, fejkowa personalizacja ('widze, ze pracuje Pan w X'), "
    "JAKIKOLWIEK markdown w tresci maila (czysty tekst!).\n"
    "- LinkedIn: zaproszenie <300 znakow BEZ pitchu; pitch dopiero w wiadomosci po akcepcie, "
    "value-first.\n"
    "- Sekwencja follow-up: dzien 3 (nowy kat), dzien 7 (inny value prop), dzien 14 (break-up, "
    "krotki). Agent PROPONUJE terminy, Tomasz wysyla.\n"
    "PROSPECT RESEARCH: szukaj sygnalow kupna (zatrudnianie, wzrost, nowe uslugi, slaba "
    "retencja/opinie, brak follow-upu po leadzie), problemow ktore rozwiazujemy (klienci nie "
    "wracaja, leady gina, brak systemu poleceń) i haka personalizacji.\n"
    "PIPELINE (higiena): KAZDY otwarty deal ma next step Z DATA; cisza >14 dni = follow-up "
    "albo przenies do lost; pilnuj zeby rozmowa nie wisiala na jednej osobie; przy /pipeline "
    "wskazuj co wymaga ruchu DZIS."
)

_RULES = (
    "TWARDE ZASADY:\n"
    "- KONFLIKT INTERESOW (kanon Tomasza, doprecyzowany 24/07 - JEDNO kryterium, bez promieni): "
    "NIE sprzedajemy szkolom tanca, studiom i zespolom tanecznym z MIASTA OPOLE. Tylko Opole. "
    "Reszta wojewodztwa opolskiego, caly Slask, Dolny Slask i reszta Polski sa w ICP - tam "
    "Royal Dance Center nie rekrutuje uczestnikow. Nie licz odleglosci i nie rozszerzaj reguly "
    "na sasiednie miejscowosci: jesli adres prospekta to nie Opole, piszesz normalnie. Powod "
    "reguly: system retencji w rekach konkurenta z tego samego miasta = narzedzie do odbierania "
    "klientow RDC. Regula obowiazuje, dopoki Tomasz prowadzi RDC. Prospekt z Opola: NIE rob "
    "researchu, NIE pisz outreachu - oznacz w lejku jako 'lost' z notatka 'konflikt interesow "
    "RDC' i powiedz Tomaszowi wprost.\n"
    "- NARZEDZIA NIE UJAWNIAMY: nazwa platformy (GHL i inne) NIGDY nie pada w komunikacji "
    "sprzedazowej.\n"
    # Paczka Managera 24/07 pkt 3 (blocker rozmowy z Piotrem/Adamietz): klient nie kupuje
    # technologii, tylko wynik. Slowo "system AI" opisuje NASZ swiat, nie jego problem.
    "- SLOWNICTWO PRODUKTU (auto-odrzut): w tekstach do klienta NIE uzywamy slow "
    "'automatyzacje', 'workflows', 'systemy AI', 'integracje', 'AI systems', 'AI workflows', "
    "'agents platform', 'custom AI'. Mowimy REZULTATEM w jego jezyku: 'utrzymuje Ci klientow, "
    "ktorzy dzis odchodza' zamiast 'buduje Ci system AI'; 'nikt nie zostaje bez odpowiedzi' "
    "zamiast 'wdrazamy automatyzacje'; 'zapisy same sie domykaja' zamiast 'integracja z CRM'. "
    "Nazwa technologii moze paść dopiero, gdy klient SAM o nia zapyta.\n"
    # Sugestia Tomasza 24/07: "wszelkie zangielszczenia nie powinny miec tu miejsca".
    "- CZYSTA POLSZCZYZNA w tekstach PL: zero anglicyzmow i kalk. 'follow-up' to "
    "'przypomnienie' albo 'kontakt zwrotny'; 'lead' to 'zapytanie'; 'case study' to 'przyklad "
    "wdrozenia'; 'onboarding' to 'wdrozenie'; 'deadline' to 'termin'; 'feedback' to 'informacja "
    "zwrotna'; 'insight' to 'wniosek'. Test mamy: czy moja mama uznalaby to zdanie za naturalne "
    "po polsku. Angielski zostaje w tekstach EN, gdzie jest u siebie.\n"
    "- REGULA PRAWDY: AGS jest przed pierwszym platnym klientem - ZERO zmyslonych case studies, "
    "liczb i referencji. Dowod spoleczny = wlasny zywy system AGS (build-in-public) i realne "
    "wdrozenia rodzinne (TNM, RDC) opisywane uczciwie.\n"
    "- Waluty: oferty PL w PLN, oferty miedzynarodowe AGS w USD; fakty w walucie zrodla.\n"
    "- NIE odsylasz do strony /apply (doktryna).\n"
    "- Wartosc przed cena: problem -> wartosc -> mechanizm -> cena. Cennik od gory (premium "
    "pierwsze), schodzisz nizej TYLKO na wyrazny sygnal.\n"
    "- HITL: NIC nie wysyla sie samo. Kazdy outreach = gotowiec, Tomasz wysyla recznie.\n"
    "- Zero em dash; po polsku czysta polszczyzna.\n"
    "- TWARDA ZASADA WYKONANIA: kazda zmiana stanu (lejek, research, gotowiec, zapis wiedzy) "
    "dzieje sie WYLACZNIE przez wywolanie narzedzia w TEJ turze. NIGDY nie mow 'zapisalem/"
    "zlecilem', jesli nie masz wyniku narzedzia."
)

# Sekcja powstala z ZYWEGO dowodu (gotowiec StandART 24/07 11:44): model otworzyl mail od "widze,
# ze...", czyli od frazy wprost zakazanej w frameworkach, i zamknal go CTA przepisanym doslownie
# z PRZYKLADU w tych frameworkach. Zakaz w liscie nie wystarczyl - potrzebny jest osobny blok,
# ktory nazywa te dwa mechanizmy: recytowanie ilustracji i pozorowana personalizacja.
_ANTY_SZABLON = (
    "ZAKAZ SZABLONU (najwazniejsze dla jakosci tekstu):\n"
    "- Przyklady w powyzszych frameworkach to ILUSTRACJE MECHANIZMU, nie tekst do przepisania. "
    "Jesli Twoje zdanie da sie znalezc w instrukcji, ktora czytasz - napisz je od nowa.\n"
    "- Zakazane otwarcia: 'widze, ze', 'zauwazylem, ze', 'trafilem na', 'pisze, poniewaz', "
    "'mam nadzieje, ze'. Nie opisuj adresatowi jego wlasnej firmy - on wie, czym sie zajmuje. "
    "Wchodzisz od OBSERWACJI albo PYTANIA, ktore ma sens tylko wobec NIEGO.\n"
    "- Zakazane zwroty sprzedazowe: 'pomagamy firmom/klubom/szkolom X robic Y', 'nie chodzi o "
    "gorsza oferte, tylko o brak systemu', 'chetnie pokaze, jak to wyglada w praktyce', "
    "'masz 15 minut w tym tygodniu'. Kazde z nich pasuje do dowolnej firmy, wiec nie znaczy nic.\n"
    "- Hak MUSI byc weryfikowalny w researchu: konkretna inicjatywa, wydarzenie, oferta, zapis "
    "ze strony. Bez takiego konkretu napisz krotszy, uczciwie ogolny tekst - nie udawaj "
    "personalizacji ogolnikiem.\n"
    "- CTA formuluj jako pytanie o RZECZ, nie o kalendarz: pytaj o to, jak dzis obsluguja u nich "
    "konkretny proces. W PIERWSZEJ wiadomosci NIE proponujesz spotkania w zadnej formie - zaden "
    "'15 minut', 'krotka rozmowa', 'call', 'zamienie kilka slow', zadna liczba minut ani "
    "propozycja terminu. Rozmowa jest do zaproponowania dopiero, gdy odpisza (dowod 24/07: model "
    "przeredagowal zakazane '15 minut' zamiast je porzucic - liczy sie INTENCJA zakazu).\n"
    "- JEDEN rejestr w calym tekscie. Po polsku do firmy: konsekwentnie 'Panstwo' albo "
    "konsekwentnie 'Pan/Pani' z nazwiskiem, gdy research wskazuje jedna osobe decyzyjna. "
    "Mieszanie 'u Was' i 'z Panstwem' w jednym mailu czyta sie jak sklejka z szablonu.\n"
    "- Rytm: krotkie zdania, zero symetrycznych konstrukcji 'nie X, tylko Y' wiecej niz raz, zero "
    "wyliczen korzysci, zero slow 'rozwiazanie', 'proces', 'optymalizacja', 'usprawnienie'.\n"
    # Dowod 24/07: hak brzmial "trzymam kciuki PRZED Mistrzostwami Europy", a mistrzostwa juz sie
    # odbyly. Wydarzenie w zlym czasie jest gorsze niz brak haka - czyta sie jak automat.
    "- CZAS WYDARZENIA: zanim uzyjesz wydarzenia jako haka, ustal, czy JUZ BYLO, czy dopiero "
    "bedzie. Sprawdz date w materiale i porownaj z dzisiejsza. Gdy juz bylo - pytaj, jak poszlo. "
    "Gdy dopiero bedzie - mozesz trzymac kciuki. Gdy daty NIE MA w materiale, nie zgaduj czasu: "
    "napisz o wydarzeniu bez rozstrzygania, czy jest przed, czy po.\n"
    "- Test przed oddaniem tekstu: gdyby podmienic nazwe firmy na inna z tej samej branzy, czy "
    "mail dalej mialby sens? Jesli tak - jest za slaby, przepisz go."
)


def _system(chat_id):
    from .conversation import comm_guide, _memory_text
    brand = load_brand(BRAND)
    now = datetime.datetime.now(WARSAW).strftime("%A %d/%m/%Y %H:%M")
    role = (
        f"Jestes AGENTEM SPRZEDAZY AGS (Authentic Growth Systems). Rozmawiasz na Telegramie z "
        f"Tomaszem, wlascicielem - jestes jego PARTNEREM STRATEGICZNYM w sprzedazy: masz wlasne "
        f"zdanie, proponujesz kogo targetowac, jak, kiedy dosylac follow-up i kiedy domykac; "
        f"zadajesz jedno trafne pytanie zamiast ankiet. {comm_guide()} "
        f"Priorytet operacyjny: PIERWSZA sprzedaz jak najszybciej - kazda rozmowa ma prowadzic "
        f"do nastepnego konkretnego ruchu w lejku.\n"
        f"Teraz jest {now} (Europe/Warsaw).\n\n"
        f"{_GOTOWOSC}\n\n"
        f"OFERTA I CENY (pricing_tiers, zywe z bazy):\n{_pricing_text()}\n\n"
        f"{_RULES}\n\n"
        f"ICP (kogo szukamy):\n{_icp_text()}\n\n"
        f"SALES PLAYBOOK (z bazy):\n{_playbook_text()}\n\n"
        f"{_FRAMEWORKS}\n\n"
        f"LEJEK (zywy stan):\n{pipeline_text()}\n\n"
        f"BAZA WIEDZY SPRZEDAZOWEJ: {_knowledge_stats()}\n\n"
        # Wczesniej szlo tu voice_bible[:2500] z 22 tys. znakow razem z poleceniem "outreach MUSI
        # byc w tym glosie" - polecenie bez pokrycia, bo zasad pisania w tym oknie nie ma. Rdzen
        # glosu jest krotki i wchodzi w calosci; pelna Voice Bible dostaje narzedzie draft_outreach.
        f"RDZEN GLOSU (pelny):\n{_voice_dna_core()}\n"
        f"Pelna Voice Bible wchodzi automatycznie do narzedzia draft_outreach. W rozmowie NIE "
        f"parafrazuj jej z pamieci - gotowce pisz narzedziem.\n\n"
        f"PAMIEC WCZESNIEJSZYCH ROZMOW (skroty wygaslych watkow):\n{_memory_text(AGENT_KEY)}"
    )
    return [{"type": "text", "text": role}]


# ---------------- narzedzia ----------------
TOOL_PROSPECT_RESEARCH = {
    "name": "prospect_research",
    "description": ("Zlec Researcherowi research prospekta (firma/osoba; URL albo nazwa). "
                    "Async: kilka minut, ~1-2 PLN (tier medium), wynik przyjdzie na Telegram "
                    "i zapisze sie w lejku. Tworzy/aktualizuje wpis w lejku (stage prospect). "
                    "Uzywaj gdy Tomasz podaje nowego prospekta albo prosi o rozpoznanie firmy. "
                    "KANON KOSZTOWY 20/07: critical NIGDY przez API (~18 PLN) - glebokie "
                    "przeswietlenie Tomasz robi RECZNIE na abonamentach i wrzuca zrzut."),
    "input_schema": {"type": "object", "properties": {
        "prospect": {"type": "string", "description": "Nazwa firmy/osoby (jak w lejku)."},
        "url": {"type": ["string", "null"], "description": "URL strony/profilu, jesli jest."},
        "tier": {"type": ["string", "null"], "enum": ["low", "medium", None],
                 "description": "Glebokosc researchu; default medium."}},
        "required": ["prospect"]},
}

TOOL_PROSPECT_RESULTS = {
    "name": "prospect_results",
    "description": ("Pokaz WYNIKI researchu prospekta z lejka (claims z linkami zrodel). Uzywaj "
                    "zanim napiszesz outreach albo gdy Tomasz pyta 'co wiemy o X'."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string", "description": "Fragment nazwy prospekta z lejka."}},
        "required": ["prospect_fragment"]},
}

TOOL_DRAFT_OUTREACH = {
    "name": "draft_outreach",
    "description": ("Napisz spersonalizowany outreach (email / LinkedIn DM / X DM) do prospekta "
                    "w Voice Bible i wyslij Tomaszowi jako GOTOWIEC do recznego wyslania (czysta "
                    "wklejka osobna wiadomoscia; NIC nie wysyla sie samo). Korzysta z researchu "
                    "prospekta (jesli jest) i bazy wiedzy sprzedazowej. Zapisuje propozycje w "
                    "engagement_log i notatke w lejku."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string", "description": "Fragment nazwy prospekta z lejka."},
        "channel": {"type": "string", "enum": ["email", "linkedin_dm", "x_dm"],
                    "description": "Kanal outreachu."},
        "language": {"type": ["string", "null"], "enum": ["pl", "en", None],
                     "description": "Jezyk wiadomosci; default pl (rynek PL), en dla zagranicy."},
        "guidance": {"type": ["string", "null"],
                     "description": "Wskazowki Tomasza / uzgodniony kat (hook, oferta, ton)."}},
        "required": ["prospect_fragment", "channel"]},
}

TOOL_OFFER_FOR = {
    "name": "offer_for",
    "description": ("Zbierz DANE do dopasowania oferty dla prospekta: wpis z lejka + wyniki "
                    "researchu + pelny cennik. Wynik wraca do Ciebie - na jego bazie REKOMENDUJESZ "
                    "tier (od gory: premium pierwsze) z uzasadnieniem wartoscia, i zapisujesz "
                    "wybor przez pipeline_move (offer_tier)."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string", "description": "Fragment nazwy prospekta z lejka."}},
        "required": ["prospect_fragment"]},
}

TOOL_PIPELINE_VIEW = {
    "name": "pipeline_view",
    "description": "Pokaz aktualny lejek sprzedazy (otwarte pozycje, follow-upy, zaniedbania).",
    "input_schema": {"type": "object", "properties": {}},
}

TOOL_PIPELINE_ADD = {
    "name": "pipeline_add",
    "description": ("Dodaj prospekta do lejka RECZNIE (bez researchu). Uzywaj gdy Tomasz mowi "
                    "'dodaj do lejka X' / 'mam leada Y'."),
    "input_schema": {"type": "object", "properties": {
        "prospect_name": {"type": "string"},
        "url": {"type": ["string", "null"]},
        "stage": {"type": ["string", "null"], "enum": list(_STAGES) + [None],
                  "description": "Default prospect."},
        "value": {"type": ["number", "null"], "description": "Szacowana wartosc dealu."},
        "currency": {"type": ["string", "null"], "description": "PLN albo USD; default PLN."},
        "note": {"type": ["string", "null"]}},
        "required": ["prospect_name"]},
}

TOOL_PIPELINE_MOVE = {
    "name": "pipeline_move",
    "description": ("Przesun prospekta w lejku / zaktualizuj deal (stage, wartosc, oferta, "
                    "data follow-up, notatka). KAZDA zmiana stanu lejka idzie przez to narzedzie "
                    "(paragon). Stage: prospect->qualified->proposal->negotiation->won/lost."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string"},
        "stage": {"type": ["string", "null"], "enum": list(_STAGES) + [None]},
        "offer_tier": {"type": ["string", "null"], "description": "Nazwa tieru z cennika."},
        "value": {"type": ["number", "null"]},
        "currency": {"type": ["string", "null"]},
        "next_followup_at": {"type": ["string", "null"],
                             "description": "ISO 8601 Europe/Warsaw, np. 2026-07-23T10:00."},
        "note": {"type": ["string", "null"]}},
        "required": ["prospect_fragment"]},
}

TOOL_KNOWLEDGE_SEARCH = {
    "name": "sales_knowledge_search",
    "description": ("Przeszukaj SEMANTYCZNIE baze wiedzy sprzedazowej (ksiazki/techniki/case "
                    "studies Tomasza) pod konkretne pytanie: technika otwarcia, obiekcja cenowa, "
                    "follow-up, negocjacje. Uzywaj PRZED pisaniem outreachu i przy doradztwie."),
    "input_schema": {"type": "object", "properties": {
        "query": {"type": "string", "description": "Czego szukasz, konkretnie."}},
        "required": ["query"]},
}

TOOL_OUTREACH_SENT = {
    "name": "outreach_sent",
    "description": ("Odnotuj, ze Tomasz WYSLAL outreach do prospekta (mowi 'wyslalem', 'poszlo'). "
                    "Oznacza propozycje jako wyslana i ustawia follow-up za 3 dni, jesli nie ma."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string"}},
        "required": ["prospect_fragment"]},
}

_SALES_TOOLS = [TOOL_PROSPECT_RESEARCH, TOOL_PROSPECT_RESULTS, TOOL_DRAFT_OUTREACH, TOOL_OFFER_FOR,
                TOOL_PIPELINE_VIEW, TOOL_PIPELINE_ADD, TOOL_PIPELINE_MOVE, TOOL_KNOWLEDGE_SEARCH,
                TOOL_OUTREACH_SENT]
# wyniki pokazywane Tomaszowi doslownie (dane); offer_for wraca TYLKO do modelu (kontekst rekomendacji)
_VERBATIM = {"pipeline_view", "prospect_results", "sales_knowledge_search", "dziennik_klienta"}
_MODEL_ONLY = {"offer_for"}


# ---------------- research prospekta (kontrakt /request Researchera) ----------------
def _ensure_pipeline(name, url=None, source="conversation"):
    row = _find_pipeline(name) or (_find_pipeline(url) if url else None)
    if row:
        return row, False
    row = db.fetchone(
        """INSERT INTO sales_pipeline (brand_id, prospect_name, prospect_url, stage, source)
           VALUES ('AGS',%s,%s,'prospect',%s) RETURNING *""",
        (name.strip()[:200], (url or None), source))
    return row, True


def _identity_hint(row):
    """Dyskryminator tozsamosci dla prospekta BEZ domeny (9 z 12 w lejku ma tylko gmail).
    Pierwsza linia notatek niesie miasto i kontakt ("Szkola tanca, Dobrzykowice. Kontakt: ...") -
    bez tego zapytaniem jest sama nazwa i research trafia w podmiot z innego kraju."""
    head = re.split(r"\n\[", (row or {}).get("notes") or "", maxsplit=1)[0]
    head = re.sub(r"\s+", " ", head).strip()
    return head[:200] or None


def _city_from_notes(pipe):
    """Miasto z pierwszej linii kartoteki ("Szkola tanca, Dobrzykowice. Kontakt: ...")."""
    m = re.match(r"[^,]{0,60},\s*([^.,;]{3,40})", _identity_hint(pipe) or "")
    return m.group(1).strip() if m else None


def _identity_verdict(pipe, job_id, summary="", tekst_strony=""):
    """Bramka tozsamosci: TRZY stany, bo to DWA rozne pytania.
    (1) Czy research dotyczy TEJ firmy - liczone z DOWODOW (domena prospekta w zrodlach albo
        claims; bez domeny: miasto z kartoteki w claims). Model tu nie glosuje: tap-test 24/07
        pokazal, ze potrafi zignorowac kontrakt pierwszej linii.
    (2) Czy cos budzi watpliwosc - deklaracja modelu ("TOZSAMOSC: niepewna - powod").

    Pierwsza wersja dawala modelowi prawo weta i zablokowala 2 poprawne prospekty na 2
    (La Cultura z Sosnowca i STC - w obu dowody potwierdzaly podmiot, a model marudzil o kanal
    kontaktu). Bramka blokujaca poprawne przypadki zostanie zignorowana i przestanie chronic
    przed prawdziwym Rhode Island, wiec zastrzezenie MODELU obniza stan do ostrzezenia,
    a blokuje wylacznie BRAK DOWODU.

    Zwraca (stan, powod), stan: 'potwierdzona' | 'z zastrzezeniem' | 'niepotwierdzona'."""
    m = re.search(r"TOZSAMOSC:\s*niepewn\w*\s*[-:]?\s*(.{0,160})", summary or "", re.IGNORECASE)
    zastrzezenie = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
    if not job_id:
        return "niepotwierdzona", "brak joba researchu"
    host = re.sub(r"^https?://(www\.)?", "", (pipe or {}).get("prospect_url") or "").split("/")[0].strip()
    dowod, opis = False, "kartoteka bez domeny i miasta"
    try:
        if host:
            r = db.fetchone(
                """SELECT (EXISTS (SELECT 1 FROM evidence_items e
                                   JOIN research_runs rr ON rr.run_id = e.run_id
                                   WHERE rr.job_id=%s AND e.source_url ILIKE %s)
                        OR EXISTS (SELECT 1 FROM claims c
                                   WHERE c.job_id=%s AND c.claim_text ILIKE %s)) AS ok""",
                (job_id, f"%{host}%", job_id, f"%{host}%"))
            dowod, opis = bool((r or {}).get("ok")), f"domena {host}"
            # Strona pobrana przez agenta jest dowodem MOCNIEJSZYM niz evidence z wyszukiwarki:
            # to tresc pod adresem prospekta, zdjeta w tej turze.
            if not dowod and host.lower() in (tekst_strony or "").lower():
                dowod, opis = True, f"domena {host} (strona pobrana przez agenta)"
        else:
            miasto = _city_from_notes(pipe)
            if miasto:
                r = db.fetchone(
                    "SELECT EXISTS (SELECT 1 FROM claims c WHERE c.job_id=%s AND c.claim_text ILIKE %s) AS ok",
                    (job_id, f"%{miasto}%"))
                dowod, opis = bool((r or {}).get("ok")), f"miasto {miasto}"
                if not dowod and miasto.lower() in (tekst_strony or "").lower():
                    dowod, opis = True, f"miasto {miasto} (na stronie pobranej przez agenta)"
    except Exception:
        traceback.print_exc()
        return "niepotwierdzona", "sonda tozsamosci padla"
    if not dowod:
        return "niepotwierdzona", (f"{opis} nie wystepuje w dowodach" if host or opis.startswith("miasto") else opis)
    return ("z zastrzezeniem", zastrzezenie or "research zglosil watpliwosc") if zastrzezenie \
        else ("potwierdzona", f"{opis} w dowodach")


def _research_query(name, url, hint=None, ze_strony=None):
    return (
        f"Prospect research dla sprzedazy B2B (AGS - systemy retencji klientow i agenty AI "
        f"dla malych firm): {name}" + (f", strona: {url}" if url else "")
        + (f", dane z kartoteki: {hint}" if hint and not url else "") + ". "
        "Ustal: 1) czym dokladnie jest ta firma/osoba (branza, skala, oferta, lokalizacja); "
        "2) SYGNALY KUPNA: zatrudnianie, wzrost, nowe uslugi/lokalizacje, aktywnosc "
        "marketingowa, opinie klientow (zwlaszcza skargi na kontakt/obsluge/brak odpowiedzi); "
        "3) problemy, ktore rozwiazuje automatyzacja follow-up i system retencji klientow "
        "(gubione leady, klienci nie wracaja, brak systemu opinii/polecen); "
        "4) hak personalizacji do pierwszego kontaktu (konkretny news, tresc, inicjatywa); "
        "5) kto decyduje i jak ich dosiegnac. Kazdy fakt z linkiem zrodla. "
        + (f"FAKTY ZDJETE BEZPOSREDNIO ZE STRONY PROSPEKTA (traktuj jako pewne, nie podwazaj "
           f"i nie pisz, ze ich brak): {re.sub(chr(10), ' ', ze_strony)[:900]} " if ze_strony else "")
        # REGULA PRAWDY 24/07: podmiot o podobnej nazwie w innym kraju wrocil jako "ten" prospekt.
        + "TOZSAMOSC: potwierdz, ze badany podmiot to TEN podmiot (zgodnosc domeny, miasta, kraju). "
          "Jesli pewnosci nie ma, napisz to wprost w pierwszym claimie zamiast zgadywac.")


# GOTCHA (docs/komponenty/researcher.md): payload.model_tier = NAZWA MODELU (haiku/sonnet/
# opus), nie poziom kaskady - 'medium'/'critical' bylyby zignorowane (router decydowalby sam).
_TIER_MODEL = {"low": "haiku", "medium": "sonnet", "critical": "opus"}


def _request_research(query, tier, correlation_id):
    body = {"query": query, "from": AGENT_ID, "correlation_id": str(correlation_id)}
    if tier:
        body["model_tier"] = _TIER_MODEL.get(tier, tier)
    try:
        r = httpx.post(config.RESEARCHER_URL + "/request", json=body,
                       headers={"X-Researcher-Secret": config.RESEARCHER_WEBHOOK_SECRET}, timeout=20)
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return r.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


def _prospect_research(inp):
    name = (inp.get("prospect") or "").strip()
    if not name:
        return "Podaj nazwe albo URL prospekta."
    url = (inp.get("url") or "").strip() or None
    if not url and re.match(r"^https?://", name, re.IGNORECASE):
        url, name = name, re.sub(r"^https?://(www\.)?", "", name).split("/")[0]
    # "/prospect <nazwa> <domena>" - ostatni token wygladajacy na adres to STRONA, nie czesc nazwy.
    # Bez tego doprecyzowanie tozsamosci przez Tomasza wchodzilo do nazwy firmy i nic nie dawalo.
    if not url:
        m = re.search(r"\s((?:https?://)?[\w-]+(?:\.[\w-]+)+(?:/\S*)?)$", name)
        if m:
            url, name = m.group(1), name[: m.start()].strip()
        elif re.fullmatch(r"(?:https?://)?[\w-]+(?:\.[\w-]+)+(?:/\S*)?", name):
            url = name
    # kanon kosztowy 20/07: default medium (~1-2 PLN); critical przez API zablokowany
    tier = inp.get("tier") or "medium"
    if tier == "critical":
        tier = "medium"
    row, created = _ensure_pipeline(name, url, source="research")
    # FIX 24/07: powtorne zlecenie (np. "/prospect La Cultura") nie mialo URL w wiadomosci, wiec
    # zapytanie szlo BEZ adresu i Researcher trafial w inny podmiot o podobnej nazwie. Dowod: job
    # 0602c6a7 - "Dance Company La Cultura" (Sosnowiec, lacultura.pl) zbadany jako Cultura Dance
    # Arts w Pawtucket RI. Adres z lejka jest twardym identyfikatorem - bierz go zawsze.
    url = url or (row.get("prospect_url") or None)
    if url and not row.get("prospect_url"):
        db.execute("UPDATE sales_pipeline SET prospect_url=%s, updated_at=NOW() WHERE id=%s",
                   (url, row["id"]))
    hint = None if url else _identity_hint(row)  # bez domeny jedziemy na miescie i kontakcie
    # Wizytowka PRZED zleceniem researchu: wlasna strona prospekta to pierwsze zrodlo prawdy,
    # a kaskada zrodel potrafi jej nie otworzyc (dowod: job 7411d0ba - z domeny klubu weszly
    # same tytuly, telefon ze strony glownej nie trafil do dowodow wcale).
    wiz = wizytowka(url) if url else {}
    osoba_txt = _zapisz_osobe_ze_strony(row["id"], wiz.get("tekst") or "") if wiz.get("tekst") else None
    if wiz.get("tel") or wiz.get("mail"):
        _zapisz_kontakt(row["id"], mail=wiz.get("mail"), tel=wiz.get("tel"), ze_strony=True)
        _append_notes(row["id"], "wizytowka ze strony: " + ", ".join(
            x for x in [f"tel {wiz.get('tel')}" if wiz.get("tel") else "",
                        f"mail {wiz.get('mail')}" if wiz.get("mail") else "",
                        f"podstron {len(wiz.get('strony') or [])}",
                        osoba_txt or ""] if x))
    code, resp = _request_research(_research_query(name, url, hint, wiz.get("tekst")), tier, row["id"])
    job_id = (resp or {}).get("job_id")
    if code == 202 and job_id:
        db.execute("UPDATE sales_pipeline SET research_job_id=%s, updated_at=NOW() WHERE id=%s",
                   (str(job_id), row["id"]))
        _append_notes(row["id"], f"research zlecony (tier {tier}, job {str(job_id)[:8]})")
        eta = "kilka minut, ~1-2 PLN"
        # REGULA PRAWDY: nieudane otwarcie strony ma byc WIDOCZNE w paragonie, nie domyslane
        # z pustego wyniku (dowod 24/07: gola domena bez DNS = cicha pustka przez pol godziny).
        if url and not (wiz or {}).get("tekst"):
            eta += "; ⚠️ NIE udalo sie otworzyc strony prospekta - research bez niej"
        elif (wiz or {}).get("tel") or (wiz or {}).get("mail"):
            eta += (f"; ze strony: {wiz.get('tel') or 'brak tel'} / "
                    f"{wiz.get('mail') or 'brak maila'} (zapisane w lejku)")
        return (f"🔍 Research zlecony: {name} (tier {tier}, {eta}). "
                f"{'Nowy wpis w lejku. ' if created else ''}Wynik przyjdzie na Telegram "
                f"i doklei sie do lejka - NIE czekaj w tej rozmowie.")
    return (f"❌ Researcher nie przyjal zlecenia (HTTP {code}: "
            f"{json.dumps(resp, ensure_ascii=False)[:200]}). Prospekt "
            f"{'dodany do lejka' if created else 'jest w lejku'} - sprobuj pozniej.")


def _prospect_results(inp):
    row = _find_pipeline(inp.get("prospect_fragment"))
    if not row:
        return f"Nie znajduje w lejku prospekta \"{(inp.get('prospect_fragment') or '')[:60]}\"."
    if not row.get("research_job_id"):
        return (f"{row['prospect_name']}: brak researchu (zlec prospect_research). "
                f"Notatki:\n{(row.get('notes') or '(brak)')[:800]}")
    status = research.job_status(row["research_job_id"])
    grounding = research.grounding_with_sources(row["research_job_id"], limit=12)
    head = f"🔎 {row['prospect_name']} [research job {str(row['research_job_id'])[:8]}, status: {status or '?'}]"
    if not grounding:
        return head + "\nJob bez claims (jeszcze sie liczy albo padl) - sprawdz za chwile."
    return head + "\n" + grounding + f"\n\nNOTATKI LEJKA:\n{(row.get('notes') or '(brak)')[:600]}"


# ---------------- outreach (gotowiec HITL) ----------------
_ENG_CHANNEL = {"email": "Other", "linkedin_dm": "LinkedIn", "x_dm": "X"}

# Prog trafnosci bazy wiedzy dla tekstow do klienta. Kalibracja 24/07 z zywego korpusu:
# materialy o Adamietzu wracaly na zapytanie o szkole tanca z podobienstwem 0.40-0.45.
_KNOWLEDGE_MIN_SIM = 0.55
_VOICE_MAX = 30000  # gorna granica wsadu glosu w znakach (~8 tys. tokenow, kilka groszy na gotowiec)


def _voice_dna_core():
    """Osobisty rdzen glosu Tomasza (destylat 20 wywiadow, brand_config.voice_dna_core, ~4,5 tys.
    znakow). Do 24/07 sciezka sprzedazowa NIE czytala go w ogole - brala tylko voice_bible."""
    try:
        r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id=%s "
                        "AND config_key='voice_dna_core' LIMIT 1", (BRAND,))
        return (r or {}).get("config_value") or ""
    except Exception:
        traceback.print_exc()
        return ""


def _voice_for_outreach(brand):
    """Glos do tekstow sprzedazowych: CALY voice_dna_core (osobisty rdzen z 20 wywiadow) + CALA
    voice_bible. Wczesniej szlo `voice_bible[:2000]` z 22 168 znakow, czyli naglowek pliku i
    pozycjonowanie - zasad pisania model nie widzial NIGDY (dowod: gotowiec StandART 24/07).

    Probowalem wybierac sekcje po slowach kluczowych i sonda to obalila: z 37 naglowkow zywej
    Voice Bible dopasowaly sie dwa, a listy zakazanego slownictwa (4.1-4.5) i regula em-dash
    maja naglowki po angielsku, wiec wypadlyby. To ta sama klasa bledu co pierwotna: ciche
    gubienie zasad. Wsad kosztuje kilka groszy na gotowiec i jest tego wart - to tekst do
    klienta, nie log."""
    parts = []
    rdzen = _voice_dna_core()
    if rdzen:
        parts.append("RDZEN GLOSU TOMASZA (voice_dna_core):\n" + rdzen)
    bible = ((brand or {}).get("voice_bible") or "").strip()
    if bible:
        parts.append("VOICE BIBLE:\n" + bible)
    return "\n\n".join(parts)[:_VOICE_MAX]


_WIZYTOWKA_PODSTRONY = re.compile(r"kontakt|contact|cennik|zapisy|grafik|instruktor|o-nas|about",
                                  re.IGNORECASE)


_URL_W_TEKSCIE = re.compile(r"https?://[^\s\)\]\|,>\"']+", re.IGNORECASE)
# Adresy, ktore NIE sa strona prospekta: przekierowania wyszukiwarek, agregatory, nauka.
_URL_SMIECI = re.compile(r"vertexaisearch|googleusercontent|google\.com/url|arxiv\.org|"
                         r"wikipedia|youtube\.com|pomagam\.pl|aleo\.com|panoramafirm|targeo|"
                         r"rejestr\.io|krs-online|linkedin\.com/pulse", re.IGNORECASE)
_URL_SOCIAL = re.compile(r"facebook\.com|instagram\.com|linkedin\.com|tiktok\.com", re.IGNORECASE)


def _znajdz_strone_w_researchu(prospect_name, tekst):
    """Wylow adres STRONY PROSPEKTA z wynikow researchu.

    Powod (dowod 24/07, Stepownia): research SAM podal w sekcji HAK adres
    https://stepownia.pl/wroclawska_stepownia/ i profil FB, po czym orzekl "tozsamosc
    niepotwierdzona, podaj strone" - poprosil Tomasza o rzecz, ktora mial przed nosem.
    Agent ma wejsc na to, co znalazl, a nie odsylac czlowieka po dane.

    Kolejnosc: adres zawierajacy slowo z nazwy prospekta -> dowolny niesmieciowy -> profil
    spolecznosciowy (ostatecznosc, lepszy niz nic).

    POPRAWKA 24/07 (dowod: Stepownia dostala w lejku https://stepownia.pl/author/dudzikdariusz):
    dopasowanie po nazwie lapalo TAKZE strony-smieci tego samego serwisu (archiwum autora,
    tag, kategoria, koszyk). Adres prospekta ma prowadzic do FIRMY, nie do archiwum wpisow
    jednego czlowieka. Teraz: sciezki-smieci sa obcinane do korzenia domeny, a przy remisie
    wygrywa adres KROTSZY (korzen bije podstrone). Sensowna podstrona zostaje - jesli klub
    zyje pod https://stepownia.pl/wroclawska_stepownia/, to jest jego wizytowka."""
    slowa = [w.lower() for w in re.split(r"\W+", prospect_name or "") if len(w) > 4]
    zwykle, social = [], []
    for u in _URL_W_TEKSCIE.findall(tekst or ""):
        # jeden adres = jeden zapis: bez koncowego ukosnika, zeby 'stepownia.pl/' i
        # 'stepownia.pl' nie konkurowaly ze soba jako dwa rozne kandydaty
        u = u.rstrip(".,);]").rstrip("/")
        if _URL_SMIECI.search(u):
            continue
        if _URL_SCIEZKA_SMIECI.search(u + "/"):
            u = _korzen_url(u)          # archiwum/tag/koszyk -> zostaje sama domena
            if not u:
                continue
        (social if _URL_SOCIAL.search(u) else zwykle).append(u)
    zwykle = list(dict.fromkeys(zwykle))
    trafione = [u for u in zwykle if any(s in u.lower() for s in slowa)]
    if trafione:
        # korzen przed podstrona: najkrotszy adres, ktory dalej niesie nazwe prospekta
        return sorted(trafione, key=len)[0]
    return (zwykle or social or [None])[0]


# Sciezki, ktore NIE sa strona firmy, choc leza na jej domenie (archiwa, systemowe, zakupowe).
_URL_SCIEZKA_SMIECI = re.compile(
    r"/(author|tag|tags|category|kategoria|feed|rss|search|szukaj|login|logowanie|koszyk|cart|"
    r"checkout|polityka|privacy|regulamin|cookies?|page/\d+|wp-(content|json|admin|includes))\b"
    # rozszerzenie pliku sprawdzamy z wyprzedzeniem, bo wolajacy dokleja '/' do adresu
    r"|\.(pdf|jpe?g|png|gif|webp|svg|docx?|xlsx?)(?=/|$)", re.IGNORECASE)


def _korzen_url(u):
    """'https://stepownia.pl/author/x?y=1' -> 'https://stepownia.pl'. Brak hosta = None."""
    m = re.match(r"(https?://[^/\s?#]+)", (u or "").strip(), re.IGNORECASE)
    return m.group(1) if m else None


def _kandydaci_url(adres):
    """Warianty adresu do sprobowania. Powod (dowod 24/07): w lejku mamy
    'klubsportowystandart.org', a ta GOLA domena nie ma wpisu DNS - odpowiada tylko
    'www.klubsportowystandart.org'. Jeden wariant = 'No address associated with hostname'
    i cicha pustka. Firmy zapisuja adres raz z www, raz bez, wiec probujemy oba, a takze
    http, gdy https nie wstaje (male strony bywaja bez certyfikatu)."""
    a = (adres or "").strip().rstrip("/")
    if a.lower().startswith("http"):
        return [a]
    host = a.lstrip("/")
    bez_www = host[4:] if host.lower().startswith("www.") else host
    warianty = [f"https://www.{bez_www}", f"https://{bez_www}",
                f"http://www.{bez_www}", f"http://{bez_www}"]
    if host.lower().startswith("www."):  # zapisany z www - jego wariant probujemy pierwszy
        warianty.insert(0, f"https://{host}")
    return list(dict.fromkeys(warianty))
_TAGI_RE = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>|<[^>]+>")


def wizytowka(url, max_podstron=3, limit_znakow=6000):
    """Wejscie na STRONE PROSPEKTA i zdjecie z niej tekstu - deterministycznie, bez modelu.

    Powod (24/07, zgloszenie Tomasza): research prospekta orzekl "brak danych kontaktowych",
    a numer telefonu stoi na stronie glownej. Sonda jobu 7411d0ba pokazala dlaczego: web_search
    zwrocil z domeny klubu SAME TYTULY (22-52 znaki), a adapter firecrawl przyniosl osiem
    linkow z arXiv o prospectingu AI i ani jednej strony klubu. Synteza byla uczciwa, pobieranie
    bylo puste. Pierwsze zrodlo prawdy o firmie to jej wlasna strona, wiec bierzemy ja sami.

    Zwraca {'tekst', 'mail', 'tel', 'strony'}; kazdy blad = pusty wynik, nigdy wyjatek w gore."""
    out = {"tekst": "", "mail": None, "tel": None, "strony": []}
    adres = (url or "").strip()
    if not adres:
        return out
    naglowki = {"User-Agent": "Mozilla/5.0 (compatible; AGS-SalesAgent/1.0)"}
    kawalki = []
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=naglowki) as klient:
            r, html = None, ""
            for kandydat in _kandydaci_url(adres):
                try:
                    rr = klient.get(kandydat)
                    rr.raise_for_status()
                    r, html = rr, rr.text
                    break
                except Exception:
                    continue
            if r is None:
                print(f"[sales] wizytowka: zaden wariant adresu nie odpowiedzial ({adres})", flush=True)
                return out
            out["strony"].append(str(r.url))
            kawalki.append(_TAGI_RE.sub(" ", html))
            # podstrony, ktore u malych firm niosa kontakt i oferte (kontakt, cennik, grafik...)
            linki, widziane = [], {str(r.url).rstrip("/")}
            for m in re.finditer(r'href=["\']([^"\'#]+)["\']', html, re.IGNORECASE):
                href = m.group(1)
                if not _WIZYTOWKA_PODSTRONY.search(href):
                    continue
                pelny = href if href.lower().startswith("http") else str(r.url).rstrip("/") + "/" + href.lstrip("/")
                if pelny.rstrip("/") in widziane:
                    continue
                widziane.add(pelny.rstrip("/"))
                linki.append(pelny)
                if len(linki) >= max_podstron:
                    break
            for link in linki:
                try:
                    rr = klient.get(link)
                    if rr.status_code == 200:
                        out["strony"].append(link)
                        kawalki.append(_TAGI_RE.sub(" ", rr.text))
                except Exception:
                    continue
    except Exception:
        traceback.print_exc()
        return out
    tekst = re.sub(r"\s+", " ", " ".join(kawalki)).strip()
    out["tekst"] = tekst[:limit_znakow]
    m, t = _EMAIL_RE.search(tekst), _PHONE_RE.search(tekst)
    out["mail"] = m.group(0) if m else None
    out["tel"] = t.group(0).strip() if t else None
    return out


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# telefon PL: opcjonalny +48, potem 9 cyfr w typowym grupowaniu. NIP-y (10 cyfr) i daty odpadaja.
_PHONE_RE = re.compile(r"(?<![\d-])(?:\+48[\s-]?)?(?:\d{3}[\s-]?\d{3}[\s-]?\d{3})(?![\d-])")


# ---- Osoba decyzyjna ze strony prospekta (24/07, dlug techniczny C2) --------------------
# Ze strony klubu dalo sie juz zdjac podstrone instruktorow, ale INSTRUKTOR TO NIE DECYDENT.
# Wpisanie przypadkowego trenera w 'contact_person' byloby gorsze niz puste pole: gotowiec
# zaczynalby sie od zwrotu do osoby, ktora nie decyduje o zakupie, a Tomasz nie mialby jak
# tego zauwazyc. Dlatego rola musi byc JAWNIE decyzyjna, inaczej nazwisko idzie tylko
# do notatek jako kontakt pomocniczy.
# UWAGA NA FLAGI (blad zlapany wlasnym testem 24/07): nazwisko poznajemy PO WIELKIEJ LITERZE,
# wiec wzorzec osoby MUSI byc wrazliwy na wielkosc liter. Globalne re.IGNORECASE kasowalo to
# rozroznienie i lapalo "Anna Kowalska prowadzi" jako imie i nazwisko. Role sa nieczule na
# wielkosc liter LOKALNIE, przez (?i:...).
_ROLE_DECYZYJNE = (r"wlascic\w*|właścic\w*|wspolwlascic\w*|współwłaścic\w*|prezes\w*|dyrektor\w*|"
                   r"kierowni\w*|zarzad\w*|zarząd\w*|co-?founder|founder|owner|ceo|szef\w*")
_ROLE_POMOCNICZE = r"instruktor\w*|trener\w*|nauczyciel\w*|prowadz\w*|choreograf\w*|recepcj\w*"
_IMIE_NAZWISKO = r"[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż-]{2,}){1,2}"
_OSOBA_PRZY_ROLI = re.compile(
    rf"(?:(?P<rola1>(?i:{_ROLE_DECYZYJNE}|{_ROLE_POMOCNICZE}))[\s:,\-]+(?P<osoba1>{_IMIE_NAZWISKO})"
    rf"|(?P<osoba2>{_IMIE_NAZWISKO})[\s,\-]+(?:to\s+)?(?P<rola2>(?i:{_ROLE_DECYZYJNE}|{_ROLE_POMOCNICZE})))")
_ROLA_DECYZYJNA_RE = re.compile(_ROLE_DECYZYJNE, re.IGNORECASE)


def osoba_decyzyjna(tekst):
    """Kto decyduje po stronie prospekta, wg TEGO CO STOI NA STRONIE (zero modelu).

    Zwraca {'osoba', 'rola', 'decyzyjna': bool} albo None. decyzyjna=True TYLKO gdy rola
    jest jawnie wlascicielska/zarzadcza. Instruktor, trener, recepcja = kontakt pomocniczy:
    nazwisko warto miec, ale nie wolno go podac jako osoby decyzyjnej."""
    najlepszy = None
    for m in _OSOBA_PRZY_ROLI.finditer(tekst or ""):
        rola = (m.group("rola1") or m.group("rola2") or "").strip()
        osoba = (m.group("osoba1") or m.group("osoba2") or "").strip()
        if not (rola and osoba):
            continue
        decyzyjna = bool(_ROLA_DECYZYJNA_RE.fullmatch(rola))
        kandydat = {"osoba": osoba[:120], "rola": rola.lower()[:40], "decyzyjna": decyzyjna}
        if decyzyjna:                      # pierwsza roli decyzyjna wygrywa i konczy szukanie
            return kandydat
        najlepszy = najlepszy or kandydat  # pomocniczy zapamietujemy, ale szukamy dalej
    return najlepszy


def _zapisz_osobe_ze_strony(row_id, tekst):
    """Zapisz osobe decyzyjna do kolumny lejka; osobe pomocnicza tylko do notatek.
    Zwraca krotki opis do paragonu albo None (REGULA PRAWDY: milczymy tylko, gdy nic nie ma)."""
    kand = osoba_decyzyjna(tekst)
    if not kand:
        return None
    if kand["decyzyjna"]:
        _zapisz_kontakt(row_id, osoba=f"{kand['osoba']} ({kand['rola']})")
        return f"osoba decyzyjna ze strony: {kand['osoba']} ({kand['rola']})"
    _append_notes(row_id, f"kontakt pomocniczy ze strony: {kand['osoba']} ({kand['rola']}) - "
                          f"NIE potwierdzone, ze decyduje o zakupie")
    return f"kontakt pomocniczy: {kand['osoba']} ({kand['rola']}), decydent nieustalony"


def _zapisz_kontakt(row_id, mail=None, tel=None, osoba=None, ze_strony=False):
    """Dane kontaktowe do KOLUMN lejka (DDL 029), nie tylko do prozy w notatkach.

    Zgloszenie Tomasza 24/07: "research ma tez automatycznie uzupelniac baze danych bo od tego
    jest". Zasada: nadpisujemy TYLKO PUSTE pola (COALESCE) - dane wpisane recznie przez Tomasza
    sa nietykalne, automat je uzupelnia, nigdy nie poprawia."""
    try:
        db.execute(
            """UPDATE sales_pipeline
               SET contact_email = COALESCE(NULLIF(contact_email,''), %s),
                   contact_phone = COALESCE(NULLIF(contact_phone,''), %s),
                   contact_person = COALESCE(NULLIF(contact_person,''), %s),
                   site_checked_at = CASE WHEN %s THEN NOW() ELSE site_checked_at END,
                   updated_at = NOW()
               WHERE id=%s""",
            (mail or None, tel or None, osoba or None, bool(ze_strony), row_id))
    except Exception:
        traceback.print_exc()


def _kontakt_prospekta(row, wiz=None):
    """Dane do naglowka gotowca: kto i pod jakim adresem. Zrodla po kolei: kartoteka CRM
    (contacts), notatki lejka, claims z researchu. Deterministycznie, bez LLM - to ma byc
    dowod do zrewidowania w dwie sekundy, nie kolejna generacja.

    Czego NIE MA, mowimy wprost: research StandART 24/07 nie znalazl osoby decyzyjnej ani
    telefonu, wiec naglowek musi to pokazac zamiast udawac komplet."""
    # Kolejnosc zrodel: swieza wizytowka ze strony -> KOLUMNY lejka (DDL 029) -> kartoteka
    # -> notatki i claims. Kolumny sa tu wyzej niz proza, bo to one sa zrodlem dla innych
    # konsumentow (widok lejka, dziennik klienta).
    osoba = row.get("contact_person")
    mail = (wiz or {}).get("mail") or row.get("contact_email")
    tel = (wiz or {}).get("tel") or row.get("contact_phone")
    if row.get("contact_id"):
        try:
            # AP-304 (moj blad z 24/07, wykryty sonda): kluczem contacts jest `id`, NIE
            # `contact_id` - zapytanie lecialo wyjatkiem, wyjatek byl lapany, wiec osoba
            # decyzyjna ZAWSZE wychodzila "nieustalona". Kolumny sprawdzamy PRZED, nie po.
            c = db.fetchone("SELECT COALESCE(full_name, name) AS name FROM contacts WHERE id=%s",
                            (row["contact_id"],))
            osoba = (c or {}).get("name")
        except Exception:
            traceback.print_exc()
    zrodla = [row.get("notes") or ""]
    if row.get("research_job_id"):
        try:
            for c in db.fetchall("SELECT claim_text FROM claims WHERE job_id=%s LIMIT 20",
                                 (row["research_job_id"],)):
                zrodla.append(c.get("claim_text") or "")
        except Exception:
            traceback.print_exc()
    for tekst in zrodla:
        if not mail:
            m = _EMAIL_RE.search(tekst)
            mail = m.group(0) if m else None
        if not tel:
            t = _PHONE_RE.search(tekst)
            tel = t.group(0).strip() if t else None
    return osoba, mail, tel


# Paczka Managera 24/07 pkt 3: slownictwo, ktore opisuje NASZ swiat zamiast problemu klienta.
# Odmiany po polsku lapiemy rdzeniem (automatyzacj*, integracj*), angielskie doslownie.
_ZAKAZANE_PRODUKTOWE = [
    "automatyzacj", "workflow", "system ai", "systemy ai", "systemem ai", "integracj",
    "ai system", "ai workflow", "agents platform", "custom ai",
]


def _zakazane_slownictwo(tekst):
    """Zwraca liste zakazanych zwrotow produktowych znalezionych w tekscie do klienta."""
    low = (tekst or "").lower()
    return sorted({w for w in _ZAKAZANE_PRODUKTOWE if w in low})


def _tylko_gotowiec(tekst, channel):
    """Odcina komentarz modelu sprzed tresci. Instrukcja "zwroc wylacznie tresc" nie wystarczyla:
    model poprzedzil mail wlasnym rozumowaniem o konflikcie RDC i haku (dowod: wklejka 24/07
    14:03). Czysta wklejka ma byc czysta, wiec tniemy deterministycznie:
    1) po znaczniku ---GOTOWIEC--- (kontrakt formatu w prompcie),
    2) awaryjnie dla maila: od linii TEMAT:,
    3) gdy nie ma ani jednego, zostawiamy caly tekst (lepiej za duzo niz pusto)."""
    t = (tekst or "").strip()
    m = re.search(r"^-{2,}\s*GOTOWIEC\s*-{2,}\s*$", t, re.MULTILINE | re.IGNORECASE)
    if m:
        return t[m.end():].strip()
    if channel == "email":
        m = re.search(r"^TEMAT:", t, re.MULTILINE)
        if m and m.start() > 0:
            return t[m.start():].strip()
    return t


def _outreach_naglowek(row, channel, ostrzezenie="", wiz=None):
    """Naglowek gotowca: do kogo to leci i czym to zweryfikowac."""
    osoba, mail, tel = _kontakt_prospekta(row, wiz)
    linie = [f"🧾 OUTREACH DO WYSLANIA RECZNIE - {channel} - {row['prospect_name'][:80]}",
             f"👤 Osoba decyzyjna: {osoba or '(nieustalona - research jej nie znalazl)'}",
             f"✉️ Mail: {mail or '(brak w danych)'}    ☎️ Telefon: {tel or '(brak w danych)'}"]
    if row.get("prospect_url"):
        linie.append(f"🔗 {row['prospect_url']}")
    if ostrzezenie:
        linie.append(ostrzezenie.rstrip())
    linie.append("(ponizej czysta wklejka; NIC nie wysyla sie samo)")
    return "\n".join(linie)


def _outreach_stopka(row):
    """Stopka gotowca: gdzie jestesmy w lejku i ktory to kontakt. Liczba wczesniejszych
    gotowcow idzie z engagement_log, nie z pamieci modelu."""
    try:
        r = db.fetchone(
            """SELECT COUNT(*) AS wszystkie,
                      COUNT(*) FILTER (WHERE status='sent') AS wyslane
               FROM engagement_log
               WHERE agent='AGS:sprzedaz' AND content ILIKE %s""",
            (f"%{(row.get('prospect_name') or '')[:60]}%",))
    except Exception:
        traceback.print_exc()
        r = None
    # Liczy sie WYSYLKA, nie liczba gotowcow. Pierwsza wersja mowila "kolejny kontakt
    # (0 wyslanych wczesniej)" - zdanie, ktore przeczy samo sobie (dowod: stopka 24/07 14:03).
    gotowce = int((r or {}).get("wszystkie") or 0)
    wyslane = int((r or {}).get("wyslane") or 0)
    if wyslane:
        ktory = f"kolejny kontakt ({wyslane} wyslanych wczesniej)"
    else:
        ktory = "PIERWSZY kontakt" + (f" (gotowcow w kolejce: {gotowce}, zaden nie oznaczony "
                                      f"jako wyslany)" if gotowce > 1 else "")
    nast = row.get("next_followup_at")
    return ("📊 Lejek: etap " + str(row.get("stage") or "?") + " | " + ktory
            + (" | follow-up: " + nast.astimezone(WARSAW).strftime("%d/%m %H:%M") if nast else "")
            + "\n⏭ Po wyslaniu napisz \"wyslalem\" - przesune etap i ustawie nastepny kontakt.")


def _outreach_examples(limit=3):
    """Wiadomosci, ktore Tomasz NAPRAWDE wyslal (material_type='outreach_example', wrzucane przez
    /add_sales_material z podpowiedzia 'wzorzec'). Model pisze OD NICH, nie od teorii - to jest
    roznica miedzy tekstem poprawnym a tekstem Tomasza."""
    try:
        rows = db.fetchall(
            """SELECT material_name, content_excerpt FROM sales_knowledge
               WHERE brand_id='AGS' AND material_type='outreach_example'
               ORDER BY added_at DESC LIMIT %s""", (limit,))
    except Exception:
        traceback.print_exc()
        return ""
    return "\n\n".join(
        f"--- wzorzec: {(r['material_name'] or '')[:60]} ---\n{(r['content_excerpt'] or '')[:1200]}"
        for r in rows or [])


def _draft_outreach(inp, chat_id):
    row = _find_pipeline(inp.get("prospect_fragment"))
    if not row:
        return (f"Nie znajduje w lejku prospekta \"{(inp.get('prospect_fragment') or '')[:60]}\" "
                f"- najpierw pipeline_add albo prospect_research.")
    channel = inp.get("channel") or "email"
    lang = inp.get("language") or "pl"
    brand = load_brand(BRAND)
    grounding = research.grounding_with_sources(row["research_job_id"], limit=10) \
        if row.get("research_job_id") else ""
    knowledge = _knowledge_search_text(f"outreach {row['prospect_name']} {inp.get('guidance') or ''}",
                                       top_n=3, quiet=True, min_similarity=_KNOWLEDGE_MIN_SIM)
    wzorce = _outreach_examples()
    # Strona prospekta jako zrodlo cytowalnych faktow do haka (i danych do naglowka).
    wiz = wizytowka(row.get("prospect_url")) if row.get("prospect_url") else {}
    if wiz.get("tekst"):
        _zapisz_osobe_ze_strony(row["id"], wiz["tekst"])  # decydent do kolumny, instruktor do notatek
    if wiz.get("mail") or wiz.get("tel"):  # swieze dane ze strony ida takze do bazy
        _zapisz_kontakt(row["id"], mail=wiz.get("mail"), tel=wiz.get("tel"), ze_strony=True)
    forms = {
        "email": "email sprzedazowy: linia 'TEMAT: ...' i po pustej linii tresc",
        "linkedin_dm": "wiadomosc LinkedIn (jesli to pierwszy kontakt: TAKZE zaproszenie <300 znakow bez pitchu, oznacz 'ZAPROSZENIE:' i 'WIADOMOSC PO AKCEPCIE:')",
        "x_dm": "DM na X, zwiezly, peer-to-peer",
    }
    model, tier, source = tasks.model_for("sales_outreach")
    resp = client().messages.create(
        model=model, max_tokens=1200, thinking={"type": "disabled"},
        system=[{"type": "text", "text":
                 f"Piszesz outreach w imieniu Tomasza Nawrockiego (AGS).\n{_RULES}\n\n"
                 f"{_FRAMEWORKS}\n\n{_ANTY_SZABLON}\n\n{_voice_for_outreach(brand)}"
                 + (f"\n\nTAK PISZE TOMASZ - wzorce z wiadomosci, ktore NAPRAWDE wyslal. Rytm, "
                    f"dlugosc zdan i sposob wchodzenia w temat bierz STAD, nie z teorii:\n{wzorce}"
                    if wzorce else "")}],
        messages=[{"role": "user", "content":
                   f"Napisz {forms.get(channel, channel)} po "
                   f"{'polsku' if lang == 'pl' else 'angielsku'} do prospekta: "
                   f"{row['prospect_name']}" + (f" ({row['prospect_url']})" if row.get("prospect_url") else "") + ".\n"
                   + (f"WSKAZOWKI TOMASZA: {inp['guidance']}\n" if inp.get("guidance") else "")
                   + (f"\nSTRONA PROSPEKTA (tekst zdjety bezposrednio - fakty PEWNE, hak bierz "
                      f"stad w pierwszej kolejnosci):\n{wiz['tekst'][:2500]}\n" if wiz.get("tekst") else "")
                   + (f"\nRESEARCH (fakty z linkami - hak personalizacji STAD):\n{grounding[:3000]}\n"
                      if grounding else "\nBRAK researchu - personalizuj tylko tym, co pewne z nazwy/kontekstu; ZERO zmyslonych faktow.\n")
                   + (f"\nTECHNIKI Z BAZY WIEDZY (trafne dla tego przypadku):\n{knowledge[:1500]}\n"
                      if knowledge else "\nBAZA WIEDZY: brak materialu trafnego dla tego prospekta. "
                                        "Pisz z frameworkow i researchu; NIE nadrabiaj ogolnikami.\n")
                   + f"\nNOTATKI LEJKA: {(row.get('notes') or '')[:600]}\n\n"
                   "Zanim napiszesz: wybierz JEDEN konkret z researchu, ktory bedzie hakiem, i "
                   "sprawdz, czy da sie go zacytowac. To rozumowanie zostaw dla siebie.\n"
                   "FORMAT ODPOWIEDZI: pierwsza linia to doslownie ---GOTOWIEC---, a pod nia "
                   "WYLACZNIE tresc do wyslania (zero komentarza, zero uzasadnien, zero markdown). "
                   "Nic przed ta linia."}])
    tasks.log_task("sales_outreach", tier, model, source, getattr(resp, "usage", None))
    draft = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    if not draft:
        return "Nie wyszlo - sprobuj jeszcze raz (model nie zwrocil tresci)."
    draft = compliance.fix_dashes(draft)  # RULE 1 kanonu marki dziala TAKZE na tekstach do klienta
    draft = _tylko_gotowiec(draft, channel)
    # AUTO-ODRZUT slownictwa produktowego (paczka Managera 24/07 pkt 3). Sama instrukcja w
    # prompcie nie wystarcza - dzis model dwa razy zignorowal zakaz (fraza "15 minut", komentarz
    # przed wklejka). Wiec: wykryj, popros o JEDNA poprawke, a gdy dalej jest - powiedz wprost.
    zakazane = _zakazane_slownictwo(draft)
    if zakazane:
        try:
            resp2 = client().messages.create(
                model=model, max_tokens=1200, thinking={"type": "disabled"},
                messages=[{"role": "user", "content":
                           f"Ponizszy tekst do klienta uzywa slownictwa, ktore opisuje NASZ swiat "
                           f"zamiast jego problemu: {', '.join(zakazane)}. Przepisz go tak, by "
                           f"znaczyl to samo, ale mowil REZULTATEM (co klient przestanie tracic, "
                           f"co zacznie sie dziac samo). Nie dodawaj oferty ani prosby o rozmowe. "
                           f"Zwroc WYLACZNIE poprawiony tekst.\n\n{draft}"}])
            poprawka = "".join(b.text for b in resp2.content if getattr(b, "type", "") == "text").strip()
            tasks.log_task("sales_outreach", tier, model, source, getattr(resp2, "usage", None))
            if poprawka:
                draft = _tylko_gotowiec(compliance.fix_dashes(poprawka), channel)
                zakazane = _zakazane_slownictwo(draft)
        except Exception:
            traceback.print_exc()
    # CZYSTA POLSZCZYZNA (sugestia Tomasza 24/07: "wszelkie zangielszczenia nie powinny miec tu
    # miejsca"). Filtr istnieje od 06/07, ale sciezka sprzedazowa nigdy przez niego nie szla -
    # ta sama luka co z em dash. Tekst do polskiego klienta ma brzmiec po polsku.
    if lang == "pl":
        try:
            draft = _tylko_gotowiec(compliance.polish_pl(draft), channel)
        except Exception:
            traceback.print_exc()
    # gotowiec: naglowek + CZYSTA WKLEJKA osobna wiadomoscia (kanon comment-radar)
    # Bramka tozsamosci: marker z podsumowania researchu zyje w notatkach lejka. Nie blokujemy
    # pisania (decyduje Tomasz), ale gotowiec ma jechac z ostrzezeniem, nie po cichu.
    # Liczy sie OSTATNI marker - po ponownym researchu ze strona werdykt sie zmienia.
    # Skan po WERDYKCIE kodu, nie po slowie "TOZSAMOSC" - to drugie pisze tez model w pierwszej
    # linii podsumowania (dowod 24/07 11:18: ostatnim trafieniem byl tekst modelu, nie werdykt).
    _markery = re.findall(r"\[WERDYKT TOZSAMOSCI:\s*(potwierdzona|z zastrzezeniem|niepotwierdzona)\]",
                          row.get("notes") or "", re.IGNORECASE)
    _stan = _markery[-1].lower() if _markery else ""
    _ostrzezenie = ("⛔ RESEARCH NIE POTWIERDZIL TOZSAMOSCI TEJ FIRMY - zweryfikuj adresata PRZED "
                    "wyslaniem.\n" if _stan == "niepotwierdzona"
                    else "⚠️ Podmiot potwierdzony dowodami, ale research zglosil zastrzezenie - "
                         "sprawdz je przed wyslaniem.\n" if _stan == "z zastrzezeniem" else "")
    # Auto-odrzut nie zawsze domyka sprawe za pierwszym razem - wtedy Tomasz ma to WIDZIEC.
    if zakazane:
        _ostrzezenie += (f"⚠️ SLOWNICTWO PRODUKTOWE mimo poprawki: {', '.join(zakazane)} - "
                         f"przeczytaj te fragmenty przed wyslaniem.\n")
    _tg_send(chat_id, _outreach_naglowek(row, channel, _ostrzezenie, wiz))
    _tg_send(chat_id, draft)
    _tg_send(chat_id, _outreach_stopka(row))
    try:
        db.execute(
            """INSERT INTO engagement_log (action_type, channel, agent, content, response, notes,
                                           contact_id, status, author_display)
               VALUES ('other',%s,'AGS:sprzedaz',%s,%s,%s,%s,'proposed',%s)""",
            (_ENG_CHANNEL.get(channel, "Other"), f"outreach {channel}: {row['prospect_name'][:200]}",
             draft[:3000], "gotowiec outreach (Agent Sprzedazy, HITL)",
             row.get("contact_id"), row["prospect_name"][:200]))
    except Exception:
        traceback.print_exc()
    _append_notes(row["id"], f"outreach draft ({channel}, {lang}) - gotowiec u Tomasza")
    return (f"Gotowiec {channel} dla {row['prospect_name']} wyslany Tomaszowi osobna wiadomoscia "
            f"(zapisany w engagement_log i notatkach lejka). Poczatek: {draft[:150]}")


def _offer_for(inp):
    row = _find_pipeline(inp.get("prospect_fragment"))
    if not row:
        return f"Nie znajduje w lejku prospekta \"{(inp.get('prospect_fragment') or '')[:60]}\"."
    grounding = research.grounding_with_sources(row["research_job_id"], limit=8) \
        if row.get("research_job_id") else "(brak researchu)"
    return (f"DANE DO DOPASOWANIA OFERTY dla {row['prospect_name']}:\n"
            f"LEJEK: stage {row['stage']}, oferta dotychczas: {row.get('offer_tier') or 'brak'}, "
            f"notatki: {(row.get('notes') or '(brak)')[:500]}\n\n"
            f"RESEARCH:\n{grounding[:2500]}\n\nCENNIK:\n{_pricing_text()}\n\n"
            f"Teraz zarekomenduj Tomaszowi tier OD GORY (premium pierwsze, nizej tylko na jawny "
            f"sygnal), uzasadnij WARTOSCIA (problem -> wartosc -> mechanizm -> cena) i po "
            f"akceptacji zapisz przez pipeline_move (offer_tier).")


# ---------------- lejek ----------------
def _pipeline_add(inp):
    name = (inp.get("prospect_name") or "").strip()
    if not name:
        return "Podaj nazwe prospekta."
    if _find_pipeline(name):
        return f"\"{name[:60]}\" juz jest w lejku - uzyj pipeline_move."
    stage = inp.get("stage") if inp.get("stage") in _STAGES else "prospect"
    row = db.fetchone(
        """INSERT INTO sales_pipeline (brand_id, prospect_name, prospect_url, stage, value, currency, notes)
           VALUES ('AGS',%s,%s,%s,%s,%s,%s) RETURNING id""",
        (name[:200], inp.get("url"), stage, inp.get("value"),
         (inp.get("currency") or "PLN")[:10], (inp.get("note") or None)))
    return f"📊 Dodane do lejka: {name[:80]} [{stage}]" + \
           (f", {inp['value']:.0f} {inp.get('currency') or 'PLN'}" if inp.get("value") else "") + "."


def _pipeline_move(inp):
    row = _find_pipeline(inp.get("prospect_fragment"))
    if not row:
        return f"Nie znajduje w lejku prospekta \"{(inp.get('prospect_fragment') or '')[:60]}\"."
    sets, params, bits = [], [], []
    stage = inp.get("stage")
    if stage and stage in _STAGES and stage != row["stage"]:
        sets.append("stage=%s")
        params.append(stage)
        bits.append(f"{row['stage']} -> {stage}")
    if inp.get("offer_tier"):
        sets.append("offer_tier=%s")
        params.append(str(inp["offer_tier"])[:120])
        bits.append(f"oferta: {inp['offer_tier']}")
    if inp.get("value") is not None:
        sets.append("value=%s")
        params.append(inp["value"])
        bits.append(f"wartosc: {inp['value']:.0f} {inp.get('currency') or row.get('currency') or 'PLN'}")
    if inp.get("currency"):
        sets.append("currency=%s")
        params.append(str(inp["currency"])[:10])
    if inp.get("next_followup_at"):
        try:
            fu = datetime.datetime.fromisoformat(str(inp["next_followup_at"]))
            if fu.tzinfo is None:
                fu = fu.replace(tzinfo=WARSAW)
            sets.append("next_followup_at=%s")
            params.append(fu)
            bits.append(f"nastepny kontakt: {fu.astimezone(WARSAW).strftime('%d/%m %H:%M')}")
        except (ValueError, TypeError):
            return f"Nie rozumiem terminu \"{inp['next_followup_at']}\" - podaj ISO, np. 2026-07-23T10:00."
    if not sets and not inp.get("note"):
        return "Nic do zmiany - podaj stage / oferte / wartosc / follow-up / notatke."
    if sets:
        db.execute(f"UPDATE sales_pipeline SET {', '.join(sets)}, updated_at=NOW() WHERE id=%s",
                   (*params, row["id"]))
    if inp.get("note"):
        _append_notes(row["id"], str(inp["note"])[:500])
        bits.append("notatka zapisana")
    return f"📊 {row['prospect_name'][:70]}: " + "; ".join(bits) + "."


def _outreach_sent(inp):
    row = _find_pipeline(inp.get("prospect_fragment"))
    if not row:
        return f"Nie znajduje w lejku prospekta \"{(inp.get('prospect_fragment') or '')[:60]}\"."
    upd = db.fetchone(
        """UPDATE engagement_log SET status='sent'
           WHERE id = (SELECT id FROM engagement_log
                       WHERE agent='AGS:sprzedaz' AND status='proposed' AND content ILIKE %s
                       ORDER BY created_at DESC LIMIT 1)
           RETURNING id""", (f"%{row['prospect_name'][:80]}%",))
    if not row.get("next_followup_at"):
        db.execute("UPDATE sales_pipeline SET next_followup_at=NOW() + interval '3 days', updated_at=NOW() WHERE id=%s",
                   (row["id"],))
    _append_notes(row["id"], "outreach WYSLANY przez Tomasza")
    return (f"✉️ Odnotowane: outreach do {row['prospect_name'][:70]} wyslany"
            + ("" if upd else " (nie znalazlem pasujacej propozycji - zapisalem sama notatke)")
            + (". Follow-up ustawiony za 3 dni." if not row.get("next_followup_at") else "."))


# ---------------- baza wiedzy ----------------
def _knowledge_search_text(query, top_n=5, quiet=False, min_similarity=None):
    """min_similarity: prog dla tekstow do KLIENTA. Baza ma dzis 3 materialy (same Adamietz), wiec
    najblizszy sasiad ZAWSZE cos zwraca - do promptu o szkole tanca wchodzily raporty o holdingu
    budowlanym z podobienstwem 0.40-0.45 jako "techniki" (dowod: gotowiec StandART 24/07 11:44).
    Lepiej nie podac nic niz podac cudzy case: model ma wtedy jawna luke, nie falszywy kontekst."""
    v = content_memory.embed(query)
    rows = []
    if v:
        rows = db.fetchall(
            """SELECT material_name, material_type, content_excerpt,
                      1 - (embedding <=> %s::vector) AS similarity
               FROM sales_knowledge WHERE brand_id='AGS' AND embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector LIMIT %s""",
            (content_memory._vec_literal(v), content_memory._vec_literal(v), top_n))
        if min_similarity is not None:
            rows = [r for r in rows if r.get("similarity") is not None
                    and float(r["similarity"]) >= min_similarity]
    if min_similarity is not None and not rows:
        return ""  # fallback ILIKE nie ma wyniku podobienstwa, wiec przy progu go nie uzywamy
    if not rows:  # fallback bez embeddingow (brak klucza OpenAI / baza swieza)
        words = [w for w in re.split(r"\W+", query) if len(w) > 3][:4]
        if words:
            rows = db.fetchall(
                "SELECT material_name, material_type, content_excerpt, NULL AS similarity "
                "FROM sales_knowledge WHERE brand_id='AGS' AND ("
                + " OR ".join(["content_excerpt ILIKE %s"] * len(words))
                + ") ORDER BY added_at DESC LIMIT %s",
                (*[f"%{w}%" for w in words], top_n))
    if not rows:
        return "" if quiet else "Baza wiedzy nie zwrocila nic do tego pytania (pusta albo bez dopasowan)."
    out = []
    for r in rows:
        sim = f" ({float(r['similarity']):.2f})" if r.get("similarity") is not None else ""
        out.append(f"[{r['material_type']}] {r['material_name'][:50]}{sim}:\n"
                   f"{(r['content_excerpt'] or '')[:400]}")
    return "\n\n".join(out)


_TYPE_HINTS = (("outreach_example", ("wzorzec", "moj mail", "moja wiadomosc", "tak pisze",
                                     "przyklad outreach", "wyslalem")),
               ("book", ("ksiazk", "book")), ("technique", ("technik", "technique")),
               ("case_study", ("case", "studium")), ("framework", ("framework", "model")),
               ("script", ("skrypt", "script")), ("recording", ("nagran", "recording", "transkrypc")))


def _guess_type(hint):
    low = (hint or "").lower()
    for t, keys in _TYPE_HINTS:
        if any(k in low for k in keys):
            return t
    return "other"


def _chunks(text, size=2000, max_chunks=40):
    out, buf = [], ""
    for para in re.split(r"\n\s*\n", text):
        if len(buf) + len(para) + 2 > size and buf:
            out.append(buf.strip())
            buf = ""
            if len(out) >= max_chunks:
                break
        buf += para + "\n\n"
    if buf.strip() and len(out) < max_chunks:
        out.append(buf.strip())
    return out


def ingest_material(chat_id, text, state):
    """Zapis materialu sprzedazowego: [DOKUMENT: x] albo wklejony tekst -> chunk -> embedding
    -> sales_knowledge. REGULA PRAWDY: paragon z liczba kawalkow i embeddingow."""
    clear_pending()
    hint = (state or {}).get("hint") or ""
    name = hint.strip()[:150] or None
    m = re.match(r"^\[DOKUMENT:\s*([^\]]+)\]\s*(.*)$", text, re.DOTALL)
    if m:
        name = name or m.group(1).strip()[:150]
        body = m.group(2).strip()
    else:
        body = text.strip()
    if not name:
        name = body.splitlines()[0].strip()[:80] or "material bez nazwy"
    mtype = _guess_type(hint + " " + name)
    parts = _chunks(body)
    if not parts:
        _tg_send(chat_id, "❌ Pusty material - nic nie zapisalem.")
        return
    embedded = 0
    for i, p in enumerate(parts, start=1):
        v = content_memory.embed(p)
        if v:
            embedded += 1
            db.execute(
                """INSERT INTO sales_knowledge (brand_id, material_type, material_name, chunk_no,
                                                content_excerpt, embedding, tags, added_by)
                   VALUES ('AGS',%s,%s,%s,%s,%s::vector,%s,'telegram')""",
                (mtype, name, i, p, content_memory._vec_literal(v),
                 [w for w in re.split(r"[,\s]+", hint) if w][:6]))
        else:
            db.execute(
                """INSERT INTO sales_knowledge (brand_id, material_type, material_name, chunk_no,
                                                content_excerpt, tags, added_by)
                   VALUES ('AGS',%s,%s,%s,%s,%s,'telegram')""",
                (mtype, name, i, p, [w for w in re.split(r"[,\s]+", hint) if w][:6]))
    note = "" if embedded == len(parts) else \
        f" (embeddingi tylko {embedded}/{len(parts)} - reszta znajdzie sie po slowach kluczowych)"
    _tg_send(chat_id, f"📚 Zapisane do bazy wiedzy sprzedazowej: \"{name}\" [{mtype}] - "
                      f"{len(parts)} kawalkow{note}. Sprzedawca bedzie z tego korzystal przy "
                      f"outreachu i doradztwie.")


def pdf_text(blob):
    """Ekstrakcja tekstu z PDF (pypdf). None gdy biblioteka/plik zawodzi - wolajacy melduje jawnie."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(blob))
        out = "\n\n".join((page.extract_text() or "") for page in reader.pages[:200])
        out = out.strip()
        return out[:150_000] if out else None
    except Exception:
        traceback.print_exc()
        return None


# ---------------- komendy deterministyczne (PRZED LLM, wzorzec _config_route) ----------------
# ---------------- PODSUMOWANIE KLIENTA (kanon Sales Manager 22/07; decyzja Managera P1) ----------------
# Feedback Tomasza 22/07 po tap-tescie: bez nazwy "dziennik kapitanski" w interfejsie
# (wystarczy "podsumowanie"), pelna polszczyzna, KROTKIE wpisy osi czasu zamiast wklejonych
# blobow (research renderowal sie jako wielkie naglowki, strategia ucieta w pol slowa).
_NOTE_TS_SPLIT = re.compile(r"(?=\[\d{2}/\d{2} \d{2}:\d{2}\])")


def _note_entries(notes):
    """Notatki lejka -> lista krotkich wpisow osi czasu (markdown i biale znaki sprzatniete)."""
    out = []
    for chunk in _NOTE_TS_SPLIT.split(notes or ""):
        t = re.sub(r"[#*_`>]+", "", chunk)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append(t)
    return out


def _captain_log_text(fragment):
    """Podsumowanie klienta: esencja na gorze (etap, nastepny krok, obowiazujaca strategia,
    ostatni ruch), potem zwarta os czasu i interakcje. WIDOK na zrodla append-only
    (sales_pipeline.notes + engagement_log) - niczego nie duplikuje. Cel: ratowanie
    kontaktu po miesiacach = przeczytanie tego jednego pliku."""
    row = _find_pipeline(fragment)
    if not row:
        return None, f"Nie znajduję w lejku klienta \"{(fragment or '')[:60]}\"."
    name = row.get("prospect_name") or "(bez nazwy)"
    entries = _note_entries(row.get("notes"))
    strategy = next((e for e in reversed(entries) if "STRATEGIA OBOWIAZUJACA" in e.upper()
                     or "STRATEGIA OBOWIĄZUJĄCA" in e.upper()), None)
    nf = row.get("next_followup_at")
    head = [f"📋 PODSUMOWANIE KLIENTA: {name}"
            + (f"  ({row['prospect_url']})" if row.get("prospect_url") else "")]
    head.append("")
    head.append("NAJWAŻNIEJSZE:")
    head.append(f"• Etap lejka: {row.get('stage')} | następny krok: "
                + (nf.astimezone(WARSAW).strftime("%d/%m %H:%M") if nf else "NIE USTAWIONY"))
    if strategy:
        head.append("• Strategia: " + strategy[:500])
    if entries:
        head.append("• Ostatni ruch: " + entries[-1][:220])
    lines = ["\n".join(head), "OŚ CZASU:"]
    if entries:
        lines.append("\n".join("• " + (e if len(e) <= 220 else e[:217] + "...") for e in entries))
    else:
        lines.append("(pusto)")
    e_rows = db.fetchall(
        """SELECT created_at, action_type, status,
                  LEFT(COALESCE(NULLIF(response,''), content), 300) AS what
           FROM engagement_log
           WHERE content ILIKE %s OR notes ILIKE %s OR author_display ILIKE %s
           ORDER BY created_at""",
        (f"%{name}%", f"%{name}%", f"%{name}%"))
    lines.append("INTERAKCJE:")
    if e_rows:
        il = []
        for e in e_rows:
            try:
                stamp = e["created_at"].astimezone(WARSAW).strftime("%d/%m %H:%M")
            except Exception:
                stamp = "??"
            what = re.sub(r"\s+", " ", (e.get("what") or "")).strip()
            il.append(f"• [{stamp}] {e['action_type']} ({e['status']}): "
                      + (what if len(what) <= 160 else what[:157] + "..."))
        lines.append("\n".join(il))
    else:
        lines.append("(brak zapisanych interakcji)")
    lines.append("Pełne treści (research, oferty, maile): baza wiedzy sprzedażowa + docs/research/prospekci/.")
    return name, "\n\n".join(lines)


def _show_dziennik(chat_id, fragment):
    title, text = _captain_log_text(fragment)
    if not title:
        _tg_send(chat_id, text)
        return
    if len(text) > 3500:
        from . import matreview
        matreview._tg_send_document(chat_id, f"podsumowanie_{re.sub(r'[^a-z0-9]+', '_', title.lower())[:40]}.md",
                                    text, caption=f"📋 Podsumowanie klienta: {title} (całość w pliku)")
    else:
        _tg_send(chat_id, text)


TOOL_DZIENNIK = {
    "name": "dziennik_klienta",
    "description": ("Pokaz DZIENNIK KAPITANSKI klienta: chronologiczny zapis calej pracy "
                    "(kartoteka lejka + wszystkie interakcje). Uzywaj gdy Tomasz pyta o historie "
                    "klienta, przygotowuje sie do rozmowy albo chce uratowac kontakt."),
    "input_schema": {"type": "object", "properties": {
        "prospect_fragment": {"type": "string", "description": "Fragment nazwy/URL klienta z lejka."}},
        "required": ["prospect_fragment"]},
}
_SALES_TOOLS.append(TOOL_DZIENNIK)  # definicja ponizej listy - dolaczamy tu, nie przy deklaracji


_PROSPECT_RE = re.compile(r"^/prospect(?:@\w+)?\s+(.+)$", re.IGNORECASE | re.DOTALL)
_DZIENNIK_RE = re.compile(r"^/dziennik(?:@\w+)?\s*(.*)$", re.IGNORECASE | re.DOTALL)
_PIPELINE_RE = re.compile(r"^/pipeline(?:@\w+)?\s*$", re.IGNORECASE)
_OFERTA_RE = re.compile(r"^/oferta(?:@\w+)?\s*(.*)$", re.IGNORECASE | re.DOTALL)
_ADDMAT_RE = re.compile(r"^/add_sales_material(?:@\w+)?\s*(.*)$", re.IGNORECASE | re.DOTALL)


def try_command(chat_id, text, active):
    """Deterministyczna sciezka komend sprzedazowych + konsumpcja uzbrojonego /add_sales_material.
    Zwraca True gdy obsluzone (conversation.handle konczy). Dziala z KAZDYM aktywnym agentem."""
    st = _pending_armed()
    if st:
        low = text.strip().lower()
        if low in ("/cancel", "/anuluj", "anuluj"):
            clear_pending()
            _tg_send(chat_id, "Anulowane - nic nie zapisalem do bazy wiedzy.")
            return True
        if text.startswith("[DOKUMENT:") or (not text.startswith("/") and len(text.strip()) >= 200):
            ingest_material(chat_id, text, st)
            return True
    m = _PROSPECT_RE.match(text)
    if m:
        _tg_send(chat_id, _prospect_research({"prospect": m.group(1).strip(), "tier": "medium"}))
        return True
    if re.match(r"^/prospect(?:@\w+)?\s*$", text, re.IGNORECASE):
        _tg_send(chat_id, "Uzycie: /prospect <nazwa firmy albo URL> - zleca research medium "
                          "(kilka minut, ~1-2 PLN) i dodaje prospekta do lejka. Glebokie "
                          "przeswietlenie: recznie na abonamencie, zrzut wrzuc jako material.")
        return True
    if _PIPELINE_RE.match(text):
        _tg_send(chat_id, pipeline_text())
        return True
    m = _DZIENNIK_RE.match(text)
    if m:
        arg = m.group(1).strip()
        if not arg:
            _tg_send(chat_id, "Uzycie: /dziennik <nazwa klienta z lejka> - pelny dziennik "
                              "kapitanski (kartoteka + wszystkie interakcje chronologicznie).")
        else:
            _show_dziennik(chat_id, arg)
        return True
    m = _OFERTA_RE.match(text)
    if m:
        arg = m.group(1).strip()
        if not arg:
            _tg_send(chat_id, "💰 CENNIK (pelna drabinka):\n" + _pricing_text()
                     + "\n\nDopasowanie do prospekta: /oferta <nazwa z lejka>.")
            return True
        handle_chat(chat_id, f"Dopasuj oferte dla prospekta: {arg}. Uzyj offer_for i zarekomenduj "
                             f"tier od gory z uzasadnieniem wartoscia.")
        return True
    m = _ADDMAT_RE.match(text)
    if m:
        _state_set({"armed": True, "hint": m.group(1).strip()[:200],
                    "ts": datetime.datetime.now(WARSAW).isoformat(), "chat_id": chat_id})
        _tg_send(chat_id, "📚 Tryb dodawania materialu sprzedazowego UZBROJONY (2h): wyslij teraz "
                          "dokument .md/.txt/.pdf ALBO wklej tekst (min 200 znakow) jedna "
                          "wiadomoscia. Podpowiedz typu w komendzie pomaga (np. "
                          "/add_sales_material ksiazka Hormozi oferta). '/anuluj' wycofuje.")
        return True
    return False


# ---------------- rozmowa (petla agentowa, wzorzec _subagent_handle) ----------------
def _dispatch(name, inp, chat_id):
    inp = dict(inp or {})
    if name == "prospect_research":
        return _prospect_research(inp)
    if name == "prospect_results":
        return _prospect_results(inp)
    if name == "draft_outreach":
        return _draft_outreach(inp, chat_id)
    if name == "offer_for":
        return _offer_for(inp)
    if name == "pipeline_view":
        return pipeline_text()
    if name == "pipeline_add":
        return _pipeline_add(inp)
    if name == "pipeline_move":
        return _pipeline_move(inp)
    if name == "sales_knowledge_search":
        # Prog obowiazuje TAKZE tutaj: w rozmowie o StandART narzedzie zwracalo materialy
        # o Adamietzu z podobienstwem 0.40-0.48 (dowod 24/07 13:29) i model musial je odsiewac
        # sam. Ponizej progu mowimy wprost, ze bazie brakuje materialu.
        out = _knowledge_search_text(str(inp.get("query") or ""), min_similarity=_KNOWLEDGE_MIN_SIM)
        return out or ("Baza wiedzy nie ma materialu trafnego dla tego pytania (prog "
                       f"{_KNOWLEDGE_MIN_SIM}). Nie nadrabiaj ogolnikami - powiedz to wprost.")
    if name == "outreach_sent":
        return _outreach_sent(inp)
    if name == "dziennik_klienta":
        _, text = _captain_log_text(str(inp.get("prospect_fragment") or ""))
        return text
    return "ok"


def handle_chat(chat_id, text):
    """Rozmowa z Agentem Sprzedazy (active_agent = subagent:AGS:sprzedaz). Petla agentowa do 5
    krokow; kazdy wynik narzedzia = paragon pokazany Tomaszowi (test prawdy)."""
    from . import conversation
    ph = conversation._tg("sendMessage", {"chat_id": chat_id, "text": "⏳"})
    ph_id = ((ph or {}).get("result") or {}).get("message_id")
    history = conversation._load_history(chat_id, agent=AGENT_KEY) + [{"role": "user", "content": text}]
    model, tier, source = tasks.model_for("sales_chat")
    sysblocks = _system(chat_id)
    msgs = list(history)
    parts = []
    for _step in range(_MAX_TOOL_STEPS):
        resp = client().messages.create(
            model=model, max_tokens=2500, thinking={"type": "disabled"},
            system=sysblocks, tools=_SALES_TOOLS, messages=msgs)
        tasks.log_task("sales_chat", tier, model, source, getattr(resp, "usage", None))
        parts += [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
        tool_uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
        if not tool_uses:
            break
        msgs.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in tool_uses:
            try:
                out = _dispatch(tu.name, tu.input, chat_id) or "ok"
            except Exception as e:
                traceback.print_exc()
                out = f"BLAD narzedzia {tu.name}: {type(e).__name__}: {str(e)[:150]}"
            if tu.name in _MODEL_ONLY:
                # dane-kontekst dla modelu (rekomendacje sklada model, nie surowy zrzut)
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(out)[:3000]})
                continue
            parts.append(out)  # PARAGON: wynik narzedzia idzie do Tomasza doslownie
            if tu.name in _VERBATIM:
                fb = "POKAZANE TOMASZOWI DOSLOWNIE (nie powtarzaj, mozesz sie krotko odniesc):\n" + str(out)[:1500]
            else:
                fb = "WYKONANE - potwierdzenie pokazane Tomaszowi (nie powtarzaj go): " + str(out)[:400]
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": fb[:3000]})
        msgs.append({"role": "user", "content": results})
    reply = "\n\n".join(parts).strip() or "Przyjete."
    conversation._save_history(chat_id, history + [{"role": "assistant", "content": reply}], agent=AGENT_KEY)
    conversation._reply(chat_id, reply, placeholder_id=ph_id)


# ---------------- tick workera: wyniki researchu prospektow ----------------
def tick():
    """Petla workera: RESPONSE Researchera do sales-agent -> synteza sygnalow buyer (Sonnet)
    -> Telegram + notatka w lejku. Kazda sciezka konczy sie jawnie (REGULA PRAWDY)."""
    try:
        rows = db.fetchall(
            """SELECT message_id, payload, correlation_id FROM agent_messages
               WHERE to_agent_id=(SELECT agent_id FROM agent_registry WHERE agent_name=%s)
                 AND message_type='response' AND status='unread'
               ORDER BY created_at LIMIT 3""", (AGENT_ID,))
    except Exception:
        traceback.print_exc()
        return
    if not rows:
        return
    from . import hitl
    chat = hitl._admin_chat_id()
    for r in rows:
        db.execute("UPDATE agent_messages SET status='read', read_at=NOW() WHERE message_id=%s",
                   (r["message_id"],))  # najpierw read - zepsuty wpis nie zapetla ticka
        try:
            pipe = db.fetchone("SELECT * FROM sales_pipeline WHERE id::text=%s",
                               (str(r.get("correlation_id") or ""),))
            payload = r.get("payload") or {}
            job_id = (payload.get("job_id") if isinstance(payload, dict) else None) \
                or (pipe or {}).get("research_job_id")
            grounding = research.grounding_with_sources(job_id, limit=12) if job_id else ""
            name = (pipe or {}).get("prospect_name") or "(prospekt spoza lejka)"
            if not grounding:
                if chat:
                    _tg_send(chat, f"🔍 Research prospekta {name}: Researcher odpowiedzial, ale bez "
                                   f"claims (job {str(job_id)[:8] if job_id else '?'}). Sprawdz job "
                                   f"albo zlec ponownie.")
                continue
            summary = compliance.fix_dashes(_summarize_research(name, grounding))  # kanon marki: zero em dash
            # SAMODZIELNA WERYFIKACJA (24/07, frustracja Tomasza przy Stepowni): research podal
            # w swoim wlasnym tekscie adres strony prospekta i profil FB, po czym agent orzekl
            # "tozsamosc niepotwierdzona, podaj strone". Prosil czlowieka o rzecz, ktora mial
            # przed nosem. Teraz: gdy w lejku nie ma adresu, agent wylawia go z researchu,
            # WCHODZI na niego i dopiero potem orzeka.
            tekst_strony = ""
            if pipe and not (pipe.get("prospect_url") or "").strip():
                kandydat = _znajdz_strone_w_researchu(name, f"{grounding}\n{summary}")
                if kandydat:
                    wiz2 = wizytowka(kandydat)
                    tekst_strony = wiz2.get("tekst") or ""
                    if tekst_strony:
                        db.execute("UPDATE sales_pipeline SET prospect_url=%s, updated_at=NOW() "
                                   "WHERE id=%s AND COALESCE(prospect_url,'')=''", (kandydat, pipe["id"]))
                        pipe["prospect_url"] = kandydat
                        _zapisz_kontakt(pipe["id"], mail=wiz2.get("mail"), tel=wiz2.get("tel"),
                                        ze_strony=True)
                        _zapisz_osobe_ze_strony(pipe["id"], tekst_strony)
                        _append_notes(pipe["id"], f"agent sam wszedl na strone z researchu: {kandydat}"
                                      + (f", tel {wiz2.get('tel')}" if wiz2.get("tel") else "")
                                      + (f", mail {wiz2.get('mail')}" if wiz2.get("mail") else ""))
            # Bramka tozsamosci: przy niepotwierdzonym podmiocie nastepnym ruchem NIE jest outreach.
            # Wysylka do firmy, ktorej research nie potwierdzil, kosztuje wiarygodnosc, nie tokeny.
            stan, powod = _identity_verdict(pipe, job_id, summary, tekst_strony)
            if stan == "potwierdzona":
                nastepny = (f"✅ Tozsamosc potwierdzona ({powod}). Nastepny ruch: przelacz /agents "
                            f"na Sprzedawce i powiedz np. 'napisz outreach do {name[:40]}'.")
            elif stan == "z zastrzezeniem":
                nastepny = (f"⚠️ Podmiot potwierdzony dowodami ({powod[:150]}). Outreach mozesz "
                            f"pisac, ale ZWERYFIKUJ ten punkt przed wyslaniem - najtaniej telefonem. "
                            f"Nastepny ruch: 'napisz outreach do {name[:40]}'.")
            else:
                nastepny = (f"⛔ TOZSAMOSC NIEPOTWIERDZONA ({powod}). Nastepny ruch: NIE pisz "
                            f"outreachu. Podaj strone i zlec ponownie: /prospect {name[:40]} "
                            f"<adres strony>. Bez strony potwierdz firme telefonem albo profilem.")
            text = f"🔍 RESEARCH PROSPEKTA GOTOWY: {name}\n\n{summary}\n\n{nastepny}"
            if chat:
                _tg_send(chat, text)
            if pipe:
                # Research UZUPELNIA BAZE, nie tylko notatki (zgloszenie Tomasza 24/07: "od tego
                # jest"). Deterministycznie: mail i telefon z claims i z podsumowania, zapisywane
                # WYLACZNIE w puste kolumny (DDL 029).
                _zrodlo = " ".join([grounding[:6000], summary[:4000]])
                _m, _t = _EMAIL_RE.search(_zrodlo), _PHONE_RE.search(_zrodlo)
                if _m or _t:
                    _zapisz_kontakt(pipe["id"], mail=_m.group(0) if _m else None,
                                    tel=_t.group(0).strip() if _t else None)
                # Marker niesie werdykt dalej (czyta go _draft_outreach). Nazwa MUSI byc inna niz
                # "TOZSAMOSC:", bo tak zaczyna sie pierwsza linia podsumowania pisana przez model -
                # skan po samym "TOZSAMOSC:" trafial w tekst modelu zamiast w werdykt kodu.
                _append_notes(pipe["id"], f"research gotowy [WERDYKT TOZSAMOSCI: {stan}]:\n{summary[:1200]}")
        except Exception:
            traceback.print_exc()


def _summarize_research(name, grounding):
    try:
        model, tier, source = tasks.model_for("sales_research_summary")
        resp = client().messages.create(
            # 800 obcinalo podsumowanie w polowie sekcji (dowod 24/07 10:46: karta La Cultury
            # urwana na "HA" z HAK PERSONALIZACJI). Linia TOZSAMOSCI + linki zjadaja budzet.
            model=model, max_tokens=1600, thinking={"type": "disabled"},
            messages=[{"role": "user", "content":
                       f"Podsumuj research prospekta \"{name}\" dla sprzedazy B2B (AGS: systemy "
                       f"retencji klientow i agenty AI). Po polsku, zwiezle, zero em dash.\n"
                       # BRAMKA TOZSAMOSCI (24/07): research potrafi opisac inna firme o podobnej
                       # nazwie (La Cultura z Sosnowca wrocila jako studio w Pawtucket RI).
                       # Pierwsza linia jest KONTRAKTEM dla kodu, nie ozdoba.
                       f"PIERWSZA LINIA MUSI brzmiec doslownie 'TOZSAMOSC: potwierdzona' albo "
                       f"'TOZSAMOSC: niepewna - <powod>'. Pytanie dotyczy PODMIOTU (czy claims "
                       f"opisuja te firme: zgodna domena, miasto, kraj), NIE tego, ktory kanal "
                       f"kontaktu jest wlasciwy - watpliwosci o kanal, mail czy profil zglaszaj "
                       f"w sekcji HAK PERSONALIZACJI. 'niepewna' gdy rozbiezny kraj albo miasto, "
                       f"kilka rownie prawdopodobnych firm o tej nazwie, albo brak potwierdzenia "
                       f"adresu.\n"
                       f"Dalej sekcje: KIM SA (2-3 zdania) / SYGNALY KUPNA / PROBLEMY KTORE "
                       f"ROZWIAZUJEMY / HAK PERSONALIZACJI / REKOMENDOWANY TIER (od gory). Fakt "
                       f"bez zrodla w danych oznacz '(do weryfikacji)'. Zachowaj 2-3 linki.\n"
                       # Dowod 24/07: hak oparto o Mistrzostwa Europy, ktore juz sie odbyly -
                       # gotowiec pisal "trzymam kciuki PRZED", a impreza byla za nami.
                       f"Przy KAZDYM wydarzeniu w sekcji HAK podaj jego DATE i napisz wprost, "
                       f"czy JUZ SIE ODBYLO, czy DOPIERO BEDZIE wzgledem dzisiaj "
                       f"({datetime.datetime.now(WARSAW).strftime('%d/%m/%Y')}). Gdy daty nie ma "
                       f"w danych, napisz 'data nieznana' - nie zgaduj czasu.\n\n"
                       f"CLAIMS Z RESEARCHU:\n{grounding[:5000]}"}])
        tasks.log_task("sales_research_summary", tier, model, source, getattr(resp, "usage", None))
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        if out:
            return out
    except Exception:
        traceback.print_exc()
    return "Synteza padla - surowe claims:\n" + grounding[:2500]  # REGULA PRAWDY: fakty i tak docieraja
