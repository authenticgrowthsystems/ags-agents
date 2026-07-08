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

from . import db, config, tasks, content_memory, reports
from . import planner
from .brand import load_brand
from .generate import client

wake_event = None  # injected by worker.main(); a new material wakes the state-machine loop

WARSAW = ZoneInfo("Europe/Warsaw")
HISTORY_MAX = 16      # conversation turns kept in fsm_data
STATE_TTL_MIN = 30    # stale conversation resets (research verdict: TTL + /cancel exit every state)
TG_LIMIT = 4096

_PREVIEW_RE = re.compile(r"^\s*(/plan|/kolejka|plan|kolejka|status|poka[zż]\s+(plan|kolejk\w*))\s*\??\s*$", re.IGNORECASE)
_SCHOWEK_RE = re.compile(r"^\s*(/schowek|schowek|baza\s+pomys\w*|poka[zż]\s+(schowek|baz\w*))\s*\??\s*$", re.IGNORECASE)
_KARTY_RE = re.compile(r"^\s*(?:/karty|karty|przegl[aą]daj|poka[zż]\s+(?:karty|materia\w*)|materia[lł]y\s+do\s+przegl[aą]du)"
                       r"(?:\s+(dzi[sś]|dzisiaj|jutro|jutrzejsze))?\s*\??\s*$", re.IGNORECASE)
_DECYZJE_RE = re.compile(r"^\s*(/decyzje|decyzje|poka[zż]\s+decyzje|czekaj[aą]ce\s+decyzje)\s*\??\s*$", re.IGNORECASE)
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
        """SELECT id, master_theme, status, target_channels, scheduled_for, media
           FROM content_items
           WHERE brand_id=%s AND status NOT IN ('published','rejected','failed','proposed')
           ORDER BY COALESCE(scheduled_for, created_at) LIMIT 60""",
        (brand_id,),
    )  # 'proposed' celowo poza kolejka - propozycje planu maja wlasny widok (planner.plan_text)
    lines = []
    for it in items:
        ch = ",".join(it.get("target_channels") or [])
        n_media = sum(1 for m in (it.get("media") or []) if (m or {}).get("file_id"))
        med = f" 🖼x{n_media}" if n_media else ""  # 06/07: CM MUSI widziec zalaczniki w kolejce
        lines.append(f"- [{it['status']}]{med} {it['master_theme'][:80]} | {ch} | slot: {_fmt_slot(it.get('scheduled_for'))}")
    if len(items) == 60:
        lines.append("(...kolejka dluzsza - to pierwsze 60; ZANIM powiesz ze materialu nie ma, "
                     "sprawdz show_review_cards z theme_fragment)")
    return "\n".join(lines) if lines else "(kolejka pusta)"


_SRC_ICON = {"telegram": "💡", "cm_conversation": "🧠", "notion": "📓"}


def _schowek_view():
    """Deterministyczny podglad schowka (bez LLM): pomysly 'new' czekajace na planer + liczniki statusow."""
    rows = db.fetchall(
        "SELECT id, source, content, created_at FROM inspirations WHERE status='new' ORDER BY id DESC LIMIT 20")
    counts = db.fetchall("SELECT status, COUNT(*) AS n FROM inspirations GROUP BY status ORDER BY status")
    lines = [f"🗃 Schowek - CZEKAJACE na planer ({len(rows)}):"]
    for r in rows:
        when = r["created_at"].astimezone(WARSAW).strftime("%d/%m") if r.get("created_at") else "?"
        lines.append(f"#{r['id']} {_SRC_ICON.get(r['source'], '📌')} ({when}) {(r['content'] or '')[:80]}")
    if len(rows) == 0:
        lines.append("(pusto - wrzuc pomysl przez Idea Bota albo 'zapisz do schowka' tutaj)")
    lines.append("")
    lines.append("Wszystkie wpisy wg statusu: " + ", ".join(f"{c['status']}: {c['n']}" for c in counts))
    lines.append("Statusy inne niz 'new' = pomysly juz przerobione przez stary pipeline (post_drafted/researched...) "
                 "albo odrzucone; planer bierze tylko 'new'.")
    return "\n".join(lines)


def _channels_snapshot(brand_id="AGS"):
    """Konfiguracja CELOW dla rozmowy (fix 06/07: CM nie znal okien publikacji/kadencji)."""
    rows = db.fetchall(
        "SELECT channel, status, supervised, config FROM channels WHERE brand_id=%s ORDER BY channel",
        (brand_id,))
    lines = []
    for r in rows:
        cfg = r.get("config") or {}
        bits = [f"status={r['status']}" + ("/supervised" if r.get("supervised") else "/standalone")]
        if cfg.get("publish_windows"):
            bits.append(f"okno={cfg['publish_windows']}")
        if r["channel"] == "x":
            bits.append(f"kadencja={cfg.get('posts_per_day', '3-5')}/dzien")
        elif r["channel"].startswith("linkedin"):
            bits.append("kadencja=pn-pt post, sob nic, nd artykul")
        bits.append(f"jezyk={cfg.get('language_publish', 'en')}")
        lines.append(f"- {r['channel']}: " + ", ".join(bits))
    return "\n".join(lines) or "(brak celow)"


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
_COMM_GUIDE = {
    "pl": ("Mowisz po polsku, czysta polszczyzna bez anglicyzmow, zero em dash. Krotko i konkretnie, "
           "jak wspolpracownik, nie jak asystent."),
    "en": "You speak English. Zero em dashes. Short and concrete, like a coworker, not an assistant.",
}


def language_comm():
    """R6: jezyk KOMUNIKACJI bota (rozmowa/raporty) z brand_config, default pl. /set language_comm en = live."""
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='language_comm' ORDER BY version DESC LIMIT 1")
    return (((row or {}).get("config_value")) or "pl").strip().lower()


def comm_guide():
    lang = language_comm()
    return _COMM_GUIDE.get(lang, f"You speak the language with code '{lang}'. Zero em dashes.")


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

TOOL_ARCHIVE = {
    "name": "show_archive",
    "description": ("Pokaz archiwum publikacji: najlepiej performujace i ostatnie posty (wszystkie kanaly albo "
                    "jeden). Uzyj gdy Tomasz pyta co najlepiej zagralo, co juz publikowalismy, o historie."),
    "input_schema": {
        "type": "object",
        "properties": {"channel": {"type": ["string", "null"], "description": "Kanal (x/linkedin/...) albo null = wszystkie."},
                       "top_n": {"type": "integer", "description": "Ile pozycji, default 10."}},
        "required": [],
    },
}

TOOL_SIMILAR = {
    "name": "find_similar_published",
    "description": ("Znajdz w archiwum publikacje SEMANTYCZNIE podobne do podanego tematu/tekstu (pgvector). "
                    "Uzyj przed proponowaniem materialu, zeby nie dublowac tresci, albo gdy Tomasz pyta "
                    "'czy juz o tym pisalismy'."),
    "input_schema": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "Temat albo tekst do porownania."}},
        "required": ["text"],
    },
}

TOOL_ADAPT = {
    "name": "adapt_published",
    "description": ("Zaproponuj adaptacje OPUBLIKOWANEGO posta (po numerze #id z archiwum) na inny kanal. "
                    "Zwraca propozycje tekstu; do kolejki trafia dopiero przez propose_material po akceptacji."),
    "input_schema": {
        "type": "object",
        "properties": {"published_id": {"type": "integer", "description": "Numer #id z archiwum."},
                       "target_channel": {"type": "string", "description": "Kanal docelowy, np. linkedin, x, instagram."}},
        "required": ["published_id", "target_channel"],
    },
}


