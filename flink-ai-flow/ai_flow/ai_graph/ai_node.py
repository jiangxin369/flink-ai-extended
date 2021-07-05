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
from typing import Text, List, Dict
from ai_flow.graph.node import BaseNode
from ai_flow.workflow.job import JobConfig
from ai_flow.util import serialization_utils
from ai_flow.graph.channel import Channel, NoneChannel


class AINode(BaseNode):
    def __init__(self,
                 executor: object = None,
                 name: Text = None,
                 instance_id: Text = None,
                 output_num: int = 1,
                 config: JobConfig = None,
                 node_type: Text = 'AINode',
                 **kwargs) -> None:
        super().__init__(properties=None,
                         name=name,
                         instance_id=instance_id,
                         output_num=output_num)
        self.executor: bytes = serialization_utils.serialize(executor)
        self.config: JobConfig = config
        self.node_config: Dict = kwargs
        self.node_config['name'] = name
        self.node_config['node_type'] = node_type

    def outputs(self) -> List[Channel]:
        if self.output_num > 0:
            result = []
            for i in range(self.output_num):
                result.append(Channel(node_id=self.instance_id, port=i))
            return result
        else:
            return [NoneChannel(self.instance_id)]

    def get_executor(self)->object:
        if self.executor is None:
            return None
        else:
            return serialization_utils.deserialize(self.executor)
