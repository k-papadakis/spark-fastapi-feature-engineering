
FROM ubuntu:focal AS base

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y ssh pdsh openjdk-8-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

# ADD https://dlcdn.apache.org/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz /opt/
ADD ./hadoop-3.3.4.tar.gz /opt/
ENV HADOOP_HOME=/opt/hadoop-3.3.4
ENV HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
ENV YARN_CONF_DIR=${HADOOP_CONF_DIR}
ENV HADOOP_MAPRED_HOME=/opt/hadoop-3.3.4
COPY hadoop-env.sh hdfs-site.xml core-site.xml mapred-site.xml yarn-site.xml workers ${HADOOP_HOME}/etc/hadoop/

# https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html#Setup_passphraseless_ssh
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa \
  && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys \
  && chmod 0600 ~/.ssh/authorized_keys


FROM base AS namenode
RUN ${HADOOP_HOME}/bin/hdfs namenode -format
CMD service ssh restart && ${HADOOP_HOME}/bin/hdfs namenode

FROM base AS datanode
CMD service ssh restart && ${HADOOP_HOME}/bin/hdfs datanode

FROM base AS resourcemanager
# ADD https://dlcdn.apache.org/spark/spark-3.3.1/spark-3.3.1-bin-hadoop3.tgz /opt/
ADD spark-3.3.1-bin-hadoop3.tgz /opt/
ENV SPARK_HOME=/opt/spark-3.3.1-bin-hadoop3
CMD service ssh restart && ${HADOOP_HOME}/bin/yarn resourcemanager

FROM base AS nodemanager
CMD service ssh restart && ${HADOOP_HOME}/bin/yarn nodemanager

FROM base AS proxyserver
CMD service ssh restart && ${HADOOP_HOME}/bin/yarn proxyserver

FROM base AS historyserver
CMD service ssh restart && ${HADOOP_HOME}/bin/mapred historyserver
