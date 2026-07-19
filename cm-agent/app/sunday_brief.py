# -*- coding: utf-8 -*-
"""CM CZYTA SWIAT (KANON 19/07, budowniczy BE-SWIAT): cotygodniowy PODKLAD pod niedzielny
artykul LinkedIn Tomasza. Niedzielny artykul = insight tygodnia ze swiata AI; robi go Tomasz
RECZNIE (planer ma zakaz niedzieli). Ten organ daje mu ZDOLNOSC CZYTANIA SWIATA: w sobote CM
zleca Researcherowi badanie "co sie dzialo w AI przez 7 dni dla ICP solo-founderow", laczy to
ze schowkiem tygodnia + topowymi publikacjami i syntetyzuje 3 KANDYDACKIE TEZY z twardymi
liczbami i LINKAMI ZRODEL. Podklad idzie do Tomasza jako wiadomosc - draft do recznej obrobki.

TWARDE GRANICE (DoD briefu):
- Podklad NIE wchodzi do content_items ani post_queue (niedziela = recznie, kanon).
- Zrodla LINKOWANE (regula prawdy - zero niepodpartych faktow; brak URL = jawnie oznaczone).
- Zero DDL, zero n8n; stan anty-dublowy w brand_config (klucz cm_sunday_brief), wzorzec
  weekly_metrics_reminder (jeden podklad / tydzien ISO).
"""
import datetime
import json
import uuid
from zoneinfo import ZoneInfo

from . import db, tasks, research, content_memory
from .matreview import _state_get, _state_set

WARSAW = ZoneInfo("Europe/Warsaw")
STATE_KEY = "cm_sunday_brief"
BRAND = "AGS"

# Okna czasowe (Europe/Warsaw). Sobota = weekday()==5.
REQUEST_FROM_MIN = 8 * 60          # zlecenie badania od 08:00 (research ma czas dojechac przed poludniem)
REQUEST_UNTIL_MIN = 12 * 60 + 30   # do 12:30 wolno jeszcze zlecic (gdy worker wstal pozno)
SEND_FLOOR_MIN = 11 * 60           # nie wysylaj podkladu przed 11:00 (chyba ze research juz gotowy i tak)
SEND_FORCE_MIN = 13 * 60           # o 13:00 wysylaj mimo niegotowego researchu (fallback prawdy)
MANUAL_FALLBACK_S = 20 * 60        # tap-test: research nie dojechal w 20 min -> podklad bez niego

RESEARCHER_DONE = ("completed", "partial_failure")   # partial = mniej zrodel, ale evidence jest
RESEARCHER_DEAD = ("failed", "archived")

SUNDAY_QUERY = (
    "Najwazniejsze wydarzenia, premiery i dyskusje w swiecie AI z ostatnich 7 dni, istotne dla "
    "solo-founderow i malych zespolow budujacych z AI (2-4h dziennie, ograniczony budzet). "
    "Interesuja mnie: konkretne premiery modeli/narzedzi z datami, zmiany cen i limitow, realne "
    "wzorce wdrozen i porazki, liczby i benchmarki. Dla kazdego watku podaj tworde fakty (co, "
    "kiedy, ile) i zrodla. Kontekst odbiorcy: przedsiebiorca-operator, buduje agentow AI, "
    "publikuje build-in-public na LinkedIn/X."
)


def _admin_chat():
    from . import hitl
    return hitl._admin_chat_id()


def _tg(method, body):
    from . import conversation
    return conversation._tg(method, body)


def _send_long(text, kb_last=None):
    """Wysyla podklad do Tomasza, dzielac na kawalki < 3800 zn (URL-e potrafia byc dlugie).
    Guzik (jesli podany) leci przy OSTATNIM kawalku."""
    chat = _admin_chat()
    if not chat:
        return False
    chunks, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > 3800:
            chunks.append(buf)
            buf = ""
        buf += (line + "\n")
    if buf.strip():
        chunks.append(buf)
    ok = False
    for i, ch in enumerate(chunks):
        body = {"chat_id": chat, "text": ch[:4000], "disable_web_page_preview": True}
        if kb_last and i == len(chunks) - 1:
            body["reply_markup"] = kb_last
        r = _tg("sendMessage", body)
        ok = bool(r and r.get("ok"))
    return ok


