import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from batch_processing.readers.csv_reader import read_all_datasets
from batch_processing.normalizers.normalizer import normalize_dataset

# Ghi vào thư mục mới trên ổ D, giữ nguyên kết quả chạy lỗi cũ.
OUTPUT_PATH = str(PROJECT_ROOT / "data" / "processed" / "parquet_day3")
EXPECTED_TOTAL = 1_615_138


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day3_Write_Parquet_Incremental")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        print("\n========== DAY 3: INCREMENTAL PARQUET ==========")
        print("OUTPUT:", OUTPUT_PATH)

        datasets = read_all_datasets(spark)

        if not datasets:
            raise RuntimeError("Khong tim thay dataset nao de ghi.")

        print("\nDATASETS:", list(datasets.keys()))

        for index, (name, raw_df) in enumerate(datasets.items(), start=1):
            print(f"\n========== DATASET {index}/{len(datasets)} ==========")
            print("NAME:", name)
            print("NORMALIZING...")

            normalized_df = normalize_dataset(raw_df)

            required_columns = [
                "event_id",
                "text",
                "created_at",
                "sentiment_label",
                "source_dataset",
            ]

            missing = [
                col for col in required_columns
                if col not in normalized_df.columns
            ]

            if missing:
                raise ValueError(
                    f"Dataset {name} thieu cot bat buoc: {missing}"
                )

            invalid_condition = (
                F.col("event_id").isNull()
                | F.col("text").isNull()
                | F.col("created_at").isNull()
                | F.col("sentiment_label").isNull()
            )

            invalid_rows = normalized_df.filter(
                invalid_condition
            ).limit(1).count()

            if invalid_rows > 0:
                raise ValueError(
                    f"Dataset {name} co ban ghi khong hop le."
                )

            mode = "overwrite" if index == 1 else "append"

            print("WRITE MODE:", mode)
            print("WRITING...")

            (
                normalized_df.write
                .mode(mode)
                .partitionBy("source_dataset")
                .parquet(OUTPUT_PATH)
            )

            print("WRITE SUCCESS:", name)

            # Giải phóng tham chiếu DataFrame trước dataset tiếp theo.
            del normalized_df
            del raw_df

        print("\n========== VERIFY PARQUET ==========")

        parquet_df = spark.read.parquet(OUTPUT_PATH)

        total_rows = parquet_df.count()
        print("TOTAL ROWS:", f"{total_rows:,}")

        print("\nROWS BY DATASET:")
        parquet_df.groupBy("source_dataset").count().show(
            truncate=False
        )

        invalid_total = parquet_df.filter(
            F.col("event_id").isNull()
            | F.col("text").isNull()
            | F.col("created_at").isNull()
            | F.col("sentiment_label").isNull()
        ).limit(1).count()

        print("INVALID ROWS:", invalid_total)

        if total_rows != EXPECTED_TOTAL:
            raise ValueError(
                f"Sai tong so dong: {total_rows:,}; "
                f"mong doi: {EXPECTED_TOTAL:,}"
            )

        if invalid_total != 0:
            raise ValueError("Parquet co ban ghi khong hop le.")

        print("\nDAY 3 PARQUET: PASS")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
