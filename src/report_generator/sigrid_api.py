# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import json

class SigridAPI:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        self.base_url = "https://sigrid-says.com/rest"
        self.base_analysis_results_url = "analysis-results/api/v1"

    def get_headers(self, is_patch=False):
        headers = {
            "Content-type" : "application/json",
            "Authorization" : f"Bearer {self.bearer_token}"
        }
        if is_patch:
            headers['Content-type'] = "application/merge-patch+json"
        return headers

    def get_maintainability_ratings_for_customer(self, customer):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/maintainability/{customer}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_maintainability_ratings_for_customer_system(self, customer, system, includeTechStats: bool):
        headers = self.get_headers()
        techStats = "true" if includeTechStats else "false"
        url = f"{self.base_url}/{self.base_analysis_results_url}/maintainability/{customer}/{system}?technologyStats={techStats}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_maintainability_ratings_for_customer_system_components(self, customer, system):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/maintainability/{customer}/{system}/components"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    # Probably won't work; API not accessible for outsiders (even SIG consultants)
    def get_capabilities_for_customer_system(self, customer, system):
        headers = self.get_headers()
        url = f"{self.base_url}/analysis-results/capabilities/{customer}/{system}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_metadata_for_customer(self, customer):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/system-metadata/{customer}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def set_metadata_for_customer_system(self, customer, system, payload):
        headers = self.get_headers(is_patch=True)
        url = f"{self.base_url}/{self.base_analysis_results_url}/system-metadata/{customer}/{system}"
        retval = requests.patch(url, data=json.dumps(payload), headers=headers)
        retval.raise_for_status()

    def get_osh_findings_for_customer(self, customer, is_vulnerable=True):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/osh-findings/{customer}"
        if is_vulnerable:
            url = f"{url}?vulnerable=true"
        else:
            url = f"{url}?vulnerable=false"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_osh_findings_for_customer_system(self, customer, system, is_vulnerable=False):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/osh-findings/{customer}/{system}"
        if is_vulnerable:
            url = f"{url}?vulnerable=true"
        else:
            url = f"{url}?vulnerable=false"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_security_findings_for_customer_system(self, customer, system):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/security-findings/{customer}/{system}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()
    
    def get_architecture_findings_for_customer(self, customer):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/architecture-quality/{customer}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()

    def get_architecture_findings_for_customer_system(self, customer, system):
        headers = self.get_headers()
        url = f"{self.base_url}/{self.base_analysis_results_url}/architecture-quality/{customer}/{system}"
        retval = requests.get(url, headers=headers)
        retval.raise_for_status()
        return retval.json()
