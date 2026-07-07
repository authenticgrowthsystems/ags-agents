"""Brand canon enforcement: deterministic em/en-dash removal (Rule 1) always, a Haiku redraft when
banned vocabulary is present, plus (06/07, feedback Tomasza) a PURE-POLISH pass for Polish texts:
poprawna odmiana i skladnia, zero kalk z angielskiego (doktryna jezykowa: 'test mamy')."""
import re

from psycopg.types.json import Jsonb

from . import config, tasks, db
from .generate import client

_DASH = re.compile(r"\s*[—–]\s*")  # em dash + en dash with surrounding space
_PL_DIACRITICS = re.compile(r"[ąćęłńóśżź]")

# Voice Bible v2.1 / Task #75: Re-Introduction Line dla LinkedIn (Zasada 10 Lara Acosta).
RE_INTRO_LINE_PROMPT = (
    "Sprawdz czy ponizszy tekst LinkedIn zawiera Re-Introduction Line: JEDNO zdanie (ok. 10-25 slow) "
    "laczace trzy elementy - kim jest autor + co konkretnie robi/buduje + dla kogo. NIE liczy sie: "
    "sama rola bez mechanizmu ('Founder of AGS'), samo CTA ('Book a call'), generyczne haslo "
    "('Helping people grow'), ani wielozdaniowy blok o autorze. Odpowiedz PIERWSZYM slowem: TAK albo NIE."
)


def fix_dashes(text):
    return _DASH.sub(", ", text or "")


def find_banned(text, banned_vocab):
    low = (text or "").lower()
    return [w for w in (banned_vocab or []) if w and re.search(r"\b" + re.escape(w.lower()) + r"\b", low)]


def looks_polish(text):
    """Heurystyka: >=4 polskie znaki diakrytyczne albo typowe slowa funkcyjne."""
    t = text or ""
    if len(_PL_DIACRITICS.findall(t)) >= 4:
        return True
    low = f" {t.lower()} "
    return sum(1 for w in (" się ", " że ", " jest ", " nie ", " który ", " ktora ") if w in low) >= 2


def _rewrite(prompt, text, content_item_id, task_name="compliance"):
    try:
        model, tier, source = tasks.model_for("compliance")
        resp = client().messages.create(
            model=model, max_tokens=1200, thinking={"type": "disabled"},
            messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
        )
        tasks.log_task(task_name, tier, model, source, getattr(resp, "usage", None), content_item_id)
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        return out or text
    except Exception:
        return text


def polish_pl(text, content_item_id=None):
    """Filtr poprawnej polszczyzny (feedback 06/07): odmiana, skladnia, naturalny szyk;
    kalki i anglicyzmy na polskie odpowiedniki (zostaja TYLKO utrwalone terminy techniczne
    bez polskiego odpowiednika). Sens, glos i dlugosc bez zmian."""
    if not looks_polish(text):
        return text
    return fix_dashes(_rewrite(
        "Popraw ponizszy polski tekst na NIENAGANNA polszczyzne: poprawna odmiana i skladnia, "
        "naturalny szyk zdania, zero kalk z angielskiego i zbednych anglicyzmow (zamien na polskie "
        "odpowiedniki; zostaw wylacznie utrwalone terminy techniczne bez polskiego odpowiednika). "
        "Test: czy moja mama by to zrozumiala i uznala za naturalne? NIE zmieniaj sensu, tonu ani "
        "dlugosci. Zero em dashes. Zwroc WYLACZNIE poprawiony tekst.",
        text, content_item_id, task_name="polish_pl"))


def check_re_intro_line(text, channel, content_item_id=None):
    """Voice Bible v2.1 / Task #75: LinkedIn content ma zawierac Re-Introduction Line (kim/co/dla kogo).
    FAZA 1 (decyzja Tomasza 07/07): WARN+log do agent_logs, NIE blokuje (nie ryzykujemy pierwszego
    postu falszywym blokiem). Hard-block po weryfikacji 2-3 postow. Nieblokujacy - zwraca tekst bez zmian."""
    if not channel or not str(channel).startswith("linkedin") or not (text or "").strip():
        return
    try:
        model, tier, source = tasks.model_for("compliance")  # haiku (spec v2.1)
        resp = client().messages.create(
            model=model, max_tokens=40, thinking={"type": "disabled"},
            messages=[{"role": "user", "content": f"{RE_INTRO_LINE_PROMPT}\n\nTEKST:\n{text[:2000]}"}])
        tasks.log_task("re_intro_check", tier, model, source, getattr(resp, "usage", None), content_item_id)
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip().upper()
        if not out.startswith("TAK"):
            db.execute(
                "INSERT INTO agent_logs (agent_id, log_type, rationale, context) VALUES ('cm','RE_INTRO_MISSING',%s,%s)",
                (f"LinkedIn {channel}: brak Re-Introduction Line (Voice Bible v2.1, warn-only faza 1)",
                 Jsonb({"channel": channel,
                        "content_item_id": str(content_item_id) if content_item_id else None})))
    except Exception:
        pass


def enforce(brand, text, content_item_id=None, channel=None):
    """Return clean text: dashes deterministically; banned vocab -> LLM rewrite; polski tekst ->
    filtr czystej polszczyzny (jeden przebieg, tier compliance). channel (v2.1): dla LinkedIn odpala
    nieblokujacy check Re-Introduction Line (warn+log)."""
    text = fix_dashes(text)
    banned = find_banned(text, brand.get("banned_vocab"))
    if banned:
        text = fix_dashes(_rewrite(
            f"Rewrite the text removing these banned words/phrases entirely while keeping the "
            f"meaning and voice: {', '.join(banned)}. Zero em dashes. Return ONLY the rewritten text.",
            text, content_item_id))
    text = polish_pl(text, content_item_id)
    check_re_intro_line(text, channel, content_item_id)  # v2.1: warn-only na razie
    return text
