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
from abc import abstractmethod, ABC
from typing import Text, Dict, List
import logging
from ai_flow.common.registry import BaseRegistry
from ai_flow.util.json_utils import Jsonable
from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo
from ai_flow.runtime.job_runtime_env import JobRuntimeEnv
from ai_flow.translator.translator import register_job_generator, JobGenerator
from ai_flow.workflow.job import Job


class JobHandler(Jsonable):
    """
    JobHandler is created by JobController. When call submit_job function, then return a JobHandler.
    Using JobHandler, you can get the job information.
    """
    def __init__(self,
                 job: Job,
                 job_execution: JobExecutionInfo) -> None:
        self._log = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        self.job: Job = job
        self.job_execution: JobExecutionInfo = job_execution

    def get_result(self) -> object:
        """If the job execution has a result, then return it."""
        pass

    def wait_until_finish(self):
        """Wait the job execution until it is finished"""
        while self.is_job_running():
            # TODO make it configurable
            time.sleep(5)

    def is_job_running(self):
        """Check if the job is still running."""
        pass

    def obtain_job_labels(self) -> Dict[str, str]:
        """Obtain job labels related to this job"""
        pass

    @property
    def log(self) -> logging.Logger:
        """Returns a logger."""
        return self._log


class JobController(ABC):
    """
    Used for control an executable job to specific platform when it's scheduled to run in workflow scheduler.
    The controller is able to control the lifecycle of a workflow job. Users can also implement custom job controller
    with their own job type.
    """

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

    @property
    def log(self) -> logging.Logger:
        """Returns a logger. This logger is used as a log for control jobs """
        return self._log

    @abstractmethod
    def submit_job(self, job: Job, job_runtime_env: JobRuntimeEnv) -> JobHandler:
        """
        submit an executable job to run.
        :param job_runtime_env: The job runtime environment. Type: ai_flow.runtime.job_runtime_env.JobRuntimeEnv
        :param job: A job object that contains the necessary information for an execution.
        :return job_handler: a job handler that maintain the handler of a job runtime.
        """
        pass

    @abstractmethod
    def stop_job(self, job_handler: JobHandler, job_runtime_env: JobRuntimeEnv):
        """
        Stop a ai flow job.
        :param job_runtime_env: The job runtime environment. Type: ai_flow.runtime.job_runtime_env.JobRuntimeEnv
        :param job_handler: The job handler that contains the necessary information for an execution.
        """
        pass

    @abstractmethod
    def cleanup_job(self, job_handler: JobHandler, job_runtime_env: JobRuntimeEnv):
        """
        clean up temporary resources created during this execution.
        :param job_runtime_env: The job runtime environment. Type: ai_flow.runtime.job_runtime_env.JobRuntimeEnv
        :param job_handler: The job handler that contains the necessary information for an execution.
        """
        pass


class JobControllerManager(BaseRegistry):
    def __init__(self) -> None:
        super().__init__()

    def submit_job(self, job: Job, job_runtime_env: JobRuntimeEnv) -> JobHandler:
        job_controller = self.get_job_controller(job)
        return job_controller.submit_job(job, job_runtime_env)

    def get_job_controller(self, job: Job) -> JobController:
        job_controller: JobController = self.get_object(job.job_config.job_type)
        if job_controller is None:
            raise Exception("job submitter not found! job_type {}".format(job.job_config.job_type))
        return job_controller

    def stop_job(self, job_handler: JobHandler, job_context: JobRuntimeEnv):
        job_controller = self.get_job_controller(job_handler.job)
        job_controller.stop_job(job_handler, job_context)

    def cleanup_job(self, job_handler: JobHandler, job_context: JobRuntimeEnv):
        job_controller = self.get_job_controller(job_handler.job)
        job_controller.cleanup_job(job_handler, job_context)


__job_controller_manager__ = JobControllerManager()


def register_job_controller(job_type: Text, job_controller: JobController):
    __job_controller_manager__.register(job_type, job_controller)


def get_job_controller_manager() -> JobControllerManager:
    return __job_controller_manager__


class AbstractJobPluginFactory(JobGenerator, JobController):

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def job_type(self) -> Text:
        """
        :return: The job type.
        """
        pass

    @abstractmethod
    def get_job_generator(self) -> JobGenerator:
        """
        :return a JobGenerator which type is same with AbstractJobPluginFactory job_type.
        """
        pass

    @abstractmethod
    def get_job_controller(self) -> JobController:
        """
        :return a JobController which type is same with AbstractJobPluginFactory job_type.
        """
        pass


def register_job_plugin_factory(plugin: AbstractJobPluginFactory):
    logging.debug("Register job plugin {} {}".format(plugin.__class__.__name__, plugin.job_type()))
    register_job_generator(job_type=plugin.job_type(), generator=plugin.get_job_generator())
    register_job_controller(job_type=plugin.job_type(), job_controller=plugin.get_job_controller())


def get_registered_job_plugin_factory_list() -> Dict:
    result = {}
    jm = get_job_controller_manager()
    for job_type, plugin in jm.object_dict.items():
        result[job_type] = (plugin.__class__.__module__, plugin.__class__.__name__)
    return result
