"""FailureHandler: decide job outcome from how many sources yielded evidence (graceful degradation)."""
from . import config


class FailureHandler:
    @staticmethod
    def assess(evidence_by_source: dict) -> tuple[str, float | None]:
        """Return (job_status, confidence_cap).
        confidence_cap is None when full, else an upper bound the synthesis must respect."""
        ok = [s for s, ev in evidence_by_source.items() if ev]
        if len(ok) == 0:
            return "failed", 0.0
        if len(ok) < config.MIN_SOURCES_FOR_CONFIDENCE:
            return "partial_failure", config.PARTIAL_CONFIDENCE_CAP
        return "completed", None

    @staticmethod
    def cap_confidence(value: float, cap: float | None) -> float:
        v = float(value or 0)
        return min(v, cap) if cap is not None else v
