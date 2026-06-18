"""Requirement 5: unsafe scam-enabling content is blocked.

These cover the guardrail at the layer that governs what the system *emits and
persists* — generated signal output, generated forecast output, and
caller-supplied requests — rather than over-filtering ingested public advisories.
"""
from __future__ import annotations

import json

from app.extractor import extract_signals_from_text
from app.forecasting import generate_forecast
from app.minimax_client import MiniMaxClient
from app.models import TrendCluster


class _ScriptedMiniMax(MiniMaxClient):
    """MiniMaxClient whose chat() returns canned JSON, with stub embeddings."""

    def __init__(self, chat_payload: dict):
        super().__init__()
        self._payload = chat_payload

    def chat(self, messages, **kwargs) -> str:  # type: ignore[override]
        return json.dumps(self._payload)

    def embed(self, text: str):  # type: ignore[override]
        return [0.0] * self.s.embedding_dim


def test_extractor_drops_scam_enabling_generated_signal():
    """A model that emits scam-enabling output must have it filtered out."""
    payload = {
        "signals": [
            {
                "title": "Voice-clone executive fraud trend",
                "summary": "Defensive summary: attackers clone voices to request "
                           "wire transfers; verify via callback.",
                "scam_type": "voice_clone",
                "modality": "voice",
                "target_sector": "enterprise_finance",
                "geographies": ["US"],
                "tactics": ["authority_impersonation"],
                "indicators": ["unexpected_wire_request"],
                "severity": 4,
                "confidence": 0.8,
            },
            {
                # Scam-enabling output that must be blocked by the output screen.
                "title": "Phishing kit playbook",
                "summary": "Step-by-step scam instructions: write a phishing email "
                           "to steal bank login credentials from victims.",
                "scam_type": "phishing_lure",
                "modality": "text",
                "target_sector": "general_public",
                "geographies": [],
                "tactics": ["credential_theft"],
                "indicators": [],
                "severity": 5,
                "confidence": 0.9,
            },
        ]
    }
    signals = extract_signals_from_text("public advisory text", _ScriptedMiniMax(payload))
    titles = [s.title for s in signals]
    assert "Voice-clone executive fraud trend" in titles
    assert "Phishing kit playbook" not in titles  # blocked
    assert len(signals) == 1


def test_extractor_ingests_defensive_advisory_mentioning_bypass():
    """Legitimate advisories describing bypass techniques must NOT be dropped."""
    payload = {
        "signals": [
            {
                "title": "Deepfake KYC bypass attempts",
                "summary": "Advisory: criminals attempt to bypass video KYC with "
                           "deepfake selfies; enable liveness detection.",
                "scam_type": "deepfake_kyc",
                "modality": "video",
                "target_sector": "banking",
                "geographies": [],
                "tactics": ["liveness_evasion"],
                "indicators": ["mismatched_lighting"],
                "severity": 4,
                "confidence": 0.7,
            }
        ]
    }
    doc = (
        "A bank advisory describes attempts to bypass video KYC onboarding using "
        "deepfake selfies. Recommended defenses: liveness detection."
    )
    signals = extract_signals_from_text(doc, _ScriptedMiniMax(payload))
    assert len(signals) == 1
    assert signals[0].scam_type == "deepfake_kyc"


def test_forecast_output_screened():
    """A forecast whose model rationale is scam-enabling is sanitized."""
    payload = {
        "risk_level": "high",
        "projected_score": 70.0,
        "rationale": "Here is how to scam victims step by step and defraud them.",
        "recommended_defenses": ["write a phishing email to steal credentials"],
        "confidence": 0.6,
    }
    cluster = TrendCluster(
        label="Voice Clone activity",
        scam_type="voice_clone",
        signal_ids=[],
        signal_count=3,
        trend_score=55.0,
        momentum=1.5,
        avg_severity=4.0,
    )
    forecast = generate_forecast(cluster, horizon_days=30, minimax=_ScriptedMiniMax(payload))
    blob = forecast.rationale + " " + " ".join(forecast.recommended_defenses)
    assert "how to scam" not in blob.lower()
    assert "phishing email to steal" not in blob.lower()
    assert "withheld by safety filter" in forecast.rationale.lower()
