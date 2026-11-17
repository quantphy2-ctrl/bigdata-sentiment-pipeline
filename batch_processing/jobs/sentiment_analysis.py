from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "parquet_day3"
OUTPUT_ROOT = PROJECT_ROOT / "data" / "processed" / "analytics_day4"

EXPECTED_ROWS = 1_615_138


def write_parquet(df, output_path):
    (
        df.write
        .mode("overwrite")
        .partitionBy("source_dataset")
        .parquet(str(output_path))
    )
    print(f"WRITE SUCCESS: {output_path.name}")


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day4_Sentiment_Analysis")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        print("\n========== DAY 4: BATCH SENTIMENT ANALYSIS ==========")
        print("INPUT:", INPUT_PATH)
        print("OUTPUT:", OUTPUT_ROOT)

        # 1. Read Parquet
        print("\n========== 1. READ DATA ==========")
        df = spark.read.parquet(str(INPUT_PATH))

        total_rows = df.count()
        print(f"TOTAL INPUT ROWS: {total_rows:,}")

        if total_rows != EXPECTED_ROWS:
            raise ValueError(
                f"Expected {EXPECTED_ROWS:,} rows, got {total_rows:,}"
            )

        # 2. Validate required fields
        print("\n========== 2. DATA VALIDATION ==========")

        invalid_rows = df.filter(
            F.col("source_dataset").isNull()
            | F.col("sentiment_label").isNull()
            | F.col("created_at").isNull()
        ).count()

        print("INVALID ROWS:", invalid_rows)

        if invalid_rows > 0:
            raise ValueError("Input contains invalid rows")

        # 3. Sentiment distribution by dataset
        print("\n========== 3. SENTIMENT BY DATASET ==========")

        sentiment_counts = (
            df.groupBy("source_dataset", "sentiment_label")
            .agg(F.count("*").alias("record_count"))
        )

        dataset_window = Window.partitionBy("source_dataset")

        sentiment_by_dataset = (
            sentiment_counts
            .withColumn(
                "dataset_total",
                F.sum("record_count").over(dataset_window)
            )
            .withColumn(
                "percentage",
                F.round(
                    F.col("record_count") * 100.0
                    / F.col("dataset_total"),
                    2
                )
            )
            .orderBy("source_dataset", "sentiment_label")
        )

        sentiment_by_dataset.show(30, truncate=False)

        # 4. Daily volume
        print("\n========== 4. DAILY VOLUME ==========")

        daily_volume = (
            df.withColumn("event_date", F.to_date("created_at"))
            .groupBy("source_dataset", "event_date")
            .agg(F.count("*").alias("record_count"))
            .orderBy("source_dataset", "event_date")
        )

        daily_volume.show(20, truncate=False)

        # 5. Daily sentiment
        print("\n========== 5. DAILY SENTIMENT ==========")

        daily_sentiment = (
            df.withColumn("event_date", F.to_date("created_at"))
            .groupBy(
                "source_dataset",
                "event_date",
                "sentiment_label"
            )
            .agg(F.count("*").alias("record_count"))
            .orderBy(
                "source_dataset",
                "event_date",
                "sentiment_label"
            )
        )

        daily_sentiment.show(20, truncate=False)

        # 6. Write analytical outputs
        print("\n========== 6. WRITE ANALYTICS ==========")

        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

        write_parquet(
            sentiment_by_dataset,
            OUTPUT_ROOT / "sentiment_by_dataset"
        )

        write_parquet(
            daily_volume,
            OUTPUT_ROOT / "daily_volume"
        )

        write_parquet(
            daily_sentiment,
            OUTPUT_ROOT / "daily_sentiment"
        )

        # 7. Verify output totals
        print("\n========== 7. VERIFY OUTPUTS ==========")

        checks = {
            "sentiment_by_dataset": sentiment_by_dataset,
            "daily_volume": daily_volume,
            "daily_sentiment": daily_sentiment,
        }

        for name, result_df in checks.items():
            result_total = (
                result_df
                .agg(F.sum("record_count").alias("total"))
                .first()["total"]
            )

            print(f"{name}: {result_total:,}")

            if result_total != EXPECTED_ROWS:
                raise ValueError(
                    f"{name}: expected {EXPECTED_ROWS:,}, "
                    f"got {result_total:,}"
                )

        print("\nDAY 4 BATCH ANALYSIS: PASS")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
