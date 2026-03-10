"""Content wrapper for LLM prompt injection defense.

Adapted from gilby-core's content_wrapper.py pattern:
- Wraps untrusted content (user input, dataset content, tool output)
  in boundary markers so the LLM treats it as data, not instructions.
- Strips known injection patterns from external content.
- Removes Unicode control characters used for visual deception.
- Truncates oversized content to prevent context stuffing.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Boundary markers
# ---------------------------------------------------------------------------

_BOUNDARY_START = "<<<UNTRUSTED_DATA source={source}>>>"
_BOUNDARY_END = "<<<END_UNTRUSTED_DATA>>>"

# ---------------------------------------------------------------------------
# Injection pattern stripping
# ---------------------------------------------------------------------------

# Patterns commonly used in prompt injection attacks
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"</?system>", re.IGNORECASE),
    re.compile(r"\[/?SYSTEM\]", re.IGNORECASE),
    re.compile(r"\[/?INST\]", re.IGNORECASE),
    re.compile(r"ignore (?:all )?previous instructions", re.IGNORECASE),
    re.compile(r"you are now (?:a|an|my|the) ", re.IGNORECASE),
    re.compile(r"(?:enable|activate|enter) developer mode", re.IGNORECASE),
    re.compile(r"disregard (?:all )?(?:prior|above) (?:instructions|rules)", re.IGNORECASE),
    re.compile(r"new (?:system )?instructions?:", re.IGNORECASE),
    re.compile(r"override (?:safety|security|instructions)", re.IGNORECASE),
    re.compile(r"act as (?:if|though) you (?:are|were)", re.IGNORECASE),
]

# Unicode control characters used for visual deception / homoglyph attacks
_UNICODE_CONTROL_RE = re.compile(r"[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]")

# Maximum characters for external content before truncation
MAX_CONTENT_CHARS = 50_000


def strip_injections(text: str) -> str:
    """Strip known prompt injection patterns from text."""
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[STRIPPED]", text)
    return text


def strip_unicode_control(text: str) -> str:
    """Remove Unicode zero-width and control characters."""
    return _UNICODE_CONTROL_RE.sub("", text)


def wrap_external_content(content: str, source: str = "user_input") -> str:
    """Wrap untrusted content in boundary markers for LLM safety.

    The boundary markers tell the LLM that everything inside is DATA,
    not instructions to follow.

    Args:
        content: The untrusted content to wrap.
        source: Label for the content origin (e.g., "user_query", "dataset_row").

    Returns:
        Content wrapped in boundary markers with injections stripped.
    """
    # Strip any existing boundary markers to prevent escape attacks
    content = content.replace(_BOUNDARY_END, "[BOUNDARY-STRIPPED]")
    content = content.replace("<<<UNTRUSTED_DATA", "[BOUNDARY-STRIPPED]")

    # Strip injection patterns and control characters
    content = strip_injections(content)
    content = strip_unicode_control(content)

    # Truncate oversized content
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "\n[TRUNCATED]"

    # Sanitize source label to prevent format string issues
    safe_source = re.sub(r"[^a-zA-Z0-9_\-]", "_", source)
    start = _BOUNDARY_START.format(source=safe_source)
    return f"{start}\n{content}\n{_BOUNDARY_END}"


def sanitize_prompt_literal(text: str) -> str:
    """Sanitize a user-supplied literal before prompt interpolation.

    Lighter than full wrapping — strips control characters and injection
    patterns but does not add boundary markers. Use for short metadata
    fields (names, descriptions) that are interpolated into prompts.
    """
    text = strip_unicode_control(text)
    text = strip_injections(text)
    return text
