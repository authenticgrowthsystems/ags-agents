"""Brand context: load voice (brand_config single-source) + strategy (brand_strategy) + build the cached
system block. voice_bible is read LIVE; its hash is stamped on each content_item for audit/reproducibility."""
import hashlib
import json

from . import db


def _config_value(brand_id, key):
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key=%s ORDER BY version DESC LIMIT 1",
        (brand_id, key),
    )
    return row["config_value"] if row else None


def load_brand(brand_id):
    """Return {voice_bible, voice_dna_core, voice_hash, banned_vocab[list], strategy{...}}.
    voice_bible canonical in brand_config."""
    voice = _config_value(brand_id, "voice_bible") or ""
    dna = _config_value(brand_id, "voice_dna_core") or ""
    banned_raw = _config_value(brand_id, "banned_vocab")
    banned = []
    if banned_raw:
        try:
            banned = json.loads(banned_raw)
        except Exception:
            banned = [w.strip() for w in str(banned_raw).split(",") if w.strip()]
    strat = db.fetchone(
        "SELECT target_audience, content_pillars, core_topics FROM brand_strategy WHERE brand_id=%s",
        (brand_id,),
    ) or {}
    return {
        "brand_id": brand_id,
        "voice_bible": voice,
        "voice_dna_core": dna,
        "voice_hash": hashlib.md5(voice.encode("utf-8")).hexdigest(),
        "banned_vocab": [str(b) for b in banned],
        "strategy": strat,
    }


def voice_text(brand):
    """CALY glos marki: rdzen osobisty (voice_dna_core) + PELNA Voice Bible.

    BUG NAPRAWIONY 24/07 (zgloszenie Managera, potwierdzone gremem): osiem miejsc w kodzie
    wysylalo model do pisania z `voice_bible[:1200..3000]` z 22 168 znakow, czyli z naglowkiem
    pliku i pozycjonowaniem. Zasad pisania (sekcje 4.x: zakazane slownictwo, em-dash, rytm)
    model NIE WIDZIAL NIGDY, a mimo to dostawal polecenie "pisz tym glosem" - polecenie bez
    pokrycia. To ta sama klasa bledu, ktora zlapalismy rano w sciezce sprzedazowej.

    Wybieranie sekcji po slowach kluczowych zostalo sprawdzone i obalone (z 37 naglowkow
    dopasowaly sie dwa; listy zakazanego slownictwa maja naglowki po angielsku), wiec glos
    idzie w CALOSCI. Koszt trzyma prompt-cache: blok jest bajtowo staly."""
    parts = []
    dna = (brand or {}).get("voice_dna_core") or ""
    if dna.strip():
        parts.append("RDZEN GLOSU TOMASZA (voice_dna_core, pelny):\n" + dna.strip())
    bible = ((brand or {}).get("voice_bible") or "").strip()
    if bible:
        parts.append("VOICE BIBLE (pelna):\n" + bible)
    return "\n\n".join(parts)


def voice_block(brand):
    """Blok `system` z pelnym glosem, oznaczony do prompt-cache. Uzywaj TEGO zamiast
    recznych wycinkow voice_bible - kazdy wycinek to ciche gubienie zasad marki."""
    return {"type": "text",
            "text": f"OFICJALNY GLOS MARKI ({(brand or {}).get('brand_id', 'AGS')}). "
                    f"Pisz scisle w tym glosie:\n\n{voice_text(brand)}",
            "cache_control": {"type": "ephemeral"}}


def system_blocks(brand):
    """Anthropic `system` param: a stable CM-role block + the voice_bible block marked cache_control ephemeral
    (prompt caching: the voice prefix is byte-stable so repeated calls hit the cache and bill input cheaper)."""
    strat = brand.get("strategy") or {}
    role = (
        "You are the AGS Content Manager: a brand-aware content backbone. You produce ONE canonical post body "
        "in the brand voice, which channel adapters then transform per platform. Hard rules: zero em dashes "
        "(use commas, hyphens, colons, new lines, or restructure); never sound like a guru; start with a moment "
        "not a lesson; end with forward motion."
    )
    if strat.get("target_audience"):
        role += f"\nAudience: {strat['target_audience']}"
    if strat.get("content_pillars"):
        role += f"\nContent pillars: {', '.join(strat['content_pillars'])}"
    return [{"type": "text", "text": role}, voice_block(brand)]
