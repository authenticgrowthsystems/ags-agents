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

# --- models ---
SYNTH_MODEL = os.getenv("SYNTH_MODEL", "claude-sonnet-4-6")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536
OPENAI_DR_HIGH = os.getenv("OPENAI_DR_HIGH", "o4-mini-deep-research")
OPENAI_DR_CRITICAL = os.getenv("OPENAI_DR_CRITICAL", "o3-deep-research")

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
SOURCE_TIMEOUT_S = _i("SOURCE_TIMEOUT_S", 300)
PARTIAL_AFTER_S = _i("PARTIAL_AFTER_S", 180)
SOURCE_RETRIES = _i("SOURCE_RETRIES", 2)
POLL_INTERVAL_S = _i("POLL_INTERVAL_S", 5)
ASYNC_POLL_INTERVAL_S = _i("ASYNC_POLL_INTERVAL_S", 20)
HTTP_PORT = _i("HTTP_PORT", 8088)
MIN_SOURCES_FOR_CONFIDENCE = _i("MIN_SOURCES_FOR_CONFIDENCE", 2)
PARTIAL_CONFIDENCE_CAP = _f("PARTIAL_CONFIDENCE_CAP", 0.5)

# --- source routing policy (cost cascade) ---
SOURCE_POLICY = {
    "low": ["web_search"],
    "medium": ["web_search", "firecrawl"],
    "high": ["web_search", "firecrawl", "openai_dr"],
    "critical": ["web_search", "firecrawl", "openai_dr", "gemini_dr", "manus"],
}
# sources skipped automatically when their API key is absent (must not block LIVE)
OPTIONAL_SOURCES = {"manus", "gemini_dr"}

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
ASYNC_SOURCES = {"openai_dr", "gemini_dr", "manus"}

OPTIONS_LABELS = ["Najszybsza", "Najtansza", "Najwyzsze upside", "Najwyzsza pewnosc"]


def source_key(source: str) -> str:
    return {
        "firecrawl": FIRECRAWL_API_KEY,
        "gemini_dr": GEMINI_API_KEY,
        "manus": MANUS_API_KEY,
        "openai_dr": OPENAI_API_KEY,
        "web_search": ANTHROPIC_API_KEY,
    }.get(source, "")


def active_sources(level: str) -> list[str]:
    """Sources for a complexity level, dropping optional ones whose key is missing."""
    out = []
    for s in SOURCE_POLICY.get(level, ["web_search"]):
        if s in OPTIONAL_SOURCES and not source_key(s):
            continue
        out.append(s)
    return out
