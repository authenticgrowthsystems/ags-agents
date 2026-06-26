"""Structured-output schema for synthesis. Sonnet 4.6 is forced to emit ResearchOutput."""
from pydantic import BaseModel, Field


class Claim(BaseModel):
    text: str
    supporting_evidence: list[str] = Field(default_factory=list)  # evidence_id (UUID str)
    confidence: float
    conflict_flag: bool = False


class ResearchOption(BaseModel):
    label: str                       # one of config.OPTIONS_LABELS
    description: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    supporting_claims: list[str] = Field(default_factory=list)
    rank_order: int


class ResearchOutput(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)
    overall_confidence: float = 0.0
    options: list[ResearchOption] = Field(default_factory=list)  # exactly 4, enforced post-parse by _enforce_four (optional here so a truncated/partial model output degrades instead of crashing the job)
    recommendation: str | None = None
