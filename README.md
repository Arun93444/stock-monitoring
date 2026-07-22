# Restock Checker

A small automation script that reads a warehouse stock CSV, flags any item
at or below its reorder threshold, and generates a clean restock report.
Built to run as an unattended daily job — the kind of quiet backend script
nobody notices until it's missing.

## What it does

- Reads `stock.csv` (item name, current quantity, reorder threshold) into a list of dicts
- Compares each item's quantity against its threshold
- Classifies low-stock items as **Critical** (≤25% of threshold) or **Low**
- Calculates a suggested reorder quantity to bring stock back to a healthy level
- Prints a console report
- Prints a simulated email alert (subject + body)
- Exports flagged items to `restock_report.csv`

## Usage

```bash
python restock_checker.py stock.csv
```

If no file path is given, it defaults to `stock.csv` in the same folder.

## Approach summary

Loaded the CSV with `csv.DictReader` into a list of dicts, validating each
row before use so malformed data (blank fields, non-numeric values, missing
names) gets skipped and logged instead of crashing the script. Flagged
items are classified as Critical (≤25% of threshold) or Low, sorted by
urgency, and given a suggested reorder quantity to reach 1.5x threshold.
Output goes to console, a simulated email alert, and a `restock_report.csv`
— structured so it could run daily via cron with no manual intervention.

## Reflection

With more time I'd add: real email delivery via `smtplib`/SendGrid instead
of a printed simulation, a scheduler wrapper (cron/APScheduler) so this
genuinely runs unattended daily, a supplier/SKU lookup so the reorder
suggestion ties to an actual PO, and historical trend tracking (logging
each run's snapshot) so thresholds could be adjusted based on real
consumption patterns instead of a fixed number.

## Files

- `restock_checker.py` — the main script
- `stock.csv` — sample input data (includes edge cases: missing value, zero stock)
- `restock_report.csv` — example output from running the script on the sample data
