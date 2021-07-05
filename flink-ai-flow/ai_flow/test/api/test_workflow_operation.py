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
import unittest
import os
from typing import Text, List, Optional, Dict

from ai_flow.ai_graph.ai_graph import default_graph
from ai_flow.ai_graph.ai_node import AINode
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.api.ai_flow_context import init_ai_flow_context
from ai_flow.context.workflow_context import workflow_config
from ai_flow.plugin_interface.scheduler_interface import AbstractScheduler, JobExecutionInfo, WorkflowExecutionInfo, \
    WorkflowInfo

from ai_flow.project.project_description import ProjectDesc
from ai_flow.workflow.state import State
from ai_flow.workflow.workflow import Workflow
from ai_flow.api import workflow_operation
from ai_flow.test.api import mock_plugins

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


class MockScheduler(AbstractScheduler):

    def submit_workflow(self, workflow: Workflow, project_desc: ProjectDesc, args: Dict = None) -> WorkflowInfo:
        return WorkflowInfo(namespace=project_desc.project_name, workflow_name=workflow.workflow_name)

    def delete_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        return WorkflowInfo(namespace=project_name, workflow_name=workflow_name)

    def pause_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        return WorkflowInfo(namespace=project_name, workflow_name=workflow_name)

    def resume_workflow_scheduling(self, project_name: Text, workflow_name: Text) -> WorkflowInfo:
        return WorkflowInfo(namespace=project_name, workflow_name=workflow_name)

    def get_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        return WorkflowInfo(namespace=project_name, workflow_name=workflow_name)

    def list_workflows(self, project_name: Text) -> List[WorkflowInfo]:
        return [WorkflowInfo(namespace=project_name, workflow_name='workflow_1'),
                WorkflowInfo(namespace=project_name, workflow_name='workflow_2')]

    def start_new_workflow_execution(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowExecutionInfo]:
        return WorkflowExecutionInfo(workflow_execution_id='1', state=State.RUNNING)

    def kill_all_workflow_execution(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        return [WorkflowExecutionInfo(workflow_execution_id='1', state=State.RUNNING),
                WorkflowExecutionInfo(workflow_execution_id='2', state=State.RUNNING)]

    def kill_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        return WorkflowExecutionInfo(workflow_execution_id='1', state=State.RUNNING)

    def get_workflow_execution(self, execution_id: Text) -> Optional[WorkflowExecutionInfo]:
        return WorkflowExecutionInfo(workflow_execution_id='1', state=State.RUNNING)

    def list_workflow_executions(self, project_name: Text, workflow_name: Text) -> List[WorkflowExecutionInfo]:
        return [WorkflowExecutionInfo(workflow_execution_id='1', state=State.RUNNING),
                WorkflowExecutionInfo(workflow_execution_id='2', state=State.RUNNING)]

    def start_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        return JobExecutionInfo(job_name='task_1', state=State.RUNNING)

    def stop_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        return JobExecutionInfo(job_name='task_1', state=State.RUNNING)

    def restart_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        return JobExecutionInfo(job_name='task_1', state=State.RUNNING)

    def get_job_executions(self, job_name: Text, execution_id: Text) -> List[JobExecutionInfo]:
        return [JobExecutionInfo(job_name='task_1', state=State.RUNNING)]

    def list_job_executions(self, execution_id: Text) -> List[JobExecutionInfo]:
        return [JobExecutionInfo(job_name='task_1', state=State.RUNNING),
                JobExecutionInfo(job_name='task_2', state=State.RUNNING)]


SCHEDULER_CLASS = 'ai_flow.test.api.test_workflow_operation.MockScheduler'


class TestWorkflowOperation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        config = {"scheduler_class_name": SCHEDULER_CLASS}
        cls.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                  start_default_notification=False,
                                  start_meta_service=True,
                                  start_metric_service=False,
                                  start_model_center_service=False,
                                  start_scheduler_service=True,
                                  scheduler_config=config)
        cls.server.run()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)

    def setUp(self):
        init_ai_flow_context(os.path.join(os.path.dirname(__file__), 'ut_workflows', 'workflows',
                                          'workflow_1', 'workflow_1.py'))
        self.build_ai_graph()

    def tearDown(self):
        default_graph().clear_graph()


    def build_ai_graph(self):
        g = default_graph()
        for jc in workflow_config().job_configs.values():
            n = AINode(name=jc.job_name)
            n.config = jc
            g.add_node(n)

    def test_submit_workflow(self):
        w = workflow_operation.submit_workflow(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_delete_workflow(self):
        w = workflow_operation.delete_workflow(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_pause_workflow(self):

        w = workflow_operation.pause_workflow_scheduling(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_resume_workflow(self):

        w = workflow_operation.resume_workflow_scheduling(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_get_workflow(self):

        w = workflow_operation.get_workflow(workflow_name='workflow_1')
        self.assertEqual('workflow_1', w.workflow_name)

    def test_list_workflows(self):

        ws = workflow_operation.list_workflows()
        self.assertEqual(2, len(ws))

    def test_start_new_workflow_execution(self):

        w = workflow_operation.start_new_workflow_execution(workflow_name='workflow_1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_kill_all_workflow_execution(self):

        ws = workflow_operation.kill_all_workflow_executions(workflow_name='workflow_1')
        self.assertEqual(2, len(ws))

    def test_kill_workflow_execution(self):

        w = workflow_operation.kill_workflow_execution(execution_id='1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_get_workflow_execution(self):

        w = workflow_operation.get_workflow_execution(execution_id='1')
        self.assertEqual('1', w.workflow_execution_id)

    def test_list_workflow_executions(self):

        ws = workflow_operation.list_workflow_executions(workflow_name='workflow_1')
        self.assertEqual(2, len(ws))

    def test_start_job_execution(self):

        j = workflow_operation.start_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_stop_job_execution(self):

        j = workflow_operation.stop_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_restart_job_execution(self):

        j = workflow_operation.restart_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_get_job_execution(self):

        j = workflow_operation.get_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual('task_1', j.job_name)

    def test_list_job_execution(self):

        js = workflow_operation.list_job_executions(execution_id='1')
        self.assertEqual(2, len(js))


if __name__ == '__main__':
    unittest.main()