def _archive_text(inp):
    ch = inp.get("channel") or None
    n = int(inp.get("top_n") or 10)
    top = content_memory.top_performing("AGS", channel=ch, top_n=n)
    if not top:
        return "Archiwum puste dla tego zakresu."
    lines = ["Archiwum (top wg metryk, bez metryk = najswiezsze):"]
    for t in top:
        mv = f" | metryka: {t['metric_value']}" if t.get("metric_value") is not None else ""
        when = t["published_at"].astimezone(WARSAW).strftime("%d/%m") if t.get("published_at") else "?"
        lines.append(f"- #{t['id']} [{t['platform']}] ({when}) {(t['content'] or '')[:70]}{mv}")
    return "\n".join(lines)


def _similar_text(inp):
    rows = content_memory.find_similar(str(inp.get("text") or ""), "AGS")
    if not rows:
        return "Brak podobnych publikacji w archiwum (albo embeddingi jeszcze sie licza)."
    lines = ["Podobne publikacje:"]
    for r in rows:
        c = (r["content"] or "").replace("\n", " ")
        c = c[:70] + "..." if len(c) > 70 else c  # S1 (feedback 05/07): uciete tytuly z trojkropkiem
        lines.append(f"- #{r['id']} [{r['platform']}] podob. {float(r['similarity']):.2f}: {c}")
    return "\n".join(lines)


def _adapt_text(inp):
    text, src = content_memory.suggest_adaptation(int(inp.get("published_id") or 0),
                                                  str(inp.get("target_channel") or "").strip() or "linkedin")
    if not text:
        return "Nie znalazlem takiej publikacji w archiwum."
    return f"Propozycja adaptacji (zrodlo: {src}):\n\n{text}\n\nJesli pasuje, powiedz 'dawaj' - zapisze jako material do zatwierdzenia."


TOOL_PLAN_BUILD = {
    "name": "plan_build",
    "description": ("Zbuduj PROPOZYCJE planu tygodnia (schowek + strategia + archiwum + kadencja). "
                    "Uzyj gdy Tomasz mowi 'zaplanuj tydzien' albo prosi o nowy plan. Wynik przyjdzie "
                    "osobna ponumerowana wiadomoscia."),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

TOOL_PLAN_APPROVE = {
    "name": "plan_approve",
    "description": ("Zatwierdz PROPOZYCJE planu (pozycje 'proposed' -> produkcja CALOSCI od razu). "
                    "Uzyj gdy Tomasz mowi 'zatwierdz plan' / 'dawaj plan'; wyjatki podaj numerami."),
    "input_schema": {"type": "object",
                     "properties": {"except_numbers": {"type": "array", "items": {"type": "integer"},
                                                        "description": "Numery pozycji do POMINIECIA (odrzucane)."}},
                     "required": []},
}

TOOL_PLAN_EDIT = {
    "name": "plan_edit",
    "description": "Edytuj JEDNA pozycje propozycji planu po jej numerze: usun, zmien temat i/lub slot.",
    "input_schema": {"type": "object",
                     "properties": {"number": {"type": "integer"},
                                    "new_theme": {"type": ["string", "null"]},
                                    "new_slot": {"type": ["string", "null"], "description": "ISO 8601 z offsetem"},
                                    "remove": {"type": "boolean"}},
                     "required": ["number"]},
}

TOOL_TARGET_CREATE = {
    "name": "target_create",
    "description": ("Dodaj NOWY CEL publikacji (wiersz channels, status 'ready') kopiujac konfiguracje "
                    "z istniejacego celu i nadpisujac wskazane pola. Aktywacja pozniej w ⚙️ Cele."),
    "input_schema": {"type": "object",
                     "properties": {"brand_id": {"type": "string", "description": "Marka (AGS/TNM/RDC...)."},
                                    "channel": {"type": "string", "description": "Nazwa celu, np. linkedin, instagram."},
                                    "copy_from_channel": {"type": ["string", "null"],
                                                          "description": "Istniejacy cel-wzorzec (config kopiowany)."},
                                    "language_publish": {"type": ["string", "null"]},
                                    "secret_prefix": {"type": ["string", "null"]}},
                     "required": ["brand_id", "channel"]},
}

TOOL_TARGET_UPDATE = {
    "name": "target_update",
    "description": "Zmien JEDNO pole konfiguracji istniejacego celu (channels.config), np. language_publish, posts_per_day, work_mode, emergency_publish, stats_mode, org_urn.",
    "input_schema": {"type": "object",
                     "properties": {"brand_id": {"type": "string"}, "channel": {"type": "string"},
                                    "key": {"type": "string"}, "value": {"type": "string"}},
                     "required": ["brand_id", "channel", "key", "value"]},
}


def _plan_build_async():
    import threading
    threading.Thread(target=planner.build_plan, args=("AGS",), daemon=True).start()
    return "🗓 Buduje propozycje planu - przyjdzie osobna, ponumerowana wiadomoscia za chwile."


def _plan_approve(inp):
    ok, skipped = planner.approve_plan("AGS", inp.get("except_numbers") or [])
    if not ok and not skipped:
        return "Nie ma propozycji do zatwierdzenia (najpierw 'zaplanuj tydzien')."
    if wake_event:
        wake_event.set()
    return (f"✅ Plan zatwierdzony: {ok} pozycji idzie do produkcji OD RAZU (odrzucone: {skipped}). "
            "Materialy przyjda do zatwierdzenia pojedynczo; brak reakcji 24h = publikacja awaryjna w slocie.")


def _plan_edit(inp):
    return planner.edit_plan_item("AGS", int(inp.get("number") or 0),
                                  new_theme=inp.get("new_theme"), new_slot=inp.get("new_slot"),
                                  remove=bool(inp.get("remove")))


def _target_create(inp):
    brand = str(inp.get("brand_id") or "AGS").strip()
    channel = str(inp.get("channel") or "").strip().lower()
    if not channel:
        return "Podaj nazwe celu."
    base = {}
    if inp.get("copy_from_channel"):
        row = db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s",
                          (brand, str(inp["copy_from_channel"]).strip()))
        base = dict((row or {}).get("config") or {})
    base.setdefault("publish_mode", "webhook")
    if inp.get("language_publish"):
        base["language_publish"] = str(inp["language_publish"]).strip().lower()
    base["secret_prefix"] = str(inp.get("secret_prefix") or f"{brand.lower()}_{channel}").strip()
    row = db.fetchone(
        """INSERT INTO channels (brand_id, channel, status, adapter_path, config, supervised)
           VALUES (%s,%s,'ready','/webhook/subagent-linkedin-publish',%s,true)
           ON CONFLICT (brand_id, channel) DO NOTHING RETURNING id""",
        (brand, channel, Jsonb(base)))
    if not row:
        return f"Cel {brand}/{channel} juz istnieje - uzyj target_update."
    return (f"🎯 Nowy cel {brand}/{channel} dodany jako USPIONY (ready), jezyk: {base.get('language_publish', '?')}, "
            f"klucze pod prefiksem '{base['secret_prefix']}'. Wlaczysz go w ⚙️ Cele gdy wgramy tokeny.")


def _target_update(inp):
    brand = str(inp.get("brand_id") or "AGS").strip()
    channel = str(inp.get("channel") or "").strip()
    key = str(inp.get("key") or "").strip()
    val = str(inp.get("value") or "").strip()
    if key in ("welcomed",):
        return "Tego pola nie zmieniamy recznie."
    if val.lower() in ("true", "false"):
        val_json = val.lower() == "true"
    else:
        try:
            val_json = int(val)
        except ValueError:
            val_json = val
    row = db.fetchone(
        "UPDATE channels SET config = config || %s WHERE brand_id=%s AND channel=%s RETURNING channel",
        (Jsonb({key: val_json}), brand, channel))
    return f"⚙️ {brand}/{channel}: {key} = {val}." if row else f"Nie znam celu {brand}/{channel}."


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


