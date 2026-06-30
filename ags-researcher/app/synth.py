"""Synthesizer: Sonnet 4.6 turns one evidence pack into exactly 4 decision strategies.
Tool-forced structured output (robust across SDK versions) + prompt caching on the stable system block.
Brand voice is loaded from brand_config.voice_bible (single source of truth) when available."""
from anthropic import Anthropic

from . import config, db, models

_SYSTEM_STABLE = """Jestes Researcher AGS, agent badawczy wielu zrodel.
Rola: synteza evidence z wielu zrodel do DOKLADNIE 4 strategii decyzji.
Etykiety (dokladnie te, rank_order 1-4): Najszybsza, Najtansza, Najwyzsze upside, Najwyzsza pewnosc.
Najpierw wyznacz claims (fakty): text, supporting_evidence (lista evidence_id), confidence 0-1, conflict_flag=true gdy zrodla sie roznia.
Potem 4 opcje: description, pros[], cons[], supporting_claims (id z Twoich claims), rank_order.
Tresc: konwergencja (co potwierdzaja wszystkie zrodla) plus dywergencja (gdzie sie roznia).
Bez em-dashy (przecinek, dywiz, dwukropek). Liczby jako kotwice. Cytuj zrodla po evidence_id.
overall_confidence 0-1. Jesli mniej niz 2 zrodla daly evidence, ustaw overall_confidence <= 0.5.
Zwroc wynik WYLACZNIE przez narzedzie emit_research_output."""

_TOOL = {
    "name": "emit_research_output",
    "description": "Zwroc ustrukturyzowany wynik badania: claims plus dokladnie 4 opcje decyzji.",
    "input_schema": models.ResearchOutput.model_json_schema(),
}


class Synthesizer:
    def __init__(self):
        self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self._system = self._build_system()

    @staticmethod
    def _load_brand_voice() -> str:
        try:
            r = db.fetchone(
                "SELECT config_value FROM brand_config WHERE brand_id='AGS' AND config_key='voice_bible' LIMIT 1"
            )
            return (r or {}).get("config_value") or ""
        except Exception:
            return ""

    def _build_system(self):
        voice = self._load_brand_voice()
        text = _SYSTEM_STABLE + (f"\n\nGLOS MARKI (brand_config.voice_bible):\n{voice}" if voice else "")
        # one cached block: stable instructions + brand voice (~stable across queries)
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    def synthesize(self, query: str, evidence: list[dict], partial: bool = False, model: str = None):
        user = f"PYTANIE:\n{query}\n\nEVIDENCE ({len(evidence)} pozycji):\n{self._format_evidence(evidence)}"
        if partial:
            user += "\n\nUWAGA: czesc zrodel padla (dane czesciowe). overall_confidence <= 0.5."
        resp = self._client.messages.create(
            model=model or config.SYNTH_MODEL,
            max_tokens=8192,
            thinking={"type": "disabled"},  # Sonnet 5 defaults thinking ON; forced tool_choice needs it off
            system=self._system,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "emit_research_output"},
            messages=[{"role": "user", "content": user}],
        )
        data = None
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == "emit_research_output":
                data = block.input
                break
        if data is None:
            raise ValueError("synthesis: model returned no emit_research_output tool call")
        out = self._enforce_four(models.ResearchOutput.model_validate(data))
        return out, resp.usage

    @staticmethod
    def _enforce_four(out: models.ResearchOutput) -> models.ResearchOutput:
        by_label = {o.label: o for o in out.options}
        fixed = []
        for i, lab in enumerate(config.OPTIONS_LABELS, start=1):
            o = by_label.get(lab) or models.ResearchOption(label=lab, description="(brak)", rank_order=i)
            o.rank_order = i
            fixed.append(o)
        out.options = fixed
        return out

    @staticmethod
    def _format_evidence(evidence: list[dict]) -> str:
        lines = []
        for e in evidence:
            eid = e.get("evidence_id", "?")
            src = e.get("source_name", "?")
            fresh = e.get("freshness", "?")
            content = (e.get("content") or "")[:1200]
            lines.append(f"[{eid}] ({src}, {fresh}) {content}")
        return "\n".join(lines) if lines else "(brak evidence)"
