"""ConversationRouter (CM Brain Phase 1): two-way Telegram conversation with Tomasz.
n8n HITL is TRANSPORT only - it forwards text messages to POST /message; this module owns the logic:
dedup by update_id, per-chat state in user_agent_state (TTL 30 min), fast paths for preview/cancel,
free discussion via Sonnet with the propose_material tool. One approve model (decision D2): a proposed
material becomes a 'planned' content_item; the existing pipeline generates + sends approve buttons;
after approve the loop publishes in the slot and confirms on the log channel (bot #2)."""
import datetime
import json
import re
import traceback
from zoneinfo import ZoneInfo

import httpx
from psycopg.types.json import Jsonb

from . import db, config
from .brand import load_brand
from .generate import client

wake_event = None  # injected by worker.main(); a new material wakes the state-machine loop

WARSAW = ZoneInfo("Europe/Warsaw")
HISTORY_MAX = 16      # conversation turns kept in fsm_data
STATE_TTL_MIN = 30    # stale conversation resets (research verdict: TTL + /cancel exit every state)
TG_LIMIT = 4096

_PREVIEW_RE = re.compile(r"^\s*(/plan|/kolejka|plan|kolejka|status|poka[zż]\s+(plan|kolejk\w*))\s*\??\s*$", re.IGNORECASE)
_CANCEL_RE = re.compile(r"^\s*(/cancel|anuluj)\s*$", re.IGNORECASE)


# ---------------- Telegram transport ----------------
def _tg(method, payload):
    tok = config.TELEGRAM_BOT_TOKEN
    if not tok:
        return None
    try:
        r = httpx.post(f"https://api.telegram.org/bot{tok}/{method}", json=payload, timeout=20)
        return r.json()
    except Exception:
        return None


def _split(text, limit=TG_LIMIT):
    """Chunk long replies on paragraph boundaries (Telegram hard limit 4096)."""
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks or [" "]


def _reply(chat_id, text, placeholder_id=None):
    """Send a reply; the first chunk edits the '⏳' placeholder when we have one (live-stream pattern)."""
    parts = _split(text)
    if placeholder_id:
        r = _tg("editMessageText", {"chat_id": chat_id, "message_id": placeholder_id,
                                    "text": parts[0], "disable_web_page_preview": True})
        if r and r.get("ok"):
            parts = parts[1:]
    for p in parts:
        _tg("sendMessage", {"chat_id": chat_id, "text": p, "disable_web_page_preview": True})


# ---------------- dedup + state ----------------
def _seen(update_id):
    """True if this Telegram update was already processed (webhook retry / double delivery)."""
    if update_id is None:
        return False
    row = db.fetchone(
        "INSERT INTO processed_updates (update_id) VALUES (%s) ON CONFLICT DO NOTHING RETURNING update_id",
        (int(update_id),),
    )
    db.execute("DELETE FROM processed_updates WHERE processed_at < NOW() - interval '24 hours'")
    return row is None


def _load_history(chat_id, agent="cm"):
    """Historia rozmowy per AGENT w jednym czacie (fsm_data.histories[agent]) - przelaczenie agenta
    w menu nie przecieka watkiem do innego agenta."""
    row = db.fetchone("SELECT fsm_data, updated_at FROM user_agent_state WHERE chat_id=%s", (chat_id,))
    if not row:
        return []
    if datetime.datetime.now(datetime.timezone.utc) - row["updated_at"] > datetime.timedelta(minutes=STATE_TTL_MIN):
        return []
    data = row.get("fsm_data") or {}
    return (data.get("histories") or {}).get(agent) or data.get("history") or []


def _save_history(chat_id, history, agent="cm"):
    row = db.fetchone("SELECT fsm_data FROM user_agent_state WHERE chat_id=%s", (chat_id,))
    hists = ((row or {}).get("fsm_data") or {}).get("histories") or {}
    hists[agent] = history[-HISTORY_MAX:]
    db.execute(
        """INSERT INTO user_agent_state (chat_id, active_agent, fsm_state, fsm_data, updated_at)
           VALUES (%s,%s,'idle',%s,NOW())
           ON CONFLICT (chat_id) DO UPDATE SET fsm_data=EXCLUDED.fsm_data, fsm_state='idle', updated_at=NOW()""",
        (chat_id, agent, Jsonb({"histories": hists})),
    )


def _reset_state(chat_id):
    db.execute("UPDATE user_agent_state SET fsm_state='idle', fsm_data='{}'::jsonb, updated_at=NOW() WHERE chat_id=%s",
               (chat_id,))