TOOL_ATTACH_PHOTO = {
    "name": "attach_last_photo",
    "description": ("Dolacz OSTATNIE zdjecie wyslane botu (trafia do schowka z file_id) do materialu. "
                    "Wywoluj gdy Tomasz prosi o dodanie zdjecia/grafiki do posta/materialu. "
                    "theme_fragment = fragment tematu materialu (pusty = ostatnio tworzony material)."),
    "input_schema": {"type": "object", "properties": {
        "theme_fragment": {"type": ["string", "null"],
                           "description": "Fragment tematu materialu docelowego (albo null)."}}},
}


def _attach_last_photo(inp):
    """Etap 1 multimediow (06/07): zdjecia lapane przez bota leza w inspirations.metadata.media
    (file_id) - dolaczamy descriptor do content_items.media; publisher X wgrywa przy publikacji."""
    photo = db.fetchone(
        """SELECT id, metadata FROM inspirations
           WHERE metadata->'media'->>'file_id' IS NOT NULL ORDER BY created_at DESC LIMIT 1""")
    if not photo:
        return "Nie widze zadnego zdjecia w schowku - wyslij je najpierw botu (jak pomysl)."
    frag = (inp.get("theme_fragment") or "").strip()
    if frag:
        item = db.fetchone(
            """SELECT id, master_theme FROM content_items
               WHERE brand_id='AGS' AND status IN ('draft','planned','needs_approval','proposed')
                 AND master_theme ILIKE %s ORDER BY updated_at DESC LIMIT 1""", (f"%{frag}%",))
    else:
        item = db.fetchone(
            """SELECT id, master_theme FROM content_items
               WHERE brand_id='AGS' AND status IN ('draft','planned','needs_approval','proposed')
               ORDER BY updated_at DESC LIMIT 1""")
    if not item:
        return "Nie znajduje materialu docelowego - podaj fragment tematu."
    desc = {"source": "telegram", "file_id": photo["metadata"]["media"]["file_id"],
            "kind": photo["metadata"]["media"].get("kind", "photo"), "inspiration_id": photo["id"]}
    row = db.fetchone("SELECT status, media FROM content_items WHERE id=%s", (item["id"],))
    # antydubel (06/07): to samo zdjecie dopiete drugi raz = dwa identyczne obrazy w tweecie
    if any((m or {}).get("file_id") == desc["file_id"] for m in ((row or {}).get("media") or [])):
        return f"To zdjecie jest juz dopiete do: \"{item['master_theme'][:120]}\" - nic nie dublowalem."
    from . import matreview as _mrv
    _mrv._note_attach(item["master_theme"])
    db.execute("UPDATE content_items SET media = media || %s::jsonb, updated_at=NOW() WHERE id=%s",
               (json.dumps([desc]), item["id"]))
    # zalacznik dopiety do materialu W KOLEJCE; juz zestagowane warianty tez go dostaja
    db.execute("UPDATE post_queue SET media = media || %s::jsonb WHERE content_item_id=%s AND status IN ('review','held','scheduled')",
               (json.dumps([desc]), item["id"]))
    if row and row["status"] == "draft":
        # material czeka na decyzje intake - przywolaj guziki NA DOL (feedback 06/07: zero scrollowania)
        from . import matreview
        matreview.send_intake_buttons(item["id"], item["master_theme"])
        return (f"🖼 Zdjecie dopiete do: \"{item['master_theme'][:120]}\" - material czeka na Twoja "
                f"decyzje, guziki lecia ponizej.")
    return f"🖼 Zdjecie dopiete do: \"{item['master_theme'][:120]}\" (poleci razem z publikacja na X)."


TOOL_REVIEW_CARDS = {
    "name": "show_review_cards",
    "description": ("Wyslij Tomaszowi SWIEZA karte przegladu materialow (needs_approval) z guzikami "
                    "decyzji i strzalkami, na dole czatu. Gdy Tomasz pyta o KONKRETNY material "
                    "(np. 'pokaz post ze zdjeciem', 'ta o tolerancji') - podaj theme_fragment i/lub "
                    "only_with_media, zeby karta otworzyla sie NA TYM materiale."),
    "input_schema": {"type": "object", "properties": {
        "theme_fragment": {"type": ["string", "null"], "description": "Fragment tematu szukanego materialu."},
        "only_with_media": {"type": ["boolean", "null"], "description": "true = pierwszy material z zalacznikiem."}}},
}


TOOL_STYLE_RULE = {
    "name": "add_style_rule",
    "description": ("Zapisz NA STALE regule stylu/jezyka podana wprost przez Tomasza (np. 'przed i nie "
                    "stawia sie przecinkow', 'nie uzywaj slowa X'). Wywoluj ZAWSZE gdy Tomasz mowi "
                    "'zapamietaj' o stylu pisania - sama rozmowa NIE jest trwala pamiecia."),
    "input_schema": {"type": "object", "properties": {
        "rule": {"type": "string", "description": "Regula w 1 zdaniu, po polsku."}},
        "required": ["rule"]},
}


TOOL_RESCHEDULE = {
    "name": "reschedule_material",
    "description": ("Przesun SLOT publikacji istniejacego materialu (feedback 06/07 'zatwierdz w innym "
                    "terminie' / 'przesun na ...'). Wywoluj gdy Tomasz chce zmienic KIEDY cos pojdzie: "
                    "'przesun Tolerancje na czwartek 14:00', 'daj to jutro rano', 'na nastepny wolny slot'. "
                    "Podaj theme_fragment (ktory material). Czas: scheduled_for = ISO 8601 Europe/Warsaw "
                    "(policz z aktualnej daty podanej w kontekscie), ALBO to_next_free=true = najblizszy "
                    "wolny slot w oknie kadencji. NIE tworzy nowego materialu."),
    "input_schema": {"type": "object", "properties": {
        "theme_fragment": {"type": "string", "description": "Fragment tematu materialu do przesuniecia."},
        "scheduled_for": {"type": ["string", "null"],
                          "description": "Docelowy termin ISO 8601 (np. 2026-07-09T14:00). Pomin gdy to_next_free."},
        "to_next_free": {"type": ["boolean", "null"],
                         "description": "true = przydziel najblizszy wolny slot wg okien+kadencji (ignoruje scheduled_for)."}},
        "required": ["theme_fragment"]},
}


TOOL_REPLACE = {
    "name": "replace_material",
    "description": ("PODMIEN zaplanowany post na nowa, lepsza wersje ZACHOWUJAC jego slot (feedback 07/07). "
                    "Wywoluj gdy wykryjesz bliski duplikat/mocniejszy kat i Tomasz zgadza sie podmienic "
                    "(zamiast dodawac drugi podobny post). Znajdz zaplanowany post po target_theme_fragment "
                    "i nadaj mu new_master_theme - system przegeneruje tresc, slot i kanaly zostaja. "
                    "NIE tworzy drugiego materialu, NIE kasuje slotu."),
    "input_schema": {"type": "object", "properties": {
        "target_theme_fragment": {"type": "string", "description": "Fragment tematu zaplanowanego postu do podmiany."},
        "new_master_theme": {"type": "string", "description": "Nowy temat-matka (mocniejszy kat), konkretny."}},
        "required": ["target_theme_fragment", "new_master_theme"]},
}


