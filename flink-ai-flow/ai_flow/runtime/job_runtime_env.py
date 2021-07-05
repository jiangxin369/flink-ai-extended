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
from typing import Text
from ai_flow.util import serialization_utils


class JobRuntimeEnv(object):
    """
    The job runtime environment
    """
    def __init__(self,
                 working_dir: Text,
                 workflow_name: Text = None,
                 job_name: Text = None):
        self._working_dir: Text = working_dir
        self._workflow_name: Text = workflow_name
        self._job_name: Text = job_name

    @property
    def working_dir(self)->Text:
        return self._working_dir

    @property
    def workflow_name(self)->Text:
        if self._workflow_name is None:
            self._workflow_name = serialization_utils.read_object_from_serialized_file(
                os.path.join(self.working_dir, 'workflow_name'))
        return self._workflow_name

    @property
    def job_name(self)->Text:
        if self._job_name is None:
            self._job_name = serialization_utils.read_object_from_serialized_file(
                os.path.join(self.working_dir, 'job_name')
            )
        return self._job_name

    @property
    def log_dir(self) -> Text:
        return os.path.join(self._working_dir, 'logs')

    @property
    def resource_dir(self)->Text:
        return os.path.join(self._working_dir, 'resources')

    @property
    def generated_dir(self)->Text:
        return os.path.join(self._working_dir, 'generated')

    @property
    def dependencies_dir(self)->Text:
        return os.path.join(self._working_dir, 'dependencies')

    @property
    def python_dep_dir(self)->Text:
        return os.path.join(self.dependencies_dir, 'python')

    @property
    def go_dep_dir(self) -> Text:
        return os.path.join(self.dependencies_dir, 'go')

    @property
    def jar_dep_dir(self) -> Text:
        return os.path.join(self.dependencies_dir, 'jar')

    @property
    def project_config_file(self)->Text:
        return os.path.join(self.working_dir, 'project.yaml')

    @property
    def workflow_config_file(self)->Text:
        return os.path.join(self.working_dir, '{}.yaml'.format(self.workflow_name))

    @property
    def workflow_entry_file(self) -> Text:
        return os.path.join(self.working_dir, '{}.py'.format(self.workflow_name))

    def save_workflow_name(self):
        if self._workflow_name is None:
            return
        file_path = os.path.join(self.working_dir, 'workflow_name')
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'wb') as fp:
            fp.write(serialization_utils.serialize(self._workflow_name))

    def save_job_name(self):
        if self._job_name is None:
            return
        file_path = os.path.join(self.working_dir, 'job_name')
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'wb') as fp:
            fp.write(serialization_utils.serialize(self._job_name))
