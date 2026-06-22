import pytest

from app.cost_control import CostControlSnapshot, evaluate_cost_controls


def test_daily_1000_query_target_stays_under_monthly_one_dollar_budget() -> None:
    result = evaluate_cost_controls(
        CostControlSnapshot(
            total_queries=1000,
            cache_hits=960,
            llm_call_count=40,
            estimated_cost_per_llm_call_usd=0.0005,
        )
    )

    assert result.ok is True
    assert result.cache_hit_rate == 0.96
    assert result.estimated_daily_cost_usd == pytest.approx(0.02)
    assert result.max_daily_budget_usd == pytest.approx(1 / 30)
    assert result.warnings == ()


def test_cost_control_flags_excess_llm_calls_and_low_cache_hit_rate() -> None:
    result = evaluate_cost_controls(
        CostControlSnapshot(
            total_queries=1000,
            cache_hits=800,
            llm_call_count=300,
            estimated_cost_per_llm_call_usd=0.0002,
        )
    )

    assert result.ok is False
    assert result.cache_hit_rate_ok is False
    assert result.llm_call_count_ok is False
    assert result.within_daily_budget is False
    assert result.warnings == (
        "estimated_daily_budget_exceeded",
        "cache_hit_rate_below_target",
        "llm_calls_exceed_uncached_queries",
    )


def test_cost_control_flags_daily_query_limit() -> None:
    result = evaluate_cost_controls(
        CostControlSnapshot(
            total_queries=1001,
            cache_hits=1001,
            llm_call_count=0,
            estimated_cost_per_llm_call_usd=0.0005,
        )
    )

    assert result.within_daily_query_limit is False
    assert "daily_query_limit_exceeded" in result.warnings
