"""Orchestration of the daily defensive intelligence run."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .collector import SearchProvider, collect_daily
from .extractor import extract_and_store
from .forecasting import generate_and_store
from .minimax_client import MiniMaxClient
from .schemas import DailyRunResult
from .scoring import score_recent_signals


def run_daily(
    session: Session,
    *,
    queries: list[str] | None = None,
    max_results_per_query: int = 5,
    horizon_days: int = 30,
    minimax: MiniMaxClient | None = None,
    provider: SearchProvider | None = None,
) -> DailyRunResult:
    """Collect → extract → score → forecast, persisting everything."""
    minimax = minimax or MiniMaxClient()

    sources = collect_daily(
        session,
        queries=queries,
        max_results_per_query=max_results_per_query,
        provider=provider,
        minimax=minimax,
    )

    signal_count = 0
    for src in sources:
        signal_count += len(extract_and_store(session, src, minimax=minimax))

    clusters = score_recent_signals(session, persist=True)

    forecasts = 0
    for cluster in clusters:
        generate_and_store(
            session, cluster, horizon_days=horizon_days, minimax=minimax
        )
        forecasts += 1

    return DailyRunResult(
        collected_sources=len(sources),
        extracted_signals=signal_count,
        clusters=len(clusters),
        forecasts=forecasts,
        run_at=datetime.now(timezone.utc),
    )
