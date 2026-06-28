"""Optional local vision extraction via Ollama — opt-in, off by default.

Disabled unless the operator passes ``--vision`` and an Ollama endpoint (flag or
``$OLLAMA_URL``). Unconfigured, it is a graceful no-op that makes ZERO network
calls and the heuristic parser is used instead. (S1 ships the no-op contract; the
real client lands in S8.)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def resolve_endpoint(ollama_url: Optional[str]) -> Optional[str]:
    """The configured Ollama base URL, or ``None`` when vision is not configured."""
    return ollama_url or os.environ.get("OLLAMA_URL") or None


def vision_extract_text(path: Path, ollama_url: Optional[str] = None) -> str:
    """Return OCR/vision text for a receipt image, or ``""`` when unconfigured.

    Real client implemented in S8; the no-op contract (no endpoint → no network,
    empty string, heuristic fallback) is the stable boundary callers rely on.
    """
    endpoint = resolve_endpoint(ollama_url)
    if not endpoint:
        return ""
    return ""
