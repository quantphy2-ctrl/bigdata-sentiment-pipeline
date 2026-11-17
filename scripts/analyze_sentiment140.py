
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "raw" / "sentiment140"
OUTPUT = ROOT / "docs" / "reports" / "w02_sentiment140_eda.json"

DATASETS = {
    "train": DATA_DIR / "training.1600000.processed.noemoticon.csv",
    "test": DATA_DIR / "testdata.manual.2009.06.14.csv",
}

VALID_LABELS = {
    "train": {"0", "4"},
    "test": {"0", "2", "4"},
}

LABEL_NAMES = {
    "0": "negative",
    "2": "neutral",
    "4": "positive",
}

MONTHS = {
    name: i
    for i, name in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}

DATE_PATTERN = re.compile(
    r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) "
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"(\d{1,2}) (\d{2}):(\d{2}):(\d{2}) "
    r"([A-Z]{2,5}) (\d{4})$"
)

KNOWN_TIMEZONES = {"PDT", "PST", "UTC", "GMT"}


def valid_timestamp(value):
    match = DATE_PATTERN.fullmatch(value.strip())

    if match is None:
        return False

    weekday, month, day, hour, minute, second, zone, year = (
        match.groups()
    )

    if zone not in KNOWN_TIMEZONES:
        return False

    try:
        datetime(
            int(year),
            MONTHS[month],
            int(day),
            int(hour),
            int(minute),
            int(second),
        )
        return True
    except ValueError:
        return False


def analyze_dataset(name, path):
    if not path.exists():
        raise FileNotFoundError(
            f"Khong tim thay file: {path}"
        )

    print(f"\n=== DANG PHAN TICH: {name.upper()} ===")

    total = 0
    malformed = 0
    empty_text = 0
    empty_id = 0
    invalid_label = 0
    invalid_timestamp = 0
    duplicate_ids = 0
    duplicate_texts = 0
    replacement_chars = 0

    labels = Counter()

    # Luu ID va text duy nhat de phat hien trung lap.
    # Khong luu tat ca cac dong CSV vao RAM.
    seen_ids = set()
    seen_texts = set()

    # Sentiment140 co 6 cot va khong co header.
    # File goc thuong duoc doc bang Latin-1.
    with path.open(
        "r",
        encoding="latin-1",
        newline=""
    ) as f:

        reader = csv.reader(f)

        for row in reader:
            total += 1

            if len(row) != 6:
                malformed += 1
                continue

            target, tweet_id, date, flag, user, text = row

            target = target.strip()
            tweet_id = tweet_id.strip()
            text = text.strip()

            labels[target] += 1

            if target not in VALID_LABELS[name]:
                invalid_label += 1

            if not tweet_id:
                empty_id += 1
            elif tweet_id in seen_ids:
                duplicate_ids += 1
            else:
                seen_ids.add(tweet_id)

            if not text:
                empty_text += 1
            elif text in seen_texts:
                duplicate_texts += 1
            else:
                seen_texts.add(text)

            if not valid_timestamp(date):
                invalid_timestamp += 1

            replacement_chars += text.count("\ufffd")

            if total % 250000 == 0:
                print(
                    f"Da kiem tra {total:,} ban ghi..."
                )

    report = {
        "dataset": name,
        "file": path.name,
        "file_size_mb": round(
            path.stat().st_size / (1024 * 1024), 2
        ),
        "total_records": total,
        "malformed_rows": malformed,
        "label_distribution": {
            LABEL_NAMES.get(k, f"unknown_{k}"): v
            for k, v in sorted(labels.items())
        },
        "empty_text_records": empty_text,
        "empty_id_records": empty_id,
        "invalid_label_records": invalid_label,
        "duplicate_id_extra_rows": duplicate_ids,
        "duplicate_text_extra_rows": duplicate_texts,
        "invalid_timestamp_records": invalid_timestamp,
        "replacement_character_count": replacement_chars,
    }

    print(f"So ban ghi: {total:,}")
    print(f"Phan bo nhan: {report['label_distribution']}")
    print(f"Dong sai cau truc: {malformed}")
    print(f"Text rong: {empty_text}")
    print(f"ID rong: {empty_id}")
    print(f"Nhan khong hop le: {invalid_label}")
    print(f"ID trung: {duplicate_ids}")
    print(f"Text trung: {duplicate_texts}")
    print(f"Timestamp khong hop le: {invalid_timestamp}")
    print(f"Ky tu thay the: {replacement_chars}")

    return report


def main():
    results = {}

    for name, path in DATASETS.items():
        results[name] = analyze_dataset(name, path)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n=== HOAN THANH ===")
    print(f"Da luu bao cao: {OUTPUT}")


if __name__ == "__main__":
    main()
