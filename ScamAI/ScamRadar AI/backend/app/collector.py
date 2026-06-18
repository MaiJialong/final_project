"""Daily collector job — gathers public defensive intelligence via WebSearch MCP.

The backend itself does not call the Claude WebSearch MCP tool directly at
runtime; instead it talks to a `SearchProvider`. In production wire this to
your WebSearch MCP gateway (an HTTP shim that forwards to the MCP tool). For
local dev / CI a deterministic `StubSearchProvider` is provided.

Default queries are framed defensively (trend monitoring, advisories), never
to source attack material.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .minimax_client import MiniMaxClient
from .models import RawSource

DEFAULT_QUERIES = [
    "latest deepfake scam trends advisory",
    "voice cloning fraud warning report",
    "AI impersonation scam consumer alert",
    "phishing trend report cybersecurity agency",
    "business email compromise deepfake CEO fraud advisory",
    "romance scam AI generated profile warning",
]


@dataclass
class SearchHit:
    url: str
    title: str | None
    content: str
    publisher: str | None = None
    published_at: datetime | None = None


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int) -> list[SearchHit]:
        ...


class MCPSearchProvider:
    """Calls a WebSearch MCP HTTP gateway.

    Expects a gateway exposing `POST {base_url}/search` that proxies to the
    WebSearch MCP tool and returns `{"results": [{"url","title","content",...}]}`.
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def search(self, query: str, max_results: int) -> list[SearchHit]:
        resp = self._client.post(
            "/search", json={"query": query, "max_results": max_results}
        )
        resp.raise_for_status()
        out: list[SearchHit] = []
        for r in resp.json().get("results", []):
            out.append(
                SearchHit(
                    url=r.get("url", ""),
                    title=r.get("title"),
                    content=r.get("content") or r.get("snippet") or "",
                    publisher=r.get("publisher"),
                    published_at=_parse_dt(r.get("published_at")),
                )
            )
        return out


class StubSearchProvider:
    """Deterministic offline provider for dev/CI."""

    def search(self, query: str, max_results: int) -> list[SearchHit]:
        hits = []
        for i in range(min(max_results, 3)):
            hits.append(
                SearchHit(
                    url=f"https://example-advisory.org/{abs(hash(query)) % 9999}/{i}",
                    title=f"Advisory: {query} (item {i+1})",
                    content=(
                        f"Public advisory discussing the trend '{query}'. "
                        "Reports describe AI-assisted impersonation and voice "
                        "cloning used against the public, with guidance on "
                        "detection indicators and recommended defenses."
                    ),
                    publisher="example-advisory.org",
                    published_at=datetime.now(timezone.utc),
                )
            )
        return hits


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _hash(url: str, content: str) -> str:
    return hashlib.sha256(f"{url}\n{content}".encode("utf-8")).hexdigest()


def get_default_provider(settings: Settings | None = None) -> SearchProvider:
    s = settings or get_settings()
    gateway = __import__("os").environ.get("WEBSEARCH_MCP_URL")
    if s.offline_mode or not gateway:
        return StubSearchProvider()
    return MCPSearchProvider(gateway)


def collect_daily(
    session: Session,
    *,
    queries: list[str] | None = None,
    max_results_per_query: int = 5,
    provider: SearchProvider | None = None,
    minimax: MiniMaxClient | None = None,
) -> list[RawSource]:
    """Run searches, dedupe, embed, and persist new raw_sources.

    Returns the list of newly inserted RawSource rows.
    """
    queries = queries or DEFAULT_QUERIES
    provider = provider or get_default_provider()
    minimax = minimax or MiniMaxClient()

    new_rows: list[RawSource] = []
    for query in queries:
        for hit in provider.search(query, max_results_per_query):
            if not hit.url or not hit.content:
                continue
            chash = _hash(hit.url, hit.content)
            exists = session.scalar(
                select(RawSource.id).where(RawSource.content_hash == chash)
            )
            if exists:
                continue
            row = RawSource(
                url=hit.url,
                title=hit.title,
                publisher=hit.publisher,
                content=hit.content,
                query=query,
                published_at=hit.published_at,
                content_hash=chash,
                embedding=minimax.embed(hit.content[:4000]),
            )
            session.add(row)
            new_rows.append(row)

    session.flush()
    return new_rows
