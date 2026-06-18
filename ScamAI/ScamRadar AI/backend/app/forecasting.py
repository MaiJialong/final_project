"""Forecast generation — project forward risk for a trend cluster.

Combines a deterministic baseline (current score + momentum extrapolation)
with a MiniMax-M3 rationale and defensive recommendations. All model output
is validated against the `Forecast` schema and screened by the safety filter.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import safety
from .minimax_client import ChatMessage, MiniMaxClient
from .models import Forecast as ForecastRow, TrendCluster
from .schemas import Forecast, RiskLevel

_SYSTEM_PROMPT = """You are a defensive risk forecaster for an anti-scam \
intelligence platform. Given a trend cluster's statistics, produce a forward \
looking risk assessment for defenders.

STRICT RULES:
- Output is defensive only: risk level, rationale, and recommended DEFENSES \
(detection, verification, user education). Never describe how to conduct the \
scam or evade controls.
Return ONLY valid JSON:
{"risk_level": "low|moderate|elevated|high|critical",
 "projected_score": 0-100, "rationale": str,
 "recommended_defenses": [str], "confidence": 0.0-1.0}"""


def _baseline_projection(score: float, momentum: float) -> float:
    """Extrapolate the score one window forward, clamped to 0..100."""
    projected = score * (0.5 + 0.5 * min(momentum, 2.0))
    return round(max(0.0, min(projected, 100.0)), 2)


def _risk_from_score(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.critical
    if score >= 60:
        return RiskLevel.high
    if score >= 40:
        return RiskLevel.elevated
    if score >= 20:
        return RiskLevel.moderate
    return RiskLevel.low


def generate_forecast(
    cluster: TrendCluster,
    *,
    horizon_days: int = 30,
    minimax: MiniMaxClient | None = None,
) -> Forecast:
    """Produce a validated Forecast for a cluster."""
    minimax = minimax or MiniMaxClient()

    baseline = _baseline_projection(cluster.trend_score, cluster.momentum)
    baseline_risk = _risk_from_score(baseline)

    prompt = (
        "Forecast scam risk for this defensive trend cluster.\n"
        f"scam_type: {cluster.scam_type}\n"
        f"current_trend_score: {cluster.trend_score}\n"
        f"momentum: {cluster.momentum}\n"
        f"avg_severity: {cluster.avg_severity}\n"
        f"signal_count: {cluster.signal_count}\n"
        f"horizon_days: {horizon_days}\n"
        f"baseline_projected_score: {baseline}\n"
    )

    try:
        raw = minimax.chat(
            [ChatMessage("system", _SYSTEM_PROMPT), ChatMessage("user", prompt)],
            json_mode=True,
            temperature=0.2,
        )
        data = json.loads(raw)
    except (Exception,):
        data = {}

    # Fall back to the deterministic baseline for any missing/invalid fields.
    projected = data.get("projected_score", baseline)
    rationale = data.get("rationale") or (
        f"Projection based on current score {cluster.trend_score} and "
        f"{cluster.momentum:.2f}x momentum over a {horizon_days}-day horizon."
    )
    defenses = data.get("recommended_defenses") or [
        "Enforce out-of-band verification for sensitive requests",
        "Train staff/users on the cluster's detection indicators",
        "Add monitoring rules for the observed tactics",
    ]
    risk = data.get("risk_level") or baseline_risk.value
    confidence = data.get("confidence", 0.5)

    # Screen the rationale + defenses before returning. Description-tolerant:
    # a forecast may discuss attacker techniques, but not give operational
    # how-to / step-by-step instructions or reproduce a lure.
    if not safety.check_generated_text(rationale + "\n" + "\n".join(defenses)).allowed:
        rationale = (
            f"Defensive projection for {cluster.scam_type}: risk {risk}. "
            "Model rationale withheld by safety filter."
        )
        defenses = ["Apply standard anti-fraud verification and monitoring controls."]

    try:
        forecast = Forecast(
            cluster_id=cluster.id,
            horizon_days=horizon_days,
            risk_level=risk,
            projected_score=float(projected),
            rationale=rationale,
            recommended_defenses=defenses,
            confidence=float(confidence),
        )
    except Exception:
        # Last-resort deterministic forecast that always validates.
        forecast = Forecast(
            cluster_id=cluster.id,
            horizon_days=horizon_days,
            risk_level=baseline_risk,
            projected_score=baseline,
            rationale=(
                f"Baseline projection for {cluster.scam_type}: score {baseline} "
                f"over {horizon_days} days."
            ),
            recommended_defenses=defenses,
            confidence=0.4,
        )
    return forecast


def generate_and_store(
    session: Session,
    cluster: TrendCluster,
    *,
    horizon_days: int = 30,
    minimax: MiniMaxClient | None = None,
) -> ForecastRow:
    f = generate_forecast(cluster, horizon_days=horizon_days, minimax=minimax)
    row = ForecastRow(
        cluster_id=cluster.id,
        horizon_days=f.horizon_days,
        risk_level=f.risk_level,
        projected_score=f.projected_score,
        rationale=f.rationale,
        recommended_defenses=f.recommended_defenses,
        confidence=f.confidence,
    )
    session.add(row)
    session.flush()
    return row
