import csv

def load_stock_data(filepath):
    items = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                quantity = float(row["current_quantity"])
                threshold = float(row["reorder_threshold"])
            except ValueError:
                print("skipping row, couldn't convert:", row)
                continue
            items.append({
                "item_name": row["item_name"],
                "current_quantity": quantity,
                "reorder_threshold": threshold,
            })
    return items

def classify_items(items):
    CRITICAL_FRACTION = 0.25
    flagged = []
    for item in items:
        qty = item["current_quantity"]
        threshold = item["reorder_threshold"]
        if qty > threshold:
            continue
        critical_cutoff = threshold * CRITICAL_FRACTION
        priority = "Critical" if qty <= critical_cutoff else "Low"
        reorder_qty = round((threshold * 1.5) - qty)
        item["priority"] = priority
        item["suggested_reorder_qty"] = reorder_qty
        flagged.append(item)
    return flagged

def print_report(flagged):
    print("RESTOCK REPORT")
    print("=" * 40)
    if not flagged:
        print("All items OK, nothing to restock.")
    else:
        for item in flagged:
            print(f"[{item['priority']}] {item['item_name']} - "
                  f"Current: {item['current_quantity']:.0f}, "
                  f"Threshold: {item['reorder_threshold']:.0f}, "
                  f"Reorder: {item['suggested_reorder_qty']}")
        print(f"\nTotal items needing restock: {len(flagged)}")

def write_csv_report(flagged, output_path="restock_report.csv"):
    fieldnames = ["item_name", "current_quantity", "reorder_threshold",
                  "priority", "suggested_reorder_qty"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in flagged:
            writer.writerow(item)
    print(f"Report saved to {output_path}")

items = load_stock_data("stock.csv")
flagged = classify_items(items)
print_report(flagged)
write_csv_report(flagged)
