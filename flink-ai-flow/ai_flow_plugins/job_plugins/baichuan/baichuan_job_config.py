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
from typing import Dict, Text

from ai_flow import Jsonable
from ai_flow.workflow.job_config import JobConfig


class BaichuanJobConfig(JobConfig):
    def __init__(self, job_name: Text = None,
                 properties: Dict[Text, Jsonable] = None) -> None:
        super().__init__(job_name, 'baichuan', properties)

    @property
    def baichuan_job_id(self):
        return self.properties.get('job_id')

    def baichuan_base_url(self):
        return self.properties.get('baichuan_base_url')
