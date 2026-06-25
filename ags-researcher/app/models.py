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
    overall_confidence: float
    options: list[ResearchOption]    # exactly 4 (validated post-parse)
    recommendation: str | None = None
