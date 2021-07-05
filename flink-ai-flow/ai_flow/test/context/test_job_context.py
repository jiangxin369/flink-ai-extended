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
import unittest
from ai_flow.workflow.workflow_config import WorkflowConfig
from ai_flow.workflow.job_config import JobConfig
from ai_flow.context.job_context import job_config, current_job_name
from ai_flow.context.workflow_context import __default_workflow_context__


class TestJobContext(unittest.TestCase):

    def test_job_context(self):
        workflow_config_ = WorkflowConfig()
        workflow_config_.job_configs['job_1'] = JobConfig(job_name='job_1')
        __default_workflow_context__.workflow_config = workflow_config_
        with job_config('job_1') as jc:
            self.assertEqual(jc.job_name, current_job_name())


if __name__ == '__main__':
    unittest.main()
