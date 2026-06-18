"""Defensive report asset generation.

Wraps MiniMax image-01. Every prompt is screened and sanitized by the safety
filter so that only abstract / educational / enterprise-report style visuals
are produced. Realistic, deceptive, or impersonating imagery is blocked.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from . import safety
from .config import get_settings
from .minimax_client import MiniMaxClient
from .models import GeneratedAsset
from .schemas import AssetGenerateRequest, AssetGenerateResult

_STYLE_BY_TYPE = {
    "report_cover": "minimal corporate security report cover, geometric shapes, "
                    "muted blues and slate, abstract network motif",
    "infographic": "clean abstract infographic style, simple iconography, flat "
                   "design, data-dashboard aesthetic, no real text",
    "abstract_chart": "abstract data-visualization artwork, flowing gradient "
                      "lines suggesting rising risk, no labels",
}


def generate_asset(
    session: Session,
    req: AssetGenerateRequest,
    *,
    minimax: MiniMaxClient | None = None,
) -> AssetGenerateResult:
    minimax = minimax or MiniMaxClient()
    settings = get_settings()

    asset_type = req.asset_type if isinstance(req.asset_type, str) else req.asset_type.value
    style = _STYLE_BY_TYPE.get(asset_type, _STYLE_BY_TYPE["report_cover"])
    base_prompt = f"{req.brief}. Style: {style}."

    verdict = safety.check_image_prompt(base_prompt)
    if not verdict.allowed:
        # Persist the block for auditability.
        row = GeneratedAsset(
            cluster_id=req.cluster_id,
            forecast_id=req.forecast_id,
            asset_type=asset_type,
            prompt=base_prompt,
            safety_label="blocked",
        )
        session.add(row)
        session.flush()
        return AssetGenerateResult(
            id=row.id,
            asset_type=asset_type,
            safety_label="blocked",
            blocked_reason=verdict.reason,
        )

    safe_prompt = safety.sanitize_image_prompt(base_prompt)
    basename = f"asset_{uuid.uuid4().hex[:12]}"
    file_path, image_url = minimax.generate_image(
        safe_prompt, output_dir=settings.asset_output_dir, basename=basename
    )

    row = GeneratedAsset(
        cluster_id=req.cluster_id,
        forecast_id=req.forecast_id,
        asset_type=asset_type,
        prompt=safe_prompt,
        file_path=file_path,
        image_url=image_url,
        safety_label="approved",
    )
    session.add(row)
    session.flush()
    return AssetGenerateResult(
        id=row.id,
        asset_type=asset_type,
        safety_label="approved",
        file_path=file_path,
        image_url=image_url,
    )
