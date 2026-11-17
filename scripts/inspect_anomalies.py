
import csv
import json
import re
from pathlib import Path
from collections import Counter
from html import unescape

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "reports" / "anomaly_samples.json"

DATASETS = [
    {
        "name": "Twitter US Airline Sentiment",
        "path": ROOT / "data/raw/Tweets.csv",
        "encoding": "cp1252",
        "header": True,
        "text_col": "text",
    },
    {
        "name": "Sentiment140 Training",
        "path": ROOT / "data/raw/sentiment140/training.1600000.processed.noemoticon.csv",
        "encoding": "latin-1",
        "header": False,
        "text_col": 5,
    },
    {
        "name": "Sentiment140 Test",
        "path": ROOT / "data/raw/sentiment140/testdata.manual.2009.06.14.csv",
        "encoding": "latin-1",
        "header": False,
        "text_col": 5,
    },
]

PATTERNS = {
    "Mention (@username)": re.compile(r"@\w+"),
    "Hashtag (#topic)": re.compile(r"#\w+"),
    "URL": re.compile(r"https?://|www\.", re.I),
    "HTML Entity": re.compile(r"&(?:amp|lt|gt|quot|#\d+);", re.I),
    "Từ phủ định": re.compile(
        r"\b(?:not|no|never|don't|didn't|can't|isn't|wasn't|won't)\b",
        re.I,
    ),
    "Từ viết tắt": re.compile(
        r"\b(?:lol|omg|idk|imo|btw| u |ur|thx|lmao)\b",
        re.I,
    ),
    "Nhiều dấu câu": re.compile(r"[!?]{2,}|\.{3,}"),
    "Ký tự thay thế encoding": re.compile("\uFFFD"),
    "Ký tự Unicode/emoji": re.compile(
        r"[^\x00-\x7F]"
    ),
}

def mask_private_parts(text):
    # Ẩn tên tài khoản và URL trong báo cáo mẫu
    text = re.sub(r"@\w+", "@USER", text)
    text = re.sub(r"https?://\S+|www\.\S+", "[URL]", text)
    return text.replace("\r", " ").replace("\n", " ")[:400]

def get_text(row, config, header):
    if config["header"]:
        return row.get(config["text_col"], "") or ""
    return row[config["text_col"]] if len(row) > config["text_col"] else ""

def main():
    buckets = {name: [] for name in PATTERNS}
    buckets["Có xuống dòng"] = []
    buckets["Có dấu hiệu HTML sau giải mã"] = []

    total_records = Counter()

    for config in DATASETS:
        path = config["path"]

        if not path.exists():
            print(f"Không tìm thấy: {path}")
            continue

        with path.open(
            "r",
            encoding=config["encoding"],
            errors="replace",
            newline="",
        ) as f:
            if config["header"]:
                reader = csv.DictReader(f)
            else:
                reader = csv.reader(f)

            for row in reader:
                text = get_text(row, config, None)
                if not text.strip():
                    continue

                total_records[config["name"]] += 1

                for category, pattern in PATTERNS.items():
                    if pattern.search(text) and len(buckets[category]) < 2:
                        buckets[category].append({
                            "dataset": config["name"],
                            "category": category,
                            "text": mask_private_parts(text),
                        })

                if "\n" in text or "\r" in text:
                    if len(buckets["Có xuống dòng"]) < 2:
                        buckets["Có xuống dòng"].append({
                            "dataset": config["name"],
                            "category": "Có xuống dòng",
                            "text": mask_private_parts(text),
                        })

                if unescape(text) != text:
                    if len(buckets["Có dấu hiệu HTML sau giải mã"]) < 2:
                        buckets["Có dấu hiệu HTML sau giải mã"].append({
                            "dataset": config["name"],
                            "category": "Có dấu hiệu HTML sau giải mã",
                            "text": mask_private_parts(text),
                        })

    samples = []
    seen = set()

    for category, items in buckets.items():
        for item in items:
            key = (item["dataset"], item["text"])
            if key not in seen and len(samples) < 20:
                seen.add(key)
                samples.append(item)

    result = {
        "total_records_scanned": dict(total_records),
        "sample_count": len(samples),
        "samples": samples,
        "notes": [
            "Đây là các mẫu được chọn tự động để kiểm tra thủ công.",
            "Tên tài khoản và URL đã được ẩn trong nội dung mẫu.",
            "Ký tự Unicode không đồng nghĩa chắc chắn với emoji hoặc lỗi encoding.",
            "Cần kiểm tra thủ công trước khi quyết định tiền xử lý."
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Đã lưu:", OUTPUT)
    print("Số mẫu được chọn:", len(samples))
    print("\nSố bản ghi đã quét:")
    for name, count in total_records.items():
        print(f"- {name}: {count:,}")

    print("\nCác nhóm mẫu:")
    for category, items in buckets.items():
        if items:
            print(f"- {category}: {len(items)} mẫu")

if __name__ == "__main__":
    main()