# ---------------- queue preview ----------------
def _fmt_slot(dt):
    return dt.astimezone(WARSAW).strftime("%d/%m %H:%M") if dt else "brak slotu"


def _queue_snapshot(brand_id="AGS"):
    items = db.fetchall(
        """SELECT id, master_theme, status, target_channels, scheduled_for
           FROM content_items
           WHERE brand_id=%s AND status NOT IN ('published','rejected','failed')
           ORDER BY COALESCE(scheduled_for, created_at) LIMIT 20""",
        (brand_id,),
    )
    lines = []
    for it in items:
        ch = ",".join(it.get("target_channels") or [])
        lines.append(f"- [{it['status']}] {it['master_theme'][:80]} | {ch} | slot: {_fmt_slot(it.get('scheduled_for'))}")
    return "\n".join(lines) if lines else "(kolejka pusta)"


def _memory_snapshot(brand_id="AGS"):
    """Kontekst pamieci do rozmowy: ostatnie publikacje + rozmiar schowka (pelny modul content_memory = krok 1f)."""
    pub = db.fetchall(
        """SELECT master_theme, updated_at FROM content_items
           WHERE brand_id=%s AND status='published' ORDER BY updated_at DESC LIMIT 5""",
        (brand_id,),
    )
    zan = db.fetchone("SELECT COUNT(*) AS n FROM inspirations WHERE status='new'") or {"n": 0}
    lines = [f"- {p['master_theme'][:80]} ({p['updated_at'].astimezone(WARSAW).strftime('%d/%m')})" for p in pub]
    pub_txt = "\n".join(lines) if lines else "(brak)"
    return f"OSTATNIE PUBLIKACJE:\n{pub_txt}\nSCHOWEK (pomysly czekajace): {zan['n']}"


# ---------------- LLM discussion ----------------
def _conversation_model():
    """Tier rozmowy czytany LIVE z brand_config (klucz cm_tier_conversation, np. 'opus'/'sonnet'/'haiku');
    default = Opus 4.8 dla dyskusji strategicznej (R4). Zmiana przez /set, zero deployu."""
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='cm_tier_conversation' ORDER BY version DESC LIMIT 1")
    tier = (row or {}).get("config_value", "")
    return config.TIER_MODELS.get(str(tier).strip(), config.CONVERSATION_MODEL)


TOOL_SCHOWEK = {
    "name": "save_to_schowek",
    "description": ("Zapisz pomysl do SCHOWKA (baza pomyslow) BEZ uruchamiania produkcji. Uzyj gdy Tomasz "
                    "mowi 'na pozniej', 'do schowka', 'do bazy', 'zapisz pomysl' albo pomysl jest dobry ale nie teraz. "
                    "Schowek zasila planer i Idea Bota - to wspolna pula inspirations."),
    "input_schema": {
        "type": "object",
        "properties": {"idea": {"type": "string", "description": "Tresc pomyslu, zwiezle, z uzgodnionym katem jesli byl."}},
        "required": ["idea"],
    },
}

TOOL_PROPOSE = {
    "name": "propose_material",
    "description": ("Zapisz uzgodniony material do kolejki produkcyjnej CM. Wywolaj TYLKO gdy Tomasz wyraznie "
                    "potwierdzil temat (np. 'dawaj', 'zapisz', 'zrob to', 'opublikuj o 15'). Po zapisie pipeline "
                    "generuje tekst i wysyla Tomaszowi material do zatwierdzenia jednym guzikiem."),
    "input_schema": {
        "type": "object",
        "properties": {
            "master_theme": {"type": "string",
                             "description": "Temat-matka materialu, konkretny, z uzgodnionym katem narracji."},
            "target_channels": {"type": "array", "items": {"type": "string", "enum": ["x", "linkedin"]},
                                "description": "Kanaly publikacji. Domyslnie oba: x i linkedin."},
            "scheduled_for": {"type": ["string", "null"],
                              "description": ("Slot publikacji jako ISO 8601 z offsetem, np. 2026-07-03T15:00:00+02:00. "
                                              "null = publikacja od razu po zatwierdzeniu.")},
        },
        "required": ["master_theme", "target_channels"],
    },
}


