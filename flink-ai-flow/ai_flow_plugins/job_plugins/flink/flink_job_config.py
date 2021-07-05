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
from typing import Dict, Text, Optional

from ai_flow import ExecutionMode, Jsonable
from ai_flow.workflow.job_config import JobConfig


class FlinkJobConfig(JobConfig):
    """
    |- job_name
        |-job_type: flink
        |-properties
            |-jm: the job manager uri (default None)
            |-language: python or java (default python)
            |-run_mode: local or cluster (default python)
    """
    def __init__(self, job_name: Text = None,
                 exec_mode: Optional[ExecutionMode] = ExecutionMode.BATCH,
                 properties: Dict[Text, Jsonable] = None) -> None:
        super().__init__(job_name, 'flink', exec_mode, properties)

    @property
    def env(self):
        return self.properties.get('env')

    @property
    def run_mode(self):
        if 'run_mode' in self.properties:
            return self.properties.get('run_mode')
        else:
            return 'local'

    @property
    def language(self):
        if 'language' in self.properties:
            return self.properties.get('language')
        else:
            return 'python'

    @property
    def parallelism(self):
        if 'parallelism' in self.properties:
            return str(self.properties.get('parallelism'))
        else:
            return '1'

    @property
    def jm(self):
        if 'jm' in self.properties:
            return self.properties.get('jm')
        else:
            return None

    @classmethod
    def from_job_config(cls, job_config: JobConfig)->'FlinkJobConfig':
        return FlinkJobConfig(job_name=job_config.job_name,
                              exec_mode=job_config.exec_mode,
                              properties=job_config.properties)
