"""MasterPromptBuilder: per-source request payloads tuned to each adapter's API shape."""
from . import config


class MasterPromptBuilder:
    def build(self, source: str, query: str, complexity: str, context: str = "") -> dict:
        fn = getattr(self, f"build_for_{source}", None)
        return fn(query, complexity, context) if fn else {"query": query}

    def build_for_site(self, q, c, ctx):
        """Zrodlo natywne: bierze ADRES z zapytania ('strona: <url>' albo goly link)."""
        from . import site
        return {"url": site.extract_url(q), "max_pages": site.MAX_PAGES}

    def build_for_web_search(self, q, c, ctx):
        return {"query": q, "max_results": 5}

    def build_for_firecrawl(self, q, c, ctx):
        return {"query": q, "limit": 8, "maxCredits": config.FIRECRAWL_MAX_CREDITS}

    def build_for_openai_dr(self, q, c, ctx):
        model = config.OPENAI_DR_CRITICAL if c == "critical" else config.OPENAI_DR_HIGH
        return {
            "model": model,
            "input": q,
            "background": True,
            "max_tool_calls": config.OPENAI_DR_MAX_TOOL_CALLS,
        }

    def build_for_gemini_dr(self, q, c, ctx):
        return {"query": q, "background": True}

    def build_for_manus(self, q, c, ctx):
        return {"task": q}
