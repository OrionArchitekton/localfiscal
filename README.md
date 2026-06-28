# localfiscal

Local-first, private receipt + invoice + ledger for solopreneurs and small businesses.
Your books stay on your machine in a single sqlite file — no cloud, no account, no data exfil.

**The problem it solves:** receipt chaos and tax-time pain without handing your financial
data to a SaaS. localfiscal keeps everything local and gets the boring, important parts right
— money is exact, amounts are never invented, and exports import cleanly into accounting tools.

## What it does (all shipped, all tested)

- **Exact money.** Amounts are stored as integer minor units (cents) with an ISO-4217 currency —
  never floats. The markdown, JSON, and CSV reports always agree to the cent.
- **Receipt extraction.** A heuristic parser reads vendor / amount / date / category from
  image or PDF receipts (locale-aware, prefers the grand **TOTAL**). When it can't read an amount
  it flags the receipt **needs-review** rather than inventing one.
- **Optional local vision.** Off by default. Point it at your own [Ollama](https://ollama.com)
  endpoint (`--vision` / `$OLLAMA_URL`) to use a local vision model for OCR. No endpoint → no
  network call, ever.
- **Invoices.** Generate clean invoice PDFs (fpdf2).
- **Reports.** Income / expense / **net** per currency, as Markdown, JSON, or CSV.
- **Exports accountants use.** Real **CSV** (RFC-4180) and **OFX/QFX** of your ledger.
- **CLI + web UI.** Six CLI commands; a minimal FastAPI web UI (loopback-only by default).
- **One-command Docker.**

MIT. Dan Mercede / OrionArchitekton.

**Releases:** https://github.com/OrionArchitekton/localfiscal/releases ·
**Source:** https://github.com/OrionArchitekton/localfiscal · **Changes:** [CHANGELOG.md](CHANGELOG.md)

## Quick start (Docker)

```bash
git clone https://github.com/OrionArchitekton/localfiscal.git
cd localfiscal
docker compose up --build
# open http://127.0.0.1:8080
```

The web UI binds to **127.0.0.1 only** by default and has **no authentication** — it is meant for
your own machine. To expose it on a LAN, change the compose port mapping to `0.0.0.0:8080:8080`
and put it behind your own auth/proxy first.

## Install (CLI, Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
localfiscal --help
```

## CLI usage

```bash
localfiscal add 2026-06-28 "Coffee Shop" 4.50 --category meals       # expense
localfiscal add 2026-06-01 "Client A" "$1,234.56" --income           # income
localfiscal ingest receipt.pdf                                       # parse a receipt
localfiscal ingest receipt.jpg --vision --ollama-url http://localhost:11434
localfiscal list-tx
localfiscal invoice "Acme Co" 1200 --out invoice.pdf
localfiscal report --fmt md         # or json | csv
localfiscal export --fmt csv        # or ofx  — full ledger for your accountant
localfiscal health
```

Amounts accept grouped/locale formats (`1,234.56`, `1.234,56`) and are validated at the boundary
(no negative, non-finite, or absurd values reach the ledger).

## Privacy & security

- **No network calls** unless you explicitly enable Ollama vision. No telemetry.
- SQL is fully parameterized; uploaded filenames are sanitized (no path traversal).
- The Docker image runs as a **non-root** user; the server binds loopback by default.
- The web UI has no auth — keep it local or front it with your own auth.

## Roadmap

Bank-statement auto-import, recurring transactions, an MCP server surface for agents, and
multi-user self-host are deferred to a later release. See [CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Tests: `pytest -q`. Lint/type: `ruff check . && mypy`.
