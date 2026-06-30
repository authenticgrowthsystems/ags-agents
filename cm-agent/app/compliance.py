"""Brand canon enforcement: deterministic em/en-dash removal (Rule 1) always, plus a Haiku redraft only when
banned vocabulary is present. Cheap and safe; the dash filter never depends on an LLM."""
import re

from . import config
from .generate import client

_DASH = re.compile(r"\s*[—–]\s*")  # em dash + en dash with surrounding space


def fix_dashes(text):
    return _DASH.sub(", ", text or "")


def find_banned(text, banned_vocab):
    low = (text or "").lower()
    return [w for w in (banned_vocab or []) if w and re.search(r"\b" + re.escape(w.lower()) + r"\b", low)]


def enforce(brand, text):
    """Return clean text: dashes fixed deterministically; if banned vocab remains, one Haiku rewrite."""
    text = fix_dashes(text)
    banned = find_banned(text, brand.get("banned_vocab"))
    if banned:
        try:
            resp = client().messages.create(
                model=config.COMPLIANCE_MODEL, max_tokens=900,
                messages=[{"role": "user", "content":
                           f"Rewrite the text removing these banned words/phrases entirely while keeping the "
                           f"meaning and voice: {', '.join(banned)}. Zero em dashes. Return ONLY the rewritten text."
                           f"\n\n{text}"}],
            )
            out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
            if out:
                text = fix_dashes(out)
        except Exception:
            pass
    return text
