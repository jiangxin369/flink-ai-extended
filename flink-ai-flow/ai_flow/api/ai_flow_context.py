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
import traceback
from typing import Text
from ai_flow.context.project_context import init_project_context, project_config
from ai_flow.context.workflow_context import init_workflow_context
from ai_flow.client.ai_flow_client import get_ai_flow_client


def init_ai_flow_context(workflow_entry_file: Text = None):
    """
    Init project description, project config, workflow config.
    :param workflow_entry_file: The workflow definition python file.
    If workflow_entry_file is None, it means this function is called in workflow definition file.
    :return: None
    """
    if workflow_entry_file is None:
        stack = traceback.extract_stack()
        workflow_entry_file = stack[-2].filename
    workflows_path = os.path.dirname(os.path.dirname(workflow_entry_file))
    # workflow_name/workflow_name.py len(.py) == 3
    workflow_name = os.path.basename(workflow_entry_file)[:-3]
    project_path = os.path.dirname(workflows_path)
    init_project_context(project_path)
    __ensure_project_registered()
    # workflow_name/workflow_name.yaml
    init_workflow_context(workflow_config_file
                          =os.path.join(workflows_path, workflow_name, '{}.yaml'.format(workflow_name)))


def __ensure_project_registered():
    """ Ensure the project configured in project.yaml has been registered. """

    client = get_ai_flow_client()
    project_meta = client.get_project_by_name(project_config().get_project_name())
    pp = {}
    for k, v in project_config().items():
        pp[k] = str(v)
    if project_meta is None:
        project_meta = client.register_project(name=project_config().get_project_name(),
                                               properties=pp)
    else:
        project_meta = client.update_project(project_name=project_config().get_project_name(), properties=pp)

    project_config().set_project_uuid(str(project_meta.uuid))
