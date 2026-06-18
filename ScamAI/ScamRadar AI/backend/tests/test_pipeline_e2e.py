"""End-to-end pipeline test.

Runs the full daily pipeline (collect → extract → score → forecast) against a
real Postgres+pgvector database with 5 sample public sources about AI scams and
deepfake fraud, then verifies each contract:

  1. raw_sources are stored correctly
  2. scam_signals follow the Pydantic ScamSignal schema
  3. trend_clusters are generated
  4. forecasts include source evidence (cluster linkage) and confidence scores
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.collector import SearchHit
from app.models import Forecast, RawSource, ScamSignal as ScamSignalRow, TrendCluster
from app.pipeline import run_daily
from app.schemas import ScamSignal as ScamSignalSchema

# Five realistic public advisories about AI scams / deepfake fraud. Note the
# KYC-bypass advisory: a legitimate defensive source whose wording previously
# tripped the request-oriented safety filter and was silently dropped.
SAMPLE_SOURCES = [
    SearchHit(
        url="https://ic3.gov/advisory/deepfake-ceo-2026",
        title="FBI warns of deepfake CEO video calls",
        content=(
            "The FBI advisory warns that criminals use deepfake video on live "
            "calls to impersonate executives and request urgent wire transfers. "
            "Detection indicators include lip-sync drift and refusal to switch "
            "communication channel."
        ),
        publisher="ic3.gov",
        published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    ),
    SearchHit(
        url="https://ftc.gov/voice-clone-2026",
        title="FTC consumer alert: AI voice cloning grandparent scams",
        content=(
            "The FTC reports a surge in voice cloning used in grandparent scams. "
            "AI clones a relative's voice from social media audio to demand "
            "emergency money. Verify via a known callback number."
        ),
        publisher="ftc.gov",
        published_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
    ),
    SearchHit(
        url="https://cisa.gov/phishing-ai-2026",
        title="CISA: AI-generated phishing campaigns rising",
        content=(
            "CISA advisory describes AI-generated phishing emails with fewer "
            "grammatical errors targeting enterprise finance teams. Recommended "
            "defenses include DMARC and out-of-band verification."
        ),
        publisher="cisa.gov",
        published_at=datetime(2026, 6, 3, tzinfo=timezone.utc),
    ),
    SearchHit(
        url="https://europol.europa.eu/deepfake-romance-2026",
        title="Europol: deepfake romance fraud networks",
        content=(
            "Europol warns of romance scams using AI-generated profile photos "
            "and deepfake video calls to build trust before requesting crypto "
            "investments."
        ),
        publisher="europol.europa.eu",
        published_at=datetime(2026, 6, 4, tzinfo=timezone.utc),
    ),
    SearchHit(
        url="https://example-bank.com/fraud-alert-2026",
        title="Bank fraud alert: deepfake KYC bypass attempts",
        content=(
            "A bank advisory describes attempts to use deepfake selfies to "
            "bypass video KYC onboarding. Liveness detection and document "
            "cross-checks are recommended defenses."
        ),
        publisher="example-bank.com",
        published_at=datetime(2026, 6, 5, tzinfo=timezone.utc),
    ),
]


class _FixedProvider:
    """Returns the same 5 curated sample sources for any query."""

    def __init__(self, hits):
        self._hits = hits

    def search(self, query: str, max_results: int):
        return self._hits[:max_results]


@pytest.fixture()
def daily_run(db_session):
    provider = _FixedProvider(SAMPLE_SOURCES)
    result = run_daily(
        db_session,
        queries=["ai scam deepfake fraud trends"],
        max_results_per_query=5,
        horizon_days=30,
        provider=provider,
    )
    db_session.commit()
    return result


def test_pipeline_runs_end_to_end(daily_run):
    assert daily_run.collected_sources == 5
    assert daily_run.extracted_signals == 5  # no legitimate advisory dropped
    assert daily_run.clusters >= 1
    assert daily_run.forecasts == daily_run.clusters


# ── Requirement 1: raw_sources stored correctly ─────────────────────
def test_raw_sources_stored_correctly(daily_run, db_session):
    rows = db_session.query(RawSource).all()
    assert len(rows) == 5

    by_url = {r.url: r for r in rows}
    for sample in SAMPLE_SOURCES:
        stored = by_url[sample.url]
        assert stored.title == sample.title
        assert stored.publisher == sample.publisher
        assert stored.content == sample.content
        assert stored.query == "ai scam deepfake fraud trends"
        assert stored.published_at == sample.published_at
        assert stored.content_hash  # dedupe key populated
        assert stored.collected_at is not None
        assert stored.embedding is not None and len(stored.embedding) == 1536

    # content_hash must be unique across stored sources.
    hashes = [r.content_hash for r in rows]
    assert len(set(hashes)) == len(hashes)


def test_raw_sources_dedupe_on_rerun(daily_run, db_session):
    """A second identical run must not duplicate raw_sources."""
    provider = _FixedProvider(SAMPLE_SOURCES)
    run_daily(
        db_session,
        queries=["ai scam deepfake fraud trends"],
        max_results_per_query=5,
        provider=provider,
    )
    db_session.commit()
    assert db_session.query(RawSource).count() == 5


# ── Requirement 2: scam_signals follow the Pydantic schema ──────────
def test_scam_signals_follow_schema(daily_run, db_session):
    signals = db_session.query(ScamSignalRow).all()
    assert len(signals) == 5

    valid_modalities = {"voice", "video", "image", "text", "multimodal", "other"}
    for s in signals:
        # Re-validate each persisted row against the Pydantic contract.
        model = ScamSignalSchema(
            title=s.title,
            summary=s.summary,
            scam_type=s.scam_type,
            modality=s.modality,
            target_sector=s.target_sector,
            geographies=s.geographies,
            tactics=s.tactics,
            indicators=s.indicators,
            severity=s.severity,
            confidence=s.confidence,
            source_id=s.source_id,
            first_seen=s.first_seen,
        )
        assert 1 <= model.severity <= 5
        assert 0.0 <= model.confidence <= 1.0
        assert model.modality in valid_modalities
        assert s.source_id is not None  # linked back to its raw_source


def test_signals_reference_existing_sources(daily_run, db_session):
    source_ids = {r.id for r in db_session.query(RawSource).all()}
    for s in db_session.query(ScamSignalRow).all():
        assert s.source_id in source_ids


# ── Requirement 3: trend_clusters are generated ─────────────────────
def test_trend_clusters_generated(daily_run, db_session):
    clusters = db_session.query(TrendCluster).all()
    assert len(clusters) >= 1

    all_signal_ids = {s.id for s in db_session.query(ScamSignalRow).all()}
    for c in clusters:
        assert c.signal_count >= 1
        assert c.signal_count == len(c.signal_ids)
        assert 0.0 <= c.trend_score <= 100.0
        assert c.label
        assert c.window_start is not None and c.window_end is not None
        # Every clustered signal id must resolve to a stored signal.
        assert set(c.signal_ids).issubset(all_signal_ids)

    # Each extracted signal lands in exactly one cluster.
    clustered = [sid for c in clusters for sid in c.signal_ids]
    assert sorted(clustered) == sorted(all_signal_ids)


# ── Requirement 4: forecasts include source evidence + confidence ───
def test_forecasts_have_evidence_and_confidence(daily_run, db_session):
    forecasts = db_session.query(Forecast).all()
    clusters = {c.id: c for c in db_session.query(TrendCluster).all()}
    assert len(forecasts) >= 1

    valid_levels = {"low", "moderate", "elevated", "high", "critical"}
    for f in forecasts:
        # Source evidence: forecast traces to a cluster backed by real signals.
        assert f.cluster_id in clusters
        cluster = clusters[f.cluster_id]
        assert cluster.signal_count >= 1
        assert len(cluster.signal_ids) >= 1

        # Confidence score present and in-range.
        assert 0.0 <= f.confidence <= 1.0
        assert 0.0 <= f.projected_score <= 100.0
        assert f.risk_level in valid_levels
        assert f.rationale and len(f.rationale) >= 10
        assert f.recommended_defenses  # non-empty defensive guidance
        assert f.horizon_days == 30


def test_forecast_traces_to_originating_sources(daily_run, db_session):
    """Full evidence chain: forecast → cluster → signals → raw_sources."""
    forecast = db_session.query(Forecast).first()
    cluster = db_session.get(TrendCluster, forecast.cluster_id)

    signals = (
        db_session.query(ScamSignalRow)
        .filter(ScamSignalRow.id.in_(cluster.signal_ids))
        .all()
    )
    assert signals
    source_ids = {s.source_id for s in signals}
    sources = (
        db_session.query(RawSource).filter(RawSource.id.in_(source_ids)).all()
    )
    assert sources  # forecast is grounded in real collected sources