def _system_blocks(brand):
    now = datetime.datetime.now(WARSAW).strftime("%A %d/%m/%Y %H:%M")
    role = (
        "Jestes Content Managerem AGS (Agent Growth Systems) i rozmawiasz na Telegramie z Tomaszem, wlascicielem. "
        "Mowisz po polsku, czysta polszczyzna bez anglicyzmow, zero em dash. Krotko i konkretnie, jak wspolpracownik, "
        "nie jak asystent. Twoja rola: dyskutujesz o pomyslach na tresci, proponujesz katy narracji, odpowiadasz "
        "na pytania o kolejke, a gdy Tomasz potwierdzi temat, zapisujesz material narzedziem propose_material. "
        "Model pracy: jedno zatwierdzenie. Po zapisaniu materialu pipeline generuje tekst, Tomasz klika raz "
        "Zatwierdz, a publikacja idzie automatycznie w slocie. Pomysl 'na pozniej' zapisujesz narzedziem "
        "save_to_schowek (bez produkcji). Nie dopytuj o szczegoly, ktore mozesz sensownie "
        "zalozyc (kanaly: domyslnie x + linkedin; slot: null gdy nie podany). "
        f"\nTeraz jest {now} (Europe/Warsaw)."
        f"\n\nAKTUALNA KOLEJKA CM:\n{_queue_snapshot()}"
        f"\n\n{_memory_snapshot()}"
    )
    return [
        {"type": "text", "text": role},
        {"type": "text",
         "text": f"GLOS MARKI (kontekst do dyskusji o tresciach):\n\n{brand['voice_bible']}",
         "cache_control": {"type": "ephemeral"}},
    ]


def _create_material(inp):
    theme = (inp.get("master_theme") or "").strip()
    channels = [c for c in (inp.get("target_channels") or ["x", "linkedin"]) if c]
    sched_dt = None
    raw = inp.get("scheduled_for")
    if raw:
        try:
            sched_dt = datetime.datetime.fromisoformat(str(raw))
            if sched_dt.tzinfo is None:
                sched_dt = sched_dt.replace(tzinfo=WARSAW)
        except ValueError:
            sched_dt = None
    db.fetchone(
        """INSERT INTO content_items (brand_id, master_theme, target_channels, status, scheduled_for)
           VALUES ('AGS',%s,%s,'planned',%s) RETURNING id""",
        (theme, list(channels), sched_dt),
    )
    if wake_event:
        wake_event.set()
    when = _fmt_slot(sched_dt) if sched_dt else "zaraz po zatwierdzeniu"
    return f"✅ W kolejce: \"{theme}\" | kanaly: {', '.join(channels)} | publikacja: {when}"


def _save_schowek(inp, chat_id):
    idea = (inp.get("idea") or "").strip()
    if not idea:
        return "Pusty pomysl, nic nie zapisuje."
    db.fetchone(
        """INSERT INTO inspirations (source, content, brand, status, metadata)
           VALUES ('cm_conversation', %s, 'AGS', 'new', %s) RETURNING id""",
        (idea, Jsonb({"chat_id": chat_id, "via": "cm_brain"})),
    )
    return f"🗃 W schowku: \"{idea[:120]}\""


def _discuss(chat_id, text):
    history = _load_history(chat_id) + [{"role": "user", "content": text}]
    brand = load_brand("AGS")
    resp = client().messages.create(
        model=_conversation_model(), max_tokens=1200,
        thinking={"type": "disabled"},  # Sonnet 5/Opus: thinking off, rozmowa ma byc szybka i tania
        system=_system_blocks(brand),
        tools=[TOOL_PROPOSE, TOOL_SCHOWEK],
        messages=history,
    )
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
    for b in resp.content:
        if getattr(b, "type", "") == "tool_use" and b.name == "propose_material":
            parts.append(_create_material(b.input))
        elif getattr(b, "type", "") == "tool_use" and b.name == "save_to_schowek":
            parts.append(_save_schowek(b.input, chat_id))
    reply = "\n\n".join(parts).strip() or "Przyjete."
    # history stores plain text only (tool calls are summarized in the reply line itself)
    _save_history(chat_id, history + [{"role": "assistant", "content": reply}], agent="cm")
    return reply


# ---------------- subagent conversation (1d) ----------------
TOOL_SUB_REMOVE = {
    "name": "subagent_remove_post",
    "description": "Usun pozycje z kolejki TEGO subagenta (status -> rejected). Uzyj tylko na wyrazne polecenie.",
    "input_schema": {"type": "object",
                     "properties": {"post_queue_id": {"type": "integer", "description": "Numer pozycji z listy kolejki."}},
                     "required": ["post_queue_id"]},
}

TOOL_SUB_RESCHEDULE = {
    "name": "subagent_reschedule_post",
    "description": "Przesun slot publikacji pozycji z kolejki TEGO subagenta.",
    "input_schema": {"type": "object",
                     "properties": {"post_queue_id": {"type": "integer"},
                                    "new_time": {"type": "string", "description": "ISO 8601 z offsetem, np. 2026-07-04T14:00:00+02:00"}},
                     "required": ["post_queue_id", "new_time"]},
}


