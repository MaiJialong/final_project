"""Pure-function tests for trend scoring (no database required)."""
import pytest

from app.forecasting import _baseline_projection, _risk_from_score
from app.schemas import RiskLevel
from app.scoring import compute_trend_score


def test_trend_score_in_range():
    score = compute_trend_score(
        recent_count=5, momentum=2.0, avg_severity=4.0,
        avg_confidence=0.8, recency_weight=0.9,
    )
    assert 0.0 <= score <= 100.0


def test_trend_score_monotonic_in_volume():
    low = compute_trend_score(recent_count=1, momentum=1.0, avg_severity=3.0,
                              avg_confidence=0.5, recency_weight=0.5)
    high = compute_trend_score(recent_count=10, momentum=1.0, avg_severity=3.0,
                               avg_confidence=0.5, recency_weight=0.5)
    assert high > low


def test_trend_score_clamps_extreme_inputs():
    # Out-of-range factors must not push the score outside 0..100.
    score = compute_trend_score(recent_count=10_000, momentum=99.0,
                                avg_severity=50.0, avg_confidence=9.0,
                                recency_weight=9.0)
    assert score <= 100.0
    zero = compute_trend_score(recent_count=0, momentum=-5.0, avg_severity=0.0,
                               avg_confidence=0.0, recency_weight=0.0)
    assert zero >= 0.0


def test_baseline_projection_clamped():
    assert _baseline_projection(90.0, 2.0) <= 100.0
    assert _baseline_projection(0.0, 0.0) >= 0.0


@pytest.mark.parametrize(
    "score,expected",
    [
        (85.0, RiskLevel.critical),
        (65.0, RiskLevel.high),
        (45.0, RiskLevel.elevated),
        (25.0, RiskLevel.moderate),
        (5.0, RiskLevel.low),
    ],
)
def test_risk_from_score(score, expected):
    assert _risk_from_score(score) == expected
