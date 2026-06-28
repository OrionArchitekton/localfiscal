"""S4 — uploads can't escape the sandbox; service is not root/LAN-exposed by default."""

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from localfiscal import web
from localfiscal.web import default_host, safe_upload_path


def test_safe_upload_path_strips_traversal(tmp_path):
    p = safe_upload_path(tmp_path, "../../../../etc/passwd")
    assert p.parent.resolve() == tmp_path.resolve()
    assert ".." not in p.name
    assert p.resolve().is_relative_to(tmp_path.resolve())


def test_safe_upload_path_strips_absolute(tmp_path):
    p = safe_upload_path(tmp_path, "/abs/evil.png")
    assert p.parent.resolve() == tmp_path.resolve()
    assert p.name == "evil.png"


def test_safe_upload_path_rejects_empty(tmp_path):
    p = safe_upload_path(tmp_path, "")
    assert p.parent.resolve() == tmp_path.resolve()
    assert p.name  # falls back to a safe generated name


def test_ingest_traversal_filename_does_not_escape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    importlib.reload(web)
    client = TestClient(web.app)
    resp = client.post(
        "/ingest",
        files={"file": ("../../pwned.txt", b"no amount in here", "text/plain")},
    )
    assert resp.status_code == 200
    # nothing was written outside the sandbox by the traversal name
    assert not (tmp_path.parent / "pwned.txt").exists()
    assert not Path("/pwned.txt").exists()


def test_default_host_is_loopback(monkeypatch):
    monkeypatch.delenv("LOCALFISCAL_HOST", raising=False)
    assert default_host() == "127.0.0.1"  # not 0.0.0.0 — opt in to exposure explicitly


def test_dockerfile_drops_root_and_compose_is_loopback():
    root = Path(__file__).resolve().parents[1]
    dockerfile = (root / "Dockerfile").read_text()
    assert "USER " in dockerfile and "USER root" not in dockerfile
    compose = (root / "docker-compose.yml").read_text()
    assert "127.0.0.1:8080:8080" in compose  # host-loopback by default