def _sub_queue(brand, channel, limit=15):
    return db.fetchall(
        """SELECT id, status, content, scheduled_for FROM post_queue
           WHERE brand=%s AND platform=%s AND status IN ('review','scheduled','queued','held','dispatching')
           ORDER BY scheduled_for NULLS LAST, id LIMIT %s""",
        (brand, channel, limit),
    )


def _sub_queue_text(brand, channel):
    rows = _sub_queue(brand, channel)
    if not rows:
        return "(kolejka pusta)"
    return "\n".join(f"#{r['id']} [{r['status']}] {(r['content'] or '')[:70]} | slot: {_fmt_slot(r.get('scheduled_for'))}"
                     for r in rows)


def _sub_published_text(brand, channel, limit=10):
    rows = db.fetchall(
        """SELECT id, content FROM post_queue WHERE brand=%s AND platform=%s AND status='published'
           ORDER BY id DESC LIMIT %s""",
        (brand, channel, limit),
    )
    return "\n".join(f"#{r['id']} {(r['content'] or '')[:70]}" for r in rows) or "(brak publikacji)"


def _sub_decisions_text(brand, channel):
    try:
        rows = db.fetchall(
            """SELECT log_type, rationale, created_at FROM agent_logs
               WHERE agent_id=%s AND log_type='AUTONOMOUS_DECISION' ORDER BY created_at DESC LIMIT 5""",
            (f"{brand}:{channel}",),
        )
        if rows:
            return "\n".join(f"- {r['created_at'].astimezone(WARSAW).strftime('%d/%m %H:%M')}: {r['rationale'][:120]}" for r in rows)
    except Exception:
        pass  # tabela agent_logs wchodzi w kroku 1g
    return "(brak zarejestrowanych decyzji autonomicznych; log startuje w kroku 1g)"


def _sub_report(brand, channel):
    return (f"Raport subagenta {brand} {channel} (na zadanie):\n\n"
            f"OSTATNIE PUBLIKACJE:\n{_sub_published_text(brand, channel)}\n\n"
            f"KOLEJKA:\n{_sub_queue_text(brand, channel)}\n\n"
            f"DECYZJE AUTONOMICZNE:\n{_sub_decisions_text(brand, channel)}\n\n"
            "Metryki engagement: w przygotowaniu (weryfikacja zrodel API w toku); "
            "cykliczny raport dzienny/tygodniowy wchodzi w kroku 1g.")


def _sub_remove(inp, brand, channel):
    pid = int(inp.get("post_queue_id") or 0)
    row = db.fetchone("UPDATE post_queue SET status='rejected' WHERE id=%s AND brand=%s AND platform=%s RETURNING id",
                      (pid, brand, channel))
    return f"🗑 Usunieta pozycja #{pid}." if row else f"Nie znalazlem pozycji #{pid} w kolejce {channel}."


def _sub_reschedule(inp, brand, channel):
    pid = int(inp.get("post_queue_id") or 0)
    try:
        new_dt = datetime.datetime.fromisoformat(str(inp.get("new_time")))
        if new_dt.tzinfo is None:
            new_dt = new_dt.replace(tzinfo=WARSAW)
    except (ValueError, TypeError):
        return "Nie rozumiem terminu, podaj konkretnie (np. jutro 14:00)."
    row = db.fetchone(
        "UPDATE post_queue SET scheduled_for=%s WHERE id=%s AND brand=%s AND platform=%s RETURNING content_item_id",
        (new_dt, pid, brand, channel))
    if not row:
        return f"Nie znalazlem pozycji #{pid} w kolejce {channel}."
    if row.get("content_item_id"):
        db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s",
                   (new_dt, row["content_item_id"]))
    return f"🕐 Pozycja #{pid} przesunieta na {_fmt_slot(new_dt)}."


def _sub_system(brand_row, brand, channel):
    cfg = brand_row.get("config") or {}
    now = datetime.datetime.now(WARSAW).strftime("%A %d/%m/%Y %H:%M")
    role = (
        f"Jestes SUBAGENTEM publikacji dla celu: marka {brand}, kanal {channel}. Rozmawiasz na Telegramie "
        "z Tomaszem, wlascicielem. Mowisz po polsku, czysta polszczyzna, zero em dash, krotko i konkretnie. "
        "Odpowiadasz za SWOJ kanal: kolejka publikacji, sloty, historia. Mozesz usuwac i przesuwac pozycje "
        "(narzedzia) oraz proponowac material ad-hoc narzedziem propose_material z target_channels "
        f"ustawionym WYLACZNIE na ['{channel}'] (material przejdzie przez normalne zatwierdzenie Tomasza). "
        "Nie wychodz poza swoj kanal. Jesli pytanie dotyczy strategii calosci, odeslij do Content Managera (/agents)."
        f"\nKonfiguracja celu: {json.dumps(cfg, ensure_ascii=False)[:400]}"
        f"\nTeraz jest {now} (Europe/Warsaw)."
        f"\n\nKOLEJKA ({channel}):\n{_sub_queue_text(brand, channel)}"
        f"\n\nOSTATNIE PUBLIKACJE:\n{_sub_published_text(brand, channel, 5)}"
    )
    return [{"type": "text", "text": role}]


