"""Generation: Sonnet for the canonical tekst-matka, Haiku for per-channel variants. Brand voice comes from
the cached system block (brand.system_blocks), so the voice prefix is reused cheaply across calls."""
import anthropic

from . import config
from .brand import system_blocks

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _text(resp):
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


def generate_canonical(brand, master_theme, research_context=""):
    """Sonnet -> the canonical post body in brand voice (channel adapters transform it later)."""
    msg = f"Write a canonical post for the theme: {master_theme}."
    if research_context:
        msg += f"\n\nGround it in this evidence (use what is relevant, do not list sources):\n{research_context[:6000]}"
    msg += "\n\nReturn ONLY the post body. Brand voice. Zero em dashes."
    resp = client().messages.create(
        model=config.CANONICAL_MODEL, max_tokens=1500,
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    return _text(resp), getattr(resp, "usage", None)


CHANNEL_GUIDE = {
    "x": "X/Twitter: at most 280 characters, one strong hook line, at most one hashtag.",
    "linkedin": "LinkedIn: up to ~1300 characters, problem then decision then mechanism then result, professional but human.",
    "youtube": "YouTube: a title line plus a 2 to 3 line description.",
    "facebook": "Facebook: a short conversational post.",
    "instagram": "Instagram: a caption with a strong first line.",
}


def generate_variant(brand, canonical_body, channel):
    """Haiku -> a platform-ready adaptation of the canonical body for one channel."""
    guide = CHANNEL_GUIDE.get(channel, f"{channel}: adapt naturally for this platform.")
    msg = (f"Adapt the canonical post below for {channel}. {guide}\n"
           f"Keep the brand voice. Zero em dashes. Return ONLY the adapted text.\n\nCANONICAL:\n{canonical_body}")
    resp = client().messages.create(
        model=config.VARIANT_MODEL, max_tokens=800,
        system=system_blocks(brand),
        messages=[{"role": "user", "content": msg}],
    )
    return _text(resp), getattr(resp, "usage", None)
