# Changelog

All notable changes to localfiscal are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-06-28 — "harden & honest"

A correctness, security, and honesty release. Every public claim is now backed by code.

### Added
- **Exact money model** (`localfiscal.money`): integer minor units + ISO-4217 currency,
  locale-aware parsing (US `$1,234.56` and EU `1.234,56`) and formatting.
- **Real CSV export** (RFC-4180) and **real OFX/QFX export** (`localfiscal export --fmt csv|ofx`).
- **Optional local vision** via Ollama (`ingest --vision` / `$OLLAMA_URL`), off by default,
  standard-library client, graceful fallback when unconfigured or unavailable.
- **Signed reports**: income / expense / **net** per currency, consistent across md / json / csv.
- Boundary validation: rejects negative, non-finite, and absurd amounts.
- `localfiscal-web` console entrypoint; CHANGELOG; v0.2 spec under `specs/`.

### Changed
- Reports are derived from one exact integer source, so markdown and JSON can no longer disagree.
- Receipts in mixed currencies are reported per currency instead of being summed into a false total.
- Docker image runs as a **non-root** user; the web server binds **127.0.0.1** by default.
- `requirements.txt` / `pyproject.toml` cleaned up (added `python-multipart`, removed unused
  `sqlalchemy` / `pydantic`, dropped the nonexistent `typer[all]` extra).
- CI now runs ruff + mypy + coverage in addition to the test suite.

### Fixed
- **BLOCKING — money as float.** Amounts were floats end-to-end (`0.1 + 0.2` drift; md/json
  disagreement). Now exact integer minor units.
- **BLOCKING — fabricated $42.00.** A failed receipt scan recorded a fake `$42.00`. It now
  returns *needs-review* and writes nothing.
- **BLOCKING — receipt amount truncation.** `$1,234.56` parsed as `$1.23`. Fixed with a
  locale-aware parser that prefers the grand TOTAL.
- **BLOCKING — path traversal / root write.** The web upload wrote `'/tmp' / file.filename`
  (a `../` escape) as root. Filenames are now sanitized and sandbox-contained; the container
  is non-root.
- Module-level database side effect on import (created `./data` on `--help`) removed (lazy ledger).
- Dead code removed (`SELECT *`, last-match-wins category classifier) and dead config wired
  (`LOCALFISCAL_DB`, `OLLAMA_URL`).

## [0.1.0] — 2026-06

- Initial release: sqlite ledger, receipt heuristic, invoice PDF, FastAPI web UI, CLI, Docker, CI.
