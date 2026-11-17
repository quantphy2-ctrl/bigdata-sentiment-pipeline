import csv
import sys
from pathlib import Path
from collections import Counter

files = [
    Path("data/raw/sentiment140/training.1600000.processed.noemoticon.csv"),
    Path("data/raw/sentiment140/testdata.manual.2009.06.14.csv"),
]

for file_path in files:
    print("\n" + "=" * 70)
    print("FILE:", file_path)

    if not file_path.exists():
        print("KHONG TIM THAY FILE")
        continue

    print("Size (MB):", round(file_path.stat().st_size / 1024**2, 2))

    labels = Counter()
    total = 0
    bad_rows = 0
    empty_text = 0
    duplicate_ids = set()
    seen_ids = set()

    try:
        with file_path.open("r", encoding="latin-1", newline="") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')

            for row in reader:
                if len(row) != 6:
                    bad_rows += 1
                    continue

                total += 1

                label, tweet_id, date, flag, user, text = row

                labels[label] += 1

                if not text.strip():
                    empty_text += 1

                if tweet_id in seen_ids:
                    duplicate_ids.add(tweet_id)
                else:
                    seen_ids.add(tweet_id)

                if total <= 20:
                    print(f"\nROW {total}:")
                    print("Label:", label)
                    print("ID:", tweet_id)
                    print("Date:", date)
                    print("Text:", text[:300])

        print("\n--- SUMMARY ---")
        print("Valid records:", total)
        print("Malformed rows:", bad_rows)
        print("Empty text:", empty_text)
        print("Duplicate IDs:", len(duplicate_ids))
        print("Label distribution:")

        for label, count in labels.items():
            percent = count / total * 100 if total else 0
            print(f"  {label}: {count:,} ({percent:.2f}%)")

    except Exception as e:
        print("ERROR:", repr(e))
