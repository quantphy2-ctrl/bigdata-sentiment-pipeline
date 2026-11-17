
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Cho phep import module trong processing/
sys.path.insert(0, str(ROOT))

HADOOP_HOME = Path(r"C:\hadoop")

if HADOOP_HOME.exists():
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["PATH"] = (
        str(HADOOP_HOME / "bin")
        + os.pathsep
        + os.environ.get("PATH", "")
    )

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from processing.sentiment_inference import (
    MODEL_VERSION,
    predict_sentiments
)

PARQUET_PATH = (
    ROOT
    / "data"
    / "processed"
    / "sentiment140_train_parquet"
)

if not PARQUET_PATH.exists():
    raise FileNotFoundError(
        f"Khong tim thay Parquet: {PARQUET_PATH}"
    )

# ==========================================
# 1. KHOI TAO SPARK
# ==========================================

spark = (
    SparkSession.builder
    .appName("BatchMLInferenceSmokeTest")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    print("\n=== BATCH + ML INTEGRATION TEST ===")
    print(f"Model: {MODEL_VERSION}")

    # ======================================
    # 2. DOC DU LIEU PARQUET
    # ======================================

    df = spark.read.parquet(str(PARQUET_PATH))

    # Lay 3 tweet Negative va 3 tweet Positive
    # Chi de thu nghiem ket noi.
    rows = []

    for label in ["negative", "positive"]:
        samples = (
            df.filter(
                col("ground_truth_label") == label
            )
            .select(
                "event_id",
                "text",
                "ground_truth_label"
            )
            .limit(3)
            .collect()
        )

        if len(samples) != 3:
            raise RuntimeError(
                f"Khong du mau cho nhan {label}"
            )

        rows.extend(samples)

    print(f"Sample records: {len(rows)}")

    # ======================================
    # 3. GOI SHARED INFERENCE
    # ======================================

    texts = [row["text"] for row in rows]

    predictions = predict_sentiments(texts)

    if len(predictions) != len(rows):
        raise RuntimeError(
            "So ket qua du doan khong khop"
        )

    # ======================================
    # 4. KIEM TRA KET QUA
    # ======================================

    valid_labels = {
        "negative", "neutral", "positive"
    }

    for i, (row, prediction) in enumerate(
        zip(rows, predictions),
        start=1
    ):
        predicted_label = prediction["sentiment_label"]
        confidence = prediction["sentiment_confidence"]
        processed_at = prediction["processed_at"]

        if predicted_label not in valid_labels:
            raise ValueError("Nhan du doan khong hop le")

        if not 0 <= confidence <= 1:
            raise ValueError("Confidence khong hop le")

        if not processed_at.endswith("Z"):
            raise ValueError("Timestamp khong o dang UTC")

        print(f"\n=== SAMPLE {i} ===")
        print(f"Event ID: {row['event_id']}")
        print(f"Ground truth: {row['ground_truth_label']}")
        print(f"Predicted: {predicted_label}")
        print(f"Confidence: {confidence:.4f}")
        print(f"Processed at: {processed_at}")

    print("\nPASS: Batch Parquet -> Shared ML Inference")

finally:
    spark.stop()
