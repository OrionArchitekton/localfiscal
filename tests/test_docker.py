"""FIX-H — the one-command Docker path can write its data as the non-root user."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compose_uses_named_volume_so_nonroot_can_write():
    compose = (ROOT / "docker-compose.yml").read_text()
    # default mount is a named volume (image-initialized, appuser-owned), not a
    # host bind that the daemon would create root-owned and break first write
    assert "localfiscal-data:/app/data" in compose
    assert "\nvolumes:\n" in compose and "localfiscal-data:" in compose.split("\nvolumes:\n")[1]
    assert "127.0.0.1:8080:8080" in compose  # still loopback by default


def test_dockerfile_data_dir_owned_by_appuser():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "chown -R appuser:appuser /app" in dockerfile
    assert "USER appuser" in dockerfile and "USER root" not in dockerfile
