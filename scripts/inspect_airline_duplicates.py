
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "airline" / "Tweets.csv"
OUTPUT = ROOT / "docs" / "reports" / "w02_airline_duplicates.json"

by_id = defaultdict(list)
by_text = defaultdict(list)

with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        tweet_id = (row.get("tweet_id") or "").strip()
        text = (row.get("text") or "").strip()
        label = (row.get("airline_sentiment") or "").strip().lower()

        if tweet_id:
            by_id[tweet_id].append((text, label))

        if text:
            by_text[text].append((tweet_id, label))


def count_extra_rows(groups):
    return sum(len(records) - 1 for records in groups.values()
               if len(records) > 1)


duplicate_id_groups = {
    key: records
    for key, records in by_id.items()
    if len(records) > 1
}

duplicate_text_groups = {
    key: records
    for key, records in by_text.items()
    if len(records) > 1
}

# Cung ID nhung nhan khac nhau
id_conflicting_labels = sum(
    len({label for text, label in records}) > 1
    for records in duplicate_id_groups.values()
)

# Cung ID nhung noi dung khac nhau
id_conflicting_texts = sum(
    len({text for text, label in records}) > 1
    for records in duplicate_id_groups.values()
)

# Cung noi dung nhung nhan cam xuc khac nhau
text_conflicting_labels = sum(
    len({label for tweet_id, label in records}) > 1
    for records in duplicate_text_groups.values()
)

report = {
    "duplicate_id_groups": len(duplicate_id_groups),
    "duplicate_id_extra_rows": count_extra_rows(by_id),
    "same_id_different_label_groups": id_conflicting_labels,
    "same_id_different_text_groups": id_conflicting_texts,
    "duplicate_text_groups": len(duplicate_text_groups),
    "duplicate_text_extra_rows": count_extra_rows(by_text),
    "same_text_different_label_groups": text_conflicting_labels
}

print("=== KIEM TRA TRUNG LAP CHI TIET ===")

for key, value in report.items():
    print(f"{key}: {value}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\nDa luu bao cao: {OUTPUT}")
