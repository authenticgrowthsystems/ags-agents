"""Generation: Sonnet for the canonical tekst-matka, Haiku for per-channel variants. Brand voice comes from
the cached system block (brand.system_blocks), so the voice prefix is reused cheaply across calls."""
import json
import re

import anthropic

from . import config, tasks
from . import db as _db
from .brand import system_blocks

_client = None


def client():
    global _client
    if _client is None:
        # max_retries: SDK ponawia 429/5xx/529 z backoffem (fix 07/08: 529 overloaded gubil propozycje/generacje)
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, max_retries=5)
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


def _channel_rules(brand_id, channel):
    """T (07/08): zasady konta z channels.config.rules (subagent_remember_rule) - generacja ich
    przestrzega (np. 'zadnych threadow do 1000 followers')."""
    try:
        r = _db.fetchone("SELECT config->'rules' AS rules FROM channels WHERE brand_id=%s AND channel=%s",
                         (brand_id, channel))
        return (r or {}).get("rules") or []
    except Exception:
        return []


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


def _image_quality():
    """Feedback Tomasza 10/07 ('ma byc premium'): default HIGH; zbicie kosztow bez deployu przez
    /set cm_image_quality medium."""
    row = _db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='cm_image_quality' ORDER BY version DESC LIMIT 1")
    v = str(((row or {}).get("config_value")) or "").strip().lower()
    return v if v in ("low", "medium", "high") else "high"


# Destylat sekcji 3 brand-canon/ags.md (fallback, gdy brand_config 'visual_canon' pusty).
# Kontener nie ma dostepu do repo - SSOT docelowo w brand_config (INSERT po stronie Tomasza).
_VISUAL_CANON_AGS = (
    "AGS visual canon: palette STRICTLY Soft Sandstone #F5F5F5 (light surfaces), Cosmic Navy #1A1A2E "
    "(dominant dark surfaces), Electric Cyan #00E0FF (max 1-2 small accents, never a fill), Muted Gold "
    "#D4AF37 (premium accent line or emphasis word), Subtle Red #C73E3A (only for 'wrong way' marks). "
    "Cosmic Navy + Soft Sandstone must cover ~80% of the composition. NO gradients, NO colors outside "
    "this palette. Typography: elegant serif display headline (Playfair Display style) OR bold modern "
    "grotesque; body/labels in clean sans (DM Sans/Inter style); technical labels in monospace "
    "(JetBrains Mono style). Signature motif: thin circuit-board trace lines with a small gold terminal "
    "pin, as subtle background texture at 5-10% opacity, occupying its own band, never overlapping "
    "text. Generous negative space, engineering precision, editorial minimal, geometric abstract. "
    "FORBIDDEN: stock-photo look, AI-generated faces or hands, gradient backgrounds, cyber "
    "blue-purple-pink palette, whimsical hand-drawn style, emoji clutter.")


_VISUAL_CANON_TNM = (
    "TNM visual canon (fallback do czasu brand_tokens): palette warm green + terracotta + cream "
    "(SOP dual-brand 12/07), clean editorial minimal, Polish market warmth, NO cyber-tech look, "
    "no gradients between palette colors, no stock-photo look, no AI faces.")


def _visual_canon(brand_id="AGS"):
    """Kanon wizualny marki do promptow graficznych (feedback Tomasza 10/07 'caly brand - kolory,
    fonty'). KOLEJNOSC ZRODEL (#84, 12/07): 1) brand_tokens (Notion SSOT, W3C DTCG JSON) ->
    2) brand_config 'visual_canon' -> 3) fallback w kodzie (AGS destylat / TNM barwy SOP)."""
    try:
        row = _db.fetchone("SELECT tokens FROM brand_tokens WHERE brand_id=%s", (brand_id,))
        toks = (row or {}).get("tokens")
        if toks:
            return ("BRAND TOKENS (source of truth - uzyj DOKLADNIE tych wartosci, hexy litera "
                    "w litere): " + json.dumps(toks, ensure_ascii=False)[:2600])
    except Exception:
        pass  # tabela przed DDL 019 albo chwilowy blad - lecimy fallbackami
    row = _db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id=%s AND config_key='visual_canon' ORDER BY version DESC LIMIT 1",
        (brand_id,))
    v = str(((row or {}).get("config_value")) or "").strip()
    if len(v) > 40:
        return v
    return _VISUAL_CANON_TNM if brand_id == "TNM" else _VISUAL_CANON_AGS


