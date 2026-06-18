"""Safety filter — blocks scam-enabling outputs.

ScamRadar is a *defensive* product. This module is the guardrail that keeps
generated text and image prompts on the right side of that line. It is
intentionally conservative: when in doubt, block.

What we BLOCK (offensive / scam-enabling):
  - Requests to write phishing emails, smishing/vishing scripts, or lures
  - Step-by-step instructions to run a scam or impersonate a person/brand
  - Generation of realistic impersonation assets (fake bank/login pages,
    cloned brand UIs, forged documents, deepfake likenesses of real people)
  - Instructions to bypass detection, KYC, 2FA, content filters, or moderation

What we ALLOW (defensive):
  - Describing trends, indicators, and detection signals
  - Recommending defenses and awareness guidance
  - Abstract / educational / enterprise-report style visuals
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Text guardrails ─────────────────────────────────────────────────
# Patterns target *productive* offensive intent, not mere mention of a concept
# (a defensive report must be able to say the word "phishing" and to *describe*
# how a technique works).
#
# Two groups, because the same words mean different things depending on who is
# "speaking":
#   * AUTHORING / OPERATIONAL — producing the actual scam artifact, or giving
#     step-by-step / how-to instructions to commit fraud or defeat controls.
#     These are dangerous regardless of framing, so they are ALWAYS blocked
#     (in user requests AND in generated defensive output).
#   * IMPERSONATION / TECHNIQUE — references to cloning a voice, deepfaking a
#     person, faking a bank page, forging a document, or bypassing a control.
#     A *request* to do these is blocked; a defensive *description* of attackers
#     doing them ("criminals clone voices to...") is exactly what this product
#     must be able to emit, so these are only enforced for caller-supplied
#     requests and image prompts — not for generated threat-intel text.

_AUTHORING_PATTERNS: list[tuple[str, str]] = [
    (r"\bwrite\b.{0,40}\b(phishing|smishing|vishing|scam|spam)\b.{0,40}\b(email|message|text|script|sms|letter)\b",
     "authoring scam/phishing content"),
    (r"\b(generate|draft|compose|create)\b.{0,40}\b(phishing|scam|fraud)\b.{0,30}\b(email|message|script|lure|template|page)\b",
     "authoring scam/phishing content"),
    (r"\b(scam|phishing|fraud)\s+(script|template|kit|playbook)\b",
     "scam script/template/kit"),
    (r"\bhow to\b.{0,40}\b(scam|defraud|phish|launder|steal|impersonate)\b",
     "operational how-to for committing a scam"),
    (r"\bhow to\b.{0,40}\b(bypass|evade|circumvent|defeat|disable|get around)\b.{0,30}\b(2fa|mfa|otp|kyc|detection|filter|verification|moderation|antivirus|spam filter|liveness)\b",
     "operational how-to for defeating security controls"),
    (r"\b(step[- ]by[- ]step|step \d)\b.{0,40}\b(scam|phish|defraud|impersonat|launder)\b",
     "step-by-step scam instructions"),
]

_IMPERSONATION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(fake|clone[d]?|spoof(ed)?|counterfeit|replica)\b.{0,30}\b(bank|login|sign[- ]?in|payment|checkout|paypal|wallet)\b.{0,20}\bpage\b",
     "fake/cloned bank or login page"),
    (r"\b(clone|impersonate|mimic|spoof)\b.{0,30}\b(voice|face|identity|likeness|ceo|executive|relative|person)\b",
     "realistic impersonation of a real person"),
    (r"\bdeepfake\b.{0,30}\b(of|impersonat|likeness|video|create|generate|make)\b.{0,30}\b(person|ceo|celebrity|official|someone|him|her|them)\b",
     "deepfake impersonation of a real person"),
    (r"\b(forge|forged|fabricate)\b.{0,30}\b(document|invoice|id|passport|statement|credential)\b",
     "forged documents/credentials"),
    (r"\b(bypass|evade|circumvent|defeat|get around|trick)\b.{0,30}\b(2fa|mfa|otp|kyc|detection|filter|verification|moderation|antivirus|spam filter|liveness)\b",
     "instructions to bypass security/detection controls"),
]

_AUTHORING_RE = [(re.compile(p, re.IGNORECASE | re.DOTALL), label)
                 for p, label in _AUTHORING_PATTERNS]
_IMPERSONATION_RE = [(re.compile(p, re.IGNORECASE | re.DOTALL), label)
                     for p, label in _IMPERSONATION_PATTERNS]
# Full strict set, used for caller-supplied requests and image prompts.
_OFFENSIVE_RE = _AUTHORING_RE + _IMPERSONATION_RE

# ── Image-prompt guardrails ─────────────────────────────────────────
# Generated visuals must be abstract / educational / enterprise-report style.
# Block anything that asks for realistic, deceptive, or impersonating imagery.

_IMAGE_BLOCK_TERMS: list[tuple[str, str]] = [
    (r"\b(real|realistic|photo[- ]?realistic|lifelike|authentic[- ]looking)\b.{0,20}\b(bank|login|invoice|id|passport|document|website|page|screenshot|ui)\b",
     "realistic deceptive asset"),
    (r"\b(fake|spoof|clone|counterfeit|replica|mock)\b.{0,20}\b(bank|login|website|page|app|brand|logo|screenshot)\b",
     "fake/cloned brand or page"),
    (r"\b(deepfake|face[- ]?swap|face swap)\b", "deepfake/face-swap imagery"),
    (r"\b(photorealistic|realistic)\b.{0,20}\b(face|person|portrait|human)\b",
     "realistic human likeness"),
    (r"\b(qr code|login form|sign[- ]?in form|credit card number|otp code)\b",
     "functional credential-capture element"),
    (r"\bimpersonat(e|ion|ing)\b", "impersonation imagery"),
]
_IMAGE_BLOCK_RE = [(re.compile(p, re.IGNORECASE), label)
                   for p, label in _IMAGE_BLOCK_TERMS]

# Positive framing we encourage for image prompts.
_SAFE_IMAGE_PREFIX = (
    "Abstract, non-photorealistic, enterprise security-report illustration. "
    "No real people, no logos, no readable text, no UI mockups. "
)


@dataclass
class SafetyVerdict:
    allowed: bool
    reason: str | None = None
    matched: list[str] = field(default_factory=list)

    def raise_if_blocked(self) -> None:
        if not self.allowed:
            raise SafetyViolation(self.reason or "blocked by safety filter")


class SafetyViolation(Exception):
    """Raised when content is blocked by the safety filter."""


def _screen(text: str, rules: list) -> SafetyVerdict:
    if not text or not text.strip():
        return SafetyVerdict(allowed=True)
    matched = [label for rx, label in rules if rx.search(text)]
    if matched:
        return SafetyVerdict(
            allowed=False,
            reason="Blocked: content appears to seek/contain scam-enabling "
                   f"material ({matched[0]}). ScamRadar only produces defensive output.",
            matched=matched,
        )
    return SafetyVerdict(allowed=True)


def check_text(text: str) -> SafetyVerdict:
    """Strict screen for caller-supplied requests (queries, briefs).

    Blocks both authoring/operational intent AND requests to produce
    impersonation/technique artifacts (clone a voice, fake a bank page, etc.).
    """
    return _screen(text, _OFFENSIVE_RE)


def check_generated_text(text: str) -> SafetyVerdict:
    """Screen generated defensive intelligence (signal/forecast text).

    Defensive output must be able to *describe* attacker techniques (voice
    cloning, deepfakes, KYC bypass), so only the authoring/operational rules
    apply here — never reproduce a lure/script or give step-by-step / how-to
    instructions for committing fraud or defeating controls.
    """
    return _screen(text, _AUTHORING_RE)


def check_image_prompt(prompt: str) -> SafetyVerdict:
    """Screen an image-generation prompt; must be abstract/educational only."""
    matched = [label for rx, label in _IMAGE_BLOCK_RE if rx.search(prompt or "")]
    # Also apply the text rules (e.g. "impersonate the CEO").
    matched += check_text(prompt).matched
    if matched:
        return SafetyVerdict(
            allowed=False,
            reason="Blocked image prompt: visuals must be abstract/educational "
                   f"({matched[0]}). Realistic or deceptive imagery is not permitted.",
            matched=matched,
        )
    return SafetyVerdict(allowed=True)


def sanitize_image_prompt(prompt: str) -> str:
    """Force an allowed image prompt into the safe enterprise-report style."""
    check_image_prompt(prompt).raise_if_blocked()
    return _SAFE_IMAGE_PREFIX + prompt.strip()
