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
from typing import List

from ai_flow.endpoint.server import stringValue
from ai_flow.protobuf.message_pb2 import WorkflowProto, WorkflowExecutionProto, StateProto, JobProto, \
    ExecutionLabelProto
from ai_flow.plugin_interface.scheduler_interface import WorkflowInfo, WorkflowExecutionInfo, JobExecutionInfo, \
    ExecutionLabel
from ai_flow.workflow.state import State


def proto_to_state(state):
    if state == StateProto.INIT:
        return State.INIT
    elif state == StateProto.STARTING:
        return State.STARTING
    elif state == StateProto.RUNNING:
        return State.RUNNING
    elif state == StateProto.FINISHED:
        return State.FINISHED
    elif state == StateProto.FAILED:
        return State.FAILED
    elif state == StateProto.KILLING:
        return State.KILLING
    elif state == StateProto.KILLED:
        return State.KILLED


def workflow_to_proto(workflow: WorkflowInfo) -> WorkflowProto:
    if workflow is None:
        return None
    wp = WorkflowProto(name=workflow.workflow_name, namespace=workflow.namespace)
    for k, v in workflow.properties.items():
        wp.properties[k] = v
    return wp


def proto_to_workflow(proto: WorkflowProto) -> WorkflowInfo:
    if proto is None:
        return None
    else:
        return WorkflowInfo(namespace=proto.namespace, workflow_name=proto.name, properties=dict(proto.properties))


def workflow_list_to_proto(workflow_list: List[WorkflowInfo]) -> List[WorkflowProto]:
    result = []
    for workflow in workflow_list:
        result.append(workflow_to_proto(workflow))
    return result


def proto_to_workflow_list(proto_list: List[WorkflowProto]) -> List[WorkflowInfo]:
    result = []
    for proto in proto_list:
        result.append(proto_to_workflow(proto))
    return result


def workflow_execution_to_proto(workflow_execution: WorkflowExecutionInfo) -> WorkflowExecutionProto:
    if workflow_execution is None:
        return None
    if workflow_execution.state is None:
        state = State.INIT
    else:
        state = workflow_execution.state
    wp = WorkflowExecutionProto(execution_id=workflow_execution.workflow_execution_id,
                                execution_state=StateProto.Value(state),
                                workflow=workflow_to_proto(workflow_execution.workflow_info))
    for k, v in workflow_execution.properties.items():
        wp.properties[k] = v
    return wp


def proto_to_workflow_execution(proto: WorkflowExecutionProto) -> WorkflowExecutionInfo:
    if proto is None:
        return None
    else:
        return WorkflowExecutionInfo(workflow_execution_id=proto.execution_id,
                                     state=proto_to_state(proto.execution_state),
                                     workflow_info=proto_to_workflow(proto.workflow),
                                     properties=dict(proto.properties))


def workflow_execution_list_to_proto(workflow_execution_list: List[WorkflowExecutionInfo]) \
        -> List[WorkflowExecutionProto]:
    result = []
    for workflow_execution in workflow_execution_list:
        result.append(workflow_execution_to_proto(workflow_execution))
    return result


def proto_to_workflow_execution_list(proto_list: List[WorkflowExecutionProto]) -> List[WorkflowExecutionInfo]:
    result = []
    for proto in proto_list:
        result.append(proto_to_workflow_execution(proto))
    return result


def job_to_proto(job: JobExecutionInfo) -> JobProto:
    if job.state is None:
        state = State.INIT
    else:
        state = job.state
    return JobProto(name=job.job_name,
                    job_id=stringValue(job.job_execution_id),
                    job_state=StateProto.Value(state),
                    properties=job.properties,
                    workflow_execution=workflow_execution_to_proto(job.workflow_execution))


def proto_to_job(proto: JobProto) -> JobExecutionInfo:
    if proto is None:
        return None
    else:
        return JobExecutionInfo(job_name=proto.name,
                                job_execution_id=proto.job_id.value,
                                state=proto_to_state(proto.job_state),
                                properties=proto.properties,
                                workflow_execution=proto_to_workflow_execution(proto.workflow_execution))


def job_list_to_proto(job_list: List[JobExecutionInfo]) -> List[JobProto]:
    result = []
    for job in job_list:
        result.append(job_to_proto(job))
    return result


def proto_to_job_list(proto_list: List[JobProto]) -> List[JobExecutionInfo]:
    result = []
    for proto in proto_list:
        result.append(proto_to_job(proto))
    return result


def execution_label_to_proto(label: ExecutionLabel) -> ExecutionLabelProto:
    if label is None:
        return None
    else:
        return ExecutionLabelProto(uuid=label.uuid,
                                   name=stringValue(label.name),
                                   value=stringValue(label.value))


def proto_to_execution_label(proto: ExecutionLabelProto) -> ExecutionLabel:
    if proto is None:
        return None
    else:
        return ExecutionLabel(uuid=proto.uuid,
                              name=proto.name.value,
                              value=proto.value.value)
