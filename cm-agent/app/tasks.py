"""R4 model selection: per-task tier router + cm_tasks ledger (wzorzec Researcher model_selection).
Defaults: strategia=opus, mid=sonnet, routine=haiku. Override bez deployu: brand_config klucz
cm_tier_<task_type> (ustawiany przez /set albo guziki cmtier:<task_type>:<tier> w HITL, ktore
dodatkowo loguja korekte do agent_approval_gates type 'model_selection' - approval-learning)."""
from . import db, config

DEFAULT_TIERS = {
    "conversation": "opus",     # dyskusja strategiczna z Tomaszem (R4: Opus 4.8)
    "planner": "opus",          # plan tygodnia / 2 miesiecy (Faza 2)
    "canonical": "sonnet",      # tekst-matka
    "weekly_report": "sonnet",  # analiza tygodniowa subagenta
    "subagent_chat": "sonnet",  # rozmowa o kolejce (jakosc polszczyzny > koszt; /set moze zbic na haiku)
    "variant": "haiku",         # adaptacja per kanal
    "compliance": "haiku",      # redraft po banned vocab
    "daily_report": "haiku",    # zestawienie dzienne
    "memory_summary": "haiku",  # skrot wygasajacego watku rozmowy (pamiec dlugoterminowa, 10/07)
}


def tier_for(task_type):
    """(tier, source): source = 'config' gdy brand_config nadpisuje, inaczej 'auto' (default)."""
    row = db.fetchone(
        "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key=%s ORDER BY version DESC LIMIT 1",
        (f"cm_tier_{task_type}",),
    )
    v = str((row or {}).get("config_value") or "").strip()
    if v in config.TIER_MODELS:
        return v, "config"
    return DEFAULT_TIERS.get(task_type, "sonnet"), "auto"


def model_for(task_type):
    tier, source = tier_for(task_type)
    return config.TIER_MODELS[tier], tier, source


def log_task(task_type, tier, model, source, usage=None, content_item_id=None):
    """Ledger operacji CM (koszt liczony ze stawek konfiguracyjnych). Nigdy nie wywraca produkcji."""
    tin = getattr(usage, "input_tokens", None)
    tout = getattr(usage, "output_tokens", None)
    cost = None
    if tin is not None and tout is not None:
        ri, ro = config.rates_for_model(model)
        cost = round((tin * ri + tout * ro) / 1_000_000, 5)
    try:
        db.execute(
            """INSERT INTO cm_tasks (task_type, content_item_id, model_tier, model, tier_source, tokens_in, tokens_out, cost_usd)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (task_type, content_item_id, tier, model, source, tin, tout, cost),
        )
    except Exception:
        pass  # brak tabeli (przed DDL 004) albo chwilowy blad DB nie moze blokowac generacji
