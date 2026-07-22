"""
restock_checker.py

Reads a warehouse stock CSV, flags any item at or below its reorder
threshold, and produces a plain-English restock report.

Meant to run as a daily unattended job (e.g. via cron / Task Scheduler) --
no manual checking required.

Usage:
    python restock_checker.py [path_to_csv]

    If no path is given, defaults to "stock.csv" in the same folder.

Expected CSV columns (header row required):
    item_name, current_quantity, reorder_threshold
"""

import csv
import sys
from datetime import datetime

DEFAULT_INPUT = "stock.csv"
OUTPUT_CSV = "restock_report.csv"

CRITICAL_FRACTION = 0.25

TARGET_STOCK_MULTIPLIER = 1.5


def load_stock_data(filepath):
    """
    Reads the CSV and returns a list of dicts, one per valid row.
    Skips (and reports) rows that are missing data or can't be parsed
    as numbers, rather than crashing the whole job.
    """
    items = []
    skipped = []

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            required_cols = {"item_name", "current_quantity", "reorder_threshold"}
            if not required_cols.issubset(set(reader.fieldnames or [])):
                missing = required_cols - set(reader.fieldnames or [])
                raise ValueError(f"CSV is missing required column(s): {missing}")

            for row_num, row in enumerate(reader, start=2):  # row 1 = header
                name = (row.get("item_name") or "").strip()
                qty_raw = (row.get("current_quantity") or "").strip()
                threshold_raw = (row.get("reorder_threshold") or "").strip()

                if not name:
                    skipped.append((row_num, row, "missing item name"))
                    continue

                if qty_raw == "" or threshold_raw == "":
                    skipped.append((row_num, row, "missing quantity or threshold"))
                    continue

                try:
                    quantity = float(qty_raw)
                    threshold = float(threshold_raw)
                except ValueError:
                    skipped.append((row_num, row, "quantity/threshold not numeric"))
                    continue

                if quantity < 0 or threshold < 0:
                    skipped.append((row_num, row, "negative quantity or threshold"))
                    continue

                items.append({
                    "item_name": name,
                    "current_quantity": quantity,
                    "reorder_threshold": threshold,
                })

    except FileNotFoundError:
        print(f"ERROR: Could not find input file '{filepath}'.")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if skipped:
        print(f"Note: skipped {len(skipped)} row(s) due to bad data:")
        for row_num, row, reason in skipped:
            print(f"  - row {row_num} ({row}): {reason}")
        print()

    return items


def classify_item(item):
    """
    Compares current quantity to threshold and returns the item with
    priority ('Critical' / 'Low' / None) and a suggested reorder qty
    added on, or None if the item doesn't need restocking.
    """
    qty = item["current_quantity"]
    threshold = item["reorder_threshold"]

    if threshold == 0:
        return None

    if qty > threshold:
        return None

    critical_cutoff = threshold * CRITICAL_FRACTION
    priority = "Critical" if qty <= critical_cutoff else "Low"

    target_stock = threshold * TARGET_STOCK_MULTIPLIER
    reorder_qty = max(0, round(target_stock - qty))

    return {
        **item,
        "priority": priority,
        "suggested_reorder_qty": reorder_qty,
    }


def build_restock_list(items):
    flagged = [classify_item(item) for item in items]
    flagged = [item for item in flagged if item is not None]
    flagged.sort(key=lambda i: (i["priority"] != "Critical", i["current_quantity"]))
    return flagged


def print_console_report(flagged):
    print("=" * 50)
    print("RESTOCK REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    if not flagged:
        print("All items are above their reorder threshold. Nothing to do today.")
        return

    for item in flagged:
        print(f"[{item['priority'].upper():8}] {item['item_name']}")
        print(f"           Current: {item['current_quantity']:.0f}  "
              f"Threshold: {item['reorder_threshold']:.0f}  "
              f"Suggested reorder: {item['suggested_reorder_qty']}")
    print("-" * 50)
    print(f"Total items needing restock: {len(flagged)}")


def build_email_alert(flagged):
    """
    Formats the report as a simulated email (subject + body), the way
    an automated alert to a warehouse manager might look.
    """
    critical_count = sum(1 for i in flagged if i["priority"] == "Critical")
    low_count = len(flagged) - critical_count

    subject = f"[Stock Alert] {len(flagged)} item(s) need restocking" if flagged \
        else "[Stock Alert] All items OK - no action needed"

    lines = [
        "To: warehouse-manager@example.com",
        f"Subject: {subject}",
        "",
        f"Hi team,",
        "",
        f"Automated stock check ran on {datetime.now().strftime('%Y-%m-%d %H:%M')}.",
        "",
    ]

    if not flagged:
        lines.append("All items are currently above their reorder threshold. No action needed today.")
    else:
        lines.append(f"{critical_count} item(s) are CRITICAL and {low_count} are LOW. Details below:")
        lines.append("")
        for item in flagged:
            lines.append(
                f"  - [{item['priority']}] {item['item_name']}: "
                f"{item['current_quantity']:.0f} in stock "
                f"(threshold {item['reorder_threshold']:.0f}), "
                f"suggest reordering {item['suggested_reorder_qty']} units."
            )
        lines.append("")
        lines.append("Please arrange reorders for the items above.")

    lines.append("")
    lines.append("- Automated Restock Checker")

    return "\n".join(lines)


def write_csv_report(flagged, output_path):
    fieldnames = [
        "item_name", "current_quantity", "reorder_threshold",
        "priority", "suggested_reorder_qty",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in flagged:
            writer.writerow({k: item[k] for k in fieldnames})


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT

    items = load_stock_data(input_path)
    flagged = build_restock_list(items)

    print_console_report(flagged)

    print()
    print("=" * 50)
    print("SIMULATED EMAIL ALERT")
    print("=" * 50)
    print(build_email_alert(flagged))

    write_csv_report(flagged, OUTPUT_CSV)
    print()
    print(f"Full restock report written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