def _sub_tier_model():
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='cm_tier_subagent_chat' ORDER BY version DESC LIMIT 1")
    tier = (row or {}).get("config_value", "")
    return config.TIER_MODELS.get(str(tier).strip(), config.TIER_MODELS["sonnet"])


def _subagent_handle(chat_id, text, active):
    """Rozmowa z subagentem per KONTO/CEL. active = 'subagent:<brand>:<channel>'."""
    try:
        _, brand, channel = active.split(":", 2)
    except ValueError:
        _reply(chat_id, "Nieznany subagent. /agents aby wybrac.")
        return
    brand_row = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s", (brand, channel))
    if not brand_row:
        _reply(chat_id, f"Nie znam celu {brand}/{channel}. /agents aby wybrac.")
        return
    low = text.lower().strip()
    if re.match(r"^/?(kolejka|poka[zż]\s+kolejk\w*)\s*\??$", low):
        _reply(chat_id, f"Kolejka {brand} {channel}:\n{_sub_queue_text(brand, channel)}")
        return
    if re.match(r"^/?raport\s*(dzienny|tygodniowy)?\s*$", low):
        _reply(chat_id, _sub_report(brand, channel))
        return
    ph = _tg("sendMessage", {"chat_id": chat_id, "text": "⏳"})
    ph_id = ((ph or {}).get("result") or {}).get("message_id")
    history = _load_history(chat_id, agent=active) + [{"role": "user", "content": text}]
    resp = client().messages.create(
        model=_sub_tier_model(), max_tokens=900,
        thinking={"type": "disabled"},
        system=_sub_system(brand_row, brand, channel),
        tools=[TOOL_SUB_REMOVE, TOOL_SUB_RESCHEDULE, TOOL_PROPOSE],
        messages=history,
    )
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
    for b in resp.content:
        if getattr(b, "type", "") != "tool_use":
            continue
        if b.name == "subagent_remove_post":
            parts.append(_sub_remove(b.input, brand, channel))
        elif b.name == "subagent_reschedule_post":
            parts.append(_sub_reschedule(b.input, brand, channel))
        elif b.name == "propose_material":
            inp = dict(b.input)
            inp["target_channels"] = [channel]  # subagent nie wychodzi poza swoj kanal
            parts.append(_create_material(inp))
    reply = "\n\n".join(parts).strip() or "Przyjete."
    _save_history(chat_id, history + [{"role": "assistant", "content": reply}], agent=active)
    _reply(chat_id, reply, placeholder_id=ph_id)


# ---------------- entry point ----------------
def handle(update):
    """Process one forwarded Telegram text message (runs on a background thread; /message returned 202)."""
    chat_id = None
    try:
        chat_id = int(update.get("chat_id"))
        text = str(update.get("text") or "").strip()
        if not text or _seen(update.get("update_id")):
            return
        active = str(update.get("active_agent") or "").strip()
        if not active:
            row = db.fetchone("SELECT active_agent FROM user_agent_state WHERE chat_id=%s", (chat_id,))
            active = (row or {}).get("active_agent") or "cm"
        if active.startswith("subagent:"):
            if _CANCEL_RE.match(text):
                _reset_state(chat_id)
                _reply(chat_id, "Anulowane.")
                return
            _subagent_handle(chat_id, text, active)
            return
        if _CANCEL_RE.match(text):
            _reset_state(chat_id)
            _reply(chat_id, "Anulowane. Zaczynamy od nowa.")
            return
        if _PREVIEW_RE.match(text):
            _reply(chat_id, "Kolejka CM:\n" + _queue_snapshot())
            return
        ph = _tg("sendMessage", {"chat_id": chat_id, "text": "⏳"})
        ph_id = ((ph or {}).get("result") or {}).get("message_id")
        _reply(chat_id, _discuss(chat_id, text), placeholder_id=ph_id)
    except Exception:
        traceback.print_exc()
        if chat_id:
            _reply(chat_id, "Blad przetwarzania wiadomosci. Napisz jeszcze raz albo 'anuluj'.")
