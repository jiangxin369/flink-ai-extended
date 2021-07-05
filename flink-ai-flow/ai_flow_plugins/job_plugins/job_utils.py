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

from ai_flow.project.project_description import ProjectDesc
from ai_flow.runtime.job_runtime_env import JobRuntimeEnv


def prepare_job_runtime_env(workflow_id, workflow_name, job_name, project_desc: ProjectDesc) -> JobRuntimeEnv:
    temp_path = project_desc.get_absolute_temp_path()
    working_dir = os.path.join(temp_path, workflow_id, job_name)
    job_runtime_env: JobRuntimeEnv = JobRuntimeEnv(working_dir=working_dir,
                                                   workflow_name=workflow_name,
                                                   job_name=job_name)
    if not os.path.exists(working_dir):
        os.makedirs(job_runtime_env.log_dir)
        job_runtime_env.save_workflow_name()
        job_runtime_env.save_job_name()
        os.symlink(project_desc.get_absolute_workflow_entry_file(workflow_name=workflow_name),
                   os.path.join(working_dir, '{}.py'.format(workflow_name)))
        os.symlink(project_desc.get_absolute_workflow_config_file(workflow_name=workflow_name),
                   os.path.join(working_dir, '{}.yaml'.format(workflow_name)))
        if os.path.exists(project_desc.get_absolute_generated_path()):
            os.symlink(os.path.join(project_desc.get_absolute_generated_path(), workflow_id, job_name),
                       job_runtime_env.generated_dir)
        if os.path.exists(project_desc.get_absolute_resources_path()):
            os.symlink(project_desc.get_absolute_resources_path(), job_runtime_env.resource_dir)
        if os.path.exists(project_desc.get_absolute_dependencies_path()):
            os.symlink(project_desc.get_absolute_dependencies_path(), job_runtime_env.dependencies_dir)
        os.symlink(project_desc.get_absolute_project_config_file(), job_runtime_env.project_config_file)
    return job_runtime_env
