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
import os
import queue
import shutil
import sys
import time
import unittest
import ai_flow as af
from ai_flow import AIFlowMaster, SchedulerType, unset_project_config
from ai_flow.api.project import generate_project_desc
from ai_flow.application_master.master_config import MasterConfig
from ai_flow.executor.executor import CmdExecutor
from ai_flow.graph.edge import MetCondition, TaskAction, EventLife, MetValueCondition, DEFAULT_NAMESPACE
from ai_flow.test import test_util
from ai_flow.test.test_util import set_scheduler_timeout
from notification_service.base_notification import BaseEvent
from notification_service.client import NotificationClient
from notification_service.event_storage import DbEventStorage
from notification_service.master import NotificationMaster
from notification_service.service import NotificationService

PROJECT_NAME = 'test_project'
# dag_folder should be same as airflow_deploy_path in project.yaml
dag_folder = "/tmp/airflow/unittest/dags"
notification_client = None


class TestProject(unittest.TestCase):

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
                                                 default_namespace=DEFAULT_NAMESPACE)
        cls.master = AIFlowMaster(config_file=config_file)
        cls.master.start()

    @classmethod
    def tearDownClass(cls) -> None:
        notification_client.stop_listen_events()
        notification_client.stop_listen_event()
        cls.master.stop()
        cls.notification_master.stop()
        af.unset_project_config()

    def setUp(self):
        af.default_graph().clear_graph()
        self.__class__.make_dir(parent=dag_folder)
        unset_project_config()
        test_util.set_project_config(__file__)
        self.clear_db()

    def tearDown(self):
        self.clear_dag_folder()
        self.__class__.master._clear_db()
        self.clear_db()

    def run_with_airflow_scheduler(self, target, timeout=150):
        from ai_flow.test.test_util import StoppableThread
        signal_queue = queue.Queue()
        t = StoppableThread(target=target, daemon=True)
        t.start()
        timeout_thread = set_scheduler_timeout(notification_client=notification_client,
                                               secs=timeout,
                                               signal_queue=signal_queue)
        self.start_scheduler(SchedulerType.AIRFLOW)
        print("scheculer stopped")
        t.stop()
        timeout_thread.stop()
        timeout_thread.join()
        if signal_queue.qsize() > 0:
            self.fail("Airflow scheduler timeout after {}s".format(timeout))

    def test_run_project(self):
        self.run_with_airflow_scheduler(target=self.run_project)

    def run_project(self):
        from airflow.utils.state import State
        print(sys._getframe().f_code.co_name)
        self.wait_for_scheduler_started()
        self.build_ai_graph(1)
        self.submit_workflow(workflow_name=PROJECT_NAME)
        self.wait_for_task_execution(dag_id=PROJECT_NAME, state=State.SUCCESS, expected_num=3)
        self.__class__.stop_scheduler()

    def test_stream_with_external_trigger(self):
        self.run_with_airflow_scheduler(target=self.stream_with_external_trigger)

    def stream_with_external_trigger(self):
        from airflow.utils.state import State
        print(sys._getframe().f_code.co_name)
        self.wait_for_scheduler_started()
        trigger = af.external_trigger(name='stream_trigger')
        job_config = af.BaseJobConfig('local', 'cmd_line')
        job_config.job_name = 'test_cmd'
        with af.config(job_config):
            cmd_executor = af.user_define_operation(output_num=0,
                                                    executor=CmdExecutor(
                                                        cmd_line="echo hello_world && sleep {}".format(1)))

        af.user_define_control_dependency(src=cmd_executor, dependency=trigger, event_key='key',
                                          event_value='value', event_type='name', condition=MetCondition.NECESSARY
                                          , action=TaskAction.START, life=EventLife.ONCE,
                                          value_condition=MetValueCondition.EQUAL, namespace=DEFAULT_NAMESPACE)
        self.submit_workflow(workflow_name=PROJECT_NAME)
        self.wait_for_task_instance(dag_id=PROJECT_NAME, state=State.SCHEDULED, expected_num=1)
        self.__class__.publish_event(key='key', value='value', event_type='name', namespace=DEFAULT_NAMESPACE)
        self.wait_for_task_execution(PROJECT_NAME, State.SUCCESS, 1)

        # SUCCESS dagrun will not be scheduled anymore, is it reasonable?
        #self.__class__.publish_event(key='key', value='value', event_type='name', namespace=DEFAULT_NAMESPACE)
        #self.wait_for_task_execution('test_project', State.SUCCESS, 2)
        self.__class__.stop_scheduler()

    def submit_workflow(self, workflow_name):
        try:
            project_desc = generate_project_desc()
            project_path = project_desc.project_path
            airflow_file_path = af.submit(project_path=project_path, dag_id=workflow_name)
            self.assertEqual(os.path.join(project_desc.project_config.get_airflow_deploy_path(), workflow_name + ".py"),
                              airflow_file_path)
            from airflow.contrib.jobs.scheduler_client import ExecutionContext
            context: ExecutionContext = af.run(project_path=project_path, dag_id=workflow_name,
                                               scheduler_type=SchedulerType.AIRFLOW)
            self.assertIsNotNone(context.dagrun_id)
        except Exception as e:
            print(e)

    @classmethod
    def publish_event(cls, key, value, event_type, namespace=DEFAULT_NAMESPACE):
        try:
            notification_client.send_event(BaseEvent(key=key,
                                                     value=value,
                                                     event_type=event_type,
                                                     namespace=namespace))
        except Exception as e:
            print(e)

    @staticmethod
    def build_ai_graph(sleep_time: int):
        with af.engine('cmd_line'):
            p_list = []
            for i in range(3):
                p = af.user_define_operation(
                    executor=CmdExecutor(cmd_line="echo hello_{} && sleep {}".format(i, sleep_time)))
                p_list.append(p)
            af.stop_before_control_dependency(p_list[0], p_list[1])
            af.stop_before_control_dependency(p_list[0], p_list[2])

    @staticmethod
    def make_dir(parent=None, dir_name=''):
        if not parent:
            parent = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(parent, dir_name)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

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
            print("Error occurred in scheduler, " + str(e))

    @classmethod
    def stop_scheduler(cls):
        from airflow.events.scheduler_events import StopSchedulerEvent
        notification_client.send_event(StopSchedulerEvent(job_id=0).to_event())

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

    def wait_for_task_instance(self, dag_id, state, expected_num):
        result = False
        check_nums = 100
        while check_nums > 0:
            time.sleep(2)
            check_nums = check_nums - 1
            tes = self.get_task_instance(dag_id, state)
            if len(tes) == expected_num:
                result = True
                break
        self.assertTrue(result)

    @staticmethod
    def wait_for_scheduler_started():
        """Just sleep 10 secs for now"""
        time.sleep(10)

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

    @staticmethod
    def get_task_instance(dag_id, state):
        from airflow.utils.session import create_session
        from airflow.models.taskinstance import TaskInstance
        with create_session() as session:
            if state:
                return session.query(TaskInstance).filter(
                    TaskInstance.dag_id == dag_id,
                    TaskInstance.state == state).all()
            else:
                return session.query(TaskInstance).filter(
                    TaskInstance.dag_id == dag_id).all()

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

    @staticmethod
    def clear_dag_folder():
        shutil.rmtree(dag_folder)