def _system_blocks(brand):
    from . import matreview as _mrv
    now = datetime.datetime.now(WARSAW).strftime("%A %d/%m/%Y %H:%M")
    role = (
        "Jestes Content Managerem AGS (Agent Growth Systems) i rozmawiasz na Telegramie z Tomaszem, wlascicielem. "
        f"{comm_guide()} Jestes PARTNEREM STRATEGICZNYM, nie ekspedientem: masz WLASNE ZDANIE i je "
        "wyrazasz. Gdy Tomasz rzuca temat - dorzuc SWOJ kat albo mocniejsze ujecie, powiedz co zrobilbys "
        "inaczej i dlaczego, zaproponuj konkret (haczyk, struktura, powiazanie z realnym momentem). Prowadzisz "
        "DIALOG, nie obsluge: zadaj JEDNO trafne pytanie, gdy realnie wyostrzy tekst (kat, kanal PL/EN, "
        "powiazanie z dzisiejszym buildem, seria czy swieze ujecie) - ale nie przesluchuj. Dyskutujesz o "
        "pomyslach, proponujesz katy narracji, odpowiadasz na pytania o kolejke, a gdy Tomasz potwierdzi "
        "temat, zapisujesz material narzedziem propose_material. RUNDA DOPRECYZOWANIA: gdy sam dokladasz "
        "mocne wlasne ramowanie do swiezego tematu, POKAZ swoj kat i spytaj krotko 'dawac tak, czy cos "
        "doprecyzowac (kanal, ramowanie)?' ZANIM zapiszesz - daj Tomaszowi runde sterowania (np. moze nie "
        "chciec ujawniac na personal LinkedIn ze publikuje maszyna). Gdy temat jasny albo potwierdzony "
        "wprost ('dawaj', 'zapisz') - zapisuj od razu, bez zbednego pytania. "
        "Model pracy: jedno zatwierdzenie. Po zapisaniu materialu pipeline generuje tekst, Tomasz klika raz "
        "Zatwierdz, a publikacja idzie automatycznie w slocie. Pomysl 'na pozniej' zapisujesz narzedziem "
        "save_to_schowek (bez produkcji). PLANOWANIE: 'zaplanuj tydzien' -> plan_build; 'zatwierdz plan' -> "
        "plan_approve (wyjatki numerami); edycje pozycji -> plan_edit. Cele: target_create / target_update. "
        "Brak reakcji Tomasza 24h po prosbie o approve = publikacja awaryjna w slocie (poinformuj, gdy pyta). "
        "Domyslne zalozenia gdy nie podano: kanaly x + linkedin, slot null - nie pytaj o to. Gdy dedup "
        "wykryje podobny/blizniaczy temat w kolejce, NIE poprzestawaj na liscie 'podobne publikacje': jesli "
        "Twoj nowy kat jest MOCNIEJSZY, ZAPROPONUJ PODMIANE tamtego zaplanowanego postu na nowa wersje "
        "(replace_material - slot zostaje, kolejka sie nie dubluje), albo spytaj wprost 'podmienic tamten "
        "czy zostawic oba / seria czy swieze ujecie?'. Nie zostawiaj Tomasza z sama lista. "
        "Gdy Tomasz pyta o KONKRETNY material: NAJPIERW show_review_cards z theme_fragment "
        "(przeszukuje PELNA baze) - migawka kolejki bywa przycieta; NIE twierdz, ze materialu "
        "nie ma, dopoki narzedzie tego nie potwierdzi. "
        f"\nTeraz jest {now} (Europe/Warsaw)."
        f"\n\nSTAN OPERACYJNY (o mechanizmach mow WYLACZNIE wg tego stanu - zero zgadywania; "
        f"przypinanie zdjec robi automat, nie Ty):\n{_mrv.modes_snapshot()}"
        f"\n\nCELE I KONFIGURACJA (okna publikacji w czasie Europe/Warsaw; zmiany przez target_update):\n"
        f"{_channels_snapshot()}"
        f"\nMECHANIKA SLOTOW: material 'approved' bez slotu albo z minionym slotem dostaje slot "
        f"AUTOMATYCZNIE (najblizszy wolny wg okna i kadencji) - NIE trzeba budowac planu, zeby "
        f"poukladac sloty zatwierdzonych. PRZESUWANIE: 'przesun <material> na <termin>' / 'zatwierdz w "
        f"innym terminie' -> reschedule_material (policz ISO z 'Teraz jest' powyzej; 'nastepny wolny' "
        f"-> to_next_free=true)."
        f"\n\nAKTUALNA KOLEJKA CM:\n{_queue_snapshot()}"
        f"\n\nPROPOZYCJA PLANU (proposed, numeracja dla plan_edit/plan_approve):\n{planner.plan_text()}"
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
    # guard (06/07 wieczor): CM potrafi puscic propose_material z pustym master_theme (np. przy
    # 'osobnym drugim poscie') -> gola karta ""; nie wstawiaj smiecia, powiedz CM zeby dokonczyl temat.
    if len(theme) < 4:
        return ("⚠️ Nie zapisuje - brak konkretnego tematu-matki (dostalem pusty). Jesli to mial byc "
                "drugi/wspierajacy material, najpierw ulóz jego temat, potem zapisz.")
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
    # S2 (feedback 05/07): material NIE idzie cicho do produkcji - laduje jako 'draft'
    # (status poza ACTIONABLE) i Tomasz decyduje guzikami: Do kolejki / Dzis / Odrzuc (matdec:).
    row = db.fetchone(
        """INSERT INTO content_items (brand_id, master_theme, target_channels, status, scheduled_for)
           VALUES ('AGS',%s,%s,'draft',%s) RETURNING id""",
        (theme, list(channels), sched_dt),
    )
    from . import matreview
    matreview.send_intake_buttons(row["id"], theme)
    when = _fmt_slot(sched_dt) if sched_dt else "zaraz po zatwierdzeniu tekstu"
    return (f"📝 Zapisany: \"{theme}\" | kanaly: {', '.join(channels)} | slot: {when}\n"
            f"Zdecyduj guzikami (wiadomosc ponizej): Do kolejki / Dzis / Odrzuc.")


def _within_windows(brand_id, channels_list, slot):
    """Miekki sygnal: czy godzina slotu miesci sie w oknach publikacji WSZYSTKICH kanalow."""
    from . import slots as _sl
    rules = _sl.channel_rules(brand_id, channels_list)
    if not rules:
        return True
    tt = slot.time()
    return all(ws <= tt <= we for _ch, ws, we, _gap, _grid in rules)


def _reschedule_material(inp):
    """(o): przesun slot istniejacego materialu (nie tworzy nowego). Aktualizuje content_items ORAZ
    powiazane wiersze post_queue (zeby Scheduler wzial nowy czas). Tomasz nadrzedny - poza oknem tez
    ustawi, tylko z uwaga."""
    frag = (inp.get("theme_fragment") or "").strip()
    if not frag:
        return "Podaj ktory material przesunac (fragment tematu)."
    row = db.fetchone(
        """SELECT id, master_theme, brand_id, target_channels, scheduled_for, status
           FROM content_items
           WHERE brand_id='AGS' AND status IN
             ('draft','planned','drafting','needs_approval','approved','dispatching')
             AND master_theme ILIKE %s
           ORDER BY updated_at DESC LIMIT 1""",
        (f"%{frag}%",))
    if not row:
        return f"Nie znajduje w kolejce materialu pasujacego do \"{frag[:80]}\" (moze juz opublikowany albo odrzucony?)."
    from . import slots
    from .planner import _DAYS_PL
    now = datetime.datetime.now(WARSAW)
    note = ""
    if inp.get("to_next_free") or not inp.get("scheduled_for"):
        is_article = str(row.get("master_theme") or "").startswith("[ARTYKUL]")
        slot = slots.next_slot(row["brand_id"], row.get("target_channels") or ["x"],
                               is_article=is_article, prefer_today=True)
        if not slot:
            return "Nie znalazlem wolnego slotu w oknach na najblizsze 2 tygodnie."
    else:
        try:
            slot = datetime.datetime.fromisoformat(str(inp["scheduled_for"]))
        except (ValueError, TypeError):
            return f"Nie rozumiem terminu \"{inp.get('scheduled_for')}\" - podaj np. 'czwartek 14:00' albo 'jutro 9:00'."
        if slot.tzinfo is None:
            slot = slot.replace(tzinfo=WARSAW)
        slot = slot.astimezone(WARSAW)
        if slot <= now + datetime.timedelta(minutes=2):
            return f"Termin {_fmt_slot(slot)} jest w przeszlosci - podaj przyszly."
        if not _within_windows(row["brand_id"], row.get("target_channels") or ["x"], slot):
            note = "\n(uwaga: to poza standardowym oknem publikacji tego kanalu - ustawiam mimo to, bo Ty decydujesz o terminie)"
    db.execute("UPDATE content_items SET scheduled_for=%s, updated_at=NOW() WHERE id=%s", (slot, row["id"]))
    db.execute(
        """UPDATE post_queue SET scheduled_for=%s
           WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued','dispatching')""",
        (slot, row["id"]))
    return (f"🗓 Przesuniete: \"{row['master_theme'][:90]}\"\n"
            f"   nowy slot: {_DAYS_PL[slot.weekday()]} {_fmt_slot(slot)}.{note}")


def _replace_material(inp):
    """(B, feedback 07/07): podmien zaplanowany post na nowa wersje ZACHOWUJAC slot i kanaly.
    Zamiast dodawac duplikat - nadaj istniejacemu materialowi nowy temat, skasuj stare warianty,
    wroc do produkcji (status 'planned'). Petla przegeneruje i przyjdzie karta do zatwierdzenia."""
    frag = (inp.get("target_theme_fragment") or "").strip()
    new_theme = (inp.get("new_master_theme") or "").strip()
    if not frag:
        return "Podaj ktory zaplanowany post podmienic (fragment tematu)."
    if len(new_theme) < 4:
        return "Podaj nowy temat-matke (konkretny) do podmiany."
    row = db.fetchone(
        """SELECT id, master_theme, scheduled_for FROM content_items
           WHERE brand_id='AGS' AND status IN
             ('draft','planned','drafting','needs_approval','approved','dispatching')
             AND master_theme ILIKE %s ORDER BY updated_at DESC LIMIT 1""",
        (f"%{frag}%",))
    if not row:
        return f"Nie znajduje w kolejce postu do podmiany pasujacego do \"{frag[:80]}\"."
    old_theme = row["master_theme"]
    db.execute("UPDATE content_items SET master_theme=%s, status='planned', updated_at=NOW() WHERE id=%s",
               (new_theme, row["id"]))
    db.execute("DELETE FROM post_queue WHERE content_item_id=%s AND status IN ('review','held','scheduled','queued')",
               (row["id"],))
    when = _fmt_slot(row.get("scheduled_for"))
    return (f"🔁 Podmieniam zaplanowany post (slot {when} zostaje):\n"
            f"   bylo: \"{old_theme[:90]}\"\n   jest: \"{new_theme[:90]}\"\n"
            f"   Produkuje nowa tresc, przyjdzie jako karta do zatwierdzenia (~min).")


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


_CM_TOOLS = None
_MAX_TOOL_STEPS = 5


def _cm_tools():
    global _CM_TOOLS
    if _CM_TOOLS is None:
        _CM_TOOLS = [TOOL_PROPOSE, TOOL_SCHOWEK, TOOL_ARCHIVE, TOOL_SIMILAR, TOOL_ADAPT,
                     TOOL_PLAN_BUILD, TOOL_PLAN_APPROVE, TOOL_PLAN_EDIT, TOOL_TARGET_CREATE, TOOL_TARGET_UPDATE,
                     TOOL_REVIEW_CARDS, TOOL_ATTACH_PHOTO, TOOL_STYLE_RULE, TOOL_RESCHEDULE, TOOL_REPLACE]
    return _CM_TOOLS


def _dispatch_tool(name, inp, chat_id):
    """Wykonaj narzedzie CM i zwroc WYNIK jako tekst (wraca do modelu w petli agentowej -> CM moze
    zareagowac: po find_similar zaproponowac kat/podmiane, nie utknac na liscie)."""
    from . import matreview
    inp = inp or {}
    if name == "propose_material":
        return _create_material(inp)
    if name == "save_to_schowek":
        return _save_schowek(inp, chat_id)
    if name == "show_archive":
        return _archive_text(inp)
    if name == "find_similar_published":
        return _similar_text(inp)
    if name == "adapt_published":
        return _adapt_text(inp)
    if name == "plan_build":
        return _plan_build_async()
    if name == "plan_approve":
        return _plan_approve(inp)
    if name == "plan_edit":
        return _plan_edit(inp)
    if name == "target_create":
        return _target_create(inp)
    if name == "target_update":
        return _target_update(inp)
    if name == "show_review_cards":
        ok = matreview.send_review_card(chat_id, theme_fragment=inp.get("theme_fragment"),
                                        only_with_media=bool(inp.get("only_with_media")))
        return "Karta wyslana ponizej (widoczna dla Tomasza)." if ok else "Nie znajduje takiego materialu w przegladzie."
    if name == "attach_last_photo":
        return _attach_last_photo(inp)
    if name == "add_style_rule":
        n = matreview.add_style_rule(inp.get("rule"))
        return f"Regula stylu zapisana na stale (lacznie {n})."
    if name == "reschedule_material":
        return _reschedule_material(inp)
    if name == "replace_material":
        return _replace_material(inp)
    return "ok"


def _discuss(chat_id, text):
    """Petla agentowa (fix 07/07 'zero opcji, zero propozycji'): model moze zawolac narzedzie, DOSTAC
    wynik z powrotem i dzialac dalej (np. find_similar -> zaproponuj kat + podmiane), az zwroci finalny
    tekst. Efekty uboczne (guziki intake, karty) leca bezposrednio z narzedzi; do Tomasza idzie tekst CM."""
    history = _load_history(chat_id) + [{"role": "user", "content": text}]
    brand = load_brand("AGS")
    model, tier, source = tasks.model_for("conversation")  # R4: default opus, override cm_tier_conversation
    sysblocks = _system_blocks(brand)
    msgs = list(history)
    reply_texts = []
    for _step in range(_MAX_TOOL_STEPS):
        resp = client().messages.create(
            model=model, max_tokens=1200, thinking={"type": "disabled"},
            system=sysblocks, tools=_cm_tools(), messages=msgs)
        tasks.log_task("conversation", tier, model, source, getattr(resp, "usage", None))
        reply_texts += [b.text for b in resp.content
                        if getattr(b, "type", "") == "text" and b.text.strip()]
        tool_uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
        if not tool_uses:
            break
        msgs.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in tool_uses:
            out = _dispatch_tool(tu.name, tu.input, chat_id) or "ok"
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(out)[:3000]})
        msgs.append({"role": "user", "content": results})
    reply = "\n\n".join(reply_texts).strip() or "Przyjete."
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

