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
import unittest
from ai_flow.ai_graph.ai_node import AINode
from ai_flow.workflow.job_config import JobConfig
from ai_flow.workflow.workflow_config import WorkflowConfig
from ai_flow.project.project_config import ProjectConfig
from ai_flow.context.workflow_context import __default_workflow_context__
from ai_flow.translator.translator import *


def build_ai_graph(node_number, job_number) -> AIGraph:
    graph = AIGraph()
    for i in range(node_number):
        j = i % job_number
        config = JobConfig(job_name='job_{}'.format(j), job_type='mock')
        ai_node = AINode(instance_id="node_" + str(i))
        ai_node.config = config
        graph.nodes[ai_node.instance_id] = ai_node

    add_data_edge(graph=graph, head='node_6', tail='node_0')
    add_data_edge(graph=graph, head='node_6', tail='node_3')
    add_control_edge(graph, 'job_2', 'job_0')
    add_control_edge(graph, 'job_2', 'job_1')

    return graph


def add_data_edge(graph, head, tail):
    graph.add_edge(head, DataEdge(head=head, tail=tail))


def add_control_edge(graph, job_name, upstream_job_name):
    graph.add_edge(job_name,
                   ControlEdge(head=job_name,
                               sender=upstream_job_name,
                               event_key='',
                               event_value=''))


class MockJobGenerator(BaseJobGenerator):

    def generate(self, sub_graph: AISubGraph) -> Job:
        return Job(job_config=sub_graph.config)


class TestTranslator(unittest.TestCase):

    def test_translate_graph(self):
        __default_workflow_context__.workflow_config = WorkflowConfig(workflow_name='workflow_1')
        project_desc = ProjectDesc()
        project_desc.project_path = '/tmp'
        project_desc.project_config = ProjectConfig()
        project_desc.project_config.set_project_name('test_project')
        graph: AIGraph = build_ai_graph(9, 3)
        splitter = GraphSplitter()
        split_graph = splitter.split(graph,project_desc)
        self.assertEqual(3, len(split_graph.nodes))
        self.assertEqual(1, len(split_graph.edges))
        self.assertEqual(2, len(split_graph.edges.get('job_2')))
        sub_graph = split_graph.nodes.get('job_0')
        self.assertTrue('node_6' in sub_graph.edges)
        constructor = WorkflowConstructor()
        constructor.register_job_generator('mock', MockJobGenerator())
        workflow = constructor.build_workflow(split_graph, project_desc)
        self.assertEqual(3, len(workflow.nodes))


if __name__ == '__main__':
    unittest.main()
