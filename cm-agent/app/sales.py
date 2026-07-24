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

from . import db, config, tasks, research, content_memory
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
            pass
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
        """SELECT prospect_name, stage, offer_tier, value, currency, next_followup_at, updated_at, notes
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
            bits.append(f"follow-up: {fu.astimezone(WARSAW).strftime('%d/%m %H:%M')}{late}")
        else:
            bits.append("⚠️ BRAK next-step")
        stale = (now - r["updated_at"]).days if r.get("updated_at") else 0
        if stale >= 14:
            bits.append(f"⚠️ cisza {stale} dni")
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
    "- KONFLIKT INTERESOW (kanon Tomasza 24/07): NIE sprzedajemy KONKURENCJI BEZPOSREDNIEJ "
    "Royal Dance Center. Wykluczone z lejka: szkoly tanca, studia i zespoly taneczne z Opola "
    "i okolic (promien ok. 50 km: Opole, Strzelce Opolskie, Brzeg, Kluczbork, Krapkowice, "
    "Nysa, Kedzierzyn-Kozle). System retencji w rekach lokalnego konkurenta = narzedzie do "
    "odbierania klientow RDC. Szkoly tanca spoza tego regionu (Slask, Dolny Slask, reszta "
    "Polski) sa OK - tam RDC nie konkuruje. Regula obowiazuje, dopoki Tomasz prowadzi RDC; "
    "gdy zamknie studio, znika. Gdy prospekt wpada pod te regule: NIE rob researchu, NIE pisz "
    "outreachu - oznacz go w lejku jako 'lost' z notatka 'konflikt interesow RDC' i powiedz "
    "Tomaszowi wprost.\n"
    "- NARZEDZIA NIE UJAWNIAMY: nazwa platformy (GHL i inne) NIGDY nie pada w komunikacji "
    "sprzedazowej. Sprzedajemy REZULTAT: 'system retencji klientow', 'uszczelnienie sciezki "
    "klienta', 'automatyzacja follow-up'.\n"
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
        f"GLOS MARKI (Voice Bible - outreach MUSI byc w tym glosie):\n"
        f"{(brand.get('voice_bible') or '')[:2500]}\n\n"
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


def _research_query(name, url, hint=None):
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
        # REGULA PRAWDY 24/07: podmiot o podobnej nazwie w innym kraju wrocil jako "ten" prospekt.
        "TOZSAMOSC: potwierdz, ze badany podmiot to TEN podmiot (zgodnosc domeny, miasta, kraju). "
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
    code, resp = _request_research(_research_query(name, url, hint), tier, row["id"])
    job_id = (resp or {}).get("job_id")
    if code == 202 and job_id:
        db.execute("UPDATE sales_pipeline SET research_job_id=%s, updated_at=NOW() WHERE id=%s",
                   (str(job_id), row["id"]))
        _append_notes(row["id"], f"research zlecony (tier {tier}, job {str(job_id)[:8]})")
        eta = "kilka minut, ~1-2 PLN"
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
                                       top_n=3, quiet=True)
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
                 f"{_FRAMEWORKS}\n\nGLOS MARKI:\n{(brand.get('voice_bible') or '')[:2000]}"}],
        messages=[{"role": "user", "content":
                   f"Napisz {forms.get(channel, channel)} po "
                   f"{'polsku' if lang == 'pl' else 'angielsku'} do prospekta: "
                   f"{row['prospect_name']}" + (f" ({row['prospect_url']})" if row.get("prospect_url") else "") + ".\n"
                   + (f"WSKAZOWKI TOMASZA: {inp['guidance']}\n" if inp.get("guidance") else "")
                   + (f"\nRESEARCH (fakty z linkami - hak personalizacji STAD):\n{grounding[:3000]}\n"
                      if grounding else "\nBRAK researchu - personalizuj tylko tym, co pewne z nazwy/kontekstu; ZERO zmyslonych faktow.\n")
                   + (f"\nTECHNIKI Z BAZY WIEDZY:\n{knowledge[:1500]}\n" if knowledge else "")
                   + f"\nNOTATKI LEJKA: {(row.get('notes') or '')[:600]}\n\n"
                   "Zwroc WYLACZNIE gotowa tresc do wyslania (zero komentarza, zero markdown)."}])
    tasks.log_task("sales_outreach", tier, model, source, getattr(resp, "usage", None))
    draft = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    if not draft:
        return "Nie wyszlo - sprobuj jeszcze raz (model nie zwrocil tresci)."
    # gotowiec: naglowek + CZYSTA WKLEJKA osobna wiadomoscia (kanon comment-radar)
    # Bramka tozsamosci: marker z podsumowania researchu zyje w notatkach lejka. Nie blokujemy
    # pisania (decyduje Tomasz), ale gotowiec ma jechac z ostrzezeniem, nie po cichu.
    watpliwa = "tozsamosc: niepewn" in (row.get("notes") or "").lower()
    _tg_send(chat_id, f"🧾 OUTREACH DO WYSLANIA RECZNIE - {channel} - {row['prospect_name'][:80]}\n"
                      + ("⚠️ RESEARCH NIE POTWIERDZIL TOZSAMOSCI TEJ FIRMY - zweryfikuj adresata "
                         "PRZED wyslaniem.\n" if watpliwa else "")
                      + f"(ponizej czysta wklejka; NIC nie wysyla sie samo)")
    _tg_send(chat_id, draft)
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
            bits.append(f"follow-up: {fu.astimezone(WARSAW).strftime('%d/%m %H:%M')}")
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
def _knowledge_search_text(query, top_n=5, quiet=False):
    v = content_memory.embed(query)
    rows = []
    if v:
        rows = db.fetchall(
            """SELECT material_name, material_type, content_excerpt,
                      1 - (embedding <=> %s::vector) AS similarity
               FROM sales_knowledge WHERE brand_id='AGS' AND embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector LIMIT %s""",
            (content_memory._vec_literal(v), content_memory._vec_literal(v), top_n))
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


_TYPE_HINTS = (("book", ("ksiazk", "book")), ("technique", ("technik", "technique")),
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
        return _knowledge_search_text(str(inp.get("query") or ""))
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
            summary = _summarize_research(name, grounding)
            # Bramka tozsamosci: przy niepewnym podmiocie nastepnym ruchem NIE jest outreach.
            # Wysylka do firmy, ktorej research nie potwierdzil, kosztuje wiarygodnosc, nie tokeny.
            niepewna = bool(re.match(r"\s*TOZSAMOSC:\s*niepewn", summary, re.IGNORECASE))
            nastepny = (
                f"⚠️ TOZSAMOSC NIEPOTWIERDZONA. Nastepny ruch: NIE pisz outreachu. Podaj strone "
                f"i zlec ponownie: /prospect {name[:40]} <adres strony>. Jesli firma nie ma "
                f"strony, potwierdz ja telefonem albo profilem spolecznosciowym."
                if niepewna else
                f"Nastepny ruch: przelacz /agents na Sprzedawce i powiedz np. "
                f"'napisz outreach do {name[:40]}'.")
            text = f"🔍 RESEARCH PROSPEKTA GOTOWY: {name}\n\n{summary}\n\n{nastepny}"
            if chat:
                _tg_send(chat, text)
            if pipe:
                _append_notes(pipe["id"], f"research gotowy:\n{summary[:1200]}")
        except Exception:
            traceback.print_exc()


def _summarize_research(name, grounding):
    try:
        model, tier, source = tasks.model_for("sales_research_summary")
        resp = client().messages.create(
            model=model, max_tokens=800, thinking={"type": "disabled"},
            messages=[{"role": "user", "content":
                       f"Podsumuj research prospekta \"{name}\" dla sprzedazy B2B (AGS: systemy "
                       f"retencji klientow i agenty AI). Po polsku, zwiezle, zero em dash.\n"
                       # BRAMKA TOZSAMOSCI (24/07): research potrafi opisac inna firme o podobnej
                       # nazwie (La Cultura z Sosnowca wrocila jako studio w Pawtucket RI).
                       # Pierwsza linia jest KONTRAKTEM dla kodu, nie ozdoba.
                       f"PIERWSZA LINIA MUSI brzmiec doslownie 'TOZSAMOSC: potwierdzona' albo "
                       f"'TOZSAMOSC: niepewna - <powod>'. 'potwierdzona' TYLKO wtedy, gdy claims "
                       f"wskazuja na TEN podmiot (zgodna domena, miasto, kraj). Rozbieznosc kraju "
                       f"albo miasta, kilka podobnie nazwanych firm, brak potwierdzenia adresu = "
                       f"'niepewna'.\n"
                       f"Dalej sekcje: KIM SA (2-3 zdania) / SYGNALY KUPNA / PROBLEMY KTORE "
                       f"ROZWIAZUJEMY / HAK PERSONALIZACJI / REKOMENDOWANY TIER (od gory). Fakt "
                       f"bez zrodla w danych oznacz '(do weryfikacji)'. Zachowaj 2-3 linki.\n\n"
                       f"CLAIMS Z RESEARCHU:\n{grounding[:5000]}"}])
        tasks.log_task("sales_research_summary", tier, model, source, getattr(resp, "usage", None))
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        if out:
            return out
    except Exception:
        traceback.print_exc()
    return "Synteza padla - surowe claims:\n" + grounding[:2500]  # REGULA PRAWDY: fakty i tak docieraja
