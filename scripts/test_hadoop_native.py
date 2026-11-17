
from pyspark.sql import SparkSession

def main():
    spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("Test_Hadoop_Native")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    try:
        jvm = spark.sparkContext._jvm

        print("\n========== LOAD HADOOP DLL ==========")
        jvm.java.lang.System.loadLibrary("hadoop")
        print("HADOOP DLL LOAD: PASS")

        print("\n========== TEST NATIVEIO ==========")
        native_io = jvm.org.apache.hadoop.io.nativeio.NativeIO.Windows
        access_right = native_io.AccessRight.ACCESS_READ

        result = native_io.access(
            r"C:\hadoop\bin\winutils.exe",
            access_right
        )

        print("NATIVEIO ACCESS:", result)
        print("NATIVEIO TEST: PASS")

    finally:
        spark.stop()

if __name__ == "__main__":
    main()
