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
pipx install https://github.com/OrionArchitekton/localfiscal/archive/fb87e96a7f193e870239c7f47eb7d5209f74cf84.zip
localfiscal health
localfiscal demo --out first-test
```

No standalone binary installer is shipped. This archive is pinned to the reviewed implementation commit. It does not track future updates. Stop the web server and back up books before upgrading: uninstall with `pipx uninstall localfiscal`, then install a newer explicitly reviewed commit archive.

Use a local disk. NFS and other remote filesystems are outside the supported demo/ledger path: a remote rename acknowledgement can be ambiguous.

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

The ledger path defaults to the working folder's `data/ledger.db`. Normal report/invoice outputs also use working-folder paths even when the ledger is elsewhere. The demo builds privately and atomically publishes completed books without replacing any existing path. Linux uses `renameat2(RENAME_NOREPLACE)`, macOS `renamex_np(RENAME_EXCL)`, and Windows a non-replacing rename; an unsupported platform/filesystem fails closed. Check unreadable-receipt warnings manually. No background workers or automatic backups exist. Generation errors clean the private staging area without deleting the destination. Requested parent directories may remain. After a forced process termination, inspect any `.localfiscal-demo-*` staging folder and remove it only after confirming ownership and fictional contents.

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
