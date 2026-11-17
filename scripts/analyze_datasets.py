import csv
import sqlite3
from pathlib import Path
from collections import Counter
from datetime import datetime
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = REPORT_DIR / "dedup_temp.sqlite"
OUTPUT_PATH = REPORT_DIR / "dataset_statistics.json"

DATASETS = [
    {
        "name": "Twitter US Airline Sentiment",
        "encoding": "cp1252",
        "path": ROOT / "data/raw/Tweets.csv",
        "has_header": True,
        "text_col": "text",
        "label_col": "airline_sentiment",
        "id_col": "tweet_id",
        "time_col": "tweet_created",
        "valid_labels": {"negative", "neutral", "positive"},
    },
    {
        "name": "Sentiment140 Training",
        "encoding": "latin-1",
        "path": ROOT / "data/raw/sentiment140/training.1600000.processed.noemoticon.csv",
        "has_header": False,
        "text_col": 5,
        "label_col": 0,
        "id_col": 1,
        "time_col": 2,
        "valid_labels": {"0", "4"},
    },
    {
        "name": "Sentiment140 Test",
        "encoding": "latin-1",
        "path": ROOT / "data/raw/sentiment140/testdata.manual.2009.06.14.csv",
        "has_header": False,
        "text_col": 5,
        "label_col": 0,
        "id_col": 1,
        "time_col": 2,
        "valid_labels": {"0", "2", "4"},
    },
]

def parse_timestamp(value, dataset_name):
    if not value:
        return False

    value = value.strip()

    # Định dạng Twitter US Airline: 2015-02-24 11:35:52 -0800
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
        return True
    except ValueError:
        pass

    # Định dạng Sentiment140: Mon Apr 06 22:19:45 PDT 2009
    value_without_tz = re.sub(
        r"\s+(PDT|PST|UTC|GMT)\s+",
        " ",
        value
    )

    try:
        datetime.strptime(
            value_without_tz,
            "%a %b %d %H:%M:%S %Y"
        )
        return True
    except ValueError:
        return False

def get_value(row, col, header):
    if isinstance(col, int):
        return row[col] if col < len(row) else ""

    try:
        return row[header.index(col)]
    except (ValueError, IndexError):
        return ""

def analyze(config, conn):
    path = config["path"]
    name = config["name"]

    result = {
        "dataset": name,
        "file": str(path.relative_to(ROOT)),
        "exists": path.exists(),
    }

    if not path.exists():
        result["error"] = "File not found"
        return result

    result["size_bytes"] = path.stat().st_size
    result["size_mb"] = round(path.stat().st_size / 1024**2, 3)

    labels = Counter()
    total = 0
    malformed = 0
    empty_text = 0
    decode_replacement_chars = 0
    missing_label = 0
    invalid_label = 0
    missing_timestamp = 0
    invalid_timestamp = 0
    duplicate_ids = 0
    duplicate_texts = 0
    examples = []
    columns = []

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS seen_ids")
    cur.execute("DROP TABLE IF EXISTS seen_texts")
    cur.execute("CREATE TABLE seen_ids (value TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE seen_texts (value TEXT PRIMARY KEY)")

    with path.open(
    "r",
    encoding=config["encoding"],
    errors="replace",
    newline=""
) as f:
        reader = csv.reader(f)

        header = next(reader) if config["has_header"] else None
        columns = header or [
            "target", "ids", "date", "flag", "user", "text"
        ]

        for row in reader:
            if len(row) != len(columns):
                malformed += 1
                continue

            total += 1

            text = get_value(row, config["text_col"], header)
            label = get_value(row, config["label_col"], header).strip()
            decode_replacement_chars += text.count("\uFFFD")
            record_id = get_value(row, config["id_col"], header).strip()
            timestamp = get_value(row, config["time_col"], header).strip()

            labels[label if label else "<MISSING>"] += 1

            if not text or not text.strip():
                empty_text += 1

            if not label:
                missing_label += 1
            elif label not in config["valid_labels"]:
                invalid_label += 1

            if not timestamp:
                missing_timestamp += 1
            elif not parse_timestamp(timestamp, name):
                invalid_timestamp += 1

            if record_id:
                cur.execute(
                    "INSERT OR IGNORE INTO seen_ids(value) VALUES (?)",
                    (record_id,)
                )
                if cur.rowcount == 0:
                    duplicate_ids += 1

            if text and text.strip():
                cur.execute(
                    "INSERT OR IGNORE INTO seen_texts(value) VALUES (?)",
                    (text,)
                )
                if cur.rowcount == 0:
                    duplicate_texts += 1

            if len(examples) < 20:
                if (
                    not text.strip()
                    or not label
                    or any(x in text for x in ["&amp;", "http://", "https://", "@", "#", "\n"])
                    or any(ord(ch) > 127 for ch in text)
                ):
                    examples.append({
                        "id": record_id,
                        "label": label,
                        "text": text[:500],
                    })

            if total % 100000 == 0:
                print(f"  Processed {total:,} rows...")

    conn.commit()

    valid_label_total = sum(
        count for label, count in labels.items()
        if label in config["valid_labels"]
    )

    label_stats = {}
    for label, count in labels.items():
        denominator = valid_label_total if label in config["valid_labels"] else total
        label_stats[label] = {
            "count": count,
            "percentage_of_valid_labels": (
                round(count / valid_label_total * 100, 2)
                if label in config["valid_labels"] and valid_label_total
                else None
            ),
        }

    result.update({
        "columns": columns,
        "decode_replacement_chars": decode_replacement_chars,
        "records_read": total,
        "malformed_rows": malformed,
        "empty_text": empty_text,
        "missing_label": missing_label,
        "invalid_label": invalid_label,
        "missing_timestamp": missing_timestamp,
        "unparseable_timestamp": invalid_timestamp,
        "duplicate_id_rows": duplicate_ids,
        "duplicate_text_rows": duplicate_texts,
        "valid_label_denominator": valid_label_total,
        "labels": label_stats,
        "sample_quality_examples": examples,
    })

    return result

def main():
    conn = sqlite3.connect(DB_PATH)
    results = []

    try:
        for config in DATASETS:
            print("\n" + "=" * 70)
            print("Analyzing:", config["name"])
            result = analyze(config, conn)
            results.append(result)

            print("Records:", result.get("records_read"))
            print("Malformed:", result.get("malformed_rows"))
            print("Labels:", result.get("labels"))
            print("Empty text:", result.get("empty_text"))
            print("Duplicate IDs:", result.get("duplicate_id_rows"))
            print("Duplicate texts:", result.get("duplicate_text_rows"))

        OUTPUT_PATH.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print("\nSaved report:", OUTPUT_PATH)

    finally:
        conn.close()
        if DB_PATH.exists():
            DB_PATH.unlink()

if __name__ == "__main__":
    main()
