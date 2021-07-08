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

from ai_flow.util.json_utils import dumps
from typing import Any, Text
import os
from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from ai_flow.common.module_load import import_string
from ai_flow.util.time_utils import datetime_to_int64
from ai_flow.plugin_interface.job_plugin_interface import JobController, JobHandler, JobRuntimeEnv
from ai_flow.context.project_context import build_project_context
from ai_flow.endpoint.client.scheduler_client import SchedulerClient
from ai_flow.plugin_interface.blob_manager_interface import BlobManagerFactory
from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo, WorkflowExecutionInfo, WorkflowInfo
from ai_flow.workflow.job import Job
from ai_flow.workflow.workflow import Workflow, WorkflowPropertyKeys
from ai_flow_plugins.job_plugins.job_utils import prepare_job_runtime_env


class AIFlowOperator(BaseOperator):
    @apply_defaults
    def __init__(
            self,
            job: Job,
            workflow: Workflow,
            **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.job: Job = job
        self.workflow: Workflow = workflow
        plugins = self.workflow.properties.get(WorkflowPropertyKeys.JOB_PLUGINS)
        module, name = plugins.get(self.job.job_config.job_type)
        class_object = import_string('{}.{}'.format(module, name))
        self.job_controller: JobController = class_object()
        self.job_handler: JobHandler = None
        self.job_runtime_env: JobRuntimeEnv = None

    def context_to_job_info(self, project_name: Text, context: Any) -> JobExecutionInfo:
        wi = WorkflowInfo(namespace=project_name, workflow_name=self.workflow.workflow_name)
        we = WorkflowExecutionInfo(workflow_execution_id=context.get('dag_run').run_id,
                                   workflow_info=wi,
                                   start_date=str(datetime_to_int64(context.get('dag_run').start_date)),
                                   end_date=str(datetime_to_int64(context.get('dag_run').end_date)),
                                   status=context.get('dag_run').get_state())
        je = JobExecutionInfo(job_name=self.job.job_name,
                              job_execution_id=str(context.get('ti').try_number),
                              status=context.get('ti').state,
                              start_date=str(datetime_to_int64(context.get('ti').start_date)),
                              end_date=str(datetime_to_int64(context.get('ti').end_date)),
                              workflow_execution=we)
        return je

    def pre_execute(self, context: Any):
        config = {}
        config.update(self.workflow.properties['blob'])
        local_repo = config.get('local_repository')
        if local_repo is not None:
            # Maybe Download the project code
            if not os.path.exists(local_repo):
                os.makedirs(local_repo)
            blob_manager = BlobManagerFactory.get_blob_manager(config)
            project_path: Text = blob_manager \
                .download_project(workflow_id=self.workflow.workflow_snapshot_id,
                                  remote_path=self.workflow.project_uri,
                                  local_path=local_repo)
        else:
            project_path = self.workflow.project_uri
        self.log.info("project_path:" + project_path)
        project_context = build_project_context(project_path)

        job_execution_info: JobExecutionInfo = self.context_to_job_info(project_context.project_name, context)
        if context['conf'].has_option('scheduler', 'working_dir'):
            root_working_dir = context['conf'].get('scheduler', 'working_dir')
        else:
            root_working_dir = os.path.join(project_context.project_path, 'temp')
        self.log.info('working dir: {}'.format(root_working_dir))

        self.job_runtime_env = prepare_job_runtime_env(workflow_snapshot_id=self.workflow.workflow_snapshot_id,
                                                       workflow_name=self.workflow.workflow_name,
                                                       project_context=project_context,
                                                       job_execution_info=job_execution_info,
                                                       root_working_dir=root_working_dir)

    def execute(self, context: Any):
        self.log.info("context:" + str(context))
        self.job_handler: JobHandler = self.job_controller.submit_job(self.job, self.job_runtime_env)
        server_uri = self.job_runtime_env.project_config.get_server_uri()
        scheduler_client = SchedulerClient(server_uri)
        job_execution_info = self.job_runtime_env.job_execution_info
        execution_str = job_execution_info.generate_execution_str()
        old_labels = None
        while self.job_handler.is_job_running():
            labels = dumps(self.job_handler.obtain_job_labels())
            if labels != old_labels:
                scheduler_client.upsert_execution_label(label_name=execution_str, label_value=labels)
                old_labels = labels
            # TODO make sleep time configurable
            time.sleep(3)
        result = self.job_handler.get_result()
        self.job_controller.cleanup_job(self.job_handler, self.job_runtime_env)
        return result

    def on_kill(self):
        self.job_controller.stop_job(self.job_handler, self.job_runtime_env)
        self.job_controller.cleanup_job(self.job_handler, self.job_runtime_env)
