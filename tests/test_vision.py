"""S8 — opt-in Ollama vision: configured uses the model; unconfigured is a no-op."""

from localfiscal.extract import extract_receipt
from localfiscal.vision import resolve_endpoint, vision_extract_text


def _img(tmp_path):
    p = tmp_path / "receipt.png"
    p.write_bytes(b"\x89PNG\r\n fake image bytes")
    return p


def test_unconfigured_makes_zero_network_calls(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    calls = {"n": 0}

    def poster(url, payload):
        calls["n"] += 1
        return {}

    out = vision_extract_text(_img(tmp_path), None, http_post=poster)
    assert out == ""
    assert calls["n"] == 0  # never touches the network when vision is off


def test_configured_uses_model_response(tmp_path):
    captured = {}

    def poster(url, payload):
        captured["url"] = url
        captured["payload"] = payload
        return {"response": "TOTAL $12.34\nCoffee Shop"}

    out = vision_extract_text(_img(tmp_path), "http://localhost:11434", http_post=poster)
    assert "TOTAL $12.34" in out
    assert captured["url"].endswith("/api/generate")
    assert "images" in captured["payload"] and captured["payload"]["images"]


def test_configured_failure_is_graceful(tmp_path):
    def poster(url, payload):
        raise ConnectionError("ollama is down")

    out = vision_extract_text(_img(tmp_path), "http://localhost:11434", http_post=poster)
    assert out == ""  # a vision failure must never crash ingest


def test_resolve_endpoint(monkeypatch):
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    assert resolve_endpoint(None) is None
    assert resolve_endpoint("http://x:11434") == "http://x:11434"
    monkeypatch.setenv("OLLAMA_URL", "http://env:11434")
    assert resolve_endpoint(None) == "http://env:11434"


def test_extract_uses_vision_text_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "localfiscal.vision.vision_extract_text",
        lambda path, ollama_url=None: "TOTAL $99.99\nWhole Foods",
    )
    data = extract_receipt(_img(tmp_path), use_vision=True, ollama_url="http://x:11434")
    assert data["amount_minor"] == 9999
