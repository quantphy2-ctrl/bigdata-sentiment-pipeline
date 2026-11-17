
import sys
from pathlib import Path

# Thêm thư mục gốc dự án vào Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from batch_processing.readers.csv_reader import read_all_datasets


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day3_CSV_Reader_Test")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        datasets = read_all_datasets(spark)

        expected_counts = {
            "airline": 14640,
            "sentiment140_train": 1600000,
            "sentiment140_test": 498,
        }

        for name, df in datasets.items():
            print("\n" + "=" * 60)
            print("DATASET:", name)
            print("COLUMNS:", df.columns)

            df.printSchema()

            actual_count = df.count()
            expected_count = expected_counts[name]

            print(f"ACTUAL ROWS:   {actual_count:,}")
            print(f"EXPECTED ROWS: {expected_count:,}")
            print("COUNT CHECK:", "PASS" if actual_count == expected_count else "FAIL")

            df.select(
                "source_id",
                "source_label",
                "source_timestamp",
                "text"
            ).show(3, truncate=100)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
