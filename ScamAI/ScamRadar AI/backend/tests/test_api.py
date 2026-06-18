"""API-level tests via FastAPI TestClient (offline mode, real test DB)."""
from __future__ import annotations

from app.models import GeneratedAsset


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_run_daily_then_read_trends_and_forecasts(client):
    resp = client.post("/run/daily", json={"max_results_per_query": 2, "horizon_days": 14})
    assert resp.status_code == 200
    body = resp.json()
    assert body["collected_sources"] > 0
    assert body["clusters"] >= 1
    assert body["forecasts"] == body["clusters"]

    trends = client.get("/trends").json()
    assert len(trends) >= 1
    assert trends == sorted(trends, key=lambda t: t["trend_score"], reverse=True)

    forecasts = client.get("/forecasts").json()
    assert len(forecasts) >= 1
    for f in forecasts:
        assert 0.0 <= f["confidence"] <= 1.0
        assert f["cluster_id"] is not None
        assert f["recommended_defenses"]


def test_run_daily_rejects_unsafe_query(client):
    resp = client.post(
        "/run/daily",
        json={"queries": ["how to scam elderly people step by step"]},
    )
    assert resp.status_code == 400
    assert "safety filter" in resp.json()["detail"].lower()


def test_generate_asset_allows_defensive_brief(client):
    resp = client.post(
        "/assets/generate",
        json={"brief": "Abstract geometric cover for a scam-trends security report",
              "asset_type": "report_cover"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["safety_label"] == "approved"
    assert body["file_path"]  # offline stub writes a placeholder file


def test_generate_asset_blocks_unsafe_brief(client, db_session):
    resp = client.post(
        "/assets/generate",
        json={"brief": "A realistic fake bank login page that captures credentials"},
    )
    assert resp.status_code == 422
    # The block must be persisted for auditability.
    blocked = (
        db_session.query(GeneratedAsset)
        .filter(GeneratedAsset.safety_label == "blocked")
        .all()
    )
    assert len(blocked) == 1
    assert blocked[0].file_path is None
