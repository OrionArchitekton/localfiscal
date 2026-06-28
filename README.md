# localfiscal

Ambitious local-first, private receipt + invoice + ledger intelligence for solopreneurs and small businesses.

**The problem it solves:** Receipt chaos, tax-time pain, SaaS lock-in and data exfil for people who just want their books to work privately and simply. Existing OSS is dated or incomplete; cloud tools cost money and leak data. No good working ambitious OSS solution existed — until now.

- Fully local by default (sqlite file)
- Optional local LLM / vision via Ollama for extraction & categorization
- Beautiful-enough web UI + powerful CLI
- Invoice PDFs, reports, exports (CSV/OFX)
- One-command Docker

MIT. Dan Mercede / OrionArchitekton.

## Quick start (Docker, recommended)

```bash
git clone https://github.com/OrionArchitekton/localfiscal.git
cd localfiscal
docker compose up --build
# open http://localhost:8080
```

CLI also available inside or via pipx / editable.

See `docs/quickstart.md` (or README below) for non-docker.

## What v1 delivers (ambitious but shipped)

- Receipt/image/PDF upload → local extraction (vendor, amount, date, suggested category)
- Ledger (add/edit/list/transactions)
- Invoice creation → clean PDF
- Reports: P&L, by category (md + csv)
- Exports for accountants
- All private, no cloud required for core
- Tests + docker proof that the core flows work

## Philosophy (ambitious result)

We follow the ambitious result: solve the painful unsolved problem end-to-end with quality rather than ship a tiny toy. v1 is fuller-than-MVP but has a hard cut-line so it actually ships and proves itself.

## Install (dev / CLI)

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
localfiscal --help
```

## Docker one-liner proof

```bash
docker compose up -d
curl -f http://localhost:8080/health
# then use the web or docker exec for cli
```

## License

MIT © 2026 Dan Mercede

## Status

v0.1 (ambitious localfiscal) — see CHANGELOG and the MAP that drove this build.

## Roadmap (deferred)

v0.2: bank csv auto-import, recurring, better vision models, MCP server surface for agents, multi-user self-host, polish.

## Contributing

See CONTRIBUTING.md. We love tests, small slices, and ambitious scope that ships.

Run tests: `pytest -q`

## Why this exists

Because consumers and businesses deserve a tool that respects their time, money, and privacy — and does the hard boring parts well without forcing them into another subscription or data hostage situation. We built the working solution that didn't exist.