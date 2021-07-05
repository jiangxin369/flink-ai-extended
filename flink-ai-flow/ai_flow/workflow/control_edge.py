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
from enum import Enum
from typing import Text

from ai_flow.util.json_utils import Jsonable
from notification_service.base_notification import UNDEFINED_EVENT_TYPE, DEFAULT_NAMESPACE

from ai_flow.graph.edge import Edge


class MetCondition(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    NECESSARY = "NECESSARY"


class TaskAction(str, Enum):
    START = "START"
    RESTART = "RESTART"
    STOP = "STOP"
    NONE = "NONE"


class EventLife(str, Enum):
    """
    ONCE: the event value will be used only once
    REPEATED: the event value will be used repeated
    """
    ONCE = "ONCE"
    REPEATED = "REPEATED"


class MetValueCondition(str, Enum):
    """
    EQUAL: the condition that notification service updates a value which equals to the event value
    UPDATE: the condition that notification service has a update operation on the event key which event
            value belongs to
    """
    EQUAL = "EQUAL"
    UPDATE = "UPDATE"


class MetConfig(Jsonable):
    def __init__(self,
                 event_key: Text,
                 event_value: Text,
                 event_type: Text = UNDEFINED_EVENT_TYPE,
                 condition: MetCondition = MetCondition.NECESSARY,
                 action: TaskAction = TaskAction.START,
                 life: EventLife = EventLife.ONCE,
                 value_condition: MetValueCondition = MetValueCondition.EQUAL,
                 namespace: Text = DEFAULT_NAMESPACE,
                 sender: Text = None
                 ):
        self.event_type = event_type
        self.event_key = event_key
        self.event_value = event_value
        self.condition = condition
        self.action = action
        self.life = life
        self.value_condition = value_condition
        self.namespace = namespace
        self.sender = sender


class ControlEdge(Edge):

    def __init__(self,
                 head: Text,
                 event_key: Text,
                 event_value: Text,
                 event_type: Text = UNDEFINED_EVENT_TYPE,
                 condition: MetCondition = MetCondition.NECESSARY,
                 action: TaskAction = TaskAction.START,
                 life: EventLife = EventLife.ONCE,
                 value_condition: MetValueCondition = MetValueCondition.EQUAL,
                 namespace: Text = DEFAULT_NAMESPACE,
                 sender: Text = None
                 ) -> None:
        super().__init__(sender, head)
        self.event_key = event_key
        self.event_value = event_value
        self.event_type = event_type
        self.condition = condition
        self.action = action
        self.life = life
        self.value_condition = value_condition
        self.namespace = namespace
        self.sender = sender

    def generate_met_config(self) -> MetConfig:
        return MetConfig(event_key=self.event_key,
                         event_value=self.event_value,
                         event_type=self.event_type,
                         condition=self.condition,
                         action=self.action,
                         life=self.life,
                         value_condition=self.value_condition,
                         namespace=self.namespace,
                         sender=self.sender)


class AIFlowInnerEventType(object):
    JOB_STATUS_CHANGED = "JOB_STATUS_CHANGED"
    UPSTREAM_JOB_SUCCESS = "UPSTREAM_JOB_SUCCESS"
    PERIODIC_ACTION = "PERIODIC_ACTION"
    DATASET_CHANGED = "DATASET_CHANGED"
