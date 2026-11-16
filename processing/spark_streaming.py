
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

# 1. Cau hinh Hadoop cho Windows neu co san
hadoop_home = Path(r"C:\hadoop")

if hadoop_home.exists():
    os.environ["HADOOP_HOME"] = str(hadoop_home)
    os.environ["PATH"] = (
        str(hadoop_home / "bin")
        + os.pathsep
        + os.environ.get("PATH", "")
    )

# 2. Chi nap Kafka Connector
# Khong su dung Elasticsearch Spark Connector cu
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
    IntegerType,
    StringType
)

# 3. Khoi tao Spark
spark = (
    SparkSession.builder
    .appName("SentimentAnalysisStreaming")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# 4. Dinh nghia schema du lieu
schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("text", StringType(), True),
    StructField("platform", StringType(), True)
])

# 5. Doc luong du lieu tu Kafka
kafka_df = (
    spark.readStream
    .format("kafka")
    .option(
        "kafka.bootstrap.servers",
        "localhost:9092"
    )
    .option("subscribe", "raw_text_data")
    .option("startingOffsets", "earliest")
    .load()
)

# 6. Chuyen JSON thanh du lieu co cau truc
parsed_df = (
    kafka_df
    .select(
        "topic",
        "partition",
        "offset",
        from_json(
            col("value").cast("string"),
            schema
        ).alias("data")
    )
    .select(
        "topic",
        "partition",
        "offset",
        "data.*"
    )
    .filter(
        col("id").isNotNull()
        & col("text").isNotNull()
    )
)

# 7. Gui du lieu bang Elasticsearch Bulk API
def send_bulk(lines):
    if not lines:
        return

    payload = "".join(lines).encode("utf-8")

    request = Request(
        "http://localhost:9200/_bulk",
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
            f"Elasticsearch bulk loi: {failures[:3]}"
        )


# 8. Xu ly va luu tung micro-batch
def save_to_elasticsearch(batch_df, batch_id):
    lines = []
    total = 0

    for row in batch_df.toLocalIterator():

        # ID on dinh theo vi tri ban ghi Kafka
        doc_id = (
            f"{row['topic']}-"
            f"{row['partition']}-"
            f"{row['offset']}"
        )

        document = {
            "id": row["id"],
            "text": row["text"],
            "platform": row["platform"],
            "kafka_topic": row["topic"],
            "kafka_partition": row["partition"],
            "kafka_offset": row["offset"]
        }

        lines.append(
            json.dumps({
                "index": {
                    "_index": "sentiment_data",
                    "_id": doc_id
                }
            }) + "\n"
        )

        lines.append(
            json.dumps(
                document,
                ensure_ascii=False
            ) + "\n"
        )

        total += 1

        # Gui 250 documents moi lan
        if total % 250 == 0:
            send_bulk(lines)
            lines.clear()

    send_bulk(lines)

    print(
        f"Batch {batch_id}: "
        f"da ghi {total} ban ghi vao Elasticsearch"
    )


# 9. Tao checkpoint moi
checkpoint_path = (
    Path(__file__).resolve().parents[1]
    / "checkpoints"
    / "sentiment_http_v1"
)

checkpoint_path.mkdir(
    parents=True,
    exist_ok=True
)

# 10. Khoi dong Streaming
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
    "Dang nhan Kafka va ghi Elasticsearch "
    "qua Bulk API..."
)

query.awaitTermination()
