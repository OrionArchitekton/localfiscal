# localfiscal v0.2 — "harden & honest" spec

**Status:** active · **Authored:** 2026-06-28 (from 4-lens audit of v0.1.0) · **Operator scope decision locked 2026-06-28.**

## Premise

v0.1.0 (autonomously built) shipped a coherent end-to-end vertical but with finance-dangerous
defects and **false public claims**. v0.2 makes every public claim TRUE and every money path exact.
Operator decision (locked): **build all three previously-false features for real** — CSV export,
OFX/QFX export, and an opt-in local vision client — alongside the correctness/safety fixes. Nothing
is cut from public copy to a roadmap.

## Ubiquitous language (one canonical term per concept)

- **Minor units** — money as an exact integer count of a currency's smallest unit (e.g. US cents).
  Replaces "amount as float/REAL". Synonyms retired: "amount" (when it meant a float dollar value).
- **Money** — the in-memory exact representation: integer minor units + an ISO-4217 **currency** code.
- **Needs-review** — an extraction outcome where no amount could be confidently parsed. Replaces the
  v0.1 behaviour of fabricating `$42.00`. A needs-review receipt is NEVER auto-written to the ledger
  with an invented amount.
- **Signed amount** — income is positive, expense is negative. Enables a real **net** (P&L), replacing
  v0.1's "sum of all amounts regardless of direction".

## Test seams (named, fewest/highest)

1. **money seam** — `localfiscal.money` pure functions (`parse_money`, `format_money`, Decimal/minor
   conversions). Unit tests. The foundational exactness seam.
2. **ledger seam** — `Ledger.add` / `.list` round-trip through sqlite. Unit tests on a temp db.
3. **report/export seam** — `generate_report` + `export_csv` / `export_ofx` produce parseable output;
   md and json/csv agree on totals. Unit tests parse the output back.
4. **extract seam** — `extract_receipt` over crafted receipt text. Unit tests (no real OCR needed).
5. **web seam** — FastAPI `TestClient` for the upload-sanitisation + validation scenarios.
6. **vision seam** — the Ollama client behind a small interface, tested with a mocked HTTP transport
   (configured path) and the unconfigured no-op path.

## Scenarios (each a tracer-bullet vertical slice, sequenced by dependency)

### S1 — Money is represented and stored exactly (BLOCKING)
- `parse_money("$1,234.56", "USD")` → `123456` minor units; `format_money(123456, "USD")` → `"$1,234.56"`.
- `parse_money("1.234,56", "EUR")` (EU grouping) → `123456`; rendered with the EUR symbol.
- Adding two amounts that are lossy in float (`0.10 + 0.20`) yields exactly `0.30` in every report format.
- Ledger stores minor units as INTEGER + a currency column; `add`→`list` round-trips with zero drift.
- **Seam:** money + ledger. **Acceptance:** no `float` appears in the money path; md and json totals equal.

### S2 — Receipt amounts are parsed correctly or marked needs-review (BLOCKING)
- A receipt containing `Subtotal 1,200.00 … TOTAL $1,234.56` extracts **1234.56**, not `1.23` and not the subtotal.
- EU-formatted `TOTAL 1.234,56` extracts 1234.56.
- A receipt with no recognisable amount returns **needs-review** (no amount), and ingest does NOT
  write a fabricated `$42.00` (or any invented amount) to the ledger.
- **Seam:** extract (+ ingest path). **Acceptance:** the string `42.0` fabrication is gone; needs-review is surfaced.

### S3 — Money inputs are validated at every boundary (BLOCKING)
- CLI `add` and web `/invoice` reject non-finite, negative-where-not-allowed, and absurd magnitudes
  with a clear error, never persisting a poisoned value.
- **Seam:** CLI (CliRunner) + web (TestClient). **Acceptance:** invalid input → non-zero exit / 4xx, ledger unchanged.

### S4 — Uploads cannot escape their sandbox and the service is not root-exposed by default (BLOCKING)
- Uploading a receipt named `../../etc/passwd` (or any traversal) writes only inside a private temp
  dir under a sanitised basename; nothing is written outside it.
- The container runs as a non-root `USER`; the server binds `127.0.0.1` by default (documented how to expose).
- **Seam:** web (TestClient) + Dockerfile assertion. **Acceptance:** no path escape; Dockerfile has `USER`; default host is loopback.

### S5 — Reports show a real net (signed P&L) (WARNING→done)
- Income and expense carry sign; the report shows income, expense, and **net**, consistent across md/json/csv.
- **Seam:** report. **Acceptance:** net = income − expense, exact.

### S6 — CSV export is real (P1, claim-honesty)
- Two distinct CSV artifacts, both valid RFC-4180 (no JSON-in-a-.csv):
  - **`export --fmt csv`** writes the full **transaction** ledger that re-parses with `csv.reader`
    into the same rows/amounts (the round-trippable accountant export).
  - **`report --fmt csv`** writes the **summary** report (income/expense/net + by-category per
    currency) — the same content as the md/json report, in CSV form (not transactions).
- Every text cell in either CSV is neutralized against spreadsheet formula injection.
- **Seam:** report/export. **Acceptance:** the transaction export round-trips through `csv.reader`;
  the report CSV carries income/expense/net consistent with md/json; no cell triggers a formula.

### S7 — OFX/QFX export is real (P1, claim-honesty)
- An export command emits a well-formed OFX document (valid header + `<OFX>` SGML body, `<STMTTRN>`
  per transaction) that a parser accepts.
- **Seam:** export. **Acceptance:** OFX header present; structure parses; transaction count + amounts match.

### S8 — Optional local vision extraction works and degrades gracefully (P1, claim-honesty)
- With a configured Ollama endpoint, `ingest --vision` (or `OLLAMA_URL` set) sends the image to a local
  vision model and uses its structured result; tested against a mocked HTTP transport.
- With no endpoint configured, the vision path is a **no-op with a clear message** and falls back to the
  heuristic — never a hard dependency, never a crash, never a network call unless explicitly enabled.
- **Seam:** vision (mocked transport) + extract. **Acceptance:** configured → uses model; unconfigured → graceful fallback, 0 network calls.

### S9 — Currency is first-class (P1)
- Every transaction stores a currency; reports render the right symbol; mixed-currency totals are
  rejected or segregated (never silently summed as USD).
- **Seam:** ledger + report. **Acceptance:** EUR stays EUR; a mixed-currency report does not produce a false single total.

### S10 — Docs, deps, and CI tell the truth (P1/P2)
- README has no dead links; CHANGELOG documents v0.2; version is `0.2.0`; dead deps (`sqlalchemy`,
  `pydantic`) and dead code (`Ledger.get`'s `SELECT *`, the `if`-not-`elif` categoriser, module-level
  DB side effects on import) are removed; CI runs ruff + mypy + coverage in addition to pytest.
- **Seam:** repo/CI. **Acceptance:** `ruff`, `mypy`, `pytest` all green in CI; no `import`-time DB creation on `--help`.

## Out of scope (v0.2)
- Multi-user / auth on the web UI beyond loopback-by-default + documented exposure (note in README roadmap).
- Bank-sync / live OFX download (export only). Tax logic. Multi-entity accounting.

## Non-negotiables
- No `float` anywhere in the money path. No fabricated amounts. No network call unless the operator
  explicitly enables vision. Public copy (README + microsite) matches shipped reality exactly.
