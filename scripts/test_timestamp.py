
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from batch_processing.readers.csv_reader import read_all_datasets
from batch_processing.normalizers.normalizer import normalize_timestamp


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day3_Timestamp_Test")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        datasets = read_all_datasets(spark)

        for name, raw_df in datasets.items():
            print("\n" + "=" * 60)
            print("DATASET:", name)

            df = normalize_timestamp(raw_df)

            df.select(
                "source_timestamp",
                "created_at"
            ).show(5, truncate=False)

            total = df.count()
            null_count = df.filter(
                df.created_at.isNull()
            ).count()

            print("TOTAL:", f"{total:,}")
            print("NULL TIMESTAMPS:", null_count)
            print(
                "TIMESTAMP CHECK:",
                "PASS" if null_count == 0 else "FAIL"
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
