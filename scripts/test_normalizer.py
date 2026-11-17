
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from batch_processing.readers.csv_reader import read_all_datasets
from batch_processing.normalizers.normalizer import normalize_dataset


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day3_Normalizer_Test")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        datasets = read_all_datasets(spark)

        total_rows = 0

        for name, raw_df in datasets.items():
            print("\n" + "=" * 65)
            print("NORMALIZING:", name)

            df = normalize_dataset(raw_df)

            count = df.count()
            total_rows += count

            print("ROWS:", f"{count:,}")
            print("SCHEMA:")
            df.printSchema()

            print("SAMPLE:")
            df.show(5, truncate=80)

            print("SENTIMENT DISTRIBUTION:")
            (
                df.groupBy("sentiment_label")
                .count()
                .orderBy("sentiment_label")
                .show()
            )

            # Kiểm tra event_id.
            null_ids = df.filter(
                df.event_id.isNull()
            ).count()

            print("NULL EVENT IDs:", null_ids)

            # Kiểm tra timestamp.
            null_timestamps = df.filter(
                df.created_at.isNull()
            ).count()

            print("NULL TIMESTAMPS:", null_timestamps)

            # Kiểm tra nhãn không hợp lệ.
            invalid_labels = df.filter(
                df.sentiment_label.isNull()
            ).count()

            print("INVALID SENTIMENT LABELS:", invalid_labels)

        print("\n" + "=" * 65)
        print("TOTAL NORMALIZED ROWS:", f"{total_rows:,}")
        print("EXPECTED TOTAL ROWS: 1,615,138")
        print(
            "TOTAL CHECK:",
            "PASS" if total_rows == 1615138 else "FAIL"
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
