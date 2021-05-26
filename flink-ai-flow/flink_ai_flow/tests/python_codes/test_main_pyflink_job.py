#
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
#
import threading
import time
import unittest

from ai_flow.application_master.master_config import MasterConfig
from ai_flow.common import path_util
from notification_service.client import NotificationClient
from notification_service.event_storage import DbEventStorage
from notification_service.master import NotificationMaster
from notification_service.service import NotificationService
from typing import List

from ai_flow.common.path_util import get_file_dir

import ai_flow as af
from ai_flow import AIFlowMaster, SchedulerType, project_config, set_project_config_file
from flink_ai_flow.pyflink import Executor, FlinkFunctionContext, SourceExecutor, SinkExecutor, TableEnvCreator
from ai_flow.test import test_util
from pyflink.table import DataTypes
from pyflink.table.descriptors import Schema, OldCsv, FileSystem
from pyflink.table import Table
import flink_ai_flow as faf
import os

# dag_folder should be same as airflow_deploy_path in project.yaml
dag_folder = "/tmp/airflow/"
notification_client = None


class Transformer(Executor):
    def execute(self, function_context: FlinkFunctionContext, input_list: List[Table]) -> List[Table]:
        return [input_list[0].group_by('word').select('word, count(1)')]


class Source(SourceExecutor):
    def execute(self, function_context: FlinkFunctionContext) -> Table:
        example_meta: af.ExampleMeta = function_context.get_example_meta()
        t_env = function_context.get_table_env()
        t_env.connect(FileSystem().path(example_meta.batch_uri)) \
            .with_format(OldCsv()
                         .field('word', DataTypes.STRING())) \
            .with_schema(Schema()
                         .field('word', DataTypes.STRING())) \
            .create_temporary_table('mySource')
        return t_env.from_path('mySource')


class Sink(SinkExecutor):
    def execute(self, function_context: FlinkFunctionContext, input_table: Table) -> None:
        example_meta: af.ExampleMeta = function_context.get_example_meta()
        output_file = example_meta.batch_uri
        if os.path.exists(output_file):
            os.remove(output_file)

        t_env = function_context.get_table_env()
        statement_set = function_context.get_statement_set()
        t_env.connect(FileSystem().path(output_file)) \
            .with_format(OldCsv()
                         .field_delimiter('\t')
                         .field('word', DataTypes.STRING())
                         .field('count', DataTypes.BIGINT())) \
            .with_schema(Schema()
                         .field('word', DataTypes.STRING())
                         .field('count', DataTypes.BIGINT())) \
            .create_temporary_table('mySink')
        statement_set.add_insert('mySink', input_table)


class TestPyFlinkJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_file = test_util.get_master_config_file(SchedulerType.AIRFLOW)
        config = MasterConfig()
        config.load_from_file(config_file)
        cls.notification_uri = config.get_notification_uri()

        notification_port = int(cls.notification_uri.split(':')[1])
        storage = DbEventStorage('sqlite:///aiflow.db', create_table_if_not_exists=True)
        cls.notification_master = NotificationMaster(NotificationService(storage), notification_port)
        cls.notification_master.run()
        global notification_client
        notification_client = NotificationClient(server_uri=cls.notification_uri,
                                                 default_namespace="test_namespace")
        cls.master = AIFlowMaster(config_file=config_file)
        cls.master.start()
        project_config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "project.yaml")
        cls.set_project_config(config_file=project_config_file, main_file=__file__)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.master.stop()
        cls.notification_master.stop()
        af.unset_project_config()

    def setUp(self) -> None:
        af.default_graph().clear_graph()

    def tearDown(self):
        self.clear_db()
        TestPyFlinkJob.master._clear_db()

    @classmethod
    def set_project_config(cls, config_file, main_file):
        set_project_config_file(config_file)
        project_config()['entry_module_path'] = path_util.get_module_name(main_file)

    def test_run_pyflink_job(self):
        project_path = os.path.dirname(os.path.dirname(__file__))
        #af.set_project_config_file(project_path + "project.yaml")
        input_file = project_path + '/resources/word_count.txt'
        output_file = get_file_dir(__file__) + "/word_count_output.csv"
        if os.path.exists(output_file):
            os.remove(output_file)

        example_1 = af.create_example(name="example_1",
                                      support_type=af.ExampleSupportType.EXAMPLE_BOTH,
                                      batch_uri=input_file,
                                      stream_uri=input_file,
                                      data_format="csv")

        example_2 = af.create_example(name="example_2",
                                      support_type=af.ExampleSupportType.EXAMPLE_BOTH,
                                      batch_uri=output_file,
                                      stream_uri=output_file,
                                      data_format="csv")
        flink_config = faf.LocalFlinkJobConfig()
        flink_config.local_mode = 'cluster'
        flink_config.flink_home = os.environ.get('FLINK_HOME')
        flink_config.set_table_env_create_func(TableEnvCreator())
        with af.config(flink_config):
            input_example = af.read_example(example_info=example_1,
                                            executor=faf.flink_executor.FlinkPythonExecutor(python_object=Source())
                                            )
            processed = af.transform(input_data_list=[input_example],
                                     executor=faf.flink_executor.FlinkPythonExecutor(python_object=Transformer()))

            af.write_example(input_data=processed,
                             example_info=example_2,
                             executor=faf.flink_executor.FlinkPythonExecutor(python_object=Sink())
                             )
        workflow_id = af.run(project_path)
        res = af.wait_workflow_execution_finished(workflow_id)

    def test_run_pyflink_job_on_airflow(self):
        self.run_with_airflow_scheduler(target=self.run_pyflink_job_on_airflow)

    def run_pyflink_job_on_airflow(self):
        from airflow.utils.state import State
        self.wait_for_scheduler_started()
        project_path = os.path.dirname(os.path.dirname(__file__))
        input_file = project_path + '/resources/word_count.txt'
        output_file = get_file_dir(__file__) + "/word_count_output.csv"
        if os.path.exists(output_file):
            os.remove(output_file)

        example_1 = af.create_example(name="example_1",
                                      support_type=af.ExampleSupportType.EXAMPLE_BOTH,
                                      batch_uri=input_file,
                                      stream_uri=input_file,
                                      data_format="csv")

        example_2 = af.create_example(name="example_2",
                                      support_type=af.ExampleSupportType.EXAMPLE_BOTH,
                                      batch_uri=output_file,
                                      stream_uri=output_file,
                                      data_format="csv")
        flink_config = faf.LocalFlinkJobConfig()
        flink_config.local_mode = 'cluster'
        flink_config.flink_home = os.environ.get('FLINK_HOME')
        flink_config.set_table_env_create_func(TableEnvCreator())
        with af.config(flink_config):
            input_example = af.read_example(example_info=example_1,
                                            executor=faf.flink_executor.FlinkPythonExecutor(python_object=Source())
                                            )
            processed = af.transform(input_data_list=[input_example],
                                     executor=faf.flink_executor.FlinkPythonExecutor(python_object=Transformer()))

            af.write_example(input_data=processed,
                             example_info=example_2,
                             executor=faf.flink_executor.FlinkPythonExecutor(python_object=Sink())
                             )
        self.submit_workflow(workflow_name='test_run_pyflink_job_on_airflow')
        self.wait_for_task_execution(dag_id='test_run_pyflink_job_on_airflow', state=State.SUCCESS, expected_num=1)
        self.__class__.stop_scheduler()

    def submit_workflow(self, workflow_name):
        try:
            project_path = os.path.dirname(os.path.dirname(__file__))
            airflow_file_path = af.submit(project_path=project_path, dag_id=workflow_name)
            print(airflow_file_path)
            from airflow.contrib.jobs.scheduler_client import ExecutionContext
            context: ExecutionContext = af.run(project_path=project_path, dag_id=workflow_name,
                                               scheduler_type=SchedulerType.AIRFLOW)
            self.assertIsNotNone(context.dagrun_id)
        except Exception as e:
            print(e)

    def run_with_airflow_scheduler(self, target):

        from airflow.contrib.jobs.dag_trigger import StoppableThread
        t = StoppableThread(target=target, daemon=True)
        t.start()
        #timeout_thread = test_util.set_scheduler_timeout(notification_client, 180)
        self.start_scheduler(SchedulerType.AIRFLOW)
        #timeout_thread.stop()
        t.stop()

    @staticmethod
    def wait_for_scheduler_started():
        """Just sleep 5 secs for now"""
        time.sleep(5)

    def wait_for_task_execution(self, dag_id, state, expected_num):
        result = False
        check_nums = 100
        while check_nums > 0:
            time.sleep(2)
            check_nums = check_nums - 1
            tes = self.get_task_execution(dag_id, state)
            if len(tes) == expected_num:
                result = True
                break
        self.assertTrue(result)

    @staticmethod
    def get_task_execution(dag_id, state):
        from airflow.utils.session import create_session
        from airflow.models.taskexecution import TaskExecution
        with create_session() as session:
            if state:
                return session.query(TaskExecution).filter(
                    TaskExecution.dag_id == dag_id,
                    TaskExecution.state == state).all()
            else:
                return session.query(TaskExecution).filter(
                    TaskExecution.dag_id == dag_id).all()

    def start_scheduler(self, scheduler_type):
        from airflow.contrib.jobs.event_based_scheduler_job import EventBasedSchedulerJob
        from airflow.executors.local_executor import LocalExecutor
        try:
            if scheduler_type == SchedulerType.AIRFLOW:
                scheduler = EventBasedSchedulerJob(
                    dag_directory=dag_folder,
                    server_uri=self.notification_uri,
                    executor=LocalExecutor(3),
                    max_runs=-1,
                    refresh_dag_dir_interval=1
                )
            scheduler.run()
        except Exception as e:
            print(e)

    @classmethod
    def stop_scheduler(cls):
        from airflow.events.scheduler_events import StopSchedulerEvent
        notification_client.send_event(StopSchedulerEvent(job_id=0).to_event())

    @staticmethod
    def clear_db():
        from airflow.utils.session import create_session
        with create_session() as session:
            from airflow.models import DagRun, DagModel, TaskInstance, Message
            from airflow.models.taskexecution import TaskExecution
            from airflow.models.serialized_dag import SerializedDagModel
            from airflow.models.dagcode import DagCode
            from airflow.jobs.base_job import BaseJob
            session.query(BaseJob).delete()
            session.query(DagModel).delete()
            session.query(SerializedDagModel).delete()
            session.query(DagRun).delete()
            session.query(TaskInstance).delete()
            session.query(TaskExecution).delete()
            session.query(Message).delete()
            session.query(DagCode).delete()


if __name__ == '__main__':

    tt = TestPyFlinkJob()
    tt.test_run_pyflink_job()
    tt.test_run_pyflink_job_on_airflow()
