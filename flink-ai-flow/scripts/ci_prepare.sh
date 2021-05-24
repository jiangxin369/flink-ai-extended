#!/usr/bin/env bash
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
set -e

port=$1
user=$2
password=$3

export AIRFLOW_HOME=~/airflow
MYSQL_CONN="mysql://${user}:${password}@127.0.0.1:${port}/airflow"

mysql --host 127.0.0.1 --port $1 -uroot -ppassword -e "ALTER DATABASE airflow CHARACTER SET UTF8mb3 COLLATE utf8_general_ci;"
mysql --host 127.0.0.1 --port $1 -uroot -ppassword -e "show variables;"

# prepare airflow configs and tables in mysql
mkdir ${AIRFLOW_HOME} >/dev/null 2>&1
cd ${AIRFLOW_HOME}
airflow db init >/dev/null 2>&1 || true
mv airflow.cfg airflow.cfg.tmpl
awk "{gsub(\"sql_alchemy_conn = sqlite:///${AIRFLOW_HOME}/airflow.db\", \"sql_alchemy_conn = ${MYSQL_CONN}\"); \
      gsub(\"load_examples = True\", \"load_examples = False\"); \
      gsub(\"load_default_connections = True\", \"load_default_connections = False\"); \
      gsub(\"dag_dir_list_interval = 300\", \"dag_dir_list_interval = 3\"); \
      gsub(\"executor = SequentialExecutor\", \"executor = LocalExecutor\"); \
      gsub(\"dags_are_paused_at_creation = True\", \"dags_are_paused_at_creation = False\"); \
      gsub(\"# mp_start_method =\", \"mp_start_method = forkserver\"); \
      gsub(\"execute_tasks_new_python_interpreter = False\", \"execute_tasks_new_python_interpreter = True\"); \
      gsub(\"min_serialized_dag_update_interval = 30\", \"min_serialized_dag_update_interval = 0\"); \
      print \$0}" airflow.cfg.tmpl > airflow.cfg
rm airflow.cfg.tmpl >/dev/null 2>&1

# prepare the database
airflow db reset -y

# create default admin user for airflow
airflow users create \
    --username admin \
    --password admin \
    --firstname admin \
    --lastname admin \
    --role Admin \
    --email admin@example.org

# start a local Flink cluster
cd /tmp
wget https://mirrors.bfsu.edu.cn/apache/flink/flink-1.13.0/flink-1.13.0-bin-scala_2.11.tgz
chmod 755 flink-1.13.0-bin-scala_2.11.tgz
tar -xzvf flink-1.13.0-bin-scala_2.11.tgz

FLINK_HOME=/tmp/flink-1.13.0
${FLINK_HOME}/bin/start-cluster.sh
