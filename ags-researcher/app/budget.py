"""BudgetGovernor: hard cost stops (per-query / daily / monthly) + cost_events logging."""
from . import config, db


class BudgetExceeded(Exception):
    pass


class BudgetGovernor:
    @staticmethod
    def _sum(interval: str) -> float:
        r = db.fetchone(
            f"SELECT COALESCE(SUM(cost_pln),0) AS s FROM cost_events WHERE timestamp > NOW() - interval '{interval}'"
        )
        return float(r["s"] or 0)

    def daily_spent_pln(self) -> float:
        return self._sum("24 hours")

    def monthly_spent_pln(self) -> float:
        return self._sum("30 days")

    def preflight(self):
        """Raise BudgetExceeded if a daily/monthly hard cap is already reached."""
        if self.monthly_spent_pln() >= config.BUDGET_MONTHLY_PLN:
            raise BudgetExceeded(f"monthly cap {config.BUDGET_MONTHLY_PLN} PLN reached")
        if self.daily_spent_pln() >= config.BUDGET_DAILY_PLN:
            raise BudgetExceeded(f"daily cap {config.BUDGET_DAILY_PLN} PLN reached")

    def log_cost(self, run_id, source, endpoint, in_tok, out_tok, usd, cached=False) -> float:
        pln = round((usd or 0) * config.USD_PLN, 4)
        db.execute(
            """INSERT INTO cost_events
               (run_id, source_name, api_endpoint, input_tokens, output_tokens, cost_usd, cost_pln, cached)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (run_id, source, endpoint, in_tok, out_tok, usd, pln, cached),
        )
        return pln

    @staticmethod
    def anthropic_cost_usd(usage, in_rate: float = 3.0, out_rate: float = 15.0) -> float:
        """Sonnet 4.6 cost incl. prompt caching (write 1.25x, read 0.10x of input rate)."""
        def g(attr):
            return getattr(usage, attr, 0) or 0
        usd = (
            g("input_tokens") * in_rate
            + g("output_tokens") * out_rate
            + g("cache_creation_input_tokens") * in_rate * 1.25
            + g("cache_read_input_tokens") * in_rate * 0.10
        ) / 1_000_000
        return round(usd, 6)
