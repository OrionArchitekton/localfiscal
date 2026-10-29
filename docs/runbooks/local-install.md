---
verified: 2026-10-28
review_after: 2027-01-28
topics: [installation, backup, demo]
references: [pyproject.toml, localfiscal/cli.py, localfiscal/demo.py, docker-compose.yml]
---

# Install, verify and recover

## Rollout

Install Python 3.11+ from [python.org](https://www.python.org/downloads/) and pipx using its [current guide](https://pipx.pypa.io/latest/how-to/install-pipx.html).

| OS | Typical prerequisite command | Finish |
|---|---|---|
| macOS with Homebrew | `brew install pipx` | `pipx ensurepath` |
| Ubuntu/Debian with pipx available | `sudo apt install pipx` | `pipx ensurepath` |
| Windows with Python launcher | `py -m pip install --user pipx` | `py -m pipx ensurepath` |

Open a new terminal, then:

```sh
pipx install https://github.com/OrionArchitekton/localfiscal/archive/refs/heads/main.zip
localfiscal health
localfiscal demo --out first-test
```

No standalone binary installer is shipped. Stop the web server and back up books before `pipx upgrade localfiscal`.

## Validate and monitor

Open the sample PDF, CSV and report; net must be $1,195.50. A second run against `first-test` must refuse. CI checks installed-package samples on Linux, Windows and macOS. For the sample web screen:

macOS/Linux:

```sh
export LOCALFISCAL_DB="$PWD/first-test/ledger.db"
localfiscal-web
```

PowerShell:

```powershell
$env:LOCALFISCAL_DB = Join-Path (Get-Location) 'first-test/ledger.db'
localfiscal-web
```

Open [the UI](http://127.0.0.1:8080), check health and download the report. Stop with Ctrl+C. Clear the setting afterwards: `unset LOCALFISCAL_DB` or `Remove-Item Env:LOCALFISCAL_DB`.

The ledger path defaults to the working folder's `data/ledger.db`. Normal report/invoice outputs also use working-folder paths even when the ledger is elsewhere; the demo keeps all outputs in its new folder. Check unreadable-receipt warnings manually. No background workers or automatic backups exist.

## Docker alternative

With Docker and Git installed:

```sh
git clone https://github.com/OrionArchitekton/localfiscal.git
cd localfiscal
docker compose up --build
```

Open loopback port 8080. Preserve the `localfiscal-data` named volume. Never use `docker compose down -v` on real books. Keep the unauthenticated UI local.

## Rollback

Stop the server (or `docker compose down`, preserving volumes). `pipx uninstall localfiscal` removes the app, not your books. Reinstall an approved earlier commit's source archive if needed. Restore a database copy only with the server stopped; preserve the current file separately first. Back up receipt originals and PDFs too. Only delete sample folders after confirming they contain fictional data.