TOOL_SUB_SHOW = {
    "name": "subagent_show_post",
    "description": ("Pokaz PELNA tresc pozycji z kolejki TEGO subagenta (numer #id z listy KOLEJKA). "
                    "Uzyj gdy Tomasz chce zobaczyc caly tekst zaplanowanego posta, nie skrot."),
    "input_schema": {"type": "object",
                     "properties": {"post_queue_id": {"type": "integer"}},
                     "required": ["post_queue_id"]},
}

TOOL_SUB_EDIT = {
    "name": "subagent_edit_post",
    "description": ("Podmien TRESC zaplanowanej pozycji z kolejki TEGO subagenta na wersje podana przez "
                    "Tomasza (edycja = akceptacja). Uzyj gdy Tomasz podaje nowy/poprawiony pelny tekst dla #id."),
    "input_schema": {"type": "object",
                     "properties": {"post_queue_id": {"type": "integer"},
                                    "new_content": {"type": "string", "description": "Pelna nowa tresc posta."}},
                     "required": ["post_queue_id", "new_content"]},
}

TOOL_SUB_METRICS = {
    "name": "subagent_set_metrics",
    "description": ("Zapisz RECZNIE podane metryki publikacji (numer #id z sekcji OSTATNIE PUBLIKACJE). "
                    "Uzywane dla X (API odczytu zablokowane) - Tomasz odczytuje liczby z aplikacji i dyktuje. "
                    "Podaj tylko pola, ktore Tomasz wymienil."),
    "input_schema": {"type": "object",
                     "properties": {"published_id": {"type": "integer"},
                                    "impressions": {"type": ["integer", "null"]},
                                    "reactions": {"type": ["integer", "null"]},
                                    "comments": {"type": ["integer", "null"]},
                                    "reshares": {"type": ["integer", "null"]},
                                    "clicks": {"type": ["integer", "null"]}},
                     "required": ["published_id"]},
}


