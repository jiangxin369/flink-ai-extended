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
from contextlib import contextmanager
from typing import Text
from ai_flow.context.workflow_context import workflow_config


class JobContext(object):
    def __init__(self) -> None:
        self.current_job_name = None
        self.job_depth = 0


__default_job_context__ = JobContext()


@contextmanager
def job_config(job_name: Text):
    """
    Set the specific job config.
    :param job_name: The job name
    """
    __default_job_context__.current_job_name = job_name
    __default_job_context__.job_depth += 1
    if __default_job_context__.job_depth > 1:
        raise Exception("job_config can not nesting")
    try:
        yield workflow_config().job_configs.get(__default_job_context__.current_job_name)
    finally:
        __default_job_context__.current_job_name = None
        __default_job_context__.job_depth -= 1


def current_job_name() -> Text:
    return __default_job_context__.current_job_name
