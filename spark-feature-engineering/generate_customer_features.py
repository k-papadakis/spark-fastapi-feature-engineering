from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, DateType, DecimalType, ShortType, StructField, StructType
from pyspark.sql import functions as F

spark = SparkSession.builder.appName('customerFeatureEngineering').getOrCreate()

DATE_FORMAT = "d/M/y"
SCHEMA = StructType(
    [
        StructField("customer_ID", StringType(), False),
        StructField("loan_date", DateType(), True),
        StructField("amount", DecimalType(), True),
        StructField("fee", DecimalType(), True),
        StructField("loan_status", ShortType(), True),
        StructField("term", StringType(), True),
        StructField("annual_income", DecimalType(), True),
    ]
)

df = spark.read.csv("/input/cvas_data.csv", dateFormat=DATE_FORMAT, schema=SCHEMA, header=True)

aggs = df.groupBy("customer_ID").agg(
    F.count("loan_date").alias("count"),
    F.min("loan_date").alias("min_date"),
    F.max("loan_date").alias("max_date"),
    F.mean("loan_status").alias("default_ratio"),
    F.mean(F.col("term").eqNullSafe("long").cast("float")).alias("long_ratio"),
    F.min("fee").alias("min_fee"),
    F.max("fee").alias("max_fee"),
    F.mean("fee").alias("mean_fee"),
    # F.var_pop("fee").alias("var_fee"),
    F.min("amount").alias("min_amount"),
    F.max("amount").alias("max_amount"),
    F.mean("amount").alias("mean_amount"),
    # F.var_pop("amount").alias("var_amount"),
)

customer_features = (
    df.select(["customer_ID", "annual_income"]).dropDuplicates(["customer_ID"]).join(aggs, on="customer_ID")
)

customer_features.write.save('engineered_customer_features.parquet')