def hint_wants_generated_graphic(hint):
    """Czy sugestia wizualu to GRAFIKA do wygenerowania (nie zdjecie/screenshot/wideo, ktore robi
    czlowiek). Uzywane przez auto-grafike przed karta zatwierdzenia (feedback Tomasza 10/07)."""
    h = (hint or "").lower()
    if not h:
        return False
    if re.search(r"zdjec|zdjęc|foto|wideo|video|screencast|nagran|screenshot|zrzut", h):
        return False
    return bool(re.search(r"grafik|ilustracj|diagram|typograf|infografik|schemat|wykres|flowchart", h))


def generate_image_prompt(brand, master_theme, canonical_body, hint, guidance=None, content_item_id=None):
    """Feedback Tomasza 10/07: prompt graficzny ma byc BARDZO SZCZEGOLOWY, efekt premium, W BRANDZIE
    (kolory, fonty, motywy z kanonu wizualnego). Sonnet pisze pelny prompt po angielsku."""
    model, tier, source = tasks.model_for("image_prompt")
    guide = f"\n\nWSKAZOWKI WLASCICIELA (priorytet, zastosuj wprost): {guidance[:400]}" if guidance else ""
    brand_id = (brand or {}).get("brand_id") or "AGS"
    resp = client().messages.create(
        model=model, max_tokens=700, thinking={"type": "disabled"},
        messages=[{"role": "user", "content":
                   "Napisz JEDEN szczegolowy prompt (po angielsku, 150-250 slow) dla generatora obrazow "
                   "gpt-image do grafiki social media klasy PREMIUM, SCISLE w kanonie wizualnym marki "
                   "podanym nizej (dokladne hexy kolorow i proporcje z kanonu wpisz do promptu). Prompt "
                   "MUSI opisywac: dokladna kompozycje i uklad (co w centrum, co po bokach, ile wolnej "
                   "przestrzeni), palete WYLACZNIE z kanonu (z hexami), typografie zgodna z kanonem, "
                   "DOKLADNY krotki tekst na grafice (naglowek max 6 slow - podaj go doslownie w "
                   "cudzyslowie, generator ma go odwzorowac litera w litere), styl i motyw przewodni "
                   "z kanonu, format poziomy 3:2. ZAKAZY z kanonu wpisz do promptu, plus: no watermarks, "
                   "no lorem ipsum, no extra text beyond the specified headline. Zwroc WYLACZNIE prompt.\n\n"
                   f"KANON WIZUALNY MARKI:\n{_visual_canon(brand_id)}\n\n"
                   f"SUGESTIA WIZUALU: {(hint or 'clean conceptual illustration of the post theme')[:400]}\n"
                   f"TEMAT POSTA: {(master_theme or '')[:300]}\n"
                   f"TRESC POSTA (kontekst): {(canonical_body or '')[:1200]}{guide}"}])
    tasks.log_task("image_prompt", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp)[:3400]


def generate_image(prompt):
    """ETAP 2a (decyzja Tomasza 06/07): obraz z sugestii wizualu przez OpenAI gpt-image
    (klucz 'openai_api_key' juz w sejfie - uzywa go tez content_memory). Zwraca bytes PNG.
    Regula prawdy dla obrazow: estetyka grafiki/ilustracji, zero udawania zdjec realnych wydarzen.
    10/07: quality z configu (default high - 'ma byc premium')."""
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
                          "size": "1536x1024", "quality": _image_quality()},
                    timeout=180)
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


