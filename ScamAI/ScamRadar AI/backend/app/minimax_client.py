"""MiniMax client — OpenAI-compatible Chat Completions, embeddings, and image gen.

Chat:       MiniMax-M3 via /chat/completions (OpenAI-compatible)
Embeddings: embo-01  via /embeddings
Images:     image-01 via /image_generation

When `OFFLINE_MODE` is set, deterministic local stubs are returned so the
pipeline (and CI) can run without network access or API keys.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import Settings, get_settings


@dataclass
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class MiniMaxError(RuntimeError):
    pass


class MiniMaxClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.s = settings or get_settings()
        self._client = httpx.Client(
            base_url=self.s.minimax_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {self.s.minimax_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    # ── Chat completion ──────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> str:
        if self.s.offline_mode:
            return _stub_chat(messages, json_mode=json_mode)

        payload: dict = {
            "model": self.s.minimax_chat_model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = self._client.post("/chat/completions", json=payload)
        if resp.status_code >= 400:
            raise MiniMaxError(f"chat failed {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            raise MiniMaxError(f"unexpected chat response: {data}") from exc

    # ── Embeddings ───────────────────────────────────────────────────
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def embed(self, text: str) -> list[float]:
        if self.s.offline_mode:
            return _stub_embedding(text, self.s.embedding_dim)

        resp = self._client.post(
            "/embeddings",
            json={"model": self.s.minimax_embed_model, "input": text},
        )
        if resp.status_code >= 400:
            raise MiniMaxError(f"embed failed {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            return data["data"][0]["embedding"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            raise MiniMaxError(f"unexpected embed response: {data}") from exc

    # ── Image generation ─────────────────────────────────────────────
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=6))
    def generate_image(
        self, prompt: str, *, output_dir: str, basename: str | None = None
    ) -> tuple[str | None, str | None]:
        """Generate a defensive-report image. Returns (file_path, image_url).

        NOTE: callers MUST pass a prompt already screened/sanitized by
        app.safety.sanitize_image_prompt — this client does not vet content.
        """
        os.makedirs(output_dir, exist_ok=True)
        basename = basename or f"asset_{int(time.time())}"

        if self.s.offline_mode:
            path = os.path.join(output_dir, f"{basename}.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("[OFFLINE STUB IMAGE]\nprompt:\n" + prompt)
            return path, None

        resp = self._client.post(
            "/image_generation",
            json={
                "model": self.s.minimax_image_model,
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "response_format": "url",
                "n": 1,
            },
        )
        if resp.status_code >= 400:
            raise MiniMaxError(f"image failed {resp.status_code}: {resp.text}")
        data = resp.json()

        # MiniMax returns either image URLs or base64 depending on account.
        image_url = None
        file_path = None
        try:
            payload = data.get("data", data)
            if isinstance(payload, dict):
                urls = payload.get("image_urls") or payload.get("images")
                if urls:
                    image_url = urls[0]
                b64 = payload.get("image_base64")
                if b64:
                    file_path = os.path.join(output_dir, f"{basename}.png")
                    with open(file_path, "wb") as fh:
                        fh.write(base64.b64decode(b64[0] if isinstance(b64, list) else b64))
        except Exception as exc:  # pragma: no cover - defensive
            raise MiniMaxError(f"unexpected image response: {data}") from exc

        return file_path, image_url

    def close(self) -> None:
        self._client.close()


# ── Deterministic offline stubs ─────────────────────────────────────
def _stub_embedding(text: str, dim: int) -> list[float]:
    """Hash-seeded pseudo-embedding, L2-stable for the same input."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Tile the 32-byte digest out to `dim` floats in [-1, 1].
    vals = []
    i = 0
    while len(vals) < dim:
        b = h[i % len(h)]
        vals.append((b / 127.5) - 1.0)
        i += 1
    return vals


def _stub_chat(messages: list[ChatMessage], *, json_mode: bool) -> str:
    """Offline extractor/forecaster stub.

    Produces schema-shaped JSON so the pipeline runs end-to-end without a
    live model. Heuristic only — not a substitute for the real model.
    """
    user_text = " ".join(m.content for m in messages if m.role == "user").lower()
    system_text = " ".join(m.content for m in messages if m.role == "system").lower()

    if not json_mode:
        return "Defensive summary unavailable in offline mode."

    # Discriminate on the *system* prompt, which we control — the user prompt is
    # ambiguous (a forecast prompt contains "signal_count", and advisory text fed
    # to the extractor can contain the word "forecast"). Check the forecaster
    # branch first so it is never shadowed by the extractor's "signal" match.
    is_forecast = "forecaster" in system_text or "risk forecaster" in system_text
    is_extract = "extractor" in system_text or "extract structured signals" in system_text

    # Forecast request.
    if is_forecast or (not is_extract and ("forecast" in user_text or "projected_score" in user_text)):
        return json.dumps({
            "risk_level": "elevated",
            "projected_score": 62.0,
            "rationale": "Offline stub projection based on recent signal volume "
                         "and severity; replace with live model output.",
            "recommended_defenses": [
                "Deploy out-of-band verification for payment changes",
                "Brief staff on voice-clone and deepfake indicators",
                "Add detection rules for the observed indicators",
            ],
            "confidence": 0.5,
        })

    # Extractor request → emit a signal-shaped object.
    if is_extract or "extract" in user_text or "signal" in user_text:
        modality = (
            "voice" if "voice" in user_text or "call" in user_text
            else "video" if "video" in user_text or "deepfake" in user_text
            else "text"
        )
        scam_type = (
            "voice_clone" if modality == "voice"
            else "deepfake_video" if modality == "video"
            else "phishing_lure"
        )
        return json.dumps({
            "signals": [{
                "title": "Detected scam technique (offline stub)",
                "summary": "Offline-mode heuristic extraction of a reported "
                           "scam/deepfake technique for defensive tracking.",
                "scam_type": scam_type,
                "modality": modality,
                "target_sector": "general_public",
                "geographies": [],
                "tactics": ["urgency_pressure", "authority_impersonation"],
                "indicators": ["unusual_payment_request", "out_of_band_contact"],
                "severity": 3,
                "confidence": 0.5,
            }]
        })

    return json.dumps({})
