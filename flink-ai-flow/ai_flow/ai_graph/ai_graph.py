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
from ai_flow.graph.graph import Graph, get_id_generator
from ai_flow.graph.channel import Channel
from ai_flow.ai_graph.ai_node import AINode
from typing import Dict, List, Text, Optional, Union
from ai_flow.ai_graph.data_edge import DataEdge
from ai_flow.workflow.control_edge import ControlEdge
from ai_flow.workflow.job_config import JobConfig
from ai_flow.context.workflow_context import workflow_config
from ai_flow.context.job_context import current_job_name


class AIGraph(Graph):

    def __init__(self) -> None:
        super().__init__()
        self.nodes: Dict[Text, AINode] = {}

    def add_node(self, node: AINode):
        instance_id = get_id_generator(self).generate_id(node)
        node.set_instance_id(instance_id)
        if workflow_config() is not None \
                and current_job_name() is not None \
                and current_job_name() in workflow_config().job_configs:
            node.config = workflow_config().job_configs.get(current_job_name())
        self.nodes[instance_id] = node

    def get_node_by_id(self, node_id: Text) -> Optional[AINode]:
        if node_id in self.nodes:
            return self.nodes[node_id]
        else:
            return None

    def add_channel(self, instance_id: Text, channel: Channel):
        edge = DataEdge(head=instance_id, tail=channel.node_id, port=channel.port)
        self.add_edge(instance_id=instance_id, edge=edge)


__default_ai_graph__ = AIGraph()


def default_graph() -> AIGraph:
    return __default_ai_graph__


def add_ai_node_to_graph(node, inputs: Union[None, Channel, List[Channel]]):
    default_graph().add_node(node)
    if isinstance(inputs, Channel):
        default_graph().add_channel(instance_id=node.instance_id, channel=inputs)

    elif isinstance(inputs, List):
        for c in inputs:
            default_graph().add_channel(instance_id=node.instance_id, channel=c)


class AISubGraph(AIGraph):

    def __init__(self,
                 config: JobConfig,
                 ) -> None:
        super().__init__()
        self.config: JobConfig = config
        self.edges: Dict[Text, List[DataEdge]] = {}

    def add_node(self, node: AINode):
        self.nodes[node.instance_id] = node


class SplitGraph(AIGraph):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: Dict[Text, AISubGraph] = {}
        self.edges: Dict[Text, List[ControlEdge]] = {}

    def add_node(self, node: AISubGraph):
        self.nodes[node.config.job_name] = node
