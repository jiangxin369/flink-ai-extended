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
import time
import logging
from typing import Text

from ai_flow.translator.translator import JobGenerator
from ai_flow.ai_graph.ai_graph import AISubGraph
from ai_flow.plugin_interface.job_plugin_interface import AbstractJobPluginFactory, JobHandler, JobRuntimeEnv, \
    JobController
from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo
from ai_flow.workflow.job import Job


class BaichuanJob(Job):
    def __init__(self, job_config):
        super().__init__(job_config)

    def baichuan_job_id(self):
        return self.job_config.properties.get('job_id')


class BaichuanHandler(JobHandler):

    def __init__(self, job: BaichuanJob,
                 job_execution: JobExecutionInfo):
        super().__init__(job=job, job_execution=job_execution)
        self.job = job
        self.stopped = False
        self.query_cnt = 0

    def get_result(self) -> object:
        return str(self.job.baichuan_job_id()) + " is finished"

    def wait_until_finish(self):
        while True:
            if self.is_finished():
                break
            time.sleep(1)

    def is_finished(self) -> bool:
        # query baichuan
        logging.info("Checking if %s is finished", self.job.baichuan_job_id())
        self.query_cnt += 1
        if self.query_cnt > 100 or self.stopped:
            return True
        return False

    def stop_job(self):
        self.stopped = True


class BaichuanJobPluginFactory(AbstractJobPluginFactory, JobGenerator, JobController):

    def __init__(self) \
            -> None:
        super().__init__()

    def generate(self, sub_graph: AISubGraph, resource_dir: Text = None) -> Job:
        job = BaichuanJob(job_config=sub_graph.config)
        return job

    def submit_job(self, job: BaichuanJob, job_runtime_env: JobRuntimeEnv) -> JobHandler:
        handler = BaichuanHandler(job=job, job_execution=job_runtime_env.job_execution_info)
        return handler

    def stop_job(self, job_handler: BaichuanHandler, job_runtime_env: JobRuntimeEnv = None):
        job_handler.stop_job()

    def cleanup_job(self, job_handler: JobHandler, job_runtime_env: JobRuntimeEnv = None):
        pass

    def get_job_generator(self) -> JobGenerator:
        return self

    def get_job_controller(self) -> JobController:
        return self

    def job_type(self) -> Text:
        return "baichuan"
