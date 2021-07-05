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

from ai_flow import AIFlowServerRunner, init_ai_flow_context, PeriodicConfig
from ai_flow.plugin_interface.scheduler_interface import AbstractScheduler, JobExecutionInfo, WorkflowExecutionInfo, \
    WorkflowInfo, SchedulerConfig
import ai_flow as af
from ai_flow.project.project_description import ProjectDesc
from ai_flow.test.api import mock_plugins
from ai_flow.workflow.control_edge import TaskAction
from ai_flow.workflow.state import State
from ai_flow.workflow.workflow import Workflow
from ai_flow_plugins.scheduler_plugins.airflow.dag_generator import DAGGenerator


class MockScheduler(AbstractScheduler):
    def __init__(self, config: SchedulerConfig):
        super().__init__(config)
        self.dag_generator = DAGGenerator()

    def submit_workflow(self, workflow: Workflow, project_desc: ProjectDesc, args: Dict = None) -> WorkflowInfo:
        code_text = self.dag_generator.generate(workflow=workflow,
                                                project_name=project_desc.project_name,
                                                args=args)
        return WorkflowInfo(workflow_name='test', properties={'code': code_text})

    def delete_workflow(self, project_name: Text, workflow_name: Text) -> Optional[WorkflowInfo]:
        pass

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
        pass

    def stop_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        pass

    def restart_job_execution(self, job_name: Text, execution_id: Text) -> JobExecutionInfo:
        pass

    def get_job_executions(self, job_name: Text, execution_id: Text) -> List[JobExecutionInfo]:
        pass

    def list_job_executions(self, execution_id: Text) -> List[JobExecutionInfo]:
        pass


class TestDagGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_file = os.path.dirname(__file__) + '/master.yaml'
        cls.master = AIFlowServerRunner(config_file=config_file)
        cls.master.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.master.stop()

    def setUp(self):
        self.master._clear_db()
        af.default_graph().clear_graph()
        init_ai_flow_context(os.path.join(os.path.dirname(__file__), 'ut_workflows', 'workflows',
                                          'workflow_1', 'workflow_1.py'))

    def tearDown(self):
        self.master._clear_db()

    def test_one_task(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('op_0 = AIFlowOperator' in code)

    def test_two_task(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        with af.job_config('task_2'):
            af.user_define_operation(executor=None)
        af.action_on_event(job_name='task_2', event_key='a', event_type='a', event_value='a', sender='task_1')
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue("op_1.subscribe_event('a', 'a', 'default', 'task_1')" in code)
        self.assertTrue("op_1.set_events_handler(AIFlowHandler(configs_op_1))" in code)

    def test_three_task(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        with af.job_config('task_2'):
            af.user_define_operation(executor=None)
        with af.job_config('task_3'):
            af.user_define_operation(executor=None)
        af.action_on_event(job_name='task_3', event_key='a', event_type='a', event_value='a', sender='task_1')
        af.action_on_state(job_name='task_3', upstream_job_name='task_2',
                           upstream_job_state=State.FINISHED,
                           action=TaskAction.START)
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue(".subscribe_event('a', 'a', 'default', 'task_1')" in code)
        self.assertTrue(".subscribe_event('workflow_1', 'JOB_STATUS_CHANGED', 'test_project', 'task_2')" in code)
        self.assertTrue(".set_events_handler(AIFlowHandler(configs_op_" in code)

    def test_periodic_cron_task(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        af.periodic_run('task_1', periodic_config=PeriodicConfig(cron_expression="* * * * * * *"))
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('op_0 = AIFlowOperator' in code)
        self.assertTrue('op_0.executor_config' in code)

    def test_periodic_interval_task(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        af.periodic_run('task_1', periodic_config=PeriodicConfig(interval_expression="1,1,1,1"))
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('op_0 = AIFlowOperator' in code)
        self.assertTrue('op_0.executor_config' in code)

    def test_periodic_cron_workflow(self):
        workflow_config_ = af.workflow_config()
        workflow_config_.periodic_config = PeriodicConfig(start_date_expression="2020,1,1,,,,Asia/Chongqing",
                                                          cron_expression="* * * * * * *")
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('op_0 = AIFlowOperator' in code)
        self.assertTrue('datetime' in code)
        self.assertTrue('schedule_interval' in code)

    def test_periodic_interval_workflow(self):
        workflow_config_ = af.workflow_config()
        workflow_config_.periodic_config = PeriodicConfig(start_date_expression="2020,1,1,,,,Asia/Chongqing",
                                                          interval_expression="1,1,1,")
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('op_0 = AIFlowOperator' in code)
        self.assertTrue('datetime' in code)
        self.assertTrue('schedule_interval' in code)
        self.assertTrue('timedelta' in code)

    def test_run_after(self):
        with af.job_config('task_1'):
            af.user_define_operation(executor=None)
        with af.job_config('task_2'):
            af.user_define_operation(executor=None)
        with af.job_config('task_3'):
            af.user_define_operation(executor=None)
        af.run_after(job_name='task_3', upstream_job_name='task_1')
        af.run_after(job_name='task_3', upstream_job_name='task_2')

        w = af.workflow_operation.submit_workflow(workflow_name='workflow_1')
        code = w.properties.get('code')
        self.assertTrue('set_upstream' in code)


if __name__ == '__main__':
    unittest.main()
