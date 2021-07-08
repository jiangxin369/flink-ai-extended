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

import requests

from typing import List


class BaichuanClient:
    GET_JOB_ATTEMPT_URL_TEMPLATE = "{}/api/jobs/jobAttempt/{}/list"
    GET_ATTEMPT_STATUS_URL_TEMPLATE = "{}/api/jobs/jobAttempt/{}/_status"

    def __init__(self, baichuan_base_url: str):
        self.baichuan_base_url = baichuan_base_url

    def get_job_attempt_ids(self, job_id) -> List[str]:
        url = self.GET_JOB_ATTEMPT_URL_TEMPLATE.format(self.baichuan_base_url, job_id)
        r = requests.get(url).json()
        return [job['id'] for job in r['data']['jobs']]

    def get_latest_job_attempt_id(self, job_id) -> str:
        attempt_ids = self.get_job_attempt_ids(job_id)
        if len(attempt_ids) <= 0:
            return None
        return attempt_ids[0]

    def get_latest_job_attempt_status(self, job_id) -> str:
        attempt_id = self.get_latest_job_attempt_id(job_id)
        return self.get_job_attempt_status(attempt_id)

    def get_job_attempt_status(self, attempt_id) -> str:
        url = self.GET_ATTEMPT_STATUS_URL_TEMPLATE.format(self.baichuan_base_url, attempt_id)
        r = requests.get(url).json()
        reason_ = r['data']['reason']
        if reason_ is None:
            return r['data']['job_status']
        return r['data']['job_status'] + ": " + reason_
