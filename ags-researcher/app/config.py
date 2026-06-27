"""Central config for the AGS Researcher worker. Every value is env-overridable."""
import os


def _f(name, default):
    v = os.getenv(name)
    return float(v) if v not in (None, "") else default


def _i(name, default):
    v = os.getenv(name)
    return int(v) if v not in (None, "") else default


def _b(name, default):
    v = os.getenv(name)
    return default if v in (None, "") else v.lower() in ("1", "true", "yes", "on")


# --- connections ---
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "").rstrip("/")

# --- API keys (Researcher reads-only the world; writes only its own DB tables) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MANUS_API_KEY = os.getenv("MANUS_API_KEY", "")

# Shared secret the worker sends as the X-Researcher-Secret header on every adapter call; the
# adapters reject calls without it (guards the credit-spending webhooks). Loaded from app_secrets
# at startup (single source) - the value never lives in code, .env, chat, or logs.
RESEARCHER_WEBHOOK_SECRET = os.getenv("RESEARCHER_WEBHOOK_SECRET", "")

# --- models ---
SYNTH_MODEL = os.getenv("SYNTH_MODEL", "claude-sonnet-4-6")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536
OPENAI_DR_HIGH = os.getenv("OPENAI_DR_HIGH", "o4-mini-deep-research")
# temp: validate Deep Research on the cheap model for both tiers. Switch CRITICAL to
# o3-deep-research once the router actually splits high (o4-mini) vs critical (o3).
OPENAI_DR_CRITICAL = os.getenv("OPENAI_DR_CRITICAL", "o4-mini-deep-research")

# --- model selection (per-job synth model tier) ---
# Tomasz / Manager pick a tier per query via payload.model_tier; falls back to DEFAULT_MODEL_TIER.
DEFAULT_MODEL_TIER = "sonnet"
TIER_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",  # cheap / fast
    "sonnet": "claude-sonnet-4-6",          # standard (default)
    "opus": "claude-opus-4-8",              # heavy / most capable
}
# input / output USD per 1M tokens (verified via claude-api skill 27/06). Cache: write 1.25x input, read 0.10x input.
MODEL_RATES = {
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
}


def model_for_tier(tier) -> str:
    """Resolve a tier label to a model id; unknown / None -> default tier."""
    return TIER_MODELS.get(tier or DEFAULT_MODEL_TIER, TIER_MODELS[DEFAULT_MODEL_TIER])


def rates_for_model(model):
    """(input_rate, output_rate) USD per 1M for a model; unknown -> sonnet rates."""
    return MODEL_RATES.get(model, MODEL_RATES["claude-sonnet-4-6"])


# auto-by-complexity (slice 2): the default tier when a REQUEST does not pin payload.model_tier.
# low -> haiku (cheap/simple), medium -> sonnet (full 4 options), high/critical -> opus (hardest).
LEVEL_TIERS = {"low": "haiku", "medium": "sonnet", "high": "opus", "critical": "opus"}


def tier_for_level(level) -> str:
    """Map a router complexity level to its default model tier."""
    return LEVEL_TIERS.get(level, DEFAULT_MODEL_TIER)

# --- budgets (PLN) ---
USD_PLN = _f("USD_PLN", 4.0)
BUDGET_PER_QUERY_PLN = _f("BUDGET_PER_QUERY_PLN", 50.0)
BUDGET_DAILY_PLN = _f("BUDGET_DAILY_PLN", 100.0)
BUDGET_MONTHLY_PLN = _f("BUDGET_MONTHLY_PLN", 1500.0)
OPENAI_DR_MAX_TOOL_CALLS = _i("OPENAI_DR_MAX_TOOL_CALLS", 20)
FIRECRAWL_MAX_CREDITS = _i("FIRECRAWL_MAX_CREDITS", 50)

