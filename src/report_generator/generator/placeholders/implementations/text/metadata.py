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

from report_generator.generator.domain import maintainability_data, system_metadata
from report_generator.generator.utils.constants.metadata import (
    METADATA_APPLICATION_TYPE_MAPPING,
    METADATA_BUSINESS_CRITICALITY_MAPPING,
    METADATA_DEPLOYMENT_MAPPING,
    METADATA_DISTRIBUTION_MAPPING,
    METADATA_LIFECYCLE_MAPPING,
    METADATA_TARGET_INDUSTRY_MAPPING,
)

from .base import text_placeholder


@text_placeholder()
def system_name():
    """The name of the system as defined in Sigrid Metadata, capitalized."""
    return system_metadata.display_name


@text_placeholder()
def customer_name():
    """The name of the customer as defined in Sigrid, capitalized."""
    return maintainability_data.customer_name


@text_placeholder()
def system_full_name():
    """The full name of the system as defined in Sigrid."""
    return maintainability_data.system_name


@text_placeholder()
def metadata_division():
    """The division name of the system."""
    return system_metadata.division_name or ""


@text_placeholder()
def metadata_team():
    """The team names associated with the system, comma-separated."""
    teams = system_metadata.team_names
    if not teams:
        return ""
    return ", ".join(teams)


@text_placeholder()
def metadata_supplier():
    """The supplier names associated with the system, comma-separated."""
    suppliers = system_metadata.supplier_names
    if not suppliers:
        return ""
    return ", ".join(suppliers)


@text_placeholder()
def metadata_remark():
    """The remark field for the system."""
    return system_metadata.remark or ""


@text_placeholder()
def metadata_status_active():
    """Whether the system is active (Yes/No)."""
    return "Yes" if system_metadata.active else "No"


@text_placeholder()
def metadata_excluded_from_dashboards():
    """Whether the system is excluded from dashboards (Yes/No)."""
    return "Yes" if system_metadata.is_development_only else "No"


@text_placeholder()
def metadata_in_production_since():
    """The year when the system was put into production."""
    year = system_metadata.in_production_since
    return str(year) if year else ""


@text_placeholder()
def metadata_business_criticality():
    """The business criticality level of the system."""
    criticality = system_metadata.business_criticality
    if not criticality:
        return ""
    return METADATA_BUSINESS_CRITICALITY_MAPPING.get(criticality, criticality)


@text_placeholder()
def metadata_lifecycle_phase():
    """The lifecycle phase of the system."""
    phase = system_metadata.lifecycle_phase
    if not phase:
        return ""
    return METADATA_LIFECYCLE_MAPPING.get(phase, phase)


@text_placeholder()
def metadata_target_industry():
    """The target industry of the system."""
    industry = system_metadata.target_industry
    if not industry:
        return ""
    return METADATA_TARGET_INDUSTRY_MAPPING.get(industry, industry)


@text_placeholder()
def metadata_deployment_type():
    """The deployment type of the system."""
    deployment = system_metadata.deployment_type
    if not deployment:
        return ""
    return METADATA_DEPLOYMENT_MAPPING.get(deployment, deployment)


@text_placeholder()
def metadata_application_type():
    """The application type of the system."""
    app_type = system_metadata.application_type
    if not app_type:
        return ""
    return METADATA_APPLICATION_TYPE_MAPPING.get(app_type, app_type)


@text_placeholder()
def metadata_distribution_strategy():
    """The software distribution strategy of the system."""
    strategy = system_metadata.software_distribution_strategy
    if not strategy:
        return ""
    return METADATA_DISTRIBUTION_MAPPING.get(strategy, strategy)


@text_placeholder()
def metadata_external_id():
    """The external ID of the system."""
    return system_metadata.external_id or ""


@text_placeholder()
def metadata_external_display_name():
    """The external display name of the system."""
    return system_metadata.external_display_name or ""
