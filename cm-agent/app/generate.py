"""Generation: Sonnet for the canonical tekst-matka, Haiku for per-channel variants. Brand voice comes from
the cached system block (brand.system_blocks), so the voice prefix is reused cheaply across calls."""
import anthropic

from . import config, tasks
from . import db as _db
from .brand import system_blocks

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _text(resp):
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


# TWARDA REGULA PRAWDY (Tomasz 06/07: "nie moge oszukiwac swojej publicznosci") - generator
# wymyslal pierwszoosobowe anegdoty, ktore nigdy sie nie wydarzyly. Doklejana do KAZDEGO promptu.
TRUTH_GUARD = (
    "HARD TRUTH RULE: do NOT invent events, anecdotes, client stories, numbers or first-person "
    "experiences. First person is allowed ONLY for facts explicitly present in the theme or the "
    "provided evidence. If a concrete example is missing, write in general terms or clearly "
    "hypothetically ('imagine...', 'a typical pattern is...'). One fabricated story destroys the "
    "build-in-public brand. When unsure whether something happened - it did not.")


def _learned_style(brand_id="AGS"):
    """Nauka poziom 2 (06/07): regulki wydestylowane z RECZNYCH korekt Tomasza (VOICE_EDIT),
    trzymane w brand_config 'style_learned' - dokladane do KAZDEJ generacji."""
    import json as _json
    row = _db.fetchone("SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key='style_learned'",
                       (brand_id,))
    try:
        rules = (_json.loads(row["config_value"]).get("rules") or []) if row and row.get("config_value") else []
    except Exception:
        rules = []
    if not rules:
        return ""
    return ("\nOWNER STYLE PREFERENCES (learned from his manual edits - follow them):\n"
            + "\n".join(f"- {r}" for r in rules[-15:]))


def generate_canonical(brand, master_theme, research_context="", content_item_id=None):
    """Tekst-matka; model per task z routera R4 (default sonnet, override brand_config cm_tier_canonical)."""
    model, tier, source = tasks.model_for("canonical")
    msg = f"Write a canonical post for the theme: {master_theme}."
    if research_context:
        msg += f"\n\nGround it in this evidence (use what is relevant, do not list sources):\n{research_context[:6000]}"
    msg += f"\n\n{TRUTH_GUARD}{_learned_style(brand.get('brand_id', 'AGS'))}\n\nReturn ONLY the post body. Brand voice. Zero em dashes."
    resp = client().messages.create(
        model=model, max_tokens=1500,
        thinking={"type": "disabled"},  # Sonnet 5 defaults thinking ON when omitted; keep it off (preserves budget)
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    tasks.log_task("canonical", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp), getattr(resp, "usage", None)


CHANNEL_GUIDE = {
    # format X (Tomasz 06/07): krotkie formy ~500-600 zn. (konto Premium); dluga tresc = NITKA
    "x": ("X/Twitter: short punchy posts. If the canonical is short, write ONE post of at most ~550 "
          "characters with a strong hook. If the canonical is long or article-like, write a THREAD of "
          "3-6 posts, each 300-550 characters, separated by lines containing exactly ===TWEET=== ; "
          "post 1 = a hook that stands alone, last post = the takeaway. At most one hashtag total."),
    "linkedin": "LinkedIn: up to ~1300 characters, problem then decision then mechanism then result, professional but human.",
    "youtube": "YouTube: a title line plus a 2 to 3 line description.",
    "facebook": "Facebook: a short conversational post.",
    "instagram": "Instagram: a caption with a strong first line.",
}


LANGUAGE_GUIDE = {
    "pl": ("Write the adaptation in PURE POLISH: natural, everyday Polish with ZERO anglicisms "
           "(the 'mom test' - a non-technical Polish speaker must understand every word)."),
    "en": "Write the adaptation in English.",
}


def _language_publish(brand_id, channel):
    """R6: jezyk publikacji per CEL z channels.config.language_publish (default en)."""
    row = _db.fetchone("SELECT config FROM channels WHERE brand_id=%s AND channel=%s", (brand_id, channel))
    return (((row or {}).get("config") or {}).get("language_publish") or "en").lower()


def generate_media_hint(brand, canonical_body, content_item_id=None):
    """Propozycja wizualu per material (feedback 06/07: 'przy kazdym materiale sugestia grafiki/
    zdjecia/filmu'). Jedno zdanie, tylko wizuale WYKONALNE przez autora (screenshot, zdjecie biurka,
    prosta grafika z teza) - regula prawdy obowiazuje takze obrazy."""
    model, tier, source = tasks.model_for("variant")
    resp = client().messages.create(
        model=model, max_tokens=150, thinking={"type": "disabled"},
        system=system_blocks(brand),
        messages=[{"role": "user", "content":
                   "Zaproponuj JEDNA konkretna forme wizualna do ponizszego posta: autentyczne zdjecie "
                   "(np. biurko/ekran autora), screenshot systemu, prosta grafika z jedna teza, albo "
                   "krotkie wideo. Napisz JEDNO zdanie po polsku: co dokladnie ma przedstawiac. ZAKAZ: "
                   "wizuale wydarzen, ktore sie nie odbyly, zdjecia stockowe udajace zycie autora.\n\n"
                   f"POST:\n{canonical_body[:1500]}"}])
    tasks.log_task("media_hint", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp)[:300]


_openai_key = [None]


def generate_image(prompt):
    """ETAP 2a (decyzja Tomasza 06/07): obraz z sugestii wizualu przez OpenAI gpt-image
    (klucz 'openai_api_key' juz w sejfie - uzywa go tez content_memory). Zwraca bytes PNG.
    Regula prawdy dla obrazow: estetyka grafiki/ilustracji, zero udawania zdjec realnych wydarzen."""
    import base64
    import httpx as _httpx
    if not _openai_key[0]:
        _openai_key[0] = _db.fetchone("SELECT value FROM app_secrets WHERE key='openai_api_key'")
        _openai_key[0] = _openai_key[0]["value"] if _openai_key[0] else ""
    if not _openai_key[0]:
        raise RuntimeError("brak openai_api_key w app_secrets")
    r = _httpx.post("https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {_openai_key[0]}"},
                    json={"model": "gpt-image-1", "prompt": prompt[:3500],
                          "size": "1536x1024", "quality": "medium"},
                    timeout=120)
    r.raise_for_status()
    b64 = r.json()["data"][0]["b64_json"]
    return base64.b64decode(b64)


def generate_variant(brand, canonical_body, channel, content_item_id=None):
    """Adaptacja per kanal; model per task z routera R4 (default haiku); jezyk per cel (R6)."""
    model, tier, source = tasks.model_for("variant")
    guide = CHANNEL_GUIDE.get(channel, f"{channel}: adapt naturally for this platform.")
    lang = _language_publish(brand.get("brand_id", "AGS"), channel)
    lang_guide = LANGUAGE_GUIDE.get(lang, f"Write the adaptation in language code '{lang}'.")
    msg = (f"Adapt the canonical post below for {channel}. {guide}\n{lang_guide}\n{TRUTH_GUARD}"
           f"{_learned_style(brand.get('brand_id', 'AGS'))}\n"
           f"Keep the brand voice. Zero em dashes. Return ONLY the adapted text.\n\nCANONICAL:\n{canonical_body}")
    resp = client().messages.create(
        model=model, max_tokens=2000,
        thinking={"type": "disabled"},  # gdy config podbije tier na Sonnet 5, thinking nie moze wlaczyc sie domyslnie
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    tasks.log_task("variant", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp), getattr(resp, "usage", None)
