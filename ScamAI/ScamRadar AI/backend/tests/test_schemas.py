"""Schema validation tests for ScamSignal and Forecast."""
import uuid

import pytest
from pydantic import ValidationError

from app.schemas import Forecast, Modality, RiskLevel, ScamSignal


def _valid_signal_kwargs():
    return dict(
        title="Voice-clone CEO fraud surge",
        summary="Reports of AI voice cloning used to impersonate executives "
                "requesting urgent wire transfers.",
        scam_type="voice_clone",
        modality=Modality.voice,
        target_sector="enterprise_finance",
        geographies=["US", "UK"],
        tactics=["authority_impersonation", "urgency_pressure"],
        indicators=["unexpected_wire_request", "out_of_band_contact"],
        severity=4,
        confidence=0.82,
    )


def test_scam_signal_valid():
    sig = ScamSignal(**_valid_signal_kwargs())
    assert sig.severity == 4
    assert sig.modality == "voice"  # use_enum_values
    assert "US" in sig.geographies


def test_scam_signal_severity_bounds():
    kw = _valid_signal_kwargs()
    kw["severity"] = 6
    with pytest.raises(ValidationError):
        ScamSignal(**kw)
    kw["severity"] = 0
    with pytest.raises(ValidationError):
        ScamSignal(**kw)


def test_scam_signal_confidence_bounds():
    kw = _valid_signal_kwargs()
    kw["confidence"] = 1.5
    with pytest.raises(ValidationError):
        ScamSignal(**kw)


def test_scam_signal_rejects_blank_title():
    kw = _valid_signal_kwargs()
    kw["title"] = "   "
    with pytest.raises(ValidationError):
        ScamSignal(**kw)


def test_scam_signal_invalid_modality():
    kw = _valid_signal_kwargs()
    kw["modality"] = "telepathy"
    with pytest.raises(ValidationError):
        ScamSignal(**kw)


def test_scam_signal_cleans_list_whitespace():
    kw = _valid_signal_kwargs()
    kw["geographies"] = ["  US ", "", "  "]
    sig = ScamSignal(**kw)
    assert sig.geographies == ["US"]


def test_forecast_valid():
    f = Forecast(
        cluster_id=uuid.uuid4(),
        horizon_days=30,
        risk_level=RiskLevel.high,
        projected_score=72.5,
        rationale="Sustained growth in voice-clone reports across two regions.",
        recommended_defenses=["Out-of-band verification", "Staff training"],
        confidence=0.7,
    )
    assert f.risk_level == "high"
    assert f.projected_score == 72.5


def test_forecast_score_bounds():
    with pytest.raises(ValidationError):
        Forecast(
            horizon_days=30,
            risk_level=RiskLevel.low,
            projected_score=140.0,
            rationale="too high to be valid",
            confidence=0.5,
        )


def test_forecast_horizon_bounds():
    with pytest.raises(ValidationError):
        Forecast(
            horizon_days=0,
            risk_level=RiskLevel.low,
            projected_score=10.0,
            rationale="zero horizon invalid",
            confidence=0.5,
        )


def test_forecast_invalid_risk_level():
    with pytest.raises(ValidationError):
        Forecast(
            horizon_days=30,
            risk_level="apocalyptic",
            projected_score=10.0,
            rationale="bad risk level",
            confidence=0.5,
        )
