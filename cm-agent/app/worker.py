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
from psycopg.types.json import Jsonb

from . import generate, compliance, channels, research, hitl, conversation, logbot, content_memory, reports, planner, matreview, slots, proactive

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


@api.post("/message", status_code=202)
def message(body: dict, x_researcher_secret: str = Header(default="")):
    """Conversation entry: n8n HITL forwards a Telegram text {chat_id, text, update_id}. Returns 202
    immediately; a background thread runs the ConversationRouter and replies via sendMessage directly."""
    _guard(x_researcher_secret)
    if not body.get("chat_id"):
        raise HTTPException(status_code=400, detail="chat_id required")
    threading.Thread(target=conversation.handle, args=(body,), daemon=True).start()
    return {"accepted": True}


# ---------------- state machine ----------------
def _draft(item):
    brand = load_brand(item["brand_id"])
    ctx = research.research_context(item.get("research_job_id"))
    canonical, _ = generate.generate_canonical(brand, item["master_theme"], ctx, content_item_id=item["id"])
    canonical = compliance.enforce(brand, canonical, content_item_id=item["id"])
    # sugestia wizualu per material (06/07); podmiana starej sugestii przy regeneracji
    try:
        hint = generate.generate_media_hint(brand, canonical, content_item_id=item["id"])
        media = [m for m in (item.get("media") or []) if (m or {}).get("kind") != "suggestion"]
        if hint:
            media.append({"kind": "suggestion", "text": hint})
        import json as _json
        db.execute("UPDATE content_items SET media=%s::jsonb, updated_at=NOW() WHERE id=%s",
                   (_json.dumps(media), item["id"]))
        item["media"] = media
    except Exception:
        traceback.print_exc()
    variants = []
    for ch in channels.active_targets(item["brand_id"], item.get("target_channels")):
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
        slot, changed = slots.assign_if_needed(item)
        if changed and slot:
            logbot.send(f"🗓 CM przydzielil slot: {slot.strftime('%a %d/%m %H:%M')} - "
                        f"{item['master_theme'][:70]} (zmiana? napisz do CM: 'przesun na ...')")
            return f"slot_assigned({slot:%d/%m %H:%M})"
        # backlog b: dispatch = HAND-OFF, nie publikacja. Item zostaje 'dispatching' (poza ACTIONABLE),
        # reconcile_publications zamelduje realny sukces/porazke po callbacku (Scheduler/subagent).
        db.set_item_status(item["id"], "dispatching")
        handoff = channels.dispatch_item(item)
        logbot.send(_dispatch_ack(item, handoff))
        return f"dispatching({len(handoff)})"
    return "noop"


# ---------------- backlog b: meldunek po CALLBACKU (nie przy delegacji) ----------------
# Slownik statusow post_queue: w locie / terminalny-OK / terminalny-porazka. Nieznany status = traktuj
# jak 'w locie' (konserwatywnie - timeout alert zlapie realny zwis, np. X media_errors).
_DISPATCH_PENDING = ("review", "dispatching", "scheduled", "queued")
_DISPATCH_OK = ("published", "held")
_DISPATCH_FAIL = ("failed", "error", "rejected")


def _chan_label(brand_id, platform):
    try:
        return planner._target_label(brand_id, platform)
    except Exception:
        return platform


def _dispatch_ack(item, handoff):
    """Prawdziwy meldunek W MOMENCIE delegacji: 'wyslane/zaplanowane/czeka recznie' - NIE 'opublikowal'.
    Sukces potwierdza dopiero reconcile_publications po callbacku."""
    if not handoff:
        return f"⚠️ Nic do wyslania: {item['master_theme'][:80]} (brak wariantow w kolejce - sprawdz kanaly celu)."
    lines = [f"📤 CM wyslal do publikacji: {item['master_theme'][:90]}"]
    for h in handoff:
        lab = _chan_label(item["brand_id"], h["platform"])
        if h["mode"] == config.PUBLISH_POST_QUEUE:
            lines.append(f"   • {lab}: zaplanowane (Scheduler opublikuje w slocie - potwierdze PO fakcie)")
        elif h["mode"] == config.PUBLISH_WEBHOOK:
            lines.append(f"   • {lab}: zlecone subagentowi (potwierdze po jego callbacku)")
        else:
            lines.append(f"   • {lab}: gotowiec czeka na Twoje reczne wklejenie")
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
    """Zwis publikacji: item siedzi w 'dispatching' dluzej niz DISPATCH_TIMEOUT_H bez potwierdzenia ->
    JEDEN glosny alert (to jest to, co wczesniej ginelo pod optymistycznym 'opublikowal')."""
    upd = item.get("updated_at")
    if not upd:
        return
    try:
        age_h = (_now() - upd).total_seconds() / 3600.0
    except Exception:
        return
    if age_h < config.DISPATCH_TIMEOUT_H:
        return
    st = _dispatch_alert_state()
    ids = st.get("ids", [])
    if str(item["id"]) in ids:
        return
    st["ids"] = (ids + [str(item["id"])])[-100:]
    _dispatch_alert_set(st)
    chans = ", ".join(sorted({_chan_label(item["brand_id"], r["platform"]) for r in pending}))
    logbot.send(f"⏱️ ZWIS PUBLIKACJI ({age_h:.0f} h bez potwierdzenia): {item['master_theme'][:80]}\n"
                f"   Kanaly wciaz w locie: {chans}. Sprawdz egzekucje Schedulera/Publishera (media_errors?).")


