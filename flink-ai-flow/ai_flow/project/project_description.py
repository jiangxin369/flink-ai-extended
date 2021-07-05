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
from typing import List, Text
from ai_flow.project.project_config import ProjectConfig
from ai_flow.util.json_utils import Jsonable


class ProjectDesc(Jsonable):
    """
    ProjectDesc( project descriptor) maintains the directory structure and information of an ai flow project.
    A common ai flow project would follow the directory structure as bellow.

    SimpleProject
        |- workflows
           |- workflow_name1
           |- workflow_name2
           |- workflow_name3
              |- workflow_name3.py
              |- workflow_name3.yaml
        |- dependencies
            |-python
            |-jar
            |-go
        |- logs
        |- generated
        |- temp
        |- resources
        └─ project.yaml
    """
    def __init__(self) -> None:
        super().__init__()
        self.project_path: Text = None
        self.project_config: ProjectConfig = None

    @property
    def project_name(self):
        return self.project_config.get_project_name()

    def get_absolute_temp_path(self)->Text:
        return os.path.join(self.project_path, 'temp')

    def get_absolute_log_path(self)->Text:
        return os.path.join(self.project_path, 'logs')

    def get_absolute_resources_path(self)->Text:
        return os.path.join(self.project_path, 'resources')

    def get_absolute_generated_path(self)->Text:
        return os.path.join(self.project_path, 'generated')

    def list_resources_paths(self)->List:
        return os.listdir(self.get_absolute_resources_path())

    def get_absolute_dependencies_path(self)->Text:
        return os.path.join(self.project_path, 'dependencies')

    def get_absolute_project_config_file(self)->Text:
        return os.path.join(self.project_path, 'project.yaml')

    def get_absolute_python_dependencies_path(self)->Text:
        return os.path.join(self.get_absolute_dependencies_path(), 'python')

    def get_absolute_jar_dependencies_path(self)->Text:
        return os.path.join(self.get_absolute_dependencies_path(), 'jar')

    def list_jar_paths(self)->List:
        return os.listdir(self.get_absolute_jar_dependencies_path())

    def get_absolute_go_dependencies_path(self)->Text:
        return os.path.join(self.get_absolute_dependencies_path(), 'go')

    def get_absolute_workflows_path(self)->Text:
        return os.path.join(self.project_path, 'workflows')

    def list_workflows(self)->List[Text]:
        return os.listdir(self.get_absolute_workflows_path())

    def get_absolute_workflow_path(self, workflow_name)->Text:
        return os.path.join(self.get_absolute_workflows_path(), workflow_name)

    def get_absolute_workflow_config_file(self, workflow_name)->Text:
        return os.path.join(self.get_absolute_workflow_path(workflow_name), '{}.yaml'.format(workflow_name))

    def get_absolute_workflow_entry_file(self, workflow_name)->Text:
        return os.path.join(self.get_absolute_workflow_path(workflow_name), '{}.py'.format(workflow_name))

    def get_workflow_entry_module(self, workflow_name)->Text:
        return workflow_name


def get_project_description_from(project_path: Text) -> ProjectDesc:
    """
    Load a project descriptor for a given project path.
    :param project_path: the path of a ai flow project.
    :return: a ProjectDesc object that contains the structure information of this project.
    """
    project_spec = ProjectDesc()
    project_path = os.path.abspath(project_path)
    project_spec.project_path = project_path
    project_spec.project_config = ProjectConfig()
    project_spec.project_config.load_from_file(project_spec.get_absolute_project_config_file())
    return project_spec


