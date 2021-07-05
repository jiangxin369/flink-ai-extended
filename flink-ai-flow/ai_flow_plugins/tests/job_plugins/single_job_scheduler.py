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
from typing import Text, List, Optional, Dict

from ai_flow.common.module_load import import_string
from ai_flow.plugin_interface.job_plugin_interface import BaseJobController, JobHandler, JobExecutionContext
from ai_flow.plugin_interface.scheduler_interface import AbstractScheduler, JobExecutionInfo, WorkflowExecutionInfo, \
    WorkflowInfo, SchedulerConfig
from ai_flow.project.project_description import ProjectDesc
from ai_flow.runtime.job_runtime_env import JobRuntimeEnv
from ai_flow.workflow.state import State
from ai_flow.workflow.workflow import Workflow, WorkflowPropertyKeys
from ai_flow_plugins.job_plugins.job_utils import prepare_job_runtime_env


class SingleJobScheduler(AbstractScheduler):
    def __init__(self, config: SchedulerConfig):
        super().__init__(config)
        self.workflow: Workflow = None
        self.project_desc: ProjectDesc = None
        self.job_controller: BaseJobController = None
        self.job_handler: JobHandler = None
        self.job_context: JobExecutionContext = None

    def submit_workflow(self, workflow: Workflow, project_desc: ProjectDesc, args: Dict = None) -> WorkflowInfo:
        self.workflow = workflow
        self.project_desc = project_desc
        return WorkflowInfo(workflow_name=workflow.workflow_name)

    def delete_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        self.workflow: Workflow = None
        self.project_desc: ProjectDesc = None
        self.job_controller: BaseJobController = None
        self.job_handler: JobHandler = None
        self.job_context: JobExecutionContext = None
        return WorkflowInfo(workflow_name=workflow_name)

    def pause_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        pass

    def resume_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        pass

    def get_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        pass

    def list_workflows(self, project_name: Text) -> List[WorkflowInfo]:
        pass

    def start_new_workflow_execution(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowExecutionInfo]:
        pass

    def kill_all_workflow_execution(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        pass

    def kill_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        pass

    def get_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        pass

    def list_workflow_executions(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        pass

    def start_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        job = self.workflow.jobs[job_name]
        plugins = self.workflow.properties.get(WorkflowPropertyKeys.JOB_PLUGINS)
        module, name = plugins.get(job.job_config.job_type)
        class_object = import_string('{}.{}'.format(module, name))
        self.job_controller: BaseJobController = class_object()
        job_runtime_env: JobRuntimeEnv = prepare_job_runtime_env(workflow_id=self.workflow.workflow_id,
                                                                 workflow_name=self.workflow.workflow_name,
                                                                 job_name=job_name,
                                                                 project_desc=self.project_desc)
        job_execution_info = JobExecutionInfo(job_execution_id='1', job_name=job_name,
                                              workflow_execution
                                              =WorkflowExecutionInfo(workflow_execution_id='1',
                                                                     workflow_info=WorkflowInfo(
                                                                         workflow_name=self.workflow.workflow_name)))
        self.job_context: JobExecutionContext = JobExecutionContext(job_runtime_env=job_runtime_env,
                                                                    workflow_config=self.workflow.workflow_config,
                                                                    project_config=self.project_desc.project_config,
                                                                    job_execution_info=job_execution_info)
        self.job_handler = self.job_controller.submit_job(job=job, job_context=self.job_context)
        return job_execution_info

    def stop_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        self.job_controller.stop_job(self.job_handler, self.job_context)
        self.job_controller.cleanup_job(self.job_handler, self.job_context)
        return JobExecutionInfo(job_execution_id='1', job_name=job_name)

    def restart_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        return JobExecutionInfo(job_execution_id='1', job_name=job_name)

    def get_job_executions(self, job_name: Text, execution_id: Text) -> List[JobExecutionInfo]:
        try:
            self.job_handler.wait_finished()
            result = self.job_handler.get_result()
            print(result)
            self.job_controller.cleanup_job(self.job_handler, self.job_context)
        except Exception as e:
            return [JobExecutionInfo(job_execution_id='1', job_name=job_name,
                                     state=State.FAILED, properties={'err': str(e)})]
        return [JobExecutionInfo(job_execution_id='1', job_name=job_name, state=State.FINISHED)]

    def list_job_executions(self, execution_id: Text) -> List[JobExecutionInfo]:
        pass
