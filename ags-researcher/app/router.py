"""QueryRouter: classify a query into low/medium/high/critical and pick the source set."""
import re

from . import config

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

    def sources(self, level: str) -> list[str]:
        """Sources for the level, with optional ones dropped when their key is missing."""
        return config.active_sources(level)