# --- cache ---
# SEMANTIC_CACHE_ENABLED stays False until db/002_vector_addon.sql is applied (needs superuser once).
SEMANTIC_CACHE_ENABLED = _b("SEMANTIC_CACHE_ENABLED", False)
SEMANTIC_THRESHOLD = _f("SEMANTIC_THRESHOLD", 0.92)   # cosine similarity (1 - cosine_distance)
SEMANTIC_TTL_DAYS = _i("SEMANTIC_TTL_DAYS", 3)
# exact-match TTL (days) per content class
EXACT_TTL_DAYS = {"tooling": 7.0, "pricing": 1.0, "news": 0.25, "default": 7.0}

# --- failure / timing (seconds) ---
SOURCE_TIMEOUT_S = _i("SOURCE_TIMEOUT_S", 420)  # async sources (DR) can exceed 300s; sequential so keep modest
PARTIAL_AFTER_S = _i("PARTIAL_AFTER_S", 180)
SOURCE_RETRIES = _i("SOURCE_RETRIES", 2)
POLL_INTERVAL_S = _i("POLL_INTERVAL_S", 5)
ASYNC_POLL_INTERVAL_S = _i("ASYNC_POLL_INTERVAL_S", 20)
HTTP_PORT = _i("HTTP_PORT", 8088)
MIN_SOURCES_FOR_CONFIDENCE = _i("MIN_SOURCES_FOR_CONFIDENCE", 2)
PARTIAL_CONFIDENCE_CAP = _f("PARTIAL_CONFIDENCE_CAP", 0.5)

# --- source routing policy (cost cascade) ---
# Aspirational full cascade. active_sources() filters this to DEPLOYED_ADAPTERS, so a tier may
# name a source whose adapter is not built yet without the worker ever calling it.
SOURCE_POLICY = {
    "low": ["web_search"],
    "medium": ["web_search", "firecrawl", "gemini_dr"],
    "high": ["web_search", "firecrawl", "gemini_dr", "openai_dr"],
    "critical": ["web_search", "firecrawl", "gemini_dr", "openai_dr", "manus"],
}
# Adapters actually deployed + active in n8n right now. active_sources() routes ONLY to these.
# openai_dr LIVE 27/06 (START XmwNyZEGqe89plcy + STATUS FlkyrFad8U7CE4iS). manus LIVE 27/06
# (START eKD2tgXHrreWkGfN + STATUS iDNBK5Xdan44Mugd; task.create -> task.detail+listMessages,
# agent_profile lite). Both async start+poll, fire at the critical tier (DR + Manus together).
DEPLOYED_ADAPTERS = {"web_search", "firecrawl", "gemini_dr", "openai_dr", "manus"}

# n8n source-adapter webhook paths (Python orchestrator calls these)
ADAPTER_PATHS = {
    "web_search": "/webhook/researcher-web-search",
    "firecrawl": "/webhook/researcher-firecrawl",
    "openai_dr": "/webhook/researcher-openai-dr",
    "openai_dr_status": "/webhook/researcher-openai-dr-status",
    "gemini_dr": "/webhook/researcher-gemini-dr",
    "gemini_dr_status": "/webhook/researcher-gemini-dr-status",
    "manus": "/webhook/researcher-manus",
    "manus_status": "/webhook/researcher-manus-status",
    "callback": "/webhook/researcher-callback",
}
# gemini adapter returns evidence inline (sync); only DR / Manus are start+poll.
ASYNC_SOURCES = {"openai_dr", "manus"}

OPTIONS_LABELS = ["Najszybsza", "Najtansza", "Najwyzsze upside", "Najwyzsza pewnosc"]


def active_sources(level: str) -> list[str]:
    """Sources for a complexity level, filtered to adapters actually deployed in n8n.
    Source API keys live in app_secrets and are read by each n8n adapter itself, so the worker
    does not gate on keys here - it gates on which adapters exist (DEPLOYED_ADAPTERS)."""
    return [s for s in SOURCE_POLICY.get(level, ["web_search"]) if s in DEPLOYED_ADAPTERS]