TOOL_SUB_ESCALATE = {
    "name": "escalate_to_cm",
    "description": ("Zglos Content Managerowi SPRAWE STRATEGICZNA kanalu (siatka slotow, kadencja, "
                    "okno publikacji). CM rozpatrzy, przy zgodzie wpisze do configu i odpowie - "
                    "agenci dogaduja to MIEDZY SOBA, bez posrednictwa Tomasza. Uzywaj zamiast "
                    "odsylania Tomasza do /agents."),
    "input_schema": {"type": "object", "properties": {
        "topic": {"type": "string", "enum": ["slot_grid", "kadencja", "inne"]},
        "proposal": {"type": "string", "description": "Konkretna propozycja (np. 'siatka 14:00,16:00,18:00,20:00 bo publicznosc US')."}},
        "required": ["topic", "proposal"]},
}


TOOL_SUB_COMMENT = {
    "name": "suggest_comment",
    "description": ("Zaproponuj 3 komentarze w glosie marki pod CUDZY post (Tomasz wkleja tresc "
                    "posta i ew. autora). Doktryna comment-first: realna wartosc merytoryczna, "
                    "peer-level, 2-4 zdania, ZERO linkow i pitchu."),
    "input_schema": {"type": "object", "properties": {
        "post_text": {"type": "string", "description": "Tresc cudzego posta (wklejona przez Tomasza)."},
        "author": {"type": ["string", "null"], "description": "Autor/handle, jesli podany."}},
        "required": ["post_text"]},
}


def _sub_escalate(inp, brand, channel):
    from .proactive import _agent_id
    # antydubel (fix 06/07: 'i jak zatwierdzil?' wyslalo propozycje 2. raz)
    pending = db.fetchone(
        """SELECT 1 AS x FROM agent_messages
           WHERE message_type='request' AND status IN ('unread','processing')
             AND payload->>'kind'='channel_proposal' AND payload->>'channel'=%s
             AND payload->>'topic'=%s LIMIT 1""", (channel, inp.get("topic", "inne")))
    if pending:
        return "📨 Ta propozycja JUZ czeka u CM - odpowiedz przyjdzie za chwile, nie dubluje."
    sub_id = _agent_id(f"%{channel.split('_')[0]}%")
    cm_id = _agent_id("%content-manager%")
    if not (sub_id and cm_id):
        return "Nie moge wyslac - brak wpisow agentow w rejestrze (zglos BE)."
    db.execute(
        """INSERT INTO agent_messages (from_agent_id, to_agent_id, message_type, payload)
           VALUES (%s,%s,'request',%s)""",
        (sub_id, cm_id, json.dumps({"kind": "channel_proposal", "topic": inp.get("topic", "inne"),
                                    "proposal": (inp.get("proposal") or "")[:800],
                                    "brand": brand, "channel": channel}, ensure_ascii=False)))
    return ("📨 Przekazane do Content Managera (kontrakt agent->agent). CM rozpatrzy w ciagu minuty, "
            "przy zgodzie wpisze do configu; wynik zobaczysz w USTALENIACH Z CM i na bocie logowym.")


def _sub_comment(inp, brand, channel):
    """Komentarze pod cudze posty (decyzja Tomasza 06/07: element wzrostu zasiegow; sonnet)."""
    from .generate import _language_publish, TRUTH_GUARD
    brand_data = load_brand(brand)
    lang = _language_publish(brand, channel)
    model, tier, source = tasks.model_for("canonical")  # sonnet default - jakosc komentarzy
    author = (inp.get("author") or "").strip()
    resp = client().messages.create(
        model=model, max_tokens=700, thinking={"type": "disabled"},
        system=[{"type": "text", "text": f"Glos marki:\n{brand_data['voice_bible'][:2500]}"}],
        messages=[{"role": "user", "content":
                   f"Zaproponuj DOKLADNIE 3 rozne komentarze pod ponizszy cudzy post na {channel}"
                   f"{(' (autor: ' + author + ')') if author else ''}. Doktryna comment-first: "
                   f"kazdy komentarz wnosi KONKRETNA wartosc merytoryczna (doswiadczenie, kontrprzyklad, "
                   f"pogłebienie), ton peer-level, 2-4 zdania, ZERO linkow, zero pitchu, zero pochlebstw "
                   f"typu 'great post'. Jezyk: {'polski' if lang == 'pl' else 'angielski'}. {TRUTH_GUARD}\n"
                   f"Format: 1) ... 2) ... 3) ...\n\nPOST:\n{(inp.get('post_text') or '')[:1500]}"}])
    tasks.log_task("comment_suggest", tier, model, source, getattr(resp, "usage", None))
    out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    return "💬 Propozycje komentarzy:\n" + out if out else "Nie wyszlo - sprobuj jeszcze raz."


def _sub_cm_agreements(channel):
    rows = db.fetchall(
        """SELECT payload, created_at FROM agent_messages
           WHERE message_type='response' AND payload->>'kind'='channel_proposal_reply'
             AND payload->>'channel'=%s ORDER BY created_at DESC LIMIT 2""", (channel,))
    out = []
    for r in rows:
        p = r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"])
        verdict = ("PRZEKAZANE TOMASZOWI" if p.get("routed_to_human")
                   else ("OK" if p.get("approve") else "ODMOWA"))
        out.append(f"- {r['created_at'].astimezone(WARSAW).strftime('%d/%m %H:%M')}: "
                   f"{verdict} - {p.get('reply', '')[:120]}")
    return "\n".join(out) or "(brak)"


def _log_autonomous(brand, channel, rationale, context=None):
    """Blueprint zasada 4: kazde wyjscie poza plan CM = wpis AUTONOMOUS_DECISION (widoczny w raportach)."""
    try:
        db.execute("INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES (%s,'AUTONOMOUS_DECISION',%s,%s)",
                   (f"{brand}:{channel}", rationale, Jsonb(context or {})))
    except Exception:
        pass


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


def _review_copy(media, lang=None):
    """T8: wyciagnij kopie do przegladu (kind='review_<lang>') z media content_itemu."""
    for m in (media or []):
        k = str((m or {}).get("kind", ""))
        if k.startswith("review_") and (lang is None or k == f"review_{lang}"):
            return m.get("text")
    return None


def _update_review_copy(content_item_id, lang, text):
    """T8: zapisz/nadpisz kopie do przegladu w jezyku komunikacji na content_item."""
    import json as _json
    row = db.fetchone("SELECT media FROM content_items WHERE id=%s", (content_item_id,))
    media = [m for m in ((row or {}).get("media") or []) if not str((m or {}).get("kind", "")).startswith("review_")]
    media.append({"kind": f"review_{lang}", "text": text})
    db.execute("UPDATE content_items SET media=%s::jsonb, updated_at=NOW() WHERE id=%s",
               (_json.dumps(media), content_item_id))


