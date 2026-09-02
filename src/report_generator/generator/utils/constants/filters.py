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

# Singular/plural label for each portfolio metadata dimension, used to describe
# applied filters and the active group-by in a report. Keys must match the filter
# names in FILTER_CONFIGURATION.

DIMENSION_LABELS: dict[str, tuple[str, str]] = {
    "team": ("team", "teams"),
    "division": ("division", "divisions"),
    "lifecycle": ("lifecycle phase", "lifecycle phases"),
    "deployment": ("deployment type", "deployment types"),
    "business_criticality": ("business criticality", "business criticalities"),
    "distribution": ("distribution strategy", "distribution strategies"),
    "application_type": ("application type", "application types"),
    "target_industry": ("target industry", "target industries"),
    "technology_category": ("technology category", "technology categories"),
    "main_technology": ("main technology", "main technologies"),
    "supplier": ("supplier", "suppliers"),
}
