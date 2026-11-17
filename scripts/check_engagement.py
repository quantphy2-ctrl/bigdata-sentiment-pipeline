
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from batch_processing.readers.csv_reader import read_all_datasets


def main():
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("Day3_Engagement_Check")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        datasets = read_all_datasets(spark)
        airline = datasets["airline"]

        print("\nRETWEET COUNT SUMMARY")

        airline.select(
            F.count("*").alias("total_rows"),
            F.count("retweet_count").alias("non_null"),
            F.sum(
                F.when(F.col("retweet_count").isNull(), 1).otherwise(0)
            ).alias("null_count"),
            F.min(F.col("retweet_count").cast("long")).alias("min_value"),
            F.max(F.col("retweet_count").cast("long")).alias("max_value"),
            F.sum(F.col("retweet_count").cast("long")).alias("total_shares")
        ).show(truncate=False)

        print("SAMPLE VALUES:")
        airline.select("retweet_count").show(10)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
