
from pyspark.sql import DataFrame
from pyspark.sql import functions as F



def normalize_timestamp(df: DataFrame) -> DataFrame:
    """
    Chuẩn hóa timestamp của Airline và Sentiment140 về UTC.
    """

    # Chuyển timezone viết tắt thành offset.
    normalized = F.regexp_replace(
        F.col("source_timestamp"), r"\bPDT\b", "-0700"
    )
    normalized = F.regexp_replace(
        normalized, r"\bPST\b", "-0800"
    )
    normalized = F.regexp_replace(
        normalized, r"\bUTC\b", "+0000"
    )
    normalized = F.regexp_replace(
        normalized, r"\bGMT\b", "+0000"
    )

    # Định dạng Airline:
    # 2015-02-24 11:35:52 -0800
    airline_timestamp = F.to_timestamp(
        normalized,
        "yyyy-MM-dd HH:mm:ss Z"
    )

    # Định dạng Sentiment140:
    # Mon Apr 06 22:19:45 -0700 2009
    # Bỏ tên thứ trong tuần trước khi parse.
    without_weekday = F.regexp_replace(
        normalized,
        r"^[A-Za-z]{3} ",
        ""
    )

    sentiment140_timestamp = F.to_timestamp(
        without_weekday,
        "MMM dd HH:mm:ss Z yyyy"
    )

    return df.withColumn(
        "created_at",
        F.coalesce(
            airline_timestamp,
            sentiment140_timestamp
        )
    )


def normalize_dataset(df: DataFrame) -> DataFrame:
    """
    Đưa một dataset về schema chung.
    """

    dataset_name = df.select("source_dataset").first()["source_dataset"]

    # Chuẩn hóa nhãn sentiment.
    if dataset_name == "twitter_airline":
        sentiment = (
            F.when(F.lower(F.col("source_label")) == "negative", "negative")
             .when(F.lower(F.col("source_label")) == "neutral", "neutral")
             .when(F.lower(F.col("source_label")) == "positive", "positive")
        )

    elif dataset_name in ("sentiment140_train", "sentiment140_test"):
        sentiment = (
            F.when(F.col("source_label") == "0", "negative")
             .when(F.col("source_label") == "2", "neutral")
             .when(F.col("source_label") == "4", "positive")
        )

    else:
        raise ValueError(
            f"Dataset không được hỗ trợ: {dataset_name}"
        )

    df = df.withColumn(
        "sentiment_label",
        sentiment
    )

    # Chuẩn hóa timestamp.
    df = normalize_timestamp(df)

    # Tạo engagement.
    if "retweet_count" in df.columns:
        shares = F.col("retweet_count").cast("long")
    else:
        shares = F.lit(None).cast("long")

    engagement = F.struct(
        F.lit(None).cast("long").alias("likes"),
        F.lit(None).cast("long").alias("replies"),
        shares.alias("shares")
    )

    df = df.withColumn(
        "engagement",
        engagement
    )

    # Tạo event_id ổn định bằng SHA-256.
    identity_data = F.to_json(
        F.struct(
            F.col("source_dataset"),
            F.col("source_id"),
            F.col("source_timestamp"),
            F.col("text"),
            F.col("source_label")
        )
    )

    df = df.withColumn(
        "event_id",
        F.sha2(identity_data, 256)
    )

    # Thời điểm chạy pipeline.
    df = df.withColumn(
        "collected_at",
        F.current_timestamp()
    )

    # Schema chung.
    result = df.select(
        "event_id",
        "source_id",
        "source_dataset",
        F.lit("twitter").alias("platform"),
        F.lit("tweet").alias("content_type"),
        F.col("text").cast("string").alias("text"),
        F.lit(None).cast("string").alias("language"),
        "sentiment_label",
        F.col("source_label").alias("source_label"),
        "created_at",
        "collected_at",
        "engagement"
    )

    return result