def reconcile_publications():
    """backlog b: awansuj 'dispatching' -> 'published' DOPIERO gdy wiersze post_queue osiagnely stan
    terminalny (realny callback Schedulera/subagenta), i DOPIERO WTEDY meldunek - z porazkami wlacznie.
    Optymistyczny 'opublikowal' przy delegacji ukrywal nieudane publikacje X (media_errors)."""
    rows = db.fetchall(
        "SELECT id, brand_id, master_theme, updated_at FROM content_items WHERE status='dispatching'")
    for item in rows:
        pq = db.fetchall("SELECT platform, status FROM post_queue WHERE content_item_id=%s", (item["id"],))
        if not pq:
            continue  # nic nie zdazylo trafic do kolejki - nastepny tick
        pending = [r for r in pq if r["status"] not in (_DISPATCH_OK + _DISPATCH_FAIL)]
        if pending:
            _dispatch_timeout_alert(item, pending)
            continue
        db.set_item_status(item["id"], "published")
        logbot.send(_publish_report(item, pq))
        print(f"[cm] reconciled -> published {item['id']}", flush=True)


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


def _emergency_promote():
    """STAN AWARYJNY (kanon 11c, D-F2-3b): brak reakcji Tomasza 24h po wyslaniu approve -> automatyczne
    zatwierdzenie najlepszej opcji (publikacja pojdzie normalnie w slocie). Log + glosne powiadomienie.
    Wylaczalne per cel: channels.config.emergency_publish=false blokuje item, ktory celuje w ten kanal."""
    rows = db.fetchall(
        """SELECT * FROM content_items
           WHERE status='needs_approval' AND approval_requested_at IS NOT NULL
             AND approval_requested_at < NOW() - interval '24 hours'""")
    for item in rows:
        targets = channels.active_targets(item["brand_id"], item.get("target_channels"))
        if not targets or not all((t.get("config") or {}).get("emergency_publish", True) for t in targets):
            continue
        db.set_item_status(item["id"], "approved")
        try:
            db.execute(
                "INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES ('cm','AUTONOMOUS_DECISION',%s,%s)",
                (f"Publikacja awaryjna: brak reakcji 24h na approve - {item['master_theme'][:70]}",
                 Jsonb({"content_item_id": str(item["id"]), "trigger": "silence_24h"})))
        except Exception:
            pass
        logbot.send(f"⚠️ STAN AWARYJNY: brak reakcji 24h. Zatwierdzam automatycznie i publikuje w slocie: "
                    f"{item['master_theme'][:80]}")
        print(f"[cm] emergency-approved {item['id']}", flush=True)


# ---------------- loop ----------------
def loop():
    print("[cm] worker loop started", flush=True)
    while True:
        worked = False
        try:
            research.ingest_research_responses()  # researching -> drafting on Researcher callback
            reconcile_publications()              # backlog b: dispatching -> published PO callbacku (+ zwis alert)
            _welcome_new_channels()               # R5: nowy kanal -> propozycja reuse archiwum
            _emergency_promote()                  # F2: stan awaryjny po 24h ciszy
            matreview.sunday_guard()              # S4: niedzielne przypomnienia + fallback 23:00
            matreview.media_attach_watch()        # v7: ➕ Media - swieze zdjecie -> przypiecie do materialu
            proactive.tick()                      # 06/07: luka kadencji -> subagent wola CM; odprawa semi
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
