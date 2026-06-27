"""FailureHandler: decide job outcome from how many sources yielded evidence (graceful degradation)."""
from . import config


class FailureHandler:
    @staticmethod
    def assess(evidence_by_source: dict) -> tuple[str, float | None]:
        """Return (job_status, confidence_cap). confidence_cap is None when full, else an upper bound.
        partial_failure means sources FAILED, not that a cheap tier intentionally used fewer sources:
        a low-tier job that dispatched 1 source and got it back is 'completed' (single-source cap),
        not partial. A job where fewer sources returned than were dispatched IS partial (something broke)."""
        dispatched = len(evidence_by_source)
        n = len([s for s, ev in evidence_by_source.items() if ev])
        if n == 0:
            return "failed", 0.0
        if n >= config.MIN_SOURCES_FOR_CONFIDENCE:
            return "completed", None
        if n == dispatched:
            # all intentionally-dispatched sources succeeded (e.g. low tier = 1 source): not a failure
            return "completed", config.PARTIAL_CONFIDENCE_CAP
        # fewer sources came back than were dispatched -> some genuinely failed
        return "partial_failure", config.PARTIAL_CONFIDENCE_CAP

    @staticmethod
    def cap_confidence(value: float, cap: float | None) -> float:
        v = float(value or 0)
        return min(v, cap) if cap is not None else v
