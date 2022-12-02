#!/bin/bash

# Initialize a hadoop cluster with yarn, mapreduce and spark.
docker compose --file ./docker/docker-compose.yml build
docker compose --file ./docker/docker-compose.yml up --detach

# Upload the data and the feature-genererating script on the namenode.
docker cp ./generate_customer_features.py docker-namenode-1:/
docker cp ./data/cvas_data.csv docker-namenode-1:/

# Upload the data on the hdfs
docker exec docker-namenode-1 bash -c '$HADOOP_HOME/bin/hdfs dfs -mkdir /input'
docker exec docker-namenode-1 bash -c '$HADOOP_HOME/bin/hdfs dfs -put /cvas_data.csv /input/'

# Submit the feature-generating job
docker exec docker-namenode-1 bash -c '$SPARK_HOME/bin/spark-submit --master yarn --deploy-mode cluster /generate_customer_features.py'

# Download the results
docker exec docker-namenode-1 bash -c '$HADOOP_HOME/bin/hdfs dfs -get /user/root/csv_data.parquet'
docker cp docker-namenode-1:/csv_data.parquet ./data

# Stop and clean up the containers
docker compose --file ./docker/docker-compose.yml down