def describe_published_screenshot(image_bytes, media_type, content_item_id=None):
    """Intake publikacji zewnetrznej (wymog Tomasza 10/07: 'opublikowalem to i tam' + zrzut):
    Claude vision opisuje zrzut WLASNEGO opublikowanego posta - temat + platforma jesli widoczna.
    Zwraca 1-2 zdania PL (do master_theme i pamieci)."""
    import base64
    model, tier, source = tasks.model_for("canonical")
    b64 = base64.b64encode(image_bytes).decode()
    resp = client().messages.create(
        model=model, max_tokens=250, thinking={"type": "disabled"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text":
             "To zrzut WLASNEGO opublikowanego posta wlasciciela. Opisz w 1-2 zdaniach po polsku: "
             "temat/teza posta (+ platforma, jesli widoczna na zrzucie). Czysta polszczyzna, zero "
             "em dash. WYLACZNIE to, co realnie widac. Zwroc sam opis."}]}])
    tasks.log_task("external_pub_vision", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp)[:400]


def inspect_image(image_bytes, media_type, question=None, content_item_id=None):
    """Luka 10/07 ('czemu refleksja i reflection?'): agent OGLADA zalacznik materialu i odpowiada
    na pytanie Tomasza o grafike (albo ja opisuje). Zwraca odpowiedz PL."""
    import base64
    model, tier, source = tasks.model_for("canonical")
    b64 = base64.b64encode(image_bytes).decode()
    ask = (question or "").strip() or "Opisz dokladnie co jest na tej grafice (uklad, teksty, kolory)."
    resp = client().messages.create(
        model=model, max_tokens=400, thinking={"type": "disabled"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text":
             f"To grafika dopieta do materialu contentowego wlasciciela. {ask}\n"
             f"Odpowiedz po polsku, czysta polszczyzna, zero em dash, WYLACZNIE o tym co widac."}]}])
    tasks.log_task("inspect_image", tier, model, source, getattr(resp, "usage", None), content_item_id)
    return _text(resp)[:1200]


def comment_from_image(image_bytes, media_type, brand, channel, lang="en"):
    """T9 (07/08): Claude VISION analizuje zrzut z 1+ postami/komentarzami i proponuje odpowiedz
    comment-first PER element (autor osobno). Jezyk celu. Glos marki. Zero pitchu."""
    import base64
    model, tier, source = tasks.model_for("canonical")  # sonnet - jakosc komentarzy
    b64 = base64.b64encode(image_bytes).decode()
    prompt = (f"Na obrazie sa JEDEN lub WIECEJ postow/komentarzy z {channel}. Dla KAZDEGO osobno "
              f"(podaj autora jesli widoczny) zaproponuj 1 wartosciowy komentarz-odpowiedz (doktryna "
              f"comment-first): konkretna wartosc, doswiadczenie albo kontrprzyklad, ton peer-level, "
              f"2-4 zdania, ZERO linkow, zero pitchu, zero pustych pochlebstw ('great post'). "
              f"Jezyk: {'polski (czysty, test mamy)' if lang == 'pl' else 'angielski'}. {TRUTH_GUARD}\n"
              f"Format:\n### <Autor 1>\n<komentarz>\n\n### <Autor 2>\n<komentarz>")
    resp = client().messages.create(
        model=model, max_tokens=1200, thinking={"type": "disabled"},
        system=[{"type": "text", "text": f"Glos marki:\n{brand['voice_bible'][:2500]}"}],
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": prompt}]}])
    tasks.log_task("comment_vision", tier, model, source, getattr(resp, "usage", None))
    return _text(resp)


def generate_variant(brand, canonical_body, channel, content_item_id=None):
    """Adaptacja per kanal; model per task z routera R4 (default haiku); jezyk per cel (R6)."""
    model, tier, source = tasks.model_for("variant")
    guide = CHANNEL_GUIDE.get(channel, f"{channel}: adapt naturally for this platform.")
    note = _channel_voice_note(brand.get("brand_id", "AGS"), channel)  # C: per-konto override
    if note:
        guide = f"{guide} ACCOUNT-SPECIFIC RULE: {note}"
    rules = _channel_rules(brand.get("brand_id", "AGS"), channel)  # T: zasady konta (nadrzedne)
    if rules:
        guide = f"{guide} OWNER RULES FOR THIS ACCOUNT (obey strictly, override defaults if conflict): " + "; ".join(rules[-10:])
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
