"""Pydantic models for CM structured generation (tool-forced output, like the Researcher synth)."""
from pydantic import BaseModel, Field


class CanonicalDraft(BaseModel):
    """The brand-aware tekst-matka the channel adapters transform."""
    canonical_body: str = Field(..., description="The canonical post body, in brand voice, zero em dashes.")
    taxonomy: str = Field("edu", description="One of: build-report, news, edu")


class ChannelVariant(BaseModel):
    """A per-channel adaptation of the canonical body."""
    text: str = Field(..., description="Platform-ready text for this channel, brand voice, zero em dashes.")
