# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from abc import abstractmethod

from pyflink.dataset import ExecutionEnvironment
from pyflink.table import TableConfig, BatchTableEnvironment, StreamTableEnvironment, TableEnvironment, StatementSet


class AbstractFlinkEnv(object):
    @abstractmethod
    def create_env(self) -> (ExecutionEnvironment, TableEnvironment, StatementSet):
        pass


class FlinkBatchEnv(AbstractFlinkEnv):

    def create_env(self) -> (ExecutionEnvironment, TableEnvironment, StatementSet):
        exec_env = ExecutionEnvironment.get_execution_environment()
        exec_env.set_parallelism(1)
        t_config = TableConfig()
        t_env = BatchTableEnvironment.create(exec_env, t_config)
        t_env.get_config().get_configuration().set_string("taskmanager.memory.task.off-heap.size", '80m')
        statement_set = t_env.create_statement_set()
        return exec_env, t_env, statement_set


class FlinkStreamEnv(AbstractFlinkEnv):

    def create_env(self) -> (ExecutionEnvironment, TableEnvironment, StatementSet):
        exec_env = ExecutionEnvironment.get_execution_environment()
        exec_env.set_parallelism(1)
        t_config = TableConfig()
        t_env = StreamTableEnvironment.create(exec_env, t_config)
        t_env.get_config().get_configuration().set_string("taskmanager.memory.task.off-heap.size", '80m')
        statement_set = t_env.create_statement_set()
        return exec_env, t_env, statement_set


__flink_env__: AbstractFlinkEnv = FlinkBatchEnv()


def set_flink_env(env: AbstractFlinkEnv):
    __flink_env__ = env


def get_flink_env() -> AbstractFlinkEnv:
    return __flink_env__
