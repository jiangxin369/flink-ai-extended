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
from typing import List, Dict
from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo
from ai_flow.util import json_utils


class ExecutionContext(json_utils.Jsonable):
    def __init__(self,
                 job_execution_info: JobExecutionInfo,
                 config: Dict):
        self._job_execution_info = job_execution_info
        self._config: Dict = config

    @property
    def job_execution_info(self)-> JobExecutionInfo:
        return self._job_execution_info

    @property
    def name(self):
        return self._config['name']

    @property
    def node_type(self):
        return self._config['node_type']

    @property
    def config(self)->Dict:
        return self._config


class PythonExecutor(object):

    def __init__(self) -> None:
        super().__init__()

    """
    Execute method for user-defined function. User write their code logic in this method.
    """

    @abstractmethod
    def execute(self, execution_context: ExecutionContext, input_list: List) -> List:
        pass

    """
    Setup method for user-defined function. It can be used for initialization work.
    By default, this method does nothing.
    """

    def setup(self, execution_context: ExecutionContext):
        pass

    """
    Tear-down method for user-defined function. It can be used for clean up work.
    By default, this method does nothing.
    """

    def close(self, execution_context: ExecutionContext):
        pass
