"""QueryRouter: classify a query into low/medium/high/critical and pick the source set."""
import re

from . import config, site

_MEDIUM_KW = re.compile(
    r"\b(compare|comparison|alternativ\w*|strateg\w*|deep|research|best\s+practic\w*|"
    r"recommend\w*|guide|tutorial|architect\w*|orchestrat\w*|scal\w*|optimi[sz]\w*|"
    r"por[oó]wn\w*|opcj\w*|architekt\w*|orkiestr\w*|praktyk\w*|najlep\w*|rekomend\w*|"
    r"skalow\w*|wydajn\w*|multi[- ]?agent|postgres\w*)",
    re.I,
)
_CRITICAL_KW = re.compile(r"\b(urgent|critical|high[- ]?stakes|piln\w*|krytyczn\w*)", re.I)


class QueryRouter:
    def classify(self, query_text: str) -> str:
        q = query_text or ""
        if _CRITICAL_KW.search(q):
            return "critical"
        if len(q) > 500 or _MEDIUM_KW.search(q):
            return "medium"
        return "low"

    def sources(self, level: str, query_text: str = "") -> list[str]:
        """Sources for the level, with optional ones dropped when their key is missing.

        'site' (24/07) pobiera strone BADANEGO PODMIOTU, wiec ma sens wylacznie wtedy, gdy
        zapytanie niesie adres ('strona: <url>' albo goly link). Pytanie tematyczne nie tworzy
        pustego przebiegu - odsiewamy je tutaj, zanim powstanie wiersz w research_runs."""
        srcs = config.active_sources(level)
        if "site" in srcs and not site.extract_url(query_text):
            srcs = [s for s in srcs if s != "site"]
        return srcs
