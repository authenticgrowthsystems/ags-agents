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
    # C (feedback 07/07): personal profile = PIERWSZOOSOBOWY glos czlowieka, nie ujawniaj maszynowego
    # autorstwa POSTU (LinkedIn preferuje ludzi, wiarygodnosc Tomasza); o agentach ktore buduje - moze.
    "linkedin": ("LinkedIn (Tomasz's PERSONAL profile): up to ~1300 characters, problem then decision then "
                 "mechanism then result. Write as Tomasz's own FIRST-PERSON human post, authentic founder "
                 "voice. He may talk about the agents and systems he builds (that is his work), but the post "
                 "MUST read as written by a human and MUST NOT reveal or imply that this post itself was "
                 "generated or published by a machine/agent. "
                 "MANDATORY Re-Introduction Line (Voice Bible v2.1): include EXACTLY ONE sentence (~10-25 words) "
                 "that says who Tomasz is + what he concretely builds + for whom, woven naturally into the post "
                 "(opening, mid-bridge, or signature), varied each time, NOT a template banner and NOT a CTA."),
    "linkedin_page": ("LinkedIn AGS COMPANY page: up to ~1300 characters, problem then mechanism then result, "
                      "company voice. May speak openly about AGS building agents and autonomous systems "
                      "('AGS builds', 'we build'). Human-readable, zero AI-slop. "
                      "MANDATORY Re-Introduction Line (Voice Bible v2.1): include EXACTLY ONE sentence saying what "
                      "AGS builds and for whom, woven naturally (slide 1 or outro), not a template banner."),
    "youtube": "YouTube: a title line plus a 2 to 3 line description.",
    "facebook": "Facebook: a short conversational post.",
    "instagram": "Instagram: a caption with a strong first line.",
}


def _channel_voice_note(brand_id, channel):
    """C: per-konto notka glosu/autorstwa z channels.config.voice_note (edytowalna przez target_update).
    Nadpisuje/uzupelnia domyslny CHANNEL_GUIDE - substrat pod multi-konto (D)."""
    try:
        r = _db.fetchone("SELECT config->>'voice_note' AS vn FROM channels WHERE brand_id=%s AND channel=%s",
                         (brand_id, channel))
        return ((r or {}).get("vn") or "").strip()
    except Exception:
        return ""


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


_LANG_NAME = {"pl": "polski", "en": "English", "de": "Deutsch"}


def translate_text(text, target_lang, content_item_id=None):
    """T8 (feedback 07/08): wierny przeklad tresci na jezyk komunikacji (kopia do przegladu/edycji).
    Publikacja zostaje native w swoim jezyku; PL trzymamy obok, zeby Tomasz czytal/edytowal po polsku."""
    text = (text or "").strip()
    if not text:
        return ""
    model, tier, source = tasks.model_for("variant")  # haiku, tanie
    name = _LANG_NAME.get(target_lang, target_lang)
    resp = client().messages.create(
        model=model, max_tokens=2000, thinking={"type": "disabled"},
        messages=[{"role": "user", "content":
                   f"Przetlumacz WIERNIE ponizszy tekst na jezyk: {name}. Zachowaj sens, ton, akapity i "
                   f"dlugosc. Zero em-dash. To kopia do przegladu wlasciciela, nie do publikacji. Zwroc "
                   f"WYLACZNIE tlumaczenie.\n\n{text}"}])
    tasks.log_task("translate_review", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp)


def generate_variant(brand, canonical_body, channel, content_item_id=None):
    """Adaptacja per kanal; model per task z routera R4 (default haiku); jezyk per cel (R6)."""
    model, tier, source = tasks.model_for("variant")
    guide = CHANNEL_GUIDE.get(channel, f"{channel}: adapt naturally for this platform.")
    note = _channel_voice_note(brand.get("brand_id", "AGS"), channel)  # C: per-konto override
    if note:
        guide = f"{guide} ACCOUNT-SPECIFIC RULE: {note}"
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
