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
from typing import Text

from ai_flow.ai_graph.ai_graph import AISubGraph
from ai_flow.plugin_interface.job_plugin_interface import AbstractJobPlugin, \
    register_job_plugin, get_registered_job_plugins, JobHandler, JobExecutionContext
from ai_flow.workflow.job import Job


class MockJobPlugin1(AbstractJobPlugin):

    def job_type(self) -> Text:
        return "mock1"

    def generate(self, sub_graph: AISubGraph) -> Job:
        pass

    def submit_job(self, job: Job, job_context: JobExecutionContext) -> JobHandler:
        pass

    def stop_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass

    def cleanup_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass


class MockJobPlugin2(AbstractJobPlugin):

    def job_type(self) -> Text:
        return "mock2"

    def generate(self, sub_graph: AISubGraph) -> Job:
        pass

    def submit_job(self, job: Job, job_context: JobExecutionContext) -> JobHandler:
        pass

    def stop_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass

    def cleanup_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass


class TestJobPlugin(unittest.TestCase):

    def test_job_plugin(self):
        register_job_plugin(MockJobPlugin1())
        register_job_plugin(MockJobPlugin2())
        self.assertEqual(2, len(get_registered_job_plugins()))
        self.assertTrue('mock1' in get_registered_job_plugins())
        self.assertTrue('mock2' in get_registered_job_plugins())


if __name__ == '__main__':
    unittest.main()