def _correlation(week):
    """Deterministyczny UUID per tydzien. WAZNE: jest to POPRAWNY uuid (nie kolizyjny z content_items -
    ingest_research_responses znajdzie brak itemu i tylko oznaczy wiadomosc 'read', bez bledu)."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"ags-sunday-brief-{week}")


# ---------------- zrodla podkladu ----------------
def _gather_inspirations(days=7, limit=15):
    """Schowek tygodnia = inspiracje + zlapane cudze posty (Idea Bot laduje przez telegram/notion)."""
    rows = db.fetchall(
        """SELECT content, source FROM inspirations
           WHERE created_at > NOW() - make_interval(days => %s)
           ORDER BY created_at DESC LIMIT %s""", (days, limit))
    if not rows:
        return "(schowek pusty w tym tygodniu)"
    return "\n".join(f"- ({r.get('source') or '?'}) {(r.get('content') or '')[:160]}" for r in rows)


def _gather_top_posts(days=7, limit=8):
    """Top publikacje tygodnia (co juz rezonowalo - kontekst, nie do powielania)."""
    try:
        rows = content_memory.top_performing(BRAND, top_n=limit, days_ago=days)
    except Exception:
        rows = content_memory.get_published(BRAND, days_ago=days, limit=limit)
    if not rows:
        return "(brak publikacji w tym tygodniu)"
    out = []
    for r in rows:
        metric = r.get("metric_value")
        tag = f" [{metric}]" if metric not in (None, "") else ""
        out.append(f"- ({r.get('platform') or '?'}{tag}) {(r.get('content') or r.get('topic') or '')[:120]}")
    return "\n".join(out)


# ---------------- synteza + wyslanie ----------------
def _synthesize(job_id, has_research):
    from .brand import load_brand
    from .generate import client
    brand = load_brand(BRAND)
    grounding = research.grounding_with_sources(job_id, limit=12) if (job_id and has_research) else ""
    schowek = _gather_inspirations()
    top = _gather_top_posts()
    research_block = grounding or ("(RESEARCH NIEDOSTEPNY w tym tygodniu - buduj tezy WYLACZNIE ze "
                                   "schowka i publikacji, i JAWNIE zaznacz przy fakcie brak zewnetrznego "
                                   "zrodla. NIE zmyslaj wydarzen ani liczb.)")
    model, tier, source = tasks.model_for("sunday_synth")   # domyslnie sonnet
    resp = client().messages.create(
        model=model, max_tokens=1600, thinking={"type": "disabled"},
        system=[{"type": "text", "text":
                 f"Jestes Content Managerem marki {BRAND}. Redagujesz PODKLAD (nie gotowy artykul) pod "
                 f"NIEDZIELNY artykul LinkedIn Tomasza - insight tygodnia ze swiata AI. Artykul finalnie "
                 f"pisze Tomasz recznie; Ty dajesz mu twardy material do wyboru.\n"
                 f"Glos marki (skrot):\n{brand['voice_bible'][:1200]}\n\n"
                 f"ZASADY TWARDE:\n"
                 f"- ZERO em-dash (kanon marki RULE 1): myslnik lub przebuduj zdanie.\n"
                 f"- REGULA PRAWDY: kazdy fakt/liczba MUSI miec pokrycie w dostarczonym materiale i link "
                 f"zrodla. Fakt bez zrodla oznacz '(do weryfikacji)'. Zero zmyslonych wydarzen.\n"
                 f"- Odbiorca artykulu: solo-founder / operator budujacy z AI (ICP AGS)."}],
        messages=[{"role": "user", "content":
                   f"Zbuduj PODKLAD pod niedzielny artykul. Zwroc DOKLADNIE 3 KANDYDACKIE TEZY. Kazda teza:\n"
                   f"1) jedno mocne zdanie-teza (kat pod ICP solo-founderow),\n"
                   f"2) 2-3 twarde fakty/liczby z tego tygodnia,\n"
                   f"3) LINKI ZRODEL (uzyj URL-i z materialu ponizej; jesli brak - '(do weryfikacji)'),\n"
                   f"4) jedno zdanie: dlaczego to wazne dla odbiorcy AGS.\n"
                   f"Na koncu dopisz krotki blok 'MATERIALY WLASNE' - przypomnienie, ze Tomasz moze "
                   f"dolozyc wlasny watek/anegdote z tygodnia.\n\n"
                   f"=== RESEARCH SWIATA (7 dni, claims + zrodla) ===\n{research_block[:6000]}\n\n"
                   f"=== SCHOWEK TYGODNIA (inspiracje + cudze posty) ===\n{schowek[:2000]}\n\n"
                   f"=== TOP PUBLIKACJE TYGODNIA (kontekst, nie powielaj) ===\n{top[:1500]}\n\n"
                   f"Pisz NIENAGANNA polszczyzna, zwiezle."}])
    tasks.log_task("sunday_synth", tier, model, source, getattr(resp, "usage", None))
    txt = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text").strip()
    return txt


def _do_send(job_id, has_research):
    """Zawsze COS wysyla (podklad albo jasny komunikat), zeby cykl sie domknal bez spamu ponowien."""
    body = _synthesize(job_id, has_research)
    if not body:
        _send_long("📰 Podklad pod niedzielny artykul: nie udalo sie zsyntetyzowac tresci "
                   "(pusta odpowiedz modelu). Napisz do CM 'podklad na niedziele', ponowie.")
        return
    src_note = "" if has_research else "\n\n⚠️ Research swiata nie dojechal - podklad zbudowany ze " \
                                      "schowka i publikacji. Fakty zewnetrzne oznaczone '(do weryfikacji)'."
    header = ("📰 PODKLAD POD NIEDZIELNY ARTYKUL (insight tygodnia ze swiata AI)\n"
              "Draft do Twojej recznej obrobki - NIC nie wchodzi do planu ani kolejki.\n"
              "----------------------------------------")
    _send_long(f"{header}\n\n{body}{src_note}")


# ---------------- maszyna stanu ----------------
# Stan (brand_config cm_sunday_brief): {week, phase, job_id, requested_at, manual, auto_done, attempts}.
# auto_done = automatyczny (sobotni) podklad dostarczony za `week`. KLUCZOWE: reczny tap-test NIE zajmuje
# slotu automatu (auto_done zostaje), zeby sobotni podklad wyszedl mimo wczesniejszego testu w tym tygodniu.
def _in_request_window(now):
    return now.weekday() == 5 and REQUEST_FROM_MIN <= (now.hour * 60 + now.minute) < REQUEST_UNTIL_MIN


def _request(week, manual, preserve_auto_done):
    """Zlecenie badania Researcherowi (kontrakt /request; correlation = deterministyczny uuid tygodnia).
    Tier: auto po stronie Researchera, CM capped <=medium (guard). Zwraca True gdy zakolejkowano."""
    corr = _correlation(week)
    code, resp = research.request_research({"id": str(corr)}, SUNDAY_QUERY)
    job_id = (resp or {}).get("job_id")
    base = {"week": week, "manual": bool(manual), "auto_done": bool(preserve_auto_done)}
    if code == 202 and job_id:
        base.update(phase="polling", job_id=job_id,
                    requested_at=datetime.datetime.now(WARSAW).isoformat())
        _state_set(STATE_KEY, base)
        return True
    # nie udalo sie zakolejkowac (Researcher niedostepny/limit) - zapisz probe, ponow w nastepnym ticku
    st = _state_get(STATE_KEY)
    base.update(phase="request_failed", attempts=int(st.get("attempts") or 0) + 1,
                last_err=(resp or {}).get("error", str(code)))
    _state_set(STATE_KEY, base)
    return False


def tick():
    """Wolane z petli workera (30s). Anty-spam: jeden automatyczny podklad / tydzien ISO (auto_done).
    Sciezka reczna (manual) dziala kazdego dnia i nie blokuje sobotniego automatu."""
    now = datetime.datetime.now(WARSAW)
    week = now.strftime("%G-%V")
    minutes = now.hour * 60 + now.minute
    st = _state_get(STATE_KEY)
    manual = bool(st.get("manual"))
    auto_done_week = bool(st.get("week") == week and st.get("auto_done"))

    # 1) cykl w locie: polling wyniku (dziala niezaleznie od dnia - obejmuje tap-test)
    if st.get("phase") == "polling" and st.get("job_id"):
        status = research.job_status(st["job_id"])
        ready = status in RESEARCHER_DONE
        dead = status in RESEARCHER_DEAD
        try:
            waited = (now - datetime.datetime.fromisoformat(st["requested_at"])).total_seconds()
        except Exception:
            waited = 0
        if manual:
            force = dead or waited >= MANUAL_FALLBACK_S
            gate_ok = True                      # tap-test: wysylaj gdy tylko gotowe
        else:
            force = (now.weekday() == 5 and minutes >= SEND_FORCE_MIN) or dead
            gate_ok = minutes >= SEND_FLOOR_MIN or force
        if (ready and gate_ok) or force:
            _do_send(st["job_id"], has_research=ready)
            _state_set(STATE_KEY, {"week": week, "phase": "sent", "job_id": st["job_id"],
                                   "sent_at": now.isoformat(), "manual": False,
                                   "auto_done": auto_done_week or (not manual)})
        return

    # 2) ponow nieudane zlecenie (natychmiast dla manual, inaczej w oknie soboty)
    if st.get("phase") == "request_failed":
        if manual or _in_request_window(now):
            _request(week, manual=manual, preserve_auto_done=auto_done_week)
        return

    # 3) automatyczne zlecenie w sobotni poranek (jesli automat jeszcze nie ruszyl w tym tygodniu)
    if _in_request_window(now) and not auto_done_week:
        _request(week, manual=False, preserve_auto_done=auto_done_week)


def trigger_manual(chat_id=None):
    """TAP-TEST / na zadanie: zlec badanie teraz i zapowiedz podklad (dojdzie gdy research gotowy,
    ta sama sciezka co produkcja). Ignoruje bramke dnia/godziny; NIE kasuje sobotniego automatu."""
    now = datetime.datetime.now(WARSAW)
    week = now.strftime("%G-%V")
    st = _state_get(STATE_KEY)
    auto_done_week = bool(st.get("week") == week and st.get("auto_done"))
    ok = _request(week, manual=True, preserve_auto_done=auto_done_week)
    if ok:
        return ("📡 Zlecilem Researcherowi badanie swiata AI z ostatnich 7 dni (podklad pod niedzielny "
                "artykul). Gdy wyniki dojada, przyslę Ci 3 kandydackie tezy z faktami i linkami zrodel. "
                "Zwykle kilka minut. Nic nie wchodzi do planu ani kolejki.")
    return ("⚠️ Nie udalo sie teraz zlecic badania Researcherowi (moze byc chwilowo niedostepny). "
            "Sprobuje ponownie automatycznie; mozesz tez powtorzyc za chwile.")
