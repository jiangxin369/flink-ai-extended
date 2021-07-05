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
import time
import shutil
from typing import List
from pyflink.table import Table, DataTypes, ScalarFunction
from pyflink.table.descriptors import Schema, OldCsv, FileSystem
from pyflink.table.udf import udf

from ai_flow import AIFlowServerRunner, init_ai_flow_context
from ai_flow.workflow.state import State
from ai_flow_plugins.job_plugins import flink
import ai_flow as af

project_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class Transformer(flink.FlinkPythonExecutor):
    def execute(self, execution_context: flink.ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        return [input_list[0].group_by('word').select('word, count(1)')]


class SleepUDF(ScalarFunction):

    def eval(self, s):
        time.sleep(100)
        return s


class Transformer2(flink.FlinkPythonExecutor):
    def execute(self, execution_context: flink.ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        execution_context.table_env.register_function("sleep_func", udf(SleepUDF(),
                                                                        input_types=[DataTypes.STRING()],
                                                                        result_type=DataTypes.STRING()))
        return [input_list[0].group_by('word').select('sleep_func(word), count(1)')]


class Source(flink.FlinkPythonExecutor):
    def execute(self, execution_context: flink.ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        input_file = os.path.join(os.getcwd(), 'resources', 'word_count.txt')
        t_env = execution_context.table_env
        t_env.connect(FileSystem().path(input_file)) \
            .with_format(OldCsv()
                         .field('word', DataTypes.STRING())) \
            .with_schema(Schema()
                         .field('word', DataTypes.STRING())) \
            .create_temporary_table('mySource')
        return [t_env.from_path('mySource')]


class Sink(flink.FlinkPythonExecutor):
    def execute(self, execution_context: flink.ExecutionContext, input_list: List[Table] = None) -> List[Table]:
        output_file = os.path.join(os.getcwd(), 'output')
        if os.path.exists(output_file):
            os.remove(output_file)

        t_env = execution_context.table_env
        statement_set = execution_context.statement_set
        t_env.connect(FileSystem().path(output_file)) \
            .with_format(OldCsv()
                         .field_delimiter('\t')
                         .field('word', DataTypes.STRING())
                         .field('count', DataTypes.BIGINT())) \
            .with_schema(Schema()
                         .field('word', DataTypes.STRING())
                         .field('count', DataTypes.BIGINT())) \
            .create_temporary_table('mySink')
        statement_set.add_insert('mySink', input_list[0])
        return []


class TestFlink(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_file = os.path.dirname(project_path) + '/master.yaml'
        cls.master = AIFlowServerRunner(config_file=config_file)
        cls.master.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.master.stop()
        generated = '{}/generated'.format(project_path)
        if os.path.exists(generated):
            shutil.rmtree(generated)
        temp = '{}/temp'.format(project_path)
        if os.path.exists(temp):
            shutil.rmtree(temp)

    def setUp(self):
        self.master._clear_db()
        af.default_graph().clear_graph()
        init_ai_flow_context(workflow_entry_file=__file__)

    def tearDown(self):
        self.master._clear_db()

    def test_local_flink_task(self):
        with af.job_config('task_1'):
            input_example = af.user_define_operation(executor=Source())
            processed = af.transform(input_data=[input_example], executor=Transformer())
            af.user_define_operation(input_data=[processed], executor=Sink())
        w = af.workflow_operation.submit_workflow(workflow_name=af.workflow_config().workflow_name)
        je = af.workflow_operation.start_job_execution(job_name='task_1', execution_id='1')
        je = af.workflow_operation.get_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual(State.FINISHED, je.state)

    def test_stop_local_flink_task(self):
        with af.job_config('task_1'):
            input_example = af.user_define_operation(executor=Source())
            processed = af.transform(input_data=[input_example], executor=Transformer2())
            af.user_define_operation(input_data=[processed], executor=Sink())
        w = af.workflow_operation.submit_workflow(workflow_name='test_python')
        je = af.workflow_operation.start_job_execution(job_name='task_1', execution_id='1')
        time.sleep(2)
        af.workflow_operation.stop_job_execution(job_name='task_1', execution_id='1')
        je = af.workflow_operation.get_job_execution(job_name='task_1', execution_id='1')
        self.assertEqual(State.FAILED, je.state)
        self.assertTrue('err' in je.properties)

    @unittest.skip("need start flink cluster")
    def test_cluster_flink_task(self):
        with af.job_config('task_2'):
            input_example = af.user_define_operation(executor=Source())
            processed = af.transform(input_data=[input_example], executor=Transformer())
            af.user_define_operation(input_data=[processed], executor=Sink())
        w = af.workflow_operation.submit_workflow(workflow_name=af.workflow_config().workflow_name)
        je = af.workflow_operation.start_job_execution(job_name='task_2', execution_id='1')
        je = af.workflow_operation.get_job_execution(job_name='task_2', execution_id='1')
        self.assertEqual(State.FINISHED, je.state)

    @unittest.skip("need start flink cluster")
    def test_cluster_stop_local_flink_task(self):
        with af.job_config('task_2'):
            input_example = af.user_define_operation(executor=Source())
            processed = af.transform(input_data=[input_example], executor=Transformer2())
            af.user_define_operation(input_data=[processed], executor=Sink())
        w = af.workflow_operation.submit_workflow(workflow_name='test_python')
        je = af.workflow_operation.start_job_execution(job_name='task_2', execution_id='1')
        time.sleep(20)
        af.workflow_operation.stop_job_execution(job_name='task_2', execution_id='1')
        je = af.workflow_operation.get_job_execution(job_name='task_2', execution_id='1')
        self.assertEqual(State.FAILED, je.state)
        self.assertTrue('err' in je.properties)


if __name__ == '__main__':
    unittest.main()
