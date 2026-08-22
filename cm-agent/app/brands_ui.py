"""Task #86 (12/07/2026): zarzadzanie markami z Telegrama (multi-tenant sales - Tomasz:
'brakuje mi menu w ktorym moge marke dolaczyc albo odlaczyc').

v1 TEKSTOWA (decyzja BE 12/07 noc): komendy deterministyczne, zero nowych galezi callbackow
w n8n (tylko przepustka w Detect Update Type). Guziki-toggle = nastepna sesja z tapem.

Komendy:
  /brands                 - lista marek ze statusami + liczba celow + jak przelaczac
  /brand_on NAZWA         - marka -> active
  /brand_off NAZWA        - marka -> paused (cele supervised zostaja, planer/luki ja pomijaja)
  /brand_add NAZWA        - nowa marka (paused) + cel linkedin 'ready' + checklista uzupelnien
  /brand_remove NAZWA     - soft-delete: status 'archived' (dane historyczne zostaja)
  /brand_config NAZWA     - podglad kompletnosci: voice_bible / visual/tokens / cele / execution_mode
  /brand_export NAZWA     - pelny config marki jako JSON (plik .json na Telegram)
"""
import traceback
import json
import re

from . import config, db

# '(?:@\w+)?' = sufiks, ktory klient Telegrama dokleja do komendy w GRUPIE ('/brands@AGSbot').
# Bez niego wzorzec nie pasuje, tekst leci do LLM i dostajesz odpowiedz zamiast listy marek.
# Notacja jak w conversation._KONTEKST_RE i sales.py (22/08, przed przenosinami do supergrupy).
_CMD_RE = re.compile(r"^/(brands|brand_on|brand_off|brand_add|brand_remove|brand_config|brand_export)"
                     r"(?:@\w+)?"
                     r"(?:\s+([A-Za-z0-9_-]{2,30}))?\s*$", re.IGNORECASE)

_STATUS_ICO = {"active": "🟢", "paused": "⚪", "archived": "🗄"}


def try_handle(chat_id, text):
    """True = tekst byl komenda /brand* i zostal obsluzony (deterministycznie, bez LLM)."""
    m = _CMD_RE.match((text or "").strip())
    if not m:
        return None
    cmd = m.group(1).lower()
    name = (m.group(2) or "").strip().upper()
    if cmd == "brands":
        return _list()
    if not name:
        return f"Podaj marke: /{cmd} NAZWA (lista: /brands)."
    if cmd == "brand_add":
        return _add(name)
    row = db.fetchone("SELECT brand_id, brand_name, status FROM brands WHERE brand_id=%s", (name,))
    if not row:
        return f"Nie znam marki '{name}'. Lista: /brands; nowa: /brand_add {name}."
    if cmd == "brand_on":
        return _set_status(name, "active")
    if cmd == "brand_off":
        return _set_status(name, "paused")
    if cmd == "brand_remove":
        return _set_status(name, "archived")
    if cmd == "brand_config":
        return _config(name)
    if cmd == "brand_export":
        return _export(chat_id, name)
    return None


def _list():
    rows = db.fetchall(
        """SELECT b.brand_id, b.brand_name, b.status,
                  COUNT(c.id) FILTER (WHERE c.status='active') AS act,
                  COUNT(c.id) AS cele
           FROM brands b LEFT JOIN channels c ON c.brand_id = b.brand_id
           GROUP BY b.brand_id, b.brand_name, b.status ORDER BY b.brand_id""")
    lines = ["🏷 MARKI (toggle: /brand_on NAZWA, /brand_off NAZWA):", ""]
    for r in rows:
        lines.append(f"{_STATUS_ICO.get(r['status'], '?')} {r['brand_id']} - {r['brand_name']} "
                     f"[{r['status']}] cele: {r['act']} aktywnych / {r['cele']}")
    lines += ["", "Szczegoly: /brand_config NAZWA | eksport: /brand_export NAZWA | "
                  "nowa: /brand_add NAZWA | archiwum: /brand_remove NAZWA"]
    return "\n".join(lines)


def _set_status(name, status):
    db.execute("UPDATE brands SET status=%s WHERE brand_id=%s", (status, name))
    if status == "archived":
        db.execute("UPDATE channels SET status='paused' WHERE brand_id=%s AND status='active'", (name,))
        return (f"🗄 Marka {name} zarchiwizowana (dane historyczne zostaja; aktywne cele -> paused). "
                f"Powrot: /brand_on {name}.")
    return (f"{_STATUS_ICO[status]} Marka {name} -> {status}. "
            + ("Planer i luki znow ja widza." if status == "active" else "Planer i luki ja pomijaja."))


