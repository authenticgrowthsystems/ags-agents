"""Brand canon enforcement: deterministic em/en-dash removal (Rule 1) always, a Haiku redraft when
banned vocabulary is present, plus (06/07, feedback Tomasza) a PURE-POLISH pass for Polish texts:
poprawna odmiana i skladnia, zero kalk z angielskiego (doktryna jezykowa: 'test mamy')."""
import re

from . import config, tasks
from .generate import client

_DASH = re.compile(r"\s*[—–]\s*")  # em dash + en dash with surrounding space
_PL_DIACRITICS = re.compile(r"[ąćęłńóśżź]")


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


def enforce(brand, text, content_item_id=None):
    """Return clean text: dashes deterministically; banned vocab -> LLM rewrite; polski tekst ->
    filtr czystej polszczyzny (jeden przebieg, tier compliance)."""
    text = fix_dashes(text)
    banned = find_banned(text, brand.get("banned_vocab"))
    if banned:
        text = fix_dashes(_rewrite(
            f"Rewrite the text removing these banned words/phrases entirely while keeping the "
            f"meaning and voice: {', '.join(banned)}. Zero em dashes. Return ONLY the rewritten text.",
            text, content_item_id))
    text = polish_pl(text, content_item_id)
    return text