def _sub_show(inp, brand, channel):
    """B (feedback 07/07): PELNA tresc zaplanowanej pozycji. T8: + odpowiednik w jezyku komunikacji (PL)
    do przegladu, gdy publikacja idzie w innym jezyku."""
    pid = int(inp.get("post_queue_id") or 0)
    row = db.fetchone(
        "SELECT pq.id, pq.status, pq.content, pq.scheduled_for, ci.media FROM post_queue pq "
        "LEFT JOIN content_items ci ON ci.id=pq.content_item_id WHERE pq.id=%s AND pq.brand=%s AND pq.platform=%s",
        (pid, brand, channel))
    if not row:
        return f"Nie znajduje pozycji #{pid} w kolejce {channel}."
    body = (row.get("content") or "(brak tresci - jeszcze w produkcji)").strip()
    out = f"#{pid} [{row['status']}] slot: {_fmt_slot(row.get('scheduled_for'))}\n\n{body}"
    review = _review_copy(row.get("media"))
    if review:
        out += f"\n\n———\n🇵🇱 Odpowiednik do przegladu (NIE publikuje sie):\n{review.strip()}"
    return out


def _sub_edit(inp, brand, channel):
    """B (feedback 07/07): podmien TRESC pozycji na wersje Tomasza (edycja = akceptacja). T8: jesli Tomasz
    edytuje PO POLSKU a kanal publikuje EN - tlumaczymy do publikacji, a PL zostaje jako kopia do przegladu.
    Trzyma zasade zero em-dash. Edytuje wariant kanalu (post_queue.content)."""
    from . import compliance, generate
    pid = int(inp.get("post_queue_id") or 0)
    raw = (inp.get("new_content") or "").strip()
    if len(raw) < 4:
        return "Podaj pelna nowa tresc do podmiany (dostalem pusta)."
    pub_lang = generate._language_publish(brand, channel)
    note, review_pl = "", None
    publish_text = raw
    if compliance.looks_polish(raw) and pub_lang != "pl":
        publish_text = generate.translate_text(raw, pub_lang) or raw
        review_pl = raw
        note = f" (Twoja wersja PL przetlumaczona do publikacji {pub_lang.upper()}; PL zachowany do przegladu)"
    publish_text = compliance.fix_dashes(publish_text)
    row = db.fetchone(
        "UPDATE post_queue SET content=%s WHERE id=%s AND brand=%s AND platform=%s "
        "AND status IN ('review','held','scheduled','queued') RETURNING id, content_item_id",
        (publish_text, pid, brand, channel))
    if not row:
        return f"Nie znajduje edytowalnej pozycji #{pid} w kolejce {channel} (moze juz opublikowana?)."
    if review_pl and row.get("content_item_id"):
        _update_review_copy(row["content_item_id"], "pl", review_pl)
    return f"✏️ Tresc #{pid} podmieniona (Twoja edycja = akceptacja).{note} Ta wersja poleci w slocie."


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


def _sub_surfaces_text(family, current_brand, current_channel):
    """D (feedback 07/07): subagent zna WSZYSTKIE swoje powierzchnie danej rodziny (np. linkedin*)
    z charakterystyka - marka, status, jezyk, okno, glos per konto. Substrat: channels + voice_note (C)."""
    from .planner import _target_label
    rows = db.fetchall(
        "SELECT brand_id, channel, status, supervised, config FROM channels WHERE channel LIKE %s ORDER BY brand_id, channel",
        (family + "%",))
    if not rows:
        return "(brak zarejestrowanych powierzchni)"
    out = []
    for r in rows:
        cfg = r.get("config") or {}
        lang = cfg.get("language_publish") or "?"
        win = cfg.get("publish_windows") or "(domyslne)"
        vn = (cfg.get("voice_note") or "").strip()
        here = r["brand_id"] == current_brand and r["channel"] == current_channel
        state = "AKTYWNY (publikuje)" if (r.get("supervised") and r["status"] in ("active", "draft")) \
            else f"{r['status']} (jeszcze NIE publikuje - czeka na tokeny/aktywacje)"
        line = (f"- {_target_label(r['brand_id'], r['channel'])} [{r['brand_id']}/{r['channel']}]: {state}, "
                f"jezyk={lang}, okno={win}" + ("  <- TU JESTES" if here else ""))
        if vn:
            line += f"\n    glos konta: {vn[:110]}"
        out.append(line)
    return "\n".join(out)


def _sub_strategy_text(family):
    """D: skrot strategii publikacji od CM dla rodziny (kto co ustala + kadencja kanoniczna)."""
    if family.startswith("linkedin"):
        return ("Kadencja: pon-pt 1 post, sobota nic, niedziela ARTYKUL. Podzial rol: CM ustala TRESC i "
                "KIEDY; TY realizujesz i wybierasz KONTO. Personal = pierwszoosobowy glos czlowieka (nie "
                "ujawniaj maszyny); strona firmowa = glos firmy.")
    if family == "x":
        return "Kadencja: 3-5 postow dziennie w oknie. CM ustala TRESC i KIEDY; Ty realizujesz i pilnujesz rytmu."
    return "CM ustala TRESC i KIEDY; Ty realizujesz w swoim oknie."


