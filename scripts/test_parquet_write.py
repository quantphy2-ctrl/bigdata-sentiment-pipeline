from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    spark = (
        SparkSession.builder
        .appName("ParquetWriteSmokeTest")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    output_path = str(
        Path("data/processed/parquet_smoke_test").resolve()
    )

    try:
        print("\n========== CREATE JVM DATAFRAME ==========")

        # Tạo DataFrame bằng Spark JVM, không dùng Python RDD
        df = (
            spark.range(3)
            .withColumn("text", F.concat(F.lit("sample_"), F.col("id")))
            .withColumn("source_dataset", F.lit("smoke_test"))
        )

        df.show(truncate=False)

        print("\n========== WRITE PARQUET ==========")

        (
            df.write
            .mode("overwrite")
            .partitionBy("source_dataset")
            .parquet(output_path)
        )

        print("PARQUET WRITE: PASS")

        print("\n========== READ PARQUET ==========")

        result = spark.read.parquet(output_path)
        result.show(truncate=False)

        count = result.count()
        print("READ ROW COUNT:", count)

        assert count == 3, f"Expected 3 rows, got {count}"

        print("\n========== RESULT ==========")
        print("PARQUET SMOKE TEST: PASS")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
