import os
os.environ['HADOOP_HOME'] = 'C:\\hadoop'
os.environ['PATH'] = 'C:\\hadoop\\bin;' + os.environ.get('PATH', '')
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 pyspark-shell'

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# 1. Khởi tạo Spark Session
spark = SparkSession.builder \
    .appName("SentimentAnalysisStreaming") \
    .master("local[*]") \
    .getOrCreate()

# Giảm bớt log hệ thống để dễ nhìn dữ liệu
spark.sparkContext.setLogLevel("WARN")

print("Đang lắng nghe dữ liệu từ Kafka topic 'raw_text_data'...")

# 2. Đọc luồng dữ liệu liên tục từ Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "raw_text_data") \
    .option("startingOffsets", "earliest") \
    .load()

# 3. Tiền xử lý dữ liệu (Chuyển dạng Binary của Kafka về dạng JSON và tách cột)
# Định nghĩa khung dữ liệu (Schema) 
schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("text", StringType(), True),
    StructField("platform", StringType(), True)
])

# Chuyển đổi dữ liệu
json_df = df.selectExpr("CAST(value AS STRING) as json_string")
parsed_df = json_df.withColumn("data", from_json(col("json_string"), schema)).select("data.*")

# 4. In trực tiếp dữ liệu đang chảy ra màn hình Terminal
query = parsed_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()