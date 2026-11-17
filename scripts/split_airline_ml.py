
import csv
import json
from collections import Counter
from pathlib import Path

from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT / "data" / "processed"
    / "airline_ml" / "airline_clean.csv"
)

OUTPUT_DIR = (
    ROOT / "data" / "processed" / "airline_ml"
)

REPORT = (
    ROOT / "docs" / "reports"
    / "w04_airline_split.json"
)

RANDOM_STATE = 42

# ==========================================
# 1. DOC DU LIEU DA LAM SACH
# ==========================================

if not INPUT.exists():
    raise FileNotFoundError(f"Khong tim thay: {INPUT}")

with INPUT.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print("\n=== W04: CHIA DU LIEU MACHINE LEARNING ===")
print(f"Total clean records: {len(rows):,}")

if len(rows) != 14402:
    raise ValueError(
        f"So dong khong dung ky vong: {len(rows)}"
    )

# Xac nhan text la duy nhat truoc khi chia
all_texts = [row["text"].strip() for row in rows]

if len(all_texts) != len(set(all_texts)):
    raise ValueError(
        "Dataset van con text trung lap!"
    )

# ==========================================
# 2. CHIA TRAIN 70% VA TEMP 30%
# ==========================================

train_rows, temp_rows = train_test_split(
    rows,
    test_size=0.30,
    random_state=RANDOM_STATE,
    stratify=[
        row["airline_sentiment"]
        for row in rows
    ]
)

# ==========================================
# 3. CHIA TEMP THANH VALIDATION VA TEST
# ==========================================

val_rows, test_rows = train_test_split(
    temp_rows,
    test_size=0.50,
    random_state=RANDOM_STATE,
    stratify=[
        row["airline_sentiment"]
        for row in temp_rows
    ]
)

datasets = {
    "train": train_rows,
    "validation": val_rows,
    "test": test_rows
}

# ==========================================
# 4. KIEM TRA DATA LEAKAGE
# ==========================================

text_sets = {
    name: {row["text"].strip() for row in data}
    for name, data in datasets.items()
}

assert text_sets["train"].isdisjoint(
    text_sets["validation"]
)

assert text_sets["train"].isdisjoint(
    text_sets["test"]
)

assert text_sets["validation"].isdisjoint(
    text_sets["test"]
)

assert sum(len(data) for data in datasets.values()) == len(rows)

print("\nPASS: Khong co text trung giua cac tap")

# ==========================================
# 5. LUU CAC TAP DU LIEU
# ==========================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "dataset": "Twitter US Airline Sentiment",
    "clean_records": len(rows),
    "random_state": RANDOM_STATE,
    "split_method": "stratified",
    "splits": {}
}

for name, data in datasets.items():
    path = OUTPUT_DIR / f"{name}.csv"

    with path.open(
        "w", encoding="utf-8", newline=""
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
        writer.writerows(data)

    labels = Counter(
        row["airline_sentiment"]
        for row in data
    )

    report["splits"][name] = {
        "records": len(data),
        "percentage": round(
            len(data) / len(rows) * 100, 2
        ),
        "label_distribution": dict(labels)
    }

    print(f"\n=== {name.upper()} ===")
    print(f"Records: {len(data):,}")

    for label, count in sorted(labels.items()):
        print(f"{label}: {count:,}")

    print(f"Saved: {path}")

# ==========================================
# 6. LUU BAO CAO
# ==========================================

REPORT.parent.mkdir(parents=True, exist_ok=True)

with REPORT.open("w", encoding="utf-8") as f:
    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n=== HOAN THANH ===")
print("PASS: Stratified Split thanh cong")
print("PASS: Khong phat hien text trung giua cac tap")
print(f"Report: {REPORT}")
