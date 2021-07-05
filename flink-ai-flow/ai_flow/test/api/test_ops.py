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

from ai_flow.ai_graph.ai_node import AINode
from ai_flow.api import ops
from ai_flow.ai_graph.ai_graph import default_graph
from ai_flow.api.ai_flow_context import init_ai_flow_context
from ai_flow.context.job_context import job_config
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.meta.dataset_meta import DatasetMeta
from ai_flow.meta.model_meta import ModelMeta
from ai_flow.workflow.control_edge import ControlEdge, TaskAction, AIFlowInnerEventType
from ai_flow.workflow.periodic_config import PeriodicConfig
from ai_flow.workflow.state import State

_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


class TestOps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):

        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        cls.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                  start_default_notification=False,
                                  start_meta_service=True,
                                  start_metric_service=False,
                                  start_model_center_service=False,
                                  start_scheduler_service=False,
                                  scheduler_config=None)
        cls.server.run()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)

    def setUp(self):
        init_ai_flow_context(os.path.join(os.path.dirname(__file__), 'ut_workflows', 'workflows',
                                          'workflow_1', 'workflow_1.py'))

    def tearDown(self):
        default_graph().clear_graph()

    def get_node_by_name(self, name)->AINode:
        for n in default_graph().nodes.values():
            if n.name == name:
                return n
        return None

    def test_user_define_operation(self):
        with job_config('task_1'):
            o = ops.user_define_operation(executor=None, a='a', name='1')
            ops.user_define_operation(input_data=o, b='b', name='2')
        self.assertEqual(2, len(default_graph().nodes))
        self.assertEqual(1, len(default_graph().edges))
        node_0 = list(default_graph().nodes.values())[0]
        node_1 = list(default_graph().nodes.values())[1]
        self.assertEqual('mock', node_0.config.job_type)
        self.assertEqual('mock', node_1.config.job_type)
        self.assertEqual('a', self.get_node_by_name('1').node_config.get('a'))
        self.assertEqual('b', self.get_node_by_name('2').node_config.get('b'))

    def test_read_write_dataset(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            ops.write_dataset(input_data=o, dataset_info=DatasetMeta(name='dataset'))
        self.assertEqual(2, len(default_graph().nodes))
        self.assertEqual(1, len(default_graph().edges))
        node_0 = list(default_graph().nodes.values())[0]
        node_1 = list(default_graph().nodes.values())[1]
        self.assertEqual('dataset', node_0.node_config.get('dataset_info').name)
        self.assertEqual('dataset', node_1.node_config.get('dataset_info').name)
        self.assertEqual('mock', node_0.config.job_type)
        self.assertEqual('mock', node_1.config.job_type)

    def test_transform(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            t = ops.transform(input_data=o, executor=None)
            ops.write_dataset(input_data=t, dataset_info=DatasetMeta(name='dataset'))
        self.assertEqual(3, len(default_graph().nodes))
        self.assertEqual(2, len(default_graph().edges))

    def test_train(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            t = ops.train(input_data=o, executor=None, model_info=ModelMeta(name='model'), name='a')
            ops.write_dataset(input_data=t, dataset_info=DatasetMeta(name='dataset'))
        self.assertEqual(3, len(default_graph().nodes))
        self.assertEqual(2, len(default_graph().edges))
        n = self.get_node_by_name('a')
        self.assertEqual('model', n.node_config.get('model_info').name)

    def test_predict(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            t = ops.predict(input_data=o, executor=None,
                            model_info=ModelMeta(name='model'), name='a')
            ops.write_dataset(input_data=t, dataset_info=DatasetMeta(name='dataset'))
        self.assertEqual(3, len(default_graph().nodes))
        self.assertEqual(2, len(default_graph().edges))
        n = self.get_node_by_name('a')
        self.assertEqual('model', n.node_config.get('model_info').name)

    def test_evaluate(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            t = ops.evaluate(input_data=o, executor=None,
                             model_info=ModelMeta(name='model'), name='a')
        self.assertEqual(2, len(default_graph().nodes))
        self.assertEqual(1, len(default_graph().edges))
        n = self.get_node_by_name('a')
        self.assertEqual('model', n.node_config.get('model_info').name)

    def test_dataset_validate(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'), name='a')
            t = ops.dataset_validate(input_data=o, executor=None, name='b')
        self.assertEqual(2, len(default_graph().nodes))
        self.assertEqual(1, len(default_graph().edges))
        n = self.get_node_by_name('a')
        self.assertEqual('dataset', n.node_config.get('dataset_info').name)

    def test_model_validate(self):
        with job_config('task_1'):
            o = ops.read_dataset(executor=None, dataset_info=DatasetMeta(name='dataset'))
            t = ops.model_validate(input_data=o, executor=None,
                                   model_info=ModelMeta(name='model'), name='a')
        self.assertEqual(2, len(default_graph().nodes))
        self.assertEqual(1, len(default_graph().edges))
        n = self.get_node_by_name('a')
        self.assertEqual('model', n.node_config.get('model_info').name)

    def test_push_model(self):
        with job_config('task_1'):
            t = ops.push_model(executor=None,
                               model_info=ModelMeta(name='model'), name='a')
        self.assertEqual(1, len(default_graph().nodes))
        n = self.get_node_by_name('a')
        self.assertEqual('model', n.node_config.get('model_info').name)

    def test_action_on_event(self):
        with job_config('task_1'):
            o1 = ops.user_define_operation(executor=None, a='a', name='1')
        with job_config('task_2'):
            o2 = ops.user_define_operation(executor=None, b='b', name='2')
        ops.action_on_event(job_name='task_1', sender='task_2', event_key='a', event_value='a')
        self.assertEqual(1, len(default_graph().edges))
        edge: ControlEdge = default_graph().edges.get('task_1')[0]
        self.assertEqual('task_1', edge.head)
        self.assertEqual('task_2', edge.generate_met_config().sender)
        self.assertEqual('a', edge.generate_met_config().event_key)
        self.assertEqual('a', edge.generate_met_config().event_value)

    def test_action_on_state(self):
        with job_config('task_1'):
            o1 = ops.user_define_operation(executor=None, a='a', name='1')
        with job_config('task_2'):
            o2 = ops.user_define_operation(executor=None, b='b', name='2')
        ops.action_on_state(job_name='task_1',
                            upstream_job_name='task_2',
                            upstream_job_state=State.FINISHED, action=TaskAction.START)
        self.assertEqual(1, len(default_graph().edges))
        edge: ControlEdge = default_graph().edges.get('task_1')[0]
        self.assertEqual('task_1', edge.head)
        self.assertEqual('task_2', edge.generate_met_config().sender)
        self.assertEqual(AIFlowInnerEventType.JOB_STATUS_CHANGED, edge.generate_met_config().event_type)
        self.assertEqual(TaskAction.START, edge.generate_met_config().action)

    def test_run_after(self):
        with job_config('task_1'):
            o1 = ops.user_define_operation(executor=None, a='a', name='1')
        with job_config('task_2'):
            o2 = ops.user_define_operation(executor=None, b='b', name='2')
        ops.run_after(job_name='task_1', upstream_job_name='task_2')
        self.assertEqual(1, len(default_graph().edges))
        edge: ControlEdge = default_graph().edges.get('task_1')[0]
        self.assertEqual('task_1', edge.head)
        self.assertEqual('task_2', edge.generate_met_config().sender)
        self.assertEqual(AIFlowInnerEventType.UPSTREAM_JOB_SUCCESS, edge.generate_met_config().event_type)

    def test_action_with_periodic(self):
        with job_config('task_1'):
            o1 = ops.user_define_operation(executor=None, a='a', name='1')
        ops.periodic_run(job_name='task_1',
                         periodic_config=PeriodicConfig(cron_expression='* * * * * * *'))
        self.assertEqual(1, len(default_graph().edges))
        edge: ControlEdge = default_graph().edges.get('task_1')[0]
        self.assertEqual('task_1', edge.head)
        self.assertEqual('*', edge.generate_met_config().sender)
        self.assertEqual(AIFlowInnerEventType.PERIODIC_ACTION, edge.generate_met_config().event_type)


if __name__ == '__main__':
    unittest.main()
