# ScamRadar AI — Backend (MVP)

Defensive **scam & deepfake trend intelligence** service. It collects public
advisories, extracts structured defensive signals, clusters them into trends,
scores momentum, forecasts forward risk, and generates **abstract/educational**
report visuals. It is built to help defenders — it does **not** produce scam
content, lures, impersonation assets, or bypass instructions.

## Stack

- **FastAPI** backend
- **PostgreSQL + pgvector** for source/signal embeddings
- **MiniMax-M3** via an OpenAI-compatible Chat Completions endpoint
- **MiniMax image-01** for defensive report visuals
- **WebSearch MCP** (via a gateway) for public intelligence collection

## Layout

```
backend/
├── app/
│   ├── config.py          # env-driven settings
│   ├── database.py         # SQLAlchemy engine/session
│   ├── models.py           # ORM: raw_sources, scam_signals, trend_clusters, forecasts, generated_assets
│   ├── schemas.py          # Pydantic: ScamSignal, Forecast, API models
│   ├── minimax_client.py   # chat + embeddings + image (offline stubs supported)
│   ├── safety.py           # guardrail: blocks scam-enabling output
│   ├── collector.py        # daily WebSearch MCP collector (pluggable provider)
│   ├── extractor.py        # document → structured ScamSignal JSON
│   ├── scoring.py          # trend clustering + 0..100 trend score
│   ├── forecasting.py      # forward risk forecast generation
│   ├── assets.py           # safe defensive image generation
│   ├── pipeline.py         # collect → extract → score → forecast
│   └── main.py             # FastAPI app + endpoints
├── db/schema.sql           # Postgres schema w/ pgvector + ivfflat indexes
└── tests/                  # schema validation + safety filter tests
```

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in MINIMAX_API_KEY, DATABASE_URL

# Postgres with pgvector (Docker):
docker run -d --name scamradar-db -p 5432:5432 \
  -e POSTGRES_USER=scamradar -e POSTGRES_PASSWORD=scamradar \
  -e POSTGRES_DB=scamradar pgvector/pgvector:pg16
psql "$DATABASE_URL" -f db/schema.sql

uvicorn app.main:app --reload
```

Set `OFFLINE_MODE=1` to run the whole pipeline with deterministic stubs (no
MiniMax key or network needed) — used by the test suite and for local dev.

## Endpoints

| Method | Path                | Purpose                                            |
|--------|---------------------|----------------------------------------------------|
| POST   | `/run/daily`        | Run collect → extract → score → forecast pipeline  |
| GET    | `/trends`           | List trend clusters (by score)                     |
| GET    | `/forecasts`        | List forecasts (filter by `risk_level`)            |
| POST   | `/assets/generate`  | Generate an abstract defensive report visual       |
| GET    | `/health`           | Liveness                                           |

## WebSearch MCP wiring

`collector.py` talks to a `SearchProvider`. Point `WEBSEARCH_MCP_URL` at an HTTP
gateway that forwards `POST /search {query, max_results}` to the WebSearch MCP
tool and returns `{"results": [{url, title, content, ...}]}`. Without a gateway
(or in offline mode) a deterministic `StubSearchProvider` is used.

## Safety posture

`app/safety.py` is the guardrail and is intentionally conservative:

- **Blocks** authoring of phishing/scam scripts, realistic impersonation assets
  (fake bank/login pages, voice/face clones of real people, forged documents),
  and bypass/evasion instructions (2FA/MFA/KYC/detection).
- **Allows** trend descriptions, detection indicators, recommended defenses, and
  abstract/educational/enterprise-report visuals.

The filter is **two-tier**, because the same words mean different things
depending on who is "speaking":

- `safety.check_text` — **strict**, for caller-supplied requests (search
  queries, asset briefs) and image prompts. Blocks both authoring/operational
  intent *and* requests to produce impersonation/technique artifacts (clone a
  voice, fake a bank page, forge a document, bypass a control).
- `safety.check_generated_text` — **description-tolerant**, for generated
  defensive intelligence (signal title/summary, forecast rationale/defenses). A
  defensive report must be able to *describe* attacker techniques ("criminals
  clone voices", "deepfake KYC bypass attempts"), so only authoring/operational
  rules apply — it never lets the model reproduce a lure/script or emit
  step-by-step / how-to instructions.

Ingested public advisories are **not** pre-screened (you must be able to read
advisories about bad things); the guardrail is enforced on what the system
*emits and persists*. Blocked asset requests are persisted with
`safety_label="blocked"` for auditability (committed even though the request
returns HTTP 422).

## Tests

```bash
cd backend && OFFLINE_MODE=1 python -m pytest
```

Covers `ScamSignal`/`Forecast` validation (bounds, enums, cleaning), trend
scoring (pure functions), the safety filter (request-blocked vs
description-allowed, image-prompt rules), and an **end-to-end pipeline run**
(collect → extract → score → forecast) asserting all five contracts.

The end-to-end and API tests need a Postgres + pgvector database; they **skip
automatically** when one isn't reachable, so the schema/safety/scoring unit
tests still run anywhere. Point them at a throwaway DB via `TEST_DATABASE_URL`
(or `DATABASE_URL`):

```bash
docker run -d --name scamradar-test-db -p 5432:5432 \
  -e POSTGRES_USER=scamradar -e POSTGRES_PASSWORD=scamradar \
  -e POSTGRES_DB=scamradar pgvector/pgvector:pg16
OFFLINE_MODE=1 python -m pytest        # runs full e2e + API suite
```
