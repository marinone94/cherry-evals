"""Output scanner — detect credential leaks and sensitive data in LLM/agent outputs.

Adapted from gilby-core's supervisor.py guardrail scanner pattern.
Scans strings for patterns that should never appear in API responses:
API keys, tokens, internal hostnames, stack traces, etc.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Credential / secret patterns
# ---------------------------------------------------------------------------

_CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("api_key", re.compile(r"(?:sk|pk|rk|ak)[-_][a-zA-Z0-9]{20,}", re.ASCII)),
    ("bearer_token", re.compile(r"Bearer\s+[a-zA-Z0-9\-_.]{20,}", re.ASCII)),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}", re.ASCII)),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}", re.ASCII)),
    (
        "generic_secret",
        re.compile(r"(?:password|secret|token|key)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    ),
    (
        "connection_string",
        re.compile(r"(?:postgres|mysql|redis|mongodb)://[^\s]{10,}", re.IGNORECASE),
    ),
]

# Internal infrastructure patterns that should not leak
_INFRA_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "internal_host",
        re.compile(
            r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+):\d+",
            re.ASCII,
        ),
    ),
    ("stack_trace", re.compile(r"Traceback \(most recent call last\)", re.ASCII)),
    (
        "file_path",
        re.compile(r"(?:File|at) [\"']/(?:app|home|usr|var|etc)/[^\s\"']+\.py[\"']", re.ASCII),
    ),
]


def scan_for_leaks(text: str) -> list[dict]:
    """Scan text for credential leaks and sensitive patterns.

    Returns a list of findings, each with 'type' and 'match' keys.
    Empty list means the text is clean.
    """
    findings: list[dict] = []

    for name, pattern in _CREDENTIAL_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({"type": f"credential:{name}", "match": match.group()[:20] + "..."})

    for name, pattern in _INFRA_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({"type": f"infra:{name}", "match": match.group()[:40] + "..."})

    return findings


def redact_secrets(text: str) -> str:
    """Replace detected secrets with redaction placeholders."""
    for name, pattern in _CREDENTIAL_PATTERNS:
        text = pattern.sub(f"[REDACTED:{name}]", text)
    return text


def sanitize_error_message(error: str | Exception) -> str:
    """Sanitize an error message before including it in an API response.

    Strips file paths, connection strings, and internal details.
    Returns a generic message if the error contains sensitive patterns.
    """
    text = str(error)

    # Check for credential leaks — if found, return generic message
    for _, pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(text):
            return "An internal error occurred."

    # Redact infrastructure details
    for name, pattern in _INFRA_PATTERNS:
        text = pattern.sub(f"[{name}]", text)

    # Truncate to prevent overly verbose error messages
    if len(text) > 500:
        text = text[:500] + "..."

    return text
