
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

# Xac dinh duong dan project
ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "airline" / "Tweets.csv"
OUTPUT = ROOT / "docs" / "reports" / "w02_airline_eda.json"

VALID_LABELS = {"positive", "negative", "neutral"}

if not INPUT.exists():
    raise FileNotFoundError(f"Khong tim thay dataset: {INPUT}")

# Doc du lieu CSV
with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames or []
    rows = list(reader)

print("=== PHAN TICH TWITTER AIRLINE ===")

# 1. Thong tin co ban
total = len(rows)
print(f"So ban ghi: {total}")
print(f"So cot: {len(columns)}")

# 2. Phan bo nhan
labels = Counter(
    (r.get("airline_sentiment") or "").strip().lower()
    for r in rows
)

print("\n=== PHAN BO NHAN ===")
for label, count in sorted(labels.items()):
    percentage = count / total * 100 if total else 0
    print(f"{label}: {count} ({percentage:.2f}%)")

# 3. Kiem tra du lieu thieu
empty_text = sum(
    not (r.get("text") or "").strip()
    for r in rows
)

empty_id = sum(
    not (r.get("tweet_id") or "").strip()
    for r in rows
)

invalid_labels = sum(
    (r.get("airline_sentiment") or "").strip().lower()
    not in VALID_LABELS
    for r in rows
)

# 4. Kiem tra trung lap
ids = [
    r["tweet_id"].strip()
    for r in rows
    if (r.get("tweet_id") or "").strip()
]

texts = [
    r["text"].strip()
    for r in rows
    if (r.get("text") or "").strip()
]

duplicate_ids = len(ids) - len(set(ids))
duplicate_texts = len(texts) - len(set(texts))

# 5. Kiem tra thoi gian
invalid_dates = 0

for r in rows:
    value = (r.get("tweet_created") or "").strip()

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        invalid_dates += 1

# 6. Kiem tra ky tu thay the encoding
replacement_characters = sum(
    (r.get("text") or "").count("\ufffd")
    for r in rows
)

# 7. Tong hop ket qua
report = {
    "dataset": "Twitter US Airline Sentiment",
    "total_records": total,
    "total_columns": len(columns),
    "columns": columns,
    "label_distribution": dict(labels),
    "empty_text_records": empty_text,
    "empty_id_records": empty_id,
    "invalid_label_records": invalid_labels,
    "duplicate_id_rows": duplicate_ids,
    "duplicate_text_rows": duplicate_texts,
    "invalid_timestamp_records": invalid_dates,
    "replacement_character_count": replacement_characters
}

print("\n=== CHAT LUONG DU LIEU ===")
for key, value in report.items():
    if key not in {"columns", "label_distribution"}:
        print(f"{key}: {value}")

# 8. Luu bao cao JSON
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\nDa luu bao cao tai: {OUTPUT}")
