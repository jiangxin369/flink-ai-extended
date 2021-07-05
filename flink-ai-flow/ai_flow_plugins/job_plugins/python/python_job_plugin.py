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
import os
import sys
import signal
import time
from abc import ABC
from tempfile import NamedTemporaryFile, mkdtemp
from typing import Text, Any, Dict, List
from subprocess import Popen

from ai_flow.log import log_path_utils
from ai_flow.ai_graph.ai_node import AINode
from ai_flow.ai_graph.data_edge import DataEdge
from ai_flow.util import serialization_utils
from ai_flow.util import json_utils
from ai_flow.workflow.job_config import JobConfig
from ai_flow.ai_graph.ai_graph import AISubGraph
from ai_flow.plugin_interface.job_plugin_interface import AbstractJobPlugin, JobHandler, JobExecutionContext
from ai_flow.plugin_interface.scheduler_interface import JobExecutionInfo
from ai_flow.workflow.job import Job
from ai_flow_plugins.job_plugins.python.python_job_config import PythonJobConfig
from ai_flow_plugins.job_plugins.python.python_executor import PythonExecutor, ExecutionContext


class RunGraph(json_utils.Jsonable):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: List[AINode] = []
        self.executor_bytes: List[bytes] = []
        self.dependencies: Dict[Text, List[DataEdge]] = {}


class RunArgs(json_utils.Jsonable):
    def __init__(self,
                 working_dir: Text,
                 job_execution_info: JobExecutionInfo) -> None:
        super().__init__()
        self.working_dir: Text = working_dir
        self.job_execution_info: JobExecutionInfo = job_execution_info


def python_execute_func(run_graph: RunGraph, job_execution_info: JobExecutionInfo):
    executors: List[PythonExecutor] = []
    contexts: List[ExecutionContext] = []
    for index in range(len(run_graph.nodes)):
        caller: PythonExecutor = serialization_utils.deserialize(run_graph.executor_bytes[index])
        executors.append(caller)
        node: AINode = run_graph.nodes[index]
        execution_context = ExecutionContext(config=node.node_config, job_execution_info=job_execution_info)
        contexts.append(execution_context)

    def setup():
        for ii in range(len(executors)):
            cc = executors[ii]
            cc.setup(contexts[ii])

    def close():
        for ii in range(len(executors)):
            cc = executors[ii]
            cc.close(contexts[ii])

    setup()
    value_map = {}
    for i in range(len(run_graph.nodes)):
        node = run_graph.nodes[i]
        c = executors[i]
        if node.instance_id in run_graph.dependencies:
            ds = run_graph.dependencies[node.instance_id]
            params = []
            for d in ds:
                params.append(value_map[d.tail][d.port])
            value_map[node.instance_id] = c.execute(contexts[i], params)
        else:
            value_map[node.instance_id] = c.execute(contexts[i], [])
    close()


class PythonJob(Job):
    def __init__(self, job_config: JobConfig):
        super().__init__(job_config)
        self.run_graph_file: Text = None


class PythonJobHandler(JobHandler):

    def __init__(self, job: Job,
                 job_execution: JobExecutionInfo):
        super().__init__(job=job, job_execution=job_execution)
        self.sub_process = None
        self.run_args_file = None

    def wait_finished(self):
        self.log.info('Output:')
        self.sub_process.wait()
        self.log.info('Command exited with return code %s', self.sub_process.returncode)

        if self.sub_process.returncode != 0:
            raise Exception('python returned a non-zero exit code {}.'.format(self.sub_process.returncode))
        return None


