#  Copyright Software Improvement Group
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from functools import cached_property

import dateutil.parser

from report_generator import sigrid_api


class _AnonDataClass:
    total_deps = 0

    date_day = ""
    date_month = ""
    date_year = ""

    # critical, high, medium, low, no risk
    vuln_risks = [0, 0, 0, 0, 0]
    license_risks = [0, 0, 0, 0, 0]
    freshness_risks = [0, 0, 0, 0, 0]
    stability_risks = [0, 0, 0, 0, 0]
    mgmt_risks = [0, 0, 0, 0, 0]
    activity_risks = [0, 0, 0, 0, 0]

    vulns = []

    @property
    def total_vulnerable(self):
        return sum(self.vuln_risks[0:4])


class OSHData:
    @cached_property
    def raw_data(self):
        return sigrid_api.get_osh_findings()

    @cached_property
    def data(self):
        raw_data = self.raw_data
        data = _AnonDataClass()

        for component in raw_data.get("components", []):
            data.total_deps += 1

            if data.date_year == "":
                (data.date_year, data.date_month, data.date_day) = self._format_date(raw_data["metadata"]["timestamp"])

            self._assign_risk(data.vuln_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:vulnerability"))
            self._assign_risk(data.license_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:legal"))
            self._assign_risk(data.freshness_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:freshness"))
            self._assign_risk(data.stability_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:stability"))
            self._assign_risk(data.mgmt_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:management"))
            self._assign_risk(data.activity_risks,
                              self._find_cyclonedx_property_value(component["properties"], "sigrid:risk:activity"))

        return data

    @property
    def vulnerability_summary(self):
        total_vulns = self.data.total_vulnerable
        if total_vulns > 0:
            pct_vulns = max(total_vulns / self.data.total_deps,
                            0.01)  # Percentage should always be at least 1. 0% looks stupid.
            return f"{pct_vulns:.0%} of dependencies ({total_vulns} in total) used in the system contain one or more known vulnerabilities."
        else:
            return "The system is free of known vulnerabilities."

    @property
    def freshness_summary(self):
        total_outdated = sum(self.data.freshness_risks[
                             0:3])  # Only count critial+high+medium risk. Llow is fresh enough to not report on
        if total_outdated > 0:
            pct_outdated = max(total_outdated / self.data.total_deps, 0.01)
            return f"{pct_outdated:.0%} of dependencies ({total_outdated} in total) used in the system have not been updated for over 2 years."
        else:
            return "All dependencies in the system have been updated in the last 2 years."

    @property
    def legal_summary(self):
        total_legal = sum(self.data.license_risks[
                          0:3])  # Only count critial, high, and medium. Low license risk is typically not restrictive, so not interesting to report on
        if total_legal > 0:
            pct_legal = max(total_legal / self.data.total_deps, 0.01)
            return f"{pct_legal:.0%} of dependencies ({total_legal} in total) uses a potentially restrictive open-source license (e.g. GPL/AGPL)."
        else:
            return "All dependencies in the system use relatively liberal open-source licenses."

    @property
    def management_summary(self):
        total_unmanaged = sum(self.data.mgmt_risks[0:4])
        if total_unmanaged > 0:
            pct_unmanaged = max(total_unmanaged / self.data.total_deps, 0.01)
            return f"{pct_unmanaged:.0%} of dependencies ({total_unmanaged} in total) does not use a package manager but is placed in the codebase directly."
        else:
            return "All dependencies in the system are managed by a package manager."

    @staticmethod
    def _format_date(input_date):
        date = dateutil.parser.isoparse(input_date)
        return str(date.year), date.strftime('%b').upper(), str(date.day)

    @staticmethod
    def _assign_risk(values, risk):
        if risk == "CRITICAL":
            values[0] += 1
        elif risk == "HIGH":
            values[1] += 1
        elif risk == "MEDIUM":
            values[2] += 1
        elif risk == "LOW":
            values[3] += 1
        else:
            values[4] += 1

    @staticmethod
    def _find_cyclonedx_property_value(properties, key):
        for prop in properties:
            if prop["name"] == key:
                return prop["value"]
        return None


osh_data = OSHData()
