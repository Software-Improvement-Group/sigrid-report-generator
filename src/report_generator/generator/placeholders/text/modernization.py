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

from report_generator.generator.data_models import *
from .base import parameterized_text_placeholder, text_placeholder


@parameterized_text_placeholder(custom_key="MODERNIZATION_SYSTEM_{parameter}", parameters=range(1, 11))
def modernization_system_name(index: int):
    """Name of the modernization candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].display_name


@parameterized_text_placeholder(custom_key="MODERNIZATION_BUSINESS_{parameter}", parameters=range(1, 11))
def modernization_business_criticality(index: int):
    """Business criticality of the modernization candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].business_criticality.title()


@parameterized_text_placeholder(custom_key="MODERNIZATION_PY_{parameter}", parameters=range(1, 11))
def modernization_volume(index: int):
    """Volume of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].volume_in_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_ACTIVITY_{parameter}", parameters=range(1, 11))
def modernization_activity(index: int):
    """Activity level of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""

    activity = modernization_data.modernization_candidates[index].activity_in_py
    return "Unknown" if activity is None else f"{activity:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_SCENARIO_{parameter}", parameters=range(1, 11))
def modernization_scenario(index: int):
    """Modernization scenario for the candidate system."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return modernization_data.modernization_candidates[index].scenario.value.upper()


@parameterized_text_placeholder(custom_key="MODERNIZATION_TECHNICAL_DEBT_{parameter}", parameters=range(1, 11))
def modernization_technical_debt(index: int):
    """Technical debt of the modernization candidate system in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].technical_debt_in_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_CHANGE_SPEED_{parameter}", parameters=range(1, 11))
def modernization_change_speed(index: int):
    """Estimated change speed improvement for the modernization candidate."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"+ {modernization_data.modernization_candidates[index].estimated_change_speed:.0f}%"


@parameterized_text_placeholder(custom_key="MODERNIZATION_EFFORT_{parameter}", parameters=range(1, 11))
def modernization_effort(index: int):
    """Estimated modernization effort in person years."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{modernization_data.modernization_candidates[index].estimated_effort_py:.1f} PY"


@parameterized_text_placeholder(custom_key="MODERNIZATION_N_{parameter}", parameters=range(1, 11))
def modernization_index(index: int):
    """Index number for the modernization candidate."""
    if index >= len(modernization_data.modernization_candidates):
        return ""
    return f"{index}."


@text_placeholder()
def modernization_system_count():
    """Total number of modernization candidate systems."""
    return len(modernization_data.possible_candidates)


@text_placeholder()
def modernization_customer_name():
    """Customer name for modernization analysis."""
    return modernization_data.possible_candidates[0].metadata["customerName"].title()
