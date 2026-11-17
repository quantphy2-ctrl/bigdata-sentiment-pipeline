import json
import urllib.request
import urllib.error
from datetime import date, datetime

from pyspark.sql import SparkSession


ES_URL = "http://localhost:9200"
BATCH_SIZE = 100

TABLES = {
    "sentiment_by_dataset": {
        "path": "data/processed/analytics_day4/sentiment_by_dataset",
        "index": "sentiment-by-dataset",
        "expected": 8,
    },
    "daily_volume": {
        "path": "data/processed/analytics_day4/daily_volume",
        "index": "daily-volume",
        "expected": 72,
    },
    "daily_sentiment": {
        "path": "data/processed/analytics_day4/daily_sentiment",
        "index": "daily-sentiment",
        "expected": 157,
    },
}

MAPPINGS = {
    "sentiment-by-dataset": {
        "properties": {
            "sentiment_label": {"type": "keyword"},
            "record_count": {"type": "long"},
            "dataset_total": {"type": "long"},
            "percentage": {"type": "double"},
            "source_dataset": {"type": "keyword"},
        }
    },
    "daily-volume": {
        "properties": {
            "event_date": {"type": "date", "format": "strict_date"},
            "record_count": {"type": "long"},
            "source_dataset": {"type": "keyword"},
        }
    },
    "daily-sentiment": {
        "properties": {
            "event_date": {"type": "date", "format": "strict_date"},
            "sentiment_label": {"type": "keyword"},
            "record_count": {"type": "long"},
            "source_dataset": {"type": "keyword"},
        }
    },
}


def es_request(method, path, payload=None, content_type="application/json"):
    url = ES_URL + path

    data = None
    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        headers["Content-Type"] = content_type

        if content_type == "application/x-ndjson":
            data = payload.encode("utf-8")
        else:
            data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Elasticsearch HTTP {exc.code}: {body}"
        ) from exc


def ensure_index(index_name):
    try:
        es_request("GET", f"/{index_name}")
        print(f"INDEX EXISTS: {index_name} - KEEPING EXISTING INDEX")
        return
    except RuntimeError as exc:
        if "HTTP 404" not in str(exc):
            raise

    es_request(
        "PUT",
        f"/{index_name}",
        {"mappings": MAPPINGS[index_name]},
    )
    print(f"INDEX CREATED: {index_name}")


def make_document_id(table_name, row):
    if table_name == "sentiment_by_dataset":
        return f"{row['source_dataset']}|{row['sentiment_label']}"

    event_date = str(row["event_date"])

    if table_name == "daily_volume":
        return f"{row['source_dataset']}|{event_date}"

    return (
        f"{row['source_dataset']}|"
        f"{event_date}|{row['sentiment_label']}"
    )


def normalize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def bulk_send(index_name, documents):
    if not documents:
        return 0

    lines = []

    for document_id, source in documents:
        action = {
            "index": {
                "_index": index_name,
                "_id": document_id,
            }
        }

        lines.append(json.dumps(action, ensure_ascii=False))
        lines.append(json.dumps(source, ensure_ascii=False))

    payload = "\n".join(lines) + "\n"

    _, result = es_request(
        "POST",
        "/_bulk",
        payload,
        content_type="application/x-ndjson",
    )

    if result.get("errors"):
        failures = [
            item for item in result.get("items", [])
            if item.get("index", {}).get("error")
        ]
        raise RuntimeError(
            f"Bulk indexing errors: {json.dumps(failures[:3], ensure_ascii=False)}"
        )

    return len(documents)


def main():
    print("=" * 65)
    print("DAY 5: ELASTICSEARCH ANALYTICS LOADER")
    print("=" * 65)

    # Check Elasticsearch first
    _, health = es_request("GET", "/_cluster/health")
    print("ELASTICSEARCH STATUS:", health["status"])

    spark = (
        SparkSession.builder
        .appName("Day5AnalyticsToElasticsearch")
        .master("local[1]")
        .config("spark.driver.memory", "1g")
        .getOrCreate()
    )

    total_uploaded = 0

    try:
        for table_name, config in TABLES.items():
            index_name = config["index"]

            print("\n" + "=" * 65)
            print("TABLE:", table_name)
            print("INDEX:", index_name)

            ensure_index(index_name)

            df = spark.read.parquet(config["path"])
            actual_rows = df.count()

            print("PARQUET ROWS:", actual_rows)

            if actual_rows != config["expected"]:
                raise RuntimeError(
                    f"Expected {config['expected']} rows, got {actual_rows}"
                )

            batch = []
            uploaded = 0

            for row in df.toLocalIterator():
                source = {
                    key: normalize_value(value)
                    for key, value in row.asDict().items()
                }

                document_id = make_document_id(table_name, source)

                batch.append((document_id, source))

                if len(batch) >= BATCH_SIZE:
                    uploaded += bulk_send(index_name, batch)
                    batch.clear()
                    print("UPLOADED:", uploaded)

            if batch:
                uploaded += bulk_send(index_name, batch)
                batch.clear()

            # Make newly indexed documents visible to search/count.
            es_request("POST", f"/{index_name}/_refresh")

            _, count_result = es_request(
                "GET",
                f"/{index_name}/_count",
            )

            es_count = count_result["count"]

            print("UPLOADED THIS RUN:", uploaded)
            print("ELASTICSEARCH DOCUMENTS:", es_count)

            if es_count != config["expected"]:
                raise RuntimeError(
                    f"{index_name}: expected {config['expected']} documents, "
                    f"found {es_count}"
                )

            total_uploaded += uploaded
            print("TABLE STATUS: PASS")

        print("\n" + "=" * 65)
        print("TOTAL DOCUMENTS SENT:", total_uploaded)
        print("DAY 5 ELASTICSEARCH LOAD: PASS")
        print("=" * 65)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

