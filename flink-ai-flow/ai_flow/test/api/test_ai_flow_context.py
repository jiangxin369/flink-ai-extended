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
import os
from ai_flow.endpoint.server.server import AIFlowServer
from ai_flow.api.ai_flow_context import init_ai_flow_context
from ai_flow.context.project_context import project_config, project_description
from ai_flow.context.workflow_context import workflow_config


_SQLITE_DB_FILE = 'aiflow.db'
_SQLITE_DB_URI = '%s%s' % ('sqlite:///', _SQLITE_DB_FILE)
_PORT = '50051'


class TestSchedulingService(unittest.TestCase):
    def setUp(self):

        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)
        self.server = AIFlowServer(store_uri=_SQLITE_DB_URI, port=_PORT,
                                   start_default_notification=False,
                                   start_meta_service=True,
                                   start_metric_service=False,
                                   start_model_center_service=False,
                                   start_scheduler_service=False)
        self.server.run()

    def tearDown(self):
        self.server.stop()
        if os.path.exists(_SQLITE_DB_FILE):
            os.remove(_SQLITE_DB_FILE)

    def test_init_ai_flow_context(self):
        init_ai_flow_context(os.path.join(os.path.dirname(__file__), 'ut_workflows', 'workflows',
                                          'workflow_1', 'workflow_1.py'))
        project_config_ = project_config()
        self.assertEqual('test_project', project_config_.get_project_name())
        self.assertEqual('a', project_config_.get('a'))
        project_desc = project_description()
        self.assertEqual('test_project', project_desc.project_name)
        workflow_config_ = workflow_config()
        self.assertEqual('workflow_1', workflow_config_.workflow_name)
        self.assertEqual(5, len(workflow_config_.job_configs))


if __name__ == '__main__':
    unittest.main()
