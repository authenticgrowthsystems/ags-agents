"""CM worker: FastAPI (/health /metrics /request /plan /message) + a state-machine loop over content_items.
Event-driven: /request, /plan and /message wake the loop; a 30s poll is the backstop. Mirrors the Researcher
worker. /message = the CM Brain conversation entry (n8n HITL forwards Telegram text here)."""
import datetime
import threading
import traceback

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from . import config, db
from .brand import load_brand

from . import generate, compliance, channels, research, hitl, conversation, logbot, content_memory, reports, planner, matreview, slots, proactive, engagement, metrics_import, decisions, sunday_brief, sales, teczka

api = FastAPI(title="AGS Content Manager")
wake = threading.Event()


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------- FastAPI ----------------
@api.get("/health")
def health():
    try:
        db.fetchone("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@api.get("/metrics")
def metrics():
    return db.fetchone(
        """SELECT
             (SELECT COUNT(*) FROM content_items WHERE status='published' AND updated_at > NOW()-interval '24 hours') AS published_24h,
             (SELECT COUNT(*) FROM content_items WHERE status='needs_approval') AS awaiting_approval,
             (SELECT COUNT(*) FROM content_items WHERE status = ANY(%s)) AS active""",
        (list(config.ACTIONABLE_STATUSES),),
    ) or {}


def _guard(secret):
    if not config.RESEARCHER_WEBHOOK_SECRET or secret != config.RESEARCHER_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")


@api.post("/request", status_code=202)
def request_content(body: dict, x_researcher_secret: str = Header(default="")):
    """Create a content_item (from Manager / idea-bot / any caller) and wake the loop. Same async contract +
    guard as the Researcher. Returns 202 {content_item_id}; the result flows via HITL + dispatch."""
    _guard(x_researcher_secret)
    brand_id = str(body.get("brand_id") or "AGS").strip()
    theme = str(body.get("master_theme") or body.get("theme") or "").strip()
    if not theme:
        raise HTTPException(status_code=400, detail="master_theme required")
    targets = body.get("target_channels") or ["x"]
    status = "needs_research" if body.get("needs_research") else "planned"
    row = db.fetchone(
        """INSERT INTO content_items (brand_id, master_theme, taxonomy, target_channels, status, inspiration_id)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
        (brand_id, theme, body.get("taxonomy"), list(targets), status, body.get("inspiration_id")),
    )
    wake.set()
    return {"accepted": True, "content_item_id": str(row["id"])}


@api.post("/plan", status_code=202)
def plan(body: dict, x_researcher_secret: str = Header(default="")):
    """FAZA 2: proaktywny planer (cron niedziela 20:15 / na zadanie). Buduje propozycje tygodnia w tle."""
    _guard(x_researcher_secret)
    brand_id = str(body.get("brand_id") or "AGS").strip()
    threading.Thread(target=planner.build_plan, args=(brand_id,), daemon=True).start()
    wake.set()
    return {"accepted": True, "planner": True}


@api.post("/reports/{kind}", status_code=202)
def run_reports(kind: str, x_researcher_secret: str = Header(default="")):
    """Cron entrypoint (n8n): daily 08:00 / weekly niedziela 20:00 Europe/Warsaw. Raport per supervised cel."""
    _guard(x_researcher_secret)
    if kind not in ("daily", "weekly"):
        raise HTTPException(status_code=400, detail="kind must be daily|weekly")
    threading.Thread(target=reports.run_all, args=(kind,), daemon=True).start()
    return {"accepted": True, "kind": kind}


@api.post("/plannav", status_code=202)
def plannav(body: dict, x_researcher_secret: str = Header(default="")):
    """Nawigacja zatwierdzania planu (guziki plannav: z HITL; n8n = czysty transport)."""
    _guard(x_researcher_secret)
    threading.Thread(target=planner.handle_nav, args=(body, wake), daemon=True).start()
    return {"accepted": True}


@api.post("/matnav", status_code=202)
def matnav(body: dict, x_researcher_secret: str = Header(default="")):
    """Decyzje intake (matdec:) + karty materialow (matnav:) - feedback 05/07 (galaz mat* w HITL)."""
    _guard(x_researcher_secret)
    threading.Thread(target=matreview.handle, args=(body, wake), daemon=True).start()
    return {"accepted": True}


@api.post("/cmt", status_code=202)
def cmt(body: dict, x_researcher_secret: str = Header(default="")):
    """Decyzje dla propozycji komentarzy (guziki cmt:ok|angle|no) - zapis w engagement_log,
    zatwierdzone dodatkowo do task_queue 'comment'. Wymog Tomasza 08/07."""
    _guard(x_researcher_secret)
    threading.Thread(target=conversation.handle_cmt, args=(body, wake), daemon=True).start()
    return {"accepted": True}


@api.post("/decnav", status_code=202)
def decnav(body: dict, x_researcher_secret: str = Header(default="")):
    """Guziki decyzji ustrukturyzowanych (kanon 19/07: eskalacja GUZIKAMI + nauka do
    agent_learning_log + progi semi_autonomous). n8n galaz dec: -> {raw, chat_id, message_id}."""
    _guard(x_researcher_secret)
    threading.Thread(target=decisions.handle, args=(body, wake), daemon=True).start()
    return {"accepted": True}


@api.post("/docmsg", status_code=202)
def docmsg(body: dict, x_researcher_secret: str = Header(default="")):
    """Dokument tekstowy (.md/.txt) z Telegrama -> rozmowa aktywnego agenta (task 19/07:
    sync-dokumenty przepadaly w 'other'). n8n galaz document_text przekazuje {chat_id, file_id,
    file_name, caption}."""
    _guard(x_researcher_secret)
    if not body.get("file_id"):
        raise HTTPException(status_code=400, detail="file_id required")
    threading.Thread(target=conversation.handle_document, args=(body,), daemon=True).start()
    return {"accepted": True}


@api.post("/metrics/xlsx", status_code=202)
def metrics_xlsx(body: dict, x_researcher_secret: str = Header(default="")):
    """Import metryk LinkedIn z eksportu AggregateAnalytics (plan dnia 19/07 krok [1]).
    n8n HITL (galaz document) przekazuje {chat_id, file_id, file_name}; parsowanie i paragon w tle."""
    _guard(x_researcher_secret)
    if not body.get("file_id"):
        raise HTTPException(status_code=400, detail="file_id required")
    threading.Thread(target=metrics_import.handle_telegram_xlsx, args=(body,), daemon=True).start()
    return {"accepted": True}


@api.post("/wake", status_code=202)
def wake_up(x_researcher_secret: str = Header(default="")):
    """Kontrakt event-driven agent->agent (kanon 28/06, domkniecie 10/07): kazdy agent/workflow,
    ktory zapisal cos dla CM do DB (agent_messages, task_queue, post_queue callback), woła ten
    endpoint i budzi petle NATYCHMIAST. DB zostaje ledgerem, poll 30s = wolny backstop, nie sciezka."""
    _guard(x_researcher_secret)
    wake.set()
    return {"accepted": True}


@api.post("/message", status_code=202)
def message(body: dict, x_researcher_secret: str = Header(default="")):
    """Conversation entry: n8n HITL forwards a Telegram text {chat_id, text, update_id}. Returns 202
    immediately; a background thread runs the ConversationRouter and replies via sendMessage directly."""
    _guard(x_researcher_secret)
    if not body.get("chat_id"):
        raise HTTPException(status_code=400, detail="chat_id required")
    threading.Thread(target=conversation.handle, args=(body,), daemon=True).start()
    return {"accepted": True}


# ------------- Lacznik Etap 2: narzedzia czatu na abonamencie (BRIEF_LACZNIK_ETAP2_22072026) -------------
def _lacznik_guard(secret):
    """Sekret lacznik_e2_secret czytany z app_secrets (SSOT sekretow; rotacja = UPDATE w DB,
    bez rebuildu). Brak klucza w DB = endpointy zamkniete (brief pkt 2: NIE wystawiac bez sekretu)."""
    row = db.fetchone("SELECT value FROM app_secrets WHERE key='lacznik_e2_secret'")
    expected = ((row or {}).get("value") or "").strip()
    if not expected or (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@api.get("/lacznik/stan")
def lacznik_stan(scope: str = "all", x_lacznik_secret: str = Header(default=""), secret: str = ""):
    """Narzedzie stan_gry dla czatu na abonamencie (MCP w n8n / webhook wariantu B): stan gry
    jako markdown, synchronicznie (zero LLM - czysty reports.kontekst_text). Zastepuje czytanie
    Notion w rytuale startowym; strona Notion zostaje lustrem i fallbackiem. Sekret w naglowku
    X-Lacznik-Secret albo w query ?secret= (webhook wariantu B)."""
    _lacznik_guard(x_lacznik_secret or secret)
    try:
        return {"ok": True, "stan": reports.kontekst_text((scope or "all").strip().lower())}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:200]}")


@api.post("/lacznik/raport")
def lacznik_raport(body: dict, x_lacznik_secret: str = Header(default=""), secret: str = ""):
    """Narzedzie wyslij_raport_pracy: blok [RAPORT PRACY v1] prosto z czatu -> ISTNIEJACY parser
    (engagement.apply_work_report, idempotencja sync:<hash>) -> potwierdzenie z licznikami wraca
    W ODPOWIEDZI HTTP (czat je streszcza Tomaszowi), a KOPIA idzie do Telegrama - ten sam slad,
    co przy recznej wklejce. Synchronicznie: parser jest deterministyczny i szybki (zero LLM)."""
    _lacznik_guard(x_lacznik_secret or secret)
    raport = str(body.get("raport") or body.get("raport_md") or body.get("text") or "").strip()
    if "[raport pracy" not in raport.lower():
        raise HTTPException(status_code=400,
                            detail="raport musi zawierac blok [RAPORT PRACY v1] (naglowek + linie akcji)")
    kanal = str(body.get("kanal") or "").strip().lower()
    active = f"subagent:AGS:{kanal}" if kanal else None
    chat = hitl._admin_chat_id()
    potwierdzenie = engagement.apply_work_report(chat, raport, active_agent=active)
    if chat:
        try:
            conversation._reply(chat, "🔗 Lacznik (raport z czatu):\n" + potwierdzenie)
        except Exception:
            traceback.print_exc()
    wake.set()
    return {"ok": True, "potwierdzenie": potwierdzenie}


# ---- Teczka prospekta (31/07/2026): para zapisz_tekst + teczka, JEDEN kontrakt (app/teczka.py) ----
# Powod: teksty sprzedazowe pisane w Cowork ladowaly wylacznie w czacie - zero sladu w bazie,
# nie dalo sie iterowac ani wczytac w nowej rozmowie. Oba endpointy stoja za tym samym guardem
# co reszta Lacznika i sa synchroniczne (zero LLM - czysty SQL).
@api.post("/lacznik/zapisz-tekst")
def lacznik_zapisz_tekst(body: dict, x_lacznik_secret: str = Header(default=""), secret: str = ""):
    """Zapisuje tekst przy kontakcie, z data i statusem. Nieznany identyfikator = blad z lista
    podobnych, NIGDY ciche zalozenie nowego wiersza."""
    _lacznik_guard(x_lacznik_secret or secret)
    try:
        return {"ok": True, "potwierdzenie": teczka.zapisz(
            body.get("contact_id") or body.get("kontakt") or body.get("ident"),
            body.get("kanal"), body.get("tresc"), body.get("status") or "draft",
            next_step=body.get("next_step"), next_step_date=body.get("next_step_date"),
            temat=body.get("temat"), katalog=body.get("katalog"))}
    except teczka.Blad as e:
        # 400 z trescia DLA CZLOWIEKA: czat ma pokazac liste podobnych, a nie "bad request".
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:200]}")


@api.get("/lacznik/teczka")
def lacznik_teczka(kontakt: str = "", x_lacznik_secret: str = Header(default=""), secret: str = ""):
    """Cala teczka w JEDNYM wywolaniu: dane kontaktu, chronologia wszystkiego co poszlo,
    ostatni ustalony nastepny krok z data, status."""
    _lacznik_guard(x_lacznik_secret or secret)
    try:
        return {"ok": True, "teczka": teczka.teczka_text(kontakt)}
    except teczka.Blad as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:200]}")


def _brand_tokens_tick():
    """#84: lazy import (modul sync/ ma zaleznosci ladowane przy starcie notion_workera)."""
    from .sync import brand_tokens_pull
    brand_tokens_pull.tick()


def _x_collector_tick():
    """BRIEF_KOLEKTOR_METRYK_X 19/07: dzienne snapshoty metryk wlasnych postow X (Owned Reads
    $0.001/read). Spi dopoki zaden cel nie ma stats_mode='x_owned_reads' (wlaczenie PO sondzie)."""
    from . import x_collector
    x_collector.tick()


# ---------------- state machine ----------------
def _auto_generate_image(item, brand, hint, media):
    """KANON 25/07 (feedback Tomasza POWTORZONY - [[feedback_grafiki_tylko_prompty]]):
    ZADNYCH auto-generowanych OBRAZOW dopoki nie ma dedykowanego Agenta Wizualnego. Auto-grafika
    gpt-image wychodzila slabo, a slaba grafika szkodzi marce bardziej niz jej brak. Zamiast obrazu
    dolaczamy SZCZEGOLOWY PROMPT - Tomasz generuje grafike recznie w swoim narzedziu.

    Gdy sugestia wizualu to grafika (nie zdjecie/wideo - to i tak zadanie czlowieka), dolaczamy
    do materialu pelny prompt (kind='visual_prompt'); karta pokaze go jako propozycje do skopiowania.
    Zero kosztu gpt-image, zero wysylki obrazu. Guzik 🎨 Generuj NA ZADANIE zostaje osobno."""
    if not (hint and generate.hint_wants_generated_graphic(hint)):
        return media
    if any((m or {}).get("file_id") for m in media):
        return media  # material ma juz zalacznik (np. zdjecie Tomasza) - nie dokladamy nic
    if any((m or {}).get("kind") == "visual_prompt" for m in media):
        return media  # prompt juz dolaczony (regeneracja) - nie dublujemy
    try:
        prompt = generate.generate_image_prompt(brand, item["master_theme"], item.get("canonical_body"),
                                                hint, content_item_id=item["id"])
        media = media + [{"kind": "visual_prompt", "text": prompt[:3400], "image_prompt": prompt[:3400]}]
        print(f"[cm] visual prompt attached to {item['id']} (recznie, bez auto-obrazu)", flush=True)
    except Exception:
        traceback.print_exc()  # brak promptu nie blokuje materialu - karta przyjdzie bez niego
    return media


def _draft(item):
    brand = load_brand(item["brand_id"])
    ctx = research.research_context(item.get("research_job_id"))
    canonical, _ = generate.generate_canonical(brand, item["master_theme"], ctx, content_item_id=item["id"])
    canonical = compliance.enforce(brand, canonical, content_item_id=item["id"])
    targets = channels.active_targets(item["brand_id"], item.get("target_channels"))
    # sugestia wizualu per material (06/07); podmiana starej sugestii przy regeneracji
    try:
        hint = generate.generate_media_hint(brand, canonical, content_item_id=item["id"])
        # AP-315: znacznik zatrzymania odchodzi razem ze stara trescia. Tekst pisany od nowa
        # jest NOWYM tekstem, wiec nie moze dziedziczyc zgody wydanej na poprzedni.
        media = [m for m in (item.get("media") or [])
                 if (m or {}).get("kind") not in ("suggestion", "dup_warning", _AP315_KIND) and not str((m or {}).get("kind", "")).startswith("review_")]
        if hint:
            media.append({"kind": "suggestion", "text": hint})
        # BRAMKA DUPLIKACJI (kanon 19/07): TEMAT vs OPUBLIKOWANE (30 dni, pgvector) -> ostrzezenie
        # na karcie. NIE blokuje - decyzja ZAWSZE u Tomasza. Bez klucza/dopasowania = brak flagi.
        # KALIBRACJA 20/07 (pomiar na zywym korpusie): pelny canonical NIE separuje (blizniak 0.536
        # vs nie-blizniaki do 0.588 - dlugi tekst w stylu domowym rozmywa teze); master_theme separuje
        # (blizniaki 0.60-0.63 vs reszta <0.552). Prog w brand_config cm_dup_threshold = 0.57.
        try:
            from . import content_memory
            hit = content_memory.dup_check(item.get("master_theme") or canonical, item["brand_id"])
            wtext = content_memory.dup_warning_text(hit)
            if wtext:
                media.append({"kind": "dup_warning", "text": wtext})
                print(f"[cm] dup_warning on {item['id']}: {wtext}", flush=True)
        except Exception:
            traceback.print_exc()  # bramka informacyjna nie moze wywrocic generacji
        # 10/07: sugestia typu GRAFIKA -> obraz generuje sie od razu (karta przychodzi z grafika)
        item["canonical_body"] = canonical
        media = _auto_generate_image(item, brand, hint, media)
        # T8 (feedback 07/08): kopia PL do przegladu, gdy publikacja idzie w innym jezyku niz komunikacja.
        # Native EN publikuje; PL trzymamy obok (kind='review_pl'), zeby Tomasz czytal/edytowal po polsku.
        try:
            from .conversation import language_comm
            comm = language_comm()
            pubs = {generate._language_publish(item["brand_id"], t["channel"]) for t in targets}
            if comm and any(p != comm for p in pubs):
                review = generate.translate_text(canonical, comm, content_item_id=item["id"])
                if review:
                    # Kopia do przegladu to TEN tekst, ktory czlowiek czyta, zatwierdzajac -
                    # wiec gdy rozjezdza sie ze zrodlem, musi to byc widoczne NA KARCIE, a nie
                    # tylko w logu. Inaczej bramka ludzka ocenia nie ten tekst (AP-315).
                    uwagi = generate.sprawdz_przeklad(canonical, review)
                    if uwagi:
                        review += ("\n\n⚠️ TA KOPIA ROZJECHALA SIE ZE ZRODLEM: "
                                   + "; ".join(uwagi)
                                   + ".\nOceniaj po tekscie, ktory WYCHODZI, nie po tej kopii.")
                    media.append({"kind": f"review_{comm}", "text": review})
        except Exception:
            traceback.print_exc()
        import json as _json
        db.execute("UPDATE content_items SET media=%s::jsonb, updated_at=NOW() WHERE id=%s",
                   (_json.dumps(media), item["id"]))
        item["media"] = media
    except Exception:
        traceback.print_exc()
    variants = []
    for ch in targets:
        vtext, _ = generate.generate_variant(brand, canonical, ch["channel"], content_item_id=item["id"])
        vtext = compliance.enforce(brand, vtext, content_item_id=item["id"], channel=ch["channel"])
        channels.stage_variant(item, ch, vtext)
        variants.append((ch["channel"], vtext))
    db.set_item_status(item["id"], "needs_approval", canonical_body=canonical, voice_hash=brand["voice_hash"])
    hitl.send_approval(item, variants)
    return f"needs_approval({len(variants)} variants)"


def process_item(item):
    st = item["status"]
    if st == "needs_research":
        code, resp = research.request_research(item, item["master_theme"])
        job_id = (resp or {}).get("job_id")
        if code == 202 and job_id:
            db.set_item_status(item["id"], "researching", research_job_id=job_id)
            return "researching"
        return _draft(item)  # research could not be enqueued -> draft without it
    if st in ("planned", "drafting"):
        return _draft(item)
    if st == "approved":
        # decyzja Tomasza 06/07: Tomasz zatwierdza TRESC, CM proponuje KIEDY. Slot NULL/miniony
        # NIE publikuje natychmiast - CM przydziela najblizszy wolny wg okien+kadencji i melduje.
        slot, changed, realny = slots.assign_if_needed(item)
        if changed and slot:
            # Zgloszenie Tomasza 03/08: meldunek ma podawac godzine, o ktorej post NAPRAWDE
            # wyjdzie. Poprawka z 03/08 (d5cd43e) podawala czas z KOLEJKI i byla dobra tylko
            # w polowie przypadkow - domkniecie 10/08, patrz _godzina_publikacji.
            kiedy = _godzina_publikacji(slot, realny)
            logbot.send(f"🗓 CM przydzielil slot: {kiedy.strftime('%a %d/%m %H:%M')} - "
                        f"{item['master_theme'][:70]} (zmiana? napisz do CM: 'przesun na ...')")
            return f"slot_assigned({kiedy:%d/%m %H:%M})"
        # AP-315 (10/08): OSTATNIA bramka przed swiatem. Tedy przechodzi KAZDA publikacja -
        # takze material zatwierdzony guzikiem w n8n z pominieciem cm-agenta - wiec to jedyne
        # miejsce, ktore widzi wszystko. Bezpiecznik NIE poprawia tekstu: zawraca material do
        # czlowieka i mowi glosno, ktora fraza go zatrzymala. Sprawdzany jest WIERSZ KOLEJKI,
        # bo publikuje sie wariant, a nie canonical_body.
        zle = channels.sprawdz_gatunek(item)
        if zle:
            # Bez furtki, gdy CHOCBY JEDEN wiersz na to zasluguje - kazdy wiersz to osobny
            # tekst, ktory wyjdzie osobno. Fraza twarda albo nagromadzenie miekkich; regula
            # i progi siedza w compliance, zeby dalo sie je pokazac przy pracy.
            bez_wyjscia = any(compliance.bez_furtki(z["twarde"], z["miekkie"]) for z in zle)
            # Odcisk SORTOWANY: zapytanie o wiersze nie ma ORDER BY, wiec bez sortowania
            # dwa przebiegi na tych samych danych dalyby dwa rozne odciski i furtka
            # "drugie zatwierdzenie" nigdy by sie nie otworzyla.
            odcisk = ";".join(sorted(z["odcisk"] for z in zle))
            if bez_wyjscia or _znacznik_ap315(item) != odcisk:
                db.set_item_status(item["id"], "needs_approval",
                                   media=_media_ze_znacznikiem(item, odcisk))
                logbot.send(_meldunek_bezpiecznika(item, zle, bez_wyjscia))
                return f"zablokowany_gatunek({'bez_furtki' if bez_wyjscia else 'miekkie'},{len(zle)})"
            # Tylko miekkie i DOKLADNIE ten sam tekst, ktory czlowiek widzial w meldunku wraz
            # z nazwa frazy. Przepuszczamy, ale glosno - to nie moze wygladac jak zwykla publikacja.
            logbot.send(_ostrzezenie_ap315(item, zle))
        # backlog b: dispatch = HAND-OFF, nie publikacja. Item przechodzi w STATUS_HANDED_OFF
        # (poza ACTIONABLE), a reconcile_publications zamelduje realny sukces/porazke po callbacku.
        # D-008: to JEDYNY w calym systemie pisarz tej wartosci - stad migracja da sie domknac
        # zatrzymaniem pisarzy zamiast szukania "mniej szkodliwej kolejnosci".
        db.set_item_status(item["id"], config.STATUS_HANDED_OFF)
        handoff = channels.dispatch_item(item)
        logbot.send(_dispatch_ack(item, handoff))
        return f"{config.STATUS_HANDED_OFF}({len(handoff)})"
    return "noop"


# ---------------- backlog b: meldunek po CALLBACKU (nie przy delegacji) ----------------
# Slownik statusow post_queue: w locie / terminalny-OK / terminalny-porazka. Nieznany status = traktuj
# jak 'w locie' (konserwatywnie - timeout alert zlapie realny zwis, np. X media_errors).
# D-008: to jest slownik KOLEJKI, nie materialu. 'dispatching' ponizej ZOSTAJE - post_queue ma
# wlasna wartosc o tej nazwie i znaczy ona co innego (jeden wiersz oddany subagentowi).
# _DISPATCH_OK zawiera 'held' (gotowiec do recznej wklejki), wiec stan materialu konczy sie tez
# BEZ publikacji - dlatego material nazywa sie handed_off, a nie awaiting_publication.
_DISPATCH_PENDING = ("review", "dispatching", "scheduled", "queued")
_DISPATCH_OK = ("published", "held")
_DISPATCH_FAIL = ("failed", "error", "rejected")


def _chan_label(brand_id, platform):
    try:
        return planner._target_label(brand_id, platform)
    except Exception:
        return platform


def _godzina_publikacji(slot, realny):
    """D-015, domkniecie 10/08: godzina, o ktorej post NAPRAWDE wyjdzie, to MAX z dwoch liczb -
    slotu planu i czasu kolejki. Nie jedna z nich na stale.

    DLACZEGO. Publikacje pilnuja DWIE niezalezne bramki, obie z warunkiem "<= NOW()":
      1) `db.claim_item`: material `approved` z PRZYSZLYM `content_items.scheduled_for` NIE jest
         w ogole brany przez petle. To trzyma go do SLOTU PLANU.
      2) Scheduler n8n: publikuje `post_queue WHERE status='scheduled' AND scheduled_for <= NOW()`.
         Wiersz staje sie 'scheduled' dopiero w dispatchu, czyli PO otwarciu bramki nr 1.
    Wynika z tego, ze czas kolejki liczy sie tylko wtedy, gdy jest POZNIEJSZY niz slot planu.
    Gdy `humanize_slot` wylosuje wczesniej (a losuje symetrycznie +/-15 min, wiec w polowie
    przypadkow), ta wczesniejsza godzina jest MARTWA - bramka nr 1 i tak trzyma material.

    DOWOD, NIE TEORIA (10/08, dwa na dwa):
      #344  kolejka 15:49, slot planu 16:00  ->  opublikowane 04/08 **16:01**
      #358  kolejka 15:50, slot planu 16:00  ->  opublikowane 05/08 **16:01**
    Poszlaka potwierdzajaca: WSZYSTKIE zaobserwowane publikacje (13:48, 16:10, 16:31, 16:59,
    17:48, 19:12, 20:23, 10:01) wypadaja PO najblizszym okraglym slocie, ani jedna przed.
    Przy losowaniu symetrycznym polowa powinna wypasc wczesniej - bramka nr 1 je zjada.

    Stad d5cd43e bylo poprawne dokladnie w polowie przypadkow, tak samo jak kod, ktory poprawialo:
    stary meldunek mylil sie o 15 minut, gdy kolejka wypadala pozniej; nowy mylil sie o 15 minut,
    gdy wypadala wczesniej. Prawdziwa odpowiedzia jest max, a nie wybor jednego ze zrodel.
    Sam tik Schedulera dokłada do minuty i tego celowo NIE dodajemy - meldunek ma podawac
    godzine, od ktorej post moze wyjsc, a nie udawac precyzje sekundowa."""
    if realny and slot and realny > slot:
        return realny
    return slot or realny


_AP315_KIND = "ap315_blok"


def _znacznik_ap315(item):
    """Odcisk tresci, ktora bezpiecznik zatrzymal POPRZEDNIM razem. Pusty napis = pierwszy raz.
    Znacznik siedzi w `media` materialu, bo ma przezyc powrot do needs_approval i tapniecie
    guzika w n8n - a te dwie drogi nie przechodza przez zadna pamiec cm-agenta."""
    for m in (item.get("media") or []):
        if (m or {}).get("kind") == _AP315_KIND:
            return str((m or {}).get("odcisk") or "")
    return ""


def _media_ze_znacznikiem(item, odcisk):
    """Jeden znacznik na material: stary leci, nowy wchodzi. Bez tego kazde zatrzymanie
    dokladaloby wpis i po kilku probach `media` bylby smietnikiem."""
    media = [m for m in (item.get("media") or []) if (m or {}).get("kind") != _AP315_KIND]
    return media + [{"kind": _AP315_KIND, "odcisk": odcisk}]


def _frazy_wiersza(z):
    czesci = []
    if z["twarde"]:
        czesci.append("TWARDE: " + ", ".join(z["twarde"]))
    if z["miekkie"]:
        czesci.append("miekkie: " + ", ".join(z["miekkie"]))
    return " | ".join(czesci)


def _meldunek_bezpiecznika(item, zle, bez_wyjscia):
    """AP-315: meldunek ma powiedziec CO zatrzymalo material, a nie ze "cos jest nie tak".
    Cichy powrot do needs_approval wygladalby jak zwykle czekanie na decyzje - a to jest
    zatrzymanie publikacji i Tomasz musi wiedziec, ze slot przepadnie.
    Fraza pada Z NAZWY celowo: to ona zamienia odruchowe tapniecie "zatwierdz" w swiadome."""
    lines = [f"🛑 BEZPIECZNIK GATUNKU zatrzymal publikacje: {item['master_theme'][:90]}",
             "   Tresc wyglada na NOTATKE O TRESCI, nie na tekst dla czlowieka."]
    for z in zle:
        lab = _chan_label(item["brand_id"], z["platform"])
        lines.append(f"   • {lab} (wiersz #{z['qid']}): {_frazy_wiersza(z)}")
    if bez_wyjscia and any(z["twarde"] for z in zle):
        lines.append("   Fraza TWARDA to nazwa naszej maszynerii - drugie zatwierdzenie NIC nie da. "
                     "Tekst trzeba napisac od nowa.")
    elif bez_wyjscia:
        # Nagromadzenie miekkich. Meldunek ma nazwac POWOD, bo inaczej brak furtki przy samych
        # "zwyklych slowach" wyglada na wade bezpiecznika, a nie na jego dzialanie.
        lines.append(f"   Fraz miekkich naraz: {max(len(z['miekkie']) for z in zle)}. Jedna to wybor "
                     "slowa, tyle naraz to gatunek - drugie zatwierdzenie NIC nie da. "
                     "Tekst trzeba napisac od nowa.")
    else:
        lines.append("   Jesli to swiadomy wybor slowa, zatwierdz TEN SAM tekst drugi raz - przejdzie. "
                     "Kazda zmiana tekstu liczy sie od nowa.")
    return "\n".join(lines)


def _ostrzezenie_ap315(item, zle):
    """Drugie zatwierdzenie miekkiej frazy. Publikacja idzie, ale slad ma zostac glosny -
    inaczej za miesiac nikt nie odtworzy, dlaczego to wyszlo mimo bezpiecznika."""
    frazy = sorted({f for z in zle for f in z["miekkie"]})
    return (f"⚠️ BEZPIECZNIK PRZEPUSZCZA na Twoje drugie zatwierdzenie: {item['master_theme'][:80]}\n"
            f"   Fraza miekka: {', '.join(frazy)}. Ten sam tekst, ktory zatrzymalem poprzednio.")


def _dispatch_ack(item, handoff):
    """Prawdziwy meldunek W MOMENCIE delegacji: 'wyslane/zaplanowane/czeka recznie' - NIE 'opublikowal'.
    Sukces potwierdza dopiero reconcile_publications po callbacku.
    22/07 (uwaga Tomasza: 5 identycznych linijek przy serii wygladalo jak blad systemu):
    wiersze grupowane per kanal, z liczba czesci i KONKRETNYMI slotami."""
    if not handoff:
        return f"⚠️ Nic do wyslania: {item['master_theme'][:80]} (brak wariantow w kolejce - sprawdz kanaly celu)."
    lines = [f"📤 CM wyslal do publikacji: {item['master_theme'][:90]}"]
    groups = {}
    order = []
    for h in handoff:
        k = (h["platform"], h["mode"])
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(h.get("queue_id"))
    for (plat, mode) in order:
        qids = [q for q in groups[(plat, mode)] if q]
        lab = _chan_label(item["brand_id"], plat)
        czesci = "" if len(qids) <= 1 else f" - SERIA {len(qids)} czesci"
        if mode == config.PUBLISH_POST_QUEUE:
            slots = db.fetchall(
                """SELECT to_char(scheduled_for AT TIME ZONE 'Europe/Warsaw', 'DD/MM HH24:MI') AS s
                   FROM post_queue WHERE id = ANY(%s) ORDER BY scheduled_for""", (qids,)) if qids else []
            stxt = ", ".join(r["s"] for r in slots if r.get("s"))
            lines.append(f"   • {lab}{czesci}: zaplanowane, Scheduler opublikuje w slotach: "
                         f"{stxt[:300] or 'wg harmonogramu'} (potwierdze kazda publikacje)")
        elif mode == config.PUBLISH_WEBHOOK:
            lines.append(f"   • {lab}{czesci}: zlecone subagentowi (potwierdze po jego callbacku)")
        else:
            lines.append(f"   • {lab}{czesci}: gotowiec czeka na Twoje reczne wklejenie")
    return "\n".join(lines)


def _publish_report(item, pq):
    """Meldunek PO potwierdzeniu: per-kanal opublikowane / czeka recznie / NIE POSZLO (surfacuje X media_errors)."""
    oks = [r for r in pq if r["status"] == "published"]
    held = [r for r in pq if r["status"] == "held"]
    fails = [r for r in pq if r["status"] in _DISPATCH_FAIL]
    parts = []
    if oks:
        parts.append("✅ opublikowane: " + ", ".join(_chan_label(item["brand_id"], r["platform"]) for r in oks))
    if held:
        parts.append("📋 czeka na reczne wklejenie: " + ", ".join(_chan_label(item["brand_id"], r["platform"]) for r in held))
    if fails:
        parts.append("⚠️ NIE POSZLO: " + ", ".join(_chan_label(item["brand_id"], r["platform"]) for r in fails)
                     + " - sprawdz egzekucje Publishera/Schedulera (media_errors?)")
    head = ("⚠️ CM: publikacja z problemem" if fails else
            ("✅ CM opublikowal" if oks else "📋 CM: gotowiec do wklejenia"))
    return f"{head}: {item['master_theme'][:90]}\n   " + "\n   ".join(parts)


def _dispatch_alert_state():
    r = db.fetchone("SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='cm_dispatch_alerted'")
    try:
        import json as _json
        return _json.loads(r["config_value"]) if r and r.get("config_value") else {}
    except Exception:
        return {}


def _dispatch_alert_set(obj):
    import json as _json
    db.execute(
        """INSERT INTO brand_config (brand_id, config_key, config_value, version, updated_by, updated_at)
           VALUES ('AGS','cm_dispatch_alerted',%s,1,'cm-worker',NOW())
           ON CONFLICT (brand_id, config_key) DO UPDATE SET config_value=EXCLUDED.config_value,
             version=brand_config.version+1, updated_by='cm-worker', updated_at=NOW()""",
        (_json.dumps(obj, ensure_ascii=False),))


def _dispatch_timeout_alert(item, pending):
    """Zwis publikacji liczony OD SLOTU WIERSZA (A6, 21/07): wiersz z przyszlym slotem nie jest
    zwisem - alarm dopiero gdy slot minal o DISPATCH_TIMEOUT_H bez stanu terminalnego.
    (Stara wersja liczyla od dispatchu materialu i alarmowala o 15:15 o postach ze slotami
    na 20:10/21:57 - falszywe alarmy ucza ignorowania prawdziwych.)"""
    now = _now()
    overdue = []
    for r in pending:
        ref = r.get("scheduled_for") or item.get("updated_at")
        if not ref:
            continue
        try:
            if (now - ref).total_seconds() / 3600.0 >= config.DISPATCH_TIMEOUT_H:
                overdue.append(r)
        except Exception:
            continue
    if not overdue:
        return
    st = _dispatch_alert_state()
    ids = st.get("ids", [])
    if str(item["id"]) in ids:
        return
    st["ids"] = (ids + [str(item["id"])])[-100:]
    _dispatch_alert_set(st)
    chans = ", ".join(sorted({_chan_label(item["brand_id"], r["platform"]) for r in overdue}))
    logbot.send(f"⏱️ ZWIS PUBLIKACJI (slot minal >{config.DISPATCH_TIMEOUT_H:.0f} h temu): "
                f"{item['master_theme'][:80]}\n"
                f"   Po slocie bez potwierdzenia: {chans}. Sprawdz egzekucje Schedulera/Publishera (media_errors?).")


def reconcile_publications():
    """backlog b: awansuj STATUS_HANDED_OFF -> 'published' DOPIERO gdy wiersze post_queue osiagnely
    stan terminalny (realny callback Schedulera/subagenta), i DOPIERO WTEDY meldunek - z porazkami
    wlacznie. Optymistyczny 'opublikowal' przy delegacji ukrywal nieudane publikacje X (media_errors)."""
    rows = db.fetchall(
        "SELECT id, brand_id, master_theme, updated_at FROM content_items WHERE status=%s",
        (config.STATUS_HANDED_OFF,))
    for item in rows:
        pq = db.fetchall(
            "SELECT id, platform, status, content, media, scheduled_for FROM post_queue WHERE content_item_id=%s",
            (item["id"],))
        if not pq:
            continue  # nic nie zdazylo trafic do kolejki - nastepny tick
        pending = [r for r in pq if r["status"] not in (_DISPATCH_OK + _DISPATCH_FAIL)]
        if pending:
            _dispatch_timeout_alert(item, pending)
            continue
        db.set_item_status(item["id"], "published")
        logbot.send(_publish_report(item, pq))
        _send_manual_paste_kits(item, pq)  # A4 (21/07): gotowiec held z TRESCIA do rozmowy Tomasza
        print(f"[cm] reconciled -> published {item['id']}", flush=True)


def _send_manual_paste_kits(item, pq):
    """A4 (21/07, incydent #194): wiersz 'held' (tryb draft, np. LinkedIn profil) = gotowiec do
    RECZNEJ wklejki. Dotad szla tylko notka na kanal logowy - Tomasz nie mial CZEGO wkleic i post
    nie wychodzil. Teraz: pelna tresc + grafika ida do glownej rozmowy, domkniecie deterministyczna
    komenda 'wklejone <id>' (route w conversation)."""
    held = [r for r in pq if r["status"] == "held"]
    if not held:
        return
    try:
        chat = hitl._admin_chat_id()
    except Exception:
        chat = None
    if not chat:
        return
    for r in held:
        try:
            lab = _chan_label(item["brand_id"], r["platform"])
            conversation._tg("sendMessage", {
                "chat_id": chat,
                "text": (f"📋 GOTOWIEC DO WKLEJENIA ({lab}) - {item['master_theme'][:80]}\n"
                         f"Ponizej czysta wklejka. Po opublikowaniu odpisz: wklejone {r['id']}"),
                "disable_web_page_preview": True})
            conversation._tg("sendMessage", {"chat_id": chat, "text": (r.get("content") or "")[:4096],
                                             "disable_web_page_preview": True})
            media = r.get("media") or []
            if isinstance(media, str):
                import json as _json
                try:
                    media = _json.loads(media)
                except Exception:
                    media = []
            for m in media:
                if isinstance(m, dict) and m.get("file_id"):
                    conversation._tg("sendPhoto", {"chat_id": chat, "photo": m["file_id"],
                                                   "caption": f"grafika do wklejki #{r['id']}"})
                    break
        except Exception:
            traceback.print_exc()


def _welcome_new_channels():
    """Hook R5 (open/closed): swiezo aktywowany kanal (bez znacznika welcomed) dostaje od CM propozycje
    adaptacji najlepszych publikacji z archiwum. Znacznik w channels.config zapobiega powtorkom."""
    rows = db.fetchall(
        "SELECT brand_id, channel FROM channels WHERE status IN ('active','draft') AND supervised = true AND NOT (config ? 'welcomed')")
    for r in rows:
        try:
            note = content_memory.adaptation_candidates_note(r["brand_id"], r["channel"])
            if note:
                chat = hitl._admin_chat_id()
                if chat:
                    conversation._tg("sendMessage", {"chat_id": chat, "text": note[:4096],
                                                     "disable_web_page_preview": True})
        except Exception:
            traceback.print_exc()
        db.execute("UPDATE channels SET config = config || '{\"welcomed\": true}'::jsonb WHERE brand_id=%s AND channel=%s",
                   (r["brand_id"], r["channel"]))


def _stale_approval_watch():
    """KANON 19/07 (zastepuje USUNIETY stan awaryjny 11c/D-F2-3b): niezatwierdzone NIGDY nie
    wychodzi samo. Material czekajacy na approve >24h = ESKALACJA Z PYTANIEM (decisions.ask,
    guziki + nauka), nie auto-zatwierdzenie. Throttle w DB: jedna otwarta/swieza decyzja per item.
    Incydent 13-19/07: autopilot opublikowal serie niezatwierdzonych meta-postow na X i LinkedIn."""
    rows = db.fetchall(
        """SELECT id, brand_id, master_theme FROM content_items
           WHERE status='needs_approval' AND approval_requested_at IS NOT NULL
             AND approval_requested_at < NOW() - interval '24 hours'""")
    for item in rows:
        if db.fetchone(
                """SELECT 1 AS x FROM agent_decisions
                   WHERE decision_type='stale_approval' AND context->>'content_item_id'=%s
                     AND (status='pending' OR answered_at > NOW() - interval '24 hours') LIMIT 1""",
                (str(item["id"]),)):
            continue
        decisions.ask(
            "CM", item["brand_id"], "stale_approval",
            f"Material czeka na Twoja decyzje ponad 24h: \"{item['master_theme'][:150]}\". "
            f"Nic nie wyjdzie bez Twojego tapniecia - co robimy?",
            [{"key": "show", "label": "Pokaz karte"},
             {"key": "reject", "label": "Odrzuc material"},
             {"key": "wait", "label": "Przypomnij jutro"}],
            recommendation="show", context={"content_item_id": str(item["id"])})


# ---------------- loop ----------------
def loop():
    print("[cm] worker loop started", flush=True)
    while True:
        worked = False
        try:
            research.ingest_research_responses()  # researching -> drafting on Researcher callback
            reconcile_publications()              # backlog b: handed_off -> published PO callbacku (+ zwis alert)
            _welcome_new_channels()               # R5: nowy kanal -> propozycja reuse archiwum
            _stale_approval_watch()               # kanon 19/07: >24h ciszy = pytanie guzikami, NIGDY auto-publikacja
            matreview.sunday_guard()              # S4: niedzielne przypomnienia + fallback 23:00
            matreview.media_attach_watch()        # v7: ➕ Media - swieze zdjecie -> przypiecie do materialu
            proactive.tick()                      # 06/07: luka kadencji -> subagent wola CM; odprawa semi
            sunday_brief.tick()                   # 19/07 BE-SWIAT: sob. podklad pod niedzielny artykul (research swiata)
            conversation.memory_tick()            # 10/07: wygasajacy watek rozmowy -> skrot do pamieci trwalej
            engagement.consumer_tick()            # 10/07: zatwierdzone komentarze -> gotowiec do wklejenia + guziki
            engagement.stale_watch()              # 20/07 BE-ENGAGEMENT: propozycje/wklejenia >24h -> przypomnienie guzikami
            sales.tick()                          # 20/07 BE-SPRZEDAWCA: wyniki researchu prospektow -> synteza + lejek
            sales.followup_watch()                # 26/07: termin kontaktu w lejku minal -> pytanie guzikami (Level 2)
            _brand_tokens_tick()                  # 12/07 #84: Notion Brand Config -> brand_tokens (poll 10 min)
            _x_collector_tick()                   # 19/07 kolektor X: snapshoty Owned Reads raz na dobe UTC
            item = db.claim_content_item()
            if item:
                worked = True
                result = process_item(item)
                print(f"[cm] item {item['id']} ({item['status']}) -> {result}", flush=True)
        except Exception:
            traceback.print_exc()
        if not worked:
            wake.wait(timeout=config.POLL_INTERVAL_S)
            wake.clear()


def _load_secrets():
    for attr, key in (("ANTHROPIC_API_KEY", "anthropic_api_key"),
                      ("RESEARCHER_WEBHOOK_SECRET", "researcher_webhook_secret"),
                      ("TELEGRAM_BOT_TOKEN", "telegram_bot_token"),
                      ("LOG_BOT_TOKEN", "log_bot_token")):
        try:
            v = db.get_secret(key)
            if v:
                setattr(config, attr, v)
        except Exception:
            traceback.print_exc()
    print("[cm] secrets loaded from app_secrets", flush=True)


def main():
    _load_secrets()
    conversation.wake_event = wake  # a material proposed in conversation wakes the loop immediately
    threading.Thread(target=loop, daemon=True).start()
    # FAZA F #71: sync worker DB->Notion (LISTEN ags_sync + kolejka sync_queue; DDL 014).
    # Watchdog w run_forever(); kolejka w DB = restart kontenera nic nie gubi.
    from .sync import notion_worker
    threading.Thread(target=notion_worker.run_forever, daemon=True).start()
    uvicorn.run(api, host="0.0.0.0", port=config.HTTP_PORT, log_level="info")


if __name__ == "__main__":
    main()
