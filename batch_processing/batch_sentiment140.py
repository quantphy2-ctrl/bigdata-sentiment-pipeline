
import os
from pathlib import Path
from datetime import datetime, timezone
# ==========================================
# 1. CAU HINH MOI TRUONG
# ==========================================

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
from pyspark.sql.functions import (
    col,
    when,
    regexp_extract,
    regexp_replace,
    to_timestamp,
    date_format,
    expr,
    row_number,
    concat,
    lit,
    struct
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType
)

INPUT = (
    ROOT
    / "data"
    / "raw"
    / "sentiment140"
    / "training.1600000.processed.noemoticon.csv"
)

if not INPUT.exists():
    raise FileNotFoundError(
        f"Khong tim thay file: {INPUT}"
    )

# ==========================================
# 2. KHOI TAO SPARK SESSION
# ==========================================

spark = (
    SparkSession.builder
    .appName("Sentiment140Batch")
    .master("local[2]")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")
spark.conf.set("spark.sql.session.timeZone", "UTC")

# ==========================================
# 3. DINH NGHIA SCHEMA CSV GOC
# ==========================================

# Sentiment140 khong co header.
# Ca 6 cot tam thoi duoc doc dang string.

raw_schema = StructType([
    StructField("target", StringType(), True),
    StructField("ids", StringType(), True),
    StructField("date", StringType(), True),
    StructField("flag", StringType(), True),
    StructField("user", StringType(), True),
    StructField("text", StringType(), True)
])

# ==========================================
# 4. DOC DU LIEU BANG PYSPARK
# ==========================================

try:
    print("\n=== BAT DAU BATCH PROCESSING ===")

    df = (
        spark.read
        .format("csv")
        .option("header", "false")
        .option("encoding", "ISO-8859-1")
        .option("mode", "PERMISSIVE")
        .schema(raw_schema)
        .load(str(INPUT))
    )

    # ======================================
    # 5. KIEM TRA DU LIEU
    # ======================================

    print("\n=== SO LUONG BAN GHI ===")
    total = df.count()
    print(f"Total records: {total:,}")

    print("\n=== SCHEMA DU LIEU ===")
    df.printSchema()

    print("\n=== 5 BAN GHI MAU ===")
    (
        df.select(
            "target",
            "ids",
            "date",
            "text"
        )
        .show(5, truncate=60)
    )

    print("\n=== KET QUA KIEM TRA ===")

    if total == 1600000:
        print("PASS: Doc du 1,600,000 ban ghi")
    else:
        print(
            f"WARNING: So dong khac ky vong: {total:,}"
        )

    # ======================================
    # 6. CHUAN HOA NHAN CAM XUC
    # ======================================

    print("\n=== CHUAN HOA NHAN CAM XUC ===")

    transformed_df = df.withColumn(
        "ground_truth_label",
        when(col("target") == "0", "negative")
        .when(col("target") == "2", "neutral")
        .when(col("target") == "4", "positive")
        .otherwise(None)
    )

    print("\n=== PHAN BO NHAN SAU CHUYEN DOI ===")

    (
        transformed_df
        .groupBy("ground_truth_label")
        .count()
        .orderBy("ground_truth_label")
        .show()
    )

    print("\n=== KIEM TRA NHAN KHONG HOP LE ===")

    invalid_count = (
        transformed_df
        .filter(col("ground_truth_label").isNull())
        .count()
    )

    print(f"Invalid labels: {invalid_count:,}")

    print("\n=== DU LIEU MAU SAU CHUYEN DOI ===")

    transformed_df.select(
        "target",
        "ground_truth_label",
        "text"
    ).show(5, truncate=65)

    # ======================================
    # 7. KIEM TRA MUI GIO DU LIEU GOC
    # ======================================

    print("\n=== THONG KE MUI GIO SENTIMENT140 ===")

    timezone_df = transformed_df.withColumn(
        "source_timezone",
        regexp_extract(
            col("date"),
            r"\s([A-Z]{2,5})\s\d{4}$",
            1
        )
    )

    (
        timezone_df
        .groupBy("source_timezone")
        .count()
        .orderBy("source_timezone")
        .show(truncate=False)
    )

    # ======================================
    # 8. CHUAN HOA TIMESTAMP SANG UTC
    # ======================================

    print("\n=== CHUAN HOA TIMESTAMP SANG UTC ===")

    # Vi du:
    # Mon Apr 06 22:19:45 PDT 2009
    # -> Apr 06 22:19:45 2009

    clean_date = regexp_replace(
        regexp_replace(
            col("date"),
            r"^[A-Za-z]{3}\s+",
            ""
        ),
        r"\sPDT\s",
        " "
    )

    timestamp_df = (
        timezone_df
        .withColumn(
            "source_local_timestamp",
            to_timestamp(
                clean_date,
                "MMM dd HH:mm:ss yyyy"
            )
        )
        .withColumn(
            "created_at",
            date_format(
                expr(
                    "source_local_timestamp + INTERVAL 7 HOURS"
                ),
                "yyyy-MM-dd'T'HH:mm:ss'Z'"
            )
        )
    )

    print("\n=== 5 TIMESTAMP MAU ===")

    timestamp_df.select(
        "date",
        "source_timezone",
        "created_at"
    ).show(5, truncate=False)

    print("\n=== KIEM TRA TIMESTAMP KHONG HOP LE ===")

    invalid_timestamps = (
        timestamp_df
        .filter(col("created_at").isNull())
        .count()
    )

    print(f"Invalid timestamps: {invalid_timestamps:,}")

    print("\n=== KIEM TRA CHUYEN DOI MAU ===")

    sample_check = (
        timestamp_df
        .filter(
            col("date") == "Mon Apr 06 22:19:45 PDT 2009"
        )
        .select("created_at")
        .first()
    )

    if (
        sample_check is not None
        and sample_check["created_at"]
        == "2009-04-07T05:19:45Z"
    ):
        print("PASS: Timestamp mau chuyen doi dung")
    else:
        print("WARNING: Can kiem tra timestamp mau")

    # ======================================
    # 9. TAO EVENT_ID DUY NHAT
    # ======================================

    print("\n=== TAO EVENT_ID DUY NHAT ===")

    # Danh so cac ban ghi co cung ID goc.
    # Sap xep theo toan bo cac truong con lai
    # de ket qua co the tai lap tren cung dataset.

    id_window = (
        Window
        .partitionBy("ids")
        .orderBy(
            "target",
            "date",
            "flag",
            "user",
            "text"
        )
    )

    event_df = (
        timestamp_df
        .withColumn(
            "id_sequence",
            row_number().over(id_window)
        )
        .withColumn(
            "event_id",
            concat(
                lit("s140_train_"),
                col("ids"),
                lit("_"),
                col("id_sequence").cast("string")
            )
        )
    )

    print("\n=== 5 EVENT_ID MAU ===")

    event_df.select(
        "ids",
        "id_sequence",
        "event_id"
    ).show(5, truncate=False)

    print("\n=== KIEM TRA TINH DUY NHAT ===")

    total_events = event_df.count()

    unique_events = (
        event_df
        .select("event_id")
        .distinct()
        .count()
    )

    duplicate_events = total_events - unique_events

    print(f"Total events: {total_events:,}")
    print(f"Unique event IDs: {unique_events:,}")
    print(f"Duplicate event IDs: {duplicate_events:,}")

    if (
        total_events == 1600000
        and duplicate_events == 0
    ):
        print("PASS: Tat ca event_id deu duy nhat")
    else:
        print("WARNING: Can kiem tra event_id")

    # ======================================
    # 10. DATA MAPPING SANG SCHEMA CHUNG
    # ======================================

    print("\n=== DATA MAPPING SANG SCHEMA CHUNG ===")

    # Ghi thoi diem thuc hien lan xu ly Batch.
    # Su dung mot gia tri chung cho tat ca ban ghi.
    batch_collected_at = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    mapped_df = event_df.select(
        col("event_id"),

        lit("twitter").alias("platform"),

        lit("post").alias("content_type"),

        col("text"),

        lit("en").alias("language"),

        col("created_at"),

        lit(batch_collected_at).alias("collected_at"),

        struct(
            lit(None).cast("long").alias("likes"),
            lit(None).cast("long").alias("replies"),
            lit(None).cast("long").alias("shares")
        ).alias("engagement"),

        col("ids").alias("source_record_id"),

        col("ground_truth_label")
    )

    print("\n=== SCHEMA SAU CHUAN HOA ===")

    mapped_df.printSchema()

    print("\n=== 5 BAN GHI MAU SAU MAPPING ===")

    mapped_df.select(
        "event_id",
        "platform",
        "content_type",
        "text",
        "language",
        "created_at",
        "collected_at",
        "source_record_id",
        "ground_truth_label"
    ).show(5, truncate=50)

    print("\n=== KIEM TRA ENGAGEMENT ===")

    mapped_df.select("engagement").show(3, truncate=False)

    print("\nHoan thanh Data Mapping.")

    # ======================================
    # 11. XUAT DU LIEU SANG PARQUET
    # ======================================

    print("\n=== XUAT DU LIEU SANG PARQUET ===")

    parquet_path = (
        ROOT
        / "data"
        / "processed"
        / "sentiment140_train_parquet"
    )

    # Khong tu dong ghi de ket qua cu.
    if parquet_path.exists():
        raise FileExistsError(
            f"Thu muc Parquet da ton tai: {parquet_path}"
        )

    parquet_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Ghi du lieu bang dinh dang Parquet + Snappy.
    (
        mapped_df
        .write
        .mode("errorifexists")
        .option("compression", "snappy")
        .parquet(str(parquet_path))
    )

    print(f"Da xuat Parquet: {parquet_path}")

    # ======================================
    # 12. DOC LAI PARQUET DE KIEM TRA
    # ======================================

    print("\n=== KIEM TRA PARQUET DA LUU ===")

    parquet_df = spark.read.parquet(
        str(parquet_path)
    )

    parquet_count = parquet_df.count()

    print(f"Parquet records: {parquet_count:,}")

    if parquet_count == 1600000:
        print("PASS: Parquet chua du 1,600,000 ban ghi")
    else:
        raise RuntimeError(
            f"Sai so ban ghi Parquet: {parquet_count:,}"
        )

    print("\n=== SCHEMA PARQUET ===")
    parquet_df.printSchema()

    print("\nHoan thanh xuat va kiem tra Parquet.")

    print("\nHoan thanh buoc doc CSV bang PySpark.")

finally:
    spark.stop()