class PythonJobPlugin(AbstractJobPlugin, ABC):

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def build_run_graph(cls, sub_graph: AISubGraph) -> RunGraph:
        run_graph = RunGraph()
        processed_nodes = set()
        node_list: List[AINode] = []
        for n in sub_graph.nodes.values():
            node_list.append(n)
        for e in sub_graph.edges:
            data_channel_list = []
            for c in sub_graph.edges[e]:
                cc: DataEdge = c
                data_channel_list.append(cc)
            run_graph.dependencies[e] = data_channel_list

        node_size = len(sub_graph.nodes)
        processed_size = len(processed_nodes)
        while processed_size != node_size:
            p_nodes = []
            for i in range(len(node_list)):
                if node_list[i].instance_id in sub_graph.edges:
                    flag = True
                    for c in sub_graph.edges[node_list[i].instance_id]:
                        if c.tail in processed_nodes:
                            pass
                        else:
                            flag = False
                            break
                else:
                    flag = True
                if flag:
                    p_nodes.append(node_list[i])
            if 0 == len(p_nodes):
                raise Exception("graph has circle!")
            for n in p_nodes:
                run_graph.nodes.append(n)
                run_graph.executor_bytes.append(n.executor)
                node_list.remove(n)
                processed_nodes.add(n.instance_id)
            processed_size = len(processed_nodes)
        return run_graph

    def generate(self, sub_graph: AISubGraph) -> Job:
        python_job_config: PythonJobConfig = sub_graph.config
        run_graph: RunGraph = self.build_run_graph(sub_graph)
        job = PythonJob(job_config=python_job_config)
        tmp_dir = mkdtemp(prefix=job.job_name, dir='/tmp')
        with NamedTemporaryFile(mode='w+b', dir=tmp_dir, prefix='{}_python_'.format(job.job_name), delete=False) as fp:
            job.run_graph_file = os.path.basename(fp.name)
            fp.write(serialization_utils.serialize(run_graph))
        job.resource_dir = tmp_dir
        return job

    def submit_job(self, job: Job, job_context: JobExecutionContext = None) -> JobHandler:
        run_args: RunArgs = RunArgs(working_dir=job_context.job_runtime_env.working_dir,
                                    job_execution_info=job_context.job_execution_info)

        with NamedTemporaryFile(mode='w+b', dir=job_context.job_runtime_env.generated_dir,
                                prefix='{}_run_args_'.format(job.job_name), delete=False) as fp:
            run_args_file = fp.name
            fp.write(serialization_utils.serialize(run_args))
        handler = PythonJobHandler(job=job, job_execution=job_context.job_execution_info)
        python_job: PythonJob = job
        run_graph_file = os.path.join(job_context.job_runtime_env.generated_dir, python_job.run_graph_file)

        env = os.environ.copy()
        if 'env' in job.job_config.properties:
            env.update(job.job_config.properties.get('env'))
        # Add PYTHONEPATH
        copy_path = sys.path.copy()
        copy_path.insert(0, job_context.job_runtime_env.python_dep_dir)
        env['PYTHONPATH'] = ':'.join(copy_path)

        current_path = os.path.dirname(__file__)
        script_path = os.path.join(current_path, 'python_run_main.py')
        python3_location = sys.executable
        bash_command = [python3_location, script_path, run_graph_file, run_args_file]

        stdout_log = log_path_utils.stdout_log_path(job_context.job_runtime_env.log_dir, job.job_name)
        stderr_log = log_path_utils.stderr_log_path(job_context.job_runtime_env.log_dir, job.job_name)
        if not os.path.exists(job_context.job_runtime_env.log_dir):
            os.makedirs(job_context.job_runtime_env.log_dir)

        sub_process = self.submit_python_process(bash_command=bash_command,
                                                 env=env,
                                                 working_dir=job_context.job_runtime_env.working_dir,
                                                 stdout_log=stdout_log,
                                                 stderr_log=stderr_log)
        handler.sub_process = sub_process
        handler.run_args_file = run_args_file
        return handler

    def stop_job(self, job_handler: JobHandler, job_context: Any = None):
        handler: PythonJobHandler = job_handler
        self.log.info('Output:')
        sub_process = handler.sub_process
        self.log.info('Sending SIGTERM signal to python process group')
        if sub_process and hasattr(sub_process, 'pid') and sub_process.poll() is None:
            while sub_process.poll() is None:
                try:
                    os.killpg(os.getpgid(sub_process.pid), signal.SIGTERM)
                except Exception:
                    time.sleep(1)

    def cleanup_job(self, job_handler: JobHandler, job_context: Any = None):
        if os.path.exists(job_handler.run_args_file):
            os.remove(job_handler.run_args_file)

    def job_type(self) -> Text:
        return "python"

    def submit_python_process(self, bash_command: List, env, working_dir, stdout_log, stderr_log):

        def pre_exec():
            # Restore default signal disposition and invoke setsid
            for sig in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
                if hasattr(signal, sig):
                    signal.signal(getattr(signal, sig), signal.SIG_DFL)
            os.setsid()

        self.log.info('Running command: %s', bash_command)
        with open(stdout_log, 'a') as out, open(stderr_log, 'a') as err:
            sub_process = Popen(  # pylint: disable=subprocess-popen-preexec-fn
                bash_command,
                stdout=out,
                stderr=err,
                cwd=working_dir,
                env=env,
                preexec_fn=pre_exec,
            )
        return sub_process
