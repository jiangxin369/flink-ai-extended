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
from ai_flow.graph.node import BaseNode
from typing import Dict, List, Text, Optional
from ai_flow.graph.edge import Edge
from ai_flow.util.json_utils import Jsonable, loads

__id_generator_map__ = {}


def get_id_generator(graph: object):
    if graph in __id_generator_map__:
        return __id_generator_map__[graph]
    else:
        __id_generator_map__[graph] = _IdGenerator()
        return __id_generator_map__[graph]


class _IdGenerator(Jsonable):

    def __init__(self) -> None:
        super().__init__()
        self.node_type_to_num: Dict[Text, int] = {}

    def generate_id(self, node: BaseNode) -> Text:
        node_type = type(node).__name__
        if node_type in self.node_type_to_num:
            num = self.node_type_to_num[node_type]
            self.node_type_to_num[node_type] = num + 1
        else:
            self.node_type_to_num[node_type] = 0
        return node_type + "_" + str(self.node_type_to_num[node_type])


class Graph(BaseNode):

    def __init__(self) -> None:
        super().__init__()
        self.nodes: Dict[Text, BaseNode] = {}
        self.edges: Dict[Text, List[Edge]] = {}

    def add_node(self, node: BaseNode):
        instance_id = get_id_generator(self).generate_id(node)
        node.set_instance_id(instance_id)
        self.nodes[instance_id] = node

    def add_edge(self, instance_id: Text, edge: Edge):
        if instance_id in self.edges:
            for e in self.edges[instance_id]:
                if e == edge:
                    return
            self.edges[instance_id].append(edge)
        else:
            self.edges[instance_id] = []
            self.edges[instance_id].append(edge)

    def is_in_graph(self, node_id: Text) -> bool:
        return node_id in self.nodes

    def get_node_by_id(self, node_id: Text) -> Optional[BaseNode]:
        if node_id in self.nodes:
            return self.nodes[node_id]
        else:
            return None

    def clear_graph(self):
        self.nodes.clear()
        self.edges.clear()

    def is_empty(self) -> bool:
        return len(self.nodes) == 0 and len(self.edges) == 0


def load_graph(json_text: str) -> Graph:
    graph: Graph = loads(json_text)
    return graph
