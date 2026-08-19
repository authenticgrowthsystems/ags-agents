"""Central config for the CM (Content Manager) agent. Mirrors the Researcher's conventions.
API keys live in app_secrets (single source); the worker .env carries only POSTGRES_DSN + N8N_BASE_URL."""
import os


def _i(name, default):
    v = os.getenv(name)
    return int(v) if v not in (None, "") else default


def _f(name, default):
    v = os.getenv(name)
    return float(v) if v not in (None, "") else default


# --- connections ---
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "").rstrip("/")
# Researcher is reachable on the shared docker network; CM commissions research via its /request webhook.
RESEARCHER_URL = os.getenv("RESEARCHER_URL", "http://ags-researcher:8088").rstrip("/")

# --- secrets (loaded from app_secrets at startup; never in code/.env/logs) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
RESEARCHER_WEBHOOK_SECRET = os.getenv("RESEARCHER_WEBHOOK_SECRET", "")  # shared guard for /request calls
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
LOG_BOT_TOKEN = os.getenv("LOG_BOT_TOKEN", "")  # bot #2: log channel (publish confirmations), decision D1

# --- models (verified ids; same map as Researcher) ---
TIER_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-5",   # upgraded 30/06 from claude-sonnet-4-6 (near-Opus quality)
    "opus": "claude-opus-4-8",
}
MODEL_RATES = {  # input / output USD per 1M
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    # Sonnet 5 sticker $3/$15 (intro $2/$10 through 2026-08-31). Sticker used here for conservative budgeting;
    # NOTE the Sonnet 5 tokenizer emits ~30% more tokens for the same text, so real per-job cost rises ~30%.
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
}
CANONICAL_MODEL = TIER_MODELS[os.getenv("CM_CANONICAL_TIER", "sonnet")]   # tekst-matka
VARIANT_MODEL = TIER_MODELS[os.getenv("CM_VARIANT_TIER", "haiku")]        # per-channel adaptacja
COMPLIANCE_MODEL = TIER_MODELS[os.getenv("CM_COMPLIANCE_TIER", "haiku")]  # redraft on canon fail
CONVERSATION_MODEL = TIER_MODELS[os.getenv("CM_CONVERSATION_TIER", "opus")]  # rozmowa strategiczna = Opus 4.8 (R4);
# override bez deployu: brand_config klucz 'cm_tier_conversation' czytany live w conversation._conversation_model()


def rates_for_model(model):
    return MODEL_RATES.get(model, MODEL_RATES["claude-sonnet-5"])


# --- loop / http ---
HTTP_PORT = _i("HTTP_PORT", 8089)            # Researcher = 8088
POLL_INTERVAL_S = _i("POLL_INTERVAL_S", 30)  # slow backstop; /request + callbacks wake the loop
RESEARCH_TIER = os.getenv("CM_RESEARCH_TIER", "medium")  # CM is capped to <=medium (critical-restriction)

# D-008 (03/08/2026): JEDNO ZRODLO nazwy stanu "rozeslane do kolejki" w content_items.status.
# Stara nazwa 'dispatching' brzmiala jak stan PRZELOTNY ("wysylam"), a stan normalnie trwa DNI -
# Manager 27/07 wyciagnal z niej rozsadny, ale falszywy wniosek o zawieszonym poscie (AP-312).
# 'handed_off' to slowo, ktore ta kodebaza wybrala sama, zanim ktokolwiek przemianowal wartosc:
# "dispatch = HAND-OFF, nie publikacja" (worker) i "Every mode here just HANDS OFF" (channels).
# NIE 'awaiting_*': stan konczy sie, gdy wiersze kolejki przestaja sie ruszac - OBOJETNIE CZYM
# (_DISPATCH_OK zawiera 'held', czyli gotowiec reczny), wiec obietnica publikacji bylaby AP-312
# odtworzonym wewnatrz poprawki na AP-312. Osobno: agent_registry.current_gate uzywa juz
# przedrostka awaiting_* w ZNACZENIU "czekam na bramke zatwierdzenia".
#
# UWAGA PRZY CZYTANIU KODU: post_queue.status MA WLASNA wartosc 'dispatching' i to jest INNY
# slownik - jeden wiersz kolejki oddany subagentowi. D-008 jej NIE dotyka.
STATUS_HANDED_OFF = "handed_off"

# content_items states the loop actively advances. STATUS_HANDED_OFF is NO LONGER here (backlog b):
# once dispatched, the item waits for the REAL publish callback (post_queue -> 'published' via Scheduler /
# sub-agent adapter) reconciled by worker.reconcile_publications - NOT re-claimed by the loop.
ACTIONABLE_STATUSES = ("planned", "needs_research", "drafting", "approved")

# backlog b: how long an item may sit in STATUS_HANDED_OFF (waiting for the publish callback) before CM
# raises a loud alert on the log bot - this is what surfaces a silent X publish/media failure.
DISPATCH_TIMEOUT_H = _i("DISPATCH_TIMEOUT_H", 2)

