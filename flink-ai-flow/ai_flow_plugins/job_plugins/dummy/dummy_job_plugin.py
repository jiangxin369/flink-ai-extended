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
from abc import ABC
from typing import Text, Any

from ai_flow.ai_graph.ai_graph import AISubGraph
from ai_flow.plugin_interface.job_plugin_interface import AbstractJobPlugin, JobHandler, JobExecutionContext
from ai_flow.project.project_description import ProjectDesc
from ai_flow.workflow.job import Job


class DummyJobPlugin(AbstractJobPlugin, ABC):

    def __init__(self) -> None:
        super().__init__()

    def generate(self, sub_graph: AISubGraph) -> Job:
        job = Job(job_config=sub_graph.config)
        return job

    def submit_job(self, job: Job, job_context: JobExecutionContext) -> JobHandler:
        return JobHandler(job=job, job_execution=job_context.job_execution_info)

    def stop_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass

    def cleanup_job(self, job_handler: JobHandler, job_context: JobExecutionContext):
        pass

    def job_type(self) -> Text:
        return "dummy"