def _add(name):
    if db.fetchone("SELECT 1 AS x FROM brands WHERE brand_id=%s", (name,)):
        return f"Marka {name} juz istnieje - /brand_config {name}."
    db.execute("INSERT INTO brands (brand_id, brand_name, status) VALUES (%s,%s,'paused')", (name, name))
    # D-020 (19/08): do dzis stalo tu na sztywno 'webhook' - tryb zabroniony od 22/07 (AP-307).
    # Znaczylo to, ze KAZDA nowa marka, takze zakladana u klienta, rodzila sie w konfiguracji,
    # ktora wywolala incydent publikacyjny. Domyslnie 'draft': cel czeka na reczna wklejke,
    # dopoki Tomasz swiadomie nie przelaczy go na 'post_queue'.
    cfg = {"language_publish": "pl", "secret_prefix": f"linkedin_{name.lower()}",
           "publish_mode": config.PUBLISH_DRAFT, "publish_windows": "08:00-18:00"}
    config.sprawdz_tryb_publikacji(cfg["publish_mode"], f"{name}/linkedin")
    db.execute(
        """INSERT INTO channels (brand_id, channel, status, adapter_path, config, supervised)
           VALUES (%s,'linkedin','ready','/webhook/subagent-linkedin-publish',%s,true)
           ON CONFLICT (brand_id, channel) DO NOTHING""",
        (name, json.dumps(cfg)))
    return (f"🆕 Marka {name} utworzona (paused) + cel linkedin (ready).\n"
            f"Checklista kompletnosci (wizard krok po kroku):\n"
            f"1. Glos: przygotuj voice_bible -> BE wgra bumpem do brand_config\n"
            f"2. Wizual: wiersze {name}_Value w bazie Notion Brand Config (tokens zsynca sie same)\n"
            f"3. Cele: dodatkowe przez rozmowe z CM (target_create) albo /brand_config {name}\n"
            f"4. Tryb: execution_mode zostaje 'supervised' do Twojej decyzji\n"
            f"5. Start: /brand_on {name}\n"
            f"Stan sprawdzisz: /brand_config {name}.")


def _config(name):
    b = db.fetchone("SELECT brand_id, brand_name, status FROM brands WHERE brand_id=%s", (name,))
    voice = db.fetchone(
        "SELECT version, LENGTH(config_value) AS len FROM brand_config WHERE brand_id=%s AND config_key='voice_bible' ORDER BY version DESC LIMIT 1",
        (name,))
    toks = None
    try:
        toks = db.fetchone("SELECT jsonb_object_keys(tokens) AS k FROM brand_tokens WHERE brand_id=%s LIMIT 1", (name,))
        ntoks = db.fetchone("SELECT COUNT(*) AS n FROM (SELECT jsonb_object_keys(tokens) FROM brand_tokens WHERE brand_id=%s) t", (name,))
    except Exception:
        ntoks = None
    chans = db.fetchall(
        "SELECT channel, status, execution_mode, config->>'language_publish' AS lang FROM channels WHERE brand_id=%s ORDER BY channel",
        (name,))
    lines = [f"🏷 {b['brand_id']} - {b['brand_name']} [{b['status']}]", ""]
    lines.append("✅ voice_bible: v" + str(voice["version"]) + f" ({voice['len']} zn.)" if voice
                 else "❌ voice_bible: BRAK (generacja bez glosu marki!)")
    lines.append(f"✅ tokeny wizualne: {ntoks['n']}" if (toks and ntoks and ntoks.get("n"))
                 else "⚠️ tokeny wizualne: brak (fallback: visual_canon/kod) - wiersze w Notion Brand Config")
    lines.append("CELE:")
    for c in chans:
        lines.append(f"  - {c['channel']}: {c['status']}, {c.get('execution_mode') or 'supervised'}, jezyk {c.get('lang') or '?'}")
    if not chans:
        lines.append("  (brak - dodaj przez CM: target_create)")
    return "\n".join(lines)


def _export(chat_id, name):
    from . import matreview
    data = {
        "brand": db.fetchone("SELECT * FROM brands WHERE brand_id=%s", (name,)),
        "brand_config": db.fetchall(
            "SELECT config_key, config_value, version FROM brand_config WHERE brand_id=%s", (name,)),
        "channels": db.fetchall(
            "SELECT channel, status, supervised, execution_mode, adapter_path, config FROM channels WHERE brand_id=%s",
            (name,)),
        "brand_strategy": db.fetchone("SELECT * FROM brand_strategy WHERE brand_id=%s", (name,)),
    }
    try:
        tokens = db.fetchone("SELECT tokens FROM brand_tokens WHERE brand_id=%s", (name,))
        data["brand_tokens"] = (tokens or {}).get("tokens")
    except Exception:
        traceback.print_exc()  # AP-306: odczyt tokenow moze nie wyjsc, ale nie po cichu
    payload = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    ok = matreview._tg_send_document(chat_id, f"brand_{name}.json", payload,
                                     caption=f"📦 Eksport marki {name} (config + glos + cele + tokeny) - "
                                             f"komplet dla klienta, ktory zabiera swoja marke.")
    return True if ok else "Nie udalo sie wyslac pliku eksportu - sprobuj za chwile."
