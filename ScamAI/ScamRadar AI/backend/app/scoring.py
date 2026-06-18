"""Trend scoring — cluster recent signals and compute a 0..100 trend score.

Clustering is intentionally simple for the MVP: signals are grouped by
`scam_type`. (The embeddings/centroids are stored so a later version can
switch to vector-similarity clustering without a schema change.)

Trend score blends:
  - volume      : how many signals in the recent window
  - momentum    : recent window volume vs the prior window (growth)
  - severity    : average severity (1..5)
  - confidence  : average extraction confidence (0..1)
  - recency     : exponential recency weighting
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ScamSignal, TrendCluster


@dataclass
class ClusterStats:
    scam_type: str
    signal_ids: list = field(default_factory=list)
    recent_count: int = 0
    prior_count: int = 0
    severity_sum: float = 0.0
    confidence_sum: float = 0.0
    recency_weight: float = 0.0
    momentum: float = 0.0
    trend_score: float = 0.0

    @property
    def count(self) -> int:
        return len(self.signal_ids)

    @property
    def avg_severity(self) -> float:
        return self.severity_sum / self.count if self.count else 0.0

    @property
    def avg_confidence(self) -> float:
        return self.confidence_sum / self.count if self.count else 0.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def compute_trend_score(
    *,
    recent_count: int,
    momentum: float,
    avg_severity: float,
    avg_confidence: float,
    recency_weight: float,
) -> float:
    """Combine factors into a 0..100 trend score.

    Pure function — unit-testable without a database.
    """
    # Volume: log-scaled so a few high-quality signals still register, but
    # a flood doesn't dominate. log1p(10) ~ 2.4 → ~ full marks.
    volume = min(math.log1p(recent_count) / math.log1p(10), 1.0)
    # Momentum: map growth ratio into 0..1 (0 = flat/declining, 1 = >=2x).
    mom = max(0.0, min(momentum / 2.0, 1.0))
    sev = max(0.0, min(avg_severity / 5.0, 1.0))
    conf = max(0.0, min(avg_confidence, 1.0))
    rec = max(0.0, min(recency_weight, 1.0))

    score = (
        0.30 * volume
        + 0.25 * mom
        + 0.20 * sev
        + 0.10 * conf
        + 0.15 * rec
    ) * 100.0
    return round(score, 2)


def score_recent_signals(
    session: Session,
    *,
    window_days: int = 7,
    persist: bool = True,
) -> list[TrendCluster]:
    """Cluster signals from the last `window_days` and score each cluster."""
    now = _now()
    window_start = now - timedelta(days=window_days)
    prior_start = window_start - timedelta(days=window_days)

    rows = session.scalars(
        select(ScamSignal).where(ScamSignal.created_at >= prior_start)
    ).all()

    stats: dict[str, ClusterStats] = defaultdict(lambda: ClusterStats(scam_type=""))
    for s in rows:
        cs = stats[s.scam_type]
        cs.scam_type = s.scam_type
        created = s.created_at or now
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= window_start:
            cs.signal_ids.append(s.id)
            cs.recent_count += 1
            cs.severity_sum += s.severity
            cs.confidence_sum += s.confidence
            age_days = max((now - created).total_seconds() / 86400.0, 0.0)
            cs.recency_weight += math.exp(-age_days / window_days)
        else:
            cs.prior_count += 1

    clusters: list[TrendCluster] = []
    for cs in stats.values():
        if cs.recent_count == 0:
            continue
        cs.momentum = (cs.recent_count / cs.prior_count) if cs.prior_count else 2.0
        avg_recency = cs.recency_weight / cs.recent_count
        cs.trend_score = compute_trend_score(
            recent_count=cs.recent_count,
            momentum=cs.momentum,
            avg_severity=cs.avg_severity,
            avg_confidence=cs.avg_confidence,
            recency_weight=avg_recency,
        )
        cluster = TrendCluster(
            label=f"{cs.scam_type.replace('_', ' ').title()} activity",
            description=(
                f"{cs.recent_count} signal(s) in the last {window_days} days; "
                f"momentum {cs.momentum:.2f}x vs prior window."
            ),
            scam_type=cs.scam_type,
            signal_ids=cs.signal_ids,
            signal_count=cs.recent_count,
            trend_score=cs.trend_score,
            momentum=round(cs.momentum, 3),
            avg_severity=round(cs.avg_severity, 3),
            window_start=window_start,
            window_end=now,
        )
        if persist:
            session.add(cluster)
        clusters.append(cluster)

    if persist:
        session.flush()
    clusters.sort(key=lambda c: c.trend_score, reverse=True)
    return clusters
