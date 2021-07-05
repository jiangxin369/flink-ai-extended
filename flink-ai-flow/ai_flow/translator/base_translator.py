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
from ai_flow.project.project_description import ProjectDesc
from ai_flow.workflow.workflow import Workflow
from ai_flow.workflow.job import Job
from ai_flow.ai_graph.ai_graph import AIGraph, SplitGraph, AISubGraph
from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, graph: AIGraph, project_desc: ProjectDesc) -> Workflow:
        pass


class BaseGraphSplitter(ABC):
    @abstractmethod
    def split(self, graph: AIGraph, project_desc: ProjectDesc) -> SplitGraph:
        pass


class BaseJobGenerator(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def generate(self, sub_graph: AISubGraph) -> Job:
        pass


class BaseWorkflowConstructor(ABC):
    @abstractmethod
    def build_workflow(self, split_graph: SplitGraph, project_desc: ProjectDesc) -> Workflow:
        pass
