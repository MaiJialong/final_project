"""Extractor agent — converts raw documents into structured ScamSignal JSON.

Uses MiniMax-M3 in JSON mode with a strict defensive system prompt. Every
extracted signal is validated against the Pydantic `ScamSignal` schema and
screened by the safety filter before being persisted.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import safety
from .minimax_client import ChatMessage, MiniMaxClient
from .models import RawSource, ScamSignal as ScamSignalRow
from .schemas import ScamSignal

_SYSTEM_PROMPT = """You are a defensive threat-intelligence extractor for an \
anti-scam monitoring system. Read the supplied public document and extract \
structured signals describing scam or deepfake TECHNIQUES that defenders \
should track.

STRICT RULES:
- Output defensive observations only: descriptions, detection indicators, and \
recommended awareness — NEVER reproduce scam scripts, lures, or step-by-step \
instructions for committing fraud or impersonation.
- Do not include personal data of real individuals.
- If the document contains no scam/deepfake intelligence, return {"signals": []}.

Return ONLY valid JSON of the form:
{"signals": [{
  "title": str, "summary": str, "scam_type": str,
  "modality": "voice|video|image|text|multimodal|other",
  "target_sector": str|null,
  "geographies": [str], "tactics": [str], "indicators": [str],
  "severity": 1-5, "confidence": 0.0-1.0
}]}"""


def extract_signals_from_text(
    text: str, minimax: MiniMaxClient | None = None
) -> list[ScamSignal]:
    """Extract & validate signals from a single document's text."""
    minimax = minimax or MiniMaxClient()

    # NOTE: we deliberately do *not* run the request/output guardrail
    # (safety.check_text) over the raw source document. Sources are public
    # advisories whose whole purpose is to describe scam/deepfake techniques —
    # phrases like "criminals bypass KYC" or "how to spot a scam" are exactly
    # what defenders need to ingest, yet they trip the request-oriented patterns.
    # The guardrail that matters is on what we *emit/persist*: every extracted
    # signal's title+summary is screened below before it is kept.
    raw = minimax.chat(
        [
            ChatMessage("system", _SYSTEM_PROMPT),
            ChatMessage("user", f"Extract scam signals from this document:\n\n{text[:6000]}"),
        ],
        json_mode=True,
        temperature=0.1,
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    signals: list[ScamSignal] = []
    for item in data.get("signals", []):
        try:
            sig = ScamSignal(**item)
        except Exception:
            # Skip malformed entries rather than failing the whole batch.
            continue
        # Defensive output check on the generated summary/title. Uses the
        # description-tolerant screen: a defensive signal may *describe* a
        # technique, but must not reproduce a lure/script or how-to.
        if not safety.check_generated_text(f"{sig.title}\n{sig.summary}").allowed:
            continue
        signals.append(sig)
    return signals


def extract_and_store(
    session: Session,
    source: RawSource,
    minimax: MiniMaxClient | None = None,
) -> list[ScamSignalRow]:
    """Extract signals from a RawSource and persist them."""
    minimax = minimax or MiniMaxClient()
    rows: list[ScamSignalRow] = []
    for sig in extract_signals_from_text(source.content, minimax):
        row = ScamSignalRow(
            source_id=source.id,
            title=sig.title,
            summary=sig.summary,
            scam_type=sig.scam_type,
            modality=sig.modality,
            target_sector=sig.target_sector,
            geographies=sig.geographies,
            tactics=sig.tactics,
            indicators=sig.indicators,
            severity=sig.severity,
            confidence=sig.confidence,
            first_seen=source.published_at,
            embedding=minimax.embed(f"{sig.title}. {sig.summary}"),
        )
        session.add(row)
        rows.append(row)
    session.flush()
    return rows