# --- channel publish modes (channels.config.publish_mode) ---
PUBLISH_POST_QUEUE = "post_queue"  # write a post_queue row; the existing per-minute Scheduler publishes (X)
PUBLISH_DRAFT = "draft"            # write a draft row; Tomasz publishes manually (LinkedIn for now)
PUBLISH_WEBHOOK = "webhook"        # POST the channel's adapter_path (ZABRONIONY - blokada nizej)

# --- D-020 (19/08/2026): blokada trybu 'webhook' stoi TU, w kodzie, nie w dokumencie ---
# Powod, doslownie: `DEPLOY_CHECKLIST` przez trzy tygodnie po incydencie AP-307 nadal instruowal,
# zeby ten tryb ustawic, i wygladal przy tym swiezo. Warunek zapisany w dokumencie jest
# ZALOZENIEM, nie zabezpieczeniem (AP-314, AP-316). Kazda droga ustawiajaca publish_mode
# przechodzi przez sprawdz_tryb_publikacji() i przy 'webhook' pada glosno, z powodem przy sobie.
WEBHOOK_HASLO_ODBLOKOWANIA = "AP-307-callback-naprawiony"


class TrybPublikacjiZabroniony(ValueError):
    """Proba ustawienia publish_mode='webhook' bez swiadomego zdjecia blokady (D-020)."""


ZAKAZ_WEBHOOK = (
    "Nie ustawie publish_mode='webhook'. Ten tryb jest zabroniony od 22/07/2026 po incydencie "
    "AP-307: delegat strzela do adaptera NATYCHMIAST przy dispatchu i sloty ignoruje w calosci.\n"
    "Skutki byly cztery, wszystkie publiczne tego samego dnia: 4-5 postow X w ciagu godziny "
    "zamiast rozproszenia; wiersze z mediami wyszly BEZ mediow, bo delegat przekazuje sam tekst; "
    "polski wariant wyszedl na anglojezycznym profilu LinkedIn mimo language_publish='en'; "
    "a callback publishera oznaczyl 'published' WSZYSTKIE wiersze materialu, takze te ze slotami "
    "kilka godzin pozniej, wiec baza klamala o wlasnym stanie.\n"
    "Callback per wiersz do dzis NIE jest naprawiony (swiadoma decyzja, uzbrojona mina), wiec "
    "czwarty skutek wrocilby co do znaku.\n"
    "Uzyj 'post_queue' (publikuje Scheduler per slot wiersza, razem z mediami) albo 'draft' "
    "(gotowiec do recznej wklejki, domykasz go poleceniem 'wklejone <id>').\n"
    "Swiadome zdjecie blokady: w srodowisku workera ustaw "
    "PUBLISH_WEBHOOK_ODBLOKOWANY=" + WEBHOOK_HASLO_ODBLOKOWANIA + " i zrestartuj kontener. "
    "Wartosc 'true' ani '1' NIE zadziala, celowo - haslo nazywa warunek, ktory ma byc spelniony. "
    "Przedtem przeczytaj docs/anti-patterns/AP-307_nowy_kontrakt_bez_przelaczenia_konsumenta.md."
)


def sprawdz_tryb_publikacji(tryb, gdzie=""):
    """Bramka D-020. Kazda droga ustawiajaca publish_mode przechodzi TEDY.

    Zwraca napis-ostrzezenie do doklejenia do paragonu (pusty = nie ma o czym mowic).
    Przy 'webhook' bez zdjetej blokady rzuca TrybPublikacjiZabroniony - nigdy nie poprawia
    wartosci po cichu, bo cicha korekta wyglada jak sukces (AP-306).

    Zmienna srodowiskowa czytana przy KAZDYM wywolaniu, nie przy imporcie: blokada ma odpowiadac
    stanowi srodowiska, a nie chwili startu procesu."""
    if str(tryb or "").strip().lower() != PUBLISH_WEBHOOK:
        return ""
    czyje = f"{gdzie}: " if gdzie else ""
    if os.getenv("PUBLISH_WEBHOOK_ODBLOKOWANY", "").strip() != WEBHOOK_HASLO_ODBLOKOWANIA:
        raise TrybPublikacjiZabroniony(czyje + ZAKAZ_WEBHOOK)
    return (f"UWAGA: {czyje}blokada trybu 'webhook' jest ZDJETA zmienna PUBLISH_WEBHOOK_ODBLOKOWANY. "
            "Publikacja idzie teraz sciezka delegata: sloty i media sa pomijane (AP-307). "
            "Sprawdz, czy callback publishera oznacza JEDEN wiersz, a nie caly material.")

# brand voice prompt-cache: voice_bible is a stable system block we mark cache_control ephemeral.
USD_PLN = _f("USD_PLN", 4.0)

# LinkedIn REST versioning header (YYYYMM); fakty: docs/research/LINKEDIN_STATISTICS_API_2026.md
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202606")
