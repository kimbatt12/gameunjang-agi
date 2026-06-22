from dataclasses import dataclass

DEFAULT_DAILY_QUERY_LIMIT = 1000
DEFAULT_MONTHLY_BUDGET_USD = 1.0
DEFAULT_MIN_CACHE_HIT_RATE = 0.95
DEFAULT_DAYS_PER_MONTH = 30


@dataclass(frozen=True)
class CostControlSnapshot:
    total_queries: int
    llm_call_count: int
    cache_hits: int
    estimated_cost_per_llm_call_usd: float
    daily_query_limit: int = DEFAULT_DAILY_QUERY_LIMIT
    monthly_budget_usd: float = DEFAULT_MONTHLY_BUDGET_USD
    minimum_cache_hit_rate: float = DEFAULT_MIN_CACHE_HIT_RATE
    days_per_month: int = DEFAULT_DAYS_PER_MONTH


@dataclass(frozen=True)
class CostControlCheck:
    cache_hit_rate: float
    estimated_daily_cost_usd: float
    max_daily_budget_usd: float
    within_daily_query_limit: bool
    within_daily_budget: bool
    cache_hit_rate_ok: bool
    llm_call_count_ok: bool
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return (
            self.within_daily_query_limit
            and self.within_daily_budget
            and self.cache_hit_rate_ok
            and self.llm_call_count_ok
        )


def evaluate_cost_controls(snapshot: CostControlSnapshot) -> CostControlCheck:
    _validate_snapshot(snapshot)

    cache_hit_rate = snapshot.cache_hits / snapshot.total_queries
    estimated_daily_cost = (
        snapshot.llm_call_count * snapshot.estimated_cost_per_llm_call_usd
    )
    max_daily_budget = snapshot.monthly_budget_usd / snapshot.days_per_month
    expected_uncached_queries = snapshot.total_queries - snapshot.cache_hits

    within_daily_query_limit = snapshot.total_queries <= snapshot.daily_query_limit
    within_daily_budget = estimated_daily_cost < max_daily_budget
    cache_hit_rate_ok = cache_hit_rate >= snapshot.minimum_cache_hit_rate
    llm_call_count_ok = snapshot.llm_call_count <= expected_uncached_queries

    warnings: list[str] = []
    if not within_daily_query_limit:
        warnings.append("daily_query_limit_exceeded")
    if not within_daily_budget:
        warnings.append("estimated_daily_budget_exceeded")
    if not cache_hit_rate_ok:
        warnings.append("cache_hit_rate_below_target")
    if not llm_call_count_ok:
        warnings.append("llm_calls_exceed_uncached_queries")

    return CostControlCheck(
        cache_hit_rate=cache_hit_rate,
        estimated_daily_cost_usd=estimated_daily_cost,
        max_daily_budget_usd=max_daily_budget,
        within_daily_query_limit=within_daily_query_limit,
        within_daily_budget=within_daily_budget,
        cache_hit_rate_ok=cache_hit_rate_ok,
        llm_call_count_ok=llm_call_count_ok,
        warnings=tuple(warnings),
    )


def _validate_snapshot(snapshot: CostControlSnapshot) -> None:
    if snapshot.total_queries <= 0:
        raise ValueError("total_queries must be positive")
    if snapshot.llm_call_count < 0:
        raise ValueError("llm_call_count must not be negative")
    if snapshot.cache_hits < 0:
        raise ValueError("cache_hits must not be negative")
    if snapshot.cache_hits > snapshot.total_queries:
        raise ValueError("cache_hits must not exceed total_queries")
    if snapshot.estimated_cost_per_llm_call_usd < 0:
        raise ValueError("estimated_cost_per_llm_call_usd must not be negative")
    if snapshot.daily_query_limit <= 0:
        raise ValueError("daily_query_limit must be positive")
    if snapshot.monthly_budget_usd <= 0:
        raise ValueError("monthly_budget_usd must be positive")
    if not 0 <= snapshot.minimum_cache_hit_rate <= 1:
        raise ValueError("minimum_cache_hit_rate must be between 0 and 1")
    if snapshot.days_per_month <= 0:
        raise ValueError("days_per_month must be positive")
