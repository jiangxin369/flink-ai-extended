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
from abc import ABC, abstractmethod
from typing import Dict, Text, List, Optional
from ai_flow.common.configuration import AIFlowConfiguration
from ai_flow.util import json_utils
from ai_flow.workflow.workflow import Workflow
from ai_flow.project.project_description import ProjectDesc


class WorkflowInfo(json_utils.Jsonable):

    def __init__(self,
                 namespace: Text = None,
                 workflow_name: Text = None,
                 properties: Dict = None):
        self._namespace = namespace
        self._workflow_name = workflow_name
        if properties is None:
            properties = {}
        self._properties = properties

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        self._namespace = value

    @property
    def workflow_name(self):
        return self._workflow_name

    @workflow_name.setter
    def workflow_name(self, value):
        self._workflow_name = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    def __str__(self) -> str:
        return json_utils.dumps(self)


class WorkflowExecutionInfo(json_utils.Jsonable):
    def __init__(self,
                 workflow_execution_id: Text,
                 workflow_info: WorkflowInfo = None,
                 state: Text = None,
                 properties: Dict = None,
                 start_date: Text = None,
                 end_date: Text = None):
        if properties is None:
            properties = {}
        self._properties = properties
        self._workflow_execution_id = workflow_execution_id
        self._workflow_info = workflow_info
        self._state = state
        self._start_date = start_date
        self._end_date = end_date

    @property
    def workflow_execution_id(self):
        return self._workflow_execution_id

    @workflow_execution_id.setter
    def workflow_execution_id(self, value):
        self._workflow_execution_id = value

    @property
    def workflow_info(self):
        return self._workflow_info

    @workflow_info.setter
    def workflow_info(self, value):
        self._workflow_info = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        self._start_date = value

    @property
    def end_date(self):
        return self._start_date

    @end_date.setter
    def end_date(self, value):
        self._end_date = value

    def __str__(self) -> str:
        return json_utils.dumps(self)


class JobExecutionInfo(json_utils.Jsonable):
    def __init__(self,
                 job_name: Text = None,
                 state: Text = None,
                 workflow_execution: WorkflowExecutionInfo = None,
                 job_execution_id: Text = None,
                 start_date: Text = None,
                 end_date: Text = None,
                 properties: Dict = None,
                 ):
        self._job_name = job_name
        self._state = state
        self._workflow_execution = workflow_execution
        self._start_date = start_date
        self._end_date = end_date
        self._job_execution_id = job_execution_id
        if properties is None:
            properties = {}
        self._properties = properties

    @property
    def job_name(self):
        return self._job_name

    @job_name.setter
    def job_name(self, value):
        self._job_name = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def workflow_execution(self):
        return self._workflow_execution

    @workflow_execution.setter
    def workflow_execution(self, value):
        self._workflow_execution = value

    @property
    def job_execution_id(self):
        return self._job_execution_id

    @job_execution_id.setter
    def job_execution_id(self, value):
        self._job_execution_id = value

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        self._start_date = value

    @property
    def end_date(self):
        return self._start_date

    @end_date.setter
    def end_date(self, value):
        self._end_date = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    def __str__(self) -> str:
        return json_utils.dumps(self)


class SchedulerConfig(AIFlowConfiguration):

    def repository(self):
        if 'repository' not in self:
            return '/tmp'
        else:
            return self['repository']

    def set_repository(self, value):
        self['repository'] = value

    def scheduler_class_name(self):
        if self.get('scheduler_class_name') is not None:
            return self.get('scheduler_class_name')
        else:
            return None

    def set_scheduler_class_name(self, value):
        self['scheduler_class_name'] = value

    def notification_service_uri(self):
        return self.get('notification_service_uri', None)

    def set_notification_service_uri(self, value):
        self['notification_service_uri'] = value

    def properties(self):
        if 'properties' not in self:
            return None
        return self['properties']

    def set_properties(self, value):
        self['properties'] = value


class AbstractScheduler(ABC):
    def __init__(self, config: SchedulerConfig):
        self._config = config

    @property
    def config(self):
        return self._config

    @abstractmethod
    def submit_workflow(self, workflow: Workflow, project_desc: ProjectDesc, args: Dict = None) -> WorkflowInfo:
        """
        Submit the workflow to scheduler.
        :param workflow: ai_flow.workflow.workflow.Workflow type.
        :param project_desc: ai_flow.project.project_description.ProjectDesc type.
        :param args: arguments pass to scheduler.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def delete_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        """
        Delete the workflow from scheduler.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def pause_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        """
        Make the scheduler stop scheduling the workflow.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def resume_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        """
        Make the scheduler resume scheduling the workflow.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def get_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        """
        Get the workflow information.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def list_workflows(self, project_name: Text) -> List[WorkflowInfo]:
        """
        List the workflow information.
        :param project_name: The project name.
        :return: The workflow information.
        """
        pass

    @abstractmethod
    def start_new_workflow_execution(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowExecutionInfo]:
        """
        Make the scheduler new a workflow execution.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow execution information.
        """
        pass

    @abstractmethod
    def kill_all_workflow_execution(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        """
        Kill all workflow execution of the workflow.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow execution information.
        """
        pass

    @abstractmethod
    def kill_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        """
        Kill the workflow execution by execution id.
        :param execution_id: The workflow execution id.
        :return: The workflow execution information.
        """
        pass

    @abstractmethod
    def get_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        """
        Get the workflow execution information.
        :param execution_id: The workflow execution id.
        :return: The workflow execution information.
        """
        pass

    @abstractmethod
    def list_workflow_executions(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        """
        List all workflow executions by workflow name.
        :param project_name: The project name.
        :param workflow_name: The workflow name.
        :return: The workflow execution information.

        """
        pass

    @abstractmethod
    def start_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        """
        Make the scheduler start a new job execution.
        :param job_name: The job name.
        :param execution_id: The workflow execution id.
        :return: The job execution information.
        """
        pass

    @abstractmethod
    def stop_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        """
        Make the scheduler stop the job execution.
        :param job_name: The job name.
        :param execution_id: The workflow execution id.
        :return: The job execution information.
        """
        pass

    @abstractmethod
    def restart_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        """
        Make the scheduler restart a job execution.
        :param job_name: The job name.
        :param execution_id: The workflow execution id.
        :return: The job execution information.
        """
        pass

    @abstractmethod
    def get_job_executions(self, job_name: Text, execution_id: Text) -> List[JobExecutionInfo]:
        """
        Get the job execution information by job name.
        :param job_name: The job name.
        :param execution_id: The workflow execution id.
        :return: The job execution information.
        """
        pass

    @abstractmethod
    def list_job_executions(self, execution_id: Text) -> List[JobExecutionInfo]:
        """
        List the job execution information by the workflow execution id.
        :param execution_id: The workflow execution id.
        :return: The job execution information.
        """
        pass
