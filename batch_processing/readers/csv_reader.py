
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


AIRLINE_PATH = "data/raw/Tweets.csv"

SENTIMENT140_TRAIN_PATH = (
    "data/raw/sentiment140/"
    "training.1600000.processed.noemoticon.csv"
)

SENTIMENT140_TEST_PATH = (
    "data/raw/sentiment140/"
    "testdata.manual.2009.06.14.csv"
)

SENTIMENT140_COLUMNS = [
    "source_label",
    "source_id",
    "source_timestamp",
    "source_query_or_flag",
    "source_user",
    "text",
]



def read_airline(spark: SparkSession) -> DataFrame:
    df = (
        spark.read.format("csv")
        .option("header", "true")
        .option("encoding", "windows-1252")
        .option("mode", "PERMISSIVE")
        .option("quote", '"')
        .option("escape", '"')
        .option("multiLine", "true")
        .load(AIRLINE_PATH)
    )

    return (
        df.withColumnRenamed("tweet_id", "source_id")
          .withColumnRenamed("airline_sentiment", "source_label")
          .withColumnRenamed("tweet_created", "source_timestamp")
          .withColumn("source_dataset", F.lit("twitter_airline"))
    )

def read_sentiment140(
    spark: SparkSession,
    path: str,
    dataset_name: str
) -> DataFrame:
    """Read headerless Sentiment140 CSV."""

    df = (
        spark.read
        .format("csv")
        .option("header", "false")
        .option("encoding", "ISO-8859-1")
        .option("mode", "PERMISSIVE")
        .option("quote", '"')
        .option("escape", '"')
        .option("multiLine", "false")
        .load(path)
    )

    if len(df.columns) != 6:
        raise ValueError(
            f"{dataset_name}: Expected 6 columns, "
            f"found {len(df.columns)}"
        )

    df = df.toDF(*SENTIMENT140_COLUMNS)

    return df.withColumn(
        "source_dataset",
        F.lit(dataset_name)
    )


def read_all_datasets(spark: SparkSession):
    """Read all three historical datasets."""

    airline = read_airline(spark)

    sentiment_train = read_sentiment140(
        spark,
        SENTIMENT140_TRAIN_PATH,
        "sentiment140_train"
    )

    sentiment_test = read_sentiment140(
        spark,
        SENTIMENT140_TEST_PATH,
        "sentiment140_test"
    )

    return {
        "airline": airline,
        "sentiment140_train": sentiment_train,
        "sentiment140_test": sentiment_test,
    }
