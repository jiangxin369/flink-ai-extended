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
import unittest
from ai_flow.util.path_util import get_file_dir
from ai_flow.project.project_description import get_project_description_from


class TestProjectDesc(unittest.TestCase):

    def test_project_desc(self):
        project_path = get_file_dir(__file__)
        project_desc = get_project_description_from(project_path)
        self.assertTrue(project_desc.get_absolute_project_config_file().endswith('project.yaml'))
        self.assertTrue(project_desc.get_absolute_generated_path().endswith('generated'))
        self.assertTrue(project_desc.get_absolute_temp_path().endswith('temp'))
        self.assertTrue(project_desc.get_absolute_workflows_path().endswith('workflows'))
        self.assertTrue(project_desc.get_absolute_dependencies_path().endswith('dependencies'))
        self.assertTrue(project_desc.get_absolute_log_path().endswith('logs'))
        self.assertTrue(project_desc.get_absolute_python_dependencies_path().endswith('python'))
        self.assertTrue(project_desc.get_absolute_go_dependencies_path().endswith('go'))
        self.assertTrue(project_desc.get_absolute_jar_dependencies_path().endswith('jar'))
        self.assertTrue(project_desc.get_absolute_resources_path().endswith('resources'))


if __name__ == '__main__':
    unittest.main()
