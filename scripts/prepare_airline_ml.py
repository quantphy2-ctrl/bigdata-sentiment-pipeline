
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "raw" / "airline" / "Tweets.csv"

OUTPUT = (
    ROOT / "data" / "processed"
    / "airline_ml" / "airline_clean.csv"
)

REPORT = (
    ROOT / "docs" / "reports"
    / "w04_airline_cleaning.json"
)

VALID_LABELS = {"negative", "neutral", "positive"}

if not INPUT.exists():
    raise FileNotFoundError(f"Khong tim thay: {INPUT}")

groups = defaultdict(list)
original_labels = Counter()

total_rows = 0
invalid_rows = 0

# ==========================================
# 1. DOC DU LIEU GOC
# ==========================================

with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        total_rows += 1

        text = row["text"]
        text_key = text.strip()

        label = row["airline_sentiment"].strip().lower()
        tweet_id = row["tweet_id"].strip()

        if (
            not text_key
            or not tweet_id
            or label not in VALID_LABELS
        ):
            invalid_rows += 1
            continue

        original_labels[label] += 1

        groups[text_key].append({
            "tweet_id": tweet_id,
            "text": text,
            "airline_sentiment": label
        })

# ==========================================
# 2. XU LY TRUNG LAP VA NHAN MAU THUAN
# ==========================================

clean_rows = []

conflict_groups = 0
removed_conflict_rows = 0
removed_duplicate_rows = 0

for text_key, records in groups.items():

    labels = {
        record["airline_sentiment"]
        for record in records
    }

    # Cung text nhung khac nhan:
    # Loai toan bo nhom khoi tap ML.
    if len(labels) > 1:
        conflict_groups += 1
        removed_conflict_rows += len(records)
        continue

    # Cung text, cung nhan:
    # Chi giu ban ghi xuat hien dau tien.
    clean_rows.append(records[0])

    removed_duplicate_rows += len(records) - 1

# ==========================================
# 3. LUU DATASET SACH
# ==========================================

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "tweet_id",
            "text",
            "airline_sentiment"
        ]
    )

    writer.writeheader()
    writer.writerows(clean_rows)

# ==========================================
# 4. THONG KE SAU LAM SACH
# ==========================================

clean_labels = Counter(
    row["airline_sentiment"]
    for row in clean_rows
)

report = {
    "original_rows": total_rows,
    "invalid_rows": invalid_rows,
    "conflicting_text_groups": conflict_groups,
    "removed_conflicting_rows": removed_conflict_rows,
    "removed_same_label_duplicate_rows": removed_duplicate_rows,
    "clean_rows": len(clean_rows),
    "original_label_distribution": dict(original_labels),
    "clean_label_distribution": dict(clean_labels),
    "cleaning_rule": (
        "Group by stripped exact text; "
        "drop conflicting-label groups; "
        "retain first record for same-label groups."
    )
}

REPORT.parent.mkdir(parents=True, exist_ok=True)

with REPORT.open("w", encoding="utf-8") as f:
    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n=== W04: LAM SACH TWITTER AIRLINE ===")

for key, value in report.items():
    if not isinstance(value, dict):
        print(f"{key}: {value}")

print("\n=== PHAN BO NHAN BAN DA LAM SACH ===")

for label, count in sorted(clean_labels.items()):
    print(f"{label}: {count:,}")

print(f"\nDa luu CSV: {OUTPUT}")
print(f"Da luu bao cao: {REPORT}")
