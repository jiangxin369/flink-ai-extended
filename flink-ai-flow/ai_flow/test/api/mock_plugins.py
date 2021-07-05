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
from typing import Text

from ai_flow.ai_graph.ai_graph import AISubGraph
from ai_flow.plugin_interface.job_plugin_interface import AbstractJobPlugin, register_job_plugin, JobHandler, \
    JobExecutionContext
from ai_flow.workflow.job import Job
from ai_flow.plugin_interface.blob_manager_interface import BlobManager


class MockBlobManger(BlobManager):
    def __init__(self, config):
        super().__init__(config)

    def upload_blob(self, workflow_id: Text, prj_pkg_path: Text) -> Text:
        return prj_pkg_path

    def download_blob(self, workflow_id, remote_path: Text, local_path: Text = None) -> Text:
        return remote_path


class MockJob(AbstractJobPlugin):

    def job_type(self) -> Text:
        return 'mock'

    def generate(self, sub_graph: AISubGraph) -> Job:
        return Job(job_config=sub_graph.config)

    def submit_job(self, job: Job, job_context: JobExecutionContext) -> JobHandler:
        pass

    def stop_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass

    def cleanup_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass


register_job_plugin(MockJob())
