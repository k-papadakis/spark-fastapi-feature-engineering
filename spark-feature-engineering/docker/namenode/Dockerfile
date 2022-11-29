
FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y ssh pdsh openjdk-8-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD ./hadoop-3.3.4.tar.gz /opt/
# Alternatively: ADD https://dlcdn.apache.org/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz /opt/
# TODO: WORKDIR somewhere else after finishing
WORKDIR /opt/hadoop-3.3.4
COPY hadoop-env.sh hdfs-site.xml etc/hadoop/

# TODO: Move this to docker-compose
# Default namenode adress is 0.0.0.0:9870
# See https://hadoop.apache.org/docs/r3.3.4/hadoop-project-dist/hadoop-hdfs/hdfs-default.xml
# EXPOSE 9870 22

# https://www.guru99.com/how-to-install-hadoop.html
# Unsafe! Not using passphrases!
RUN ssh-keygen -t rsa -P "" -f $HOME/.ssh/id_rsa.pub \
    && cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys

RUN bin/hdfs namenode -format

# Restarting ssh after formatting the namenode, because otherwise it doesn't work for some reason...
RUN service ssh restart && sbin/start-dfs.sh

CMD ["bin/hdfs", "namenode"]
