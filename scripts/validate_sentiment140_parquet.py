
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HADOOP_HOME = Path(r"C:\hadoop")

if HADOOP_HOME.exists():
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["PATH"] = (
        str(HADOOP_HOME / "bin")
        + os.pathsep
        + os.environ.get("PATH", "")
    )

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

INPUT = (
    ROOT
    / "data"
    / "processed"
    / "sentiment140_train_parquet"
)

if not INPUT.exists():
    raise FileNotFoundError(f"Khong tim thay: {INPUT}")

spark = (
    SparkSession.builder
    .appName("ValidateSentiment140Parquet")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


def is_empty(column):
    return (
        F.col(column).isNull()
        | (F.trim(F.col(column)) == "")
    )


try:
    print("\n=== KIEM TRA CHAT LUONG PARQUET ===")

    df = spark.read.parquet(str(INPUT))

    # 1. Kiem tra so dong va cac gia tri bat buoc
    metrics = df.agg(
        F.count("*").alias("total"),
        F.sum(
            F.when(is_empty("event_id"), 1).otherwise(0)
        ).alias("empty_event_id"),
        F.sum(
            F.when(is_empty("text"), 1).otherwise(0)
        ).alias("empty_text"),
        F.sum(
            F.when(
                is_empty("created_at")
                | ~F.col("created_at").rlike(
                    r"^\d{4}-\d{2}-\d{2}T"
                    r"\d{2}:\d{2}:\d{2}Z$"
                ),
                1
            ).otherwise(0)
        ).alias("invalid_created_at"),
        F.sum(
            F.when(
                F.col("ground_truth_label").isNull()
                | ~F.col("ground_truth_label").isin(
                    "negative", "positive"
                ),
                1
            ).otherwise(0)
        ).alias("invalid_label")
    ).first().asDict()

    print("\n=== THONG KE CO BAN ===")
    for key, value in metrics.items():
        print(f"{key}: {value:,}")

    # 2. Kiem tra event_id duy nhat sau khi ghi Parquet
    print("\n=== KIEM TRA EVENT_ID ===")

    unique_ids = (
        df.select("event_id")
        .distinct()
        .count()
    )

    duplicate_ids = metrics["total"] - unique_ids

    print(f"Unique event IDs: {unique_ids:,}")
    print(f"Duplicate event IDs: {duplicate_ids:,}")

    # 3. Kiem tra phan bo nhan
    print("\n=== PHAN BO NHAN PARQUET ===")

    label_counts = {
        row["ground_truth_label"]: row["count"]
        for row in (
            df.groupBy("ground_truth_label")
            .count()
            .collect()
        )
    }

    for label, count in sorted(label_counts.items()):
        print(f"{label}: {count:,}")

    # 4. Danh gia
    checks = {
        "record_count": metrics["total"] == 1600000,
        "unique_event_id": duplicate_ids == 0,
        "nonempty_event_id": metrics["empty_event_id"] == 0,
        "nonempty_text": metrics["empty_text"] == 0,
        "valid_timestamp_format": (
            metrics["invalid_created_at"] == 0
        ),
        "valid_labels": metrics["invalid_label"] == 0,
        "label_distribution": (
            label_counts.get("negative") == 800000
            and label_counts.get("positive") == 800000
            and len(label_counts) == 2
        )
    }

    print("\n=== KET QUA KIEM DINH ===")

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    if all(checks.values()):
        print("\nPASS: PARQUET DAT CAC TIEU CHI KIEM TRA")
    else:
        raise RuntimeError(
            "FAIL: PARQUET CO CHI SO KHONG DAT"
        )

finally:
    spark.stop()
