# Feature Engineering with Spark

This project's goal is to set up a Hadoop cluster using docker, and engineer features by using Spark.

The [data](./data/cvas_data.csv) is comprised of loans that customers have taken. We produces new features for each customer by performing aggregations on their loan data.

The PySpark script to generate the features is [generate_customer_features.py](./generate_customer_features.py).

The shell script [generate_customer_features.sh](./generate_customer_features.sh) initializes the cluster with docker-compose, uploads the data to the HDFS, submits the job, and downloads the results locally inside the [data](./data/) directory in parquet format.
