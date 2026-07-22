# Restock Checker

A small automation script that reads a warehouse stock CSV, flags any item
at or below its reorder threshold, and generates a clean restock report.
Built to run as an unattended daily job — the kind of quiet backend script
nobody notices until it's missing.

## What it does

- Reads `stock.csv` (item name, current quantity, reorder threshold) into a list of dicts
- Skips any row with missing or non-numeric data instead of crashing
- Compares each item's quantity against its threshold
- Classifies low-stock items as **Critical** (≤25% of threshold) or **Low**
- Calculates a suggested reorder quantity to bring stock back to 1.5x threshold
- Prints a readable console report
- Exports flagged items to `restock_report.csv`

## Usage

```bash
python restock_checker.py
```

Expects `stock.csv` in the same folder, with columns: `item_name`,
`current_quantity`, `reorder_threshold`.

## Approach summary

Loaded the CSV with `csv.DictReader` into a list of dicts, converting
quantity and threshold to numbers inside a try/except so blank or
non-numeric rows (like a missing quantity) get skipped and logged instead
of crashing the script. Compared each valid item's quantity to its
threshold, flagging anything at or below it. Flagged items are split into
Critical (≤25% of threshold) or Low, with a suggested reorder quantity to
reach 1.5x threshold. Results are printed to console and written to
`restock_report.csv`.

## Reflection

With more time I'd add: a real email/notification alert instead of just
console output, a scheduler (cron) so this runs unattended daily,
supplier/SKU lookups so the reorder suggestion ties to an actual purchase
order, and historical trend logging so thresholds could be adjusted based
on real consumption patterns instead of a fixed number.

## Files

- `restock_checker.py` — the main script
- `stock.csv` — sample input data (includes edge cases: missing value, zero stock)
- `restock_report.csv` — example output from running the script on the sample data
