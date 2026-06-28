"""Optional local vision extraction via Ollama — opt-in, off by default.

Disabled unless the operator passes ``--vision`` with an Ollama endpoint (flag or
``$OLLAMA_URL``). Unconfigured, it makes ZERO network calls and returns ``""`` so the
heuristic parser is used. Any failure when configured (endpoint down, bad response)
degrades gracefully to ``""`` — vision never crashes ingest, and it is never a hard
dependency (uses only the standard library).
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

DEFAULT_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llava")
_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "60"))
_PROMPT = (
    "You are a receipt OCR engine. Transcribe this receipt as plain text. "
    "Include the vendor name and every line, and clearly label the grand TOTAL "
    "with its amount and currency symbol."
)

# A poster takes (url, json_payload) and returns the decoded JSON dict.
Poster = Callable[[str, dict], dict]


def resolve_endpoint(ollama_url: str | None) -> str | None:
    """The configured Ollama base URL, or ``None`` when vision is not configured."""
    return ollama_url or os.environ.get("OLLAMA_URL") or None


def _default_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:  # noqa: S310 (operator-configured local URL)
        return json.loads(resp.read().decode("utf-8"))


def vision_extract_text(
    path: Path,
    ollama_url: str | None = None,
    *,
    model: str = DEFAULT_MODEL,
    http_post: Poster | None = None,
) -> str:
    """Return vision-OCR text for a receipt image, or ``""`` when unconfigured/unavailable."""
    endpoint = resolve_endpoint(ollama_url)
    if not endpoint:
        return ""  # vision off → no network, fall back to heuristic
    try:
        image_b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        payload = {"model": model, "prompt": _PROMPT, "images": [image_b64], "stream": False}
        poster = http_post or _default_post
        result = poster(endpoint.rstrip("/") + "/api/generate", payload)
        return (result or {}).get("response", "") or ""
    except Exception:
        return ""  # graceful: any failure falls back to the heuristic parser
