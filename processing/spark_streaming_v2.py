
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

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
ES_INDEX = "social_events_v1"

# ==========================================
# 2. KHOI TAO SPARK
# ==========================================

spark = (
    SparkSession.builder
    .appName("SocialEventsStreamingV2")
    .master("local[*]")
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
# 6. XU LY TUNG MICRO-BATCH
# ==========================================

def save_to_elasticsearch(batch_df, batch_id):

    lines = []
    total = 0

    processed_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    for row in batch_df.toLocalIterator():

        document = row.asDict(recursive=True)

        # Thoi diem Spark xu ly batch
        document["processed_at"] = processed_at

        # ID on dinh, tranh trung khi retry
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

        total += 1

        # Moi 250 documents gui mot bulk request
        if len(lines) >= 500:
            send_bulk(lines)
            lines.clear()

    send_bulk(lines)

    print(
        f"Batch {batch_id}: "
        f"da ghi {total} su kien vao {ES_INDEX}"
    )


# ==========================================
# 7. CHECKPOINT
# ==========================================

checkpoint_path = (
    Path(__file__).resolve().parents[1]
    / "checkpoints"
    / "social_events_v1"
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
