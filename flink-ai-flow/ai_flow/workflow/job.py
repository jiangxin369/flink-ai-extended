#
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
#
from typing import Text
from ai_flow.graph.node import BaseNode
from ai_flow.workflow.job_config import JobConfig


class Job(BaseNode):
    """
    A Job contains the common information of a ai flow job. Users can implement custom jobs by adding other
    execution information for a specific job_type.
    """
    def __init__(self,
                 job_config: JobConfig) -> None:
        """
        :param job_config: Job configuration information, including job name, running environment, etc.
        """
        super().__init__()
        self.job_config = job_config
        self._project_uri: Text = None  # project code uri
        self._resource_dir: Text = None  # job resource dir

    @property
    def job_name(self):
        return self.job_config.job_name

    @property
    def resource_dir(self):
        return self._resource_dir

    @resource_dir.setter
    def resource_dir(self, value):
        self._resource_dir = value

    @property
    def project_uri(self):
        return self._project_uri

    @project_uri.setter
    def project_uri(self, value):
        self._project_uri = value
