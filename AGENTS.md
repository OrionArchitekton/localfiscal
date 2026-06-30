# AGENTS.md - localfiscal

## Repo Role

`localfiscal` is a local-first Python tool for private receipt, invoice, and
ledger workflows. It keeps financial data on the user's machine, stores exact
money as integer minor units, and flags uncertain extraction instead of
inventing amounts.

## Boundaries

- Owns the Python package, CLI, local web entry point, Docker packaging,
  tests, fixtures, and repo docs.
- Does not own cloud bookkeeping, hosted customer data, payment processing, or
  estate-shared finance systems.
- Preserve local-first privacy and exact-money behavior. Do not add network
  services, telemetry, or data exfiltration without explicit approval.

## Authority Order

1. `/home/orion/src/orion-estate/platform/orion-estate-audit/AGENTS.md`
2. `README.md`
3. `pyproject.toml`, `specs/`, and tests
4. Source tree and Docker files

## Validation

```bash
python -m pytest
ruff check .
```

For docs-only changes, run `git diff --check` at minimum.
