from pathlib import Path
from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARQUET_PATH = PROJECT_ROOT / "data" / "processed" / "parquet_day3"

def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day4_Parquet_Reader")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        print("\n========== DAY 4: PARQUET READER ==========")

        df = spark.read.parquet(str(PARQUET_PATH))

        print("\n========== SCHEMA ==========")
        df.printSchema()

        print("\n========== TOTAL ROWS ==========")
        total = df.count()
        print(f"TOTAL: {total:,}")

        print("\n========== DATASET DISTRIBUTION ==========")
        df.groupBy("source_dataset").count().orderBy("source_dataset").show()

        print("\n========== SENTIMENT DISTRIBUTION ==========")
        df.groupBy("sentiment_label").count().orderBy("sentiment_label").show()

        print("\n========== SAMPLE DATA ==========")
        df.select(
            "event_id",
            "source_dataset",
            "created_at",
            "sentiment_label",
            "text"
        ).show(5, truncate=80)

        if total != 1615138:
            raise ValueError(f"Expected 1615138 rows, got {total}")

        print("\nPARQUET READER: PASS")

    finally:
        spark.stop()

if __name__ == "__main__":
    main()
