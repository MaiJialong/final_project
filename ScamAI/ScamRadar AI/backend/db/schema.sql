-- ScamRadar AI — defensive scam & deepfake trend intelligence
-- PostgreSQL schema with pgvector for source/signal embeddings.
--
-- Apply with:  psql "$DATABASE_URL" -f db/schema.sql
-- Requires the pgvector extension (image: pgvector/pgvector:pg16).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ─────────────────────────────────────────────────────────────────────
-- raw_sources: unprocessed intelligence gathered from public web search.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_sources (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url          TEXT NOT NULL,
    title        TEXT,
    publisher    TEXT,
    content      TEXT NOT NULL,
    query        TEXT,                              -- search query that found it
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    content_hash TEXT NOT NULL,                     -- dedupe key
    embedding    vector(1536),
    UNIQUE (content_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_sources_collected_at
    ON raw_sources (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_sources_embedding
    ON raw_sources USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─────────────────────────────────────────────────────────────────────
-- scam_signals: structured, extracted observations about a scam/deepfake
-- technique. One raw_source can yield many signals.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scam_signals (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id     UUID REFERENCES raw_sources (id) ON DELETE SET NULL,
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL,
    scam_type     TEXT NOT NULL,        -- e.g. voice_clone, deepfake_video, phishing_lure
    modality      TEXT NOT NULL,        -- voice | video | image | text | multimodal | other
    target_sector TEXT,                 -- e.g. banking, elderly, enterprise_finance
    geographies   TEXT[] NOT NULL DEFAULT '{}',
    tactics       TEXT[] NOT NULL DEFAULT '{}',  -- defensive TTP labels
    indicators    JSONB NOT NULL DEFAULT '[]',   -- defensive detection indicators
    severity      SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
    confidence    REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    first_seen    TIMESTAMPTZ,
    embedding     vector(1536),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scam_signals_type      ON scam_signals (scam_type);
CREATE INDEX IF NOT EXISTS idx_scam_signals_created   ON scam_signals (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scam_signals_embedding
    ON scam_signals USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─────────────────────────────────────────────────────────────────────
-- trend_clusters: groups of related signals + a computed trend score.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trend_clusters (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label         TEXT NOT NULL,
    description   TEXT,
    scam_type     TEXT,
    signal_ids    UUID[] NOT NULL DEFAULT '{}',
    signal_count  INTEGER NOT NULL DEFAULT 0,
    trend_score   REAL NOT NULL DEFAULT 0,   -- 0..100, see scoring.py
    momentum      REAL NOT NULL DEFAULT 0,   -- recent vs prior volume delta
    avg_severity  REAL NOT NULL DEFAULT 0,
    centroid      vector(1536),
    window_start  TIMESTAMPTZ,
    window_end    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trend_clusters_score
    ON trend_clusters (trend_score DESC);

-- ─────────────────────────────────────────────────────────────────────
-- forecasts: forward-looking risk projection for a trend cluster.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecasts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id      UUID REFERENCES trend_clusters (id) ON DELETE CASCADE,
    horizon_days    INTEGER NOT NULL,
    risk_level      TEXT NOT NULL,         -- low | moderate | elevated | high | critical
    projected_score REAL NOT NULL,
    rationale       TEXT NOT NULL,
    recommended_defenses TEXT[] NOT NULL DEFAULT '{}',
    confidence      REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_forecasts_created ON forecasts (created_at DESC);

-- ─────────────────────────────────────────────────────────────────────
-- generated_assets: defensive report visuals (abstract / educational only).
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS generated_assets (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id   UUID REFERENCES trend_clusters (id) ON DELETE SET NULL,
    forecast_id  UUID REFERENCES forecasts (id) ON DELETE SET NULL,
    asset_type   TEXT NOT NULL,           -- report_cover | infographic | abstract_chart
    prompt       TEXT NOT NULL,
    file_path    TEXT,
    image_url    TEXT,
    safety_label TEXT NOT NULL DEFAULT 'approved',  -- approved | blocked
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generated_assets_created
    ON generated_assets (created_at DESC);
