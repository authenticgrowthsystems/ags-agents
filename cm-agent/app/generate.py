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


def generate_canonical(brand, master_theme, research_context="", content_item_id=None):
    """Tekst-matka; model per task z routera R4 (default sonnet, override brand_config cm_tier_canonical)."""
    model, tier, source = tasks.model_for("canonical")
    msg = f"Write a canonical post for the theme: {master_theme}."
    if research_context:
        msg += f"\n\nGround it in this evidence (use what is relevant, do not list sources):\n{research_context[:6000]}"
    msg += "\n\nReturn ONLY the post body. Brand voice. Zero em dashes."
    resp = client().messages.create(
        model=model, max_tokens=1500,
        thinking={"type": "disabled"},  # Sonnet 5 defaults thinking ON when omitted; keep it off (preserves budget)
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    tasks.log_task("canonical", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp), getattr(resp, "usage", None)


CHANNEL_GUIDE = {
    "x": "X/Twitter: at most 280 characters, one strong hook line, at most one hashtag.",
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


def generate_variant(brand, canonical_body, channel, content_item_id=None):
    """Adaptacja per kanal; model per task z routera R4 (default haiku); jezyk per cel (R6)."""
    model, tier, source = tasks.model_for("variant")
    guide = CHANNEL_GUIDE.get(channel, f"{channel}: adapt naturally for this platform.")
    lang = _language_publish(brand.get("brand_id", "AGS"), channel)
    lang_guide = LANGUAGE_GUIDE.get(lang, f"Write the adaptation in language code '{lang}'.")
    msg = (f"Adapt the canonical post below for {channel}. {guide}\n{lang_guide}\n"
           f"Keep the brand voice. Zero em dashes. Return ONLY the adapted text.\n\nCANONICAL:\n{canonical_body}")
    resp = client().messages.create(
        model=model, max_tokens=800,
        thinking={"type": "disabled"},  # gdy config podbije tier na Sonnet 5, thinking nie moze wlaczyc sie domyslnie
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    tasks.log_task("variant", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp), getattr(resp, "usage", None)
