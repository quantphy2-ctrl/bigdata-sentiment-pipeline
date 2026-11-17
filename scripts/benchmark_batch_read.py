
import os
import json
import time
import statistics
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
from pyspark.sql.types import (
    StructType, StructField, StringType
)

CSV_PATH = (
    ROOT / "data" / "raw" / "sentiment140"
    / "training.1600000.processed.noemoticon.csv"
)

PARQUET_PATH = (
    ROOT / "data" / "processed"
    / "sentiment140_train_parquet"
)

REPORT_PATH = (
    ROOT / "docs" / "reports"
    / "w03_batch_read_benchmark.json"
)

if not CSV_PATH.exists() or not PARQUET_PATH.exists():
    raise FileNotFoundError(
        "Khong tim thay CSV hoac Parquet"
    )

spark = (
    SparkSession.builder
    .appName("BatchReadBenchmark")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

csv_schema = StructType([
    StructField("target", StringType(), True),
    StructField("ids", StringType(), True),
    StructField("date", StringType(), True),
    StructField("flag", StringType(), True),
    StructField("user", StringType(), True),
    StructField("text", StringType(), True)
])


def scan_dataset(name, df):
    start = time.perf_counter()

    # Buoc Spark phai doc noi dung text va
    # tinh tong chieu dai van ban.
    # Khong chi count(), vi Parquet co the
    # toi uu count bang metadata.
    result = df.agg(
        F.count("*").alias("rows"),
        F.sum(F.length("text")).alias("text_chars")
    ).first()

    elapsed = time.perf_counter() - start

    rows = int(result["rows"])
    chars = int(result["text_chars"] or 0)
    throughput = rows / elapsed if elapsed > 0 else 0

    print(
        f"{name}: "
        f"{elapsed:.3f} giay | "
        f"{throughput:,.0f} dong/giay | "
        f"{rows:,} dong"
    )

    return {
        "seconds": round(elapsed, 3),
        "rows": rows,
        "text_chars": chars,
        "rows_per_second": round(throughput, 2)
    }


try:
    csv_df = (
        spark.read
        .format("csv")
        .option("header", "false")
        .option("encoding", "ISO-8859-1")
        .schema(csv_schema)
        .load(str(CSV_PATH))
    )

    parquet_df = spark.read.parquet(
        str(PARQUET_PATH)
    )

    # Chay khoi dong de giam anh huong
    # cua chi phi khoi tao Spark.
    print("\n=== WARM-UP (KHONG TINH) ===")

    csv_warmup = scan_dataset("CSV", csv_df)
    parquet_warmup = scan_dataset("Parquet", parquet_df)

    if (
        csv_warmup["rows"] != 1600000
        or parquet_warmup["rows"] != 1600000
        or csv_warmup["text_chars"]
        != parquet_warmup["text_chars"]
    ):
        raise RuntimeError(
            "CSV va Parquet khong khop so dong "
            "hoac tong ky tu van ban"
        )

    # Do 3 vong, cung mot phep tinh.
    results = {
        "csv": [],
        "parquet": []
    }

    for i in range(1, 4):
        print(f"\n=== LAN DO {i}/3 ===")

        csv_result = scan_dataset(
            "CSV", csv_df
        )

        parquet_result = scan_dataset(
            "Parquet", parquet_df
        )

        if (
            csv_result["rows"] != 1600000
            or parquet_result["rows"] != 1600000
            or csv_result["text_chars"]
            != parquet_result["text_chars"]
        ):
            raise RuntimeError(
                f"Du lieu khong khop o lan do {i}"
            )

        results["csv"].append(csv_result)
        results["parquet"].append(parquet_result)

    csv_median = statistics.median(
        x["seconds"] for x in results["csv"]
    )

    parquet_median = statistics.median(
        x["seconds"] for x in results["parquet"]
    )

    print("\n=== TONG KET BENCHMARK ===")

    print(f"CSV median: {csv_median:.3f} giay")
    print(
        f"Parquet median: {parquet_median:.3f} giay"
    )

    print(
        "CSV throughput: "
        f"{1600000 / csv_median:,.0f} dong/giay"
    )

    print(
        "Parquet throughput: "
        f"{1600000 / parquet_median:,.0f} dong/giay"
    )

    report = {
        "dataset": "Sentiment140 Training",
        "records": 1600000,
        "benchmark_type": "read_and_text_length_scan",
        "spark_mode": "local[2]",
        "warmup_excluded": True,
        "measured_runs": 3,
        "results": results,
        "median_seconds": {
            "csv": round(csv_median, 3),
            "parquet": round(parquet_median, 3)
        },
        "median_based_rows_per_second": {
            "csv": round(1600000 / csv_median, 2),
            "parquet": round(1600000 / parquet_median, 2)
        }
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nDa luu bao cao: {REPORT_PATH}")

finally:
    spark.stop()
