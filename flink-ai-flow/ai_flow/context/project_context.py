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
from typing import Text
from ai_flow.project.project_config import ProjectConfig
from ai_flow.project.project_description import ProjectDesc, get_project_description_from


class ProjectContext(object):
    def __init__(self) -> None:
        self.project_desc: ProjectDesc = None
        self.project_config: ProjectConfig = None


__default_project_context__ = ProjectContext()


def init_project_context(project_path: Text):
    project_desc = get_project_description_from(project_path)
    __default_project_context__.project_desc = project_desc
    __default_project_context__.project_config = project_desc.project_config


def project_description() -> ProjectDesc:
    return __default_project_context__.project_desc


def project_config() -> ProjectConfig:
    """
    :return: project configuration
    """
    return __default_project_context__.project_config
