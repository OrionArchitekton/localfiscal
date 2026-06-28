# Contributing to localfiscal

- One vertical slice at a time, test-first (RED → GREEN → refactor).
- Money is always exact integer minor units — never floats. Ground every public claim in code.
- CI must stay green. Before opening a PR, run locally:

  ```bash
  pip install -e ".[dev]"
  ruff check .
  mypy
  pytest --cov=localfiscal --cov-fail-under=85
  ```

- MIT license; commits to this repo use the Dan Mercede identity.

Thank you for helping make private, local-first finance tooling real.
