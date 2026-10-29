# Sample books

A solo business owner can try receipts, a ledger, an invoice and an export without entering private information.

## Scenarios and acceptance

1. After installing the package, the owner runs `localfiscal demo`. A new `demo-books` folder contains a fictional receipt, a three-entry USD ledger, an invoice PDF, a Markdown report and a transaction CSV. Income is $1,250.00, expenses are $54.50 and net is $1,195.50. No network or optional vision endpoint is used.
2. The owner supplies a different output folder with `--out`. The demo writes only inside that new folder and ignores the real ledger environment setting.
3. If the output path already exists (including a symlink), the command exits with a useful error and leaves all existing contents untouched. Running twice cannot duplicate entries.

4. A receipt-reading or generation error exits unsuccessfully, removes the new partial output and allows a retry. Echoed totals come from the generated ledger.

The existing ledger, report and invoice behavior stays compatible. Reports currently summarize the whole ledger; their period label does not filter dates. Receipt source files and generated PDFs are separate files, not attachments stored in the database.

## Test seam

Use the existing CLI runner seam, inspecting the resulting SQLite ledger, report, CSV and PDF. This exercises the installed command through the actual finance modules without mocks or a second API.