def _sub_system(brand_row, brand, channel):
    cfg = brand_row.get("config") or {}
    now = datetime.datetime.now(WARSAW).strftime("%A %d/%m/%Y %H:%M")
    family = channel.split("_")[0]
    role = (
        f"Jestes SUBAGENTEM publikacji dla celu: marka {brand}, kanal {channel}. Rozmawiasz na Telegramie "
        f"z Tomaszem, wlascicielem. {comm_guide()} "
        "Odpowiadasz za SWOJ kanal: kolejka publikacji, sloty, historia. Mozesz POKAZAC PELNA TRESC pozycji "
        "(subagent_show_post), EDYTOWAC tresc na wersje Tomasza (subagent_edit_post = edycja=akceptacja), "
        "usuwac i przesuwac pozycje, oraz proponowac material ad-hoc narzedziem propose_material z target_channels "
        f"ustawionym WYLACZNIE na ['{channel}'] (material przejdzie przez normalne zatwierdzenie Tomasza). "
        "ZNASZ WSZYSTKIE swoje powierzchnie (sekcja TWOJE POWIERZCHNIE nizej): ile ich jest, ich status "
        "(aktywne vs czekajace na aktywacje), jezyk, okno i glos per konto. Gdy material moze isc na WIECEJ "
        "niz jedno Twoje AKTYWNE konto, PYTASZ Tomasza na ktore (personal / strona / oba) - nie zakladaj "
        "sam. O kontach jeszcze nieaktywnych mow uczciwie, ze czekaja na aktywacje. "
        "Nie wychodz poza swoja rodzine kanalow. SPRAWY STRATEGICZNE kanalu (siatka slotow, kadencja, okno) "
        "zalatwiasz SAM z Content Managerem narzedziem escalate_to_cm - NIE odsylaj Tomasza. "
        "WYNIK eskalacji czytasz z sekcji USTALENIA Z CM ponizej - gdy Tomasz pyta 'i jak "
        "zatwierdzil?', ODPOWIEDZ z USTALEN, NIGDY nie eskaluj ponownie. "
        "Gdy Tomasz wkleja CUDZY post, proponuj komentarze narzedziem suggest_comment "
        "(comment-first: wartosc, zero pitchu). Metryki wpisuje Tomasz recznie (subagent_set_metrics) - "
        "raz w tygodniu sam sie o nie upominasz. "
        "PRAWDA O KOLEJCE I SLOTACH (twarda zasada, zero wyjatkow): gdy Tomasz pyta o sloty / kolejke / "
        "kiedy i gdzie publikujesz, podawaj WYLACZNIE pozycje z sekcji KOLEJKA ponizej wraz z ICH slotami. "
        "NIGDY nie wymyslaj godzin ani dni i NIE recytuj kadencji kanonicznej jako harmonogramu. Jesli "
        "KOLEJKA jest pusta, powiedz wprost 'kolejka pusta - nic nie zaplanowane', nie zmyslaj siatki. "
        "Sloty przydziela CM per material w oknie publikacji tego celu - nie ma stalej dziennej godziny."
        f"\nKonfiguracja celu: {json.dumps(cfg, ensure_ascii=False)[:400]}"
        f"\nOkno publikacji tego celu: {cfg.get('publish_windows', '(domyslne)')} (Europe/Warsaw)."
        f"\nTeraz jest {now} (Europe/Warsaw)."
        f"\n\nTWOJE POWIERZCHNIE (rodzina {family}) - znasz kazda i jej charakterystyke:\n"
        f"{_sub_surfaces_text(family, brand, channel)}"
        f"\n\nSTRATEGIA PUBLIKACJI (od CM):\n{_sub_strategy_text(family)}"
        f"\n\nKOLEJKA ({channel}) - JEDYNE zrodlo prawdy o slotach:\n{_sub_queue_text(brand, channel)}"
        f"\n\nOSTATNIE PUBLIKACJE:\n{_sub_published_text(brand, channel, 5)}"
        f"\n\nUSTALENIA Z CM (agent->agent):\n{_sub_cm_agreements(channel)}"
    )
    return [{"type": "text", "text": role}]


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
    model, tier, source = tasks.model_for("subagent_chat")  # R4: default sonnet, override cm_tier_subagent_chat
    resp = client().messages.create(
        model=model, max_tokens=900,
        thinking={"type": "disabled"},
        system=_sub_system(brand_row, brand, channel),
        tools=[TOOL_SUB_REMOVE, TOOL_SUB_RESCHEDULE, TOOL_SUB_SHOW, TOOL_SUB_EDIT, TOOL_SUB_METRICS,
               TOOL_PROPOSE, TOOL_SUB_ESCALATE, TOOL_SUB_COMMENT],
        messages=history,
    )
    tasks.log_task("subagent_chat", tier, model, source, getattr(resp, "usage", None))
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text" and b.text.strip()]
    for b in resp.content:
        if getattr(b, "type", "") != "tool_use":
            continue
        if b.name == "subagent_remove_post":
            out = _sub_remove(b.input, brand, channel)
            if out.startswith("🗑"):
                _log_autonomous(brand, channel, f"Usuniecie pozycji #{b.input.get('post_queue_id')} na polecenie Tomasza w rozmowie",
                                {"tool": "remove", "input": dict(b.input)})
            parts.append(out)
        elif b.name == "subagent_reschedule_post":
            out = _sub_reschedule(b.input, brand, channel)
            if out.startswith("🕐"):
                _log_autonomous(brand, channel, f"Przesuniecie slotu pozycji #{b.input.get('post_queue_id')} na {b.input.get('new_time')}",
                                {"tool": "reschedule", "input": dict(b.input)})
            parts.append(out)
        elif b.name == "subagent_show_post":
            parts.append(_sub_show(b.input, brand, channel))
        elif b.name == "subagent_edit_post":
            out = _sub_edit(b.input, brand, channel)
            if out.startswith("✏️"):
                _log_autonomous(brand, channel, f"Reczna edycja tresci #{b.input.get('post_queue_id')} w rozmowie",
                                {"tool": "edit", "post_queue_id": b.input.get("post_queue_id")})
            parts.append(out)
        elif b.name == "subagent_set_metrics":
            m = reports.set_manual_metrics(int(b.input.get("published_id") or 0), dict(b.input), brand, channel)
            parts.append(f"📈 Metryki zapisane dla #{b.input.get('published_id')}." if m
                         else f"Nie znalazlem publikacji #{b.input.get('published_id')} w {channel}.")
        elif b.name == "escalate_to_cm":
            _log_autonomous(brand, channel, f"Eskalacja do CM ({b.input.get('topic')}): {b.input.get('proposal', '')[:80]}",
                            {"tool": "escalate_to_cm", "input": dict(b.input)})
            parts.append(_sub_escalate(b.input, brand, channel))
        elif b.name == "suggest_comment":
            parts.append(_sub_comment(b.input, brand, channel))
        elif b.name == "propose_material":
            inp = dict(b.input)
            inp["target_channels"] = [channel]  # subagent nie wychodzi poza swoj kanal
            _log_autonomous(brand, channel, f"Material ad-hoc poza planem CM: {inp.get('master_theme', '')[:80]}",
                            {"tool": "propose_material", "input": inp})
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
        _km = _KARTY_RE.match(text)
        if _km:
            # feedback 06/07: karty przywolywalne Z KAZDEGO kontekstu rozmowy, swieze na dole czatu
            # (d): opcjonalny filtr dnia - 'karty jutro' / 'karty dzis'
            from . import matreview
            _q = (_km.group(1) or "").lower()
            day = "tomorrow" if _q.startswith("jutr") else ("today" if _q.startswith("dzi") else None)
            if not matreview.send_review_card(chat_id, day=day):
                _reply(chat_id, "Brak materialow do przegladu" +
                       (" na jutro." if day == "tomorrow" else (" na dzis." if day == "today" else ".")))
            return
        if _DECYZJE_RE.match(text):
            from . import matreview
            n = matreview.resend_intake()
            _reply(chat_id, f"Przywolalem {n} czekajacych decyzji (guziki ponizej)." if n
                   else "Zero czekajacych decyzji intake.")
            return
        from . import matreview as _mr
        if _mr.pending_edit() and not text.startswith("/") and not _CANCEL_RE.match(text):
            # '✏️ Edytuj' (06/07): ta wiadomosc = poprawiona wersja calego tekstu od Tomasza
            ans = _mr.apply_edit(text, wake_event)
            if ans:
                _reply(chat_id, ans)
                return
        if _mr.pending_angle() and not text.startswith("/") and not _CANCEL_RE.match(text):
            # 'Inny kat' v3: ta wiadomosc = wskazowki Tomasza (kat + wymagana tresc)
            ans = _mr.apply_angle_guidance(text, wake_event)
            if ans:
                _reply(chat_id, ans)
                return
        if active.startswith("subagent:"):
            if _CANCEL_RE.match(text):
                _reset_state(chat_id)
                _reply(chat_id, "Anulowane.")
                return
            _subagent_handle(chat_id, text, active)
            return
        if _CANCEL_RE.match(text):
            _reset_state(chat_id)
            _mr._state_set("cm_pending_angle", {})  # /cancel zamyka tez oczekiwanie na kat (fix 06/07)
            _mr._state_set("cm_pending_edit", {})   # ...i na edycje tekstu
            _mr._state_set("cm_pending_madd", {})   # ...i na doslanie zdjecia (➕ Media)
            _reply(chat_id, "Anulowane. Zaczynamy od nowa.")
            return
        if _PREVIEW_RE.match(text):
            pt = planner.plan_text()
            has_plan = pt != "(brak propozycji planu)"
            msg = ("📋 Propozycja planu (do zatwierdzenia):\n" + pt + "\n\n") if has_plan else ""
            msg += "⚙️ Kolejka produkcyjna:\n" + _queue_snapshot()
            _reply(chat_id, msg)
            if has_plan:
                planner.send_plan_controls(chat_id)
            return
        if _SCHOWEK_RE.match(text):
            _reply(chat_id, _schowek_view())
            return
        ph = _tg("sendMessage", {"chat_id": chat_id, "text": "⏳"})
        ph_id = ((ph or {}).get("result") or {}).get("message_id")
        _reply(chat_id, _discuss(chat_id, text), placeholder_id=ph_id)
    except Exception:
        traceback.print_exc()
        if chat_id:
            _reply(chat_id, "Blad przetwarzania wiadomosci. Napisz jeszcze raz albo 'anuluj'.")
