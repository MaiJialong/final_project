"""Pydantic v2 schemas for the ScamRadar API and internal pipeline.

These are the validation contracts. `ScamSignal` and `Forecast` are the
two core models; the rest support API requests/responses.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Enumerations ────────────────────────────────────────────────────
class Modality(str, Enum):
    voice = "voice"
    video = "video"
    image = "image"
    text = "text"
    multimodal = "multimodal"
    other = "other"


class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    elevated = "elevated"
    high = "high"
    critical = "critical"


class AssetType(str, Enum):
    report_cover = "report_cover"
    infographic = "infographic"
    abstract_chart = "abstract_chart"


# ── Core: ScamSignal ────────────────────────────────────────────────
class ScamSignal(BaseModel):
    """A single structured, defensive observation about a scam/deepfake technique.

    Deliberately captures *detection* and *defense* information only — never
    reproductions of scam content, lures, or step-by-step attack instructions.
    """

    model_config = ConfigDict(use_enum_values=True)

    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field(..., min_length=10, max_length=2000)
    scam_type: str = Field(..., min_length=2, max_length=64)
    modality: Modality
    target_sector: str | None = Field(default=None, max_length=120)
    geographies: list[str] = Field(default_factory=list)
    tactics: list[str] = Field(
        default_factory=list,
        description="Defensive TTP labels (what defenders should watch for).",
    )
    indicators: list[str] = Field(
        default_factory=list,
        description="Defensive detection indicators (signs of the scam).",
    )
    severity: int = Field(..., ge=1, le=5)
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_id: uuid.UUID | None = None
    first_seen: datetime | None = None

    @field_validator("title", "summary", "scam_type")
    @classmethod
    def _strip_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("geographies", "tactics", "indicators")
    @classmethod
    def _clean_list(cls, v: list[str]) -> list[str]:
        return [item.strip() for item in v if item and item.strip()]


# ── Core: Forecast ──────────────────────────────────────────────────
class Forecast(BaseModel):
    """Forward-looking, defensive risk projection for a trend cluster."""

    model_config = ConfigDict(use_enum_values=True)

    cluster_id: uuid.UUID | None = None
    horizon_days: int = Field(..., ge=1, le=365)
    risk_level: RiskLevel
    projected_score: float = Field(..., ge=0.0, le=100.0)
    rationale: str = Field(..., min_length=10, max_length=4000)
    recommended_defenses: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("recommended_defenses")
    @classmethod
    def _clean_defenses(cls, v: list[str]) -> list[str]:
        return [d.strip() for d in v if d and d.strip()]


# ── Supporting / API models ─────────────────────────────────────────
class RawSourceIn(BaseModel):
    url: str
    title: str | None = None
    publisher: str | None = None
    content: str = Field(..., min_length=1)
    query: str | None = None
    published_at: datetime | None = None


class TrendClusterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    description: str | None = None
    scam_type: str | None = None
    signal_count: int
    trend_score: float
    momentum: float
    avg_severity: float
    window_start: datetime | None = None
    window_end: datetime | None = None
    created_at: datetime


class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cluster_id: uuid.UUID | None = None
    horizon_days: int
    risk_level: str
    projected_score: float
    rationale: str
    recommended_defenses: list[str]
    confidence: float
    created_at: datetime


class DailyRunRequest(BaseModel):
    queries: list[str] | None = Field(
        default=None, description="Override default defensive search queries."
    )
    max_results_per_query: int = Field(default=5, ge=1, le=25)
    horizon_days: int = Field(default=30, ge=1, le=365)


class DailyRunResult(BaseModel):
    collected_sources: int
    extracted_signals: int
    clusters: int
    forecasts: int
    run_at: datetime


class AssetGenerateRequest(BaseModel):
    cluster_id: uuid.UUID | None = None
    forecast_id: uuid.UUID | None = None
    asset_type: AssetType = AssetType.report_cover
    brief: str = Field(
        ...,
        min_length=5,
        max_length=600,
        description="Description of the desired abstract/educational visual.",
    )


class AssetGenerateResult(BaseModel):
    id: uuid.UUID | None = None
    asset_type: str
    safety_label: str
    file_path: str | None = None
    image_url: str | None = None
    blocked_reason: str | None = None
