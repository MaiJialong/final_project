"""FastAPI application — ScamRadar AI defensive intelligence backend."""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import safety
from .assets import generate_asset
from .database import get_session
from .models import Forecast as ForecastRow, TrendCluster
from .pipeline import run_daily
from .schemas import (
    AssetGenerateRequest,
    AssetGenerateResult,
    DailyRunRequest,
    DailyRunResult,
    ForecastOut,
    TrendClusterOut,
)

app = FastAPI(
    title="ScamRadar AI",
    version="0.1.0",
    description=(
        "Defensive scam & deepfake trend intelligence. This service produces "
        "detection indicators, trend analysis, forecasts, and abstract report "
        "visuals only. It does not generate scam content of any kind."
    ),
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.post("/run/daily", response_model=DailyRunResult, tags=["pipeline"])
def post_run_daily(
    req: DailyRunRequest = DailyRunRequest(),
    session: Session = Depends(get_session),
) -> DailyRunResult:
    """Run the full daily collect → extract → score → forecast pipeline."""
    # Screen any caller-supplied queries.
    if req.queries:
        for q in req.queries:
            if not safety.check_text(q).allowed:
                raise HTTPException(400, f"Query rejected by safety filter: {q!r}")
    return run_daily(
        session,
        queries=req.queries,
        max_results_per_query=req.max_results_per_query,
        horizon_days=req.horizon_days,
    )


@app.get("/trends", response_model=list[TrendClusterOut], tags=["read"])
def get_trends(
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    session: Session = Depends(get_session),
) -> list[TrendCluster]:
    stmt = (
        select(TrendCluster)
        .where(TrendCluster.trend_score >= min_score)
        .order_by(TrendCluster.trend_score.desc(), TrendCluster.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


@app.get("/forecasts", response_model=list[ForecastOut], tags=["read"])
def get_forecasts(
    limit: int = Query(default=20, ge=1, le=100),
    risk_level: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[ForecastRow]:
    stmt = select(ForecastRow)
    if risk_level:
        stmt = stmt.where(ForecastRow.risk_level == risk_level)
    stmt = stmt.order_by(ForecastRow.created_at.desc()).limit(limit)
    return list(session.scalars(stmt).all())


@app.post("/assets/generate", response_model=AssetGenerateResult, tags=["assets"])
def post_generate_asset(
    req: AssetGenerateRequest,
    session: Session = Depends(get_session),
) -> AssetGenerateResult:
    """Generate an abstract/educational defensive report visual.

    Returns 422 if the safety filter blocks the brief.
    """
    result = generate_asset(session, req)
    if result.safety_label == "blocked":
        # Commit the audit row before raising: get_session rolls back on any
        # exception, which would otherwise discard the "blocked" record.
        session.commit()
        raise HTTPException(422, detail=result.blocked_reason or "blocked by safety filter")
    return result
