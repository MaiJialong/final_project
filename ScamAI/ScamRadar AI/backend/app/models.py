"""SQLAlchemy ORM models mirroring db/schema.sql."""
from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .config import get_settings
from .database import Base

_DIM = get_settings().embedding_dim


def _uuid_col() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class RawSource(Base):
    __tablename__ = "raw_sources"

    id: Mapped[uuid.UUID] = _uuid_col()
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_DIM))


class ScamSignal(Base):
    __tablename__ = "scam_signals"

    id: Mapped[uuid.UUID] = _uuid_col()
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_sources.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    scam_type: Mapped[str] = mapped_column(String, nullable=False)
    modality: Mapped[str] = mapped_column(String, nullable=False)
    target_sector: Mapped[str | None] = mapped_column(String)
    geographies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    tactics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    indicators: Mapped[list] = mapped_column(JSONB, default=list)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_DIM))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_signal_severity"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_signal_confidence"),
    )


class TrendCluster(Base):
    __tablename__ = "trend_clusters"

    id: Mapped[uuid.UUID] = _uuid_col()
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    scam_type: Mapped[str | None] = mapped_column(String)
    signal_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list
    )
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    trend_score: Mapped[float] = mapped_column(Float, default=0.0)
    momentum: Mapped[float] = mapped_column(Float, default=0.0)
    avg_severity: Mapped[float] = mapped_column(Float, default=0.0)
    centroid: Mapped[list[float] | None] = mapped_column(Vector(_DIM))
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = _uuid_col()
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trend_clusters.id", ondelete="CASCADE")
    )
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    projected_score: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_defenses: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_forecast_confidence"),
    )


class GeneratedAsset(Base):
    __tablename__ = "generated_assets"

    id: Mapped[uuid.UUID] = _uuid_col()
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trend_clusters.id", ondelete="SET NULL")
    )
    forecast_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="SET NULL")
    )
    asset_type: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    safety_label: Mapped[str] = mapped_column(String, default="approved")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
