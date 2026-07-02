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


def _load_history(chat_id):
    row = db.fetchone("SELECT fsm_data, updated_at FROM user_agent_state WHERE chat_id=%s", (chat_id,))
    if not row:
        return []
    if datetime.datetime.now(datetime.timezone.utc) - row["updated_at"] > datetime.timedelta(minutes=STATE_TTL_MIN):
        return []
    return (row.get("fsm_data") or {}).get("history") or []


def _save_history(chat_id, history):
    db.execute(
        """INSERT INTO user_agent_state (chat_id, active_agent, fsm_state, fsm_data, updated_at)
           VALUES (%s,'cm','idle',%s,NOW())
           ON CONFLICT (chat_id) DO UPDATE SET fsm_data=EXCLUDED.fsm_data, fsm_state='idle', updated_at=NOW()""",
        (chat_id, Jsonb({"history": history[-HISTORY_MAX:]})),
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


# ---------------- LLM discussion ----------------
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
        "Zatwierdz, a publikacja idzie automatycznie w slocie. Nie dopytuj o szczegoly, ktore mozesz sensownie "
        "zalozyc (kanaly: domyslnie x + linkedin; slot: null gdy nie podany). "
        f"\nTeraz jest {now} (Europe/Warsaw)."
        f"\n\nAKTUALNA KOLEJKA CM:\n{_queue_snapshot()}"
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


def _discuss(chat_id, text):
    history = _load_history(chat_id) + [{"role": "user", "content": text}]
    brand = load_brand("AGS")
    resp = client().messages.create(
        model=config.CONVERSATION_MODEL, max_tokens=1200,
        thinking={"type": "disabled"},  # Sonnet 5 defaults thinking ON; keep conversation lean
        system=_system_blocks(brand),
        tools=[TOOL_PROPOSE],
        messages=history,
    )
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
    for b in resp.content:
        if getattr(b, "type", "") == "tool_use" and b.name == "propose_material":
            parts.append(_create_material(b.input))
    reply = "\n\n".join(parts).strip() or "Przyjete."
    # history stores plain text only (tool calls are summarized in the reply line itself)
    _save_history(chat_id, history + [{"role": "assistant", "content": reply}])
    return reply


# ---------------- entry point ----------------
def handle(update):
    """Process one forwarded Telegram text message (runs on a background thread; /message returned 202)."""
    chat_id = None
    try:
        chat_id = int(update.get("chat_id"))
        text = str(update.get("text") or "").strip()
        if not text or _seen(update.get("update_id")):
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
