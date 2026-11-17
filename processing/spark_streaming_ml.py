
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from sentiment_inference import (
    predict_sentiments,
    MODEL_VERSION
)

# ==========================================
# 1. CAU HINH MOI TRUONG
# ==========================================

HADOOP_HOME = Path(r"C:\hadoop")

if HADOOP_HOME.exists():
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["PATH"] = (
        str(HADOOP_HOME / "bin")
        + os.pathsep
        + os.environ.get("PATH", "")
    )

# Chi su dung Kafka Connector
# Elasticsearch su dung Bulk API
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--packages "
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 "
    "pyspark-shell"
)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType
)

KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "social_events_v1"

ES_URL = "http://localhost:9200"
ES_INDEX = "social_events_ml_v1"

# ==========================================
# 2. KHOI TAO SPARK
# ==========================================

spark = (
    SparkSession.builder
    .appName("SocialEventsStreamingMLV1")
    .master("local[2]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ==========================================
# 3. SCHEMA V1.0
# ==========================================

engagement_schema = StructType([
    StructField("likes", LongType(), True),
    StructField("replies", LongType(), True),
    StructField("shares", LongType(), True)
])

event_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("platform", StringType(), True),
    StructField("content_type", StringType(), True),
    StructField("text", StringType(), True),
    StructField("language", StringType(), True),
    StructField("created_at", StringType(), True),
    StructField("collected_at", StringType(), True),
    StructField(
        "engagement",
        engagement_schema,
        True
    )
])

# ==========================================
# 4. DOC DU LIEU KAFKA
# ==========================================

kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_SERVER)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

parsed_df = (
    kafka_df
    .selectExpr(
        "CAST(value AS STRING) AS raw_json",
        "topic AS kafka_topic",
        "partition AS kafka_partition",
        "offset AS kafka_offset"
    )
    .withColumn(
        "event",
        from_json(col("raw_json"), event_schema)
    )
    .select(
        "event.*",
        "kafka_topic",
        "kafka_partition",
        "kafka_offset"
    )
    .filter(
        col("event_id").isNotNull()
        & col("platform").isNotNull()
        & col("text").isNotNull()
    )
)

# ==========================================
# 5. ELASTICSEARCH BULK API
# ==========================================

def send_bulk(lines):
    if not lines:
        return

    payload = "".join(lines).encode("utf-8")

    request = Request(
        f"{ES_URL}/_bulk",
        data=payload,
        headers={
            "Content-Type": "application/x-ndjson"
        },
        method="POST"
    )

    with urlopen(request, timeout=30) as response:
        result = json.load(response)

    if result.get("errors"):
        failures = [
            details.get("error")
            for item in result.get("items", [])
            for details in item.values()
            if details.get("error")
        ]

        raise RuntimeError(
            f"Bulk indexing failed: {failures[:3]}"
        )



# ==========================================
# 6. XU LY MICRO-BATCH + MACHINE LEARNING
# ==========================================

def save_to_elasticsearch(batch_df, batch_id):

    total = 0
    skipped = 0
    buffer = []

    # Du doan nhieu tweet cung luc,
    # sau do gui Elasticsearch Bulk API.
    def flush_buffer():
        nonlocal total

        if not buffer:
            return

        # 1. Lay text de du doan
        texts = [
            document["text"]
            for document in buffer
        ]

        # 2. Goi model chung
        predictions = predict_sentiments(texts)

        if len(predictions) != len(buffer):
            raise RuntimeError(
                "So du doan khong khop so ban ghi"
            )

        # 3. Them ket qua ML vao document
        lines = []

        for document, prediction in zip(
            buffer,
            predictions
        ):
            document.update(prediction)

            # Dung event_id lam Elasticsearch _id
            # de tranh ghi trung khi Spark retry.
            document_id = str(document["event_id"])

            action = {
                "index": {
                    "_index": ES_INDEX,
                    "_id": document_id
                }
            }

            lines.append(
                json.dumps(action) + "\n"
            )

            lines.append(
                json.dumps(
                    document,
                    ensure_ascii=False
                ) + "\n"
            )

        # 4. Gui du lieu da du doan vao ES
        send_bulk(lines)

        total += len(buffer)
        buffer.clear()

    # 5. Doc cac su kien trong micro-batch
    for row in batch_df.toLocalIterator():

        document = row.asDict(recursive=True)

        event_id = document.get("event_id")
        text = document.get("text")

        # Khong gui ban ghi thieu ID/text
        # sang module Machine Learning.
        if (
            not event_id
            or not isinstance(text, str)
            or not text.strip()
        ):
            skipped += 1
            continue

        buffer.append(document)

        # Du doan va gui 250 documents moi lan
        if len(buffer) >= 250:
            flush_buffer()

    # Xu ly nhung ban ghi con lai
    flush_buffer()

    print(
        f"Batch {batch_id}: "
        f"da ghi {total} su kien vao {ES_INDEX} "
        f"| skipped={skipped} "
        f"| model={MODEL_VERSION}"
    )


# ==========================================
# 7. CHECKPOINT
# ==========================================

checkpoint_path = (
    Path(__file__).resolve().parents[1]
    / "checkpoints"
    / "social_events_ml_v1"
)

checkpoint_path.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================
# 8. KHOI DONG STREAMING
# ==========================================

query = (
    parsed_df.writeStream
    .foreachBatch(save_to_elasticsearch)
    .option(
        "checkpointLocation",
        checkpoint_path.as_uri()
    )
    .trigger(processingTime="5 seconds")
    .start()
)

print(
    "Spark Streaming v2 dang hoat dong..."
)

print(
    f"Kafka: {KAFKA_TOPIC}"
)

print(
    f"Elasticsearch: {ES_INDEX}"
)

query.awaitTermination()
